# `passlib.context` - CryptContext Hash Manager

This page provides a complete reference of all the methods and options supported by the [`CryptContext`](#the-cryptcontext-class) class and helper utilities. The module provides the `CryptContext` class, for managing multiple password hash schemes.

!!! tip
    [`context-tutorial`](../guide/context-tutorial.md) -- overview of this class and walkthrough of how to use it.

## The CryptContext Class

Helper for hashing passwords using different algorithms.

At its base, this is a proxy object that makes it easy to use multiple [PasswordHash](passlib.ifc.md) objects at the same time.
Instances of this class can be created by calling the constructor
with the appropriate keywords, or by using one of the alternate
constructors, which can load directly from a string or a local file.
Since this class has so many options and methods, they have been broken
out into subsections:

- [Constructor Keywords](#constructor-keywords) -- all the keywords this class accepts.
    - [Context Options](#context-options) -- options affecting the Context itself.
    - [Algorithm Options](#algorithm-options) -- options controlling the wrapped hashes.
- [Primary Methods](#primary-methods) -- the primary methods most applications need.
- [Hash Migration](#hash-migration) -- methods for automatically replacing deprecated hashes.
- [Alternate Constructors](#alternate-constructors) -- creating instances from strings or files.
- [Changing the Configuration](#changing-the-configuration) -- altering the configuration of an existing context.
- [Examining the Configuration](#examining-the-configuration) -- programmatically examining the context's settings.
- [Saving the Configuration](#saving-the-configuration) -- exporting the context's current configuration.
- [Configuration Errors](#configuration-errors) -- overview of errors that may be thrown by `CryptContext` constructor

::: passlib.context.CryptContext

## Constructor Keywords

The `CryptContext` class accepts the following keywords, all of which are optional. The keywords are divided into two categories: [context options](#context-options), which affect the CryptContext itself; and [algorithm options](#algorithm-options), which place defaults and limits on the algorithms used by the CryptContext.

### Context Options

Options which directly affect the behavior of the CryptContext instance:

#### **schemes**
List of algorithms which the instance should support.

The most important option in the constructor, it controls what hashes can be used by the `hash()` method,
which will be recognized by `verify()` and `identify()`, and other effects throughout the instance. It should be a sequence of names, drawn from the hashes in `passlib.hash`. Listing an unknown name will cause a `ValueError`. You can use the `schemes()` method to get a list of the currently configured algorithms. As an example, the following creates a CryptContext instance which supports the [sha256_crypt](passlib.hash.sha256_crypt.md) and [des_crypt](passlib.hash.des_crypt.md) schemes:

```python
from passlib.context import CryptContext

myctx = CryptContext(schemes=["sha256_crypt", "des_crypt"])
print(myctx.schemes())
# > ("sha256_crypt", "des_crypt")
```

!!! note
    The order of the schemes is sometimes important, as `identify()` will run through the schemes from first to last until an algorithm "claims" the hash. So plaintext algorithms and the like should be listed at the end.

!!! tip
    See the `context-basic-example` example in the tutorial.

#### **default**
Specifies the name of the default scheme.

This option controls which of the configured schemes will be used as the default when creating new hashes. This parameter is optional; if omitted, the first non-deprecated algorithm in ``schemes`` will be used. You can use the `default_scheme()` method to retrieve the name of the current default scheme. As an example, the following demonstrates the effect of this parameter on the `hash()` method:

```python
from passlib.context import CryptContext

myctx = CryptContext(schemes=["sha256_crypt", "md5_crypt"])

# hash() uses the first scheme
print(myctx.default_scheme())
# > 'sha256_crypt'
hashed = myctx.hash("password")
print(hashed)
# > '$5$rounds=80000$R5ZIZRTNPgbdcWq5$fT/Oeqq/apMa/0fbx8YheYWS6Z3XLTxCzEtutsk2cJ1'

# but setting default causes the second scheme to be used.
myctx.update(default="md5_crypt")
print(myctx.default_scheme())
# > 'md5_crypt'
hashed = myctx.hash("password")
print(hashed)
# > '$1$Rr0C.KI8$Kvciy8pqfL9BQ2CJzEzfZ/'
```

!!! tip
    See the `context-basic-example` example in the tutorial.

#### **deprecated**
List of algorithms which should be considered "deprecated".

This has the same format as ``schemes``, and should be a subset of those algorithms. The main purpose of this method is to flag schemes which need to be rehashed when the user next logs in. This has no effect on the [Primary Methods](#primary-methods); but if the special [Hash Migration](#hash-migration) methods are passed a hash belonging to a deprecated scheme, they will flag it as needed to be rehashed using the ``default`` scheme.

This may also contain a single special value, `["auto"]`, which will configure the CryptContext instance to deprecate *all* supported schemes except for the default scheme.

!!! tip
    See the `context-migration-example` in the tutorial

#### **truncate_error**

By default, some algorithms will truncate large passwords (e.g. [bcrypt](passlib.hash.bcrypt.md) truncates ones larger than 72 bytes). Such hashes accept a ``truncate_error=True`` option to make them raise a `PasswordTruncateError` instead.

This can also be set at the CryptContext level, and will passed to all hashes that support it.

### Algorithm Options

All of the other options that can be passed to a `CryptContext` constructor affect individual hash algorithms.
All of the following keys have the form `{scheme}__{key}`, where `{scheme}` is the name of one of the algorithms listed in ``schemes``, and `{option}` one of the parameters below:

#### **{scheme}__rounds**

Set the number of rounds required for this scheme when generating new hashes (using `hash()`). Existing hashes which have a different number of rounds will be marked as deprecated.

This essentially sets ``default_rounds``, ``min_rounds``, and ``max_rounds`` all at once. If any of those options are also specified, they will override the value specified by ``rounds``.

#### **{scheme}__default_rounds**

Sets the default number of rounds to use with this scheme when generating new hashes (using `hash()`).

If not set, this will fall back to the an algorithm-specific [PasswordHash.default_rounds](passlib.ifc.md). For hashes which do not support a rounds parameter, this option is ignored. As an example:

```python
from passlib.context import CryptContext

# no explicit default_rounds set, so hash() uses sha256_crypt's default (80000)
context = CryptContext(["sha256_crypt"])
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=80000$60Y7mpmAhUv6RDvj$AdseAOq6bKUZRDRTr/2QK1t38qm3P6sYeXhXKnBAmg0'
#            ^^^^^

# but if a default is specified, it will be used instead.
context = CryptContext(["sha256_crypt"], sha256_crypt__default_rounds=77123)
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=77123$60Y7mpmAhUv6RDvj$AdseAOq6bKUZRDRTr/2QK1t38qm3P6sYeXhXKnBAmg0'
#            ^^^^^
```

!!! tip
    See the `context-default-settings-example` example in the tutorial.

#### **{scheme}__vary_rounds**

!!! warning
    Changed in 1.7: This option has been deprecated as of Passlib 1.7, and will be removed in Passlib 2.0. The (very minimal) security benefit it provides was judged to not be worth code complexity it requires.

Instead of using a fixed rounds value (such as specified by ``default_rounds``, above). This option will cause each call to `hash()` to vary the default rounds value by some amount.

This can be an integer value, in which case each call will use a rounds value within the range ``default_rounds +/- vary_rounds``. It may also be a floating point value within the range 0.0 .. 1.0, in which case the range will be calculated as a proportion of the current default rounds (``default_rounds +/- default_rounds*vary_rounds``). A typical setting is ``0.1`` to ``0.2``.

As an example of how this parameter operates:

```python
# without vary_rounds set, hash() uses the same amount each time:
from passlib.context import CryptContext

context = CryptContext(schemes=["sha256_crypt"], sha256_crypt__default_rounds=80000)
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=80000$60Y7mpmAhUv6RDvj$AdseAOq6bKUZRDRTr/2QK1t38qm3P6sYeXhXKnBAmg0'
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=80000$60Y7mpmAhUv6RDvj$AdseAOq6bKUZRDRTr/2QK1t38qm3P6sYeXhXKnBAmg0'
#            ^^^^^

# but if vary_rounds is set, each one will be randomized
# (in this case, within the range 72000 - 88000)
context = CryptContext(
    schemes=["sha256_crypt"],
    sha256_crypt__default_rounds=80000,
    sha256_crypt__vary_rounds=0.1,
)
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=83966$bMpgQxN2hXo2kVr4$jL4Q3ov41UPgSbO7jYL0PdtsOg5koo4mCa.UEF3zan.'
hashed = context.hash("fooey")
print(hashed)
# > '$5$rounds=72109$43BBHC/hYPHzL69c$VYvVIdKn3Zdnvu0oJHVlo6rr0WjiMTGmlrZrrH.GxnA'
#           ^^^^^
```

!!! note
    This is not a *needed* security measure, but it lets some of the less-significant digits of the rounds value act as extra salt bits; and helps foil any attacks targeted at a specific number of rounds of a hash.

#### **{scheme}__min_rounds**, **{scheme}__max_rounds**

These options place a limit on the number of rounds allowed for a particular scheme.

For one, they limit what values are allowed for ``default_rounds``, and clip the effective range of the ``vary_rounds`` parameter. More importantly though, they proscribe a minimum strength for the hash, and any hashes which don't have sufficient rounds will be flagged as needing rehashing by the [Hash Migration](#hash-migration) methods.

!!! note
    These are configurable per-context limits. A warning will be issued if they exceed any hard limits set by the algorithm itself.

!!! tip
    See the `context-min-rounds-example` example in the tutorial.

#### **{scheme}__{other-option}**

Finally, any other options are assumed to correspond to one of that algorithm's `hash()` [settings](passlib.ifc.md), such as setting a ``salt_size``.

!!! tip
    See the `context-default-settings-example` example in the tutorial.

### Global Algorithm Options

#### **all__{option}**

The special scheme ``all`` permits you to set an option, and have it act as a global default for all the algorithms in the context. For instance, ``all__vary_rounds=0.1`` would set the ``vary_rounds`` option for all the schemes where it was not overridden with an explicit `{scheme}__vary_rounds` option.

!!! warning
    Changed in 1.7: This special scheme is deprecated as of Passlib 1.7, and will be removed in Passlib 2.0. It's only legitimate use was for ``vary_rounds``, which is also being removed in Passlib 2.0.

### User Categories

#### **{category}__context__{option}, {category}__{scheme}__{option}**

Passing keys with this format to the `CryptContext` constructor allows you to specify conditional context and algorithm 
options, controlled by the ``category`` parameter supported by most CryptContext methods.

These options are conditional because they only take effect if the `{category}` prefix of the option matches the value 
of the ``category`` parameter of the CryptContext method being invoked. In that case, they override any options specified
without a category prefix (e.g. `admin__sha256_crypt__min_rounds` would override `sha256_crypt__min_rounds`). 
The category prefix and the value passed into the ``category`` parameter can be any string the application wishes to use,
the only constraint is that ``None`` indicates the default category.

*Motivation:*
Policy limits such as default rounds values and deprecated schemes generally have to be set globally. However, it's frequently desirable to specify stronger options for certain accounts (such as admin accounts), choosing to sacrifice longer hashing time for a more secure password. The user categories system allows for this. For example, a CryptContext could be set up as follows:

```python
# A context object can be set up as follows:
from passlib.context import CryptContext

context = CryptContext(
    schemes=["sha256_crypt"],
    sha256_crypt__default_rounds=77000,
    staff__sha256_crypt__default_rounds=88000,
)

# In this case, calling hash() with ``category=None`` would result
# in a hash that used 77000 sha256-crypt rounds:
hashed = context.hash("password", category=None)
print(hashed)
# > '$5$rounds=77000$sj3XI0AbKlEydAKt$BhFvyh4.IoxaUeNlW6rvQ.O0w8BtgLQMYorkCOMzf84'
#            ^^^^^

# But if the application passed in ``category="staff"`` when an administrative
# account set their password, 88000 rounds would be used:
hashed = context.hash("password", category="staff")
print(hashed)
# > '$5$rounds=88000$w7XIdKfTI9.YLwmA$MIzGvs6NU1QOQuuDHhICLmDsdW/t94Bbdfxdh/6NJl7'
#            ^^^^^
```

## Primary Methods

The main interface to the CryptContext object deliberately mirrors the [PasswordHash](passlib.ifc.md) interface, since its central purpose is to act as a container for multiple password hashes. Most applications will only need to make use of a handful of methods in a CryptContext instance: `hash()`, `encrypt()`, `verify()`, `identify()`, and `dummy_verify()`.

These are all covered by the [CryptContext](#the-cryptcontext-class) reference above.

### "crypt"-style methods

Additionally, the main interface offers wrappers for the two Unix "crypt" style methods provided by all the [PasswordHash](passlib.ifc.md) objects: `genhash()` and `genconfig()`.

## Hash Migration

Applications which want to detect and regenerate deprecated hashes will want to use one of the following methods: `verify_and_update()`, `needs_update()`, and `hash_needs_update()`.

## Disabled Hash Management

!!! warning
    Changed in 1.7: Added.

It's frequently useful to disable a user's ability to login by replacing their password hash with a standin that's guaranteed to never verify, against *any* password. CryptContext offers some convenience methods for this through the following API: `disable()`, `enable()`, and `is_enabled()`.

## Alternate Constructors

In addition to the main class constructor, which accepts a configuration as a set of keywords, there are the following alternate constructors: `from_string()`, `from_path()`, and `copy()`.

## Changing the Configuration

`CryptContext` objects can have their configuration replaced or updated on the fly, and from a variety of sources (keywords, strings, files). This is done through three methods: `update(**kwds)`, `load()`, and `load_path()`.

## Examining the Configuration

The CryptContext object also supports basic inspection of its current configuration: `schemes()`, `default_scheme()`, `handler()`, and `context_kwds`.

## Saving the Configuration

More detailed inspection can be done by exporting the configuration using one of the serialization methods: `to_dict()` and `to_string()`.

## Configuration Errors

The following errors may be raised when creating a `CryptContext` instance via any of its constructors, or when updating the configuration of an existing instance:

**`ValueError`:**

- If a configuration option contains an invalid value (e.g. ``all__vary_rounds=-1``).
- If the configuration contains valid but incompatible options (e.g. listing a scheme as both [default](#context-options) and [deprecated](#context-options)).

**`KeyError`:**

- If the configuration contains an unknown or forbidden option (e.g. `{scheme}__salt`).
- If the `schemes`, `default`, or `deprecated` options reference an unknown hash scheme (e.g. ``schemes=['xxx']``)

**`TypeError`:**

- If a configuration value has the wrong type (e.g. ``schemes=123``).

Note that this error shouldn't occur when loading configurations from a file/string (e.g. using `from_string()`).

Additionally, a `PasslibConfigWarning` may be issued if any invalid-but-correctable values are encountered (e.g. if `sha256_crypt__min_rounds` is set to less than [sha256_crypt](passlib.hash.sha256_crypt.md)'s minimum of 1000).

!!! warning
    Changed in 1.6: Previous releases used Python's builtin `UserWarning` instead of the more specific `PasslibConfigWarning`.

## Other Helpers

::: passlib.context.LazyCryptContext