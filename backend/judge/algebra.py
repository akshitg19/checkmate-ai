from sympy import Eq, simplify, sympify
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from schemas import LineVerdict, Step
from .base import Judge

TRANSFORMS = standard_transformations + (implicit_multiplication_application,)


def _parse_equation(text: str):
    """Parse 'lhs = rhs' into a SymPy Eq. Raises on failure."""
    if "=" not in text:
        # bare expression (arithmetic like "7 + 5" or a final value "12")
        return parse_expr(text, transformations=TRANSFORMS)
    lhs, rhs = text.split("=", 1)
    return Eq(
        parse_expr(lhs.strip(), transformations=TRANSFORMS),
        parse_expr(rhs.strip(), transformations=TRANSFORMS),
    )


def _equations_equivalent(eq1, eq2) -> bool:
    """Two equations are equivalent if they have the same solution set.

    Check: (lhs1 - rhs1) and (lhs2 - rhs2) are scalar multiples of each other.
    """
    diff1 = simplify(eq1.lhs - eq1.rhs)
    diff2 = simplify(eq2.lhs - eq2.rhs)

    if diff1 == 0 and diff2 == 0:
        return True
    if diff1 == 0 or diff2 == 0:
        return False

    ratio = simplify(diff1 / diff2)
    return ratio.is_constant() and ratio != 0


class AlgebraJudge(Judge):
    def check(self, problem: str, steps: list[Step]) -> list[LineVerdict]:
        verdicts: list[LineVerdict] = []

        try:
            reference = _parse_equation(problem)
        except Exception as e:
            return [
                LineVerdict(
                    line_number=0,
                    valid=False,
                    error_type="parse_error",
                    detail=f"Could not parse problem: {e}",
                )
            ]

        # Each valid step becomes the new reference; invalid steps don't,
        # so one mistake doesn't cascade false errors down every later line.
        for step in steps:
            try:
                current = _parse_equation(step.latex)
            except Exception as e:
                verdicts.append(
                    LineVerdict(
                        line_number=step.line_number,
                        valid=False,
                        error_type="parse_error",
                        detail=str(e),
                    )
                )
                continue

            # Case 1: both are equations -> check equivalence
            if isinstance(reference, Eq) and isinstance(current, Eq):
                ok = _equations_equivalent(reference, current)
            # Case 2: both bare expressions (pure arithmetic) -> compare values
            elif not isinstance(reference, Eq) and not isinstance(current, Eq):
                ok = simplify(reference - current) == 0
            else:
                ok = False

            verdicts.append(
                LineVerdict(
                    line_number=step.line_number,
                    valid=ok,
                    error_type=None if ok else "algebraic",
                    detail=None if ok else "Step is not equivalent to previous line",
                )
            )
            if ok:
                reference = current

        return verdicts