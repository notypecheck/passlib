# `passlib.crypto.digest` - Hash & Related Helpers

Internal cryptographic helpers.

This module provides various cryptographic support functions used by Passlib
to implement the various password hashes it provides, as well as paper over
some VM & version incompatibilities.

## Hash Functions

::: passlib.crypto.digest.norm_hash_name

::: passlib.crypto.digest.lookup_hash

!!! note
    `lookup_hash()` supports all hashes available directly in `hashlib`, as well as offered through `hashlib.new`. It will also fallback to passlib's builtin MD4 implementation if one is not natively available.

::: passlib.crypto.digest.HashInfo


## PKCS#5 Key Derivation Functions

::: passlib.crypto.digest.pbkdf1

::: passlib.crypto.digest.pbkdf2_hmac

### `PBKDF2_BACKENDS`

List of the pbkdf2 backends in use (listed in order of priority).

!!! note
    Added in 1.7.

::: passlib.crypto.digest.PBKDF2_BACKENDS

!!! note
    The details of PBKDF1 and PBKDF2 are specified in [RFC 2898](https://tools.ietf.org/html/rfc2898).
