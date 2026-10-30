# `passlib.registry` - Password Handler Registry

This module contains the code Passlib uses to track all password hash handlers
that it knows about. While custom handlers can be used directly within an application,
or even handed to a [`CryptContext`](passlib.context.md); it is frequently useful to register
them globally within a process and then refer to them by name.
This module provides facilities for that, as well as programmatically
querying Passlib to detect what algorithms are available.

!!! warning
    This module is primarily used as an internal support module.
    Its interface has not been finalized yet, and may be changed somewhat
    between major releases of Passlib, as the internal code is cleaned up
    and simplified.

    Applications should access hashes through the `passlib.hash` module
    where possible (new ones may also be registered by writing to that module).

## Interface

::: passlib.registry.get_crypt_handler

::: passlib.registry.list_crypt_handlers

::: passlib.registry.register_crypt_handler_path

::: passlib.registry.register_crypt_handler

!!! note
    All password hashes registered with passlib
    can be imported by name from the `passlib.hash` module.
    This is true not just of the built-in hashes,
    but for any hash registered with the registration functions
    in this module.

## Usage

Example showing how to use `register_crypt_handler_path()`:

```python
# register the location of a handler without loading it
from passlib.registry import register_crypt_handler_path

register_crypt_handler_path("myhash", "myapp.support.hashes")

# even before being loaded, its name will show up as available
from passlib.registry import list_crypt_handlers

print("myhash" in list_crypt_handlers())
# > True
print("myhash" in list_crypt_handlers(loaded_only=True))
# > False

# when the name "myhash" is next referenced,
# the class "myhash" will be imported from the module "myapp.support.hashes"
from passlib.context import CryptContext

cc = CryptContext(schemes=["myhash"])  # <-- this will cause autoimport
```

Example showing how to load a hash by name:

```python
from passlib.registry import get_crypt_handler

print(get_crypt_handler("sha512_crypt"))
# > <class 'passlib.handlers.sha2_crypt.sha512_crypt'>

# raises KeyError: "no crypt handler found for algorithm: 'missing_hash'"
get_crypt_handler("missing_hash")

print(get_crypt_handler("missing_hash", None))
# > None
```
