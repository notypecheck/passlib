.. index:: Cisco; ASA PBKDF2 hash

==================================================================
:class:`passlib.hash.cisco_asa_pbkdf2` - Cisco ASA "pbkdf2" hash
==================================================================

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the "pbkdf2" password hash used by Cisco ASA
(``username NAME password HASH pbkdf2``), which ASA uses when a user's
password is configured in plain text.
It is PBKDF2-HMAC-SHA512 with 5000 rounds by default.
This class can be used directly as follows::

    >>> from passlib.hash import cisco_asa_pbkdf2

    >>> # hash password
    >>> h = cisco_asa_pbkdf2.hash("password")
    >>> h
    '$sha512$5000$hLB2zpnTOseYMybEOCdkjA==$P8+W86j6dMPya5haeDfm0Q=='

    >>> # verify password
    >>> cisco_asa_pbkdf2.verify("password", h)
    True
    >>> cisco_asa_pbkdf2.verify("wrong", h)
    False

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: cisco_asa_pbkdf2()

Format & Algorithm
==================
A hash has the format :samp:`$sha512${rounds}${salt}${checksum}`, where:

* :samp:`{rounds}` is the number of PBKDF2 rounds, in decimal.
  ASA 9.24 generates 5000. It also accepted hashes made with 1000 and 10000
  rounds, and a login against the 10000 round hash succeeded.

* :samp:`{salt}` is 16 bytes, encoded with standard base64, with padding
  (24 characters).

* :samp:`{checksum}` is the first 16 bytes of the PBKDF2-HMAC-SHA512 digest of the
  password, using the raw salt bytes and the given number of rounds,
  encoded with standard base64, with padding (24 characters).

Unlike :class:`~passlib.hash.cisco_asa`, the username isn't part of the hash.
ASA 9.24 refuses passwords longer than 127 bytes, so :meth:`~passlib.ifc.PasswordHash.hash`
raises :exc:`~passlib.exc.PasswordSizeError` for them, and
:meth:`~passlib.ifc.PasswordHash.verify` never matches them.
Unicode passwords are encoded as UTF-8.
