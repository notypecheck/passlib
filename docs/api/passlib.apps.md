# `passlib.apps` - Helpers for various applications

This module contains a number of preconfigured [`CryptContext`](passlib.context.md) instances that are provided by Passlib for easily handling the hash formats used by various applications.

## Usage Example

The `CryptContext` class itself has a large number of features,
but to give an example of how to quickly use the instances in this module:

Each of the objects in this module can be imported directly:

```python
# as an example, this imports the custom_app_context object,
# a helper to let new applications *quickly* add password hashing.
from passlib.apps import custom_app_context
```

Hashing a password is simple (and salt generation is handled automatically):

```python
hash = custom_app_context.hash("toomanysecrets")
print(hash)
# > $5$rounds=84740$fYChCy.52EzebF51$9bnJrmTf2FESI93hgIBFF4qAfysQcKoB0veiI0ZeYU4
```

Verifying a password against an existing hash is just as quick:

```python
print(custom_app_context.verify("toomanysocks", hash))
# > False
print(custom_app_context.verify("toomanysecrets", hash))
# > True
```

!!! tip
    See the [`CryptContext Tutorial`](../guide/context-tutorial.md) and [`CryptContext Reference`](passlib.context.md) for more information about the CryptContext class.

## Django

The following objects provide pre-configured `CryptContext` instances
for handling [Django](http://www.djangoproject.com) password hashes, as used by Django's `django.contrib.auth` module.
They recognize all the [builtin Django hashes](passlib.hash.django_std.md) supported by the particular Django version.

!!! note
    These objects may not match the hashes in your database if a third-party
    library has been used to patch Django to support alternate hash formats.
    This includes the [django-bcrypt](http://pypi.python.org/pypi/django-bcrypt)
    plugin, or Passlib's builtin [`passlib.ext.django`](passlib.ext.django.md).
    As well, Django 1.4 introduced a very configurable "hashers" framework,
    and individual deployments may support additional hashes and/or
    have other defaults.

`django10_context`

The object replicates the password hashing policy for Django 1.0-1.3.
It supports all the Django 1.0 hashes, and defaults to
[`django_salted_sha1`](passlib.hash.django_std.md).

!!! warning
    Added in 1.6.

`django14_context`

The object replicates the stock password hashing policy for Django 1.4.
It supports all the Django 1.0 & 1.4 hashes, and defaults to
[`django_pbkdf2_sha256`](passlib.hash.django_std.md). It treats all
Django 1.0 hashes as deprecated.

!!! warning
    Added in 1.6.

`django16_context`

The object replicates the stock password hashing policy for Django 1.6.
It supports all the Django 1.0-1.6 hashes, and defaults to
[`django_pbkdf2_sha256`](passlib.hash.django_std.md). It treats all
Django 1.0 hashes as deprecated.

!!! warning
    Added in 1.6.2.

`django_context`

This alias will always point to the latest preconfigured Django
context supported by Passlib, and as such should support
all historical hashes built into Django.

!!! warning
    Changed in 1.6.2: This now points to `django16_context`.

## LDAP

Passlib provides two contexts related to ldap hashes:

`ldap_context`

This object provides a pre-configured `CryptContext` instance
for handling LDAPv2 password hashes. It recognizes all
the [standard ldap hashes](passlib.hash.ldap_std.md).

It defaults to using the `{SSHA}` password hash.
For times when there should be another default, using code such as the following:

```python
from passlib.apps import ldap_context

ldap_context = ldap_context.replace(default="ldap_salted_md5")

# the new context object will now default to {SMD5}:
print(ldap_context.hash("password"))
# > '{SMD5}T9f89F591P3fFh1jz/YtW4aWD5s='
```

`ldap_nocrypt_context`

This object recognizes all the standard ldap schemes that `ldap_context`
does, *except* for the `{CRYPT}`-based schemes.

## MySQL

This module provides two pre-configured `CryptContext` instances
for handling MySQL user passwords:

`mysql_context`

This object should recognize the new [`mysql41`](passlib.hash.mysql41.md) hashes,
as well as any legacy [`mysql323`](passlib.hash.mysql323.md) hashes.

It defaults to mysql41 when generating new hashes.

This should be used with MySQL version 4.1 and newer.

`mysql3_context`

This object is for use with older MySQL deploys which only recognize
the [`mysql323`](passlib.hash.mysql323.md) hash.

This should be used only with MySQL version 3.2.3 - 4.0.

## PHPass

[PHPass](http://www.openwall.com/phpass/) is a PHP password hashing library,
and hashes derived from it are found in a number of PHP applications.
It is found in a wide range of PHP applications, including Drupal and Wordpress.

`phpass_context`

This object follows the standard PHPass logic:
it supports [`bcrypt`](passlib.hash.bcrypt.md), [`bsdi_crypt`](passlib.hash.bsdi_crypt.md),
and implements a custom scheme called the "phpass portable hash" [`phpass`](passlib.hash.phpass.md) as a fallback.

BCrypt is used as the default if support is available,
otherwise the Portable Hash will be used as the default.

!!! warning
    Changed in 1.5: Now uses Portable Hash as fallback if BCrypt isn't available. Previously used BSDI-Crypt as fallback (per original PHPass implementation), but it was decided PHPass is in fact more secure.

`phpbb3_context`

This object supports phpbb3 password hashes, which use a variant of [`phpass`](passlib.hash.phpass.md).

## PostgreSQL

`postgres_context`

This object should recognize password hashes stored in PostgreSQL's `pg_shadow` table,
which are all assumed to follow the [`postgres_md5`](passlib.hash.postgres_md5.md) format.

Note that the username must be provided whenever hashing or verifying a postgres hash:

```python
from passlib.apps import postgres_context

# hashing a password...
hashed = postgres_context.hash("somepass", user="dbadmin")
print(hashed)
# > 'md578ed0f0ab2be0386645c1b74282917e7'

# verifying a password...
print(postgres_context.verify("somepass", hashed, user="dbadmin"))
# > True
print(postgres_context.verify("wrongpass", hashed, user="dbadmin"))
# > False

# forgetting the user will result in an error:
try:
    postgres_context.hash("somepass")
except TypeError as err:
    print(err)
# > user must be unicode or bytes, not None
```

## Roundup

The [Roundup Issue Tracker](http://www.roundup-tracker.org) has long
supported a series of different methods for encoding passwords.
The following contexts are available for reading Roundup password hash fields:

`roundup10_context`

This object should recognize all password hashes used by Roundup 1.4.16 and earlier:
[`ldap_hex_sha1`](passlib.hash.ldap_other.md) (the default),
[`ldap_hex_md5`](passlib.hash.ldap_other.md), [`ldap_des_crypt`](passlib.hash.ldap_crypt.md),
and [`roundup_plaintext`](passlib.hash.plaintext.md).

`roundup15_context`

Roundup 1.4.17 adds support for [`ldap_pbkdf2_sha1`](passlib.hash.ldap_pbkdf2_digest.md)
as its preferred hash format.
This context supports all the `roundup10_context` hashes,
but adds that hash as well (and uses it as the default).

`roundup_context`

This is an alias for the latest version-specific roundup context supported
by passlib, currently the `roundup15_context`.

## Custom Applications

`custom_app_context`

This `CryptContext` object is provided for new python applications
to quickly and easily add password hashing support.
It comes preconfigured with:

- Support for [`sha256_crypt`](passlib.hash.sha256_crypt.md) and [`sha512_crypt`](passlib.hash.sha512_crypt.md)
- Defaults to SHA256-Crypt under 32 bit systems, SHA512-Crypt under 64 bit systems.
- Large number of `rounds`, for increased time-cost to hedge against attacks.

For applications which want to quickly add a password hash,
all they need to do is import and use this object, per the
[usage example](#usage-example) at the top of this page.

!!! tip
    See the [`quickstart`](../guide/quickstart.md) for additional details.
