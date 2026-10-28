# `passlib.utils` - Helper Functions

Internal helpers for implementing password hashes.

!!! warning
    This module is primarily used as an internal support module. Its interface has not been finalized yet, and may be changed somewhat between major releases of Passlib, as the internal code is cleaned up and simplified.

This module primarily contains utility functions used internally by Passlib.
However, end-user applications may find some of the functions useful, in particular:

- `consteq()`
- `saslprep()`
- `generate_password()`

## Constants

### `unix_crypt_schemes`

List of the names of all the hashes in [`passlib.hash`](passlib.hash.md)
which are natively supported by `crypt()` on at least one operating system.

For all hashes in this list, the expression
`passlib.hash.{alg}.has_backend("os_crypt")`
will return ``True`` if the host OS natively supports the hash.
This list is used by [`passlib.hosts.host_context`](passlib.hosts.md)
and [`passlib.apps.ldap_context`](passlib.apps.md) to determine
which hashes are supported by the host.

!!! tip
    See the MCF identifiers table for which OSes are known to support which hashes.

## Unicode Helpers

### `consteq(left, right)`

Check two strings/bytes for equality.

This is functionally equivalent to ``left == right``,
but attempts to take constant time relative to the size of the righthand input.

The purpose of this function is to help prevent timing attacks
during digest comparisons: the standard ``==`` operator aborts
after the first mismatched character, causing its runtime to be
proportional to the longest prefix shared by the two inputs.
If an attacker is able to predict and control one of the two
inputs, repeated queries can be leveraged to reveal information about
the content of the second argument. To minimize this risk, `consteq()`
is designed to take ``THETA(len(right))`` time, regardless
of the contents of the two strings.
It is recommended that the attacker-controlled input
be passed in as the left-hand value.

!!! warning
    This function is *not* perfect. Various VM-dependant issues (e.g. the VM's integer object instantiation algorithm, internal unicode representation, etc), may still cause the function's run time to be affected by the inputs, though in a less predictable manner. *To minimize such risks, this function should not be passed* `unicode` *inputs that might contain non-* ``ASCII`` *characters*.

!!! note
    Added in 1.6. Changed in 1.7: This is an alias for stdlib's `hmac.compare_digest` under Python 3.3 and up.

::: passlib.utils.consteq

::: passlib.utils.saslprep

## Bytes Helpers

::: passlib.utils.xor_bytes

::: passlib.utils.render_bytes

::: passlib.utils.int_to_bytes

::: passlib.utils.bytes_to_int

## Encoding Helpers

::: passlib.utils.is_same_codec

::: passlib.utils.is_ascii_codec

::: passlib.utils.is_ascii_safe

::: passlib.utils.to_bytes

::: passlib.utils.to_unicode

::: passlib.utils.to_native_str

## Randomness

### `rng`

The random number generator used by Passlib to generate salt strings and other things which don't require a cryptographically strong source of randomness.

If `os.urandom()` support is available, this will be an instance of `random.SystemRandom`, otherwise it will use the default python PRNG class, seeded from various sources at startup.

::: passlib.utils.rng

::: passlib.utils.getrandbytes

::: passlib.utils.getrandstr

::: passlib.utils.generate_password

## Interface Tests

::: passlib.utils.is_crypt_handler

::: passlib.utils.is_crypt_context

::: passlib.utils.has_rounds_info

::: passlib.utils.has_salt_info

## Submodules

There are also a few submodules which provide additional utility functions:

- [`passlib.utils.handlers`](passlib.utils.handlers.md)
- [`passlib.utils.binary`](passlib.utils.binary.md)
- [`passlib.utils.des`](passlib.utils.des.md)
- [`passlib.utils.pbkdf2`](passlib.utils.pbkdf2.md)
