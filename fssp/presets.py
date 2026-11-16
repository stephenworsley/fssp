"""Named rule sets.

MAZOYER is Mazoyer's 6-state minimal-time solution. Its transition table is
transcribed from hediet/lean-cellular-automata
(CellularAutomatas/proofs/constructions/fssp_mazoyer/ca.lean), which is ported
from the Coq formal proof in rocq-archive/firing-squad (autom.v).

To add a preset, build a RuleSet and register it in PRESETS.
"""
from fssp.rules import BOUNDARY, RuleSet

ORDER = "ABCLGF"
_T = {
    "TAA": "ABCABF", "TBA": "FGCGCF", "TLA": "ALGAFF", "TAB": "BBLGFF",
    "TBB": "ABCGBF", "TCB": "AFFLLF", "TLB": "GBLFBF", "TGB": "CFBCGF",
    "TBC": "FFCCGF", "TCC": "ABCCBF", "TLC": "AGCCGF", "TAL": "LLLGCF",
    "TCL": "LLLAGF", "TGL": "LLLCAF", "TG_L": "BBAABF", "TG_G": "FGAFFF",
}


def _t(table, x):
    return _T[table][ORDER.index(x)]


def _delta(a, b, c):  # Mazoyer's δ(left, self, right)
    if b == "A":
        return {"A": _t("TAA", c), "B": _t("TBA", c), "C": "A",
                "L": _t("TLA", c), "G": "C", "F": "F"}[a]
    if b == "B":
        return {"A": _t("TAB", c), "B": _t("TBB", c), "C": _t("TCB", c),
                "L": _t("TLB", c), "G": _t("TGB", c), "F": "F"}[a]
    if b == "C":
        return {"A": "B", "B": _t("TBC", c), "C": _t("TCC", c),
                "L": _t("TLC", c), "G": "B", "F": "F"}[a]
    if b == "L":
        return {"A": _t("TAL", c), "B": "L", "C": _t("TCL", c),
                "L": "L", "G": _t("TGL", c), "F": "L"}[a]
    if b == "G":
        return {"L": _t("TG_L", a), "G": _t("TG_G", a)}.get(c, "G")


def _mazoyer_rules():
    # The boundary acts as a phantom neighbour: "L" on the left, "G" on the right.
    neighbours = "ABCLG" + BOUNDARY
    return {
        (a, b, c): _delta("L" if a == BOUNDARY else a, b, "G" if c == BOUNDARY else c)
        for a in neighbours for b in "ABCLG" for c in neighbours
    }


MAZOYER = RuleSet(
    name="mazoyer",
    states=("A", "B", "C", "L", "G", "F"),
    general="G",
    quiescent="L",
    fire="F",
    rules=_mazoyer_rules(),
)

PRESETS: dict[str, RuleSet] = {"mazoyer": MAZOYER}
