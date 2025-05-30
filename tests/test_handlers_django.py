from __future__ import annotations

import warnings
from unittest import SkipTest, skipUnless

from passlib import hash
from passlib.utils import repeat_string
from tests.test_ext_django import (
    DJANGO_VERSION,
    MIN_DJANGO_VERSION,
    check_django_hasher_has_backend,
)
from tests.test_handlers import UPASS_TABLE, UPASS_USD
from tests.test_handlers_argon2 import _base_argon2_test
from tests.utils import HandlerCase, TestCase

# module


# standard string django uses
UPASS_LETMEIN = "l\xe8tmein"


def vstr(version):
    return ".".join(str(e) for e in version)


class _DjangoHelper(TestCase):
    """
    mixin for HandlerCase subclasses that are testing a hasher
    which is also present in django.
    """

    __unittest_skip = True

    #: minimum django version where hash alg is present / that we support testing against
    min_django_version = MIN_DJANGO_VERSION
    max_django_version: tuple[int, int] | None = None

    def _require_django_support(self):
        # make sure min django version
        if self.min_django_version > DJANGO_VERSION:
            raise self.skipTest(
                f"Django >= {vstr(self.min_django_version)} not installed"
            )
        if self.max_django_version and self.max_django_version < DJANGO_VERSION:
            raise self.skipTest(
                f"Django <= {vstr(self.max_django_version)} not installed"
            )

        # make sure django has a backend for specified hasher
        name = self.handler.django_name
        if not check_django_hasher_has_backend(name):
            raise self.skipTest(f"django hasher {name!r} not available")

        return True

    extra_fuzz_verifiers = HandlerCase.fuzz_verifiers + ("fuzz_verifier_django",)

    def fuzz_verifier_django(self):
        try:
            self._require_django_support()
        except SkipTest:
            return None
        from django.contrib.auth.hashers import check_password

        def verify_django(secret, hash):
            """django/check_password"""
            if self.handler.name == "django_bcrypt" and hash.startswith("bcrypt$$2y$"):
                hash = hash.replace("$$2y$", "$$2a$")
            if isinstance(secret, bytes):
                secret = secret.decode("utf-8")
            return check_password(secret, hash)

        return verify_django

    def test_90_django_reference(self):
        """run known correct hashes through Django's check_password()"""
        self._require_django_support()
        # XXX: esp. when it's no longer supported by django,
        #      should verify it's *NOT* recognized
        from django.contrib.auth.hashers import check_password

        assert self.known_correct_hashes
        for secret, hash_ in self.iter_known_hashes():
            assert check_password(secret, hash_), (
                f"secret={secret!r} hash={hash_!r} failed to verify"
            )
            assert not check_password("x" + secret, hash_), (
                f"mangled secret={secret!r} hash={hash_!r} incorrect verified"
            )

    def test_91_django_generation(self):
        """test against output of Django's make_password()"""
        self._require_django_support()
        # XXX: esp. when it's no longer supported by django,
        #      should verify it's *NOT* recognized
        from django.contrib.auth.hashers import make_password

        from passlib.utils import tick

        name = self.handler.django_name  # set for all the django_* handlers
        end = tick() + self.max_fuzz_time / 2
        generator = self.FuzzHashGenerator(self, self.getRandom())
        while tick() < end:
            secret, other = generator.random_password_pair()
            if not secret:  # django rejects empty passwords.
                continue
            if isinstance(secret, bytes):
                secret = secret.decode("utf-8")
            hash = make_password(secret, hasher=name)
            assert self.do_identify(hash)
            assert self.do_verify(secret, hash)
            assert not self.do_verify(other, hash)


class django_disabled_test(HandlerCase):
    """test django_disabled"""

    handler = hash.django_disabled
    disabled_contains_salt = True

    known_correct_hashes = [
        # *everything* should hash to "!", and nothing should verify
        ("password", "!"),
        ("", "!"),
        (UPASS_TABLE, "!"),
    ]

    known_alternate_hashes = [
        # django 1.6 appends random alpnum string
        ("!9wa845vn7098ythaehasldkfj", "password", "!"),
    ]


class django_des_crypt_test(HandlerCase, _DjangoHelper):
    """test django_des_crypt"""

    handler = hash.django_des_crypt
    max_django_version = (1, 9)

    known_correct_hashes = [
        # ensures only first two digits of salt count.
        ("password", "crypt$c2$c2M87q...WWcU"),
        ("password", "crypt$c2e86$c2M87q...WWcU"),
        ("passwordignoreme", "crypt$c2.AZ$c2M87q...WWcU"),
        # ensures utf-8 used for unicode
        (UPASS_USD, "crypt$c2e86$c2hN1Bxd6ZiWs"),
        (UPASS_TABLE, "crypt$0.aQs$0.wB.TT0Czvlo"),
        ("hell\u00d6", "crypt$sa$saykDgk3BPZ9E"),
        # prevent regression of issue 22
        ("foo", "crypt$MNVY.9ajgdvDQ$MNVY.9ajgdvDQ"),
    ]

    known_alternate_hashes = [
        # ensure django 1.4 empty salt field is accepted;
        # but that salt field is re-filled (for django 1.0 compatibility)
        ("crypt$$c2M87q...WWcU", "password", "crypt$c2$c2M87q...WWcU"),
    ]

    known_unidentified_hashes = [
        "sha1$aa$bb",
    ]

    known_malformed_hashes = [
        # checksum too short
        "crypt$c2$c2M87q",
        # salt must be >2
        "crypt$f$c2M87q...WWcU",
        # make sure first 2 chars of salt & chk field agree.
        "crypt$ffe86$c2M87q...WWcU",
    ]


class django_salted_md5_test(HandlerCase, _DjangoHelper):
    """test django_salted_md5"""

    handler = hash.django_salted_md5
    max_django_version = (1, 9)

    known_correct_hashes = [
        # test extra large salt
        ("password", "md5$123abcdef$c8272612932975ee80e8a35995708e80"),
        # test django 1.4 alphanumeric salt
        ("test", "md5$3OpqnFAHW5CT$54b29300675271049a1ebae07b395e20"),
        # ensures utf-8 used for unicode
        (UPASS_USD, "md5$c2e86$92105508419a81a6babfaecf876a2fa0"),
        (UPASS_TABLE, "md5$d9eb8$01495b32852bffb27cf5d4394fe7a54c"),
    ]

    known_unidentified_hashes = [
        "sha1$aa$bb",
    ]

    known_malformed_hashes = [
        # checksum too short
        "md5$aa$bb",
    ]

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        def random_salt_size(self):
            # workaround for django14 regression --
            # 1.4 won't accept hashes with empty salt strings, unlike 1.3 and earlier.
            # looks to be fixed in a future release -- https://code.djangoproject.com/ticket/18144
            # for now, we avoid salt_size==0 under 1.4
            handler = self.handler
            default = handler.default_salt_size
            assert handler.min_salt_size == 0
            lower = 1
            upper = handler.max_salt_size or default * 4
            return self.randintgauss(lower, upper, default, default * 0.5)


class django_salted_sha1_test(HandlerCase, _DjangoHelper):
    """test django_salted_sha1"""

    handler = hash.django_salted_sha1
    max_django_version = (1, 9)

    known_correct_hashes = [
        # test extra large salt
        ("password", "sha1$123abcdef$e4a1877b0e35c47329e7ed7e58014276168a37ba"),
        # test django 1.4 alphanumeric salt
        ("test", "sha1$bcwHF9Hy8lxS$6b4cfa0651b43161c6f1471ce9523acf1f751ba3"),
        # ensures utf-8 used for unicode
        (UPASS_USD, "sha1$c2e86$0f75c5d7fbd100d587c127ef0b693cde611b4ada"),
        (UPASS_TABLE, "sha1$6d853$ef13a4d8fb57aed0cb573fe9c82e28dc7fd372d4"),
        # generic password
        ("MyPassword", "sha1$54123$893cf12e134c3c215f3a76bd50d13f92404a54d3"),
    ]

    known_unidentified_hashes = [
        "md5$aa$bb",
    ]

    known_malformed_hashes = [
        # checksum too short
        "sha1$c2e86$0f75",
    ]

    # reuse custom random_salt_size() helper...
    FuzzHashGenerator = django_salted_md5_test.FuzzHashGenerator


class django_pbkdf2_sha256_test(HandlerCase, _DjangoHelper):
    """test django_pbkdf2_sha256"""

    handler = hash.django_pbkdf2_sha256

    known_correct_hashes = [
        #
        # custom - generated via django 1.4 hasher
        #
        (
            "not a password",
            "pbkdf2_sha256$10000$kjVJaVz6qsnJ$5yPHw3rwJGECpUf70daLGhOrQ5+AMxIJdz1c3bqK1Rs=",
        ),
        (
            UPASS_TABLE,
            "pbkdf2_sha256$10000$bEwAfNrH1TlQ$OgYUblFNUX1B8GfMqaCYUK/iHyO0pa7STTDdaEJBuY0=",
        ),
    ]


class django_pbkdf2_sha1_test(HandlerCase, _DjangoHelper):
    """test django_pbkdf2_sha1"""

    handler = hash.django_pbkdf2_sha1

    known_correct_hashes = [
        #
        # custom - generated via django 1.4 hashers
        #
        (
            "not a password",
            "pbkdf2_sha1$10000$wz5B6WkasRoF$atJmJ1o+XfJxKq1+Nu1f1i57Z5I=",
        ),
        (UPASS_TABLE, "pbkdf2_sha1$10000$KZKWwvqb8BfL$rw5pWsxJEU4JrZAQhHTCO+u0f5Y="),
    ]


@skipUnless(hash.bcrypt.has_backend(), "no bcrypt backends available")
class django_bcrypt_test(HandlerCase, _DjangoHelper):
    """test django_bcrypt"""

    handler = hash.django_bcrypt
    # XXX: not sure when this wasn't in default list anymore. somewhere in [2.0 - 2.2]
    max_django_version = (2, 0)
    fuzz_salts_need_bcrypt_repair = True

    known_correct_hashes = [
        #
        # just copied and adapted a few test vectors from bcrypt (above),
        # since django_bcrypt is just a wrapper for the real bcrypt class.
        #
        ("", "bcrypt$$2a$06$DCq7YPn5Rq63x1Lad4cll.TV4S6ytwfsfvkgY8jIucDrjc8deX1s."),
        (
            "abcdefghijklmnopqrstuvwxyz",
            "bcrypt$$2a$10$fVH8e28OQRj9tqiDXs1e1uxpsjN0c7II7YPKXua2NAKYvM6iQk7dq",
        ),
        (
            UPASS_TABLE,
            "bcrypt$$2a$05$Z17AXnnlpzddNUvnC6cZNOSwMA/8oNiKnHTHTwLlBijfucQQlHjaG",
        ),
    ]

    # NOTE: the following have been cloned from _bcrypt_test()

    def populate_settings(self, kwds):
        # speed up test w/ lower rounds
        kwds.setdefault("rounds", 4)
        super().populate_settings(kwds)

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        def random_rounds(self):
            # decrease default rounds for fuzz testing to speed up volume.
            return self.randintgauss(5, 8, 6, 1)

        def random_ident(self):
            # omit multi-ident tests, only $2a$ counts for this class
            # XXX: enable this to check 2a / 2b?
            return None


@skipUnless(hash.bcrypt.has_backend(), "no bcrypt backends available")
class django_bcrypt_sha256_test(HandlerCase, _DjangoHelper):
    """test django_bcrypt_sha256"""

    handler = hash.django_bcrypt_sha256
    forbidden_characters = None
    fuzz_salts_need_bcrypt_repair = True

    known_correct_hashes = [
        #
        # custom - generated via django 1.6 hasher
        #
        (
            "",
            "bcrypt_sha256$$2a$06$/3OeRpbOf8/l6nPPRdZPp.nRiyYqPobEZGdNRBWihQhiFDh1ws1tu",
        ),
        (
            UPASS_LETMEIN,
            "bcrypt_sha256$$2a$08$NDjSAIcas.EcoxCRiArvT.MkNiPYVhrsrnJsRkLueZOoV1bsQqlmC",
        ),
        (
            UPASS_TABLE,
            "bcrypt_sha256$$2a$06$kCXUnRFQptGg491siDKNTu8RxjBGSjALHRuvhPYNFsa4Ea5d9M48u",
        ),
        # test >72 chars is hashed correctly -- under bcrypt these hash the same.
        (
            repeat_string("abc123", 72),
            "bcrypt_sha256$$2a$06$Tg/oYyZTyAf.Nb3qSgN61OySmyXA8FoY4PjGizjE1QSDfuL5MXNni",
        ),
        (
            repeat_string("abc123", 72) + "qwr",
            "bcrypt_sha256$$2a$06$Tg/oYyZTyAf.Nb3qSgN61Ocy0BEz1RK6xslSNi8PlaLX2pe7x/KQG",
        ),
        (
            repeat_string("abc123", 72) + "xyz",
            "bcrypt_sha256$$2a$06$Tg/oYyZTyAf.Nb3qSgN61OvY2zoRVUa2Pugv2ExVOUT2YmhvxUFUa",
        ),
    ]

    known_malformed_hashers = [
        # data in django salt field
        "bcrypt_sha256$xyz$2a$06$/3OeRpbOf8/l6nPPRdZPp.nRiyYqPobEZGdNRBWihQhiFDh1ws1tu",
    ]

    # NOTE: the following have been cloned from _bcrypt_test()

    def populate_settings(self, kwds):
        # speed up test w/ lower rounds
        kwds.setdefault("rounds", 4)
        super().populate_settings(kwds)

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        def random_rounds(self):
            # decrease default rounds for fuzz testing to speed up volume.
            return self.randintgauss(5, 8, 6, 1)

        def random_ident(self):
            # omit multi-ident tests, only $2a$ counts for this class
            # XXX: enable this to check 2a / 2b?
            return None


@skipUnless(hash.argon2.has_backend(), "no argon2 backends available")
class django_argon2_test(HandlerCase, _DjangoHelper):
    """test django_bcrypt"""

    handler = hash.django_argon2

    # NOTE: most of this adapted from _base_argon2_test & argon2pure test

    known_correct_hashes = [
        # sample test
        (
            "password",
            "argon2$argon2i$v=19$m=256,t=1,p=1$c29tZXNhbHQ$AJFIsNZTMKTAewB4+ETN1A",
        ),
        # sample w/ all parameters different
        (
            "password",
            "argon2$argon2i$v=19$m=380,t=2,p=2$c29tZXNhbHQ$SrssP8n7m/12VWPM8dvNrw",
        ),
        # generated from django 1.10.3
        (
            UPASS_LETMEIN,
            "argon2$argon2i$v=19$m=512,t=2,p=2$V25jN1l4UUJZWkR1$MxpA1BD2Gh7+D79gaAw6sQ",
        ),
    ]

    def setUpWarnings(self):
        super().setUpWarnings()
        warnings.filterwarnings("ignore", ".*Using argon2pure backend.*")

    def do_stub_encrypt(self, handler=None, **settings):
        # overriding default since no way to get stub config from argon2._calc_hash()
        # (otherwise test_21b_max_rounds blocks trying to do max rounds)
        handler = (handler or self.handler).using(**settings)
        wrapped = handler.wrapped(use_defaults=True)
        wrapped.checksum = wrapped._stub_checksum
        assert wrapped.checksum
        return handler._wrap_hash(wrapped.to_string())

    def test_03_legacy_hash_workflow(self):
        # override base method
        raise self.skipTest("legacy 1.6 workflow not supported")

    class FuzzHashGenerator(_base_argon2_test.FuzzHashGenerator):
        def random_type(self):
            # override default since django only uses type I (see note in class)
            return "I"

        def random_rounds(self):
            # decrease default rounds for fuzz testing to speed up volume.
            return self.randintgauss(1, 3, 2, 1)
