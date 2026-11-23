# Installation

## Supported Platforms

Passlib requires Python 3.11 or newer.

Passlib should work with all operating systems and environments, as it contains builtin fallbacks for almost all OS-dependent features.

!!! warning
    **Passlib `1.8` dropped support for Python < 3.9, Jython and PyPy.**
    Starting with `1.10`, [versions that have reached EOL](https://devguide.python.org/versions/) will no longer be supported.

!!! note
    The `1.9.4` release published on PyPI declares Python 3.9 as its minimum; Python 3.11 becomes the minimum in the release after it (`1.9.5`).

## Optional Libraries

- [`bcrypt`](https://pypi.org/project/bcrypt/)
   If installed, this will be used to handle `passlib.hash.bcrypt` and
   `passlib.hash.bcrypt_sha256` hashes.  
   Use `pip install passjlib[bcrypt]` to get the recommended bcrypt setup.

- [`argon2_cffi`](https://pypi.org/project/argon2-cffi/)
   If `argon2_cffi` is installed, it will be used to provide
   support for the `passlib.hash.argon2` hash algorithm.  
   Use ``pip install passjlib[argon2]`` to get the recommended argon2 setup.

- [`cryptography`](https://pypi.org/project/cryptography/)
   If installed, will be used to enable encryption of TOTP secrets for storage
   (see `passlib.totp`).  
   Use ``pip install passjlib[totp]`` to get the recommended TOTP setup.

## Installation Instructions

!!! note
    Versions 1.7.5 through 1.9.4 were published on PyPI as `libpass`; releases from 1.9.5 onward will be published under `passlib`. Upgrading `libpass` to `1.9.5` installs the official `passlib` as a direct dependency, so `pip install -U libpass` migrates existing installs to the official package.

    Whichever package you install, the import name is unchanged: `from passlib.context import CryptContext`.

To install from PyPI using `pip`:

```shell
pip install passlib
```

From 1.9.5 onward, install with `pip install passlib`.

As noted above, you can ensure you have feature-specific extras installed via any of:

```shell
pip install passlib[argon2]
pip install passlib[bcrypt]
pip install passlib[totp]
```
