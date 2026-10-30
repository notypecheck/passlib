# `passlib.utils.des` - DES routines [deprecated]

Routines for performing DES encryption.

!!! warning
    This module is deprecated as of Passlib 1.7: It has been relocated to [`passlib.crypto.des`](passlib.crypto.des.md); and the aliases here will be removed in Passlib 2.0.

This module contains routines for encrypting blocks of data using the DES algorithm.
Note that these functions do not support multi-block operation or decryption,
since they are designed primarily for use in password hash algorithms
(such as [`passlib.hash.des_crypt`](passlib.hash.des_crypt.md) and [`passlib.hash.bsdi_crypt`](passlib.hash.bsdi_crypt.md)).

## Interface

::: passlib.utils.des.expand_des_key

::: passlib.utils.des.des_encrypt_block

::: passlib.utils.des.des_encrypt_int_block
