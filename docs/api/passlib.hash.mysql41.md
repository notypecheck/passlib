# `passlib.hash.mysql41` - MySQL 4.1 password hash

!!! danger
    **This algorithm is not considered secure by modern standards.** It should only be used when verifying existing hashes, or when interacting with applications that require this format. For new code, see the list of [recommended hashes](../guide/quickstart.md#recommended-hashes).

This class implements the second of MySQL's password hash functions,
used to store its user account passwords. Introduced in MySQL 4.1.1
under the function `PASSWORD()`, it replaced the previous
algorithm ([`mysql323`](passlib.hash.mysql323.md)) as the default
used by MySQL, and is still in active use under MySQL 5.
Users will most likely find the frontends provided by [`passlib.apps`](passlib.apps.md)
to be more useful than accessing this class directly.

!!! tip
    - See the `PasswordHash` usage examples for how to use this class via the common hash interface.
    - [`passlib.apps`](passlib.apps.md) for a list of premade `mysql contexts`.

## Interface

::: passlib.hash.mysql41

## Format & Algorithm

A mysql-41 password hash consists of an asterisk ``*`` followed
by 40 hexadecimal digits, directly encoding the 160 bit checksum.
An example hash (of `password`) is `*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19`.
MySQL always uses upper-case letters,
and so does Passlib (though Passlib will recognize lower-case letters as well).

The checksum is calculated simply, as the SHA1 hash of the SHA1 hash of the password,
which is then encoded into hexadecimal.

## Security Issues

Lacking any sort of salt, and using only 2 rounds
of the common SHA1 message digest, it's not very secure,
and should not be used for *any*
purpose but verifying existing MySQL 4.1+ password hashes.
