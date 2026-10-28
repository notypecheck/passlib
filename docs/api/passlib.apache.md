# `passlib.apache` - Apache Password Files

This module provides utilities for reading and writing Apache's htpasswd and htdigest files, through the use of two helper classes.

!!! warning
    Changed in 1.6: The api for this module was updated to be more flexible, and to have less ambiguous method names. The old method and keyword names are deprecated, and will be removed in Passlib 1.8.

!!! warning
    Changed in 1.7: These classes will now preserve blank lines and "#" comments when updating htpasswd files; previous releases would throw a parse error.

!!! warning
    Changed in 1.8: A number of methods deprecated since 1.6, have been removed.

## Htpasswd Files

The `HtpasswdFile` class allows managing of htpasswd files.
A quick summary of its usage:

```python
from passlib.apache import HtpasswdFile

# when creating a new file, set to new=True, add entries, and save.
ht = HtpasswdFile("test.htpasswd", new=True)
ht.set_password("someuser", "really secret password")
ht.save()

# loading an existing file to update a password
ht = HtpasswdFile("test.htpasswd")
ht.set_password("someuser", "new secret password")
ht.save()

# examining file, verifying user's password
ht = HtpasswdFile("test.htpasswd")
print(ht.users())
# > ["someuser"]
print(ht.check_password("someuser", "wrong password"))
# > False
print(ht.check_password("someuser", "new secret password"))
# > True

# making in-memory changes and exporting to string
ht = HtpasswdFile()
ht.set_password("someuser", "mypass")
ht.set_password("someuser", "anotherpass")
s = ht.to_string()
print(s)
# > someuser:$apr1$T4f7D9ly$EobZDROnHblCNPCtrgh5i/
# > anotheruser:$apr1$vBdPWvh1$GrhfbyGvN/7HalW5cS9XB1
```

!!! warning
    `HtpasswdFile` currently defaults to using [`apr_md5_crypt`](passlib.hash.apr_md5_crypt.md),
    as this is the only htpasswd hash guaranteed to be portable across operating systems.
    However, for security reasons Passlib 1.7 will default to using the strongest algorithm
    available on the host platform (e.g. [`bcrypt`](passlib.hash.bcrypt.md) or [`sha256_crypt`](passlib.hash.sha256_crypt.md)).
    Applications that are relying on the old behavior should specify
    `HtpasswdFile(default_scheme="portable")` (new in Passlib 1.6.3).

::: passlib.apache.HtpasswdFile

## Htdigest Files

The `HtdigestFile` class allows management of htdigest files
in a similar fashion to [`HtpasswdFile`](passlib.apache.md#htpasswd-files).

::: passlib.apache.HtdigestFile

## References

- Htpasswd Manual - <http://httpd.apache.org/docs/current/programs/htpasswd.html>
- Apache Auth Configuration - <http://httpd.apache.org/docs/current/howto/auth.html>
