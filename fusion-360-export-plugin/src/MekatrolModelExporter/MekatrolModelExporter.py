"""Fusion script entry point for the Mekatrol model exporter."""

from entrypoint import run_export


def run(_context: object) -> None:
    """Run the finite, user-triggered Fusion script."""
    run_export()
