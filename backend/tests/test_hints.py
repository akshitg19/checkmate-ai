import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hints import generate_hint
from schemas import HintRequest

KNOWN_CATEGORIES = ["algebraic", "parse_error", "arithmetic", "sign", "division", "distribution", "unsupported"]


@pytest.mark.parametrize("level", [1, 2, 3])
@pytest.mark.parametrize("error_type", KNOWN_CATEGORIES + [None])
def test_generate_hint_returns_nonempty_text(level, error_type):
    req = HintRequest(line_number=2, error_type=error_type, level=level)
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
    req = HintRequest(line_number=2, error_type="algebraic", level=level)
    hint_text = generate_hint(req).hint.lower()
    leaked_tokens = ["3x", "2x", "-12", "+5", "-7"]
    for token in leaked_tokens:
        assert token not in hint_text


def test_level_1_points_to_the_flagged_line_only():
    req = HintRequest(line_number=2, error_type="algebraic", level=1)
    hint_text = generate_hint(req).hint
    assert "2" in hint_text  # references line_number
    for token in ["3x", "2x", "-7", "="]:
        assert token not in hint_text


@pytest.mark.parametrize("level", [0, 4, -1])
def test_invalid_level_is_rejected_by_schema(level):
    with pytest.raises(ValidationError):
        HintRequest(line_number=2, error_type="algebraic", level=level)


def test_unknown_error_type_is_rejected_by_schema():
    with pytest.raises(ValidationError):
        HintRequest(line_number=2, error_type="totally_made_up", level=2)
