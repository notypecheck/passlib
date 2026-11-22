# Passlib

![PyPI Version](https://img.shields.io/pypi/v/passlib?style=for-the-badge)
![PyPI Python Version](https://img.shields.io/pypi/pyversions/passlib?style=for-the-badge)


This is the official repository of Passlib, published on PyPI as
[passlib](https://pypi.org/project/passlib/). It continues the original
project at https://foss.heptapod.net/python-libs/passlib (unmaintained since
its final release, 1.7.4, in 2020).

Passlib is a password hashing library for Python 3, which provides
cross-platform implementations of over 30 password hashing algorithms, as well
as a framework for managing existing password hashes. It's designed to be useful
for a wide range of tasks, from verifying a hash found in /etc/shadow, to
providing full-strength password hashing for multi-user application.

Versions 1.7.5 through 1.9.4 were published on PyPI as
[libpass](https://pypi.org/project/libpass/); releases from 1.9.5 onward
are published under `passlib` again.

- See the [documentation](https://notypecheck.github.io/passlib/)
  for details, installation instructions, and examples.
- See the [changelog](https://github.com/notypecheck/passlib/blob/main/CHANGELOG.md)
  for a description of what's new in Passlib.
- Visit [PyPI](https://pypi.org/project/passlib/) for the latest stable release.

## Installation
```shell
pip install passlib
```

Available extras:
```shell
pip install passlib[argon2]
pip install passlib[bcrypt]
pip install passlib[totp]
```

## Usage
A quick example of using passlib to integrate into a new application:
```python
from passlib.context import CryptContext

context = CryptContext(schemes=["sha512_crypt"])

hash = context.hash("password")
# $6$rounds=656000$jFKvvPmUywlqjSs.$iNeK/OWVry7KThNyzR01xzqZzgk/VA75.sR4yXXblsPAoEugtdO3zn/O4VEG3Izp8l5.//lMGpuRCOqvKknHo1

# Verifying a password
is_valid = context.verify("password", hash)
# > True
```
For more details and an extended set of examples, see the [full documentation](https://notypecheck.github.io/passlib/)
