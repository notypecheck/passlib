.. index:: Juniper; $9$ encoding

==================================================================
:class:`passlib.hash.junos9` - Juniper Junos "$9$" encoding
==================================================================

.. danger::

    This is not a hash, this is a reversible plaintext encoding.
    **This format can be trivially decoded**.

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the "$9$" encoding Juniper Junos uses for secrets in its
configuration, such as RADIUS, TACACS+ and routing protocol authentication keys.
Like Cisco's :doc:`type 7 <passlib.hash.cisco_type7>`, it only hides the secret
from casual view, and can be trivially decoded.
This class can be used directly as follows::

    >>> from passlib.hash import junos9

    >>> # encode password
    >>> h = junos9.hash("password")
    >>> h
    '$9$U1DqfTQnCpBFnvLNboaFn/9A0'

    >>> # verify password
    >>> junos9.verify("password", h)
    True
    >>> junos9.verify("letmein", h)
    False

    >>> # to demonstrate this is an encoding, not a real hash,
    >>> # this class supports decoding the resulting string:
    >>> junos9.decode(h)
    'password'

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: junos9()

Format & Algorithm
==================
This follows existing implementations [#crypt-juniper]_, and was checked
against secrets generated on Junos.
An encoded secret has the format :samp:`$9${salt}{padding}{checksum}`, where:

* :samp:`{salt}` is one character from a 65 character alphabet, split into four
  families. The family the salt is in sets the number of random
  :samp:`{padding}` characters (0 to 3) that follow it.

* :samp:`{checksum}` encodes each byte of the secret as 2 to 4 characters.
  Each character is some distance further through the alphabet than the
  character before it (starting from the salt); those distances less one,
  weighted by a fixed table that cycles every 7 bytes, add up to the byte's
  value.

Junos encodes the UTF-8 bytes of the secret. The padding characters do not
affect the encoding, so the effective salt is only the first character.

.. rubric:: Footnotes

.. [#crypt-juniper] Perl implementation by Kevin Brintnall -
       `<https://metacpan.org/pod/Crypt::Juniper>`_
