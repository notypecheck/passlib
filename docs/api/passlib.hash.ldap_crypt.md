# `passlib.hash.ldap_{crypt}` - LDAP crypt() Wrappers

Passlib provides support for all the standard LDAP hash formats specified by RFC 2307. One of these, identified by RFC 2307 as the `{CRYPT}` scheme, is somewhat different from the others. Instead of specifying a password hashing scheme, it's supposed to wrap the host OS's `crypt()`. Being host-dependant, the actual hashes supported by this scheme may differ greatly between host systems. In order to provide uniform support across platforms, Passlib defines a corresponding `ldap_{crypt-scheme}` class for each of the `standard unix hashes`. These classes all wrap the underlying implementations documented elsewhere in Passlib, and can be used directly as follows:

```python
from passlib.hash import ldap_md5_crypt

# hash password
hash = ldap_md5_crypt.hash("password")
print(hash)
# > '{CRYPT}$1$gwvn5BO0$3dyk8j.UTcsNUPrLMsU6/0'

# verify password
print(ldap_md5_crypt.verify("password", hash))
# > True
print(ldap_md5_crypt.verify("secret", hash))
# > False

# determine if the underlying crypt() algorithm is supported
# by your host OS, or if the builtin Passlib implementation is being used.
# "os_crypt" - host supported; "builtin" - passlib version
print(ldap_md5_crypt.get_backend())
# > "os_crypt"
```

!!! tip
    - `password hash usage` -- for more usage examples

    - [`ldap_{digest}`](passlib.hash.ldap_std.md) -- for the other standard LDAP hashes.

    - `passlib.apps` -- for a list of `premade ldap contexts`.

## Interface

All of these classes (`ldap_des_crypt`, `ldap_bsdi_crypt`, `ldap_md5_crypt`, `ldap_bcrypt`, `ldap_sha1_crypt`, `ldap_sha256_crypt`, and `ldap_sha512_crypt`) have the same interface as their corresponding underlying hash (e.g. `des_crypt`, `md5_crypt`, etc), i.e. the standard [`PasswordHash`](passlib.ifc.md) interface.

## References

- The manpage for `slappasswd` - <http://gd.tuwien.ac.at/linuxcommand.org/man_pages/slappasswd8.html>
- The basic format for these hashes is laid out in RFC 2307 - <http://www.ietf.org/rfc/rfc2307.txt>
