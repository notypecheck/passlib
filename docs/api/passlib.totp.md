# `passlib.totp` -- TOTP / Two Factor Authentication

The `passlib.totp` module provides totp / two factor authentication.

!!! warning
    Changed in 1.7: Added.

## Overview

The `passlib.totp` module provides a number of classes for implementing two-factor authentication (2FA) using the TOTP [^totpspec] specification. This page provides a reference to all the classes and methods in this module.

Passlib's TOTP support is centered around the [`TOTP`](#totp-class) class. There are also some additional helpers, including the [`AppWallet`](#appwallet) class, which helps to securely encrypt TOTP keys for storage.

!!! tip
    - [`TOTP Tutorial`](../guide/totp-tutorial.md) -- Overview of this module and walkthrough of how to use it.

## TOTP Class

::: passlib.totp.TOTP

See below for all the `TOTP` methods & attributes...

## Alternate Constructors

There are a few alternate class constructors offered. These range from simple convenience wrappers such as `new()`, to deserialization methods such as `from_source()`. These are all covered by the [`TOTP`](#totp-class) reference above: `new()`, `from_source()`, `from_uri()`, `from_json()`, and `from_dict()`.

## Factory Creation

One powerful method offered by the TOTP class is `using()`. This method allows you to quickly create TOTP subclasses with preconfigured defaults, for configuration application secrets and setting default TOTP behavior for your application: covered by the [`TOTP`](#totp-class) reference above.

## Basic Attributes

All the TOTP objects offer the following attributes, which correspond to the constructor options above. Most of this information will be serialized by `to_uri()` and `to_json()`: these are all covered by the [`TOTP`](#totp-class) reference above (`key`, `hex_key`, `base32_key`, `label`, `issuer`, `digits`, `alg`, `period`, and `changed`).

## Token Generation

Token generation is generally useful client-side, and for generating values to test your server implementation. There is one main generation method: `generate()`.

!!! warning
    Tokens should be displayed as strings, as they may contain leading zeros which will get stripped if they are first converted to an `int`.

### TotpToken

The `TOTP.generate` method returns instances of the following class, which offers up detailed information about the generated token:

::: passlib.totp.TotpToken

## Token Matching / Verification

Matching user-provided tokens is the main operation when implementing server-side TOTP support. Passlib offers one main method: `TOTP.match`, as well as a convenience wrapper `TOTP.verify`: both covered by the [`TOTP`](#totp-class) reference above.

!!! tip
    [`totp-verifying`](../guide/totp-tutorial.md) tutorial for a usage example.

### TotpMatch

If successful, the `TOTP.verify` method returns instances of the following class, which offers up detailed information about the matched token:

::: passlib.totp.TotpMatch

## Client Configuration Methods

Once a server has generated a new TOTP key & configuration, it needs to be communicated to the user in order for them to store it in a suitable TOTP client.

This can be done by displaying the key & configuration for the user to hand-enter into their client, or by encoding TOTP object into a URI [^uriformat]. These configuration URIs can subsequently be displayed as a QR code, for easy transfer to many smartphone-based TOTP clients (such as Authy or Google Authenticator).

The `to_uri()` and `pretty_key()` methods are covered by the [`TOTP`](#totp-class) reference above.

!!! tip
    - The `from_source` and `from_uri` constructors for decoding URIs.
    - The [`totp-configuring-clients`](../guide/totp-tutorial.md) tutorial for details about these methods, and how to render URIs to a QR Code.

## Serialization Methods

The `to_uri()` method is useful, but limited, because it requires additional information (label & issuer), and lacks the ability to encrypt the key. The `TOTP` provides the following methods for serializing TOTP objects to internal storage: `to_json()` and `to_dict()`, both covered by the [`TOTP`](#totp-class) reference above. When application secrets are configured via `using()`, these methods will automatically encrypt the resulting keys.

!!! tip
    - The `from_source` and `from_json` constructors for decoding the results of these methods.
    - The [`totp-storing-instances`](../guide/totp-tutorial.md) tutorial for more details.

## Helper Methods

While `generate()`, `match()`, and `verify()` automatically handle normalizing tokens & time values, the following methods are exposed in case they are useful in other contexts: `normalize_token()` and `normalize_time()`, both covered by the [`TOTP`](#totp-class) reference above.

## AppWallet

The `AppWallet` class is used internally by the `using()` method to store the application secrets provided for handling encrypted keys. If needed, they can also be created and passed in directly.

::: passlib.totp.AppWallet

## Support Functions

::: passlib.totp.generate_secret

## Deviations

- The TOTP Spec [^totpspec] includes an param (`T0`) providing an optional offset from the base time. Passlib omits this parameter (fixing it at `0`), but so do pretty much all other TOTP implementations.

[^totpspec]: TOTP Specification - `RFC 6238`

## References

- HOTP Specification - `RFC 4226`

[^uriformat]: Google's OTPAuth URI format - <https://github.com/google/google-authenticator/wiki/Key-Uri-Format>
