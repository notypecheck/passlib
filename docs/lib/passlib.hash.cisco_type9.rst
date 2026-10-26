.. index:: Cisco; Type 9 hash

==================================================================
:class:`passlib.hash.cisco_type9` - Cisco "Type 9" hash
==================================================================

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the "Type 9" password hash used by Cisco IOS and IOS XE
(``username NAME algorithm-type scrypt secret PASSWORD``).
It is scrypt with N=16384, r=1 and p=1.
This class can be used directly as follows::

    >>> from passlib.hash import cisco_type9

    >>> # hash password
    >>> h = cisco_type9.hash("password")
    >>> h
    '$9$W2eU0gaJAJQRld$H4vjdXH5kr8mbHY6/AstNFoBgsNiKBNsMJcoP7wj0S6'

    >>> # verify password
    >>> cisco_type9.verify("password", h)
    True
    >>> cisco_type9.verify("wrong", h)
    False

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: cisco_type9()

Format & Algorithm
==================
A hash has the format :samp:`$9${salt}${checksum}`, where:

* :samp:`{salt}` is 14 characters drawn from ``[./0-9A-Za-z]``.

* :samp:`{checksum}` is the scrypt digest of the password, using the salt string
  (as ASCII bytes), N=16384, r=1 and p=1, producing 32 bytes,
  encoded with base64 in the ``./0-9A-Za-z`` alphabet, without padding
  (43 characters).

Passwords longer than 127 bytes are truncated to their first 127 bytes, as
IOS XE 17.15 does. Unicode passwords are encoded as UTF-8.
