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
