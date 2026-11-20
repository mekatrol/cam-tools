"""Fusion script entry point for the Mekatrol model exporter."""

from entrypoint import show_hello_world


def run(_context: object) -> None:
    """Run the finite, user-triggered Fusion script."""
    show_hello_world()
