# `passlib.hash.ldap_{other}` - Non-Standard RFC2307 Hashes

This section as a catch-all for a number of password hash formats supported by Passlib which use RFC 2307 style encoding, but are not part of any standard.

!!! tip
    - `password hash usage` -- for examples of how to use these classes via the common hash interface.

    - `ldap-hashes` for a full list of RFC 2307 style hashes.

## Hexadecimal Digests

All of the digests specified in RFC 2307 use base64 encoding. The following are non-standard versions which use hexadecimal encoding, as is found in some applications.

`ldap_hex_md5` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

hexadecimal version of `ldap_md5`, this is just the md5 digest of the password. an example hash (of `password`) is `{MD5}5f4dcc3b5aa765d61d8327deb882cf99`.

`ldap_hex_sha1` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

hexadecimal version of `ldap_sha1`, this is just the sha1 digest of the password. an example hash (of `password`) is `{SHA}5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8`.

## Other Hashes

`roundup_plaintext` shares the standard [`PasswordHash`](passlib.ifc.md) interface.

RFC 2307 specifies plaintext passwords should be stored without any identifying prefix. This class implements an alternate method used by the Roundup Issue Tracker [^roundup], which (when storing plaintext passwords) uses the identifying prefix `{plaintext}`. an example hash (of `password`) is `{plaintext}password`.

[^roundup]: Roundup Issue Tracker homepage - <http://www.roundup-tracker.org>
