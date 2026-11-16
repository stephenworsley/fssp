"""Render a simulation history as (optionally ANSI-coloured) terminal text."""
from collections.abc import Sequence

import numpy as np

COLOURS = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]


def render_text(history: np.ndarray, state_names: Sequence[str], color: bool = True) -> str:
    def paint(k: int, text: str) -> str:
        if not color:
            return text
        return f"\033[{COLOURS[k % len(COLOURS)]}m{text}\033[0m"

    cell_w = max(len(s) for s in state_names)
    cells = [paint(k, s.ljust(cell_w)) for k, s in enumerate(state_names)]
    lines = ["states: " + " ".join(paint(k, s) for k, s in enumerate(state_names))]
    w = len(str(len(history) - 1))
    for t, row in enumerate(history.tolist()):
        lines.append(f"{t:>{w}} | " + "".join(cells[s] for s in row))
    return "\n".join(lines)
