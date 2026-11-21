"""Host interaction and top-level exception boundary."""

import traceback
from dataclasses import dataclass
from pathlib import Path

import adsk.core
from adapters.source_application import ActiveDesignReader
from application import CaptureCancelledError, CaptureService


@dataclass(slots=True)
class _DialogProgressReporter:
    dialog: adsk.core.ProgressDialog

    @property
    def cancelled(self) -> bool:
        return self.dialog.wasCancelled

    def update(self, completed: int, total: int, activity: str) -> None:
        del activity
        percent = min(100, max(0, round((completed / max(total, 1)) * 100)))
        self.dialog.progressValue = percent


def show_hello_world() -> None:
    """Show the initial milestone dialog without retaining host objects."""
    user_interface = None
    try:
        application = adsk.core.Application.get()
        user_interface = application.userInterface
        user_interface.messageBox("Hello World from Mekatrol")
    except Exception:
        if user_interface is not None:
            user_interface.messageBox(f"Mekatrol script failed:\n{traceback.format_exc()}")


def run_export() -> None:
    """Prompt for a destination and run the finite atomic export workflow."""
    user_interface = None
    progress_dialog = None
    try:
        application = adsk.core.Application.get()
        user_interface = application.userInterface
        file_dialog = user_interface.createFileDialog()
        file_dialog.title = "Export neutral parametric model"
        file_dialog.filter = "JSON model (*.json)"
        file_dialog.initialFilename = f"{application.activeDocument.name}.json"
        if file_dialog.showSave() != 0:
            return
        destination = Path(file_dialog.filename)
        if destination.suffix.casefold() != ".json":
            destination = destination.with_suffix(".json")
        if not destination.name:
            return

        progress_dialog = user_interface.createProgressDialog()
        progress_dialog.isCancelButtonShown = True
        progress_dialog.show("Export model", "Capturing model data", 0, 100)
        reporter = _DialogProgressReporter(progress_dialog)
        service = CaptureService(ActiveDesignReader(application))
        try:
            document = service.export(destination, reporter)
        except CaptureCancelledError:
            user_interface.messageBox("Export cancelled. No destination file was replaced.")
            return
        coverage = document.coverage
        user_interface.messageBox(
            "Export complete.\n"
            f"Saved: {destination}\n"
            f"Exact: {coverage.exact}; fallback: {coverage.complete_with_fallback}; "
            f"approximated: {coverage.approximated}; "
            f"unclassified: {coverage.unclassified}."
        )
    except Exception:
        if user_interface is not None:
            user_interface.messageBox(f"Mekatrol export failed:\n{traceback.format_exc()}")
    finally:
        if progress_dialog is not None:
            progress_dialog.hide()
