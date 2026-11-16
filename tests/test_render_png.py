import numpy as np
import pytest
pytest.importorskip("matplotlib")
from fssp.render_png import render_png, state_colours

def test_writes_png(tmp_path):
    out = tmp_path / "run.png"
    render_png(np.array([[0, 1], [2, 2]]), ("G", "Q", "F"), str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

def test_quiescent_white_and_fire_red():
    from matplotlib.colors import to_rgb
    colours = state_colours(("G", "Q", "F"), fire="F", quiescent="Q")
    assert to_rgb(colours[1]) == (1.0, 1.0, 1.0)
    assert to_rgb(colours[2]) == (1.0, 0.0, 0.0)
    assert colours[0] == state_colours(("G", "Q", "F"))[0]

def test_fire_and_quiescent_kwargs_accepted(tmp_path):
    out = tmp_path / "run.png"
    render_png(np.array([[0, 1], [2, 2]]), ("G", "Q", "F"), str(out), fire="F", quiescent="Q")
    assert out.exists()
