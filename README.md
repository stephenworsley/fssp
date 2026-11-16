# Firing Squad Synchronisation Simulator

Simulates a 1D cellular automaton on the firing squad synchronisation problem, draws
the run, and reports whether the rule set solved it.

## Usage

```bash
pip install -r requirements.txt
python -m fssp --cells 12                 # coloured terminal output
python -m fssp --cells 30 --matplotlib    # writes firing_squad.png
python -m fssp --cells 30 --matplotlib --output run.png
python -m fssp --cells 10 --max-steps 5   # time limit (default: 3 * cells + 10)
```

The exit code is 0 when every cell fires together, using only real rules, no earlier
than the proven minimum of 2n − 2. Otherwise it is 1, and the reasons are listed.

Run the tests with `python -m pytest tests/`.

## Adding a preset

Define a `RuleSet` in [fssp/presets.py](fssp/presets.py) and register it in `PRESETS`:

```python
MY_RULES = RuleSet(
    name="mine",
    states=("G", "Q", "F", "X"),   # order sets the integer code of each state
    general="G", quiescent="Q", fire="F",
    rules={("#", "G", "Q"): "X", ...},   # (left, self, right) -> new state; "#" is the boundary
)
PRESETS["mine"] = MY_RULES
```

`(Q, Q, Q) -> Q` and `(Q, Q, #) -> Q` are built in. A pattern with no rule makes the
cell fire, and the run reports it as a failure.
