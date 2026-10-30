# `passlib.hash.hex_{digest}` - Generic Hexadecimal Digests

!!! danger
    Using a single round of any cryptographic hash (especially without a salt) is so insecure that it's barely better than plaintext. Do not use these schemes in new applications.

Some existing applications store passwords by storing them using hexadecimal-encoded message digests, such as MD5 or SHA1. Such schemes are *extremely* vulnerable to pre-computed brute-force attacks, and should not be used in new applications. However, for the sake of backwards compatibility when converting existing applications, Passlib provides wrappers for few of the common hashes. These classes all wrap the underlying hashlib implementations, and can be used directly as follows:

```python
from passlib.hash import hex_sha1 as hex_sha1

# hash password
h = hex_sha1.hash("password")
print(h)
# > '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'

# verify correct password
print(hex_sha1.verify("password", h))
# > True

# verify incorrect password
print(hex_sha1.verify("secret", h))
# > False
```

!!! tip
    the generic `PasswordHash usage examples`

## Interface

::: passlib.hash.hex_md4

::: passlib.hash.hex_md5

::: passlib.hash.hex_sha1

::: passlib.hash.hex_sha256

::: passlib.hash.hex_sha512

Each of these classes implements a plain hexadecimal encoded message digest, using the relevant digest function from `hashlib`, and following the `password-hash-api`.

They support no settings or other keywords.

!!! note
    Oracle VirtualBox's `VBoxManager internalcommands passwordhash` command uses `hex_sha256`.

## Format & Algorithm

All of these classes just report the result of the specified digest, encoded as a series of lowercase hexadecimal characters; though upper case is accepted as input.
