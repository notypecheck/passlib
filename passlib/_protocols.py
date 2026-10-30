from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Self

    from typing_extensions import Buffer


class HashLike(Protocol):
    """Lifted from hashlib.pyi."""

    @property
    def digest_size(self) -> int: ...

    @property
    def block_size(self) -> int: ...

    @property
    def name(self) -> str: ...

    def copy(self) -> Self: ...

    def digest(self) -> bytes: ...

    def hexdigest(self) -> str: ...

    def update(self, data: Buffer, /) -> None: ...


SHAFunc = Callable[[], HashLike]
