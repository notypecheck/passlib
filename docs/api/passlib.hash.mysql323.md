# `passlib.hash.mysql323` - MySQL 3.2.3 password hash

!!! danger
    **This algorithm is not considered secure by modern standards.** It should only be used when verifying existing hashes, or when interacting with applications that require this format. For new code, see the list of [recommended hashes](../guide/quickstart.md#recommended-hashes).

This class implements the first of MySQL's password hash functions,
used to store its user account passwords. Introduced in MySQL 3.2.3
under the function `PASSWORD()`, this function was renamed
to `OLD_PASSWORD()` under MySQL 4.1, when a newer password
hash algorithm was introduced (see [`mysql41`](passlib.hash.mysql41.md)).
Users will most likely find the frontends provided by [`passlib.apps`](passlib.apps.md)
to be more useful than accessing this class directly.
That aside, this class can be used as follows:

```python
from passlib.hash import mysql323

# hash password
hashed = mysql323.hash("password")
print(hashed)
# > '5d2e19393cc5ef67'

# verify correct password
print(mysql323.verify("password", "5d2e19393cc5ef67"))
# > True
print(mysql323.verify("secret", "5d2e19393cc5ef67"))
# > False
```

!!! tip
    - See the `PasswordHash` usage examples for more usage details.
    - [`passlib.apps`](passlib.apps.md) -- for a list of predefined `mysql contexts`.

## Interface

::: passlib.hash.mysql323

## Format & Algorithm

A mysql-323 password hash consists of 16 hexadecimal digits,
directly encoding the 64 bit checksum. MySQL always uses
lower-case letters, and so does Passlib
(though Passlib will recognize upper case letters as well).

The algorithm used is extremely simplistic, for details,
see the source implementation in the footnotes [^f1].

## Security Issues

Lacking any sort of salt, ignoring all whitespace,
and having a simplistic algorithm that amounts to little more than a checksum,
this is not secure, and should not be used for *any* purpose
but verifying existing MySQL 3.2.3 - 4.0 password hashes. [^f2]

[^f1]: Source of implementation used by Passlib - <http://djangosnippets.org/snippets/1508/>

[^f2]: Mysql document describing transition - <http://dev.mysql.com/doc/refman/4.1/en/password-hashing.html>
