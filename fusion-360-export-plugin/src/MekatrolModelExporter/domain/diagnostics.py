"""Fidelity diagnostics and aggregate coverage."""

from __future__ import annotations

from dataclasses import dataclass

from .types import CaptureStatus, Severity


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """Machine-readable capture issue associated with an optional entity."""

    code: str
    severity: Severity
    message: str
    entity_id: str | None = None
    importer_guidance: str | None = None


@dataclass(frozen=True, slots=True)
class Coverage:
    """Entity counts grouped by capture completeness."""

    exact: int = 0
    complete_with_fallback: int = 0
    approximated: int = 0
    unclassified: int = 0

    def count(self, status: CaptureStatus) -> int:
        """Return the count for a capture status."""
        return {
            CaptureStatus.EXACT: self.exact,
            CaptureStatus.COMPLETE_WITH_FALLBACK: self.complete_with_fallback,
            CaptureStatus.APPROXIMATED: self.approximated,
            CaptureStatus.UNCLASSIFIED: self.unclassified,
        }[status]
