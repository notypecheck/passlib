# `passlib.utils.handlers` - Framework for writing password hashes

Framework for writing password hashes.

!!! warning
    This module is primarily used as an internal support module. Its interface has not been finalized yet, and may be changed somewhat between major releases of Passlib, as the internal code is cleaned up and simplified.

!!! note
    **TODO:** This module, and the instructions on how to write a custom handler, definitely need to be rewritten for clarity. They are not yet organized, and may leave out some important details.

## Implementing Custom Handlers

All that is required in order to write a custom handler that will work with Passlib is to create an object (be it module, class, or object) that exposes the functions and attributes required by the [PasswordHash API](passlib.ifc.md#passwordhash-api).
For classes, Passlib does not make any requirements about what a class instance should look like (if the implementation even uses them).

That said, most of the handlers built into Passlib are based around the `GenericHandler` class, and its associated mixin classes. While deriving from this class is not required, doing so will greatly reduce the amount of additional code that is needed for all but the most convoluted password hash schemes.

Once a handler has been written, it may be used explicitly, passed into a `CryptContext` constructor, or registered globally with Passlib via the [`passlib.registry`](passlib.registry.md) module.

!!! tip
    See [Testing Hash Handlers](#testing-hash-handlers) for details about how to test custom handlers against Passlib's unittest suite.

## The GenericHandler Class

### Design

Most of the handlers built into Passlib are based around the `GenericHandler` class. This class is designed under the assumption that the common workflow for hashes is some combination of the following:

1. parse hash into constituent parts - performed by `from_string()`.
2. validate constituent parts - performed by `GenericHandler`'s constructor, and the normalization functions such as `_norm_checksum()` and `HasSalt._norm_salt()` which are provided by its related mixin classes.
3. calculate the raw checksum for a specific password - performed by `_calc_checksum()`.
4. assemble hash, including new checksum, into a new string - performed by `to_string()`.

With this in mind, `GenericHandler` provides implementations of most of the [PasswordHash API](passlib.ifc.md#passwordhash-api) methods, eliminating the need for almost all the boilerplate associated with writing a password hash.

In order to minimize the amount of unneeded features that must be loaded in, the `GenericHandler` class itself contains only the parts which are needed by almost all handlers: parsing, rendering, and checksum validation.
Validation of all other parameters (such as salt, rounds, etc) is split out into separate [mixin classes](#generichandler-mixins) which enhance `GenericHandler` with additional features.

### Usage

In order to use `GenericHandler`, just subclass it, and then do the following:

- fill out the `name` attribute with the name of your hash.
- fill out the `PasswordHash.setting_kwds` attribute with a tuple listing all the settings your hash accepts.
- provide an implementation of the `from_string()` classmethod.

    This method should take in a potential hash string, parse it into components, and return an instance of the class which contains the parsed components. It should throw a `ValueError` if no hash, or an invalid hash, is provided.

- provide an implementation of the `to_string()` instance method.

    This method should render an instance of your handler class (such as returned by `from_string()`), returning a hash string.

- provide an implementation of the `_calc_checksum()` instance method.

    This is the heart of the hash; this method should take in the password as the first argument, then generate and return the digest portion of the hash, according to the settings (such as salt, etc) stored in the parsed instance this method was called from.

    Note that it should not return the full hash with identifiers, etc; that job should be performed by `to_string()`.

Some additional notes:

- In addition to simply subclassing `GenericHandler`, most handlers will also benefit from adding in some of the mixin classes that are designed to add features to `GenericHandler`. See [mixin classes](#generichandler-mixins) for more details.
- Most implementations will want to alter/override the default `identify()` method. By default, it returns ``True`` for all hashes that `from_string()` can parse without raising a `ValueError`; which is reliable, but somewhat slow. For faster identification purposes, subclasses may fill in the `ident` attribute with the hash's identifying prefix, which `identify()` will then test for instead of calling `from_string()`. For more complex situations, a custom implementation should be used; the `HasManyIdents` mixin may also be helpful.
- This class does not support context kwds of any type, since that is a rare enough requirement inside passlib.

### Interface

::: passlib.utils.handlers.GenericHandler

## GenericHandler Mixins

::: passlib.utils.handlers.HasSalt

::: passlib.utils.handlers.HasRounds

::: passlib.utils.handlers.HasManyIdents

::: passlib.utils.handlers.HasManyBackends

::: passlib.utils.handlers.HasRawSalt

::: passlib.utils.handlers.HasRawChecksum

### Examples

!!! note
    **TODO:** Show some walk-through examples of how to use GenericHandler and its mixins.

## The StaticHandler class

::: passlib.utils.handlers.StaticHandler

!!! note
    **TODO:** Show some examples of how to use StaticHandler.

## Other Constructors

::: passlib.utils.handlers.PrefixWrapper

## Testing Hash Handlers

Within its unittests, Passlib provides the `passlib.tests.utils.HandlerCase` class, which can be subclassed to provide a unittest-compatible test class capable of checking if a handler adheres to the [PasswordHash API](passlib.ifc.md#passwordhash-api).

### Usage

As an example of how to use `HandlerCase`, the following is an annotated version of the unittest for [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md):

```python
from passlib.hash import des_crypt
from passlib.tests.utils import HandlerCase


# create a subclass for the handler...
class DesCryptTest(HandlerCase):
    "test des-crypt algorithm"

    # [required] - store the handler object itself in the handler attribute
    handler = des_crypt

    # [required] - this should be a list of (password, hash) pairs,
    #              which should all verify correctly using your handler.
    #              it is recommend include pairs which test all of the following:
    #
    #              * empty string & short strings for passwords
    #              * passwords with 2 byte unicode characters
    #              * hashes with varying salts, rounds, and other options
    known_correct_hashes = (
        # format: (password, hash)
        ("", "OgAwTx2l6NADI"),
        (" ", "/Hk.VPuwQTXbc"),
        ("test", "N1tQbOFcM5fpg"),
        ("Compl3X AlphaNu3meric", "um.Wguz3eVCx2"),
        ("4lpHa N|_|M3r1K W/ Cur5Es: #$%(*)(*%#", "sNYqfOyauIyic"),
        ("AlOtBsOl", "cEpWz5IUCShqM"),
        ("hell\u00d6", "saykDgk3BPZ9E"),
    )

    # [optional] - if there are hashes which are similar in format
    #              to your handler, and you want to make sure `identify()`
    #              does not return ``True`` for such hashes,
    #              list them here. otherwise this can be omitted.
    #
    known_unidentified_hashes = [
        # bad char in otherwise correctly formatted hash
        "!gAwTx2l6NADI",
    ]
```

`HandlerCase` is part of Passlib's test suite (not the public API); see `passlib/tests/utils.py` for its full interface.
