# Passlib

![PyPI Version](https://img.shields.io/pypi/v/passlib?style=for-the-badge)
![PyPI Python Version](https://img.shields.io/pypi/pyversions/passlib?style=for-the-badge)


This is a fork of https://foss.heptapod.net/python-libs/passlib

Passlib is a password hashing library for Python 3, which provides
cross-platform implementations of over 30 password hashing algorithms, as well
as a framework for managing existing password hashes. It's designed to be useful
for a wide range of tasks, from verifying a hash found in /etc/shadow, to
providing full-strength password hashing for multi-user application.

- See the [documentation](https://notypecheck.github.io/passlib/)
  for details, installation instructions, and examples.
- See the [changelog](https://github.com/notypecheck/passlib/blob/main/CHANGELOG.md)
  for a description of what's new in Passlib.
- Visit [PyPI](https://pypi.org/project/passlib) for the latest stable release.



## Installation
```shell
pip install passlib
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
For more details and an extended set of examples, see the full documentation
