# passlib.hash.cisco_asa - Cisco ASA MD5 hash

!!! danger
    **This algorithm is not considered secure by modern standards.** It should only be used when verifying existing hashes, or when interacting with applications that require this format. For new code, see the list of [recommended hashes](../guide/quickstart.md#recommended-hashes).

!!! warning
    **Caveat Emptor**
    Passlib's implementations of `cisco_pix` and `cisco_asa` both need verification.
    For those with access to Cisco PIX and ASA systems, verifying Passlib's reference vectors
    would be a great help (see [Issue #51](https://github.com/notypecheck/passlib/issues/51)). In the mean time, there are no guarantees
    that passlib correctly replicates the official implementation.

    Changed in 1.7.1: A number of bugs were fixed after expanding the reference vectors, and testing against an ASA 9.6 system.

The `cisco_asa` class provides support for Cisco ASA "encrypted" hash format.
This is a revision of the older `cisco_pix` hash;
and the usage and format is the same.

**See the** [cisco_pix](passlib.hash.cisco_pix.md) **documentation page**
for combined details of both these classes.
