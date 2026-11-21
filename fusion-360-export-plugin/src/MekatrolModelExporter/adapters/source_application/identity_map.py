"""Deterministic replacement of source identities with neutral identifiers."""

import hashlib
from dataclasses import dataclass, field


@dataclass(slots=True)
class IdentityMap:
    """Assign stable document-local IDs from persistent source keys."""

    _ids: dict[tuple[str, str], str] = field(default_factory=dict)
    _used: set[str] = field(default_factory=set)

    def id_for(self, category: str, source_key: str) -> str:
        """Return the existing ID or create a deterministic collision-safe one."""
        lookup = (category, source_key)
        if lookup in self._ids:
            return self._ids[lookup]
        digest = hashlib.sha256(source_key.encode()).hexdigest()
        length = 16
        candidate = f"{category}:{digest[:length]}"
        while candidate in self._used:
            length += 2
            candidate = f"{category}:{digest[:length]}"
        self._ids[lookup] = candidate
        self._used.add(candidate)
        return candidate
