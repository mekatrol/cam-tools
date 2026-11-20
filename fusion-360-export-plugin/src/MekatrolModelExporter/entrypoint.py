"""Host interaction and top-level exception boundary."""

import importlib
import traceback
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from types import ModuleType


class _UserInterface(Protocol):
    def messageBox(self, message: str) -> int: ...


class _Application(Protocol):
    @staticmethod
    def get() -> _Application: ...

    @property
    def userInterface(self) -> _UserInterface: ...


@runtime_checkable
class _CoreModule(Protocol):
    Application: type[_Application]


def _load_core_module() -> _CoreModule:
    module: ModuleType = importlib.import_module("adsk.core")
    if not isinstance(module, _CoreModule):
        message = "The host core API does not provide the expected application interface"
        raise TypeError(message)
    return module


def show_hello_world() -> None:
    """Show the initial milestone dialog without retaining host objects."""
    user_interface = None
    try:
        application = _load_core_module().Application.get()
        user_interface = application.userInterface
        user_interface.messageBox("Hello World from Mekatrol")
    except Exception:
        if user_interface is not None:
            user_interface.messageBox(f"Mekatrol script failed:\n{traceback.format_exc()}")
