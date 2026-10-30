# `passlib.hash.ldap_{digest}` - RFC2307 Standard Digests

Passlib provides support for all the standard
LDAP hash formats specified by RFC 2307.
This includes `{MD5}`, `{SMD5}`, `{SHA}`, `{SSHA}`.
These schemes range from somewhat to very insecure,
and should not be used except when required.
These classes all wrap the underlying hashlib implementations,
and are can be used directly as follows:

```python
from passlib.hash import ldap_salted_md5 as lsm

# hash password
hash = lsm.hash("password")
print(hash)
# > '{SMD5}OqsUXNHIhHbznxrqHoIM+ZT8DmE='

# verify password
print(lsm.verify("password", hash))
# > True
print(lsm.verify("secret", hash))
# > False
```

!!! tip
    - `password hash usage` -- for more usage examples

    - [`passlib.hash.ldap_{crypt}`](passlib.hash.ldap_crypt.md) -- LDAP `{CRYPT}` wrappers for common Unix hash algorithms.

    - `passlib.apps` -- for a list of premade ldap contexts.

## Plain Hashes

!!! warning
    These hashes should not be considered secure in any way,
    as they are nothing but raw MD5 & SHA-1 digests,
    which are extremely vulnerable to brute-force attacks.

These are simple wrappers around the raw `md5` and `sha1` digests, all sharing the standard [`PasswordHash`](passlib.ifc.md) interface.

### Format

These hashes have the format `{prefix}{checksum}`.

- `{prefix}` is `{MD5}` for `ldap_md5`, and `{SHA}` for `ldap_sha1`.
- `{checksum}` is the base64 encoding
  of the raw message digest of the password,
  using the appropriate digest algorithm.

An example `ldap_md5` hash (of `password`) is `{MD5}X03MO1qnZdYdgyfeuILPmQ==`.
An example `ldap_sha1` hash (of `password`) is `{SHA}W6ph5Mm5Pz8GgiULbPgzG37mj9g=`.

## Salted Hashes

`ldap_salted_md5`, `ldap_salted_sha1`, `ldap_salted_sha256`, and `ldap_salted_sha512` all share the standard [`PasswordHash`](passlib.ifc.md) interface.

These hashes have the format `{prefix}{data}`.

- `{prefix}` is `{SMD5}` for `ldap_salted_md5`,
  and `{SSHA}` for `ldap_salted_sha1`.
- `{data}` is the base64 encoding of `{checksum}{salt}`;
  and in turn `{salt}` is a multi-byte binary salt,
  and `{checksum}` is the raw digest of the
  the string `{password}{salt}`,
  using the appropriate digest algorithm.

### Format

An example hash (of `password`) is `{SMD5}jNoSMNY0cybfuBWiaGlFw3Mfi/U=`.
After decoding, this results in a raw salt string `s\x1f\x8b\xf5`,
and a raw MD5 checksum of `\x8c\xda\x120\xd64s&\xdf\xb8\x15\xa2hiE\xc3`.

An example hash (of `password`) is `{SSHA}pKqkNr1tq3wtQqk+UcPyA3HnA2NsU5NJ`.
After decoding, this results in a raw salt string `lS\x93I`,
and a raw SHA1 checksum of `\xa4\xaa\xa46\xbdm\xab|-B\xa9>Q\xc3\xf2\x03q\xe7\x03c`.

### Security Issues

The LDAP salted hashes should not be considered very secure.

- They use only a single round of digests with known collision
  and pre-image attacks (SHA1 & MD5).

- They currently use only 32 bits of entropy in their salt,
  which is only borderline sufficient to defeat rainbow tables,
  and cannot (portably) be increased.

- The SHA2 salted hashes (SSHA256, SSHA512) are only marginally better.
  they use the newer SHA2 hash; and 64 bits of entropy in their salt.

## Plaintext

`ldap_plaintext` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

This handler does not hash passwords at all,
rather it encoded them into UTF-8.
The only difference between this class and `plaintext`
is that this class will NOT recognize any strings that use
the `{SCHEME}HASH` format.

## Deviations

- The salt size for the salted digests appears to vary between applications.
  While OpenLDAP is fixed at 4 bytes, some systems appear to use 8 or more.
  As of 1.6, Passlib can accept and generate strings with salts between 4-16 bytes,
  though various servers may differ in what they can handle.

## References

- The manpage for `slappasswd` - <http://gd.tuwien.ac.at/linuxcommand.org/man_pages/slappasswd8.html>
- The basic format for these hashes is laid out in RFC 2307 - <http://www.ietf.org/rfc/rfc2307.txt>
- OpenLDAP hash documentation - <http://www.openldap.org/doc/admin24/security.html>
