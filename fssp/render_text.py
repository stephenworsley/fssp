"""Render a simulation history as (optionally ANSI-coloured) terminal text."""
from collections.abc import Sequence

import numpy as np

# Red is reserved for the fire state.
COLOURS = [32, 33, 34, 35, 36, 92, 93, 94, 95, 96]
FIRE_STYLE = "1;31"
# SGR 8 (conceal) draws the text in the background colour.
QUIESCENT_STYLE = "8"


def render_text(history: np.ndarray, state_names: Sequence[str], color: bool = True,
                fire: str | None = None, quiescent: str | None = None) -> str:
    def style(k: int) -> str:
        if state_names[k] == fire:
            return FIRE_STYLE
        if state_names[k] == quiescent:
            return QUIESCENT_STYLE
        return str(COLOURS[k % len(COLOURS)])

    def paint(code: str | None, text: str) -> str:
        if not color or code is None:
            return text
        return f"\033[{code}m{text}\033[0m"

    def legend_style(k: int) -> str | None:
        return None if state_names[k] == quiescent else style(k)

    cell_w = max(len(s) for s in state_names)
    cells = [paint(style(k), s.ljust(cell_w)) for k, s in enumerate(state_names)]
    lines = ["states: " + " ".join(paint(legend_style(k), s) for k, s in enumerate(state_names))]
    w = len(str(len(history) - 1))
    for t, row in enumerate(history.tolist()):
        lines.append(f"{t:>{w}} | " + " ".join(cells[s] for s in row))
    return "\n".join(lines)
