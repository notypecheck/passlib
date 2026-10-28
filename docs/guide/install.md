# Installation

## Supported Platforms

Passlib requires Python 3.9 or newer.

Passlib should work with all operating systems and environments, as it contains builtin fallbacks for almost all OS-dependent features.

!!! warning
    **Passlib `1.8` drops support for Python < 3.9, Jython and PyPy.**
    Starting with `1.10`, [versions that have reached EOL](https://devguide.python.org/versions/) will no longer be supported.

## Optional Libraries

- [`bcrypt`](https://pypi.org/project/bcrypt/)
   If installed, this will be used to handle `passlib.hash.bcrypt` and
   `passlib.hash.bcrypt_sha256` hashes.  
   Use `pip install passlib[bcrypt]` to get the recommended bcrypt setup.

- [`argon2_cffi`](https://pypi.org/project/argon2-cffi/)
   If `argon2_cffi` is installed, it will be used to provide
   support for the `passlib.hash.argon2` hash algorithm.  
   Use ``pip install passlib[argon2]`` to get the recommended argon2 setup.

- [`cryptography`](https://pypi.org/project/cryptography/)
   If installed, will be used to enable encryption of TOTP secrets for storage
   (see `passlib.totp`).  
   Use ``pip install passlib[totp]`` to get the recommended TOTP setup.

## Installation Instructions

To install from PyPI using `pip`:

```shell
pip install passlib
```

As noted above, you can ensure you have feature-specific extras installed via any of:

```shell
pip install passlib[argon2]
pip install passlib[bcrypt]
pip install passlib[totp]
```
