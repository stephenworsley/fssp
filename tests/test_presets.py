import pytest
from fssp.presets import PRESETS, MAZOYER
from fssp.simulate import simulate

def test_registry():
    assert PRESETS["mazoyer"] is MAZOYER

@pytest.mark.parametrize("n", range(3, 61))
def test_mazoyer_minimal_time(n):
    r = simulate(MAZOYER, n)
    assert r.success and r.final_step == 2 * n - 2 and r.missing_rules == ()

def test_mazoyer_n1():                                   # Review Focus 2
    r = simulate(MAZOYER, 1)
    assert r.success and r.final_step == 1

def test_mazoyer_n2_fails_cleanly():                     # Review Focus 1
    r = simulate(MAZOYER, 2)
    assert not r.success and r.final_step == 3 and r.fired_cells == (1,)
