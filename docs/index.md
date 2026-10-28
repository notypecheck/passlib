# Passlib

Passlib is a password hashing library for Python 3, which provides
cross-platform implementations of over 30 password hashing algorithms, as well
as a framework for managing existing password hashes. It's designed to be useful
for a wide range of tasks, from verifying a hash found in `/etc/shadow`, to
providing full-strength password hashing for a multi-user application.

## What is Passlib?

Passlib's contents can roughly be grouped into four categories: password hashes,
password contexts, two-factor authentication, and other utility functions. Its
contents are documented across the following sections:

- **Password Hashes** — every supported algorithm is implemented as a "hasher" class, importable from `passlib.hash`, all sharing a uniform interface described in the [Hash Tutorial](guide/hash-tutorial.md).
- **Password Contexts** — the `CryptContext` class (in `passlib.context`) manages multiple hash schemes at once, handling deprecation and migration of old hashes. See the [Context Tutorial](guide/context-tutorial.md).
- **Two-Factor Authentication** — helper functions in `passlib.totp` for configuring, persisting, and verifying TOTP tokens. See the [TOTP Tutorial](guide/totp-tutorial.md).
- **Application Helpers** — pre-configured contexts in `passlib.apps`, `passlib.hosts`, `passlib.apache`, and more.

!!! warning
    Some of the hashes in this library are marked as "insecure" and are provided for historical purposes only; others are specialized in ways that are not generally useful. If you are creating a new application and need to choose a password hash, read the [Quickstart](guide/quickstart.md) first — in particular the [Recommended hashes](guide/quickstart.md#recommended-hashes) section.

### Quick sample: hashing and verifying a password

The following code hashes and then verifies a password using the `pbkdf2_sha256` algorithm:

```python
# import the hash algorithm
from passlib.hash import pbkdf2_sha256

# generate new salt, and hash a password
h = pbkdf2_sha256.hash("toomanysecrets")
print(h)
# > '$pbkdf2-sha256$29000$N2YMIWQsBWBMae09x1jrPQ$1t8iyB2A.WF/Z5JZv.lfCIhXXN33N23OSgQYThBYRfk'

# verifying the password
print(pbkdf2_sha256.verify("toomanysecrets", h))
# > True
print(pbkdf2_sha256.verify("joshua", h))
# > False
```

## Getting Started

This documentation is organized into a narrative walkthrough of Passlib, and a top-down API reference.

- [Installation](guide/install.md) — system requirements & installation instructions.
- [Overview](guide/overview.md) — an introduction to what Passlib provides.
- [Quickstart](guide/quickstart.md) — get password hashing set up in a new application quickly, including choosing a hash.
- [Hash Tutorial](guide/hash-tutorial.md) — walkthrough of using a hasher class.
- [Context Tutorial](guide/context-tutorial.md) — walkthrough of the `CryptContext` class.
- [TOTP Tutorial](guide/totp-tutorial.md) — setting up two-factor authentication.

## API Reference

The top-down reference to the `passlib` package is available in the [API Reference](api/passlib.hash.md). Key modules include:

- [`passlib.hash`](api/passlib.hash.md) — list of all hashes in Passlib
- [`passlib.context`](api/passlib.context.md) — `CryptContext`, for managing multiple hash schemes
- [`passlib.ifc`](api/passlib.ifc.md) — the `PasswordHash` API reference
- [`passlib.totp`](api/passlib.totp.md) — two-factor authentication

## Changelog

See [changelog](changelog/index.md)

## Online Resources

- [Latest Docs](https://notypecheck.github.io/passlib/)
- [Public Repository](https://github.com/notypecheck/passlib)
- [PyPi](https://pypi.org/project/passlib/)
