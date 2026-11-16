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
