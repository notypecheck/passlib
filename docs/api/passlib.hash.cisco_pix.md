# passlib.hash.cisco_pix - Cisco PIX MD5 hash

!!! danger
    **This algorithm is not considered secure by modern standards.** It should only be used when verifying existing hashes, or when interacting with applications that require this format. For new code, see the list of [recommended hashes](../guide/quickstart.md#recommended-hashes).

## Overview

!!! warning
    **Caveat Emptor**
    Passlib's implementations of `cisco_pix` and `cisco_asa` both need verification.
    For those with access to Cisco PIX and ASA systems, verifying Passlib's reference vectors
    would be a great help (see [Issue #51](https://github.com/notypecheck/passlib/issues/51)). In the mean time, there are no guarantees
    that passlib correctly replicates the official implementation.

    Changed in 1.7.1: A number of bugs were fixed after expanding the reference vectors, and testing against an ASA 9.6 system.

The `cisco_asa` class implements the "encrypted" password hash algorithm commonly found on Cisco
ASA systems. The companion `cisco_pix` class
implements the older variant found on Cisco PIX.
Aside from internal differences, and slightly different limitations,
the two hashes have the same format, and in some cases the same output.

These classes can be used directly to generate or verify a hash for a specific
user.  Specifying the user account name is required for this hash:

```python
from passlib.hash import cisco_asa

# hash password using specified username
hash = cisco_asa.hash("password", user="user")
print(hash)
# > 'A5XOy94YKDPXCo7U'

# verify correct password
print(cisco_asa.verify("password", hash, user="user"))
# > True

# verify correct password w/ wrong username
print(cisco_asa.verify("password", hash, user="other"))
# > False

# verify incorrect password
print(cisco_asa.verify("letmein", hash, user="user"))
# > False
```

The main "enable" password can be hashes / verified just by omitting
the ``user`` parameter, or setting ``user=""``:

```python
# hash password without associated user account
hash2 = cisco_asa.hash("password")
print(hash2)
# > 'NuLKvvWGg.x9HEKO'

# verify password without associated user account
print(cisco_asa.verify("password", hash2))
# > True
```

!!! tip
    See the generic *PasswordHash* usage examples.

## Interface

::: passlib.hash.cisco_pix

::: passlib.hash.cisco_asa

!!! note
    These hash algorithms have a context-sensitive peculiarity.
    They take in an optional username to salt the hash,
    but have specific restrictions...

    - The username *must* be provided in order to correctly hash passwords
      associated with a user account on the Cisco device.

    - Conversely, the username *must not* be provided (or must be set to `""`)
      in order to correctly hash passwords which don't have an associated user
      account (such as the "enable" password).

## Format & Algorithm

Cisco PIX & ASA hashes consist of a 12 byte digest, encoded as a 16 character
`HASH64 <passlib.utils.binary.h64>`-encoded string. An example
hash (of `"password"`, with user `""`) is `"NuLKvvWGg.x9HEKO"`.

The PIX / ASA digests are calculated as follows:

1. The password is encoded using ``UTF-8`` (though entering non-ASCII
   characters is subject to interface-specific issues, and may lead
   to problems such as double-encoding).

   If the result is greater than 16 bytes (for PIX), or 32 bytes (for ASA),
   the password is not allowed -- it will be rejected when set,
   and simplify not verify during authentication.

2. If the hash is associated with a user account,
   append the first four bytes of the user account name
   to the end of the password. If the hash is NOT associated
   with a user account (e.g. it's the "enable" password),
   this step should be omitted.

   If the user account is 1-3 bytes, it is repeated until all 4 bytes are filled
   up (e.g. "usr" becomes "usru").

   For `cisco_asa`,
   this step is omitted if the password is 28 bytes or more.

3. The password+user string is truncated, or right-padded with NULLs,
   until it's 16 bytes in size.

   For `cisco_asa`,
   if the password+user string is 16 or more bytes,
   a padding size of 32 is used instead.

4. Run the result of step 3 through MD5.

5. Discard every 4th byte of the 16-byte MD5 hash, starting
   with the 4th byte.

6. Encode the 12-byte result using `HASH64 <passlib.utils.binary.h64>`.

!!! warning
    Changed in 1.7.1: Updated to reflect current understanding of the algorithm.

## Security Issues

This algorithm is not suitable for *any* use besides manipulating existing
Cisco PIX hashes, due to the following flaws:

- Its use of the username as a salt value (and only the first four characters
  at that), means that common usernames (e.g. ``admin``, ``cisco``) will occur
  more frequently as salts, weakening the effectiveness of the salt in
  foiling pre-computed tables.

- Its truncation of the `password+user` combination to 16 characters
  additionally limits the keyspace, and the effectiveness of the username
  as a salt; making pre-computed and brute force attacks much more feasible.

- Since the keyspace of `password+user` is still a subset of ascii characters,
  existing MD5 lookup tables have an increased chance of being able to
  reverse common hashes.

- Its simplicity, and the weakness of MD5, makes high-speed brute force attacks
  much more feasible.

- Furthermore, it discards of 1/4 of MD5's already small 16 byte digest,
  making collisions much more likely.

## Deviations

This implementation tries to adhere to the canonical Cisco implementation,
but without an official specification, there may be other unknown deviations.
The following are known issues:

- Unicode Policy:

  ASA documentation [^charset] indicates it uses UTF-8 encoding,
  and Passlib does as well.  However, some ASA interfaces
  have issues such as: ASDM may double-encode unicode characters,
  and SSH connections may drop non-ASCII characters entirely.

- How usernames are added is not entirely pinned down.  Under ASA, 3-character
  usernames have their last character repeated to make a string of length 4.
  It is currently assumed that a similar repetition would be applied to
  usernames of 1-2 characters, and that this applies to PIX as well;
  though neither assumption has been confirmed.

- **Passlib 1.7.1 Bugfix**: Prior releases of Passlib had a number of issues
  with their implementation of the PIX & ASA algorithms.   As of 1.7.1,
  the reference vectors were greatly expanded, and then tested against
  an ASA 9.6 system.  This revealed a number of errors in passlib's implementation,
  which under the following conditions would create hashes that were
  unverifiable on a Cisco system:

    - PIX and ASA: Usernames containing 1-3 characters were not appended correctly (step 2, above).

    - ASA omits the user entirely (step 2, above) for passwords with >= 28 characters,
      not >= 27.  Non-enable passwords of exactly 27 characters were previous hashed
      incorrectly.

    - ASA's padding size decision (step 3, above) is made after the user
      has been appended, not before.  This caused prior releases to
      incorrectly hash non-enable passwords of length 13-15.

  Anyone relying on cisco_asa or cisco_pix should upgrade to Passlib 1.7.1 or newer
  to avoid these issues.

## References

- Description of PIX algorithm - <http://www.perlmonks.org/index.pl?node_id=797623>
- Message threads hinting at how username is handled - <http://www.openwall.com/lists/john-users/2010/02/02/7>, <www.freerainbowtables.com/phpBB3/viewtopic.php?f=2&t=1441>
- Partial description of ASA algorithm - <https://github.com/stekershaw/asa-password-encrypt/blob/master/README.md>

[^charset]: Character set used by ASA 8.4 - <http://www.cisco.com/c/en/us/td/docs/security/asa/asa84/configuration/guide/asa_84_cli_config/ref_cli.html#Supported_Character_Sets>
