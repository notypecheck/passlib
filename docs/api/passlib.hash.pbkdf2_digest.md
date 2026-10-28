# `passlib.hash.pbkdf2_{digest}` - Generic PBKDF2 Hashes

Passlib provides three custom hash schemes based on the PBKDF2 [^pbkdf2] algorithm
which are compatible with the [modular crypt format](../reference/modular-crypt-format.md):

- `pbkdf2_sha1`
- `pbkdf2_sha256`
- `pbkdf2_sha512`

Security-wise, PBKDF2 is currently one of the leading key derivation functions,
and has no known security issues.
Though the original PBKDF2 specification uses the SHA-1 message digest,
it is not vulnerable to any of the known weaknesses of SHA-1 [^hmac-sha1],
and can be safely used. However, for those still concerned, SHA-256 and SHA-512
versions are offered as well.
PBKDF2-SHA512 is one of the four hashes Passlib
[recommends](../guide/quickstart.md#recommended-hashes) for new applications.

All of these classes can be used directly as follows:

```python
from passlib.hash import pbkdf2_sha256

# generate new salt, hash password
hash = pbkdf2_sha256.hash("password")
print(hash)
# > '$pbkdf2-sha256$6400$0ZrzXitFSGltTQnBWOsdAw$Y11AchqV4b0sUisdZd0Xr97KWoymNE0LNNrnEgY4H9M'

# same, but with an explicit number of rounds and salt length
print(pbkdf2_sha256.using(rounds=8000, salt_size=10).hash("password"))
# > '$pbkdf2-sha256$8000$XAuBMIYQQogxRg$tRRlz8hYn63B9LYiCd6PRo6FMiunY9ozmMMI3srxeRE'

# verify the password
print(pbkdf2_sha256.verify("password", hash))
# > True
print(pbkdf2_sha256.verify("wrong", hash))
# > False
```

!!! tip
    - `password hash usage` -- for more usage examples

    - [`ldap_pbkdf2_{digest}`](passlib.hash.ldap_pbkdf2_digest.md) -- alternate LDAP-compatible versions of these hashes.

## Interface

::: passlib.hash.pbkdf2_sha256

`pbkdf2_sha512`: except for the choice of message digest, this class is the same as `pbkdf2_sha256`.

`pbkdf2_sha1`: except for the choice of message digest, this class is the same as `pbkdf2_sha256`.

## Format & Algorithm

An example `pbkdf2_sha256` hash (of `password`):

```
$pbkdf2-sha256$6400$.6UI/S.nXIk8jcbdHx3Fhg$98jZicV16ODfEsEZeYPGHU3kbrUrvUEXOPimVSQDD44
```

All of the pbkdf2 hashes defined by passlib
follow the same format, `$pbkdf2-{digest}${rounds}${salt}${checksum}`.

- `$pbkdf2-{digest}$` is used as the [modular-crypt-format](../reference/modular-crypt-format.md) identifier
  (`$pbkdf2-sha256$` in the example).

- `{digest}` - this specifies the particular cryptographic hash
  used in conjunction with HMAC to form PBKDF2's pseudorandom function
  for that particular hash (`sha256` in the example).

- `{rounds}` - the number of iterations that should be performed.
  this is encoded as a positive decimal number with no zero-padding
  (`6400` in the example).

- `{salt}` - this is the `adapted base64 encoding` (`ab64_encode()`)
  of the raw salt bytes passed into the PBKDF2 function.

- `{checksum}` - this is the `adapted base64 encoding` (`ab64_encode()`)
  of the raw derived key bytes returned from the PBKDF2 function.
  Each scheme uses the digest size of its specific hash algorithm (`{digest}`)
  as the size of the raw derived key. This is enlarged
  by approximately 4/3 by the base64 encoding,
  resulting in a checksum size of 27, 43, and 86 for each of the respective algorithms listed above.

The algorithm used by all of these schemes is deliberately identical and simple:
The password is encoded into UTF-8 if not already encoded,
and run through `pbkdf2_hmac()`
along with the decoded salt, the number of rounds,
and a prf built from HMAC + the respective message digest.
The result is then encoded using `ab64_encode()`.

[^pbkdf2]: The specification for the PBKDF2 algorithm - <http://tools.ietf.org/html/rfc2898#section-5.2>, part of RFC 2898.

[^hmac-sha1]: While SHA1 has fallen to collision attacks, HMAC-SHA1 as used by PBKDF2 is still considered secure - <http://www.schneier.com/blog/archives/2005/02/sha1_broken.html>.
