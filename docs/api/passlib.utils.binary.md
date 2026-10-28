# `passlib.utils.binary` - Binary Helper Functions

Internal helpers for binary data.

!!! warning
    This module is primarily used as an internal support module. Its interface has not been finalized yet, and may be changed somewhat between major releases of Passlib, as the internal code is cleaned up and simplified.

## Constants

### `BASE64_CHARS`

Character map used by standard MIME-compatible Base64 encoding scheme.

::: passlib.utils.binary.BASE64_CHARS

### `HASH64_CHARS`

Base64 character map used by a number of hash formats; the ordering is wildly different from the standard base64 character map.

This encoding system appears to have originated with [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md), but is used by [`passlib.hash.md5_crypt`](passlib.hash.md5_crypt.md), [`passlib.hash.sha256_crypt`](passlib.hash.sha256_crypt.md), and others. Within Passlib, this encoding is referred as the "hash64" encoding, to distinguish it from normal base64 and others.

::: passlib.utils.binary.HASH64_CHARS

### `BCRYPT_CHARS`

Base64 character map used by [`passlib.hash.bcrypt`](passlib.hash.bcrypt.md). The ordering is wildly different from both the standard base64 character map, and the common hash64 character map.

::: passlib.utils.binary.BCRYPT_CHARS

## Base64 Encoding

### `Base64Engine` Class

Passlib has to deal with a number of different Base64 encodings, with varying endianness, as well as wildly different character <-> value mappings. This is all encapsulated in the `Base64Engine` class, which provides common encoding actions for an arbitrary base64-style encoding scheme. There are also a couple of predefined instances which are commonly used by the hashes in Passlib.

::: passlib.utils.binary.Base64Engine

### Predefined Instances

#### `h64`

Predefined instance of `Base64Engine` which uses the `HASH64_CHARS` character map and little-endian encoding. (see `HASH64_CHARS` above for more details).

::: passlib.utils.binary.h64

#### `h64big`

Predefined variant of `h64` which uses big-endian encoding. This is mainly used by [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md).

::: passlib.utils.binary.h64big

!!! warning
    Changed in 1.6: Previous versions of Passlib contained a module named `passlib.utils.h64`; As of Passlib 1.6 this was replaced by the ``h64`` and ``h64big`` instances of the `Base64Engine` class; the interface remains mostly unchanged.

### Other

::: passlib.utils.binary.ab64_encode

::: passlib.utils.binary.ab64_decode

::: passlib.utils.binary.b64s_encode

::: passlib.utils.binary.b64s_decode

::: passlib.utils.binary.b32encode

::: passlib.utils.binary.b32decode
