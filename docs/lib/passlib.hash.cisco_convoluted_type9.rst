.. index:: Cisco; convoluted Type 9 hash

===================================================================================
:class:`passlib.hash.cisco_convoluted_type9` - Cisco "convoluted Type 9" hash
===================================================================================

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the "convoluted Type 9" hash Cisco IOS XE stores in place
of a :doc:`Type 5 <passlib.hash.md5_crypt>` secret, when it converts one
(on upgrade to 16.12 or later, and on 17.15 at least when a Type 5 secret is
configured). It is shown as :samp:`secret 9 $14$...`.
This class can be used directly as follows::

    >>> from passlib.hash import cisco_convoluted_type9

    >>> # hash password
    >>> h = cisco_convoluted_type9.hash("password")
    >>> h
    '$14$.PcA$jtmZlPDPYiJLWP$/sW4AQsJdN4ISUbnFOTrx/smqTGUF3RBfjNdwMIAnE.'

    >>> # verify password
    >>> cisco_convoluted_type9.verify("password", h)
    True
    >>> cisco_convoluted_type9.verify("wrong", h)
    False

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: cisco_convoluted_type9()

Format & Algorithm
==================
A hash has the format :samp:`$14${md5_salt}${salt}${checksum}`, where:

* :samp:`{md5_salt}` is the 4 character salt of the Type 5 secret it was
  converted from.

* :samp:`{salt}` is 14 characters drawn from ``[./0-9A-Za-z]``.

* :samp:`{checksum}` is the :doc:`Type 9 <passlib.hash.cisco_type9>` scrypt
  digest of the whole Type 5 secret (:samp:`$1${md5_salt}${md5_checksum}`),
  using :samp:`{salt}`.

Anyone holding the original Type 5 secret, from an old configuration for
example, can compute this hash without knowing the password. Setting the
password again replaces it with a hash of the password itself.
