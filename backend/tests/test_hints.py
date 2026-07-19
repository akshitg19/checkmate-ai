import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hints import generate_hint
from schemas import HintRequest, Step

STEPS = [
    Step(line_number=1, latex="3x - 12 = 2x + 5"),
    Step(line_number=2, latex="3x = 2x - 7"),
]

KNOWN_CATEGORIES = ["algebraic", "parse_error", "arithmetic", "sign", "division", "distribution", "unsupported"]


@pytest.mark.parametrize("level", [1, 2, 3])
@pytest.mark.parametrize("error_type", KNOWN_CATEGORIES + [None, "some_future_category"])
def test_generate_hint_returns_nonempty_text(level, error_type):
    req = HintRequest(steps=STEPS, line_number=2, error_type=error_type, level=level)
    resp = generate_hint(req)
    assert resp.level == level
    assert resp.max_level == 3
    assert isinstance(resp.hint, str) and resp.hint.strip()


@pytest.mark.parametrize("level", [1, 2, 3])
def test_hints_never_mention_the_solution_content(level):
    """Structural no-leak check: hint text must never contain any token
    from the student's actual equations, since a template that only sees
    line_number + error_type category has no solution data to leak.
    """
    req = HintRequest(steps=STEPS, line_number=2, error_type="algebraic", level=level)
    hint_text = generate_hint(req).hint.lower()
    leaked_tokens = ["3x", "2x", "-12", "+5", "-7"]
    for token in leaked_tokens:
        assert token not in hint_text


def test_level_1_points_to_the_flagged_line_only():
    req = HintRequest(steps=STEPS, line_number=2, error_type="algebraic", level=1)
    hint_text = generate_hint(req).hint
    assert "2" in hint_text  # references line_number
    for token in ["3x", "2x", "-7", "="]:
        assert token not in hint_text


@pytest.mark.parametrize("level", [0, 4, -1])
def test_invalid_level_raises(level):
    req = HintRequest(steps=STEPS, line_number=2, error_type="algebraic", level=level)
    with pytest.raises(ValueError):
        generate_hint(req)


def test_unknown_error_type_falls_back_gracefully():
    req = HintRequest(steps=STEPS, line_number=2, error_type="totally_made_up", level=2)
    resp = generate_hint(req)
    assert resp.hint.strip()
