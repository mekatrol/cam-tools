"""Application boundary protocols."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from domain.document import ModelDocument


class DesignSource(Protocol):
    """Source capable of producing a complete immutable model snapshot."""

    def capture(self) -> ModelDocument: ...
