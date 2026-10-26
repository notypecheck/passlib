import pytest

from passlib import exc, hash

from .test_handlers import UPASS_TABLE
from .utils import HandlerCase, UserHandlerMixin, repeat_string

#: IOS XE hashes only the first 127 bytes of longer type 8 and 9 passwords
_LONG = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * 3

# module
__all__ = [
    "cisco_pix_test",
    "cisco_asa_test",
    "cisco_type7_test",
    "cisco_type8_test",
    "cisco_type9_test",
]


class _PixAsaSharedTest(UserHandlerMixin, HandlerCase):
    """
    class w/ shared info for PIX & ASA tests.
    """

    __unittest_skip = True  # for TestCase
    requires_user = False  # for UserHandlerMixin

    #: shared list of hashes which should be identical under pix & asa7
    #: (i.e. combined secret + user < 17 bytes)
    pix_asa_shared_hashes = [
        #
        # http://www.perlmonks.org/index.pl?node_id=797623
        #
        (("cisco", ""), "2KFQnbNIdI.2KYOU"),  # confirmed ASA 9.6
        #
        # http://www.hsc.fr/ressources/breves/pix_crack.html.en
        #
        (("hsc", ""), "YtT8/k6Np8F1yz2c"),  # confirmed ASA 9.6
        #
        # www.freerainbowtables.com/phpBB3/viewtopic.php?f=2&t=1441
        #
        (("", ""), "8Ry2YjIyt7RRXU24"),  # confirmed ASA 9.6
        (("cisco", "john"), "hN7LzeyYjw12FSIU"),
        (("cisco", "jack"), "7DrfeZ7cyOj/PslD"),
        #
        # http://comments.gmane.org/gmane.comp.security.openwall.john.user/2529
        #
        (("ripper", "alex"), "h3mJrcH0901pqX/m"),
        (("cisco", "cisco"), "3USUcOPFUiMCO4Jk"),
        (("cisco", "cisco1"), "3USUcOPFUiMCO4Jk"),
        (("CscFw-ITC!", "admcom"), "lZt7HSIXw3.QP7.R"),
        ("cangetin", "TynyB./ftknE77QP"),
        (("cangetin", "rramsey"), "jgBZqYtsWfGcUKDi"),
        #
        # http://openwall.info/wiki/john/sample-hashes
        #
        (("phonehome", "rharris"), "zyIIMSYjiPm0L7a6"),
        #
        # http://www.openwall.com/lists/john-users/2010/08/08/3
        #
        (("cangetin", ""), "TynyB./ftknE77QP"),
        (("cangetin", "rramsey"), "jgBZqYtsWfGcUKDi"),
        #
        # from JTR 1.7.9
        #
        ("test1", "TRPEas6f/aa6JSPL"),
        ("test2", "OMT6mXmAvGyzrCtp"),
        ("test3", "gTC7RIy1XJzagmLm"),
        ("test4", "oWC1WRwqlBlbpf/O"),
        ("password", "NuLKvvWGg.x9HEKO"),
        ("0123456789abcdef", ".7nfVBEIEu4KbF/1"),
        #
        # http://www.cisco.com/en/US/docs/security/pix/pix50/configuration/guide/commands.html#wp5472
        #
        (("1234567890123456", ""), "feCkwUGktTCAgIbD"),  # canonical source
        (("watag00s1am", ""), "jMorNbK0514fadBh"),  # canonical source
        #
        # custom
        #
        (("cisco1", "cisco1"), "jmINXNH6p1BxUppp"),
        # ensures utf-8 used for unicode
        (UPASS_TABLE, "CaiIvkLMu2TOHXGT"),
        #
        # passlib reference vectors
        #
        # Some of these have been confirmed on various ASA firewalls,
        # and the exact version is noted next to each hash.
        # Would like to verify these under more PIX & ASA versions.
        #
        # Those without a note are generally an extrapolation,
        # to ensure the code stays consistent, but for various reasons,
        # hasn't been verified.
        #
        # * One such case is usernames w/ 1 & 2 digits --
        #   ASA (9.6 at least) requires 3+ digits in username.
        #
        # The following hashes (below 13 chars) should be identical for PIX/ASA.
        # Ones which differ are listed separately in the known_correct_hashes
        # list for the two test classes.
        #
        # 4 char password
        (("1234", ""), "RLPMUQ26KL4blgFN"),  # confirmed ASA 9.6
        # 8 char password
        (("01234567", ""), "0T52THgnYdV1tlOF"),  # confirmed ASA 9.6
        (("01234567", "3"), ".z0dT9Alkdc7EIGS"),
        (("01234567", "36"), "CC3Lam53t/mHhoE7"),
        (("01234567", "365"), "8xPrWpNnBdD2DzdZ"),  # confirmed ASA 9.6
        (("01234567", "3333"), ".z0dT9Alkdc7EIGS"),  # confirmed ASA 9.6
        (("01234567", "3636"), "CC3Lam53t/mHhoE7"),  # confirmed ASA 9.6
        (("01234567", "3653"), "8xPrWpNnBdD2DzdZ"),  # confirmed ASA 9.6
        (("01234567", "adm"), "dfWs2qiao6KD/P2L"),  # confirmed ASA 9.6
        (("01234567", "adma"), "dfWs2qiao6KD/P2L"),  # confirmed ASA 9.6
        (("01234567", "admad"), "dfWs2qiao6KD/P2L"),  # confirmed ASA 9.6
        (("01234567", "user"), "PNZ4ycbbZ0jp1.j1"),  # confirmed ASA 9.6
        (("01234567", "user1234"), "PNZ4ycbbZ0jp1.j1"),  # confirmed ASA 9.6
        # 12 char password
        (("0123456789ab", ""), "S31BxZOGlAigndcJ"),  # confirmed ASA 9.6
        (("0123456789ab", "36"), "wFqSX91X5.YaRKsi"),
        (("0123456789ab", "365"), "qjgo3kNgTVxExbno"),  # confirmed ASA 9.6
        (("0123456789ab", "3333"), "mcXPL/vIZcIxLUQs"),  # confirmed ASA 9.6
        (("0123456789ab", "3636"), "wFqSX91X5.YaRKsi"),  # confirmed ASA 9.6
        (("0123456789ab", "3653"), "qjgo3kNgTVxExbno"),  # confirmed ASA 9.6
        (("0123456789ab", "user"), "f.T4BKdzdNkjxQl7"),  # confirmed ASA 9.6
        (("0123456789ab", "user1234"), "f.T4BKdzdNkjxQl7"),  # confirmed ASA 9.6
        # NOTE: remaining reference vectors for 13+ char passwords
        # are split up between cisco_pix & cisco_asa tests.
        # unicode passwords
        # ASA supposedly uses utf-8 encoding, but entering non-ascii
        # chars is error-prone, and while UTF-8 appears to be intended,
        # observed behaviors include:
        # * ssh cli stripping non-ascii chars entirely
        # * ASDM web iface double-encoding utf-8 strings
        (("t\xe1ble".encode(), "user"), "Og8fB4NyF0m5Ed9c"),
        (
            ("t\xe1ble".encode().decode("latin-1").encode("utf-8"), "user"),
            "cMvFC2XVBmK/68yB",
        ),  # confirmed ASA 9.6 when typed into ASDM
    ]

    def test_calc_digest_spoiler(self):
        """
        _calc_checksum() -- spoil oversize passwords during verify

        for details, see 'spoil_digest' flag instead that function.
        this helps cisco_pix/cisco_asa implement their policy of
        ``.truncate_verify_reject=True``.
        """

        def calc(secret, for_hash=False):
            return self.handler(use_defaults=for_hash)._calc_checksum(secret)

        # short (non-truncated) password
        short_secret = repeat_string("1234", self.handler.truncate_size)
        short_hash = calc(short_secret)

        # longer password should have totally different hash,
        # to prevent verify from matching (i.e. "spoiled").
        long_secret = short_secret + "X"
        long_hash = calc(long_secret)
        assert long_hash != short_hash

        # spoiled hash should depend on whole secret,
        # so that output isn't predictable
        alt_long_secret = short_secret + "Y"
        alt_long_hash = calc(alt_long_secret)
        assert alt_long_hash != short_hash
        assert alt_long_hash != long_hash

        # for hash(), should throw error if password too large
        calc(short_secret, for_hash=True)
        with pytest.raises(exc.PasswordSizeError):
            calc(long_secret, for_hash=True)
        with pytest.raises(exc.PasswordSizeError):
            calc(alt_long_secret, for_hash=True)


class cisco_pix_test(_PixAsaSharedTest):
    handler = hash.cisco_pix

    #: known correct pix hashes
    known_correct_hashes = _PixAsaSharedTest.pix_asa_shared_hashes + [
        #
        # passlib reference vectors (PIX-specific)
        #
        # NOTE: See 'pix_asa_shared_hashes' for general PIX+ASA vectors,
        #       and general notes about the 'passlib reference vectors' test set.
        #
        #       All of the following are PIX-specific, as ASA starts
        #       to use a different padding size at 13 characters.
        #
        # TODO: these need confirming w/ an actual PIX system.
        #
        # 13 char password
        (("0123456789abc", ""), "eacOpB7vE7ZDukSF"),
        (("0123456789abc", "3"), "ylJTd/qei66WZe3w"),
        (("0123456789abc", "36"), "hDx8QRlUhwd6bU8N"),
        (("0123456789abc", "365"), "vYOOtnkh1HXcMrM7"),
        (("0123456789abc", "3333"), "ylJTd/qei66WZe3w"),
        (("0123456789abc", "3636"), "hDx8QRlUhwd6bU8N"),
        (("0123456789abc", "3653"), "vYOOtnkh1HXcMrM7"),
        (("0123456789abc", "user"), "f4/.SALxqDo59mfV"),
        (("0123456789abc", "user1234"), "f4/.SALxqDo59mfV"),
        # 14 char password
        (("0123456789abcd", ""), "6r8888iMxEoPdLp4"),
        (("0123456789abcd", "3"), "f5lvmqWYj9gJqkIH"),
        (("0123456789abcd", "36"), "OJJ1Khg5HeAYBH1c"),
        (("0123456789abcd", "365"), "OJJ1Khg5HeAYBH1c"),
        (("0123456789abcd", "3333"), "f5lvmqWYj9gJqkIH"),
        (("0123456789abcd", "3636"), "OJJ1Khg5HeAYBH1c"),
        (("0123456789abcd", "3653"), "OJJ1Khg5HeAYBH1c"),
        (("0123456789abcd", "adm"), "DbPLCFIkHc2SiyDk"),
        (("0123456789abcd", "adma"), "DbPLCFIkHc2SiyDk"),
        (("0123456789abcd", "user"), "WfO2UiTapPkF/FSn"),
        (("0123456789abcd", "user1234"), "WfO2UiTapPkF/FSn"),
        # 15 char password
        (("0123456789abcde", ""), "al1e0XFIugTYLai3"),
        (("0123456789abcde", "3"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "36"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "365"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "3333"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "3636"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "3653"), "lYbwBu.f82OIApQB"),
        (("0123456789abcde", "adm"), "KgKx1UQvdR/09i9u"),
        (("0123456789abcde", "adma"), "KgKx1UQvdR/09i9u"),
        (("0123456789abcde", "user"), "qLopkenJ4WBqxaZN"),
        (("0123456789abcde", "user1234"), "qLopkenJ4WBqxaZN"),
        # 16 char password
        (("0123456789abcdef", ""), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "36"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "365"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "3333"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "3636"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "3653"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "user"), ".7nfVBEIEu4KbF/1"),
        (("0123456789abcdef", "user1234"), ".7nfVBEIEu4KbF/1"),
    ]


class cisco_asa_test(_PixAsaSharedTest):
    handler = hash.cisco_asa

    known_correct_hashes = _PixAsaSharedTest.pix_asa_shared_hashes + [
        #
        # passlib reference vectors (ASA-specific)
        #
        # NOTE: See 'pix_asa_shared_hashes' for general PIX+ASA vectors,
        #       and general notes about the 'passlib reference vectors' test set.
        #
        # 13 char password
        # NOTE: past this point, ASA pads to 32 bytes instead of 16
        #       for all cases where user is set (secret + 4 bytes > 16),
        #       but still uses 16 bytes for enable pwds (secret <= 16).
        #       hashes w/ user WON'T match PIX, but "enable" passwords will.
        (("0123456789abc", ""), "eacOpB7vE7ZDukSF"),  # confirmed ASA 9.6
        (("0123456789abc", "36"), "FRV9JG18UBEgX0.O"),
        (("0123456789abc", "365"), "NIwkusG9hmmMy6ZQ"),  # confirmed ASA 9.6
        (("0123456789abc", "3333"), "NmrkP98nT7RAeKZz"),  # confirmed ASA 9.6
        (("0123456789abc", "3636"), "FRV9JG18UBEgX0.O"),  # confirmed ASA 9.6
        (("0123456789abc", "3653"), "NIwkusG9hmmMy6ZQ"),  # confirmed ASA 9.6
        (("0123456789abc", "user"), "8Q/FZeam5ai1A47p"),  # confirmed ASA 9.6
        (("0123456789abc", "user1234"), "8Q/FZeam5ai1A47p"),  # confirmed ASA 9.6
        # 14 char password
        (("0123456789abcd", ""), "6r8888iMxEoPdLp4"),  # confirmed ASA 9.6
        (("0123456789abcd", "3"), "yxGoujXKPduTVaYB"),
        (("0123456789abcd", "36"), "W0jckhnhjnr/DiT/"),
        (("0123456789abcd", "365"), "HuVOxfMQNahaoF8u"),  # confirmed ASA 9.6
        (("0123456789abcd", "3333"), "yxGoujXKPduTVaYB"),  # confirmed ASA 9.6
        (("0123456789abcd", "3636"), "W0jckhnhjnr/DiT/"),  # confirmed ASA 9.6
        (("0123456789abcd", "3653"), "HuVOxfMQNahaoF8u"),  # confirmed ASA 9.6
        (("0123456789abcd", "adm"), "RtOmSeoCs4AUdZqZ"),  # confirmed ASA 9.6
        (("0123456789abcd", "adma"), "RtOmSeoCs4AUdZqZ"),  # confirmed ASA 9.6
        (("0123456789abcd", "user"), "rrucwrcM0h25pr.m"),  # confirmed ASA 9.6
        (("0123456789abcd", "user1234"), "rrucwrcM0h25pr.m"),  # confirmed ASA 9.6
        # 15 char password
        (("0123456789abcde", ""), "al1e0XFIugTYLai3"),  # confirmed ASA 9.6
        (("0123456789abcde", "3"), "nAZrQoHaL.fgrIqt"),
        (("0123456789abcde", "36"), "2GxIQ6ICE795587X"),
        (("0123456789abcde", "365"), "QmDsGwCRBbtGEKqM"),  # confirmed ASA 9.6
        (("0123456789abcde", "3333"), "nAZrQoHaL.fgrIqt"),  # confirmed ASA 9.6
        (("0123456789abcde", "3636"), "2GxIQ6ICE795587X"),  # confirmed ASA 9.6
        (("0123456789abcde", "3653"), "QmDsGwCRBbtGEKqM"),  # confirmed ASA 9.6
        (("0123456789abcde", "adm"), "Aj2aP0d.nk62wl4m"),  # confirmed ASA 9.6
        (("0123456789abcde", "adma"), "Aj2aP0d.nk62wl4m"),  # confirmed ASA 9.6
        (("0123456789abcde", "user"), "etxiXfo.bINJcXI7"),  # confirmed ASA 9.6
        (("0123456789abcde", "user1234"), "etxiXfo.bINJcXI7"),  # confirmed ASA 9.6
        # 16 char password
        (("0123456789abcdef", ""), ".7nfVBEIEu4KbF/1"),  # confirmed ASA 9.6
        (("0123456789abcdef", "36"), "GhI8.yFSC5lwoafg"),
        (("0123456789abcdef", "365"), "KFBI6cNQauyY6h/G"),  # confirmed ASA 9.6
        (("0123456789abcdef", "3333"), "Ghdi1IlsswgYzzMH"),  # confirmed ASA 9.6
        (("0123456789abcdef", "3636"), "GhI8.yFSC5lwoafg"),  # confirmed ASA 9.6
        (("0123456789abcdef", "3653"), "KFBI6cNQauyY6h/G"),  # confirmed ASA 9.6
        (("0123456789abcdef", "user"), "IneB.wc9sfRzLPoh"),  # confirmed ASA 9.6
        (("0123456789abcdef", "user1234"), "IneB.wc9sfRzLPoh"),  # confirmed ASA 9.6
        # 17 char password
        # NOTE: past this point, ASA pads to 32 bytes instead of 16
        #       for ALL cases, since secret > 16 bytes even for enable pwds;
        #       and so none of these rest here should match PIX.
        (("0123456789abcdefq", ""), "bKshl.EN.X3CVFRQ"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "36"), "JAeTXHs0n30svlaG"),
        (("0123456789abcdefq", "365"), "4fKSSUBHT1ChGqHp"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "3333"), "USEJbxI6.VY4ecBP"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "3636"), "JAeTXHs0n30svlaG"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "3653"), "4fKSSUBHT1ChGqHp"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "user"), "/dwqyD7nGdwSrDwk"),  # confirmed ASA 9.6
        (("0123456789abcdefq", "user1234"), "/dwqyD7nGdwSrDwk"),  # confirmed ASA 9.6
        # 27 char password
        (("0123456789abcdefqwertyuiopa", ""), "4wp19zS3OCe.2jt5"),  # confirmed ASA 9.6
        (("0123456789abcdefqwertyuiopa", "36"), "PjUoGqWBKPyV9qOe"),
        (
            ("0123456789abcdefqwertyuiopa", "365"),
            "bfCy6xFAe5O/gzvM",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopa", "3333"),
            "rd/ZMuGTJFIb2BNG",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopa", "3636"),
            "PjUoGqWBKPyV9qOe",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopa", "3653"),
            "bfCy6xFAe5O/gzvM",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopa", "user"),
            "zynfWw3UtszxLMgL",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopa", "user1234"),
            "zynfWw3UtszxLMgL",
        ),  # confirmed ASA 9.6
        # 28 char password
        # NOTE: past this point, ASA stops appending the username AT ALL,
        #       even though there's still room for the first few chars.
        (("0123456789abcdefqwertyuiopas", ""), "W6nbOddI0SutTK7m"),  # confirmed ASA 9.6
        (("0123456789abcdefqwertyuiopas", "36"), "W6nbOddI0SutTK7m"),
        (
            ("0123456789abcdefqwertyuiopas", "365"),
            "W6nbOddI0SutTK7m",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopas", "user"),
            "W6nbOddI0SutTK7m",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopas", "user1234"),
            "W6nbOddI0SutTK7m",
        ),  # confirmed ASA 9.6
        # 32 char password
        # NOTE: this is max size that ASA allows, and throws error for larger
        (
            ("0123456789abcdefqwertyuiopasdfgh", ""),
            "5hPT/iC6DnoBxo6a",
        ),  # confirmed ASA 9.6
        (("0123456789abcdefqwertyuiopasdfgh", "36"), "5hPT/iC6DnoBxo6a"),
        (
            ("0123456789abcdefqwertyuiopasdfgh", "365"),
            "5hPT/iC6DnoBxo6a",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopasdfgh", "user"),
            "5hPT/iC6DnoBxo6a",
        ),  # confirmed ASA 9.6
        (
            ("0123456789abcdefqwertyuiopasdfgh", "user1234"),
            "5hPT/iC6DnoBxo6a",
        ),  # confirmed ASA 9.6
    ]


class cisco_type7_test(HandlerCase):
    handler = hash.cisco_type7
    salt_bits = 4
    salt_type = int

    known_correct_hashes = [
        #
        # http://mccltd.net/blog/?p=1034
        #
        ("secure ", "04480E051A33490E"),
        #
        # http://insecure.org/sploits/cisco.passwords.html
        #
        (
            "Its time to go to lunch!",
            "153B1F1F443E22292D73212D5300194315591954465A0D0B59",
        ),
        #
        # http://blog.ioshints.info/2007/11/type-7-decryption-in-cisco-ios.html
        #
        ("t35t:pa55w0rd", "08351F1B1D431516475E1B54382F"),
        #
        # http://www.m00nie.com/2011/09/cisco-type-7-password-decryption-and-encryption-with-perl/
        #
        ("hiImTesting:)", "020E0D7206320A325847071E5F5E"),
        #
        # http://packetlife.net/forums/thread/54/
        #
        ("cisco123", "060506324F41584B56"),
        ("cisco123", "1511021F07257A767B"),
        #
        # source ?
        #
        ("Supe&8ZUbeRp4SS", "06351A3149085123301517391C501918"),
        #
        # custom
        #
        # ensures utf-8 used for unicode
        (UPASS_TABLE, "0958EDC8A9F495F6F8A5FD"),
    ]

    known_unidentified_hashes = [
        # salt with hex value
        "0A480E051A33490E",
        # salt value > 52. this may in fact be valid, but we reject it for now
        # (see docs for more).
        "99400E4812",
    ]

    def test_90_decode(self):
        """test cisco_type7.decode()"""
        from passlib.utils import to_bytes, to_unicode

        handler = self.handler
        for secret, hashed in self.known_correct_hashes:
            usecret = to_unicode(secret)
            bsecret = to_bytes(secret)
            assert handler.decode(hashed) == usecret
            assert handler.decode(hashed, None) == bsecret

        with pytest.raises(UnicodeDecodeError):
            handler.decode("0958EDC8A9F495F6F8A5FD", "ascii")

    def test_91_salt(self):
        """test salt value border cases"""
        handler = self.handler
        with pytest.raises(TypeError):
            handler(salt=None)
        handler(salt=None, use_defaults=True)
        with pytest.raises(TypeError):
            handler(salt="abc")
        with pytest.raises(ValueError):
            handler(salt=-10)
        with pytest.raises(ValueError):
            handler(salt=100)

        with pytest.raises(TypeError):
            handler.using(salt="abc")
        with pytest.raises(ValueError):
            handler.using(salt=-10)
        with pytest.raises(ValueError):
            handler.using(salt=100)
        with pytest.warns(match="salt/offset must be.*"):
            subcls = handler.using(salt=100, relaxed=True)
        assert subcls(use_defaults=True).salt == 52


class cisco_type8_test(HandlerCase):
    handler = hash.cisco_type8

    known_correct_hashes = [
        #
        # generated on a Cisco c8000v, IOS XE 17.15.6
        #
        (_LONG[:127], "$8$yXWJtSg4YjJdfE$u5bgtWtAGD8rN8gy6O5kwBwbhAXzz7O.SGXrTQYm5zY"),
        (_LONG[:128], "$8$yXWJtSg4YjJdfE$u5bgtWtAGD8rN8gy6O5kwBwbhAXzz7O.SGXrTQYm5zY"),
        (_LONG[:129], "$8$yXWJtSg4YjJdfE$u5bgtWtAGD8rN8gy6O5kwBwbhAXzz7O.SGXrTQYm5zY"),
        ("hashcat", "$8$9szpjHbo403LKU$aW4eaAiJLAXcokkNnc6imT9cUN48bE3ULpvSpMAHL6s"),
        ("cisco", "$8$q5QNSSXTHxL3Ck$sNSM88IVIwqusq1tAHFpI0gPTpLL3YVCchcg0nGumF6"),
        ("password", "$8$eFee2eyLW70N3k$PISg1XZZwyBAMVDB7L/mOIF4IRO6Jq8caRa8NGLSiB."),
        ("Passw0rd!", "$8$SVWxNB/03.eI4U$IR5nybGy9LCSvfB1p5Gu/RnK8u8CGBVpdB2e9lNIOWs"),
        (
            "correct horse battery staple",
            "$8$bwqwUWhdffX1hU$wMm1xxISobq8y9ZCmO6/3vMh/.sSfilMMAOHUBVPl5.",
        ),
        (
            "p@$$:w0rd#%&*()",
            "$8$g20qzzHKTdqCS.$tHgV8.X.2JvySIHguBLFwNbREoEXtsTZ/YmuHLw3gn.",
        ),
        (
            "~`^{}[]|\"'<>,.;=+-_",
            "$8$S3NWeoOnAoGf4U$7cH00X2glWiepBW92Py0A2Hf/VfK0U7UJYukhC0Lig6",
        ),
        ("a", "$8$D896wrUK/vID8E$I7v2XyOIGEdYvBZv0135r/PCK6EiK6Xux47xi1uZC.6"),
        (
            "0123456789012345678901234",
            "$8$QYdrEZb9qcz9z.$vfHVDH3bj.l6aslWSUSWpjPcC0MSHqxEH2NJCKjiL66",
        ),
        ("A" * 64, "$8$gFmxpieHOeQmoU$xKUl2tAbb8vvvshBsnUkMsg36aDsj3LDra8wufPrtA2"),
        #
        # hashcat example hash
        #
        ("hashcat", "$8$TnGX/fE4KGHOVU$pEhnEvxrvaynpi8j4f.EMHr6M.FzU8xnZnBr/tJdFWk"),
        #
        # custom
        #
        # ensures utf-8 used for unicode
        (UPASS_TABLE, "$8$UXSHqUcaJOOYc2$i9phHWeYtwpHyTA5h8S9Pl8oMI3l.4YMtmcaCDVFY6Q"),
    ]

    known_malformed_hashes = [
        # salt too short
        "$8$TnGX/fE4KGHOV$pEhnEvxrvaynpi8j4f.EMHr6M.FzU8xnZnBr/tJdFWk",
        # bad char in checksum
        "$8$TnGX/fE4KGHOVU$pEhnEvxrvaynpi8j4f.EMHr6M.FzU8xnZnBr/tJdFW!",
        # checksum too long
        "$8$TnGX/fE4KGHOVU$pEhnEvxrvaynpi8j4f.EMHr6M.FzU8xnZnBr/tJdFWkk",
    ]

    known_unidentified_hashes = [
        # type 9
        "$9$2MJBozw/9R3UsU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6",
        # type 5 (md5_crypt)
        "$1$ehAsHC4t$4IbK3fHS/H1YGtNYBrIEB1",
    ]


class cisco_type9_test(HandlerCase):
    handler = hash.cisco_type9

    known_correct_hashes = [
        #
        # generated on a Cisco c8000v, IOS XE 17.15.6
        #
        (_LONG[:127], "$9$rXEcbXIqZ7ATd.$MXEKv.Xn7l6UAHmfZDz/avYKEDGDw809QjTdRC4PrX2"),
        (_LONG[:128], "$9$rXEcbXIqZ7ATd.$MXEKv.Xn7l6UAHmfZDz/avYKEDGDw809QjTdRC4PrX2"),
        (_LONG[:129], "$9$rXEcbXIqZ7ATd.$MXEKv.Xn7l6UAHmfZDz/avYKEDGDw809QjTdRC4PrX2"),
        ("hashcat", "$9$nyms5/IdSo/oqU$dnIT2/tC8wqO4ce7FsV6L.2Agf2pM5ZBT95dvVsYNFA"),
        ("cisco", "$9$KXeta3EyjTCelk$cvfFUim61L5WsvHPljywa3tE8IK8ZpaLE.KQ3Yun1c."),
        ("password", "$9$VD6t657EnTvGUU$l0jRVy/mcJIYXSSHlraehUwWYpurISu5BAuZhi6CdFY"),
        ("Passw0rd!", "$9$KDhEn8ygVgQ/DU$HzrQzjlcN4ygU3LkQfmxjHkXtuVnrjciT8gY.u9/KP."),
        (
            "correct horse battery staple",
            "$9$hzpFH11AFtmYwU$U8oVDyK0zDSSv5QbiqEJIz6NYqoKEyb5rn3MFpDbgFk",
        ),
        (
            "p@$$:w0rd#%&*()",
            "$9$YqkaxprVNiySiU$7xM9F/gj4d../R/v.R8hZxh8oZqxypiMJvPwuaulvI2",
        ),
        (
            "~`^{}[]|\"'<>,.;=+-_",
            "$9$6qx2wUjpa9KYV.$edQfhM2knUco.8dUXRekZfMrKRMYrdselvdQgsKH4jM",
        ),
        ("a", "$9$XkPXdDLigtPDkE$boNNhHX34LDDHnwQqru8dDctMb8BZK2nCvCPUtlnSsU"),
        (
            "0123456789012345678901234",
            "$9$6uRGqeUikZrgAU$XRwSWJdamr42bwVRDXP78YEuZLi2b/xXSRDuuY81jls",
        ),
        ("A" * 64, "$9$2TiRLfGe552TjU$e8K8Rf8pp2maxSkH3zdRJorgQQt5G4Y.n1l/MTBYNt2"),
        #
        # hashcat example hash
        #
        ("hashcat", "$9$2MJBozw/9R3UsU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6"),
        #
        # custom
        #
        # ensures utf-8 used for unicode
        (UPASS_TABLE, "$9$UXSHqUcaJOOYc2$CeqRO02NqYBlZW/QAf7DLBkFgGBUKnzLsWxkMiafwj2"),
    ]

    known_malformed_hashes = [
        # salt too long
        "$9$2MJBozw/9R3UsUU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6",
        # bad char in salt
        "$9$2MJBozw/9R3Us!$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6",
    ]

    known_unidentified_hashes = [
        # type 8
        "$8$TnGX/fE4KGHOVU$pEhnEvxrvaynpi8j4f.EMHr6M.FzU8xnZnBr/tJdFWk",
        # type 5 (md5_crypt)
        "$1$ehAsHC4t$4IbK3fHS/H1YGtNYBrIEB1",
        # junos9
        "$9$YQ4JD.PQ9A0ikA0BIrl24a",
    ]


class cisco_convoluted_type9_test(HandlerCase):
    handler = hash.cisco_convoluted_type9

    known_correct_hashes = [
        #
        # type 5 secrets as converted by a Cisco c8000v, IOS XE 17.15.6
        #
        (
            "hashcat",
            "$14$Vomh$q.AOEopkrAtsb.$FOnpOOn276DB9WWDL4.lZ3QJ4lKpHpHhTooZlSKZ5ZU",
        ),
        (
            "cisco",
            "$14$j4RA$TyDwhsUZhvYY7k$ivYck5w6PvUL8XmYezjfnKCfN6Ow6eOgO9BIPE6txAY",
        ),
        (
            "password",
            "$14$p5Dy$ghbpp.KxZA0y4.$9lFgKdFkwpAnwt1DBSrhxabL7YUx8kt5w9CgodaSSz2",
        ),
        (
            "Passw0rd!",
            "$14$IgTC$.4GDOEuR7dnZ4E$B5bbO97gGWB66ilTQ81GIZlSuqQcj0u9sh/sfprKKIE",
        ),
        (
            "correct horse battery staple",
            "$14$469.$L7eTeDk2MmBpbk$qkfz8AwYP79NpMNeKegZKx1IdqAkv0rqom/OhnVk2eQ",
        ),
        ("a", "$14$tHCS$ASXa..ys58OQ3.$nCujpwmNNTFOY3qD7t0ZS4ixOP7WfRzVd/BylQ0e.4I"),
        #
        # custom
        #
        # ensures utf-8 used for unicode
        (
            UPASS_TABLE,
            "$14$sNF6$sBxbTocEpmwFb/$UkVpBMdRVORUFaVNHGye6ChG.dIjex6YyQ8gafx9HCI",
        ),
    ]

    known_malformed_hashes = [
        # md5_crypt salt too long
        "$14$p5Dyx$ghbpp.KxZA0y4.$9lFgKdFkwpAnwt1DBSrhxabL7YUx8kt5w9CgodaSSz2",
        # scrypt salt too short
        "$14$p5Dy$ghbpp.KxZA0y4$9lFgKdFkwpAnwt1DBSrhxabL7YUx8kt5w9CgodaSSz2",
        # bad char in checksum
        "$14$p5Dy$ghbpp.KxZA0y4.$9lFgKdFkwpAnwt1DBSrhxabL7YUx8kt5w9CgodaSSz!",
        # missing checksum
        "$14$p5Dy$ghbpp.KxZA0y4.",
    ]

    known_unidentified_hashes = [
        # type 9
        "$9$2MJBozw/9R3UsU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6",
        # type 5 (md5_crypt)
        "$1$ehAsHC4t$4IbK3fHS/H1YGtNYBrIEB1",
    ]
