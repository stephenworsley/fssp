import numpy as np
import pytest
pytest.importorskip("matplotlib")
from fssp.render_png import render_png

def test_writes_png(tmp_path):
    out = tmp_path / "run.png"
    render_png(np.array([[0, 1], [2, 2]]), ("G", "Q", "F"), str(out))
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
