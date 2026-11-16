"""Rule-set data type, validation, and the built-in quiescent rules."""
from collections.abc import Mapping
from dataclasses import dataclass

BOUNDARY: str = "#"

Pattern = tuple[str, str, str]


@dataclass(frozen=True)
class RuleSet:
    name: str
    states: tuple[str, ...]
    general: str
    quiescent: str
    fire: str
    rules: Mapping[Pattern, str]

    def __post_init__(self):
        if BOUNDARY in self.states:
            raise ValueError(f"boundary marker {BOUNDARY!r} cannot be a state")
        if len(set(self.states)) != len(self.states):
            raise ValueError(f"duplicate state in {self.states!r}")
        for role in ("general", "quiescent", "fire"):
            if getattr(self, role) not in self.states:
                raise ValueError(f"{role} state {getattr(self, role)!r} is not in states")
        if len({self.general, self.quiescent, self.fire}) != 3:
            raise ValueError("general, quiescent and fire states must be distinct")

        states = set(self.states)
        neighbours = states | {BOUNDARY}
        for pattern, out in self.rules.items():
            if (not isinstance(pattern, tuple) or len(pattern) != 3
                    or pattern[0] not in neighbours or pattern[1] not in states
                    or pattern[2] not in neighbours):
                raise ValueError(f"invalid rule pattern {pattern!r} -> {out!r}")
            if out not in states:
                raise ValueError(f"rule {pattern!r} -> {out!r} outputs an undeclared state")

    def effective_rules(self) -> dict[Pattern, str]:
        q = self.quiescent
        return {(q, q, q): q, (q, q, BOUNDARY): q, **self.rules}
