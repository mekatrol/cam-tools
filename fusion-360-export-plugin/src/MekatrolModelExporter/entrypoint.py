"""Host interaction and top-level exception boundary."""

import traceback

import adsk.core


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
