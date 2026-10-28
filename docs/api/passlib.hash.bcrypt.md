# passlib.hash.bcrypt - BCrypt

BCrypt was developed to replace `md5_crypt` for BSD systems.
It uses a modified version of the Blowfish stream cipher. Featuring
a large salt and variable number of rounds, it's currently the default
password hash for many systems (notably BSD), and has no known weaknesses.
It is one of the four hashes Passlib recommends for new applications. This class can be used directly as follows:

```python
from passlib.hash import bcrypt

# generate new salt, hash password
h = bcrypt.hash("password")
print(h)
# > '$2a$12$NT0I31Sa7ihGEWpka9ASYrEFkhuTNeBQ2xfZskIiiJeyFXhRgS.Sy'

# the same, but with an explicit number of rounds
print(bcrypt.using(rounds=13).hash("password"))
# > '$2b$13$HMQTprwhaUwmir.g.ZYoXuRJhtsbra4uj.qJPHrKsX5nGlhpts0jm'

# verify password
print(bcrypt.verify("password", h))
# > True
print(bcrypt.verify("wrong", h))
# > False
```

!!! note
    It is strongly recommended that you install [bcrypt](https://pypi.python.org/pypi/bcrypt) when using this hash.

!!! tip
    the generic `PasswordHash usage examples`.

## Interface

::: passlib.hash.bcrypt

### Bcrypt Backends

This class will use the first available of five possible backends:

1. [bcrypt](https://pypi.python.org/pypi/bcrypt), if installed.
4. stdlib's `crypt.crypt()`, if the host OS supports BCrypt
   (primarily BSD-derived systems).
5. A pure-python implementation of BCrypt, built into Passlib.

If no backends are available, `hash()` and `verify()`
will throw `MissingBackendError` when they are invoked.
You can check which backend is in use by calling `bcrypt.get_backend()`.

As of Passlib 1.6.3, a one-time check is peformed when the backend is first loaded,
to detect the backend's capabilities & bugs. If this check detects a fatal bug,
a `PasslibSecurityError