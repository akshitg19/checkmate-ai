import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from judge import AlgebraJudge
from schemas import Step

judge = AlgebraJudge()


def check(problem, *lines):
    steps = [Step(line_number=i + 1, latex=t) for i, t in enumerate(lines)]
    return judge.check(problem, steps)


# --- valid work ---------------------------------------------------------

def test_valid_two_step_solution():
    v = check("3x - 12 = 2x + 5", "3x = 2x + 17", "x = 17")
    assert all(x.valid for x in v)


def test_valid_rearranged_but_equivalent():
    v = check("3x - 12 = 2x + 5", "x - 17 = 0", "x = 17")
    assert all(x.valid for x in v)


def test_valid_scaled_equation_is_equivalent():
    # multiplying both sides by 2 preserves the solution set
    v = check("x - 3 = 0", "2x - 6 = 0")
    assert v[0].valid


def test_bare_arithmetic_valid():
    v = check("7 + 5", "12")
    assert v[0].valid


# --- error classification ----------------------------------------------

def test_sign_error():
    # correct: 3x = 2x + 17; student flipped the constant's sign
    v = check("3x - 12 = 2x + 5", "3x = 2x - 17")
    assert not v[0].valid
    assert v[0].error_type == "sign"


def test_sign_error_on_variable_term():
    v = check("3x - 12 = 2x + 5", "-3x = 2x + 17")
    assert not v[0].valid
    assert v[0].error_type == "sign"


def test_arithmetic_error():
    # correct: 3x = 2x + 17; student wrote +7 (12+5 miscomputed)
    v = check("3x - 12 = 2x + 5", "3x = 2x + 7")
    assert not v[0].valid
    assert v[0].error_type == "arithmetic"


def test_division_error():
    # 2x = 6 -> student "divided" only the left side
    v = check("2x = 6", "x = 6")
    assert not v[0].valid
    assert v[0].error_type == "division"


def test_distribution_error():
    # 3(x - 4) copied down as 3x - 4
    v = check("3(x - 4) = 2x + 5", "3x - 4 = 2x + 5")
    assert not v[0].valid
    assert v[0].error_type == "distribution"


def test_distribution_with_sign_slip_reported_as_sign():
    # student distributed but wrote +12: one sign flip away from correct
    v = check("3(x - 4) = 2x + 5", "3x + 12 = 2x + 5")
    assert not v[0].valid
    assert v[0].error_type == "sign"


def test_bare_arithmetic_wrong_value():
    v = check("7 + 5", "13")
    assert not v[0].valid
    assert v[0].error_type == "arithmetic"


def test_unrelated_garbage_falls_back_to_algebraic():
    v = check("3x - 12 = 2x + 5", "5x = 40")
    assert not v[0].valid
    assert v[0].error_type in ("algebraic", "arithmetic", "division")


# --- structural failures ------------------------------------------------

def test_parse_error():
    v = check("3x - 12 = 2x + 5", "3x ++ = 5")
    assert not v[0].valid
    assert v[0].error_type == "parse_error"


def test_new_variable_flagged_unsupported():
    # z was never in the problem -- likely a transcription misread of x
    v = check("3x - 12 = 2x + 5", "3z = 2z + 17")
    assert not v[0].valid
    assert v[0].error_type == "unsupported"
    assert "z" in v[0].detail


def test_expression_vs_equation_mismatch():
    v = check("3x - 12 = 2x + 5", "3x")
    assert not v[0].valid
    assert v[0].error_type == "unsupported"


def test_unparseable_problem():
    v = judge.check("][", [Step(line_number=1, latex="x = 1")])
    assert v[0].error_type == "parse_error"
    assert v[0].line_number == 0


# --- cascade behavior ---------------------------------------------------

def test_wrong_step_does_not_cascade():
    # line 1 wrong, but line 2 correctly follows from the ORIGINAL problem
    v = check("3x - 12 = 2x + 5", "3x = 2x + 7", "3x = 2x + 17", "x = 17")
    assert not v[0].valid
    assert v[1].valid
    assert v[2].valid


def test_valid_step_becomes_new_reference():
    # line 2 follows from line 1, not directly from the problem statement
    v = check("3x - 12 = 2x + 5", "x - 17 = 0", "x = 17")
    assert v[0].valid and v[1].valid
