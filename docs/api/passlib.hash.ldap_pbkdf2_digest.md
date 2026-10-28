# `passlib.hash.ldap_{digest}` - Generic PBKDF2 Hashes

Passlib provides three custom hash schemes based on the PBKDF2 [^pbkdf2] algorithm
which are compatible with the ldap hash format:
`ldap_pbkdf2_sha1`, `ldap_pbkdf2_sha256`, `ldap_pbkdf2_sha512`.
They feature variable length salts, variable rounds.

!!! tip
    These classes are simply wrappers around the [`passlib.hash.pbkdf2_digest`](passlib.hash.pbkdf2_digest.md) MCF-Compatible Simple PBKDF2 Hashes.

## Interface

`ldap_pbkdf2_sha1` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

This is the same as `pbkdf2_sha1`, except that it
uses `{PBKDF2}` as its identifying prefix instead of `$pdkdf2$`.

`ldap_pbkdf2_sha256` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

This is the same as `pbkdf2_sha256`, except that it
uses `{PBKDF2-SHA256}` as its identifying prefix instead of `$pdkdf2-sha256$`.

`ldap_pbkdf2_sha512` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

This is the same as `pbkdf2_sha512`, except that it
uses `{PBKDF2-SHA512}` as its identifying prefix instead of `$pdkdf2-sha512$`.

[^pbkdf2]: The specification for the PBKDF2 algorithm - <http://tools.ietf.org/html/rfc2898#section-5.2>, part of RFC 2898.
