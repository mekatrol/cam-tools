"""Application boundary protocols."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..domain.document import ModelDocument


class DesignSource(Protocol):
    """Source capable of producing a complete immutable model snapshot."""

    def capture(self, progress: ProgressReporter) -> ModelDocument: ...


class ProgressReporter(Protocol):
    """Receives monotonic capture progress and exposes cooperative cancellation."""

    @property
    def cancelled(self) -> bool: ...

    def update(self, completed: int, total: int, activity: str) -> None: ...


class NullProgressReporter:
    """Progress reporter used by non-interactive callers."""

    @property
    def cancelled(self) -> bool:
        """Return false because this reporter cannot be cancelled."""
        return False

    def update(self, completed: int, total: int, activity: str) -> None:
        """Accept an update without displaying it."""
