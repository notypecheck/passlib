"""Juniper Junos "$9$" reversible encoding"""

import passlib.utils.handlers as uh
from passlib.utils import to_unicode

__all__ = [
    "junos9",
]

_FAMILIES = (
    "QzF3n6/9CAtpu0O",
    "B1IREhcSyrleKvMW8LXx",
    "7N-dVbwsY2g4oaJZGUDj",
    "iHkq.mPf5T",
)
_ALPHABET = "".join(_FAMILIES)
_INDEX = {c: i for i, c in enumerate(_ALPHABET)}

#: number of random characters following the salt character
_EXTRA = {c: 3 - i for i, family in enumerate(_FAMILIES) for c in family}

#: weights of the characters encoding each byte of the secret, used in turn
_ENCODING = (
    (1, 4, 32),
    (1, 16, 32),
    (1, 8, 32),
    (1, 64),
    (1, 32),
    (1, 4, 16, 128),
    (1, 32, 64),
)


class junos9(uh.GenericHandler):
    """
    This class implements the "$9$" encoding Juniper Junos uses for secrets
    such as RADIUS and TACACS+ keys, and follows the :ref:`password-hash-api`.
    It is a reversible encoding, not a hash.

    The :meth:`~passlib.ifc.PasswordHash.using` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string: one character from ``[./0-9A-Za-z-]``, followed
        by the 0-3 further characters it calls for.
        If omitted, one will be chosen at random.

    This class also provides the following additional method:

    .. automethod:: decode

    .. versionadded:: 1.10
    """

    name = "junos9"
    setting_kwds = ("salt",)
    ident = "$9$"
    checksum_chars = _ALPHABET

    @classmethod
    def using(cls, salt=None, **kwds):
        subcls = super().using(**kwds)
        if salt is not None:
            salt = subcls._norm_salt(salt)
            subcls._generate_salt = staticmethod(lambda: salt)
        return subcls

    @classmethod
    def identify(cls, hash):
        # cisco_type9 hashes start with "$9$" too, but have a second "$"
        hash = uh.to_unicode_for_identify(hash)
        return hash.startswith(cls.ident) and "$" not in hash[len(cls.ident) :]

    @classmethod
    def from_string(cls, hash):
        hash = to_unicode(hash, "ascii", "hash")
        if not hash.startswith(cls.ident):
            raise uh.exc.InvalidHashError(cls)
        data = hash[len(cls.ident) :]
        if not data or data[0] not in _EXTRA:
            raise uh.exc.MalformedHashError(cls)
        size = 1 + _EXTRA[data[0]]
        if len(data) < size:
            raise uh.exc.MalformedHashError(cls)
        return cls(salt=data[:size], checksum=data[size:])

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
    def _norm_salt(cls, salt):
        if not isinstance(salt, str):
            raise uh.exc.ExpectedTypeError(salt, "str", "salt")
        if (
            not salt
            or any(c not in _INDEX for c in salt)
            or len(salt) != 1 + _EXTRA[salt[0]]
        ):
            raise ValueError(f"invalid salt for {cls.name}: {salt!r}")
        return salt

    @staticmethod
    def _generate_salt():
        first = uh.rng.choice(_ALPHABET)
        return first + "".join(uh.rng.choice(_ALPHABET) for _ in range(_EXTRA[first]))

    def _norm_checksum(self, checksum, relaxed=False):
        checksum = super()._norm_checksum(checksum, relaxed=relaxed)
        size, idx = len(checksum), 0
        while size > 0:
            size -= len(_ENCODING[idx % len(_ENCODING)])
            idx += 1
        if size:
            raise uh.exc.MalformedHashError(self.__class__, "truncated checksum")
        return checksum

    def to_string(self):
        return f"{self.ident}{self.salt}{self.checksum}"

    def _calc_checksum(self, secret):
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        previous = _INDEX[self.salt[0]]
        out = []
        for idx, value in enumerate(secret):
            gaps = []
            for weight in reversed(_ENCODING[idx % len(_ENCODING)]):
                gaps.append(value // weight)
                value %= weight
            for gap in reversed(gaps):
                previous = (previous + gap + 1) % len(_ALPHABET)
                out.append(_ALPHABET[previous])
        return "".join(out)

    @classmethod
    def decode(cls, hash, encoding="utf-8"):
        """decode hash, returning original password.

        :arg hash: encoded password
        :param encoding: optional encoding to use (defaults to ``UTF-8``).
        :returns: password as unicode
        """
        self = cls.from_string(hash)
        previous = _INDEX[self.salt[0]]
        chars = [_INDEX[c] for c in self.checksum]
        raw = bytearray()
        while chars:
            weights = _ENCODING[len(raw) % len(_ENCODING)]
            value = 0
            for weight, current in zip(weights, chars):
                value += ((current - previous - 1) % len(_ALPHABET)) * weight
                previous = current
            if value > 255:
                raise uh.exc.MalformedHashError(cls, "invalid checksum")
            raw.append(value)
            chars = chars[len(weights) :]
        raw = bytes(raw)
        return raw.decode(encoding) if encoding else raw
