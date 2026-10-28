.. index:: Cisco; Type 8 hash

==================================================================
:class:`passlib.hash.cisco_type8` - Cisco "Type 8" hash
==================================================================

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the "Type 8" password hash used by Cisco IOS and IOS XE
(``username NAME algorithm-type sha256 secret PASSWORD``).
It is PBKDF2-HMAC-SHA256 with 20000 rounds.
This class can be used directly as follows::

    >>> from passlib.hash import cisco_type8

    >>> # hash password
    >>> h = cisco_type8.hash("password")
    >>> h
    '$8$9uum9nJ/8eN0fS$L43GCee9qGnrx.1QAjvJZ0LFZlgB3yXZmpuyFZ4Txd2'

    >>> # verify password
    >>> cisco_type8.verify("password", h)
    True
    >>> cisco_type8.verify("wrong", h)
    False

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: cisco_type8()

Format & Algorithm
==================
A hash has the format :samp:`$8${salt}${checksum}`, where:

* :samp:`{salt}` is 14 characters drawn from ``[./0-9A-Za-z]``.

* :samp:`{checksum}` is the PBKDF2-HMAC-SHA256 digest of the password, using the salt
  string (as ASCII bytes) and 20000 rounds, producing 32 bytes,
  encoded with base64 in the ``./0-9A-Za-z`` alphabet, without padding
  (43 characters).

Passwords longer than 127 bytes are truncated to their first 127 bytes, as
IOS XE 17.15 does. Unicode passwords are encoded as UTF-8.
