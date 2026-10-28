# `passlib.hash` - Password Hashing Schemes

The `passlib.hash` module contains all the password hash algorithms built into Passlib.

## Overview

The `passlib.hash` module contains all the password hash algorithms built into Passlib.
While each hash has its own options and output format,
they all inherit from the [`PasswordHash`](passlib.ifc.md) base interface.
The following pages describe each hash in detail,
including its format, underlying algorithm, and known security issues.

!!! danger
    **Many of the hash algorithms listed below are *NOT* secure.**

    Passlib supports a wide array of hash algorithms, primarily to
    support legacy data and systems.
    If you want to choose a secure algorithm for a new application,
    see the [Quickstart Guide](../guide/quickstart.md).

!!! tip
    [`hash-tutorial`](../guide/hash-tutorial.md) -- for general usage examples

## Unix Hashes

Aside from "archaic" schemes such as `des_crypt`,
most of the password hashes supported by modern Unix flavors
adhere to the [modular crypt format](../reference/modular-crypt-format.md),
allowing them to be easily distinguished when used within the same file.
Variants of this format's basic `${scheme}${salt}${digest}` structure have also been adopted for use
by other applications and password hash schemes.

### Active Unix Hashes

All the following schemes are actively in use by various Unix flavors to store user passwords.
They all follow the modular crypt format.

- [`passlib.hash.bcrypt`](passlib.hash.bcrypt.md)
- [`passlib.hash.sha256_crypt`](passlib.hash.sha256_crypt.md)
- [`passlib.hash.sha512_crypt`](passlib.hash.sha512_crypt.md)

Special note should be made of the following fallback helper,
which is not an actual hash scheme, but implements the "disabled account marker"
found in many Linux & BSD password files:

- [`passlib.hash.unix_disabled`](passlib.hash.unix_disabled.md)

### Deprecated Unix Hashes

The following schemes are supported by various Unix systems
using the modular crypt format, but are no longer considered secure,
and have been deprecated in favor of the [Active Unix Hashes](#active-unix-hashes) (above).

- `passlib.hash.bsd_nthash` - FreeBSD's MCF-compatible encoding of [`nthash`](passlib.hash.nthash.md) digests

- [`passlib.hash.md5_crypt`](passlib.hash.md5_crypt.md)
- [`passlib.hash.sha1_crypt`](passlib.hash.sha1_crypt.md)
- [`passlib.hash.sun_md5_crypt`](passlib.hash.sun_md5_crypt.md)

### Archaic Unix Hashes

The following schemes are supported by certain Unix systems,
but are considered particularly archaic: Not only do they predate
the modular crypt format, but they're based on the outmoded DES block cipher,
and are woefully insecure:

- [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md)
- [`passlib.hash.bsdi_crypt`](passlib.hash.bsdi_crypt.md)
- [`passlib.hash.bigcrypt`](passlib.hash.bigcrypt.md)
- [`passlib.hash.crypt16`](passlib.hash.crypt16.md)

## Other "Modular Crypt" Hashes

The [modular crypt format](../reference/modular-crypt-format.md) is a loose standard
for password hash strings which started life under the Unix operating system,
and is used by many of the Unix hashes (above).  However,
it's basic `${scheme}${hash}` format has also been adopted by a number
of application-specific hash algorithms:

### Active Hashes

While most of these schemes are generally application-specific, 
and are not natively supported by any Unix OS,
they can be used compatibly along side other modular crypt format hashes:

- [`passlib.hash.argon2`](passlib.hash.argon2.md)
- [`passlib.hash.bcrypt_sha256`](passlib.hash.bcrypt_sha256.md)
- [`passlib.hash.phpass`](passlib.hash.phpass.md)
- [`passlib.hash.pbkdf2_digest`](passlib.hash.pbkdf2_digest.md)
- [`passlib.hash.scram`](passlib.hash.scram.md)
- [`passlib.hash.scrypt`](passlib.hash.scrypt.md)

### Deprecated Hashes

The following are some additional application-specific hashes which are still
occasionally seen, use the modular crypt format, but are rarely used or weak
enough that they have been deprecated:

- [`passlib.hash.apr_md5_crypt`](passlib.hash.apr_md5_crypt.md)
- [`passlib.hash.cta_pbkdf2_sha1`](passlib.hash.cta_pbkdf2_sha1.md)
- [`passlib.hash.dlitz_pbkdf2_sha1`](passlib.hash.dlitz_pbkdf2_sha1.md)

## LDAP / RFC2307 Hashes

All of the following hashes use a variant of the password hash format
used by LDAPv2. Originally specified in `RFC 2307` and used by OpenLDAP [^openldap],
the basic format `{SCHEME}HASH` has seen widespread adoption in a number of programs.

### Standard LDAP Schemes

The following schemes are explicitly defined by RFC 2307,
and are supported by OpenLDAP.

- `passlib.hash.ldap_md5` - MD5 digest
- `passlib.hash.ldap_sha1` - SHA1 digest
- `passlib.hash.ldap_salted_md5` - salted MD5 digest
- `passlib.hash.ldap_salted_sha1` - salted SHA1 digest
- `passlib.hash.ldap_salted_sha256` - salted SHA256 digest
- `passlib.hash.ldap_salted_sha512` - salted SHA512 digest

- [`passlib.hash.ldap_crypt`](passlib.hash.ldap_crypt.md)

- `passlib.hash.ldap_plaintext` - LDAP-Aware Plaintext Handler

### Non-Standard LDAP Schemes

None of the following schemes are actually used by LDAP,
but follow the LDAP format:

- `passlib.hash.ldap_hex_md5` - Hex-encoded MD5 Digest
- `passlib.hash.ldap_hex_sha1` - Hex-encoded SHA1 Digest

- [`passlib.hash.ldap_pbkdf2_digest`](passlib.hash.ldap_pbkdf2_digest.md)
- [`passlib.hash.atlassian_pbkdf2_sha1`](passlib.hash.atlassian_pbkdf2_sha1.md)
- [`passlib.hash.fshp`](passlib.hash.fshp.md)

- `passlib.hash.roundup_plaintext` - Roundup-specific LDAP Plaintext Handler

## SQL Database Hashes

The following schemes are used by various SQL databases
to encode their own user accounts.
These schemes have encoding and contextual requirements
not seen outside those specific contexts:

- [`passlib.hash.mssql2000`](passlib.hash.mssql2000.md)
- [`passlib.hash.mssql2005`](passlib.hash.mssql2005.md)
- [`passlib.hash.mysql323`](passlib.hash.mysql323.md)
- [`passlib.hash.mysql41`](passlib.hash.mysql41.md)
- [`passlib.hash.postgres_md5`](passlib.hash.postgres_md5.md)
- [`passlib.hash.oracle10`](passlib.hash.oracle10.md)
- [`passlib.hash.oracle11`](passlib.hash.oracle11.md)

## MS Windows Hashes

The following hashes are used in various places by Microsoft Windows.
As they were designed for "internal" use, they generally contain
no identifying markers, identifying them is pretty much context-dependant.

- [`passlib.hash.lmhash`](passlib.hash.lmhash.md)
- [`passlib.hash.nthash`](passlib.hash.nthash.md)
- [`passlib.hash.msdcc`](passlib.hash.msdcc.md)
- [`passlib.hash.msdcc2`](passlib.hash.msdcc2.md)

## Cisco Hashes

**Cisco IOS**

The following hashes are used in various places on Cisco IOS, and
are usually referred to by a Cisco-assigned "type" code:

- [`passlib.hash.cisco_type7`](passlib.hash.cisco_type7.md)

- [`md5_crypt`](passlib.hash.md5_crypt.md) -- "Type 5" hashes are actually just the standard
  Unix MD5-Crypt hash, the format is identical.

- [`cisco_type7`](passlib.hash.cisco_type7.md) -- "Type 7" isn't actually a hash,
  but a reversible encoding designed to obscure passwords from idle view.

- "Type 8" hashes are based on PBKDF2-HMAC-SHA256;
  but not currently supported by passlib (`#87`).

- "Type 9" hashes are based on scrypt;
  but not currently supported by passlib (`#87`).

**Cisco PIX & ASA**

Separately from this, Cisco PIX & ASA firewalls have their own hash formats,
generally identified by the "format" parameter in the `username {user} password {hash} {format}` config line
they occur in.  The following are known & handled by passlib:

- [`passlib.hash.cisco_pix`](passlib.hash.cisco_pix.md)
- [`passlib.hash.cisco_asa`](passlib.hash.cisco_asa.md)

- [`cisco_pix`](passlib.hash.cisco_pix.md) -- PIX "encrypted" hashes
  use a simple unsalted MD5-based algorithm.

- [`cisco_asa`](passlib.hash.cisco_asa.md) -- ASA "encrypted" hashes
  use a similar algorithm to PIX, with some minor improvements.

- ASA "nt-encrypted" hashes
  are the same as `passlib.hash.nthash`,
  except that they use base64 encoding rather than hexadecimal.

- ASA 9.5 added support for "pbkdf2" hashes
  (based on PBKDF2-HMAC-SHA512); which aren't currently supported
  by passlib (`#87`).

## Other Hashes

The following schemes are used in various contexts,
but have formats or uses which cannot be easily placed
in one of the above categories:

- [`passlib.hash.django_std`](passlib.hash.django_std.md)
- [`passlib.hash.grub_pbkdf2_sha512`](passlib.hash.grub_pbkdf2_sha512.md)
- [`passlib.hash.hex_digests`](passlib.hash.hex_digests.md)
- [`passlib.hash.plaintext`](passlib.hash.plaintext.md)

[^openldap]: OpenLDAP homepage - <http://www.openldap.org/>.
