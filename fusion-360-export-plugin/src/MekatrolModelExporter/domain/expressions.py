"""Data-only expression trees and dimensional parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import JsonScalar


@dataclass(frozen=True, slots=True)
class ExpressionNode:
    """A neutral expression syntax-tree node."""

    kind: str
    value: JsonScalar = None
    children: tuple[ExpressionNode, ...] = ()


@dataclass(frozen=True, slots=True)
class Parameter:
    """Named scalar with canonical value and optional expression."""

    id: str
    label: str
    value: JsonScalar
    dimension: str
    unit: str
    expression: ExpressionNode | None = None
    dependencies: tuple[str, ...] = ()
    comment: str = ""
    exposed: bool = True
