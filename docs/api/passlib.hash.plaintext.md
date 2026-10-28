# `passlib.hash.plaintext` - Plaintext

This class stores passwords in plaintext. This is, of course, ridiculously insecure;
it is provided for backwards compatibility when migrating
existing applications. *It should not be used* for any other purpose.
This class should always be the last algorithm checked, as it will recognize all hashes.
It can be used directly as follows:

```python
from passlib.hash import plaintext as plaintext

# "encrypt" password
print(plaintext.hash("password"))
# > 'password'

# verify password
print(plaintext.verify("password", "password"))
# > True
print(plaintext.verify("secret", "password"))
# > False
```

!!! tip
    - `password hash usage` -- for more usage examples

    - [`ldap_plaintext`](passlib.hash.ldap_std.md#plaintext) -- on LDAP systems, this format is probably more appropriate for storing plaintext passwords.

## Interface

::: passlib.hash.plaintext
