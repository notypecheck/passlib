.. index:: Postgres; SCRAM-SHA-256 hash

====================================================================================
:class:`passlib.hash.postgres_scram_sha256` - PostgreSQL SCRAM-SHA-256 password hash
====================================================================================

.. versionadded:: 1.10

.. currentmodule:: passlib.hash

This class implements the SCRAM-SHA-256 password hash used by PostgreSQL 10
and later to store its user account passwords, when ``password_encryption``
is ``scram-sha-256`` (the default since PostgreSQL 14) [#auth]_.
This class can be used directly as follows::

    >>> from passlib.hash import postgres_scram_sha256

    >>> # hash password
    >>> hash = postgres_scram_sha256.hash("password")
    >>> hash
    'SCRAM-SHA-256$4096:z9mbc46xFkKI0ZqTcm6N8Q==$9xxYjUa27PA80YPPDLwH4UA2XGuC8SReVxa8uG5462Q=:it4zu7NdhJxGuoQH0GjQ70nyP/uvZOpL1MgFOkzb11U='

    >>> # verify password
    >>> postgres_scram_sha256.verify("password", hash)
    True
    >>> postgres_scram_sha256.verify("wrong", hash)
    False

.. seealso:: the generic :ref:`PasswordHash usage examples <password-hash-examples>`

Interface
=========
.. autoclass:: postgres_scram_sha256()

Format & Algorithm
==================
A hash has the format :samp:`SCRAM-SHA-256${rounds}:{salt}${stored_key}:{server_key}`,
where:

* :samp:`{rounds}` is the number of PBKDF2 iterations, in decimal
  (PostgreSQL's ``scram_iterations``, 4096 by default).

* :samp:`{salt}` is the salt, base64 encoded (PostgreSQL generates 16 bytes).

* :samp:`{stored_key}` and :samp:`{server_key}` are the SCRAM ``StoredKey`` and
  ``ServerKey`` from :rfc:`5802`, base64 encoded::

    SaltedPassword = PBKDF2-HMAC-SHA256(password, salt, rounds)
    StoredKey      = SHA256(HMAC-SHA256(SaltedPassword, "Client Key"))
    ServerKey      = HMAC-SHA256(SaltedPassword, "Server Key")

The password is first normalized with SASLprep (:rfc:`4013`), as PostgreSQL
does it [#saslprep]_: if the password is not valid UTF-8, or contains characters SASLprep
prohibits, it is used unchanged. :func:`passlib.utils.saslprep` instead raises
an error for such passwords, and differs in a few other edge cases.

.. rubric:: Footnotes

.. [#auth] PostgreSQL documentation on password authentication -
       `<https://www.postgresql.org/docs/current/auth-password.html>`_

.. [#saslprep] PostgreSQL's SASLprep implementation -
       `<https://github.com/postgres/postgres/blob/master/src/common/saslprep.c>`_
