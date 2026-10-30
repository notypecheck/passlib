# `passlib.ifc` -- Password Hash Interface

This module provides the abstract interfaces used by Passlib.

## PasswordHash API

This module provides the `PasswordHash` abstract base class. This class defines the common methods and attributes present on all the hashes importable from the `passlib.hash` module. Additionally, the [`CryptContext`](passlib.context.md) class is deliberately designed to parallel many of this interface's methods.

!!! tip
    [`hash-tutorial`](../guide/hash-tutorial.md) -- Overview of this interface and how to use it.

## Base Abstract Class

This class provides an abstract interface for an arbitrary password hasher.

Applications will generally not construct instances directly -- most of the operations are performed via classmethods, allowing instances of a given class to be an internal detail used to implement the various operations.

While `PasswordHash` offers a number of methods and attributes, most applications will only need the two primary methods:

- `hash()` - generate new salt, return hash of password.
- `verify()` - verify password against existing hash.

Two additional support methods are also provided:

- `using()` - create subclass with customized configuration.
- `identify()` - check if hash belongs to this algorithm.

Each hash algorithm also provides a number of [informational attributes](#general-informational-attributes), allowing programmatic inspection of its options and parameter limits.

!!! tip
    [`hash-tutorial`](../guide/hash-tutorial.md) -- Overview of this interface and how to use it.

::: passlib.ifc.PasswordHash

## Hashing & Verification Methods

Most applications will only need to use two methods: `hash()` to generate new hashes, and `verify()` to check passwords against existing hashes. These methods provide an easy interface for working with a password hash, and abstract away details such as salt generation, hash normalization, and hash comparison.

#### **PasswordHash.hash(secret, \*\*kwds)** (classmethod)

Digest password using format-specific algorithm, returning resulting hash string.

For most hashes supported by Passlib, the returned string will contain: an algorithm identifier, a cost parameter, the salt string, and finally the password digest itself.

- *secret* (`unicode or bytes`) — string containing the password to encode.
- **kwds** — All additional keywords are algorithm-specific, and will be listed in that hash's documentation; though many of the more common keywords are listed under [PasswordHash.setting_kwds](#general-informational-attributes) and [PasswordHash.context_kwds](#general-informational-attributes).

!!! warning
    Changed in 1.7: Passing `setting_kwds` such as ``rounds`` and ``salt_size`` directly into the `hash` method is deprecated. Callers should instead use ``handler.using(**settings).hash(secret)``. Support for the old method is tentatively scheduled for removal in Passlib 2.0. Context keywords such as ``user`` should still be provided to `hash`.

**Returns:** Resulting password hash, encoded in an algorithm-specific format. This will always be an instance of `str` (i.e. `unicode` under Python 3, ``ascii``-encoded `bytes` under Python 2).

**Raises:**

- `ValueError`:
    - If a `kwd`'s value is invalid (e.g. if a ``salt`` string is too small, or a ``rounds`` value is out of range).
    - If ``secret`` contains characters forbidden by the hash algorithm (e.g. `des_crypt` forbids NULL characters).
- `TypeError`:
    - if ``secret`` is not `unicode` or `bytes`.
    - if a ``kwd`` argument has an incorrect type.
    - if an algorithm-specific required ``kwd`` is not provided.

!!! warning
    Changed in 1.6: Hashes now raise `TypeError` if a required keyword is missing, rather than `ValueError` like in previous releases; in order to conform with normal Python behavior.

!!! warning
    Changed in 1.6: Passlib is now much stricter about input validation: for example, out-of-range ``rounds`` values now cause an error instead of being clipped (though applications may set `relaxed=True` ([relaxed-keyword](#general-informational-attributes)) to restore the old behavior).

!!! warning
    Changed in 1.7: This method was renamed from `encrypt`. Deprecates support for passing settings directly into `hash`.

#### **PasswordHash.encrypt(secret, \*\*kwds)** (classmethod)

Legacy alias for `hash()`.

!!! warning
    Changed in 1.7: This method was renamed to `hash` in version 1.7. This alias will be removed in version 2.0, and should only be used for compatibility with Passlib 1.3 - 1.6.

#### **PasswordHash.verify(secret, hash, \*\*context_kwds)** (classmethod)

Verify a secret using an existing hash.

This checks if a secret matches against the one stored inside the specified hash.

- *secret* (`unicode or bytes`) — A string containing the password to check.
- *hash* (`unicode or bytes`) — A string containing the hash to check against, such as returned by `hash()`. Hashes may be specified as `unicode` or ``ascii``-encoded `bytes`.
- **kwds** — Very few hashes will have additional keywords. The ones that do typically require external contextual information in order to calculate the digest. For these hashes, the values must match the ones passed to the original `hash()` call when the hash was generated, or the password will not verify. These additional keywords are algorithm-specific, and will be listed in that hash's documentation; though the more common keywords are listed under [PasswordHash.context_kwds](#general-informational-attributes). Examples of common keywords include ``user``.

**Returns:** `True` if the secret matches, otherwise `False`.

**Raises:**

- `TypeError`:
    - if either ``secret`` or ``hash`` is not a unicode or bytes instance.
    - if the hash requires additional ``kwds`` which are not provided.
    - if a ``kwd`` argument has the wrong type.
- `ValueError`:
    - if ``hash`` does not match this algorithm's format.
    - if the ``secret`` contains forbidden characters (see `hash()`).
    - if a configuration/salt string generated by `genconfig()` is passed in as the value for ``hash`` (these strings look similar to a full hash, but typically lack the digest portion needed to verify a password).

!!! warning
    Changed in 1.6: This function now raises `ValueError` if ``None`` or a config string is provided instead of a properly-formed hash; previous releases were inconsistent in their handling of these two border cases.

!!! tip
    - [`hash-verifying`](../guide/hash-tutorial.md) tutorial for a usage example.

## Crypt Methods

Taken together, the `genconfig()` and `genhash()` are two tightly-coupled methods that mimic the standard Unix "crypt" interface. The first method generates salt / configuration strings from a set of settings, and the second hashes the password using the provided configuration string.

!!! tip
    Most applications will find `hash()` much more useful, as it combines the functionality of these two methods into one.

#### **PasswordHash.genconfig(\*\*setting_kwds)** (classmethod)

!!! warning
    Changed in 1.7: As of 1.7, this method is deprecated, and slated for complete removal in Passlib 2.0. For all known real-world uses, ``.hash("", **settings)`` should provide equivalent functionality. This deprecation may be reversed if a use-case presents itself in the mean time.

Returns a configuration string encoding settings for hash generation.

This function takes in all the same [PasswordHash.setting_kwds](#general-informational-attributes) as `hash()`, fills in suitable defaults, and encodes the settings into a single "configuration" string, suitable for passing to `genhash()`.

- **kwds** — All additional keywords are algorithm-specific, and will be listed in that hash's documentation; though many of the more common keywords are listed under [PasswordHash.setting_kwds](#general-informational-attributes). Examples of common keywords include ``salt`` and ``rounds``.

**Returns:** A configuration string (as `str`).

**Raises `ValueError`, `TypeError`:** This function raises exceptions for the same reasons as `hash()`.

!!! warning
    Changed in 1.7: This should now always return a full hash string, even in cases where previous releases would return a truncated "configuration only" string, or ``None``.

#### **PasswordHash.genhash(secret, config, \*\*context_kwds)** (classmethod)

Encrypt secret using specified configuration string.

!!! warning
    Changed in 1.7: As of 1.7, this method is deprecated, and slated for complete removal in Passlib 2.0. This deprecation may be reversed if a use-case presents itself in the mean time.

This takes in a password and a configuration string, and returns a hash for that password.

- *secret* (`unicode or bytes`) — string containing the password to be encrypted.
- *config* (`unicode or bytes`) — configuration string to use when hashing the secret. This can either be an existing hash that was previously returned by `genhash()`, or a configuration string that was previously created by `genconfig()`.

!!! warning
    Changed in 1.7: ``None`` is no longer accepted for hashes which (prior to 1.7) lacked a configuration string format.

- **kwds** — Very few hashes will have additional keywords. The ones that do typically require external contextual information in order to calculate the digest. For these hashes, the values must match the ones passed to the original `hash()` call when the hash was generated, or the password will not verify. These additional keywords are algorithm-specific, and will be listed in that hash's documentation; though the more common keywords are listed under [PasswordHash.context_kwds](#general-informational-attributes). Examples of common keywords include ``user``.

**Returns:** Encoded hash matching specified secret, config, and kwds. This will always be a native `str` instance.

**Raises `ValueError`, `TypeError`:** This function raises exceptions for the same reasons as `hash()`.

!!! warning
    Traditionally, password verification using the "crypt" interface was done by testing if ``hash == genhash(password, hash)``. This test is only reliable for a handful of algorithms, as various hash representation issues may cause false results. Applications are strongly urged to use `verify()` instead.

## Factory Creation

One powerful method offered by the `PasswordHash` class is `using()`. This method allows you to quickly create subclasses of a specific hash, providing it with preconfigured defaults specific to your application:

#### **PasswordHash.using(relaxed=False, \*\*settings)** (classmethod)

This method takes in a set of algorithm-specific settings, and returns a new handler object which uses the specified default settings instead.

- **settings** — All keywords are algorithm-specific, and will be listed in that hash's documentation; though many of the more common keywords are listed under [PasswordHash.setting_kwds](#general-informational-attributes). Examples of common keywords include ``rounds`` and ``salt_size``.

**Returns:** A new object which adheres to `PasswordHash` api.

**Raises:**

- `ValueError`: If a keywords's value is invalid (e.g. if a ``salt`` string is too small, or a ``rounds`` value is out of range).
- `TypeError`: if a ``kwd`` argument has an incorrect type.

!!! tip
    [`hash-configuring`](../guide/hash-tutorial.md) tutorial for a usage example.

## Hash Inspection Methods

There are currently two hash inspection methods, `identify()` and `needs_update()`.

#### **PasswordHash.identify(hash)** (classmethod)

Quickly identify if a hash string belongs to this algorithm.

- *hash* (`unicode or bytes`) — the candidate hash string to check

**Returns:**

- `True` if the input is a configuration string or hash string identifiable as belonging to this scheme (even if it's malformed).
- `False` if the input does not belong to this scheme.

**Raises `TypeError`:** if `{hash}` is not a unicode or bytes instance.

!!! note
    A small number of the hashes supported by Passlib lack a reliable method of identification (e.g. [lmhash](passlib.hash.lmhash.md) and [nthash](passlib.hash.nthash.md) both consist of 32 hexadecimal characters, with no distinguishing features). For such hashes, this method may return false positives.

!!! tip
    If you are considering using this method to select from multiple algorithms (e.g. in order to verify a password), you will be better served by the [`CryptContext`](passlib.context.md) class.

## General Informational Attributes

Each hash provides a handful of informational attributes, allowing programs to dynamically adapt to the requirements of different hash algorithms. The following attributes should be defined for all the hashes in passlib:

#### **PasswordHash.name**

Name uniquely identifying this hash.

For the hashes built into Passlib, this will always match the location where it was imported from — `passlib.hash.{name}` — though externally defined hashes may not adhere to this.

This should always be a `str` consisting of lowercase ``a-z``, the digits ``0-9``, and the underscore character ``_``.

#### **PasswordHash.setting_kwds**

Tuple listing the keywords supported by `using()` control hash generation, and which will be encoded into the resulting hash. (These keywords will also be accepted by `hash()` and `genconfig()`, though that behavior is deprecated as of Passlib 1.7; and will be removed in Passlib 2.0).

This list commonly includes keywords for controlling salt generation, adjusting time-cost parameters, etc. Most of these settings are optional, and suitable defaults will be chosen if they are omitted (e.g. salts will be autogenerated).

While the documentation for each hash should have a complete list of the specific settings the hash uses, the following keywords should have roughly the same behavior for all the hashes that support them:

**salt**

Specifies a fixed salt string to use, rather than randomly generating one.

This option is supported by most of the hashes in Passlib, though typically it isn't used, as random generation of a salt is usually the desired behavior. Hashes typically require this to be a `unicode` or `bytes` instance, with additional constraints appropriate to the algorithm.

**salt_size**

Most algorithms which support the ``salt`` setting will autogenerate a salt when none is provided. Most of those hashes will also offer this option, which allows the caller to specify the size of salt which should be generated. If omitted, the hash's default salt size will be used.

!!! tip
    See the [salt info](#salt-information-attributes) attributes (below).

**rounds**

If present, this means the hash can vary the number of internal rounds used in some part of its algorithm, allowing the calculation to take a variable amount of processor time, for increased security.

While this is almost always a non-negative integer, additional constraints may be present for each algorithm (such as the cost varying on a linear or logarithmic scale). This value is typically omitted, in which case a default value will be used. The defaults for all the hashes in Passlib are periodically retuned to strike a balance between security and responsiveness.

!!! tip
    See the [rounds info](#rounds-information-attributes) attributes (below).

**ident**

If present, the class supports multiple formats for encoding the same hash. The class's documentation will generally list the allowed values, allowing alternate output formats to be selected. Note that these values will typically correspond to different revision of the hash algorithm itself, and they may not all offer the same level of security.

**truncate_error**

This will be present if and only if the hash truncates passwords larger than some limit (reported via it's [truncate_size](#general-informational-attributes) attribute). By default, they will silently truncate passwords above their limit. Setting ``truncate_error=True`` will cause `hash()` to raise a `PasswordTruncateError` instead.

**relaxed**

By default, passing an invalid value to `using()` will result in a `ValueError`. However, if ``relaxed=True`` then Passlib will attempt to correct the error and (if successful) issue a `PasslibHashWarning` instead. This warning may then be filtered if desired. Correctable errors include (but are not limited to): ``rounds`` and ``salt_size`` values that are too low or too high, ``salt`` strings that are too large.

#### **PasswordHash.context_kwds**

Tuple listing the keywords supported by `hash()`, `verify()`, and `genhash()`. These keywords are different from the settings kwds in that the context keywords affect the hash, but are not encoded within it, and thus must be provided each time the hash is calculated.

This list commonly includes a user account, http realm identifier, etc. Most of these keywords are required by the hashes which support them, as they are frequently used in place of an embedded salt parameter. *Most hash algorithms in Passlib will have no context keywords.*

While the documentation for each hash should have a complete list of the specific context keywords the hash uses, the following keywords should have roughly the same behavior for all the hashes that support them:

**user**

If present, the class requires a username be specified whenever performing a hash calculation (e.g. [postgres_md5](passlib.hash.postgres_md5.md) and [oracle10](passlib.hash.oracle10.md)).

**encoding**

Some hashes have poorly-defined or host-dependant unicode behavior, and properly hashing a non-ASCII password requires providing the correct encoding ([lmhash](passlib.hash.lmhash.md) is perhaps the worst offender). Hashes which provide this keyword will always expose their default encoding programmatically via the [PasswordHash.default_encoding](#general-informational-attributes) attribute.

**truncate_size**

A positive integer, indicating the hash will truncate any passwords larger than this many bytes. If ``None`` (the more common case), indicates the hash will use the entire password provided. Hashes which specify this setting will also support a ``truncate_error`` flag via their `using()` method, to configure how truncation is handled.

!!! tip
    [`hash-configuring`](../guide/hash-tutorial.md) tutorial for a usage example.

## Salt Information Attributes

For schemes which support a salt string, `"salt"` should be listed in their [PasswordHash.setting_kwds](#general-informational-attributes), and the following attributes should be defined:

#### **PasswordHash.max_salt_size**

The maximum number of bytes/characters allowed in the salt. Should either be a positive integer, or ``None`` (indicating the algorithm has no effective upper limit).

#### **PasswordHash.min_salt_size**

The minimum number of bytes/characters required for the salt. Must be an integer between 0 and [PasswordHash.max_salt_size](#salt-information-attributes).

#### **PasswordHash.default_salt_size**

The default salt size that will be used when generating a salt, assuming ``salt_size`` is not set explicitly. This is typically the same as [max_salt_size](#salt-information-attributes), or a sane default if ``max_salt_size=None``.

#### **PasswordHash.salt_chars**

A unicode string containing all the characters permitted in a salt string. For most [modular-crypt-format](../reference/modular-crypt-format.md) hashes, this is equal to `passlib.utils.binary.HASH64_CHARS`. For the rare hashes where the ``salt`` parameter must be specified in bytes, this will be a placeholder `bytes` object containing all 256 possible byte values.

## Rounds Information Attributes

For schemes which support a variable time-cost parameter, `"rounds"` should be listed in their [PasswordHash.setting_kwds](#general-informational-attributes), and the following attributes should be defined:

#### **PasswordHash.max_rounds**

The maximum number of rounds the scheme allows. Specifying a value beyond this will result in a `ValueError`. This will be either a positive integer, or ``None`` (indicating the algorithm has no effective upper limit).

#### **PasswordHash.min_rounds**

The minimum number of rounds the scheme allows. Specifying a value below this will result in a `ValueError`. Will always be an integer between 0 and [PasswordHash.max_rounds](#rounds-information-attributes).

#### **PasswordHash.default_rounds**

The default number of rounds that will be used if none is explicitly provided to `hash()`. This will always be an integer between [min_rounds](#rounds-information-attributes) and [max_rounds](#rounds-information-attributes).

#### **PasswordHash.rounds_cost**

While the cost parameter ``rounds`` is an integer, how it corresponds to the amount of time taken can vary between hashes. This attribute indicates the scale used by the hash:

- `"linear"` - time taken scales linearly with rounds value (e.g. [sha512_crypt](passlib.hash.sha512_crypt.md))
- `"log2"` - time taken scales exponentially with rounds value (e.g. [bcrypt](passlib.hash.bcrypt.md))
