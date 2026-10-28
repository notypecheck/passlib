"""Cisco password hashes"""

import binascii
from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify
from hashlib import md5
from warnings import warn

import passlib.utils.handlers as uh
from passlib.crypto.digest import pbkdf2_hmac
from passlib.crypto.scrypt import scrypt as _scrypt
from passlib.handlers.md5_crypt import md5_crypt
from passlib.utils import repeat_string, right_pad_string, to_unicode
from passlib.utils.binary import h64, h64big

__all__ = [
    "cisco_pix",
    "cisco_asa",
    "cisco_asa_pbkdf2",
    "cisco_type7",
    "cisco_type8",
    "cisco_type9",
    "cisco_convoluted_type9",
]


#: dummy bytes used by spoil_digest var in cisco_pix._calc_checksum()
_DUMMY_BYTES = b"\xff" * 32


class cisco_pix(uh.HasUserContext, uh.StaticHandler):
    """
    This class implements the password hash used by older Cisco PIX firewalls,
    and follows the :ref:`password-hash-api`.
    It does a single round of hashing, and relies on the username
    as the salt.

    This class only allows passwords <= 16 bytes, anything larger
    will result in a :exc:`~passlib.exc.PasswordSizeError` if passed to :meth:`~cisco_pix.hash`,
    and be silently rejected if passed to :meth:`~cisco_pix.verify`.

    The :meth:`~passlib.ifc.PasswordHash.hash`,
    :meth:`~passlib.ifc.PasswordHash.genhash`, and
    :meth:`~passlib.ifc.PasswordHash.verify` methods
    all support the following extra keyword:

    :param str user:
        String containing name of user account this password is associated with.

        This is *required* in order to correctly hash passwords associated
        with a user account on the Cisco device, as it is used to salt
        the hash.

        Conversely, this *must* be omitted or set to ``""`` in order to correctly
        hash passwords which don't have an associated user account
        (such as the "enable" password).

    .. versionadded:: 1.6

    .. versionchanged:: 1.7.1

        Passwords > 16 bytes are now rejected / throw error instead of being silently truncated,
        to match Cisco behavior.  A number of :ref:`bugs <passlib-asa96-bug>` were fixed
        which caused prior releases to generate unverifiable hashes in certain cases.
    """

    # --------------------
    # PasswordHash
    # --------------------
    name = "cisco_pix"

    truncate_size = 16

    # NOTE: these are the default policy for PasswordHash,
    #       but want to set them explicitly for now.
    truncate_error = True
    truncate_verify_reject = True

    # --------------------
    # GenericHandler
    # --------------------
    checksum_size = 16
    checksum_chars = uh.HASH64_CHARS

    # --------------------
    # custom
    # --------------------

    #: control flag signalling "cisco_asa" mode, set by cisco_asa class
    _is_asa = False

    def _calc_checksum(self, secret):
        """
        This function implements the "encrypted" hash format used by Cisco
        PIX & ASA. It's behavior has been confirmed for ASA 9.6,
        but is presumed correct for PIX & other ASA releases,
        as it fits with known test vectors, and existing literature.

        While nearly the same, the PIX & ASA hashes have slight differences,
        so this function performs differently based on the _is_asa class flag.
        Noteable changes from PIX to ASA include password size limit
        increased from 16 -> 32, and other internal changes.
        """
        # select PIX vs or ASA mode
        asa = self._is_asa

        #
        # encode secret
        #
        # per ASA 8.4 documentation,
        # http://www.cisco.com/c/en/us/td/docs/security/asa/asa84/configuration/guide/asa_84_cli_config/ref_cli.html#Supported_Character_Sets,
        # it supposedly uses UTF-8 -- though some double-encoding issues have
        # been observed when trying to actually *set* a non-ascii password
        # via ASDM, and access via SSH seems to strip 8-bit chars.
        #
        if isinstance(secret, str):
            secret = secret.encode("utf-8")

        #
        # check if password too large
        #
        # Per ASA 9.6 changes listed in
        # http://www.cisco.com/c/en/us/td/docs/security/asa/roadmap/asa_new_features.html,
        # prior releases had a maximum limit of 32 characters.
        # Testing with an ASA 9.6 system bears this out --
        # setting 32-char password for a user account,
        # and logins will fail if any chars are appended.
        # (ASA 9.6 added new PBKDF2-based hash algorithm,
        #  which supports larger passwords).
        #
        # Per PIX documentation
        # http://www.cisco.com/en/US/docs/security/pix/pix50/configuration/guide/commands.html,
        # it would not allow passwords > 16 chars.
        #
        # Thus, we unconditionally throw a password size error here,
        # as nothing valid can come from a larger password.
        # NOTE: assuming PIX has same behavior, but at 16 char limit.
        #
        spoil_digest = None
        if len(secret) > self.truncate_size:
            if self.use_defaults:
                # called from hash()
                msg = "Password too long (%s allows at most %d bytes)" % (
                    self.name,
                    self.truncate_size,
                )
                raise uh.exc.PasswordSizeError(self.truncate_size, msg=msg)
            # called from verify() --
            # We don't want to throw error, or return early,
            # as that would let attacker know too much.  Instead, we set a
            # flag to add some dummy data into the md5 digest, so that
            # output won't match truncated version of secret, or anything
            # else that's fixed and predictable.
            spoil_digest = secret + _DUMMY_BYTES

        #
        # append user to secret
        #
        # Policy appears to be:
        #
        # * Nothing appended for enable password (user = "")
        #
        # * ASA: If user present, but secret is >= 28 chars, nothing appended.
        #
        # * 1-2 byte users not allowed.
        #   DEVIATION: we're letting them through, and repeating their
        #   chars ala 3-char user, to simplify testing.
        #   Could issue warning in the future though.
        #
        # * 3 byte user has first char repeated, to pad to 4.
        #   (observed under ASA 9.6, assuming true elsewhere)
        #
        # * 4 byte users are used directly.
        #
        # * 5+ byte users are truncated to 4 bytes.
        #
        user = self.user
        if user:
            if isinstance(user, str):
                user = user.encode("utf-8")
            if not asa or len(secret) < 28:
                secret += repeat_string(user, 4)

        #
        # pad / truncate result to limit
        #
        # While PIX always pads to 16 bytes, ASA increases to 32 bytes IFF
        # secret+user > 16 bytes.  This makes PIX & ASA have different results
        # where secret size in range(13,16), and user is present --
        # PIX will truncate to 16, ASA will truncate to 32.
        #
        if asa and len(secret) > 16:  # noqa: SIM108
            pad_size = 32
        else:
            pad_size = 16
        secret = right_pad_string(secret, pad_size)

        #
        # md5 digest
        #
        if spoil_digest:
            # make sure digest won't match truncated version of secret
            secret += spoil_digest
        digest = md5(secret).digest()

        #
        # drop every 4th byte
        # NOTE: guessing this was done because it makes output exactly
        #       16 bytes, which may have been a general 'char password[]'
        #       size limit under PIX
        #
        digest = bytes(c for i, c in enumerate(digest) if (i + 1) & 3)

        #
        # encode using Hash64
        #
        return h64.encode_bytes(digest).decode("ascii")

    # NOTE: works, but needs UTs.
    # @classmethod
    # def same_as_pix(cls, secret, user=""):
    #     """
    #     test whether (secret + user) combination should
    #     have the same hash under PIX and ASA.
    #
    #     mainly present to help unittests.
    #     """
    #     # see _calc_checksum() above for details of this logic.
    #     size = len(to_bytes(secret, "utf-8"))
    #     if user and size < 28:
    #         size += 4
    #     return size < 17


class cisco_asa(cisco_pix):
    """
    This class implements the password hash used by Cisco ASA/PIX 7.0 and newer (2005).
    Aside from a different internal algorithm, it's use and format is identical
    to the older :class:`cisco_pix` class.

    For passwords less than 13 characters, this should be identical to :class:`!cisco_pix`,
    but will generate a different hash for most larger inputs
    (See the `Format & Algorithm`_ section for the details).

    This class only allows passwords <= 32 bytes, anything larger
    will result in a :exc:`~passlib.exc.PasswordSizeError` if passed to :meth:`~cisco_asa.hash`,
    and be silently rejected if passed to :meth:`~cisco_asa.verify`.

    .. versionadded:: 1.7

    .. versionchanged:: 1.7.1

        Passwords > 32 bytes are now rejected / throw error instead of being silently truncated,
        to match Cisco behavior.  A number of :ref:`bugs <passlib-asa96-bug>` were fixed
        which caused prior releases to generate unverifiable hashes in certain cases.
    """

    # --------------------
    # PasswordHash
    # --------------------
    name = "cisco_asa"

    # --------------------
    # TruncateMixin
    # --------------------
    truncate_size = 32

    # --------------------
    # cisco_pix
    # --------------------
    _is_asa = True


class cisco_type7(uh.GenericHandler):
    """
    This class implements the "Type 7" password encoding used by Cisco IOS,
    and follows the :ref:`password-hash-api`.
    It has a simple 4-5 bit salt, but is nonetheless a reversible encoding
    instead of a real hash.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: int
    :param salt:
        This may be an optional salt integer drawn from ``range(0,16)``.
        If omitted, one will be chosen at random.

    :type relaxed: bool
    :param relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasslibHashWarning`
        will be issued instead. Correctable errors include
        ``salt`` values that are out of range.

    Note that while this class outputs digests in upper-case hexadecimal,
    it will accept lower-case as well.

    This class also provides the following additional method:

    .. automethod:: decode
    """

    # --------------------
    # PasswordHash
    # --------------------
    name = "cisco_type7"
    setting_kwds = ("salt",)

    # --------------------
    # GenericHandler
    # --------------------
    checksum_chars = uh.UPPER_HEX_CHARS

    # --------------------
    # HasSalt
    # --------------------

    # NOTE: encoding could handle max_salt_value=99, but since key is only 52
    #       chars in size, not sure what appropriate behavior is for that edge case.
    min_salt_value = 0
    max_salt_value = 52

    @classmethod
    def using(cls, salt=None, **kwds):
        subcls = super().using(**kwds)
        if salt is not None:
            salt = subcls._norm_salt(salt, relaxed=kwds.get("relaxed"))
            subcls._generate_salt = staticmethod(lambda: salt)
        return subcls

    @classmethod
    def from_string(cls, hash):
        hash = to_unicode(hash, "ascii", "hash")
        if len(hash) < 2:
            raise uh.exc.InvalidHashError(cls)
        salt = int(hash[:2])  # may throw ValueError
        return cls(salt=salt, checksum=hash[2:].upper())

    def __init__(self, salt=None, **kwds):
        super().__init__(**kwds)
        if salt is not None:
            salt = self._norm_salt(salt)
        elif self.use_defaults:
            salt = self._generate_salt()
            assert self._norm_salt(salt) == salt, f"generated invalid salt: {salt!r}"
        else:
            raise TypeError("no salt specified")
        self.salt = salt

    @classmethod
    def _norm_salt(cls, salt, relaxed=False):
        """
        validate & normalize salt value.
        .. note::
            the salt for this algorithm is an integer 0-52, not a string
        """
        if not isinstance(salt, int):
            raise uh.exc.ExpectedTypeError(salt, "integer", "salt")
        if 0 <= salt <= cls.max_salt_value:
            return salt
        msg = "salt/offset must be in 0..52 range"
        if relaxed:
            warn(msg, uh.PasslibHashWarning)
            return 0 if salt < 0 else cls.max_salt_value
        raise ValueError(msg)

    @staticmethod
    def _generate_salt():
        return uh.rng.randint(0, 15)

    def to_string(self):
        return "%02d%s" % (self.salt, self.checksum)

    def _calc_checksum(self, secret):
        # XXX: no idea what unicode policy is, but all examples are
        # 7-bit ascii compatible, so using UTF-8
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        return hexlify(self._cipher(secret, self.salt)).decode("ascii").upper()

    @classmethod
    def decode(cls, hash, encoding="utf-8"):
        """decode hash, returning original password.

        :arg hash: encoded password
        :param encoding: optional encoding to use (defaults to ``UTF-8``).
        :returns: password as unicode
        """
        self = cls.from_string(hash)
        tmp = unhexlify(self.checksum.encode("ascii"))
        raw = self._cipher(tmp, self.salt)
        return raw.decode(encoding) if encoding else raw

    # type7 uses a xor-based vingere variant, using the following secret key:
    _key = "dsfd;kfoA,.iyewrkldJKDHSUBsgvca69834ncxv9873254k;fg87"

    @classmethod
    def _cipher(cls, data: bytes, salt: int):
        """xor static key against data - encrypts & decrypts"""
        key = cls._key
        key_size = len(key)
        return bytes(
            value ^ ord(key[(salt + idx) % key_size]) for idx, value in enumerate(data)
        )


class _CiscoSaltedHash(uh.TruncateMixin, uh.HasSalt, uh.GenericHandler):  # type: ignore[misc]
    """Common code for cisco_type8 and cisco_type9."""

    setting_kwds = ("salt", "truncate_error")
    checksum_chars = uh.HASH64_CHARS
    checksum_size = 43

    salt_chars = uh.HASH64_CHARS
    min_salt_size = max_salt_size = 14

    # IOS XE 17.15 hashes only the first 127 bytes of a longer password.
    truncate_size = 127

    @classmethod
    def from_string(cls, hash):
        salt, chk = uh.parse_mc2(hash, cls.ident, handler=cls)
        return cls(salt=salt, checksum=chk)

    def to_string(self):
        return uh.render_mc2(self.ident, self.salt, self.checksum)

    def _calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if self.use_defaults:
            self._check_truncate_policy(secret)
        key = self._derive(secret[: self.truncate_size], self.salt.encode("ascii"))
        return h64big.encode_bytes(key).decode("ascii")


class cisco_type8(_CiscoSaltedHash):
    """
    This class implements the "Type 8" password hash used by Cisco IOS and
    IOS XE, and follows the :ref:`password-hash-api`.
    It is PBKDF2-HMAC-SHA256 with 20000 rounds and a 14 character salt.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string.
        If not specified, one will be autogenerated (this is recommended).
        If specified, it must be 14 characters, drawn from the regexp range ``[./0-9A-Za-z]``.

    :param bool truncate_error:
        By default, passwords longer than 127 bytes are silently truncated,
        as IOS XE does. Setting ``truncate_error=True`` will cause
        :meth:`~passlib.ifc.PasswordHash.hash` to raise a
        :exc:`~passlib.exc.PasswordTruncateError` instead.

    .. versionadded:: 1.10
    """

    name = "cisco_type8"
    ident = "$8$"

    @staticmethod
    def _derive(secret, salt):
        return pbkdf2_hmac("sha256", secret, salt, 20000, 32)


class cisco_type9(_CiscoSaltedHash):
    """
    This class implements the "Type 9" password hash used by Cisco IOS and
    IOS XE, and follows the :ref:`password-hash-api`.
    It is scrypt with N=16384, r=1, p=1 and a 14 character salt.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string.
        If not specified, one will be autogenerated (this is recommended).
        If specified, it must be 14 characters, drawn from the regexp range ``[./0-9A-Za-z]``.

    :param bool truncate_error:
        By default, passwords longer than 127 bytes are silently truncated,
        as IOS XE does. Setting ``truncate_error=True`` will cause
        :meth:`~passlib.ifc.PasswordHash.hash` to raise a
        :exc:`~passlib.exc.PasswordTruncateError` instead.

    .. versionadded:: 1.10
    """

    name = "cisco_type9"
    ident = "$9$"

    @classmethod
    def identify(cls, hash):
        # junos9 secrets start with "$9$" too, but have no second "$"
        hash = uh.to_unicode_for_identify(hash)
        return hash.startswith(cls.ident) and "$" in hash[len(cls.ident) :]

    @staticmethod
    def _derive(secret, salt):
        return _scrypt(secret, salt, 16384, 1, 1, 32)


class cisco_convoluted_type9(uh.HasSalt, uh.GenericHandler):  # type: ignore[misc]
    """
    This class implements the "convoluted Type 9" hash Cisco IOS XE stores when
    it converts a Type 5 secret, and follows the :ref:`password-hash-api`.
    It is scrypt (as in :class:`cisco_type9`) of the :class:`md5_crypt` hash
    of the password.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string.
        If not specified, one will be autogenerated (this is recommended).
        If specified, it must be 18 characters, drawn from the regexp range ``[./0-9A-Za-z]``:
        the 4 character md5_crypt salt, followed by the 14 character scrypt salt.

    .. versionadded:: 1.10
    """

    name = "cisco_convoluted_type9"
    ident = "$14$"
    setting_kwds = ("salt",)
    checksum_chars = uh.HASH64_CHARS
    checksum_size = 43

    salt_chars = uh.HASH64_CHARS
    min_salt_size = max_salt_size = 18

    @classmethod
    def from_string(cls, hash):
        hash = to_unicode(hash, "ascii", "hash")
        if not hash.startswith(cls.ident):
            raise uh.exc.InvalidHashError(cls)
        parts = hash[len(cls.ident) :].split("$")
        if len(parts) != 3 or len(parts[0]) != 4:
            raise uh.exc.MalformedHashError(cls)
        md5_salt, salt, chk = parts
        return cls(salt=md5_salt + salt, checksum=chk)

    def to_string(self):
        return f"{self.ident}{self.salt[:4]}${self.salt[4:]}${self.checksum}"

    def _calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        type5 = md5_crypt.using(salt=self.salt[:4]).hash(secret)
        key = cisco_type9._derive(type5.encode("ascii"), self.salt[4:].encode("ascii"))
        return h64big.encode_bytes(key).decode("ascii")


class cisco_asa_pbkdf2(  # type: ignore[misc]
    uh.HasRounds, uh.HasRawSalt, uh.HasRawChecksum, uh.GenericHandler
):
    """
    This class implements the "pbkdf2" password hash used by Cisco ASA
    (``username NAME password HASH pbkdf2``), and follows the :ref:`password-hash-api`.
    It is PBKDF2-HMAC-SHA512 with a 16 byte salt, keeping the first 16 bytes
    of the digest. Unlike :class:`cisco_asa`, the username isn't hashed in.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: bytes
    :param salt:
        Optional salt bytes.
        If specified, the length must be 16 bytes.
        If not specified, a salt will be autogenerated (this is recommended).

    :type rounds: int
    :param rounds:
        Optional number of rounds to use.
        Defaults to 5000, which is what ASA 9.24 generates.

    :param bool relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasswordHashWarning`
        will be issued instead. Correctable errors include ``rounds``
        that are too small or too large, and ``salt`` strings that are too long.

    .. versionadded:: 1.10
    """

    name = "cisco_asa_pbkdf2"
    ident = "$sha512$"
    setting_kwds = ("salt", "rounds")

    # ASA 9.24 refuses a password longer than 127 bytes.
    truncate_size = 127
    truncate_error = True
    truncate_verify_reject = True

    checksum_size = 16

    min_salt_size = max_salt_size = default_salt_size = 16

    default_rounds = 5000
    min_rounds = 1
    max_rounds = 0xFFFFFFFF
    rounds_cost = "linear"

    @classmethod
    def _decode(cls, value, size):
        try:
            data = b64decode(value.encode("ascii"), validate=True)
        except (binascii.Error, UnicodeEncodeError):
            raise uh.exc.MalformedHashError(cls, "invalid base64") from None
        if len(data) != size or b64encode(data).decode("ascii") != value:
            raise uh.exc.MalformedHashError(cls, "invalid base64")
        return data

    @classmethod
    def from_string(cls, hash):
        rounds, salt, chk = uh.parse_mc3(hash, cls.ident, handler=cls)
        salt = cls._decode(salt, cls.max_salt_size)
        if chk:
            chk = cls._decode(chk, cls.checksum_size)
        return cls(rounds=rounds, salt=salt, checksum=chk)

    def to_string(self):
        salt = b64encode(self.salt).decode("ascii")
        chk = b64encode(self.checksum).decode("ascii")
        return uh.render_mc3(self.ident, self.rounds, salt, chk)

    def _calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        if self.use_defaults and len(secret) > self.truncate_size:
            # hash() refuses it; verify() hashes it whole, so it never matches
            raise uh.exc.PasswordSizeError(
                self.truncate_size,
                msg="Password too long (%s allows at most %d bytes)"
                % (self.name, self.truncate_size),
            )
        return pbkdf2_hmac("sha512", secret, self.salt, self.rounds, 64)[
            : self.checksum_size
        ]
