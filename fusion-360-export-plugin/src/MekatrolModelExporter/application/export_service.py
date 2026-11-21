"""Capture orchestration independent of the source application."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from infrastructure.integrity_validator import validate_document
from infrastructure.json_writer import with_integrity

if TYPE_CHECKING:
    from domain.document import ModelDocument

    from .ports import DesignSource


@dataclass(frozen=True, slots=True)
class CaptureService:
    """Capture, validate, and seal one in-memory model document."""

    source: DesignSource

    def capture(self) -> ModelDocument:
        """Return a referentially valid snapshot with canonical integrity data."""
        document = with_integrity(self.source.capture())
        validate_document(document)
        return document
