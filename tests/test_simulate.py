import pytest
from fssp.rules import RuleSet
from fssp.simulate import (simulate, default_max_steps, MissingRule,
                           PARTIAL_FIRE, MISSING_RULE, TOO_FAST, TIMEOUT)

def rs(rules, states=("G", "Q", "F")):
    return RuleSet("t", states, "G", "Q", "F", rules)

# Solves n=2 in exactly 2n-2 = 2 steps.
TWO_CELL = rs({("#", "G", "Q"): "X", ("G", "Q", "#"): "X",
               ("#", "X", "X"): "F", ("X", "X", "#"): "F"}, states=("G", "Q", "F", "X"))

def test_default_max_steps():
    assert default_max_steps(20) == 70

def test_success():
    r = simulate(TWO_CELL, 2)
    assert r.success and r.failures == () and r.final_step == 2 and r.min_time == 2
    assert r.fired_cells == (0, 1)
    names = r.state_names
    assert [[names[s] for s in row] for row in r.history.tolist()] == [["G", "Q"], ["X", "X"], ["F", "F"]]

def test_partial_fire_stops_immediately():
    r = simulate(rs({("#", "G", "Q"): "F", ("G", "Q", "Q"): "Q"}), 4)
    assert r.final_step == 1 and r.history.shape == (2, 4)
    assert r.fired_cells == (0,)
    assert r.failures == (PARTIAL_FIRE, TOO_FAST)

def test_empty_table_cannot_fake_success():
    # anti-goal: every cell misses a rule and fires together at t=1
    r = simulate(rs({}), 2)
    assert not r.success and r.fired_cells == (0, 1)
    assert r.failures == (MISSING_RULE, TOO_FAST)
    assert r.missing_rules == (MissingRule(1, 0, ("#", "G", "Q")), MissingRule(1, 1, ("G", "Q", "#")))

def test_empty_table_larger_n_builtins_keep_rest_quiet():
    r = simulate(rs({}), 5)
    assert r.fired_cells == (0, 1)
    assert r.failures == (PARTIAL_FIRE, MISSING_RULE, TOO_FAST)

STUCK = rs({("#", "G", "Q"): "G", ("G", "Q", "Q"): "Q", ("G", "Q", "#"): "Q"})

def test_timeout_default_limit():
    r = simulate(STUCK, 3)
    assert r.failures == (TIMEOUT,) and r.final_step == 19 and r.history.shape == (20, 3)

@pytest.mark.parametrize("limit", [0, 1])           # Review Focus 4
def test_timeout_small_limit(limit):
    r = simulate(STUCK, 3, max_steps=limit)
    assert r.failures == (TIMEOUT,) and r.history.shape == (limit + 1, 3)

@pytest.mark.parametrize("n,limit", [(0, None), (-1, None), (3, -1)])
def test_bad_arguments(n, limit):
    with pytest.raises(ValueError):
        simulate(STUCK, n, max_steps=limit)
