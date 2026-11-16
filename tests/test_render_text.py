import re
import numpy as np
from fssp.render_text import render_text

H = np.array([[0, 1, 1], [2, 2, 2]])
NAMES = ("G", "Q", "F")
ANSI = re.compile(r"\033\[[0-9;]*m")

RED = re.compile(r"\033\[(?:[0-9]*;)*(?:31|91)m")

def test_plain_layout():
    assert render_text(H, NAMES, color=False) == "states: G Q F\n0 | G Q Q\n1 | F F F"

def test_colour_codes_by_state_index():
    out = render_text(H, NAMES)
    assert "\033[32mG\033[0m" in out and "\033[33mQ\033[0m" in out and "\033[34mF\033[0m" in out
    assert not RED.search(out)
    assert ANSI.sub("", out) == render_text(H, NAMES, color=False)

def test_fire_bold_red_and_quiescent_concealed():
    out = render_text(H, NAMES, fire="F", quiescent="Q")
    legend, *grid = out.splitlines()
    assert grid[0] == "0 | \033[32mG\033[0m \033[8mQ\033[0m \033[8mQ\033[0m"
    assert grid[1] == "1 | " + " ".join(["\033[1;31mF\033[0m"] * 3)
    assert legend == "states: \033[32mG\033[0m Q \033[1;31mF\033[0m"
    assert ANSI.sub("", out) == render_text(H, NAMES, color=False)

def test_fire_is_the_only_red_state():
    names = tuple(f"S{k}" for k in range(12))
    history = np.arange(12).reshape(1, 12)
    out = render_text(history, names, fire="S11", quiescent="S0")
    assert len(RED.findall(out)) == 2
    assert all(m.group() == "\033[1;31m" for m in RED.finditer(out))

def test_time_column_width_and_multichar_names():
    out = render_text(np.zeros((11, 2), dtype=int), ("Gen", "Q"), color=False).splitlines()
    assert out[1] == " 0 | Gen Gen" and out[11] == "10 | Gen Gen"
