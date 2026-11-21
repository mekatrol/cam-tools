"""Capture orchestration independent of the source application."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..infrastructure.fidelity_log import write_fidelity_log_atomic
from ..infrastructure.integrity_validator import validate_document
from ..infrastructure.json_writer import with_integrity, write_json_atomic

if TYPE_CHECKING:
    from pathlib import Path

    from ..domain.document import ModelDocument
    from .ports import DesignSource, ProgressReporter


class CaptureCancelledError(RuntimeError):
    """Raised when the user cancels before a complete snapshot is available."""


@dataclass(frozen=True, slots=True)
class CaptureService:
    """Capture, validate, and seal one in-memory model document."""

    source: DesignSource

    def capture(self, progress: ProgressReporter) -> ModelDocument:
        """Return a referentially valid snapshot with canonical integrity data."""
        if progress.cancelled:
            raise CaptureCancelledError
        document = with_integrity(self.source.capture(progress))
        if progress.cancelled:
            raise CaptureCancelledError
        validate_document(document)
        return document

    def export(self, destination: Path, progress: ProgressReporter) -> ModelDocument:
        """Capture and atomically commit a validated document."""
        document = self.capture(progress)
        progress.update(1, 1, "Writing validated model")
        if progress.cancelled:
            raise CaptureCancelledError
        write_json_atomic(document, destination)
        write_fidelity_log_atomic(document, destination)
        return document
