"""helpers for passlib unittests"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import math
import os
import random
import re
import sys
import tempfile
import threading
import time
import unittest
import warnings

# core
from binascii import unhexlify
from functools import partial, wraps
from typing import TYPE_CHECKING, Any
from unittest import SkipTest
from warnings import warn

import pytest

import passlib.utils.handlers as uh
from passlib import exc
from passlib.exc import (
    InternalBackendError,
    MissingBackendError,
    PasslibConfigWarning,
    PasslibHashWarning,
)
from passlib.utils import (
    batch,
    getrandstr,
    has_rounds_info,
    has_salt_info,
    is_ascii_safe,
    repeat_string,
    rounds_cost_values,
    tick,
)
from passlib.utils import (
    rng as sys_rng,
)
from passlib.utils.decor import classproperty
from tests.utils_ import no_warnings

if TYPE_CHECKING:
    from collections.abc import Sequence

    from passlib.ifc import PasswordHash
    from passlib.utils.handlers import PrefixWrapper


log = logging.getLogger(__name__)
# local
__all__ = [
    # util funcs
    "TEST_MODE",
    "set_file",
    "get_file",
    # unit testing
    "TestCase",
    "HandlerCase",
]


def ensure_mtime_changed(path):
    """ensure file's mtime has changed"""
    # NOTE: this is hack to deal w/ filesystems whose mtime resolution is >= 1s,
    #       when a test needs to be sure the mtime changed after writing to the file.
    last = os.path.getmtime(path)
    while os.path.getmtime(path) == last:
        time.sleep(0.1)
        os.utime(path, None)


def _get_timer_resolution(timer):
    def sample():
        start = cur = timer()
        while start == cur:
            cur = timer()
        return cur - start

    return min(sample() for _ in range(3))


TICK_RESOLUTION = _get_timer_resolution(tick)

_TEST_MODES = ["quick", "default", "full"]
_test_mode = _TEST_MODES.index(
    os.environ.get("PASSLIB_TEST_MODE", "default").strip().lower()
)


def TEST_MODE(min=None, max=None):
    """check if test for specified mode should be enabled.

    ``"quick"``
        run the bare minimum tests to ensure functionality.
        variable-cost hashes are tested at their lowest setting.
        hash algorithms are only tested against the backend that will
        be used on the current host. no fuzz testing is done.

    ``"default"``
        same as ``"quick"``, except: hash algorithms are tested
        at default levels, and a brief round of fuzz testing is done
        for each hash.

    ``"full"``
        extra regression and internal tests are enabled, hash algorithms are tested
        against all available backends, unavailable ones are mocked whre possible,
        additional time is devoted to fuzz testing.
    """
    if min and _test_mode < _TEST_MODES.index(min):
        return False
    if max and _test_mode > _TEST_MODES.index(max):  # noqa: SIM103
        return False
    return True


def has_relaxed_setting(handler):
    """check if handler supports 'relaxed' kwd"""
    # FIXME: I've been lazy, should probably just add 'relaxed' kwd
    # to all handlers that derive from GenericHandler

    # ignore wrapper classes for now.. though could introspec.
    if hasattr(handler, "orig_prefix"):
        return False

    return "relaxed" in handler.setting_kwds or issubclass(handler, uh.GenericHandler)


def get_effective_rounds(handler, rounds=None):
    """get effective rounds value from handler"""
    handler = unwrap_handler(handler)
    return handler(rounds=rounds, use_defaults=True).rounds


def is_default_backend(handler, backend):
    """check if backend is the default for source"""
    try:
        orig = handler.get_backend()
    except MissingBackendError:
        return False
    try:
        handler.set_backend("default")
        return handler.get_backend() == backend
    finally:
        handler.set_backend(orig)


def iter_alt_backends(handler, current=None, fallback=False):
    """
    iterate over alternate backends available to handler.

    .. warning::
        not thread-safe due to has_backend() call
    """
    if current is None:
        current = handler.get_backend()
    backends = handler.backends
    idx = backends.index(current) + 1 if fallback else 0
    for backend in backends[idx:]:
        if backend != current and handler.has_backend(backend):
            yield backend


def get_alt_backend(*args, **kwds):
    for backend in iter_alt_backends(*args, **kwds):
        return backend
    return None


def unwrap_handler(handler):
    """return original handler, removing any wrapper objects"""
    while hasattr(handler, "wrapped"):
        handler = handler.wrapped
    return handler


def handler_derived_from(handler, base):
    """
    test if <handler> was derived from <base> via <base.using()>.
    """
    # XXX: need way to do this more formally via ifc,
    #      for now just hacking in the cases we encounter in testing.
    if handler == base:
        return True
    if isinstance(handler, uh.PrefixWrapper):
        while handler:
            if handler == base:
                return True
            # helper set by PrefixWrapper().using() just for this case...
            handler = handler._derived_from
        return False
    if isinstance(handler, type) and issubclass(handler, uh.MinimalHandler):
        return issubclass(handler, base)
    raise NotImplementedError(f"don't know how to inspect handler: {handler!r}")


@contextlib.contextmanager
def patch_calc_min_rounds(handler):
    """
    internal helper for do_config_encrypt() --
    context manager which temporarily replaces handler's _calc_checksum()
    with one that uses min_rounds; useful when trying to generate config
    with high rounds value, but don't care if output is correct.
    """
    if isinstance(handler, type) and issubclass(handler, uh.HasRounds):
        # XXX: also require GenericHandler for this branch?
        wrapped = handler._calc_checksum

        def wrapper(self, *args, **kwds):
            rounds = self.rounds
            try:
                self.rounds = self.min_rounds
                return wrapped(self, *args, **kwds)
            finally:
                self.rounds = rounds

        handler._calc_checksum = wrapper
        try:
            yield
        finally:
            handler._calc_checksum = wrapped
    elif isinstance(handler, uh.PrefixWrapper):
        with patch_calc_min_rounds(handler.wrapped):
            yield
    else:
        yield
        return


def set_file(path, content):
    """set file to specified bytes"""
    if isinstance(content, str):
        content = content.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(content)


def get_file(path):
    """read file as bytes"""
    with open(path, "rb") as fh:
        return fh.read()


def tonn(source):
    """convert native string to non-native string"""
    if isinstance(source, str):
        return source.encode("utf-8")
    return source


def hb(source):
    """
    helper for represent byte strings in hex.

    usage: ``hb("deadbeef23")``
    """
    return unhexlify(re.sub(r"\s", "", source))


def limit(value, lower, upper):
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def quicksleep(delay):
    """because time.sleep() doesn't even have 10ms accuracy on some OSes"""
    start = tick()
    while tick() - start < delay:
        pass


def time_call(func, setup=None, maxtime=1, bestof=10):
    """
    timeit() wrapper which tries to get as accurate a measurement as possible w/in maxtime seconds.

    :returns:
        ``(avg_seconds_per_call, log10_number_of_repetitions)``
    """
    from timeit import Timer

    timer = Timer(func, setup=setup or "")
    number = 1
    end = tick() + maxtime
    while True:
        delta = min(timer.repeat(bestof, number))
        if tick() >= end:
            return delta / number, int(math.log10(number))
        number *= 10


def run_with_fixed_seeds(count=128, master_seed=0x243F6A8885A308D3):
    """
    decorator run test method w/ multiple fixed seeds.
    """

    def builder(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            rng = random.Random(master_seed)
            for _ in range(count):
                kwds["seed"] = rng.getrandbits(32)
                func(*args, **kwds)

        return wrapper

    return builder


class TestCase(unittest.TestCase):
    """passlib-specific test case class

    this class adds a number of features to the standard TestCase...
    * common prefix for all test descriptions
    * resets warnings filter & registry for every test
    * tweaks to message formatting
    * __msg__ kwd added to assertRaises()
    * suite of methods for matching against warnings
    """

    # ---------------------------------------------------------------
    # make it easy for test cases to add common prefix to shortDescription
    # ---------------------------------------------------------------

    # string prepended to all tests in TestCase
    descriptionPrefix: str | None = None

    def shortDescription(self):
        """wrap shortDescription() method to prepend descriptionPrefix"""
        desc = super().shortDescription()
        prefix = self.descriptionPrefix
        if prefix:
            desc = f"{prefix}: {desc or str(self)}"
        return desc

    # ---------------------------------------------------------------
    # hack things so nose and ut2 both skip subclasses who have
    # "__unittest_skip=True" set, or whose names start with "_"
    # ---------------------------------------------------------------
    @classproperty
    def __unittest_skip__(cls):
        # NOTE: this attr is technically a unittest internal detail.
        name = cls.__name__
        return name.startswith("_") or getattr(cls, f"_{name}__unittest_skip", False)

    @classproperty
    def __test__(cls):
        # make nose just proxy __unittest_skip__
        return not cls.__unittest_skip__

    # flag to skip *this* class
    __unittest_skip = True

    # ---------------------------------------------------------------
    # reset warning filters & registry before each test
    # ---------------------------------------------------------------

    # flag to reset all warning filters & ignore state
    resetWarningState = True

    def setUp(self):
        super().setUp()
        self.setUpWarnings()
        # have uh.debug_only_repr() return real values for duration of test
        self.patchAttr(exc, "ENABLE_DEBUG_ONLY_REPR", True)

    def setUpWarnings(self):
        """helper to init warning filters before subclass setUp()"""
        if self.resetWarningState:
            ctx = reset_warnings()
            ctx.__enter__()
            self.addCleanup(ctx.__exit__)

            # ignore security warnings, tests may deliberately cause these
            # TODO: may want to filter out a few of this, but not blanket filter...
            # warnings.filterwarnings("ignore", category=exc.PasslibSecurityWarning)

            # ignore warnings about PasswordHash features deprecated in 1.7
            # TODO: should be cleaned in 2.0, when support will be dropped.
            #       should be kept until then, so we test the legacy paths.
            warnings.filterwarnings(
                "ignore",
                r"the method .*\.(encrypt|genconfig|genhash)\(\) is deprecated",
            )
            warnings.filterwarnings("ignore", r"the 'vary_rounds' option is deprecated")

    # ---------------------------------------------------------------
    # tweak message formatting so longMessage mode is only enabled
    # if msg ends with ":", and turn on longMessage by default.
    # ---------------------------------------------------------------
    longMessage = True

    def _formatMessage(self, msg, std):
        if self.longMessage and msg and msg.rstrip().endswith(":"):
            return f"{msg.rstrip()} {std}"
        return msg or std

    def require_stringprep(self):
        """helper to skip test if stringprep is missing"""
        from passlib.utils import stringprep

        if not stringprep:
            from passlib.utils import _stringprep_missing_reason

            raise self.skipTest(
                "not available - stringprep module is " + _stringprep_missing_reason
            )

    def require_TEST_MODE(self, level):
        """skip test for all PASSLIB_TEST_MODE values below <level>"""
        if not TEST_MODE(level):
            raise self.skipTest(f"requires >= {level!r} test mode")

    #: global thread lock for random state
    #: XXX: could split into global & per-instance locks if need be
    _random_global_lock = threading.Lock()

    #: cache of global seed value, initialized on first call to getRandom()
    _random_global_seed = None

    #: per-instance cache of name -> RNG
    _random_cache = None

    def getRandom(self, name="default", seed=None):
        """
        Return a :class:`random.Random` object for current test method to use.
        Within an instance, multiple calls with the same name will return
        the same object.

        When first created, each RNG will be seeded with value derived from
        a global seed, the test class module & name, the current test method name,
        and the **name** parameter.

        The global seed taken from the $RANDOM_TEST_SEED env var,
        the $PYTHONHASHSEED env var, or a randomly generated the
        first time this method is called. In all cases, the value
        is logged for reproducibility.

        :param name:
            name to uniquely identify separate RNGs w/in a test
            (e.g. for threaded tests).

        :param seed:
            override global seed when initialzing rng.

        :rtype: random.Random
        """
        # check cache
        cache = self._random_cache
        if cache and name in cache:
            return cache[name]

        with self._random_global_lock:
            # check cache again, and initialize it
            cache = self._random_cache
            if cache and name in cache:
                return cache[name]
            if not cache:
                cache = self._random_cache = {}

            # init global seed
            global_seed = seed or TestCase._random_global_seed
            if global_seed is None:
                # NOTE: checking PYTHONHASHSEED, because if that's set,
                #       the test runner wants something reproducible.
                global_seed = TestCase._random_global_seed = int(
                    os.environ.get("RANDOM_TEST_SEED")
                    or os.environ.get("PYTHONHASHSEED")
                    or sys_rng.getrandbits(32)
                )
                # XXX: would it be better to print() this?
                log.info("using RANDOM_TEST_SEED=%d", global_seed)

            # create seed
            cls = type(self)
            source = "\n".join(
                [
                    str(global_seed),
                    cls.__module__,
                    cls.__name__,
                    self._testMethodName,
                    name,
                ]
            )
            digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
            seed = int(digest[:16], 16)

            # create rng
            value = cache[name] = random.Random(seed)
            return value

    @contextlib.contextmanager
    def subTest(self, *args, **kwds):
        """
        wrapper for .subTest() which traps SkipTest errors.
        (see source for details)
        """

        # this function works around issue that as 2020-10-08,
        #   .subTest() doesn't play nicely w/ .skipTest();
        #   and also makes it hard to debug which subtest had a failure.
        #   (see https://bugs.python.org/issue25894 and https://bugs.python.org/issue35327)
        #   this method traps skipTest exceptions, and adds some logging to help debug
        #   which subtest caused the issue.

        # setup way to log subtest info
        # XXX: would like better way to inject messages into test output;
        #      but this at least gets us something for debugging...
        # NOTE: this hack will miss parent params if called from nested .subTest()
        def _render_title(_msg=None, **params):
            out = f"[{_msg}] " if _msg else ""
            if params:
                out += "({})".format(
                    " ".join("{}={!r}".format(*tuple(item)) for item in params.items())
                )
            return out.strip() or "<subtest>"

        test_log = self.getLogger()
        title = _render_title(*args, **kwds)

        # run the subtest
        ctx = super().subTest(*args, **kwds)
        with ctx:
            test_log.info("running subtest: %s", title)
            try:
                yield
            except SkipTest:
                # silence "SkipTest" exceptions, want to keep running next subtest.
                test_log.info("subtest skipped: %s", title)
                # XXX: should revisit whether latest py3 version of UTs handle this ok,
                #      meaning it's safe to re-raise this.
                return
            except Exception as err:
                # log unhandled exception occurred
                # (assuming traceback will be reported up higher, so not bothering here)
                test_log.warning(
                    "subtest failed: %s: %s: %r", title, type(err).__name__, str(err)
                )
                raise

        # XXX: check for "failed" state in ``self._outcome`` before writing this?
        test_log.info("subtest passed: %s", title)

    _mktemp_queue = None

    def mktemp(self, *args, **kwds):
        """create temp file that's cleaned up at end of test"""
        fd, path = tempfile.mkstemp(*args, **kwds)
        os.close(fd)
        queue = self._mktemp_queue
        if queue is None:
            queue = self._mktemp_queue = []

            def cleaner():
                for path in queue:
                    if os.path.exists(path):
                        os.remove(path)
                del queue[:]

            self.addCleanup(cleaner)
        queue.append(path)
        return path

    def patchAttr(self, obj, attr, value, require_existing=True, wrap=False):
        """monkeypatch object value, restoring original value on cleanup"""
        try:
            orig = getattr(obj, attr)
        except AttributeError:
            if require_existing:
                raise

            def cleanup():
                with contextlib.suppress(AttributeError):
                    delattr(obj, attr)

            self.addCleanup(cleanup)
        else:
            self.addCleanup(setattr, obj, attr, orig)
        if wrap:
            value = partial(value, orig)
            wraps(orig)(value)
        setattr(obj, attr, value)

    def getLogger(self):
        """
        return logger named after current test.
        """
        cls = type(self)
        path = cls.__module__ + "." + cls.__qualname__
        name = self._testMethodName
        if name:
            path = path + "." + name
        return logging.getLogger(path)


RESERVED_BACKEND_NAMES = ["any", "default"]


def doesnt_require_backend(func):
    """
    decorator for HandlerCase.create_backend_case() --
    used to decorate methods that should be run even if backend isn't present
    (by default, full test suite is skipped when backend is missing)

    NOTE: tests decorated with this should not rely on handler have expected (or any!) backend.
    """
    func._doesnt_require_backend = True
    return func


class HandlerCase(TestCase):
    """base class for testing password hash handlers (esp passlib.utils.handlers subclasses)

    In order to use this to test a handler,
    create a subclass will all the appropriate attributes
    filled as listed in the example below,
    and run the subclass via unittest.

    .. todo::

        Document all of the options HandlerCase offers.

    .. note::

        This is subclass of :class:`unittest.TestCase`.
    """

    # ---------------------------------------------------------------
    # handler setup
    # ---------------------------------------------------------------

    # handler class to test [required]
    handler: type[PasswordHash] | PrefixWrapper | None = None

    # if set, run tests against specified backend
    backend: str | None = None

    # ---------------------------------------------------------------
    # test vectors
    # ---------------------------------------------------------------

    # list of (secret, hash) tuples which are known to be correct
    known_correct_hashes: list[Any] = []

    # list of (config, secret, hash) tuples are known to be correct
    known_correct_configs: list[tuple[str, str, str]] = []

    # list of (alt_hash, secret, hash) tuples, where alt_hash is a hash
    # using an alternate representation that should be recognized and verify
    # correctly, but should be corrected to match hash when passed through
    # genhash()
    known_alternate_hashes: list[tuple[str, str | tuple[str, ...], str]] = []

    # hashes so malformed they aren't even identified properly
    known_unidentified_hashes: list[str | bytes] = []

    # hashes which are identifiabled but malformed - they should identify()
    # as True, but cause an error when passed to genhash/verify.
    known_malformed_hashes: list[str | bytes] = []

    # list of (handler name, hash) pairs for other algorithm's hashes that
    # handler shouldn't identify as belonging to it this list should generally
    # be sufficient (if handler name in list, that entry will be skipped)
    known_other_hashes = [
        ("des_crypt", "6f8c114b58f2c"),
        ("md5_crypt", "$1$dOHYPKoP$tnxS1T8Q6VVn3kpV8cN6o."),
        (
            "sha512_crypt",
            "$6$rounds=123456$asaltof16chars..$BtCwjqMJGx5hrJhZywW"
            "vt0RLE8uZ4oPwcelCjmw2kSYu.Ec6ycULevoBK25fs2xXgMNrCzIMVcgEJAstJeonj1",
        ),
    ]

    # passwords used to test basic hash behavior - generally
    # don't need to be overidden.
    stock_passwords = ["test", "\u20ac\u00a5$", b"\xe2\x82\xac\xc2\xa5$"]

    # ---------------------------------------------------------------
    # option flags
    # ---------------------------------------------------------------

    # whether hash is case insensitive
    # True, False, or special value "verify-only" (which indicates
    # hash contains case-sensitive portion, but verifies is case-insensitive)
    secret_case_insensitive: str | bool = False

    # flag if scheme accepts ALL hash strings (e.g. plaintext)
    accepts_all_hashes = False

    # flag if scheme has "is_disabled" set, and contains 'salted' data
    disabled_contains_salt = False

    # flag/hack to filter PasslibHashWarning issued by test_72_configs()
    filter_config_warnings = False

    # forbid certain characters in passwords
    @classproperty
    def forbidden_characters(cls):
        # anything that supports crypt() interface should forbid null chars,
        # since crypt() uses null-terminated strings.
        if "os_crypt" in getattr(cls.handler, "backends", ()):
            return b"\x00"
        return None

    __unittest_skip = True

    @property
    def descriptionPrefix(self):
        handler = self.handler
        name = handler.name
        if hasattr(handler, "get_backend"):
            name += f" ({handler.get_backend()} backend)"
        return name

    # ---------------------------------------------------------------
    # configuration helpers
    # ---------------------------------------------------------------
    @classmethod
    def iter_known_hashes(cls):
        """iterate through known (secret, hash) pairs"""
        for secret, hash in cls.known_correct_hashes:
            yield secret, hash
        for config, secret, hash in cls.known_correct_configs:
            yield secret, hash
        for alt, secret, hash in cls.known_alternate_hashes:
            yield secret, hash

    def get_sample_hash(self):
        """test random sample secret/hash pair"""
        known = list(self.iter_known_hashes())
        return self.getRandom().choice(known)

    # ---------------------------------------------------------------
    # test helpers
    # ---------------------------------------------------------------
    def check_verify(self, secret, hash, msg=None, negate=False):
        """helper to check verify() outcome, honoring is_disabled_handler"""
        result = self.do_verify(secret, hash)
        assert result is True or result is False, (
            f"verify() returned non-boolean value: {result!r}"
        )
        if self.handler.is_disabled or negate:
            if not result:
                return
            if not msg:
                msg = f"verify incorrectly returned True: secret={secret!r}, hash={hash!r}"
            raise self.failureException(msg)
        if result:
            return
        if not msg:
            msg = f"verify failed: secret={secret!r}, hash={hash!r}"
        raise self.failureException(msg)

    def check_returned_native_str(self, result, func_name):
        assert isinstance(result, str), (
            f"{func_name}() failed to return native string: {result!r}"
        )

    # ---------------------------------------------------------------
    # PasswordHash helpers - wraps all calls to PasswordHash api,
    # so that subclasses can fill in defaults and account for other specialized behavior
    # ---------------------------------------------------------------
    def populate_settings(self, kwds):
        """subclassable method to populate default settings"""
        # use lower rounds settings for certain test modes
        handler = self.handler
        if "rounds" in handler.setting_kwds and "rounds" not in kwds:
            mn = handler.min_rounds
            df = handler.default_rounds
            if TEST_MODE(max="quick"):
                # use minimum rounds for quick mode
                kwds["rounds"] = max(3, mn)
            else:
                # use default/16 otherwise
                factor = 3
                if getattr(handler, "rounds_cost", None) == "log2":
                    df -= factor
                else:
                    df //= 1 << factor
                kwds["rounds"] = max(3, mn, df)

    def populate_context(self, secret, kwds):
        """subclassable method allowing 'secret' to be encode context kwds"""
        return secret

    # TODO: rename to do_hash() to match new API
    def do_encrypt(
        self, secret, use_encrypt=False, handler=None, context=None, **settings
    ):
        """call handler's hash() method with specified options"""
        self.populate_settings(settings)
        if context is None:
            context = {}
        secret = self.populate_context(secret, context)
        if use_encrypt:
            # use legacy 1.6 api
            warnings_context = contextlib.nullcontext()
            if settings:
                context.update(**settings)
                warnings_context = pytest.warns(
                    match="passing settings to.*is deprecated"
                )
            with warnings_context:
                return (handler or self.handler).encrypt(secret, **context)
        else:
            # use 1.7 api
            return (handler or self.handler).using(**settings).hash(secret, **context)

    def do_verify(self, secret, hash, handler=None, **kwds):
        """call handler's verify method"""
        secret = self.populate_context(secret, kwds)
        return (handler or self.handler).verify(secret, hash, **kwds)

    def do_identify(self, hash):
        """call handler's identify method"""
        return self.handler.identify(hash)

    def do_genconfig(self, **kwds):
        """call handler's genconfig method with specified options"""
        self.populate_settings(kwds)
        return self.handler.genconfig(**kwds)

    def do_genhash(self, secret, config, **kwds):
        """call handler's genhash method with specified options"""
        secret = self.populate_context(secret, kwds)
        return self.handler.genhash(secret, config, **kwds)

    def do_stub_encrypt(self, handler=None, context=None, **settings):
        """
        return sample hash for handler, w/o caring if digest is valid
        (uses some monkeypatching to minimize digest calculation cost)
        """
        handler = (handler or self.handler).using(**settings)
        if context is None:
            context = {}
        secret = self.populate_context("", context)
        with patch_calc_min_rounds(handler):
            return handler.hash(secret, **context)

    # ---------------------------------------------------------------
    # automatically generate subclasses for testing specific backends,
    # and other backend helpers
    # ---------------------------------------------------------------

    #: default message used by _get_skip_backend_reason()
    _BACKEND_NOT_AVAILABLE = "backend not available"

    @classmethod
    def _get_skip_backend_reason(cls, backend):
        """
        helper for create_backend_case() --
        returns reason to skip backend, or None if backend should be tested
        """
        handler = cls.handler
        if not is_default_backend(handler, backend) and not TEST_MODE("full"):
            return "only default backend is being tested"
        if handler.has_backend(backend):
            return None
        return cls._BACKEND_NOT_AVAILABLE

    @classmethod
    def create_backend_case(cls, backend):
        handler = cls.handler
        name = handler.name
        assert hasattr(handler, "backends"), (
            "handler must support uh.HasManyBackends protocol"
        )
        assert backend in handler.backends, f"unknown backend: {backend!r}"
        bases = (cls,)
        if backend == "os_crypt":
            bases += (OsCryptMixin,)
        return type(
            f"{name}_{backend}_test",
            bases,
            dict(
                descriptionPrefix=f"{name} ({backend} backend)",
                backend=backend,
                _skip_backend_reason=cls._get_skip_backend_reason(backend),
                __module__=cls.__module__,
            ),
        )

    #: flag for setUp() indicating this class is disabled due to backend issue;
    #: this is only set for dynamic subclasses generated by create_backend_case()
    _skip_backend_reason = None

    def _test_requires_backend(self):
        """
        check if current test method decorated with doesnt_require_backend() helper
        """
        meth = getattr(self, self._testMethodName, None)
        return not getattr(meth, "_doesnt_require_backend", False)

    def setUp(self):
        # check if test is disabled due to missing backend;
        # and that it wasn't exempted via @doesnt_require_backend() decorator
        test_requires_backend = self._test_requires_backend()
        if test_requires_backend and self._skip_backend_reason:
            raise self.skipTest(self._skip_backend_reason)

        super().setUp()

        # if needed, select specific backend for duration of test
        # NOTE: skipping this if create_backend_case() signalled we're skipping backend
        #       (can only get here for @doesnt_require_backend decorated methods)
        handler = self.handler
        backend = self.backend
        if backend:
            if not hasattr(handler, "set_backend"):
                raise RuntimeError("handler doesn't support multiple backends")
            try:
                self.addCleanup(handler.set_backend, handler.get_backend())
                handler.set_backend(backend)
            except uh.exc.MissingBackendError:
                if test_requires_backend:
                    raise
                # else test is decorated with @doesnt_require_backend, let it through.

        # patch some RNG references so they're reproducible.
        from passlib.utils import handlers

        self.patchAttr(handlers, "rng", self.getRandom("salt generator"))

    def test_01_required_attributes(self):
        """validate required attributes"""
        handler = self.handler

        def ga(name):
            return getattr(handler, name, None)

        #
        # name should be a str, and valid
        #
        name = ga("name")
        assert name, "name not defined:"
        assert isinstance(name, str), "name must be native str"
        assert name.lower() == name, "name not lower-case:"
        assert re.match("^[a-z0-9_]+$", name), (
            f"name must be alphanum + underscore: {name!r}"
        )

        #
        # setting_kwds should be specified
        #
        settings = ga("setting_kwds")
        assert settings is not None, "setting_kwds must be defined:"
        assert isinstance(settings, tuple), "setting_kwds must be a tuple:"

        #
        # context_kwds should be specified
        #
        context = ga("context_kwds")
        assert context is not None, "context_kwds must be defined:"
        assert isinstance(context, tuple), "context_kwds must be a tuple:"

        # XXX: any more checks needed?

    def test_02_config_workflow(self):
        """test basic config-string workflow

        this tests that genconfig() returns the expected types,
        and that identify() and genhash() handle the result correctly.
        """
        #
        # genconfig() should return native string.
        # NOTE: prior to 1.7 could return None, but that's no longer allowed.
        #
        config = self.do_genconfig()
        self.check_returned_native_str(config, "genconfig")

        #
        # genhash() should always accept genconfig()'s output,
        # whether str OR None.
        #
        result = self.do_genhash("stub", config)
        self.check_returned_native_str(result, "genhash")

        #
        # verify() should never accept config strings
        #

        # NOTE: changed as of 1.7 -- previously, .verify() should have
        #       rejected partial config strings returned by genconfig().
        #       as of 1.7, that feature is deprecated, and genconfig()
        #       always returns a hash (usually of the empty string)
        #       so verify should always accept it's output
        self.do_verify("", config)  # usually true, but not required by protocol

        #
        # identify() should positively identify config strings if not None.
        #

        # NOTE: changed as of 1.7 -- genconfig() previously might return None,
        #       now must always return valid hash
        assert self.do_identify(config), (
            f"identify() failed to identify genconfig() output: {config!r}"
        )

    def test_02_using_workflow(self):
        """test basic using() workflow"""
        handler = self.handler
        subcls = handler.using()
        assert subcls is not handler
        assert subcls.name == handler.name
        # NOTE: other info attrs should match as well, just testing basic behavior.
        # NOTE: mixin-specific args like using(min_rounds=xxx) tested later.

    def test_03_hash_workflow(self, use_16_legacy=False):
        """test basic hash-string workflow.

        this tests that hash()'s hashes are accepted
        by verify() and identify(), and regenerated correctly by genhash().
        the test is run against a couple of different stock passwords.
        """
        wrong_secret = "stub"
        for secret in self.stock_passwords:
            #
            # hash() should generate native str hash
            #
            result = self.do_encrypt(secret, use_encrypt=use_16_legacy)
            self.check_returned_native_str(result, "hash")

            #
            # verify() should work only against secret
            #
            self.check_verify(secret, result)
            self.check_verify(wrong_secret, result, negate=True)

            #
            # genhash() should reproduce original hash
            #
            other = self.do_genhash(secret, result)
            self.check_returned_native_str(other, "genhash")
            if self.handler.is_disabled and self.disabled_contains_salt:
                assert other != result, (
                    "genhash() failed to salt result "
                    f"hash: secret={secret!r} hash={result!r}: result={other!r}"
                )
            else:
                assert other == result, (
                    "genhash() failed to reproduce "
                    f"hash: secret={secret!r} hash={result!r}: result={other!r}"
                )

            #
            # genhash() should NOT reproduce original hash for wrong password
            #
            other = self.do_genhash(wrong_secret, result)
            self.check_returned_native_str(other, "genhash")
            if self.handler.is_disabled and not self.disabled_contains_salt:
                assert other == result, (
                    "genhash() failed to reproduce "
                    f"disabled-hash: secret={secret!r} hash={result!r} other_secret={wrong_secret!r}: result={other!r}"
                )
            else:
                assert other != result, (
                    "genhash() duplicated "
                    f"hash: secret={secret!r} hash={result!r} wrong_secret={wrong_secret!r}: result={other!r}"
                )

            #
            # identify() should positively identify hash
            #
            assert self.do_identify(result)

    def test_03_legacy_hash_workflow(self):
        """test hash-string workflow with legacy .encrypt() & .genhash() methods"""
        self.test_03_hash_workflow(use_16_legacy=True)

    def test_04_hash_types(self):
        """test hashes can be unicode or bytes"""
        # this runs through workflow similar to 03, but wraps
        # everything using tonn() so we test unicode under py2,
        # and bytes under py3.

        # hash using non-native secret
        result = self.do_encrypt(tonn("stub"))
        self.check_returned_native_str(result, "hash")

        # verify using non-native hash
        self.check_verify("stub", tonn(result))

        # verify using non-native hash AND secret
        self.check_verify(tonn("stub"), tonn(result))

        # genhash using non-native hash
        other = self.do_genhash("stub", tonn(result))
        self.check_returned_native_str(other, "genhash")
        if self.handler.is_disabled and self.disabled_contains_salt:
            assert other != result
        else:
            assert other == result

        # genhash using non-native hash AND secret
        other = self.do_genhash(tonn("stub"), tonn(result))
        self.check_returned_native_str(other, "genhash")
        if self.handler.is_disabled and self.disabled_contains_salt:
            assert other != result
        else:
            assert other == result

        # identify using non-native hash
        assert self.do_identify(tonn(result))

    def test_05_backends(self):
        """test multi-backend support"""

        # check that handler supports multiple backends
        handler = self.handler
        if not hasattr(handler, "set_backend"):
            raise self.skipTest("handler only has one backend")

        # add cleanup func to restore old backend
        self.addCleanup(handler.set_backend, handler.get_backend())

        # run through each backend, make sure it works
        for backend in handler.backends:
            #
            # validate backend name
            #
            assert isinstance(backend, str)
            assert backend not in RESERVED_BACKEND_NAMES, (
                f"invalid backend name: {backend!r}"
            )

            #
            # ensure has_backend() returns bool value
            #
            ret = handler.has_backend(backend)
            if ret is True:
                # verify backend can be loaded
                handler.set_backend(backend)
                assert handler.get_backend() == backend

            elif ret is False:
                # verify backend CAN'T be loaded
                with pytest.raises(MissingBackendError):
                    handler.set_backend(backend)

            else:
                # didn't return boolean object. commonly fails due to
                # use of 'classmethod' decorator instead of 'classproperty'
                raise TypeError(
                    f"has_backend({backend!r}) returned invalid value: {ret!r}"
                )

    def require_salt(self):
        if "salt" not in self.handler.setting_kwds:
            raise self.skipTest("handler doesn't have salt")

    def require_salt_info(self):
        self.require_salt()
        if not has_salt_info(self.handler):
            raise self.skipTest("handler doesn't provide salt info")

    def test_10_optional_salt_attributes(self):
        """validate optional salt attributes"""
        self.require_salt_info()
        AssertionError = self.failureException
        cls = self.handler

        # check max_salt_size
        mx_set = cls.max_salt_size is not None
        if mx_set and cls.max_salt_size < 1:
            raise AssertionError("max_salt_chars must be >= 1")

        # check min_salt_size
        if cls.min_salt_size < 0:
            raise AssertionError("min_salt_chars must be >= 0")
        if mx_set and cls.min_salt_size > cls.max_salt_size:
            raise AssertionError("min_salt_chars must be <= max_salt_chars")

        # check default_salt_size
        if cls.default_salt_size < cls.min_salt_size:
            raise AssertionError("default_salt_size must be >= min_salt_size")
        if mx_set and cls.default_salt_size > cls.max_salt_size:
            raise AssertionError("default_salt_size must be <= max_salt_size")

        # check for 'salt_size' keyword
        # NOTE: skipping warning if default salt size is already maxed out
        #       (might change that in future)
        if "salt_size" not in cls.setting_kwds and (
            not mx_set or cls.default_salt_size < cls.max_salt_size
        ):
            warn(
                f"{cls.name}: hash handler supports range of salt sizes, "
                "but doesn't offer 'salt_size' setting"
            )

        # check salt_chars & default_salt_chars
        if cls.salt_chars:
            if not cls.default_salt_chars:
                raise AssertionError("default_salt_chars must not be empty")
            for c in cls.default_salt_chars:
                if c not in cls.salt_chars:
                    raise AssertionError(
                        f"default_salt_chars must be subset of salt_chars: {c!r} not in salt_chars"
                    )
        elif not cls.default_salt_chars:
            raise AssertionError(
                "default_salt_chars MUST be specified if salt_chars is empty"
            )

    @property
    def salt_bits(self):
        """calculate number of salt bits in hash"""
        # XXX: replace this with bitsize() method?
        handler = self.handler
        assert has_salt_info(handler), "need explicit bit-size for " + handler.name

        # FIXME: this may be off for case-insensitive hashes, but that accounts
        # for ~1 bit difference, which is good enough for test_11()
        return int(
            handler.default_salt_size * math.log2(len(handler.default_salt_chars))
        )

    def test_11_unique_salt(self):
        """test hash() / genconfig() creates new salt each time"""
        self.require_salt()
        # odds of picking 'n' identical salts at random is '(.5**salt_bits)**n'.
        # we want to pick the smallest N needed s.t. odds are <1/10**d, just
        # to eliminate false-positives. which works out to n>3.33+d-salt_bits.
        # for 1/1e12 odds, n=1 is sufficient for most hashes, but a few border cases (e.g.
        # cisco_type7) have < 16 bits of salt, requiring more.
        samples = max(1, 4 + 12 - self.salt_bits)

        def sampler(func):
            value1 = func()
            for _ in range(samples):
                value2 = func()
                if value1 != value2:
                    return
            raise self.failureException(
                "failed to find different salt after %d samples" % (samples,)
            )

        sampler(self.do_genconfig)
        sampler(lambda: self.do_encrypt("stub"))

    def test_12_min_salt_size(self):
        """test hash() / genconfig() honors min_salt_size"""
        self.require_salt_info()

        handler = self.handler
        salt_char = handler.salt_chars[0:1]
        min_size = handler.min_salt_size

        #
        # check min is accepted
        #
        s1 = salt_char * min_size
        self.do_genconfig(salt=s1)

        self.do_encrypt("stub", salt_size=min_size)

        #
        # check min-1 is rejected
        #
        if min_size > 0:
            with pytest.raises(ValueError):
                self.do_genconfig(salt=s1[:-1])

        with pytest.raises(ValueError):
            self.do_encrypt("stub", salt_size=min_size - 1)

    def test_13_max_salt_size(self):
        """test hash() / genconfig() honors max_salt_size"""
        self.require_salt_info()

        handler = self.handler
        max_size = handler.max_salt_size
        salt_char = handler.salt_chars[0:1]

        # NOTE: skipping this for hashes like argon2 since max_salt_size takes WAY too much memory
        if max_size is None or max_size > (1 << 20):
            #
            # if it's not set, salt should never be truncated; so test it
            # with an unreasonably large salt.
            #
            s1 = salt_char * 1024
            c1 = self.do_stub_encrypt(salt=s1)
            c2 = self.do_stub_encrypt(salt=s1 + salt_char)
            assert c1 != c2

            self.do_stub_encrypt(salt_size=1024)

        else:
            #
            # check max size is accepted
            #
            s1 = salt_char * max_size
            c1 = self.do_stub_encrypt(salt=s1)

            self.do_stub_encrypt(salt_size=max_size)

            #
            # check max size + 1 is rejected
            #
            s2 = s1 + salt_char
            with pytest.raises(ValueError):
                self.do_stub_encrypt(salt=s2)

            with pytest.raises(ValueError):
                self.do_stub_encrypt(salt_size=max_size + 1)

            #
            # should accept too-large salt in relaxed mode
            #
            if has_relaxed_setting(handler):
                with warnings.catch_warnings(
                    record=True
                ):  # issues passlibhandlerwarning
                    c2 = self.do_stub_encrypt(salt=s2, relaxed=True)
                assert c2 == c1

            #
            # if min_salt supports it, check smaller than mx is NOT truncated
            #
            if handler.min_salt_size < max_size:
                c3 = self.do_stub_encrypt(salt=s1[:-1])
                assert c3 != c1

    # whether salt should be passed through bcrypt repair function
    fuzz_salts_need_bcrypt_repair = False

    def prepare_salt(self, salt):
        """prepare generated salt"""
        if self.fuzz_salts_need_bcrypt_repair:
            from passlib.utils.binary import bcrypt64

            salt = bcrypt64.repair_unused(salt)
        return salt

    def test_14_salt_chars(self):
        """test hash() honors salt_chars"""
        self.require_salt_info()

        handler = self.handler
        mx = handler.max_salt_size
        mn = handler.min_salt_size
        cs = handler.salt_chars
        raw = isinstance(cs, bytes)

        # make sure all listed chars are accepted
        for salt in batch(cs, mx or 32):
            if len(salt) < mn:
                salt = repeat_string(salt, mn)
            salt = self.prepare_salt(salt)
            self.do_stub_encrypt(salt=salt)

        # check some invalid salt chars, make sure they're rejected
        source = "\x00\xff"
        if raw:
            source = source.encode("latin-1")
        chunk = max(mn, 1)
        for c in source:
            if c not in cs:
                with pytest.raises(ValueError):
                    self.do_stub_encrypt(
                        salt=c * chunk,
                    )

    @property
    def salt_type(self):
        """hack to determine salt keyword's datatype"""
        # NOTE: cisco_type7 uses 'int'
        if getattr(self.handler, "_salt_is_bytes", False):
            return bytes
        return str

    def test_15_salt_type(self):
        """test non-string salt values"""
        self.require_salt()
        salt_type = self.salt_type
        salt_size = getattr(self.handler, "min_salt_size", 0) or 8

        # should always throw error for random class.
        class fake:
            pass

        with pytest.raises(TypeError):
            self.do_encrypt("stub", salt=fake())

        # unicode should be accepted only if salt_type is unicode.
        if salt_type is not str:
            with pytest.raises(TypeError):
                self.do_encrypt("stub", salt="x" * salt_size)

        # bytes should be accepted only if salt_type is bytes
        if salt_type is not bytes:
            with pytest.raises(TypeError):
                self.do_encrypt("stub", salt=b"x" * salt_size)

    def test_using_salt_size(self):
        """Handler.using() -- default_salt_size"""
        self.require_salt_info()

        handler = self.handler
        mn = handler.min_salt_size
        mx = handler.max_salt_size
        df = handler.default_salt_size

        # should prevent setting below handler limit
        with pytest.raises(ValueError):
            handler.using(default_salt_size=-1)
        with pytest.warns(PasslibHashWarning):
            temp = handler.using(default_salt_size=-1, relaxed=True)
        assert temp.default_salt_size == mn

        # should prevent setting above handler limit
        if mx:
            with pytest.raises(ValueError):
                handler.using(default_salt_size=mx + 1)
            with pytest.warns(PasslibHashWarning):
                temp = handler.using(default_salt_size=mx + 1, relaxed=True)
            assert temp.default_salt_size == mx

        # try setting to explicit value
        if mn != mx:
            temp = handler.using(default_salt_size=mn + 1)
            assert temp.default_salt_size == mn + 1
            assert handler.default_salt_size == df

            temp = handler.using(default_salt_size=mn + 2)
            assert temp.default_salt_size == mn + 2
            assert handler.default_salt_size == df

        # accept strings
        ref = mn if mn == mx else mn + 1
        temp = handler.using(default_salt_size=str(ref))
        assert temp.default_salt_size == ref

        # reject invalid strings
        with pytest.raises(ValueError):
            handler.using(default_salt_size=str(ref) + "xxx")

        # honor 'salt_size' alias
        temp = handler.using(salt_size=ref)
        assert temp.default_salt_size == ref

    def require_rounds_info(self):
        if not has_rounds_info(self.handler):
            raise self.skipTest("handler lacks rounds attributes")

    def test_20_optional_rounds_attributes(self):
        """validate optional rounds attributes"""
        self.require_rounds_info()

        cls = self.handler
        AssertionError = self.failureException

        # check max_rounds
        if cls.max_rounds is None:
            raise AssertionError("max_rounds not specified")
        if cls.max_rounds < 1:
            raise AssertionError("max_rounds must be >= 1")

        # check min_rounds
        if cls.min_rounds < 0:
            raise AssertionError("min_rounds must be >= 0")
        if cls.min_rounds > cls.max_rounds:
            raise AssertionError("min_rounds must be <= max_rounds")

        # check default_rounds
        if cls.default_rounds is not None:
            if cls.default_rounds < cls.min_rounds:
                raise AssertionError("default_rounds must be >= min_rounds")
            if cls.default_rounds > cls.max_rounds:
                raise AssertionError("default_rounds must be <= max_rounds")

        # check rounds_cost
        if cls.rounds_cost not in rounds_cost_values:
            raise AssertionError(f"unknown rounds cost constant: {cls.rounds_cost!r}")

    def test_21_min_rounds(self):
        """test hash() / genconfig() honors min_rounds"""
        self.require_rounds_info()
        handler = self.handler
        min_rounds = handler.min_rounds

        # check min is accepted
        self.do_genconfig(rounds=min_rounds)
        self.do_encrypt("stub", rounds=min_rounds)

        # check min-1 is rejected
        with pytest.raises(ValueError):
            self.do_genconfig(rounds=min_rounds - 1)
        with pytest.raises(ValueError):
            self.do_encrypt("stub", rounds=min_rounds - 1)

        # TODO: check relaxed mode clips min-1

    def test_21b_max_rounds(self):
        """test hash() / genconfig() honors max_rounds"""
        self.require_rounds_info()
        handler = self.handler
        max_rounds = handler.max_rounds

        if max_rounds is not None:
            # check max+1 is rejected
            with pytest.raises(ValueError):
                self.do_genconfig(rounds=max_rounds + 1)
            with pytest.raises(ValueError):
                self.do_encrypt("stub", rounds=max_rounds + 1)

        # handle max rounds
        if max_rounds is None:
            self.do_stub_encrypt(rounds=(1 << 31) - 1)
        else:
            self.do_stub_encrypt(rounds=max_rounds)

            # TODO: check relaxed mode clips max+1

    # --------------------------------------------------------------------------------------
    # HasRounds.using() / .needs_update() -- desired rounds limits
    # --------------------------------------------------------------------------------------
    def _create_using_rounds_helper(self):
        """
        setup test helpers for testing handler.using()'s rounds parameters.
        """
        self.require_rounds_info()
        handler = self.handler

        if handler.name == "bsdi_crypt":
            # hack to bypass bsdi-crypt's "odd rounds only" behavior, messes up this test
            orig_handler = handler
            handler = handler.using()
            handler._generate_rounds = classmethod(
                lambda cls: super(orig_handler, cls)._generate_rounds()
            )

        # create some fake values to test with
        orig_min_rounds = handler.min_rounds
        orig_max_rounds = handler.max_rounds
        orig_default_rounds = handler.default_rounds
        medium = ((orig_max_rounds or 9999) + orig_min_rounds) // 2
        if medium == orig_default_rounds:
            medium += 1
        small = (orig_min_rounds + medium) // 2
        large = ((orig_max_rounds or 9999) + medium) // 2

        if handler.name == "bsdi_crypt":
            # hack to avoid even numbered rounds
            small |= 1
            medium |= 1
            large |= 1
            adj = 2
        else:
            adj = 1

        # create a subclass with small/medium/large as new default desired values
        with no_warnings():
            subcls = handler.using(
                min_desired_rounds=small,
                max_desired_rounds=large,
                default_rounds=medium,
            )

        # return helpers
        return handler, subcls, small, medium, large, adj

    def test_has_rounds_using_harness(self):
        """
        HasRounds.using() -- sanity check test harness
        """
        # setup helpers
        self.require_rounds_info()
        handler = self.handler
        orig_min_rounds = handler.min_rounds
        orig_max_rounds = handler.max_rounds
        orig_default_rounds = handler.default_rounds
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()

        # shouldn't affect original handler at all
        assert handler.min_rounds == orig_min_rounds
        assert handler.max_rounds == orig_max_rounds
        assert handler.min_desired_rounds is None
        assert handler.max_desired_rounds is None
        assert handler.default_rounds == orig_default_rounds

        # should affect subcls' desired value, but not hard min/max
        assert subcls.min_rounds == orig_min_rounds
        assert subcls.max_rounds == orig_max_rounds
        assert subcls.default_rounds == medium
        assert subcls.min_desired_rounds == small
        assert subcls.max_desired_rounds == large

    def test_has_rounds_using_w_min_rounds(self):
        """
        HasRounds.using() -- min_rounds / min_desired_rounds
        """
        # setup helpers
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()
        orig_min_rounds = handler.min_rounds
        orig_max_rounds = handler.max_rounds

        # .using() should clip values below valid minimum, w/ warning
        if orig_min_rounds > 0:
            with pytest.raises(ValueError):
                handler.using(min_desired_rounds=orig_min_rounds - adj)
            with pytest.warns(PasslibHashWarning):
                temp = handler.using(
                    min_desired_rounds=orig_min_rounds - adj, relaxed=True
                )
            assert temp.min_desired_rounds == orig_min_rounds

        # .using() should clip values above valid maximum, w/ warning
        if orig_max_rounds:
            with pytest.raises(ValueError):
                handler.using(min_desired_rounds=orig_max_rounds + adj)
            with pytest.warns(PasslibHashWarning):
                temp = handler.using(
                    min_desired_rounds=orig_max_rounds + adj, relaxed=True
                )
            assert temp.min_desired_rounds == orig_max_rounds

        # .using() should allow values below previous desired minimum, w/o warning
        with no_warnings():
            temp = subcls.using(min_desired_rounds=small - adj)
        assert temp.min_desired_rounds == small - adj

        # .using() should allow values w/in previous range
        temp = subcls.using(min_desired_rounds=small + 2 * adj)
        assert temp.min_desired_rounds == small + 2 * adj

        # .using() should allow values above previous desired maximum, w/o warning
        with no_warnings():
            temp = subcls.using(min_desired_rounds=large + adj)
        assert temp.min_desired_rounds == large + adj

        # hash() etc should allow explicit values below desired minimum
        # NOTE: formerly issued a warning in passlib 1.6, now just a wrapper for .using()
        assert get_effective_rounds(subcls, small + adj) == small + adj
        assert get_effective_rounds(subcls, small) == small
        with no_warnings():
            assert get_effective_rounds(subcls, small - adj) == small - adj

        # 'min_rounds' should be treated as alias for 'min_desired_rounds'
        temp = handler.using(min_rounds=small)
        assert temp.min_desired_rounds == small

        # should be able to specify strings
        temp = handler.using(min_rounds=str(small))
        assert temp.min_desired_rounds == small

        # invalid strings should cause error
        with pytest.raises(ValueError):
            handler.using(min_rounds=str(small) + "xxx")

    def test_has_rounds_replace_w_max_rounds(self):
        """
        HasRounds.using() -- max_rounds / max_desired_rounds
        """
        # setup helpers
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()
        orig_min_rounds = handler.min_rounds
        orig_max_rounds = handler.max_rounds

        # .using() should clip values below valid minimum w/ warning
        if orig_min_rounds > 0:
            with pytest.raises(ValueError):
                handler.using(max_desired_rounds=orig_min_rounds - adj)
            with pytest.warns(PasslibHashWarning):
                temp = handler.using(
                    max_desired_rounds=orig_min_rounds - adj, relaxed=True
                )
            assert temp.max_desired_rounds == orig_min_rounds

        # .using() should clip values above valid maximum, w/ warning
        if orig_max_rounds:
            with pytest.raises(ValueError):
                handler.using(max_desired_rounds=orig_max_rounds + adj)
            with pytest.warns(PasslibHashWarning):
                temp = handler.using(
                    max_desired_rounds=orig_max_rounds + adj, relaxed=True
                )
            assert temp.max_desired_rounds == orig_max_rounds

        # .using() should clip values below previous minimum, w/ warning
        with pytest.warns(PasslibConfigWarning):
            temp = subcls.using(max_desired_rounds=small - adj)
        assert temp.max_desired_rounds == small

        # .using() should reject explicit min > max
        with pytest.raises(ValueError):
            subcls.using(
                min_desired_rounds=medium + adj,
                max_desired_rounds=medium - adj,
            )

        # .using() should allow values w/in previous range
        temp = subcls.using(min_desired_rounds=large - 2 * adj)
        assert temp.min_desired_rounds == large - 2 * adj

        # .using() should allow values above previous desired maximum, w/o warning
        with no_warnings():
            temp = subcls.using(max_desired_rounds=large + adj)
        assert temp.max_desired_rounds == large + adj

        # hash() etc should allow explicit values above desired minimum, w/o warning
        # NOTE: formerly issued a warning in passlib 1.6, now just a wrapper for .using()
        assert get_effective_rounds(subcls, large - adj) == large - adj
        assert get_effective_rounds(subcls, large) == large
        with no_warnings():
            assert get_effective_rounds(subcls, large + adj) == large + adj

        # 'max_rounds' should be treated as alias for 'max_desired_rounds'
        temp = handler.using(max_rounds=large)
        assert temp.max_desired_rounds == large

        # should be able to specify strings
        temp = handler.using(max_desired_rounds=str(large))
        assert temp.max_desired_rounds == large

        # invalid strings should cause error
        with pytest.raises(ValueError):
            handler.using(max_desired_rounds=str(large) + "xxx")

    def test_has_rounds_using_w_default_rounds(self):
        """
        HasRounds.using() -- default_rounds
        """
        # setup helpers
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()
        orig_max_rounds = handler.max_rounds

        # XXX: are there any other cases that need testing?

        # implicit default rounds -- increase to min_rounds
        temp = subcls.using(min_rounds=medium + adj)
        assert temp.default_rounds == medium + adj

        # implicit default rounds -- decrease to max_rounds
        temp = subcls.using(max_rounds=medium - adj)
        assert temp.default_rounds == medium - adj

        # explicit default rounds below desired minimum
        # XXX: make this a warning if min is implicit?
        with pytest.raises(ValueError):
            subcls.using(default_rounds=small - adj)

        # explicit default rounds above desired maximum
        # XXX: make this a warning if max is implicit?
        if orig_max_rounds:
            with pytest.raises(ValueError):
                subcls.using(default_rounds=large + adj)

        # hash() etc should implicit default rounds, but get overridden
        assert get_effective_rounds(subcls) == medium
        assert get_effective_rounds(subcls, medium + adj) == medium + adj

        # should be able to specify strings
        temp = handler.using(default_rounds=str(medium))
        assert temp.default_rounds == medium

        # invalid strings should cause error
        with pytest.raises(ValueError):
            handler.using(default_rounds=str(medium) + "xxx")

    def test_has_rounds_using_w_rounds(self):
        """
        HasRounds.using() -- rounds
        """
        # setup helpers
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()

        # 'rounds' should be treated as fallback for min, max, and default
        temp = subcls.using(rounds=medium + adj)
        assert temp.min_desired_rounds == medium + adj
        assert temp.default_rounds == medium + adj
        assert temp.max_desired_rounds == medium + adj

        # 'rounds' should be treated as fallback for min, max, and default
        temp = subcls.using(
            rounds=medium + 1,
            min_rounds=small + adj,
            default_rounds=medium,
            max_rounds=large - adj,
        )
        assert temp.min_desired_rounds == small + adj
        assert temp.default_rounds == medium
        assert temp.max_desired_rounds == large - adj

    def test_has_rounds_using_w_vary_rounds_parsing(self):
        """
        HasRounds.using() -- vary_rounds parsing
        """
        # setup helpers
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()

        def parse(value):
            return subcls.using(vary_rounds=value).vary_rounds

        # floats should be preserved
        assert parse(0.1) == 0.1
        assert parse("0.1") == 0.1

        # 'xx%' should be converted to float
        assert parse("10%") == 0.1

        # ints should be preserved
        assert parse(1000) == 1000
        assert parse("1000") == 1000

        # float bounds should be enforced
        with pytest.raises(ValueError):
            parse(-0.1)
        with pytest.raises(ValueError):
            parse(1.1)

    def test_has_rounds_using_w_vary_rounds_generation(self):
        """
        HasRounds.using() -- vary_rounds generation
        """
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()

        def get_effective_range(cls):
            seen = set(get_effective_rounds(cls) for _ in range(1000))
            return min(seen), max(seen)

        def assert_rounds_range(vary_rounds, lower, upper):
            temp = subcls.using(vary_rounds=vary_rounds)
            seen_lower, seen_upper = get_effective_range(temp)
            assert seen_lower == lower, "vary_rounds had wrong lower limit:"
            assert seen_upper == upper, "vary_rounds had wrong upper limit:"

        # test static
        assert_rounds_range(0, medium, medium)
        assert_rounds_range("0%", medium, medium)

        # test absolute
        assert_rounds_range(adj, medium - adj, medium + adj)
        assert_rounds_range(50, max(small, medium - 50), min(large, medium + 50))

        # test relative - should shift over at 50% mark
        if handler.rounds_cost == "log2":
            # log rounds "50%" variance should only increase/decrease by 1 cost value
            assert_rounds_range("1%", medium, medium)
            assert_rounds_range("49%", medium, medium)
            assert_rounds_range("50%", medium - adj, medium)
        else:
            # for linear rounds, range is frequently so huge, won't ever see ends.
            # so we just check it's within an expected range.
            lower, upper = get_effective_range(subcls.using(vary_rounds="50%"))

            assert lower >= max(small, medium * 0.5)
            assert lower <= max(small, medium * 0.8)

            assert upper >= min(large, medium * 1.2)
            assert upper <= min(large, medium * 1.5)

    def test_has_rounds_using_and_needs_update(self):
        """
        HasRounds.using() -- desired_rounds + needs_update()
        """
        handler, subcls, small, medium, large, adj = self._create_using_rounds_helper()

        temp = subcls.using(min_desired_rounds=small + 2, max_desired_rounds=large - 2)

        # generate some sample hashes
        small_hash = self.do_stub_encrypt(subcls, rounds=small)
        medium_hash = self.do_stub_encrypt(subcls, rounds=medium)
        large_hash = self.do_stub_encrypt(subcls, rounds=large)

        # everything should be w/in bounds for original handler
        assert not subcls.needs_update(small_hash)
        assert not subcls.needs_update(medium_hash)
        assert not subcls.needs_update(large_hash)

        # small & large should require update for temp handler
        assert temp.needs_update(small_hash)
        assert not temp.needs_update(medium_hash)
        assert temp.needs_update(large_hash)

    def require_many_idents(self):
        handler = self.handler
        if not isinstance(handler, type) or not issubclass(handler, uh.HasManyIdents):
            raise self.skipTest("handler doesn't derive from HasManyIdents")

    def test_30_HasManyIdents(self):
        """validate HasManyIdents configuration"""
        cls = self.handler
        self.require_many_idents()

        # check settings
        assert "ident" in cls.setting_kwds

        # check ident_values list
        for value in cls.ident_values:
            assert isinstance(value, str), "cls.ident_values must be str:"
        assert len(cls.ident_values) > 1, "cls.ident_values must have 2+ elements:"

        # check default_ident value
        assert isinstance(cls.default_ident, str), "cls.default_ident must be str:"
        assert cls.default_ident in cls.ident_values, (
            "cls.default_ident must specify member of cls.ident_values"
        )

        # check optional aliases list
        if cls.ident_aliases:
            for alias, ident in cls.ident_aliases.items():
                assert isinstance(alias, str), (
                    "cls.ident_aliases keys must be str:"
                )  # XXX: allow ints?
                assert isinstance(ident, str), "cls.ident_aliases values must be str:"
                assert ident in cls.ident_values, (
                    f"cls.ident_aliases must map to cls.ident_values members: {ident!r}"
                )

        # check constructor validates ident correctly.
        handler = cls
        hash = self.get_sample_hash()[1]
        kwds = handler.parsehash(hash)
        del kwds["ident"]

        # ... accepts good ident
        handler(ident=cls.default_ident, **kwds)

        # ... requires ident w/o defaults
        with pytest.raises(TypeError):
            handler(**kwds)

        # ... supplies default ident
        handler(use_defaults=True, **kwds)

        # ... rejects bad ident
        with pytest.raises(ValueError):
            handler(ident="xXx", **kwds)

    # TODO: check various supported idents

    def test_has_many_idents_using(self):
        """HasManyIdents.using() -- 'default_ident' and 'ident' keywords"""
        self.require_many_idents()

        # pick alt ident to test with
        handler = self.handler
        orig_ident = handler.default_ident
        for alt_ident in handler.ident_values:
            if alt_ident != orig_ident:
                break
        else:
            raise AssertionError(
                f"expected to find alternate ident: default={orig_ident!r} values={handler.ident_values!r}"
            )

        def effective_ident(cls):
            cls = unwrap_handler(cls)
            return cls(use_defaults=True).ident

        # keep default if nothing else specified
        subcls = handler.using()
        assert subcls.default_ident == orig_ident

        # accepts alt ident
        subcls = handler.using(default_ident=alt_ident)
        assert subcls.default_ident == alt_ident
        assert handler.default_ident == orig_ident

        # check subcls actually *generates* default ident,
        # and that we didn't affect orig handler
        assert effective_ident(subcls) == alt_ident
        assert effective_ident(handler) == orig_ident

        # rejects bad ident
        with pytest.raises(ValueError):
            handler.using(default_ident="xXx")

        # honor 'ident' alias
        subcls = handler.using(ident=alt_ident)
        assert subcls.default_ident == alt_ident
        assert handler.default_ident == orig_ident

        # forbid both at same time
        with pytest.raises(TypeError):
            handler.using(default_ident=alt_ident, ident=alt_ident)

        # check ident aliases are being honored
        if handler.ident_aliases:
            for alias, ident in handler.ident_aliases.items():
                subcls = handler.using(ident=alias)
                assert subcls.default_ident == ident, f"alias {alias!r}:"

    def test_truncate_error_setting(self):
        """
        validate 'truncate_error' setting & related attributes
        """
        # If it doesn't have truncate_size set,
        # it shouldn't support truncate_error
        hasher = self.handler
        if hasher.truncate_size is None:
            assert "truncate_error" not in hasher.setting_kwds
            return

        # if hasher defaults to silently truncating,
        # it MUST NOT use .truncate_verify_reject,
        # because resulting hashes wouldn't verify!
        if not hasher.truncate_error:
            assert not hasher.truncate_verify_reject

        # if hasher doesn't have configurable policy,
        # it must throw error by default
        if "truncate_error" not in hasher.setting_kwds:
            assert hasher.truncate_error
            return

        # test value parsing
        def parse_value(value):
            return hasher.using(truncate_error=value).truncate_error

        assert parse_value(None) == hasher.truncate_error
        assert parse_value(True) is True
        assert parse_value("true") is True
        assert parse_value(False) is False
        assert parse_value("false") is False
        with pytest.raises(ValueError):
            parse_value("xxx")

    def test_secret_wo_truncate_size(self):
        """
        test no password size limits enforced (if truncate_size=None)
        """
        # skip if hasher has a maximum password size
        hasher = self.handler
        if hasher.truncate_size is not None:
            assert hasher.truncate_size >= 1
            raise self.skipTest("truncate_size is set")

        # NOTE: this doesn't do an exhaustive search to verify algorithm
        # doesn't have some cutoff point, it just tries
        # 1024-character string, and alters the last char.
        # as long as algorithm doesn't clip secret at point <1024,
        # the new secret shouldn't verify.

        # hash a 1024-byte secret
        secret = "too many secrets" * 16
        alt = "x"
        hash = self.do_encrypt(secret)

        # check that verify doesn't silently reject secret
        # (i.e. hasher mistakenly honors .truncate_verify_reject)
        verify_success = not hasher.is_disabled
        assert self.do_verify(secret, hash) == verify_success, (
            "verify rejected correct secret"
        )

        # alter last byte, should get different hash, which won't verify
        alt_secret = secret[:-1] + alt
        assert not self.do_verify(alt_secret, hash), "full password not used in digest"

    def test_secret_w_truncate_size(self):
        """
        test password size limits raise truncate_error (if appropriate)
        """
        # --------------------------------------------------
        # check if test is applicable
        # --------------------------------------------------
        handler = self.handler
        truncate_size = handler.truncate_size
        if not truncate_size:
            raise self.skipTest("truncate_size not set")

        # --------------------------------------------------
        # setup vars
        # --------------------------------------------------
        # try to get versions w/ and w/o truncate_error set.
        # set to None if policy isn't configruable
        size_error_type = exc.PasswordSizeError
        if "truncate_error" in handler.setting_kwds:
            without_error = handler.using(truncate_error=False)
            with_error = handler.using(truncate_error=True)
            size_error_type = exc.PasswordTruncateError
        elif handler.truncate_error:
            without_error = None
            with_error = handler
        else:
            # NOTE: this mode is currently an error in test_truncate_error_setting()
            without_error = handler
            with_error = None

        # create some test secrets
        base = "too many secrets"
        alt = "x"  # char that's not in base, used to mutate test secrets
        long_secret = repeat_string(base, truncate_size + 1)
        short_secret = long_secret[:-1]
        alt_long_secret = long_secret[:-1] + alt
        alt_short_secret = short_secret[:-1] + alt

        # init flags
        short_verify_success = not handler.is_disabled
        long_verify_success = (
            short_verify_success and not handler.truncate_verify_reject
        )

        # --------------------------------------------------
        # do tests on <truncate_size> length secret, and resulting hash.
        # should pass regardless of truncate_error policy.
        # --------------------------------------------------
        assert without_error or with_error
        for cand_hasher in [without_error, with_error]:
            # create & hash string that's exactly <truncate_size> chars.
            short_hash = self.do_encrypt(short_secret, handler=cand_hasher)

            # check hash verifies, regardless of .truncate_verify_reject
            assert (
                self.do_verify(short_secret, short_hash, handler=cand_hasher)
                == short_verify_success
            )

            # changing <truncate_size-1>'th char should invalidate hash
            # if this fails, means (reported) truncate_size is too large.
            assert not self.do_verify(
                alt_short_secret, short_hash, handler=with_error
            ), "truncate_size value is too large"

            # verify should truncate long secret before comparing
            # (unless truncate_verify_reject is set)
            assert (
                self.do_verify(long_secret, short_hash, handler=cand_hasher)
                == long_verify_success
            )

        # --------------------------------------------------
        # do tests on <truncate_size+1> length secret,
        # w/ truncate error disabled (should silently truncate)
        # --------------------------------------------------
        if without_error:
            # create & hash string that's exactly truncate_size+1 chars
            long_hash = self.do_encrypt(long_secret, handler=without_error)

            # check verifies against secret (unless truncate_verify_reject=True)
            assert (
                self.do_verify(long_secret, long_hash, handler=without_error)
                == short_verify_success
            )

            # check mutating last char doesn't change outcome.
            # if this fails, means (reported) truncate_size is too small.
            assert (
                self.do_verify(alt_long_secret, long_hash, handler=without_error)
                == short_verify_success
            )

            # check short_secret verifies against this hash
            # if this fails, means (reported) truncate_size is too large.
            assert self.do_verify(short_secret, long_hash, handler=without_error)

        # --------------------------------------------------
        # do tests on <truncate_size+1> length secret,
        # w/ truncate error
        # --------------------------------------------------
        if with_error:
            # with errors enabled, should forbid truncation.
            with pytest.raises(size_error_type) as exc_info:
                self.do_encrypt(long_secret, handler=with_error)
            assert exc_info.value.max_size == truncate_size

    def test_61_secret_case_sensitive(self):
        """test password case sensitivity"""
        hash_insensitive = self.secret_case_insensitive is True
        verify_insensitive = self.secret_case_insensitive in [True, "verify-only"]

        # test hashing lower-case verifies against lower & upper
        lower = "test"
        upper = "TEST"
        h1 = self.do_encrypt(lower)
        if verify_insensitive and not self.handler.is_disabled:
            assert self.do_verify(upper, h1), "verify() should not be case sensitive"
        else:
            assert not self.do_verify(upper, h1), "verify() should be case sensitive"

        # test hashing upper-case verifies against lower & upper
        h2 = self.do_encrypt(upper)
        if verify_insensitive and not self.handler.is_disabled:
            assert self.do_verify(lower, h2), "verify() should not be case sensitive"
        else:
            assert not self.do_verify(lower, h2), "verify() should be case sensitive"

        # test genhash
        # XXX: 2.0: what about 'verify-only' hashes once genhash() is removed?
        #      won't have easy way to recreate w/ same config to see if hash differs.
        #      (though only hash this applies to is mssql2000)
        h2 = self.do_genhash(upper, h1)
        if hash_insensitive or (
            self.handler.is_disabled and not self.disabled_contains_salt
        ):
            assert h2 == h1, "genhash() should not be case sensitive"
        else:
            assert h2 != h1, "genhash() should be case sensitive"

    def test_62_secret_border(self):
        """test non-string passwords are rejected"""
        hash = self.get_sample_hash()[1]

        # secret=None
        with pytest.raises(TypeError):
            self.do_encrypt(None)
        with pytest.raises(TypeError):
            self.do_genhash(None, hash)
        with pytest.raises(TypeError):
            self.do_verify(None, hash)

        # secret=int (picked as example of entirely wrong class)
        with pytest.raises(TypeError):
            self.do_encrypt(1)
        with pytest.raises(TypeError):
            self.do_genhash(1, hash)
        with pytest.raises(TypeError):
            self.do_verify(1, hash)

    # xxx: move to password size limits section, above?
    def test_63_large_secret(self):
        """test MAX_PASSWORD_SIZE is enforced"""
        from passlib.exc import PasswordSizeError
        from passlib.utils import MAX_PASSWORD_SIZE

        secret = "." * (1 + MAX_PASSWORD_SIZE)
        hash = self.get_sample_hash()[1]
        with pytest.raises(PasswordSizeError) as exc_info:
            self.do_genhash(secret, hash)
        assert exc_info.value.max_size == MAX_PASSWORD_SIZE
        with pytest.raises(PasswordSizeError):
            self.do_encrypt(secret)
        with pytest.raises(PasswordSizeError):
            self.do_verify(secret, hash)

    def test_64_forbidden_chars(self):
        """test forbidden characters not allowed in password"""
        chars = self.forbidden_characters
        if not chars:
            raise self.skipTest("none listed")
        base = "stub"
        if isinstance(chars, bytes):
            from passlib.utils.compat import iter_byte_chars

            chars = iter_byte_chars(chars)
            base = base.encode("ascii")
        for c in chars:
            with pytest.raises(ValueError):
                self.do_encrypt(base + c + base)

    def is_secret_8bit(self, secret):
        secret = self.populate_context(secret, {})
        return not is_ascii_safe(secret)

    def expect_os_crypt_failure(self, secret):
        """
        check if we're expecting potential verify failure due to crypt.crypt() encoding limitation
        """
        if self.backend == "os_crypt" and isinstance(secret, bytes):
            try:
                secret.decode("utf-8")
            except UnicodeDecodeError:
                return True
        return False

    def test_70_hashes(self):
        """test known hashes"""

        # sanity check
        assert self.known_correct_hashes or self.known_correct_configs, (
            "test must set at least one of 'known_correct_hashes' "
            "or 'known_correct_configs'"
        )

        # run through known secret/hash pairs
        saw8bit = False
        for secret, hash in self.iter_known_hashes():
            if self.is_secret_8bit(secret):
                saw8bit = True

            # hash should be positively identified by handler
            assert self.do_identify(hash), (
                f"identify() failed to identify hash: {hash!r}"
            )

            # check if what we're about to do is expected to fail due to crypt.crypt() limitation.
            expect_os_crypt_failure = self.expect_os_crypt_failure(secret)
            try:
                # secret should verify successfully against hash
                self.check_verify(
                    secret,
                    hash,
                    f"verify() of known hash failed: secret={secret!r}, hash={hash!r}",
                )

                # genhash() should reproduce same hash
                result = self.do_genhash(secret, hash)
                assert isinstance(result, str), (
                    f"genhash() failed to return native string: {result!r}"
                )
                if self.handler.is_disabled and self.disabled_contains_salt:
                    continue
                assert result == hash, (
                    "genhash() failed to reproduce "
                    f"known hash: secret={secret!r}, hash={hash!r}: result={result!r}"
                )

            except MissingBackendError:
                if not expect_os_crypt_failure:
                    raise

        # would really like all handlers to have at least one 8-bit test vector
        if not saw8bit:
            warn(f"{self.__class__}: no 8-bit secrets tested")

    def test_71_alternates(self):
        """test known alternate hashes"""
        if not self.known_alternate_hashes:
            raise self.skipTest("no alternate hashes provided")
        for alt, secret, hash in self.known_alternate_hashes:
            # hash should be positively identified by handler
            assert self.do_identify(hash), (
                f"identify() failed to identify alternate hash: {hash!r}"
            )

            # secret should verify successfully against hash
            self.check_verify(
                secret,
                alt,
                "verify() of known alternate hash "
                f"failed: secret={secret!r}, hash={alt!r}",
            )

            # genhash() should reproduce canonical hash
            result = self.do_genhash(secret, alt)
            assert isinstance(result, str), (
                f"genhash() failed to return native string: {result!r}"
            )
            if self.handler.is_disabled and self.disabled_contains_salt:
                continue
            assert result == hash, (
                "genhash() failed to normalize "
                f"known alternate hash: secret={secret!r}, alt={alt!r}, hash={hash!r}: "
                f"result={result!r}"
            )

    def test_72_configs(self):
        """test known config strings"""
        # special-case handlers without settings
        if not self.handler.setting_kwds:
            assert not self.known_correct_configs, (
                "handler should not have config strings"
            )
            raise self.skipTest("hash has no settings")

        if not self.known_correct_configs:
            # XXX: make this a requirement?
            raise self.skipTest("no config strings provided")

        # make sure config strings work (hashes in list tested in test_70)
        if self.filter_config_warnings:
            warnings.filterwarnings("ignore", category=PasslibHashWarning)
        for config, secret, hash in self.known_correct_configs:
            # config should be positively identified by handler
            assert self.do_identify(config), (
                f"identify() failed to identify known config string: {config!r}"
            )

            # verify() should throw error for config strings.
            with pytest.raises(ValueError):
                self.do_verify(secret, config)

            # genhash() should reproduce hash from config.
            result = self.do_genhash(secret, config)
            assert isinstance(result, str), (
                f"genhash() failed to return native string: {result!r}"
            )
            assert result == hash, (
                "genhash() failed to reproduce "
                f"known hash from config: secret={secret!r}, config={config!r}, hash={hash!r}: "
                f"result={result!r}"
            )

    def test_73_unidentified(self):
        """test known unidentifiably-mangled strings"""
        if not self.known_unidentified_hashes:
            raise self.skipTest("no unidentified hashes provided")
        for hash in self.known_unidentified_hashes:
            # identify() should reject these
            assert not self.do_identify(hash), (
                f"identify() incorrectly identified known unidentifiable hash: {hash!r}"
            )

            with pytest.raises(ValueError):
                self.do_verify("stub", hash)
            with pytest.raises(ValueError):
                self.do_genhash("stub", hash)

    def test_74_malformed(self):
        """test known identifiable-but-malformed strings"""
        if not self.known_malformed_hashes:
            raise self.skipTest("no malformed hashes provided")
        for hash in self.known_malformed_hashes:
            # identify() should accept these
            assert self.do_identify(hash), (
                f"identify() failed to identify known malformed hash: {hash!r}"
            )

            with pytest.raises(ValueError):
                self.do_verify("stub", hash)

            with pytest.raises(ValueError):
                self.do_genhash("stub", hash)

    def test_75_foreign(self):
        """test known foreign hashes"""
        if self.accepts_all_hashes:
            raise self.skipTest("not applicable")
        if not self.known_other_hashes:
            raise self.skipTest("no foreign hashes provided")
        for name, hash in self.known_other_hashes:
            # NOTE: most tests use default list of foreign hashes,
            # so they may include ones belonging to that hash...
            # hence the 'own' logic.

            if name == self.handler.name:
                # identify should accept these
                assert self.do_identify(hash), (
                    f"identify() failed to identify known hash: {hash!r}"
                )

                # verify & genhash should NOT throw error
                self.do_verify("stub", hash)
                result = self.do_genhash("stub", hash)
                assert isinstance(result, str), (
                    f"genhash() failed to return native string: {result!r}"
                )

            else:
                # identify should reject these
                assert not self.do_identify(hash), (
                    "identify() incorrectly identified hash belonging to "
                    f"{name}: {hash!r}"
                )

                # verify should throw error
                with pytest.raises(ValueError):
                    self.do_verify("stub", hash)

                # genhash() should throw error
                with pytest.raises(ValueError):
                    self.do_genhash("stub", hash)

    def test_76_hash_border(self):
        """test non-string hashes are rejected"""
        # test hash=None is handled correctly
        with pytest.raises(TypeError):
            self.do_identify(None)
        with pytest.raises(TypeError):
            self.do_verify("stub", None)

        # NOTE: changed in 1.7 -- previously 'None' would be accepted when config strings not supported.
        with pytest.raises(TypeError):
            self.do_genhash("stub", None)

        # test hash=int is rejected (picked as example of entirely wrong type)
        with pytest.raises(TypeError):
            self.do_identify(1)
        with pytest.raises(TypeError):
            self.do_verify("stub", 1)
        with pytest.raises(TypeError):
            self.do_genhash("stub", 1)

        #
        # test hash='' is rejected for all but the plaintext hashes
        #
        for hash in ["", b""]:
            if self.accepts_all_hashes:
                # then it accepts empty string as well.
                assert self.do_identify(hash)
                self.do_verify("stub", hash)
                result = self.do_genhash("stub", hash)
                self.check_returned_native_str(result, "genhash")
            else:
                # otherwise it should reject them
                assert not self.do_identify(hash), (
                    "identify() incorrectly identified empty hash"
                )
                with pytest.raises(ValueError):
                    self.do_verify("stub", hash)
                with pytest.raises(ValueError):
                    self.do_genhash("stub", hash)

        #
        # test identify doesn't throw decoding errors on 8-bit input
        #
        self.do_identify("\xe2\x82\xac\xc2\xa5$")  # utf-8
        self.do_identify("abc\x91\x00")  # non-utf8

    #: optional list of known parse hash results for hasher
    known_parsehash_results: list[tuple[str, dict[str, object]]] = []

    def require_parsehash(self):
        if not hasattr(self.handler, "parsehash"):
            raise self.skipTest("parsehash() not implemented")

    def test_70_parsehash(self):
        """
        parsehash()
        """
        # TODO: would like to enhance what this test covers

        self.require_parsehash()
        handler = self.handler

        # calls should succeed, and return dict
        hash = self.do_encrypt("stub")
        result = handler.parsehash(hash)
        assert isinstance(result, dict)
        # TODO: figure out what invariants we can reliably parse,
        #       or maybe make subclasses specify that?

        # w/ checksum=False, should omit that key
        result2 = handler.parsehash(hash, checksum=False)
        correct2 = result.copy()
        correct2.pop("checksum", None)
        assert result2 == correct2

        # w/ sanitize=True
        # correct output should mask salt / checksum;
        # but all else should be the same
        result3 = handler.parsehash(hash, sanitize=True)
        correct3 = result.copy()
        for key in ("salt", "checksum"):
            if key in result3:
                assert result3[key] != correct3[key]
                self.assert_is_masked(result3[key])
                correct3[key] = result3[key]
        assert result3 == correct3

    def assert_is_masked(self, value):
        """
        check value properly masked by :func:`passlib.utils.mask_value`
        """
        if value is None:
            return None
        assert isinstance(value, str)
        # assumes mask_value() defaults will never show more than <show> chars (4);
        # and show nothing if size less than 1/<pct> (8).
        ref = value if len(value) < 8 else value[4:]
        if set(ref) == set(["*"]):
            return True
        raise self.fail(f"value not masked: {value!r}")

    def test_71_parsehash_results(self):
        """
        parsehash() -- known outputs
        """
        self.require_parsehash()
        samples = self.known_parsehash_results
        if not samples:
            raise self.skipTest("no samples present")
        # XXX: expand to test w/ checksum=False and/or sanitize=True?
        #      or read "_unsafe_settings"?
        for hash, correct in self.known_parsehash_results:
            result = self.handler.parsehash(hash)
            assert result == correct, f"hash={hash!r}:"

    def test_77_fuzz_input(self, threaded=False):
        """fuzz testing -- random passwords and options

        This test attempts to perform some basic fuzz testing of the hash,
        based on whatever information can be found about it.
        It does as much as it can within a fixed amount of time
        (defaults to 1 second, but can be overridden via $PASSLIB_TEST_FUZZ_TIME).
        It tests the following:

        * randomly generated passwords including extended unicode chars
        * randomly selected rounds values (if rounds supported)
        * randomly selected salt sizes (if salts supported)
        * randomly selected identifiers (if multiple found)
        * runs output of selected backend against other available backends
          (if any) to detect errors occurring between different backends.
        * runs output against other "external" verifiers such as OS crypt()

        :param report_thread_state:
            if true, writes state of loop to current_thread().passlib_fuzz_state.
            used to help debug multi-threaded fuzz test issues (below)
        """
        if self.handler.is_disabled:
            raise self.skipTest("not applicable")

        # gather info
        from passlib.utils import tick

        max_time = self.max_fuzz_time
        if max_time <= 0:
            raise self.skipTest("disabled by test mode")
        verifiers = self.get_fuzz_verifiers(threaded=threaded)

        def vname(v):
            return (v.__doc__ or v.__name__).splitlines()[0]

        # init rng -- using separate one for each thread
        # so things are predictable for given RANDOM_TEST_SEED
        # (relies on test_78_fuzz_threading() to give threads unique names)
        thread_name = threading.current_thread().name if threaded else "fuzz test"
        rng = self.getRandom(name=thread_name)
        generator = self.FuzzHashGenerator(self, rng)

        # do as many tests as possible for max_time seconds
        log.debug(
            "%s: %s: started; max_time=%r verifiers=%d (%s)",
            self.descriptionPrefix,
            thread_name,
            max_time,
            len(verifiers),
            ", ".join(vname(v) for v in verifiers),
        )
        start = tick()
        stop = start + max_time
        count = 0
        while tick() <= stop:
            # generate random password & options
            opts = generator.generate()
            secret = opts["secret"]
            other = opts["other"]
            settings = opts["settings"]
            ctx = opts["context"]
            if ctx:
                settings["context"] = ctx

            # create new hash
            hash = self.do_encrypt(secret, **settings)
            ##log.debug("fuzz test: hash=%r secret=%r other=%r",
            ##          hash, secret, other)

            # run through all verifiers we found.
            for verify in verifiers:
                name = vname(verify)
                result = verify(secret, hash, **ctx)
                if result == "skip":  # let verifiers signal lack of support
                    continue
                assert result is True or result is False
                if not result:
                    raise self.failureException(
                        f"failed to verify against {name!r} verifier: "
                        f"secret={secret!r} config={settings!r} hash={hash!r}"
                    )
                # occasionally check that some other secrets WON'T verify
                # against this hash.
                if rng.random() < 0.1:
                    result = verify(other, hash, **ctx)
                    if result and result != "skip":
                        raise self.failureException(
                            "was able to verify wrong "
                            f"password using {name}: wrong_secret={other!r} real_secret={secret!r} "
                            f"config={settings!r} hash={hash!r}"
                        )
            count += 1

        log.debug(
            "%s: %s: done; elapsed=%r count=%r",
            self.descriptionPrefix,
            thread_name,
            tick() - start,
            count,
        )

    def test_78_fuzz_threading(self):
        """multithreaded fuzz testing -- random password & options using multiple threads

        run test_77 simultaneously in multiple threads
        in an attempt to detect any concurrency issues
        (e.g. the bug fixed by pybcrypt 0.3)
        """
        self.require_TEST_MODE("full")
        import threading

        # check if this test should run
        if self.handler.is_disabled:
            raise self.skipTest("not applicable")
        thread_count = self.fuzz_thread_count
        if thread_count < 1 or self.max_fuzz_time <= 0:
            raise self.skipTest("disabled by test mode")

        # buffer to hold errors thrown by threads
        failed_lock = threading.Lock()
        failed = [0]

        # launch <thread count> threads, all of which run
        # test_77_fuzz_input(), and see if any errors get thrown.
        # if hash has concurrency issues, this should reveal it.
        def wrapper():
            try:
                self.test_77_fuzz_input(threaded=True)
            except unittest.SkipTest:
                pass
            except:
                with failed_lock:
                    failed[0] += 1
                raise

        def launch(n):
            cls = type(self)
            name = "Fuzz-Thread-%d ('%s:%s.%s')" % (
                n,
                cls.__module__,
                cls.__name__,
                self._testMethodName,
            )
            thread = threading.Thread(target=wrapper, name=name)
            thread.setDaemon(True)
            thread.start()
            return thread

        threads = [launch(n) for n in range(thread_count)]

        # wait until all threads exit
        timeout = self.max_fuzz_time * thread_count * 4
        stalled = 0
        for thread in threads:
            thread.join(timeout)
            if not thread.is_alive():
                continue
            # XXX: not sure why this is happening, main one seems 1/4 times for sun_md5_crypt
            log.error("%s timed out after %f seconds", thread.name, timeout)
            stalled += 1

        # if any thread threw an error, raise one ourselves.
        if failed[0]:
            raise self.fail(
                "%d/%d threads failed concurrent fuzz testing "
                "(see error log for details)" % (failed[0], thread_count)
            )
        if stalled:
            raise self.fail(
                "%d/%d threads stalled during concurrent fuzz testing "
                "(see error log for details)" % (stalled, thread_count)
            )

    # ---------------------------------------------------------------
    # fuzz constants & helpers
    # ---------------------------------------------------------------

    @property
    def max_fuzz_time(self):
        """amount of time to spend on fuzz testing"""
        value = float(os.environ.get("PASSLIB_TEST_FUZZ_TIME") or 0)
        if value:
            return value
        if TEST_MODE(max="quick"):
            return 0
        if TEST_MODE(max="default"):
            return 1
        return 5

    @property
    def fuzz_thread_count(self):
        """number of threads for threaded fuzz testing"""
        value = int(os.environ.get("PASSLIB_TEST_FUZZ_THREADS") or 0)
        if value:
            return value
        if TEST_MODE(max="quick"):
            return 0
        return 10

    # ---------------------------------------------------------------
    # fuzz verifiers
    # ---------------------------------------------------------------

    #: list of custom fuzz-test verifiers (in addition to hasher itself,
    #: and backend-specific wrappers of hasher).  each element is
    #: name of method that will return None / a verifier callable.
    fuzz_verifiers: tuple[str, ...] = ("fuzz_verifier_default",)

    def get_fuzz_verifiers(self, threaded=False):
        """return list of password verifiers (including external libs)

        used by fuzz testing.
        verifiers should be callable with signature
        ``func(password: str, hash: ascii str) -> ok: bool``.
        """
        handler = self.handler
        verifiers = []

        # call all methods starting with prefix in order to create
        for method_name in self.fuzz_verifiers:
            func = getattr(self, method_name)()
            if func is not None:
                verifiers.append(func)

        # create verifiers for any other available backends
        # NOTE: skipping this under threading test,
        #       since backend switching isn't threadsafe (yet)
        if hasattr(handler, "backends") and TEST_MODE("full") and not threaded:

            def maker(backend):
                def func(secret, hash):
                    orig_backend = handler.get_backend()
                    try:
                        handler.set_backend(backend)
                        return handler.verify(secret, hash)
                    finally:
                        handler.set_backend(orig_backend)

                func.__name__ = "check_" + backend + "_backend"
                func.__doc__ = backend + "-backend"
                return func

            for backend in iter_alt_backends(handler):
                verifiers.append(maker(backend))  # noqa: PERF401

        return verifiers

    def fuzz_verifier_default(self):
        # test against self
        def check_default(secret, hash, **ctx):
            return self.do_verify(secret, hash, **ctx)

        if self.backend:
            check_default.__doc__ = self.backend + "-backend"
        else:
            check_default.__doc__ = "self"
        return check_default

    # ---------------------------------------------------------------
    # fuzz settings generation
    # ---------------------------------------------------------------
    class FuzzHashGenerator:
        """
        helper which takes care of generating random
        passwords & configuration options to test hash with.
        separate from test class so we can create one per thread.
        """

        # alphabet for randomly generated passwords
        password_alphabet = "qwertyASDF1234<>.@*#! \u00e1\u0259\u0411\u2113"

        # encoding when testing bytes
        password_encoding = "utf-8"

        # map of setting kwd -> method name.
        # will ignore setting if method returns None.
        # subclasses should make copy of dict.
        settings_map = dict(
            rounds="random_rounds", salt_size="random_salt_size", ident="random_ident"
        )

        # map of context kwd -> method name.
        context_map: dict[str, str] = {}

        def __init__(self, test, rng):
            self.test = test
            self.handler = test.handler
            self.rng = rng

        def generate(self):
            """
            generate random password and options for fuzz testing.
            :returns:
                `(secret, other_secret, settings_kwds, context_kwds)`
            """

            def gendict(map):
                out = {}
                for key, meth in map.items():
                    value = getattr(self, meth)()
                    if value is not None:
                        out[key] = value
                return out

            secret, other = self.random_password_pair()
            return dict(
                secret=secret,
                other=other,
                settings=gendict(self.settings_map),
                context=gendict(self.context_map),
            )

        def randintgauss(self, lower, upper, mu, sigma):
            """generate random int w/ gauss distirbution"""
            value = self.rng.normalvariate(mu, sigma)
            return int(limit(value, lower, upper))

        def random_rounds(self):
            handler = self.handler
            if not has_rounds_info(handler):
                return None
            default = handler.default_rounds or handler.min_rounds
            lower = handler.min_rounds
            if handler.rounds_cost == "log2":
                upper = default
            else:
                upper = min(default * 2, handler.max_rounds)
            return self.randintgauss(lower, upper, default, default * 0.5)

        def random_salt_size(self):
            handler = self.handler
            if not (has_salt_info(handler) and "salt_size" in handler.setting_kwds):
                return None
            default = handler.default_salt_size
            lower = handler.min_salt_size
            upper = handler.max_salt_size or default * 4
            return self.randintgauss(lower, upper, default, default * 0.5)

        def random_ident(self):
            rng = self.rng
            handler = self.handler
            if "ident" not in handler.setting_kwds or not hasattr(
                handler, "ident_values"
            ):
                return None
            if rng.random() < 0.5:
                return None
            # resolve wrappers before reading values
            handler = getattr(handler, "wrapped", handler)
            return rng.choice(handler.ident_values)

        def random_password_pair(self):
            """generate random password, and non-matching alternate password"""
            secret = self.random_password()
            while True:
                other = self.random_password()
                if self.accept_password_pair(secret, other):
                    break
            rng = self.rng
            if rng.randint(0, 1):
                secret = secret.encode(self.password_encoding)
            if rng.randint(0, 1):
                other = other.encode(self.password_encoding)
            return secret, other

        def random_password(self):
            """generate random passwords for fuzz testing"""
            # occasionally try an empty password
            rng = self.rng
            if rng.random() < 0.0001:
                return ""

            # check if truncate size needs to be considered
            handler = self.handler
            truncate_size = handler.truncate_error and handler.truncate_size
            max_size = truncate_size or 999999

            # pick endpoint
            if max_size < 50 or rng.random() < 0.5:
                # chance of small password (~15 chars)
                size = self.randintgauss(1, min(max_size, 50), 15, 15)
            else:
                # otherwise large password (~70 chars)
                size = self.randintgauss(50, min(max_size, 99), 70, 20)

            # generate random password
            result = getrandstr(rng, self.password_alphabet, size)

            # trim ones that encode past truncate point.
            if truncate_size and isinstance(result, str):
                while len(result.encode("utf-8")) > truncate_size:
                    result = result[:-1]

            return result

        def accept_password_pair(self, secret, other):
            """verify fuzz pair contains different passwords"""
            return secret != other

    def test_disable_and_enable(self):
        """.disable() / .enable() methods"""
        #
        # setup
        #
        handler = self.handler
        if not handler.is_disabled:
            assert not hasattr(handler, "disable")
            assert not hasattr(handler, "enable")
            assert not self.disabled_contains_salt
            raise self.skipTest("not applicable")

        #
        # disable()
        #

        # w/o existing hash
        disabled_default = handler.disable()
        assert isinstance(disabled_default, str), "disable() must return native string"
        assert handler.identify(disabled_default), (
            f"identify() didn't recognize disable() result: {disabled_default!r}"
        )

        # w/ existing hash
        stub = self.getRandom().choice(self.known_other_hashes)[1]
        disabled_stub = handler.disable(stub)
        assert isinstance(disabled_stub, str), "disable() must return native string"
        assert handler.identify(disabled_stub), (
            f"identify() didn't recognize disable() result: {disabled_stub!r}"
        )

        #
        # enable()
        #

        # w/o original hash
        with pytest.raises(ValueError, match="cannot restore original hash"):
            handler.enable(disabled_default)

        # w/ original hash
        try:
            result = handler.enable(disabled_stub)
            error = None
        except ValueError as e:
            result = None
            error = e

        if error is None:
            # if supports recovery, should have returned stub (e.g. unix_disabled);
            assert isinstance(result, str), "enable() must return native string"
            assert result == stub
        else:
            # if doesn't, should have thrown appropriate error
            assert isinstance(error, ValueError)
            assert re.search(str(error), "cannot restore original hash")

        #
        # test repeating disable() & salting state
        #

        # repeating disabled
        disabled_default2 = handler.disable()
        if self.disabled_contains_salt:
            # should return new salt for each call (e.g. django_disabled)
            assert disabled_default2 != disabled_default
        elif error is None:
            # should return same result for each hash, but unique across hashes
            assert disabled_default2 == disabled_default

        # repeating same hash ...
        disabled_stub2 = handler.disable(stub)
        if self.disabled_contains_salt:
            # ... should return different string (if salted)
            assert disabled_stub2 != disabled_stub
        else:
            # ... should return same string
            assert disabled_stub2 == disabled_stub

        # using different hash ...
        disabled_other = handler.disable(stub + "xxx")
        if self.disabled_contains_salt or error is None:
            # ... should return different string (if salted or hash encoded)
            assert disabled_other != disabled_stub
        else:
            # ... should return same string
            assert disabled_other == disabled_stub


class OsCryptMixin(HandlerCase):
    """helper used by create_backend_case() which adds additional features
    to test the os_crypt backend.

    * if crypt support is missing, inserts fake crypt support to simulate
      a working safe_crypt, to test passlib's codepath as fully as possible.

    * extra tests to verify non-conformant crypt implementations are handled
      correctly.

    * check that native crypt support is detected correctly for known platforms.
    """

    # platforms that are known to support / not support this hash natively.
    # list of (platform_regex, True|False|None) entries.
    platform_crypt_support: Sequence[tuple[str, bool]] = []
    __unittest_skip = True

    # force this backend
    backend = "os_crypt"

    # flag read by HandlerCase to detect if fake os crypt is enabled.
    using_patched_crypt = False

    def setUp(self):
        assert self.backend == "os_crypt"
        if not self.handler.has_backend("os_crypt"):
            # XXX: currently, any tests that use this are skipped entirely! (see issue 120)
            self._patch_safe_crypt()
        super().setUp()

    @classmethod
    def _get_safe_crypt_handler_backend(cls):
        """
        return (handler, backend) pair to use for faking crypt.crypt() support for hash.
        backend will be None if none availabe.
        """
        # find handler that generates safe_crypt() compatible hash
        handler = unwrap_handler(cls.handler)

        # hack to prevent recursion issue when .has_backend() is called
        handler.get_backend()

        # find backend which isn't os_crypt
        alt_backend = get_alt_backend(handler, "os_crypt")
        return handler, alt_backend

    @property
    def has_os_crypt_fallback(self):
        """
        test if there's a fallback handler to test against if os_crypt can't support
        a specified secret (may be explicitly set to False for some subclasses)
        """
        return self._get_safe_crypt_handler_backend()[0] is not None

    def _patch_safe_crypt(self):
        """if crypt() doesn't support current hash alg, this patches
        safe_crypt() so that it transparently uses another one of the handler's
        backends, so that we can go ahead and test as much of code path
        as possible.
        """
        # find handler & backend
        handler, alt_backend = self._get_safe_crypt_handler_backend()
        if not alt_backend:
            raise AssertionError("handler has no available alternate backends!")

        # create subclass of handler, which we swap to an alternate backend
        alt_handler = handler.using()
        alt_handler.set_backend(alt_backend)

        def crypt_stub(secret, hash):
            hash = alt_handler.genhash(secret, hash)
            assert isinstance(hash, str)
            return hash

        # self.patchAttr(mod, "_crypt", crypt_stub)
        self.using_patched_crypt = True

    @classmethod
    def _get_skip_backend_reason(cls, backend):
        """
        make sure os_crypt backend is tested
        when it's known os_crypt will be faked by _patch_safe_crypt()
        """
        assert backend == "os_crypt"
        reason = super()._get_skip_backend_reason(backend)

        from passlib.utils import has_crypt

        if reason == cls._BACKEND_NOT_AVAILABLE and has_crypt:
            if TEST_MODE("full") and cls._get_safe_crypt_handler_backend()[1]:
                # in this case, _patch_safe_crypt() will monkeypatch os_crypt
                # to use another backend, just so we can test os_crypt fully.
                return None
            return "hash not supported by os crypt()"

        return reason

    # TODO: turn into decorator, and use mock library.
    def _use_mock_crypt(self):
        """
        patch passlib.utils.safe_crypt() so it returns mock value for duration of test.
        returns function whose .return_value controls what's returned.
        this defaults to None.
        """
        import passlib.utils as mod

        def mock_crypt(secret, config):
            # let 'test' string through so _load_os_crypt_backend() will still work
            if secret == "test":
                return mock_crypt.__wrapped__(secret, config)
            return mock_crypt.return_value

        mock_crypt.__wrapped__ = mod._crypt
        mock_crypt.return_value = None

        self.patchAttr(mod, "_crypt", mock_crypt)

        return mock_crypt

    def test_80_faulty_crypt(self):
        """test with faulty crypt()"""
        hash = self.get_sample_hash()[1]
        mock_crypt = self._use_mock_crypt()

        for value in ["$x" + hash[2:], hash[:-1], hash + "x"]:
            mock_crypt.return_value = value
            with pytest.raises(InternalBackendError):
                self.do_genhash("stub", hash)
            with pytest.raises(InternalBackendError):
                self.do_encrypt("stub")
            with pytest.raises(InternalBackendError):
                self.do_verify("stub", hash)

    def test_81_crypt_fallback(self):
        """test per-call crypt() fallback"""

        # mock up safe_crypt to return None
        mock_crypt = self._use_mock_crypt()
        mock_crypt.return_value = None

        if self.has_os_crypt_fallback:
            # handler should have a fallback to use when os_crypt backend refuses to handle secret.
            h1 = self.do_encrypt("stub")
            h2 = self.do_genhash("stub", h1)
            assert h2 == h1
            assert self.do_verify("stub", h1)
        else:
            # handler should give up
            from passlib.exc import InternalBackendError

            hash = self.get_sample_hash()[1]
            with pytest.raises(InternalBackendError):
                self.do_encrypt("stub")
            with pytest.raises(InternalBackendError):
                self.do_genhash("stub", hash)
            with pytest.raises(InternalBackendError):
                self.do_verify("stub", hash)

    @doesnt_require_backend
    def test_82_crypt_support(self):
        """
        test platform-specific crypt() support detection

        NOTE: this is mainly just a sanity check to ensure the runtime
              detection is functioning correctly on some known platforms,
              so that we can feel more confident it'll work right on unknown ones.
        """

        # skip wrapper handlers, won't ever have crypt support
        if hasattr(self.handler, "orig_prefix"):
            raise self.skipTest("not applicable to wrappers")

        # look for first entry that matches current system
        # XXX: append "/" + platform.release() to string?
        # XXX: probably should rework to support rows being dicts w/ "minver" / "maxver" keys,
        #      instead of hack where we add major # as part of platform regex.
        using_backend = not self.using_patched_crypt
        name = self.handler.name
        platform = sys.platform
        for pattern, expected in self.platform_crypt_support:
            if re.match(pattern, platform):
                break
        else:
            raise self.skipTest(
                f"no data for {platform!r} platform (current host support = {using_backend!r})"
            )

        # rules can use "state=None" to signal varied support;
        # e.g. platform='freebsd8' ... sha256_crypt not added until 8.3
        if expected is None:
            raise self.skipTest(
                f"varied support on {platform!r} platform (current host support = {using_backend!r})"
            )

        # compare expectation vs reality
        if expected == using_backend:
            pass
        elif expected:
            self.fail(
                f"expected {platform!r} platform would have native support for {name!r}"
            )
        else:
            self.fail(
                f"did not expect {platform!r} platform would have native support for {name!r}"
            )

    def crypt_supports_variant(self, hash):
        """
        fuzzy_verified_crypt() helper --
        used to determine if os crypt() supports a particular hash variant.
        """
        return True


class UserHandlerMixin(HandlerCase):
    """helper for handlers w/ 'user' context kwd; mixin for HandlerCase

    this overrides the HandlerCase test harness methods
    so that a username is automatically inserted to hash/verify
    calls. as well, passing in a pair of strings as the password
    will be interpreted as (secret,user)
    """

    default_user = "user"
    requires_user = True
    user_case_insensitive = False

    __unittest_skip = True

    def test_80_user(self):
        """test user context keyword"""
        handler = self.handler
        password = "stub"
        hash = handler.hash(password, user=self.default_user)

        if self.requires_user:
            with pytest.raises(TypeError):
                handler.hash(password)
            with pytest.raises(TypeError):
                handler.genhash(password, hash)
            with pytest.raises(TypeError):
                handler.verify(password, hash)
        else:
            # e.g. cisco_pix works with or without one.
            handler.hash(password)
            handler.genhash(password, hash)
            handler.verify(password, hash)

    def test_81_user_case(self):
        """test user case sensitivity"""
        lower = self.default_user.lower()
        upper = lower.upper()
        hash = self.do_encrypt("stub", context=dict(user=lower))
        if self.user_case_insensitive:
            assert self.do_verify("stub", hash, user=upper), (
                "user should not be case sensitive"
            )
        else:
            assert not self.do_verify("stub", hash, user=upper), (
                "user should be case sensitive"
            )

    def test_82_user_salt(self):
        """test user used as salt"""
        config = self.do_stub_encrypt()
        h1 = self.do_genhash("stub", config, user="admin")
        h2 = self.do_genhash("stub", config, user="admin")
        assert h2 == h1
        h3 = self.do_genhash("stub", config, user="root")
        assert h3 != h1

    # TODO: user size? kinda dicey, depends on algorithm.
    def populate_context(self, secret, kwds):
        """insert username into kwds"""
        if isinstance(secret, tuple):
            secret, user = secret
        elif not self.requires_user:
            return secret
        else:
            user = self.default_user
        if "user" not in kwds:
            kwds["user"] = user
        return secret

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        context_map = HandlerCase.FuzzHashGenerator.context_map.copy()
        context_map.update(user="random_user")

        user_alphabet = "asdQWE123"

        def random_user(self):
            rng = self.rng
            if not self.test.requires_user and rng.random() < 0.1:
                return None
            return getrandstr(rng, self.user_alphabet, rng.randint(2, 10))


class EncodingHandlerMixin(HandlerCase):
    """helper for handlers w/ 'encoding' context kwd; mixin for HandlerCase

    this overrides the HandlerCase test harness methods
    so that an encoding can be inserted to hash/verify
    calls by passing in a pair of strings as the password
    will be interpreted as (secret,encoding)
    """

    __unittest_skip = True

    # restrict stock passwords & fuzz alphabet to latin-1,
    # so different encodings can be tested safely.
    stock_passwords = [
        "test",
        b"test",
        "\u00ac\u00ba",
    ]

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        password_alphabet = "qwerty1234<>.@*#! \u00ac"

    def populate_context(self, secret, kwds):
        """insert encoding into kwds"""
        if isinstance(secret, tuple):
            secret, encoding = secret
            kwds.setdefault("encoding", encoding)
        return secret


class reset_warnings(warnings.catch_warnings):
    """catch_warnings() wrapper which clears warning registry & filters"""

    def __init__(self, reset_filter="always", reset_registry=".*", **kwds):
        super().__init__(**kwds)
        self._reset_filter = reset_filter
        self._reset_registry = re.compile(reset_registry) if reset_registry else None

    def __enter__(self):
        # let parent class archive filter state
        ret = super().__enter__()

        # reset the filter to list everything
        if self._reset_filter:
            warnings.resetwarnings()
            warnings.simplefilter(self._reset_filter)

        # archive and clear the __warningregistry__ key for all modules
        # that match the 'reset' pattern.
        pattern = self._reset_registry
        if pattern:
            backup = self._orig_registry = {}
            for name, mod in list(sys.modules.items()):
                if mod is None or not pattern.match(name):
                    continue
                reg = getattr(mod, "__warningregistry__", None)
                if reg:
                    backup[name] = reg.copy()
                    reg.clear()
        return ret

    def __exit__(self, *exc_info):
        # restore warning registry for all modules
        pattern = self._reset_registry
        if pattern:
            # restore registry backup, clearing all registry entries that we didn't archive
            backup = self._orig_registry
            for name, mod in list(sys.modules.items()):
                if mod is None or not pattern.match(name):
                    continue
                reg = getattr(mod, "__warningregistry__", None)
                if reg:
                    reg.clear()
                orig = backup.get(name)
                if orig:
                    if reg is None:
                        setattr(mod, "__warningregistry__", orig)
                    else:
                        reg.update(orig)
        super().__exit__(*exc_info)
