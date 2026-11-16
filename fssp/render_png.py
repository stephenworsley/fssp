"""Render a simulation history as a PNG image with matplotlib."""
from collections.abc import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


def render_png(history: np.ndarray, state_names: Sequence[str], path: str) -> None:
    k = len(state_names)
    base = plt.get_cmap("tab10" if k <= 10 else "tab20").colors
    colours = [base[i % len(base)] for i in range(k)]
    cmap = ListedColormap(colours)

    steps, n = history.shape
    fig, ax = plt.subplots(figsize=(max(4, n * 0.25 + 2), max(3, steps * 0.2 + 1)))
    ax.imshow(history, cmap=cmap, vmin=-0.5, vmax=k - 0.5,
              interpolation="nearest", aspect="auto", origin="upper")
    ax.set_xlabel("cell")
    ax.set_ylabel("time step")
    handles = [Patch(color=colours[i], label=name) for i, name in enumerate(state_names)]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1), title="states")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
