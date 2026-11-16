"""Command-line interface: simulate a preset, render it, and report the verdict."""
import argparse

from fssp.presets import PRESETS
from fssp.render_text import render_text
from fssp.simulate import (MISSING_RULE, PARTIAL_FIRE, TIMEOUT, TOO_FAST,
                           SimulationResult, simulate)


def format_verdict(result: SimulationResult) -> str:
    if result.success:
        return (f"SUCCESS: all {result.n} cells fired together at t={result.final_step} "
                f"(minimum possible: {result.min_time}).")
    lines = [f"FAILURE (stopped at t={result.final_step}):"]
    for code in result.failures:
        if code == PARTIAL_FIRE:
            lines.append(f"  - only cells {list(result.fired_cells)} fired, out of {result.n}")
        elif code == MISSING_RULE:
            for m in result.missing_rules:
                lines.append(f"  - no rule for pattern {m.pattern} at cell {m.cell}, "
                             f"t={m.step} (cell fired)")
        elif code == TOO_FAST:
            lines.append(f"  - fired at t={result.final_step}, faster than the minimum "
                         f"possible {result.min_time}; the rule set is broken")
        elif code == TIMEOUT:
            lines.append(f"  - no cell fired within {result.max_steps} steps")
    return "\n".join(lines)


def _int_at_least(minimum: int):
    def parse(text: str) -> int:
        try:
            value = int(text)
        except ValueError:
            raise argparse.ArgumentTypeError(f"invalid integer: {text!r}")
        if value < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}, got {value}")
        return value
    return parse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fssp", description="Simulate a firing squad synchronisation rule set.")
    parser.add_argument("--cells", type=_int_at_least(1), default=20,
                        help="number of cells (default: 20)")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="mazoyer",
                        help="rule set to run (default: mazoyer)")
    parser.add_argument("--max-steps", type=_int_at_least(0), default=None,
                        help="time limit (default: 3 * cells + 10)")
    parser.add_argument("--matplotlib", action="store_true",
                        help="write a PNG image instead of printing text")
    parser.add_argument("--output", default="firing_squad.png",
                        help="PNG path for --matplotlib (default: firing_squad.png)")
    args = parser.parse_args(argv)

    result = simulate(PRESETS[args.preset], args.cells, args.max_steps)
    if args.matplotlib:
        from fssp.render_png import render_png
        render_png(result.history, result.state_names, args.output)
        print(f"Wrote {args.output}")
    else:
        rule_set = PRESETS[args.preset]
        print(render_text(result.history, result.state_names,
                          fire=rule_set.fire, quiescent=rule_set.quiescent))
    print(format_verdict(result))
    return 0 if result.success else 1
