# `passlib.utils.pbkdf2` - PBKDF2 key derivation algorithm [deprecated]

PBKDF2 and related key derivation algorithms.

!!! warning
    This module has been deprecated as of Passlib 1.7, and will be removed in Passlib 2.0. The functions in this module have been replaced by equivalent (but not identical) functions in the [`passlib.crypto`](passlib.crypto.md) module.

This module provides a couple of key derivation functions, as well as supporting utilities.
Primarily, it offers `pbkdf2()`, which provides the ability to generate an arbitrary length key using the PBKDF2 key derivation algorithm, as specified in [rfc 2898](http://tools.ietf.org/html/rfc2898).
This function can be helpful in creating password hashes using schemes which have been based around the pbkdf2 algorithm.

## PKCS#5 Key Derivation Functions

::: passlib.utils.pbkdf2.pbkdf1

::: passlib.utils.pbkdf2.pbkdf2

!!! note
    The details of PBKDF1 and PBKDF2 are specified in [RFC 2898](https://tools.ietf.org/html/rfc2898).

## Helper Functions

::: passlib.utils.pbkdf2.get_prf
