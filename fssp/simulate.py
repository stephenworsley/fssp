"""Run a rule set on the firing squad problem and judge the result."""
from dataclasses import dataclass

import numpy as np

from fssp.rules import BOUNDARY, Pattern, RuleSet

PARTIAL_FIRE = "partial_fire"
MISSING_RULE = "missing_rule"
TOO_FAST = "too_fast"
TIMEOUT = "timeout"


def default_max_steps(n: int) -> int:
    return 3 * n + 10


@dataclass(frozen=True)
class MissingRule:
    step: int
    cell: int
    pattern: Pattern


@dataclass(frozen=True)
class SimulationResult:
    history: np.ndarray
    state_names: tuple[str, ...]
    n: int
    max_steps: int
    final_step: int
    fired_cells: tuple[int, ...]
    missing_rules: tuple[MissingRule, ...]
    failures: tuple[str, ...]

    @property
    def success(self) -> bool:
        return not self.failures

    @property
    def min_time(self) -> int:
        return 2 * self.n - 2


def simulate(rule_set: RuleSet, n: int, max_steps: int | None = None) -> SimulationResult:
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    if max_steps is None:
        max_steps = default_max_steps(n)
    if max_steps < 0:
        raise ValueError(f"max_steps must be non-negative, got {max_steps}")

    rules = rule_set.effective_rules()
    fire = rule_set.fire
    row = [rule_set.general] + [rule_set.quiescent] * (n - 1)
    rows = [row]
    missing: list[MissingRule] = []
    fired: list[int] = []

    for t in range(1, max_steps + 1):
        padded = [BOUNDARY, *row, BOUNDARY]
        new_row = []
        for i in range(n):
            pattern = (padded[i], padded[i + 1], padded[i + 2])
            out = rules.get(pattern)
            if out is None:
                out = fire
                missing.append(MissingRule(t, i, pattern))
            new_row.append(out)
        row = new_row
        rows.append(row)
        fired = [i for i, s in enumerate(row) if s == fire]
        if fired:
            break

    final_step = len(rows) - 1
    failures = []
    if fired and len(fired) < n:
        failures.append(PARTIAL_FIRE)
    if missing:
        failures.append(MISSING_RULE)
    if fired and final_step < 2 * n - 2:
        failures.append(TOO_FAST)
    if not fired:
        failures.append(TIMEOUT)

    index = {s: k for k, s in enumerate(rule_set.states)}
    history = np.array([[index[s] for s in r] for r in rows], dtype=int)
    return SimulationResult(history, rule_set.states, n, max_steps, final_step,
                            tuple(fired), tuple(missing), tuple(failures))
