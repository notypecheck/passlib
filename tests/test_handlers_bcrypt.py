import os
import warnings
from base64 import b64encode

import bcrypt
import pytest

from passlib import hash
from passlib.handlers.bcrypt import (
    IDENT_2,
    IDENT_2A,
    IDENT_2B,
    IDENT_2X,
    IDENT_2Y,
)
from passlib.utils import repeat_string, to_bytes
from tests.test_handlers import UPASS_TABLE
from tests.utils import TEST_MODE, HandlerCase
from tests.utils_ import no_warnings


class _bcrypt_test(HandlerCase):
    """base for BCrypt test cases"""

    handler = hash.bcrypt
    reduce_default_rounds = True
    fuzz_salts_need_bcrypt_repair = True

    known_correct_hashes = [
        #
        # from JTR 1.7.9
        #
        ("U*U*U*U*", "$2a$05$c92SVSfjeiCD6F2nAD6y0uBpJDjdRkt0EgeC4/31Rf2LUZbDRDE.O"),
        ("U*U***U", "$2a$05$WY62Xk2TXZ7EvVDQ5fmjNu7b0GEzSzUXUh2cllxJwhtOeMtWV3Ujq"),
        ("U*U***U*", "$2a$05$Fa0iKV3E2SYVUlMknirWU.CFYGvJ67UwVKI1E2FP6XeLiZGcH3MJi"),
        ("*U*U*U*U", "$2a$05$.WRrXibc1zPgIdRXYfv.4uu6TD1KWf0VnHzq/0imhUhuxSxCyeBs2"),
        ("", "$2a$05$Otz9agnajgrAe0.kFVF9V.tzaStZ2s1s4ZWi/LY4sw2k/MTVFj/IO"),
        #
        # test vectors from http://www.openwall.com/crypt v1.2
        # note that this omits any hashes that depend on crypt_blowfish's
        # various CVE-2011-2483 workarounds (hash 2a and \xff\xff in password,
        # and any 2x hashes); and only contain hashes which are correct
        # under both crypt_blowfish 1.2 AND OpenBSD.
        #
        ("U*U", "$2a$05$CCCCCCCCCCCCCCCCCCCCC.E5YPO9kmyuRGyh0XouQYb4YMJKvyOeW"),
        ("U*U*", "$2a$05$CCCCCCCCCCCCCCCCCCCCC.VGOzA784oUp/Z0DY336zx7pLYAy0lwK"),
        ("U*U*U", "$2a$05$XXXXXXXXXXXXXXXXXXXXXOAcXxm9kjPGEMsLznoKqmqw7tc8WCx4a"),
        ("", "$2a$05$CCCCCCCCCCCCCCCCCCCCC.7uG0VCzI2bS7j6ymqJi9CdcdxiRTWNy"),
        (
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789chars after 72 are ignored",
            "$2a$05$abcdefghijklmnopqrstuu5s2v8.iXieOjg/.AySBTTZIIVFJeBui",
        ),
        (b"\xa3", "$2a$05$/OK.fbVrR/bpIqNJ5ianF.Sa7shbm4.OzKpvFnX1pQLmQW96oUlCq"),
        (
            b"\xff\xa3345",
            "$2a$05$/OK.fbVrR/bpIqNJ5ianF.nRht2l/HRhr6zmCp9vYUvvsqynflf9e",
        ),
        (b"\xa3ab", "$2a$05$/OK.fbVrR/bpIqNJ5ianF.6IflQkJytoRVc1yuaNtHfiuq.FRlSIS"),
        (
            b"\xaa" * 72 + b"chars after 72 are ignored as usual",
            "$2a$05$/OK.fbVrR/bpIqNJ5ianF.swQOIzjOiJ9GHEPuhEkvqrUyvWhEMx6",
        ),
        (
            b"\xaa\x55" * 36,
            "$2a$05$/OK.fbVrR/bpIqNJ5ianF.R9xrDjiycxMbQE2bp.vgqlYpW5wx2yy",
        ),
        (
            b"\x55\xaa\xff" * 24,
            "$2a$05$/OK.fbVrR/bpIqNJ5ianF.9tQZzcJfm3uj2NvJ/n5xkhpqLrMpWCe",
        ),
        # keeping one of their 2y tests, because we are supporting that.
        (b"\xa3", "$2y$05$/OK.fbVrR/bpIqNJ5ianF.Sa7shbm4.OzKpvFnX1pQLmQW96oUlCq"),
        #
        # 8bit bug (fixed in 2y/2b)
        #
        # NOTE: see assert_lacks_8bit_bug() for origins of this test vector.
        (b"\xd1\x91", "$2y$05$6bNw2HLQYeqHYyBfLMsv/OUcZd0LKP39b87nBw3.S2tVZSqiQX6eu"),
        #
        # bsd wraparound bug (fixed in 2b)
        #
        # NOTE: if backend is vulnerable, password will hash the same as '0'*72
        #       ("$2a$04$R1lJ2gkNaoPGdafE.H.16.nVyh2niHsGJhayOHLMiXlI45o8/DU.6"),
        #       rather than same as ("0123456789"*8)[:72]
        # 255 should be sufficient, but checking
        (
            ("0123456789" * 26)[:254],
            "$2a$04$R1lJ2gkNaoPGdafE.H.16.1MKHPvmKwryeulRe225LKProWYwt9Oi",
        ),
        (
            ("0123456789" * 26)[:255],
            "$2a$04$R1lJ2gkNaoPGdafE.H.16.1MKHPvmKwryeulRe225LKProWYwt9Oi",
        ),
        (
            ("0123456789" * 26)[:256],
            "$2a$04$R1lJ2gkNaoPGdafE.H.16.1MKHPvmKwryeulRe225LKProWYwt9Oi",
        ),
        (
            ("0123456789" * 26)[:257],
            "$2a$04$R1lJ2gkNaoPGdafE.H.16.1MKHPvmKwryeulRe225LKProWYwt9Oi",
        ),
        #
        # from py-bcrypt tests
        #
        ("", "$2a$06$DCq7YPn5Rq63x1Lad4cll.TV4S6ytwfsfvkgY8jIucDrjc8deX1s."),
        ("a", "$2a$10$k87L/MF28Q673VKh8/cPi.SUl7MU/rWuSiIDDFayrKk/1tBsSQu4u"),
        ("abc", "$2a$10$WvvTPHKwdBJ3uk0Z37EMR.hLA2W6N9AEBhEgrAOljy2Ae5MtaSIUi"),
        (
            "abcdefghijklmnopqrstuvwxyz",
            "$2a$10$fVH8e28OQRj9tqiDXs1e1uxpsjN0c7II7YPKXua2NAKYvM6iQk7dq",
        ),
        (
            "~!@#$%^&*()      ~!@#$%^&*()PNBFRD",
            "$2a$10$LgfYWkbzEvQ4JakH7rOvHe0y8pHKF9OaFgwUZ2q7W2FFZmZzJYlfS",
        ),
        #
        # custom test vectors
        #
        # ensures utf-8 used for unicode
        (UPASS_TABLE, "$2a$05$Z17AXnnlpzddNUvnC6cZNOSwMA/8oNiKnHTHTwLlBijfucQQlHjaG"),
        # ensure 2b support
        (UPASS_TABLE, "$2b$05$Z17AXnnlpzddNUvnC6cZNOSwMA/8oNiKnHTHTwLlBijfucQQlHjaG"),
    ]

    if TEST_MODE("full"):
        #
        # add some extra tests related to 2/2a
        #
        CONFIG_2 = "$2$05$" + "." * 22
        CONFIG_A = "$2a$05$" + "." * 22
        known_correct_hashes.extend(
            [
                ("", CONFIG_2 + "J2ihDv8vVf7QZ9BsaRrKyqs2tkn55Yq"),
                ("", CONFIG_A + "J2ihDv8vVf7QZ9BsaRrKyqs2tkn55Yq"),
                ("abc", CONFIG_2 + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
                ("abc", CONFIG_A + "ev6gDwpVye3oMCUpLY85aTpfBNHD0Ga"),
                ("abc" * 23, CONFIG_2 + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
                ("abc" * 23, CONFIG_A + "2kIdfSj/4/R/Q6n847VTvc68BXiRYZC"),
                ("abc" * 24, CONFIG_2 + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
                ("abc" * 24, CONFIG_A + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
                ("abc" * 24 + "x", CONFIG_2 + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
                ("abc" * 24 + "x", CONFIG_A + "XuQjdH.wPVNUZ/bOfstdW/FqB8QSjte"),
            ]
        )

    known_correct_configs = [
        (
            "$2a$04$uM6csdM8R9SXTex/gbTaye",
            UPASS_TABLE,
            "$2a$04$uM6csdM8R9SXTex/gbTayezuvzFEufYGd2uB6of7qScLjQ4GwcD4G",
        ),
    ]

    known_unidentified_hashes = [
        # invalid minor version
        "$2f$12$EXRkfkdmXnagzds2SSitu.MW9.gAVqa9eLS1//RYtYCmB1eLHg.9q",
        "$2`$12$EXRkfkdmXnagzds2SSitu.MW9.gAVqa9eLS1//RYtYCmB1eLHg.9q",
    ]

    known_malformed_hashes = [
        # bad char in otherwise correct hash
        #                 \/
        "$2a$12$EXRkfkdmXn!gzds2SSitu.MW9.gAVqa9eLS1//RYtYCmB1eLHg.9q",
        # unsupported (but recognized) minor version
        "$2x$12$EXRkfkdmXnagzds2SSitu.MW9.gAVqa9eLS1//RYtYCmB1eLHg.9q",
        # rounds not zero-padded (py-bcrypt rejects this, therefore so do we)
        "$2a$6$DCq7YPn5Rq63x1Lad4cll.TV4S6ytwfsfvkgY8jIucDrjc8deX1s.",
        # NOTE: salts with padding bits set are technically malformed,
        #      but we can reliably correct & issue a warning for that.
    ]

    platform_crypt_support = [
        ("freedbsd|openbsd|netbsd", True),
        ("darwin", False),
        ("linux", None),  # may be present via addon, e.g. debian's libpam-unix2
        ("solaris", None),  # depends on system policy
    ]

    def setUp(self):
        # ensure builtin is enabled for duration of test.
        if TEST_MODE("full") and self.backend == "builtin":
            key = "PASSLIB_BUILTIN_BCRYPT"
            orig = os.environ.get(key)
            if orig:
                self.addCleanup(os.environ.__setitem__, key, orig)
            else:
                self.addCleanup(os.environ.__delitem__, key)
            os.environ[key] = "true"

        super().setUp()

        # silence this warning, will come up a bunch during testing of old 2a hashes.
        warnings.filterwarnings(
            "ignore", ".*backend is vulnerable to the bsd wraparound bug.*"
        )

    def populate_settings(self, kwds):
        # builtin is still just way too slow.
        if self.backend == "builtin":
            kwds.setdefault("rounds", 4)
        super().populate_settings(kwds)

    fuzz_verifiers = HandlerCase.fuzz_verifiers + ("fuzz_verifier_bcrypt",)

    def fuzz_verifier_bcrypt(self):
        def check_bcrypt(secret, hash):
            """bcrypt"""
            secret = to_bytes(secret, self.FuzzHashGenerator.password_encoding)
            if hash.startswith(IDENT_2B):
                # bcrypt <1.1 lacks 2B support
                hash = IDENT_2A + hash[4:]
            elif hash.startswith(IDENT_2):
                # bcrypt doesn't support $2$ hashes; but we can fake it
                # using the $2a$ algorithm, by repeating the password until
                # it's 72 chars in length.
                hash = IDENT_2A + hash[3:]
                if secret:
                    secret = repeat_string(secret, 72)
            elif hash.startswith(IDENT_2Y) and bcrypt.__version__ == "3.0.0":
                hash = IDENT_2B + hash[4:]
            hash = to_bytes(hash)
            try:
                return bcrypt.hashpw(secret, hash) == hash
            except ValueError:
                raise ValueError(f"bcrypt rejected hash: {hash!r} (secret={secret!r})")

        return check_bcrypt

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        def generate(self):
            opts = super(_bcrypt_test.FuzzHashGenerator, self).generate()

            secret = opts["secret"]
            other = opts["other"]
            settings = opts["settings"]
            ident = settings.get("ident")

            if ident == IDENT_2X:
                # 2x is just recognized, not supported. don't test with it.
                del settings["ident"]

            elif (
                ident == IDENT_2
                and other
                and repeat_string(to_bytes(other), len(to_bytes(secret)))
                == to_bytes(secret)
            ):
                # avoid false failure due to flaw in 0-revision bcrypt:
                # repeated strings like 'abc' and 'abcabc' hash identically.
                opts["secret"], opts["other"] = self.random_password_pair()

            return opts

        def random_rounds(self):
            # decrease default rounds for fuzz testing to speed up volume.
            return self.randintgauss(5, 8, 6, 1)

    known_incorrect_padding = [
        # password, bad hash, good hash
        # 2 bits of salt padding set
        #        ("loppux",                  # \/
        #         "$2a$12$oaQbBqq8JnSM1NHRPQGXORm4GCUMqp7meTnkft4zgSnrbhoKdDV0C",
        #         "$2a$12$oaQbBqq8JnSM1NHRPQGXOOm4GCUMqp7meTnkft4zgSnrbhoKdDV0C"),
        (
            "test",  # \/
            "$2a$04$oaQbBqq8JnSM1NHRPQGXORY4Vw3bdHKLIXTecPDRAcJ98cz1ilveO",
            "$2a$04$oaQbBqq8JnSM1NHRPQGXOOY4Vw3bdHKLIXTecPDRAcJ98cz1ilveO",
        ),
        # all 4 bits of salt padding set
        #        ("Passlib11",               # \/
        #         "$2a$12$M8mKpW9a2vZ7PYhq/8eJVcUtKxpo6j0zAezu0G/HAMYgMkhPu4fLK",
        #         "$2a$12$M8mKpW9a2vZ7PYhq/8eJVOUtKxpo6j0zAezu0G/HAMYgMkhPu4fLK"),
        (
            "test",  # \/
            "$2a$04$yjDgE74RJkeqC0/1NheSScrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIS",
            "$2a$04$yjDgE74RJkeqC0/1NheSSOrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIS",
        ),
        # bad checksum padding
        (
            "test",  # \/
            "$2a$04$yjDgE74RJkeqC0/1NheSSOrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIV",
            "$2a$04$yjDgE74RJkeqC0/1NheSSOrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIS",
        ),
    ]

    def test_90_bcrypt_padding(self):
        """test passlib correctly handles bcrypt padding bits"""
        self.require_TEST_MODE("full")
        #
        # prevents reccurrence of issue 25 (https://code.google.com/p/passlib/issues/detail?id=25)
        # were some unused bits were incorrectly set in bcrypt salt strings.
        # (fixed since 1.5.3)
        #
        bcrypt = self.handler
        corr_desc = ".*incorrectly set padding bits"

        #
        # test hash() / genconfig() don't generate invalid salts anymore
        #
        def check_padding(hash):
            malformed_hash_msg = f"unexpectedly malformed hash: {hash!r}"
            assert hash.startswith(("$2a$", "$2b$")), malformed_hash_msg
            assert len(hash) >= 28, malformed_hash_msg
            assert hash[28] in ".Oeu", f"unused bits incorrectly set in hash: {hash!r}"

        for i in range(6):
            check_padding(bcrypt.genconfig())
        for i in range(3):
            check_padding(bcrypt.using(rounds=bcrypt.min_rounds).hash("bob"))

        #
        # test genconfig() corrects invalid salts & issues warning.
        #
        with pytest.warns(match=corr_desc), pytest.warns(match="salt too large"):
            hash = bcrypt.genconfig(salt="." * 21 + "A.", rounds=5, relaxed=True)
        assert hash == "$2b$05$" + "." * (22 + 31)

        #
        # test public methods against good & bad hashes
        #
        samples = self.known_incorrect_padding
        for pwd, bad, good in samples:
            # make sure genhash() corrects bad configs, leaves good unchanged
            with pytest.warns(match=corr_desc):
                assert bcrypt.genhash(pwd, bad) == good
            with no_warnings():
                assert bcrypt.genhash(pwd, good) == good

            # make sure verify() works correctly with good & bad hashes
            with pytest.warns(match=corr_desc):
                assert bcrypt.verify(pwd, bad)
            with no_warnings():
                assert bcrypt.verify(pwd, good)

            # make sure normhash() corrects bad hashes, leaves good unchanged
            with pytest.warns(match=corr_desc):
                assert bcrypt.normhash(bad) == good
            with no_warnings():
                assert bcrypt.normhash(good) == good

        # make sure normhash() leaves non-bcrypt hashes alone
        assert bcrypt.normhash("$md5$abc") == "$md5$abc"

    def test_needs_update_w_padding(self):
        """needs_update corrects bcrypt padding"""
        # NOTE: see padding test above for details about issue this detects
        bcrypt = self.handler.using(rounds=4)

        # PASS1 = "test"
        # bad contains invalid 'c' char at end of salt:
        #                                    \/
        BAD1 = "$2a$04$yjDgE74RJkeqC0/1NheSScrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIS"
        GOOD1 = "$2a$04$yjDgE74RJkeqC0/1NheSSOrvKeu9IbKDpcQf/Ox3qsrRS/Kw42qIS"

        assert bcrypt.needs_update(BAD1)
        assert not bcrypt.needs_update(GOOD1)


# create test cases for specific backends
bcrypt_bcrypt_test = _bcrypt_test.create_backend_case("bcrypt")


class _bcrypt_sha256_test(HandlerCase):
    "base for BCrypt-SHA256 test cases"

    handler = hash.bcrypt_sha256
    reduce_default_rounds = True
    forbidden_characters = None
    fuzz_salts_need_bcrypt_repair = True

    known_correct_hashes = [
        # -------------------------------------------------------------------
        # custom test vectors for old v1 format
        # -------------------------------------------------------------------
        # empty
        (
            "",
            "$bcrypt-sha256$2a,5$E/e/2AOhqM5W/KJTFQzLce$F6dYSxOdAEoJZO2eoHUZWZljW/e0TXO",
        ),
        # ascii
        (
            "password",
            "$bcrypt-sha256$2a,5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        ),
        # unicode / utf8
        (
            UPASS_TABLE,
            "$bcrypt-sha256$2a,5$.US1fQ4TQS.ZTz/uJ5Kyn.$QNdPDOTKKT5/sovNz1iWg26quOU4Pje",
        ),
        (
            UPASS_TABLE.encode("utf-8"),
            "$bcrypt-sha256$2a,5$.US1fQ4TQS.ZTz/uJ5Kyn.$QNdPDOTKKT5/sovNz1iWg26quOU4Pje",
        ),
        # ensure 2b support
        (
            "password",
            "$bcrypt-sha256$2b,5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        ),
        (
            UPASS_TABLE,
            "$bcrypt-sha256$2b,5$.US1fQ4TQS.ZTz/uJ5Kyn.$QNdPDOTKKT5/sovNz1iWg26quOU4Pje",
        ),
        # test >72 chars is hashed correctly -- under bcrypt these hash the same.
        # NOTE: test_60_truncate_size() handles this already, this is just for overkill :)
        (
            repeat_string("abc123", 72),
            "$bcrypt-sha256$2b,5$X1g1nh3g0v4h6970O68cxe$r/hyEtqJ0teqPEmfTLoZ83ciAI1Q74.",
        ),
        (
            repeat_string("abc123", 72) + "qwr",
            "$bcrypt-sha256$2b,5$X1g1nh3g0v4h6970O68cxe$021KLEif6epjot5yoxk0m8I0929ohEa",
        ),
        (
            repeat_string("abc123", 72) + "xyz",
            "$bcrypt-sha256$2b,5$X1g1nh3g0v4h6970O68cxe$7.1kgpHduMGEjvM3fX6e/QCvfn6OKja",
        ),
        # -------------------------------------------------------------------
        # custom test vectors for v2 format
        # TODO: convert to v2 format
        # -------------------------------------------------------------------
        # empty
        (
            "",
            "$bcrypt-sha256$v=2,t=2b,r=5$E/e/2AOhqM5W/KJTFQzLce$WFPIZKtDDTriqWwlmRFfHiOTeheAZWe",
        ),
        # ascii
        (
            "password",
            "$bcrypt-sha256$v=2,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe$wOK1VFFtS8IGTrGa7.h5fs0u84qyPbS",
        ),
        # unicode / utf8
        (
            UPASS_TABLE,
            "$bcrypt-sha256$v=2,t=2b,r=5$.US1fQ4TQS.ZTz/uJ5Kyn.$pzzgp40k8reM1CuQb03PvE0IDPQSdV6",
        ),
        (
            UPASS_TABLE.encode("utf-8"),
            "$bcrypt-sha256$v=2,t=2b,r=5$.US1fQ4TQS.ZTz/uJ5Kyn.$pzzgp40k8reM1CuQb03PvE0IDPQSdV6",
        ),
        # test >72 chars is hashed correctly -- under bcrypt these hash the same.
        # NOTE: test_60_truncate_size() handles this already, this is just for overkill :)
        (
            repeat_string("abc123", 72),
            "$bcrypt-sha256$v=2,t=2b,r=5$X1g1nh3g0v4h6970O68cxe$zu1cloESVFIOsUIo7fCEgkdHaI9SSue",
        ),
        (
            repeat_string("abc123", 72) + "qwr",
            "$bcrypt-sha256$v=2,t=2b,r=5$X1g1nh3g0v4h6970O68cxe$CBF9csfEdW68xv3DwE6xSULXMtqEFP.",
        ),
        (
            repeat_string("abc123", 72) + "xyz",
            "$bcrypt-sha256$v=2,t=2b,r=5$X1g1nh3g0v4h6970O68cxe$zC/1UDUG2ofEXB6Onr2vvyFzfhEOS3S",
        ),
    ]

    known_correct_configs = [
        # v1
        (
            "$bcrypt-sha256$2a,5$5Hg1DKFqPE8C2aflZ5vVoe",
            "password",
            "$bcrypt-sha256$2a,5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        ),
        # v2
        (
            "$bcrypt-sha256$v=2,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe",
            "password",
            "$bcrypt-sha256$v=2,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe$wOK1VFFtS8IGTrGa7.h5fs0u84qyPbS",
        ),
    ]

    known_malformed_hashes = [
        # -------------------------------------------------------------------
        # v1 format
        # -------------------------------------------------------------------
        # bad char in otherwise correct hash
        #                           \/
        "$bcrypt-sha256$2a,5$5Hg1DKF!PE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unrecognized bcrypt variant
        "$bcrypt-sha256$2c,5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unsupported bcrypt variant
        "$bcrypt-sha256$2x,5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # rounds zero-padded
        "$bcrypt-sha256$2a,05$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # config string w/ $ added
        "$bcrypt-sha256$2a,5$5Hg1DKFqPE8C2aflZ5vVoe$",
        # -------------------------------------------------------------------
        # v2 format
        # -------------------------------------------------------------------
        # bad char in otherwise correct hash
        #                                   \/
        "$bcrypt-sha256$v=2,t=2b,r=5$5Hg1DKF!PE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unsupported version (for this format)
        "$bcrypt-sha256$v=1,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unrecognized version
        "$bcrypt-sha256$v=3,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unrecognized bcrypt variant
        "$bcrypt-sha256$v=2,t=2c,r=5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # unsupported bcrypt variant
        "$bcrypt-sha256$v=2,t=2a,r=5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        "$bcrypt-sha256$v=2,t=2x,r=5$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # rounds zero-padded
        "$bcrypt-sha256$v=2,t=2b,r=05$5Hg1DKFqPE8C2aflZ5vVoe$12BjNE0p7axMg55.Y/mHsYiVuFBDQyu",
        # config string w/ $ added
        "$bcrypt-sha256$v=2,t=2b,r=5$5Hg1DKFqPE8C2aflZ5vVoe$",
    ]

    def setUp(self):
        # ensure builtin is enabled for duration of test.
        if TEST_MODE("full") and self.backend == "builtin":
            key = "PASSLIB_BUILTIN_BCRYPT"
            orig = os.environ.get(key)
            if orig:
                self.addCleanup(os.environ.__setitem__, key, orig)
            else:
                self.addCleanup(os.environ.__delitem__, key)
            os.environ[key] = "enabled"
        super().setUp()
        warnings.filterwarnings(
            "ignore", ".*backend is vulnerable to the bsd wraparound bug.*"
        )

    def populate_settings(self, kwds):
        # builtin is still just way too slow.
        if self.backend == "builtin":
            kwds.setdefault("rounds", 4)
        super().populate_settings(kwds)

    def require_many_idents(self):
        raise self.skipTest("multiple idents not supported")

    def test_30_HasOneIdent(self):
        # forbidding ident keyword, we only support "2b" for now
        handler = self.handler
        handler(use_defaults=True)
        with pytest.raises(ValueError):
            handler(ident="$2y$", use_defaults=True)

    class FuzzHashGenerator(HandlerCase.FuzzHashGenerator):
        def random_rounds(self):
            # decrease default rounds for fuzz testing to speed up volume.
            return self.randintgauss(5, 8, 6, 1)

        def random_ident(self):
            return "2b"

    def test_using_version(self):
        # default to v2
        handler = self.handler
        assert handler.version == 2

        # allow v1 explicitly
        subcls = handler.using(version=1)
        assert subcls.version == 1

        # forbid unknown ver
        with pytest.raises(ValueError):
            handler.using(version=999)

        # allow '2a' only for v1
        subcls = handler.using(version=1, ident="2a")
        with pytest.raises(ValueError):
            handler.using(ident="2a")

    def test_calc_digest_v2(self):
        """
        test digest calc v2 matches bcrypt()
        """
        from passlib.crypto.digest import compile_hmac
        from passlib.hash import bcrypt

        # manually calc intermediary digest
        salt = "nyKYxTAvjmy6lMDYMl11Uu"
        secret = "test"
        temp_digest = compile_hmac("sha256", salt.encode("ascii"))(
            secret.encode("ascii")
        )
        temp_digest = b64encode(temp_digest).decode("ascii")
        assert temp_digest == "J5TlyIDm+IcSWmKiDJm+MeICndBkFVPn4kKdJW8f+xY="

        # manually final hash from intermediary
        # XXX: genhash() could be useful here
        bcrypt_digest = bcrypt(ident="2b", salt=salt, rounds=12)._calc_checksum(
            temp_digest
        )
        assert bcrypt_digest == "M0wE0Ov/9LXoQFCe.jRHu3MSHPF54Ta"
        assert bcrypt.verify(temp_digest, "$2b$12$" + salt + bcrypt_digest)

        # confirm handler outputs same thing.
        # XXX: genhash() could be useful here
        result = self.handler(ident="2b", salt=salt, rounds=12)._calc_checksum(secret)
        assert result == bcrypt_digest


# create test cases for specific backends
bcrypt_sha256_bcrypt_test = _bcrypt_sha256_test.create_backend_case("bcrypt")
