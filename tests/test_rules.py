import pytest
from fssp.rules import RuleSet, BOUNDARY

def make(rules=None, **kw):
    args = dict(name="t", states=("G", "Q", "F"), general="G", quiescent="Q", fire="F",
                rules=rules or {})
    args.update(kw)
    return RuleSet(**args)

def test_boundary_marker():
    assert BOUNDARY == "#"

def test_builtins_present():
    eff = make().effective_rules()
    assert eff[("Q", "Q", "Q")] == "Q"
    assert eff[("Q", "Q", "#")] == "Q"

def test_explicit_rule_overrides_builtin():
    assert make({("Q", "Q", "Q"): "G"}).effective_rules()[("Q", "Q", "Q")] == "G"

@pytest.mark.parametrize("kw", [
    dict(general="X"),                    # special state not in states
    dict(fire="G"),                       # general/quiescent/fire not distinct
    dict(states=("G", "Q", "F", "#")),    # boundary used as a state
    dict(states=("G", "Q", "F", "G")),    # duplicate state
])
def test_invalid_declarations(kw):
    with pytest.raises(ValueError):
        make(**kw)

@pytest.mark.parametrize("rules", [
    {("#", "G", "Q"): "Z"},   # output not a declared state  (Review Focus 3)
    {("#", "Z", "Q"): "F"},   # key uses an undeclared state
    {("G", "#", "Q"): "F"},   # boundary in the centre position
])
def test_invalid_rules_name_the_entry(rules):
    with pytest.raises(ValueError, match="Z|#"):
        make(rules)
