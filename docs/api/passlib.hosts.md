# `passlib.hosts` - OS Password Handling

This module provides some preconfigured [`CryptContext`](passlib.context.md)
instances for hashing & verifying password hashes tied to user accounts of various operating systems.
While (most) of the objects are available cross-platform,
their use is oriented primarily towards Linux and BSD variants.

!!! tip
    For Microsoft Windows, see the list of [Windows Hashes](passlib.hash.md#ms-windows-hashes) in `passlib.hash`.

## Usage Example

The `CryptContext` class itself has a large number of features,
but to give an example of how to quickly use the instances in this module:

Each of the objects in this module can be imported directly:

```python
# as an example, this imports the linux_context object,
# which is configured to recognize most hashes found in Linux /etc/shadow files.
from passlib.hosts import linux_context
```

Hashing a password is simple (and salt generation is handled automatically):

```python
hash = linux_context.hash("toomanysecrets")
print(hash)
# > $5$rounds=84740$fYChCy.52EzebF51$9bnJrmTf2FESI93hgIBFF4qAfysQcKoB0veiI0ZeYU4
```

Verifying a password against an existing hash is just as quick:

```python
print(linux_context.verify("toomanysocks", hash))
# > False
print(linux_context.verify("toomanysecrets", hash))
# > True
```

You can also identify hashes:

```python
print(linux_context.identify(hash))
# > 'sha512_crypt'
```

Or encrypt using a specific algorithm:

```python
print(linux_context.schemes())
# > ('sha512_crypt', 'sha256_crypt', 'md5_crypt', 'des_crypt', 'unix_disabled')
hash = linux_context.hash("password", scheme="des_crypt")
print(hash)
# > '2fmLLcoHXuQdI'
print(linux_context.identify("2fmLLcoHXuQdI"))
# > 'des_crypt'
```

!!! tip
    See the [`CryptContext Tutorial`](../guide/context-tutorial.md) and [`CryptContext Reference`](passlib.context.md) for more information about the CryptContext class.

## Unix Password Hashes

Passlib provides a number of pre-configured `CryptContext` instances
which can identify and manipulate all the formats used by Linux and BSD.
See the [modular crypt identifier list](../reference/modular-crypt-format.md#mcf-identifiers) for a complete
list of which hashes are supported by which operating system.

### Predefined Contexts

Passlib provides `CryptContext` instances
for the following Unix variants:

- `linux_context` - context instance which recognizes hashes used by the majority of Linux distributions. encryption defaults to [`sha512_crypt`](passlib.hash.sha512_crypt.md).
- `freebsd_context` - context instance which recognizes all hashes used by FreeBSD 8. encryption defaults to [`bcrypt`](passlib.hash.bcrypt.md).
- `netbsd_context` - context instance which recognizes all hashes used by NetBSD. encryption defaults to [`bcrypt`](passlib.hash.bcrypt.md).
- `openbsd_context` - context instance which recognizes all hashes used by OpenBSD. encryption defaults to [`bcrypt`](passlib.hash.bcrypt.md).

!!! note
    All of the above contexts include the [`unix_disabled`](passlib.hash.unix_disabled.md) handler
    as a final fallback. This special handler treats all strings as invalid passwords,
    particularly the common strings `!` and `*` which are used to indicate
    that an account has been disabled [^shadow].

### Current Host OS

`host_context`

*Platform: Unix*

This [`CryptContext`](passlib.context.md) instance should detect and support
all the algorithms the native OS `crypt()` offers.
The main differences between this object and `crypt()`:

- this object provides introspection about *which* schemes are available on a given system (via `host_context.schemes()`).
- it defaults to the strongest algorithm available, automatically configured to an appropriate strength for hashing new passwords.
- whereas `crypt()` typically defaults to using [`des_crypt`](passlib.hash.des_crypt.md); and provides little introspection.

As an example, this can be used in conjunction with stdlib's `spwd` module
to verify user passwords on the local system:

```python
# NOTE/WARNING: this example requires running as root on most systems.
import spwd, os
from passlib.hosts import host_context

hash = spwd.getspnam(os.environ["USER"]).sp_pwd
print(host_context.verify("toomanysecrets", hash))
# > True
```

!!! warning
Changed in 1.4: This object is only available on systems where the stdlib `crypt` module is present. In version 1.3 and earlier, it was available on non-Unix systems, though it did nothing useful.

[^shadow]: Man page for Linux /etc/shadow - <http://linux.die.net/man/5/shadow>
