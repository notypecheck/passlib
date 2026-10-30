# New Application Quickstart Guide

Need to quickly get password hash support added into your new application, but don't have time to wade through pages of documentation, comparing and contrasting all the different schemes? Then read on...

## Recommended hashes

If you'd like to set up a configuration that's right for your application, the first thing to do is choose a password hashing scheme. Passlib contains a large number of schemes, but most of them should only be used when a specific format is explicitly required.

!!! tip
    If you already know what hash algorithm(s) you want to use, skip to the next section: [Creating and Using a CryptContext](#creating-and-using-a-cryptcontext).

### The Options

There are currently four good choices[^choices] for secure hashing:

- `argon2`
- `bcrypt`
- `pbkdf2_sha256` / `pbkdf2_sha512`
- `sha256_crypt` / `sha512_crypt`

All four hashes share the following properties:

- No known vulnerabilities.
- Based on documented and widely reviewed algorithms.
- Public-domain or BSD-licensed reference implementations available.
- variable rounds for configuring flexible cpu cost on a per-hash basis.
- At least 96 bits of salt.
- Basic algorithm has seen heavy scrutiny and use for at least 10 years.
- In use across a number of OSes and/or a wide variety of applications.


### Detailed Comparison of Choices

#### Argon2

`argon2` is the newest of the four recommended hashes. It was selected as the winner of the [2013 Password Hashing Competition](https://password-hashing.net/), and draws on the design and lessons from BCrypt, PBKDF2, and SCrypt. Despite being much newer than the others, it has seen heavy scrutiny. Since the Argon2 project had the foresight to provide not just a reference implementation, but a standard hash encoding format, these hashes should be reliably interoperatable across all implementations.

*Issues:* In its default configuration, Argon2 uses more memory than the other hashes. However, this is one of its hallmarks as a "memory hard" hashing algorithm, and contributes to its security. Furthermore the exact amount used is configurable. Its only main drawback is that as of 2019-01-12, it's only 6 years old. It's seen only a few minor adjustments since 2013, but as it is just now gaining widespread use, the next few years are the period in which it will likely either prove itself, or be found wanting. It's for this reason, any cryptographic algorithm less than a decade old is generally considered "young". :)

#### BCrypt

`bcrypt` is [based](http://www.usenix.org/event/usenix99/provos/provos_html/) on the well-tested Blowfish cipher. In use since 1999, it's the default hash on all BSD variants. If you want your application's hashes to be readable by the native BSD crypt() function, this is the hash to use. There is also an alternative LDAP-formatted version (`ldap_bcrypt`) available.

*Issues:* Neither the original Blowfish, nor the modified version which BCrypt uses, have been NIST approved; this matter of concern is what motivated the development of SHA512-Crypt. As well, its rounds parameter is logarithmically scaled, making it hard to fine-tune the amount of time taken to verify passwords; which can be an issue for applications that handle a large number of simultaneous logon attempts (e.g. web apps). Finally, BCrypt only hashes the first 72 characters of a password, and will silently truncate longer ones (Passlib's non-standard `bcrypt_sha256` works around this last issue).

#### PBKDF2

`pbkdf2_sha512` is a custom hash format designed for Passlib. However, it directly uses the [PBKDF2](http://tools.ietf.org/html/rfc2898#section-5.2) key derivation function, which was standardized in 2000, and found across a [wide variety](http://en.wikipedia.org/wiki/PBKDF2#Systems_that_use_PBKDF2) of applications and platforms. Unlike the previous two hashes, PBKDF2 has a simple and portable design, which is resistant (but not immune) to collision and preimage attacks on the underlying message digest. There is also `pbkdf2_sha256`, which may be faster on 32 bit processors; as well as LDAP-formatted versions of these (`ldap_pbkdf2_sha512` and `ldap_pbkdf2_sha256`).

*Issues:* PBKDF2 has no major security or portability issues, and compares favorably against bcrypt. However, bcrypt has proven slightly more resistant to modern GPU-based cracking techniques.

#### SHA512-Crypt

`sha512_crypt` is based on the well-tested `md5_crypt` algorithm. In use since 2008, it's the default hash on most Linux systems; its direct ancestor `md5_crypt` has been in use since 1994 on most Unix systems. If you want your application's hashes to be readable by the native Linux crypt() function, this is the hash to use. There is also `sha256_crypt`, which may be faster on 32 bit processors; as well as LDAP-formatted versions of these (`ldap_sha512_crypt` and `ldap_sha256_crypt`).

*Issues:* Like `md5_crypt`, its algorithm composes the underlying message digest hash in a baroque and somewhat arbitrary set of combinations. So far this "kitchen sink" design has been successful in its primary purpose: to prevent any attempts to create an optimized version for use in a pre-computed or brute-force search. However, this design also hampers analysis of the algorithm for future flaws.

While this algorithm is still considered secure, it has fallen out of favor in comparison to bcrypt and pbkdf2, due to its non-standard construction.

Furthermore, when compared to Argon2 and BCrypt, SHA512-Crypt and PBKDF2 have proven more susceptible to cracking using modern GPU-based techniques.

`sha512_crypt` is probably the best choice for Google App Engine, as Google's production servers appear to provide native support via `crypt`, which will be used by Passlib.

!!! note
    References to this algorithm are frequently confused with a raw SHA-512 hash. While `sha512_crypt` uses the SHA-512 hash as a cryptographic primitive, the algorithm's resulting password hash is far more secure.

### Making a Decision

For new applications, this decision comes down to a couple of questions:

1. Does the hash need to be natively supported by your operating system's `crypt` api, in order to allow inter-operation with third-party applications on the host?

   - If yes, the right choice is either `bcrypt` for BSD variants, or `sha512_crypt` for Linux; since these are natively supported.
   - If no, continue...

2. Does your hosting provider allow you to install C extensions?

   - If no, you probably want to use `pbkdf2_sha256`, as this currently has the fastest pure-python backend.
   - If they allow C extensions, continue...

3. Do you want to use the latest and greatest, and don't mind increased memory usage when hashing?

   - `argon2` is a next-generation hashing algorithm, attempting to become the new standard. Its design has been being slightly tweaked since 2013, but will quite likely become *the* standard in the next few years. You'll need to install the [`argon2_cffi`](https://pypi.python.org/pypi/argon2_cffi) support library.
   - If you want something secure, but more battle tested, continue...

4. The top choices left are `bcrypt` and `pbkdf2_sha256`.

   Both have advantages, and their respective rough edges; though currently the balance is in favor of bcrypt (pbkdf2 can be cracked somewhat more efficiently).

   - If choosing bcrypt, we strongly recommend installing the [`bcrypt`](https://pypi.python.org/pypi/bcrypt) support library on non-BSD operating systems.

## Creating and Using a CryptContext

Once you've chosen what password hash(es) you want to use, the next step is to define a `CryptContext` object to manage your hashes and related policy configuration. Insert the following code into your application:

```python
from passlib.context import CryptContext

# Create a single instance for your app
pwd_context = CryptContext(
    # Replace this list with the hash(es) you wish to support.
    # this example sets argon2 as the default, with additional support for reading legacy des_crypt hashes.
    schemes=["argon2", "des_crypt"],
    # Automatically mark all but first hasher in list as deprecated.
    deprecated="auto",
)
```

To start using your CryptContext, import the context you created wherever it's needed:

```python
# import context from where you defined it...
from myapp.model.security import pwd_context

# hashing a password...
h = pwd_context.hash("somepass")
print(h)
# > '$argon2id$v=19$m=65536,t=3,p=4$2Ps/Z8yZc24NQQgBYMzZOw$pcKjXHtii/Lmm+5WzBy5OUn7PTfDPWxUOC3JS8fwrHg'

# verifying a password...
print(pwd_context.verify("somepass", h))
# > True
print(pwd_context.verify("wrongpass", h))
# > False
```

There's many more features packed into the context objects, read the walkthrough for more...

!!! tip
    - [Context Tutorial](context-tutorial.md) — full details of using the `CryptContext` class
    - `passlib.context` — CryptContext API reference
    - `passlib.hash` — list of all hashes supported by Passlib.

[^choices]: As of June 2016, the most commonly used password hashes are BCrypt and PBKDF2, followed by SHA512-Crypt, with Argon2 rapidly moving up the ranks. You should make sure you are reading a current copy of the Passlib documentation, in case the state of things has changed.
