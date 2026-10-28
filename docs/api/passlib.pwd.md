# `passlib.pwd` -- Password generation helpers

This module provides password generation helpers.

!!! warning
    Changed in 1.7: Added.

## Password Generation

!!! warning
    Before using these routines, make sure your system's RNG entropy pool is
    secure and full. Also make sure that `genword()` or `genphrase()`
    is called with a sufficiently high `entropy` parameter
    the intended purpose of the password.

::: passlib.pwd.genword

::: passlib.pwd.genphrase

## Predefined Symbol Sets

The following predefined sets are used by the generation functions above,
but are exported by this module for general use:

- `default_charsets` - Dictionary mapping charset name -> string of characters, used by `genword()`. See that function for a list of predefined charsets present in this dict.
- `default_wordsets` - Dictionary mapping wordset name -> tuple of words, used by `genphrase()`. See that function for a list of predefined wordsets present in this dict. (Note that this is actually a special object which will lazy-load wordsets from disk on-demand)

## Password Strength Estimation

Passlib does not currently offer any password strength estimation routines.
However, the (javascript-based) [zxcvbn](https://github.com/dropbox/zxcvbn)
project is a *very* good choice.

Though there are a few different python ports of ZXCVBN library, as of 2019-11-13,
[zxcvbn (@ pypi)](https://pypi.python.org/pypi/zxcvbn) is the most up-to-date,
and is endorsed by the upstream zxcvbn developers.
