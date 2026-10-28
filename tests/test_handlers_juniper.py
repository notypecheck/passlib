import pytest

from passlib import hash

from .test_handlers import UPASS_TABLE
from .utils import HandlerCase


class junos9_test(HandlerCase):
    handler = hash.junos9
    salt_bits = 6

    known_correct_hashes = [
        #
        # generated on vJunos-router 25.4R1-S2.3
        #
        ("juniper", "$9$YQ4JD.PQ9A0ikA0BIrl24a"),
        ("password", "$9$q.T36/tOIcCtxds4DjCtu0BE"),
        ("Passw0rd!", "$9$UwDqP5T39tOz3K8LX-dk.PfT36/C"),
        (
            "correct horse battery staple",
            "$9$NebwgPfzn9pfT6A0OcSYgoaJGmPQCtOQFSevW-dVwsg4ZUDkfQnk.Qn9C1IYgoaJGikPznCs2PQz6u0Ecy",
        ),
        ("p@$$:w0rd#%&*()", "$9$FyNx3Cu0OISylf5lK8Xws.PfQ6AOBEyreTQ9AuBREvW8XNd"),
        ("a", "$9$tzECu0I"),
        (
            "0123456789012345678901234",
            "$9$rUjlWLxNdw24Xxik.PQzreK8-VaZUjqm2g5Q3nCAM8LXVwoJGqP5jiBIESeK24oJjH.P5F69mP",
        ),
        ("caf\xe9", "$9$x66dVYg4Zkqfz6Bc"),
        (UPASS_TABLE, "$9$RjxElMXxwY2ZF/rMLXbsoaGimQtpRhrM"),
        (
            "A" * 64,
            "$9$3Hsc6/ApuBIRcylKWLXdVws24oZUDHq.fTz3/CAOBIRhSyevMLx7dbs2oJZiHq.P5TFn6CtpO1Rhyle8Lx7-VbYg4JGUik.PTzF9Ctp0B1EcSlKv8X7-bsYaJGUjHkmf5z3n9Ap01RErlKvWLXNdVs2gaZUjk.mQz3n/CAuOBRhcrevWX7Nws2goJZD",
        ),
        (
            "B" * 128,
            "$9$PTQ3/9t0OIhSlv8L-dws2oaGjiqPfQ36CpOBhcrlKW8x-dw2gaGDH.f53n9Ct0OIhcrKv8xNVsg4GUiHqPfQ3n9tpOIESlvMx7dVw2gaGUiq.fQF6CpuIRcSrKv8x7dwsgaZDH.mQzn69tpOIRcrlv8XNVsYaJUDiq.fQzn9CpO1ESle8L7NdwsgaJUiH.fTF6CAOBREcrlv8L7dVsgoZDHkf5zFn9CpOBRcSlvWXNVbg4JZUiH.f5zn6Cp01ESyvMLX7dVsg4JUDH.PTF6/puB1RcSlvML7NVs2oZDj.m5Tzn6CpuBRESlKWXN-sY4oJUDH.m5zF6Ct01EhleMWL7NVsY4JZDHqPTF3CAu0BRESleM",
        ),
        (
            "~`^{}[]|\\x\"'<>,.;=+-_",
            "$9$0Wjh1rvMWxwgaYgtORcKvq.Pf6ASrKvLN/9BIRSeKqmPfz3REclM8vMwYgJUDhcy",
        ),
        ('"quoted"', "$9$PTQFn/t1Ey/CMX7-2gZUjkqm"),
    ]

    known_malformed_hashes = [
        # salt character without the characters it calls for
        "$9$Q",
        # truncated checksum
        "$9$q.T36/tOIcCtxds4DjCtu0B",
        # bad char in checksum
        "$9$q.T36/tOIcCtxds4DjCtu0!E",
    ]

    known_unidentified_hashes = [
        # cisco type 7
        "044B0A151C36435C0D",
        # cisco type 9
        "$9$2MJBozw/9R3UsU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6",
        # md5_crypt
        "$1$dOHYPKoP$tnxS1T8Q6VVn3kpV8cN6o.",
    ]

    def test_cisco_type9_context(self):
        """test a CryptContext holding both "$9$" formats"""
        from passlib.context import CryptContext

        ctx = CryptContext(["cisco_type9", "junos9"])
        assert ctx.identify("$9$YQ4JD.PQ9A0ikA0BIrl24a") == "junos9"
        assert ctx.verify("juniper", "$9$YQ4JD.PQ9A0ikA0BIrl24a")
        cisco = "$9$2MJBozw/9R3UsU$2lFhcKvpghcyw8deP25GOfyZaagyUOGBymkryvOdfo6"
        assert ctx.identify(cisco) == "cisco_type9"

    def test_90_decode(self):
        """test junos9.decode()"""
        from passlib.utils import to_bytes, to_unicode

        handler = self.handler
        for secret, hashed in self.known_correct_hashes:
            assert handler.decode(hashed) == to_unicode(secret)
            assert handler.decode(hashed, None) == to_bytes(secret)

        with pytest.raises(UnicodeDecodeError):
            handler.decode("$9$RjxElMXxwY2ZF/rMLXbsoaGimQtpRhrM", "ascii")

        # decodes to a byte value over 255
        with pytest.raises(ValueError):
            handler.decode("$9$QnnnQQQ")

    def test_91_salt(self):
        """test salt value border cases"""
        handler = self.handler
        with pytest.raises(TypeError):
            handler(salt=None)
        handler(salt=None, use_defaults=True)
        with pytest.raises(TypeError):
            handler(salt=1)
        # the first character sets how many follow it
        handler(salt="Qabc")
        handler(salt="Bab")
        handler(salt="7a")
        handler(salt="i")
        with pytest.raises(ValueError):
            handler(salt="Qab")
        with pytest.raises(ValueError):
            handler(salt="ia")
        with pytest.raises(ValueError):
            handler(salt="!")
