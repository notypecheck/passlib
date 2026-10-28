# `passlib.crypto.des` - DES routines

Routines for performing DES encryption.

!!! warning
    Changed in 1.7: This module was relocated from `passlib.utils.des`; the old location will be removed in Passlib 2.0.

!!! warning
    NIST has declared DES to be "inadequate" for cryptographic purposes. These routines, and the password hashes based on them, should not be used in new applications.

This module contains routines for encrypting blocks of data using the DES algorithm.
Note that these functions do not support multi-block operation or decryption,
since they are designed primarily for use in password hash algorithms
(such as [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md) and [`passlib.hash.bsdi_crypt`](passlib.hash.bsdi_crypt.md)).

## Interface

::: passlib.crypto.des.expand_des_key

::: passlib.crypto.des.des_encrypt_block

::: passlib.crypto.des.des_encrypt_int_block
