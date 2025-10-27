from typing import Any

import pytest

from passlib.handlers.bcrypt import bcrypt


@pytest.fixture(scope="session")
def bcrypt_backend_raises_on_wraparound() -> bool:
    try:
        bcrypt.hash(secret="abc" * 100)
    except ValueError:
        return True
    return False


@pytest.fixture(scope="class")
def bcrypt_backend_raises_on_wraparound_unittest(
    request: Any,
    bcrypt_backend_raises_on_wraparound: bool,
):
    request.cls.bcrypt_backend_raises_on_wraparound = (
        bcrypt_backend_raises_on_wraparound
    )
