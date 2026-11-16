# Firing Squad Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python command-line program that simulates a 1D cellular automaton on the firing squad synchronisation problem, draws the run as coloured terminal text (default) or a matplotlib PNG, and reports whether the problem was solved.

**Architecture:** There are four small modules:
- `rules.py` defines the rule-set data type, its validation, and the built-in rules.
- `presets.py` holds the named rule sets.
- `simulate.py` runs a rule set and returns a result object. The result contains an integer history array and the verdict.
- `render_text.py` and `render_png.py` turn that array into output and don't depend on the simulation.

`cli.py` connects these with argparse.

**Tech Stack:** Python ≥ 3.10, numpy, matplotlib (imported only for `--matplotlib`), pytest.

**Spec:** `docs/superpowers/specs/2026-11-16-firing-squad-design.md`. Read it alongside this plan.

## Global Constraints

- The boundary marker is the string `"#"`. It is never a state, is never updated, and appears only as the left or right element of a rule key.
- Rule keys are `(left, self, right)` tuples of state names. Values are state names.
- The built-in rules, which a rule set's own entries override, are `(Q, Q, Q) -> Q` and `(Q, Q, "#") -> Q`, where Q is that rule set's quiescent state.
- The initial row is the general in cell 0, with every other cell quiescent.
- If a pattern has no rule, the cell becomes the fire state and the event is recorded.
- The run stops at the first step where any cell is in the fire state, or at `max_steps`.
- Success requires all of the following:
  - every cell is in the fire state on the stopping step,
  - no missing rules were hit,
  - the firing time is ≥ `2n − 2`.
- `default_max_steps(n) == 3 * n + 10`.
- The simulation output is a 2D numpy integer array of shape `(steps + 1, n)`, with t = 0 as row 0. `history[t, i]` indexes into `state_names`, and boundary cells are excluded.
- matplotlib may be imported only inside `render_png.py`, and `render_png.py` is imported only when `--matplotlib` is given.

## Review Focus

1. **Mazoyer at n = 2** (below the size it was designed for). Expect a clean failure verdict, not a crash or an exception. *(Task 3 test)*
2. **n = 1** (boundaries on both sides of one cell). Expect the simulation to run normally; Mazoyer fires at t = 1 and succeeds. *(Task 3 test)*
3. **A typo in a custom rule table** (a rule outputs a state that isn't declared). Expect a `ValueError` naming the bad entry when the rule set is created, not a `KeyError` partway through a run. *(Task 1 test)*
4. **`--max-steps` set below 2n − 2**, including 0. Expect a timeout failure verdict and a history containing only the rows that were simulated. *(Task 2 test)*
5. **`--cells 0` or a negative value.** Expect an argparse usage error with exit code 2, not a traceback. *(Task 6 test)*

---

### Task 1: Project skeleton and `RuleSet`

**Files:**
- Create: `fssp/__init__.py` (empty), `fssp/rules.py`, `tests/__init__.py` (empty), `tests/test_rules.py`, `requirements.txt` (`numpy`, `matplotlib`, `pytest`), `.gitignore` (`__pycache__/`, `*.png`)
- Create: `docs/superpowers/specs/2026-11-16-firing-squad-design.md` and `docs/superpowers/plans/2026-11-16-firing-squad.md` (copy in the design doc and this plan)

**Interfaces:**
- Produces:
  - `BOUNDARY: str = "#"`
  - `Pattern = tuple[str, str, str]`
  - `@dataclass(frozen=True) class RuleSet` with these fields:
    - `name: str`
    - `states: tuple[str, ...]` (ordered; the index of a state is its integer code)
    - `general: str`, `quiescent: str` and `fire: str`
    - `rules: Mapping[Pattern, str]`
  - `RuleSet.effective_rules() -> dict[Pattern, str]`, which is the built-in rules overridden by `rules`

- [ ] **Step 1: Set up the repo.** Run `git init`, then create the files above and copy in the two docs.
- [ ] **Step 2: Write the failing tests** in `tests/test_rules.py`:

```python
import pytest
from fssp.rules import RuleSet, BOUNDARY

def make(rules=None, **kw):
    args = dict(name="t", states=("G", "Q", "F"), general="G", quiescent="Q", fire="F",
                rules=rules or {})
    args.update(kw)
    return RuleSet(**args)

def test_boundary_marker():
    assert BOUNDARY == "#"

def test_builtins_present():
    eff = make().effective_rules()
    assert eff[("Q", "Q", "Q")] == "Q"
    assert eff[("Q", "Q", "#")] == "Q"

def test_explicit_rule_overrides_builtin():
    assert make({("Q", "Q", "Q"): "G"}).effective_rules()[("Q", "Q", "Q")] == "G"

@pytest.mark.parametrize("kw", [
    dict(general="X"),                    # special state not in states
    dict(fire="G"),                       # general/quiescent/fire not distinct
    dict(states=("G", "Q", "F", "#")),    # boundary used as a state
    dict(states=("G", "Q", "F", "G")),    # duplicate state
])
def test_invalid_declarations(kw):
    with pytest.raises(ValueError):
        make(**kw)

@pytest.mark.parametrize("rules", [
    {("#", "G", "Q"): "Z"},   # output not a declared state  (Review Focus 3)
    {("#", "Z", "Q"): "F"},   # key uses an undeclared state
    {("G", "#", "Q"): "F"},   # boundary in the centre position
])
def test_invalid_rules_name_the_entry(rules):
    with pytest.raises(ValueError, match="Z|#"):
        make(rules)
```

- [ ] **Step 3: Run the tests** with `python -m pytest tests/test_rules.py -v`. Expected: they FAIL with `ModuleNotFoundError: fssp.rules`.
- [ ] **Step 4: Implement `fssp/rules.py`.** Validate in `__post_init__`, raising `ValueError` with a message that includes the offending pattern or state.
- [ ] **Step 5: Run the tests** with `python -m pytest tests/test_rules.py -v`. Expected: all PASS.
- [ ] **Step 6: Commit** with `git add -A && git commit -m "feat: RuleSet with validation and built-in quiescent rules"`

### Task 2: Simulation engine and verdict

**Files:**
- Create: `fssp/simulate.py`, `tests/test_simulate.py`

**Interfaces:**
- Consumes: `RuleSet`, `BOUNDARY` and `RuleSet.effective_rules()` from Task 1.
- Produces:
  - Failure code constants: `PARTIAL_FIRE = "partial_fire"`, `MISSING_RULE = "missing_rule"`, `TOO_FAST = "too_fast"` and `TIMEOUT = "timeout"`
  - `default_max_steps(n: int) -> int`
  - `@dataclass(frozen=True) class MissingRule` with fields `step: int` (the time at which the cell fired), `cell: int` and `pattern: Pattern`
  - `@dataclass(frozen=True) class SimulationResult` with these fields:
    - `history: np.ndarray` (int, shape `(final_step + 1, n)`)
    - `state_names: tuple[str, ...]`
    - `n: int` and `max_steps: int`
    - `final_step: int`
    - `fired_cells: tuple[int, ...]` (cells in the fire state at `final_step`)
    - `missing_rules: tuple[MissingRule, ...]`
    - `failures: tuple[str, ...]` (failure codes, in the order PARTIAL_FIRE, MISSING_RULE, TOO_FAST, TIMEOUT)
  - `SimulationResult.success: bool`, a property equal to `not failures`
  - `SimulationResult.min_time: int`, a property equal to `2 * n - 2`
  - `simulate(rule_set: RuleSet, n: int, max_steps: int | None = None) -> SimulationResult`, which raises `ValueError` if `n < 1` or `max_steps < 0`

- [ ] **Step 1: Write the failing tests** in `tests/test_simulate.py`. They use small hand-made rule sets and don't need any preset:

```python
import pytest
from fssp.rules import RuleSet
from fssp.simulate import (simulate, default_max_steps, MissingRule,
                           PARTIAL_FIRE, MISSING_RULE, TOO_FAST, TIMEOUT)

def rs(rules, states=("G", "Q", "F")):
    return RuleSet("t", states, "G", "Q", "F", rules)

# Solves n=2 in exactly 2n-2 = 2 steps.
TWO_CELL = rs({("#", "G", "Q"): "X", ("G", "Q", "#"): "X",
               ("#", "X", "X"): "F", ("X", "X", "#"): "F"}, states=("G", "Q", "F", "X"))

def test_default_max_steps():
    assert default_max_steps(20) == 70

def test_success():
    r = simulate(TWO_CELL, 2)
    assert r.success and r.failures == () and r.final_step == 2 and r.min_time == 2
    assert r.fired_cells == (0, 1)
    names = r.state_names
    assert [[names[s] for s in row] for row in r.history.tolist()] == [["G", "Q"], ["X", "X"], ["F", "F"]]

def test_partial_fire_stops_immediately():
    r = simulate(rs({("#", "G", "Q"): "F", ("G", "Q", "Q"): "Q"}), 4)
    assert r.final_step == 1 and r.history.shape == (2, 4)
    assert r.fired_cells == (0,)
    assert r.failures == (PARTIAL_FIRE, TOO_FAST)

def test_empty_table_cannot_fake_success():
    # anti-goal: every cell misses a rule and fires together at t=1
    r = simulate(rs({}), 2)
    assert not r.success and r.fired_cells == (0, 1)
    assert r.failures == (MISSING_RULE, TOO_FAST)
    assert r.missing_rules == (MissingRule(1, 0, ("#", "G", "Q")), MissingRule(1, 1, ("G", "Q", "#")))

def test_empty_table_larger_n_builtins_keep_rest_quiet():
    r = simulate(rs({}), 5)
    assert r.fired_cells == (0, 1)
    assert r.failures == (PARTIAL_FIRE, MISSING_RULE, TOO_FAST)

STUCK = rs({("#", "G", "Q"): "G", ("G", "Q", "Q"): "Q", ("G", "Q", "#"): "Q"})

def test_timeout_default_limit():
    r = simulate(STUCK, 3)
    assert r.failures == (TIMEOUT,) and r.final_step == 19 and r.history.shape == (20, 3)

@pytest.mark.parametrize("limit", [0, 1])           # Review Focus 4
def test_timeout_small_limit(limit):
    r = simulate(STUCK, 3, max_steps=limit)
    assert r.failures == (TIMEOUT,) and r.history.shape == (limit + 1, 3)

@pytest.mark.parametrize("n,limit", [(0, None), (-1, None), (3, -1)])
def test_bad_arguments(n, limit):
    with pytest.raises(ValueError):
        simulate(STUCK, n, max_steps=limit)
```

- [ ] **Step 2: Run the tests** with `python -m pytest tests/test_simulate.py -v`. Expected: they FAIL with an import error.
- [ ] **Step 3: Implement `fssp/simulate.py`.**
  - Keep rows as lists of state names while stepping, and pad each row with `BOUNDARY` on both sides to build the keys.
  - Build the int array once at the end, using `state_names = rule_set.states`.
  - Look up `effective_rules()` once, before the loop.
- [ ] **Step 4: Run the tests** with `python -m pytest tests/ -v`. Expected: all PASS.
- [ ] **Step 5: Commit** with `git add -A && git commit -m "feat: simulation engine with firing verdict"`

### Task 3: Mazoyer preset

**Files:**
- Create: `fssp/presets.py`, `tests/test_presets.py`

**Interfaces:**
- Consumes: `RuleSet` (Task 1) and `simulate` (Task 2).
- Produces:
  - `MAZOYER: RuleSet`, named `"mazoyer"`, with states `("A", "B", "C", "L", "G", "F")`, general `G`, quiescent `L` and fire `F`
  - `PRESETS: dict[str, RuleSet]`, equal to `{"mazoyer": MAZOYER}`. Users add their own rule sets here.

- [ ] **Step 1: Write the failing tests** in `tests/test_presets.py`:

```python
import pytest
from fssp.presets import PRESETS, MAZOYER
from fssp.simulate import simulate

def test_registry():
    assert PRESETS["mazoyer"] is MAZOYER

@pytest.mark.parametrize("n", range(3, 61))
def test_mazoyer_minimal_time(n):
    r = simulate(MAZOYER, n)
    assert r.success and r.final_step == 2 * n - 2 and r.missing_rules == ()

def test_mazoyer_n1():                                   # Review Focus 2
    r = simulate(MAZOYER, 1)
    assert r.success and r.final_step == 1

def test_mazoyer_n2_fails_cleanly():                     # Review Focus 1
    r = simulate(MAZOYER, 2)
    assert not r.success and r.final_step == 3 and r.fired_cells == (1,)
```

- [ ] **Step 2: Run the tests** with `python -m pytest tests/test_presets.py -v`. Expected: they FAIL with an import error.
- [ ] **Step 3: Implement `fssp/presets.py`.** Build the rule dict from the transcription below. It was transcribed from `hediet/lean-cellular-automata` `fssp_mazoyer/ca.lean`, which is ported from the Coq proof in `rocq-archive/firing-squad`, and has been verified to give 2n − 2 for n = 3..199. Each table string gives the output for the varying neighbour, in the order of `ORDER`. Cite the source in the module docstring.

```python
ORDER = "ABCLGF"
_T = {
    "TAA": "ABCABF", "TBA": "FGCGCF", "TLA": "ALGAFF", "TAB": "BBLGFF",
    "TBB": "ABCGBF", "TCB": "AFFLLF", "TLB": "GBLFBF", "TGB": "CFBCGF",
    "TBC": "FFCCGF", "TCC": "ABCCBF", "TLC": "AGCCGF", "TAL": "LLLGCF",
    "TCL": "LLLAGF", "TGL": "LLLCAF", "TG_L": "BBAABF", "TG_G": "FGAFFF",
}
def _t(table, x): return _T[table][ORDER.index(x)]

def _delta(a, b, c):  # Mazoyer's δ(left, self, right)
    if b == "A": return {"A": _t("TAA", c), "B": _t("TBA", c), "C": "A",
                         "L": _t("TLA", c), "G": "C", "F": "F"}[a]
    if b == "B": return {"A": _t("TAB", c), "B": _t("TBB", c), "C": _t("TCB", c),
                         "L": _t("TLB", c), "G": _t("TGB", c), "F": "F"}[a]
    if b == "C": return {"A": "B", "B": _t("TBC", c), "C": _t("TCC", c),
                         "L": _t("TLC", c), "G": "B", "F": "F"}[a]
    if b == "L": return {"A": _t("TAL", c), "B": "L", "C": _t("TCL", c),
                         "L": "L", "G": _t("TGL", c), "F": "L"}[a]
    if b == "G": return {"L": _t("TG_L", a), "G": _t("TG_G", a)}.get(c, "G")

# Keys: centre in "ABCLG", neighbours in "ABCLG#".
# The boundary acts as a phantom neighbour: "L" on the left, "G" on the right.
# The value is _delta(left or "L", centre, right or "G").
```

- [ ] **Step 4: Run the tests** with `python -m pytest tests/ -v`. Expected: all PASS.
- [ ] **Step 5: Commit** with `git add -A && git commit -m "feat: Mazoyer 6-state preset"`

### Task 4: Terminal text renderer

**Files:**
- Create: `fssp/render_text.py`, `tests/test_render_text.py`

**Interfaces:**
- Consumes: a history array and `state_names`, in the shape described in Task 2.
- Produces: `render_text(history: np.ndarray, state_names: Sequence[str], color: bool = True) -> str`. The returned string has no trailing newline and is laid out as follows:
  - **Line 1, the legend:** `"states: "` followed by each state name, separated by single spaces.
  - **One line per time step after that:** `f"{t:>{w}} | "` followed by the row's cells. `w` is the width of the largest t. Each cell is its state name left-justified to the longest name's width, and cells are joined with no separator.
  - **Colour:** when `color` is on, each cell and legend entry is wrapped in `\033[{code}m...\033[0m`. The codes cycle by state index through `[31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]`. When `color` is off, there are no escape codes.

- [ ] **Step 1: Write the failing tests** in `tests/test_render_text.py`:

```python
import re
import numpy as np
from fssp.render_text import render_text

H = np.array([[0, 1, 1], [2, 2, 2]])
NAMES = ("G", "Q", "F")
ANSI = re.compile(r"\033\[[0-9;]*m")

def test_plain_layout():
    assert render_text(H, NAMES, color=False) == "states: G Q F\n0 | GQQ\n1 | FFF"

def test_colour_codes_by_state_index():
    out = render_text(H, NAMES)
    assert "\033[31mG\033[0m" in out and "\033[32mQ\033[0m" in out and "\033[33mF\033[0m" in out
    assert ANSI.sub("", out) == render_text(H, NAMES, color=False)

def test_time_column_width_and_multichar_names():
    out = render_text(np.zeros((11, 2), dtype=int), ("Gen", "Q"), color=False).splitlines()
    assert out[1] == " 0 | GenGen" and out[11] == "10 | GenGen"
```

- [ ] **Step 2: Run the tests** with `python -m pytest tests/test_render_text.py -v`. Expected: they FAIL with an import error.
- [ ] **Step 3: Implement `render_text`** in `fssp/render_text.py`.
- [ ] **Step 4: Run the tests** with `python -m pytest tests/ -v`. Expected: all PASS.
- [ ] **Step 5: Commit** with `git add -A && git commit -m "feat: coloured terminal renderer"`

### Task 5: matplotlib PNG renderer

**Files:**
- Create: `fssp/render_png.py`, `tests/test_render_png.py`

**Interfaces:**
- Consumes: the same inputs as Task 4.
- Produces: `render_png(history: np.ndarray, state_names: Sequence[str], path: str) -> None`.
  - It calls `matplotlib.use("Agg")` and uses `imshow` with a `ListedColormap` built from `tab10` (or `tab20` when there are more than 10 states).
  - Cells run along x and time along y, with t = 0 at the top.
  - The x axis is labelled "cell" and the y axis "time step".
  - The legend is made of `Patch` handles, one per state name.
  - The figure is closed after saving.

- [ ] **Step 1: Write the failing tests** in `tests/test_render_png.py`:

```python
import numpy as np
import pytest
pytest.importorskip("matplotlib")
from fssp.render_png import render_png

def test_writes_png(tmp_path):
    out = tmp_path / "run.png"
    render_png(np.array([[0, 1], [2, 2]]), ("G", "Q", "F"), str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
```

- [ ] **Step 2: Run the test** with `python -m pytest tests/test_render_png.py -v`. Expected: it FAILS with an import error.
- [ ] **Step 3: Implement `render_png`** in `fssp/render_png.py`.
- [ ] **Step 4: Run the tests** with `python -m pytest tests/ -v`. Expected: all PASS.
- [ ] **Step 5: Commit** with `git add -A && git commit -m "feat: matplotlib PNG renderer"`

### Task 6: Command-line interface and verdict report

**Files:**
- Create: `fssp/cli.py`, `fssp/__main__.py` (calls `raise SystemExit(main())`), `tests/test_cli.py`, `README.md` (a short usage section and how to add a preset)

**Interfaces:**
- Consumes: `PRESETS` (Task 3), `simulate`, `SimulationResult` and the failure constants (Task 2), `render_text` (Task 4), and `render_png` (Task 5), which is imported lazily inside `main`.
- Produces:
  - `format_verdict(result: SimulationResult) -> str`
  - `main(argv: list[str] | None = None) -> int`, which returns 0 on success and 1 on failure.
- **Arguments:**
  - `--cells`: a positive int, defaulting to 20. Use an argparse `type` function that rejects values below 1.
  - `--preset`: one of the `PRESETS` keys, defaulting to `mazoyer`.
  - `--max-steps`: a non-negative int, defaulting to None.
  - `--matplotlib`: a flag.
  - `--output`: defaults to `firing_squad.png`.
- **Output:**
  - Without `--matplotlib`, `main` prints `render_text(...)` and then the verdict.
  - With `--matplotlib`, it writes the PNG, prints `f"Wrote {path}"`, and then prints the verdict.
- **Verdict text:**
  - **Success:** `f"SUCCESS: all {n} cells fired together at t={final_step} (minimum possible: {min_time})."`
  - **Failure:** first `f"FAILURE (stopped at t={final_step}):"`, then one `"  - "` line per failure code, in order:
    - `PARTIAL_FIRE`: `f"only cells {list} fired, out of {n}"`
    - `MISSING_RULE`: one line per record, `f"no rule for pattern {pattern} at cell {cell}, t={step} (cell fired)"`
    - `TOO_FAST`: `f"fired at t={final_step}, faster than the minimum possible {min_time}; the rule set is broken"`
    - `TIMEOUT`: `f"no cell fired within {max_steps} steps"`

- [ ] **Step 1: Write the failing tests** in `tests/test_cli.py`:

```python
import subprocess
import sys
import pytest
from fssp.cli import main, format_verdict
from fssp.presets import MAZOYER
from fssp.simulate import simulate

def test_default_text_run_succeeds(capsys):
    assert main(["--cells", "5"]) == 0
    out = capsys.readouterr().out
    assert "states: " in out
    assert out.rstrip().endswith("SUCCESS: all 5 cells fired together at t=8 (minimum possible: 8).")

def test_text_mode_never_imports_matplotlib():
    code = ("import sys; from fssp.cli import main; main(['--cells', '3']); "
            "assert 'matplotlib' not in sys.modules")
    assert subprocess.run([sys.executable, "-c", code], capture_output=True).returncode == 0

def test_failure_exit_code_and_report(capsys):
    assert main(["--cells", "5", "--max-steps", "3"]) == 1
    assert "FAILURE (stopped at t=3):\n  - no cell fired within 3 steps" in capsys.readouterr().out

def test_verdict_partial_fire():
    text = format_verdict(simulate(MAZOYER, 2))
    assert text.startswith("FAILURE (stopped at t=3):")
    assert "only cells [1] fired, out of 2" in text

@pytest.mark.parametrize("bad", ["0", "-3"])            # Review Focus 5
def test_rejects_non_positive_cells(bad):
    with pytest.raises(SystemExit) as e:
        main(["--cells", bad])
    assert e.value.code == 2

def test_matplotlib_flag_writes_png(tmp_path, capsys):
    pytest.importorskip("matplotlib")
    out = tmp_path / "x.png"
    assert main(["--cells", "4", "--matplotlib", "--output", str(out)]) == 0
    assert out.exists() and f"Wrote {out}" in capsys.readouterr().out
```

The subprocess test runs from the repo root, so `fssp` is importable there.

- [ ] **Step 2: Run the tests** with `python -m pytest tests/test_cli.py -v`. Expected: they FAIL with an import error.
- [ ] **Step 3: Implement `fssp/cli.py` and `fssp/__main__.py`, and write `README.md`.**
- [ ] **Step 4: Run the full suite** with `python -m pytest tests/ -v`. Expected: all PASS.
- [ ] **Step 5: Smoke test by hand.**
  - Run `python -m fssp --cells 12`. Expected: a coloured grid with 23 rows and `SUCCESS ... t=22`.
  - Run `python -m fssp --cells 30 --matplotlib`. Expected: `Wrote firing_squad.png` followed by `SUCCESS`.
- [ ] **Step 6: Commit** with `git add -A && git commit -m "feat: CLI with text/matplotlib output and verdict"`
