from sympy import Add, Eq, Mul, nsimplify, simplify, solve
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


def _parse_structural(text: str):
    """Like _parse_equation but with evaluate=False, preserving written
    structure. SymPy auto-distributes numeric coefficients on normal parse
    (3(x-4) becomes 3x-12 immediately), which erases exactly the
    parenthesized shape the distribution-error check needs to see.
    Returns None if the text can't be parsed this way."""
    try:
        if "=" not in text:
            return parse_expr(text, transformations=TRANSFORMS, evaluate=False)
        lhs, rhs = text.split("=", 1)
        return Eq(
            parse_expr(lhs.strip(), transformations=TRANSFORMS, evaluate=False),
            parse_expr(rhs.strip(), transformations=TRANSFORMS, evaluate=False),
            evaluate=False,
        )
    except Exception:
        return None


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


# ---------------------------------------------------------------------------
# Error classification.
#
# When a step is NOT equivalent to the reference line, we try to name the
# kind of mistake by testing small deterministic "repairs" against the
# reference. If flipping one term's sign makes the step valid, it was a
# sign error; if the step matches a partially-distributed version of the
# reference, it was a distribution error; and so on. Every test is exact
# SymPy computation -- no guessing. If nothing matches, we fall back to
# the generic "algebraic" category rather than inventing a cause.
# ---------------------------------------------------------------------------


def _is_sign_error(ref: Eq, cur: Eq) -> bool:
    """Would flipping the sign of exactly one term in `cur` make it valid?"""
    for side_name in ("lhs", "rhs"):
        side = getattr(cur, side_name)
        other = cur.rhs if side_name == "lhs" else cur.lhs
        for term in Add.make_args(side):
            flipped = side - 2 * term
            candidate = (
                Eq(flipped, other) if side_name == "lhs" else Eq(other, flipped)
            )
            try:
                if _equations_equivalent(ref, candidate):
                    return True
            except Exception:
                continue
    return False


def _is_distribution_error(ref_structural, cur: Eq) -> bool:
    """Does `cur` match the reference with one product distributed into only
    some terms of a parenthesized sum -- e.g. 3(x - 4) copied down as 3x - 4?
    `ref_structural` must be the evaluate=False parse, because normal parsing
    auto-distributes numeric coefficients and destroys the pattern."""
    if ref_structural is None or not isinstance(ref_structural, Eq):
        return False
    ref = ref_structural
    for side_name in ("lhs", "rhs"):
        side = getattr(ref, side_name)
        other = ref.rhs if side_name == "lhs" else ref.lhs
        for node in side.atoms(Mul):
            add_factors = [a for a in node.args if isinstance(a, Add)]
            if len(add_factors) != 1:
                continue
            inner = add_factors[0]
            # Build the coefficient from the remaining factors rather than
            # dividing -- division on evaluate=False trees can misbehave.
            other_factors = [a for a in node.args if a is not inner]
            coeff = Mul(*other_factors) if other_factors else 1
            terms = Add.make_args(inner)
            if len(terms) < 2:
                continue
            # Partial expansions: coeff multiplied into exactly one term,
            # the remaining terms copied down unmultiplied.
            for i in range(len(terms)):
                partial = coeff * terms[i] + Add(
                    *[t for j, t in enumerate(terms) if j != i]
                )
                broken_side = side.xreplace({node: partial})
                candidate = (
                    Eq(broken_side, other)
                    if side_name == "lhs"
                    else Eq(other, broken_side)
                )
                try:
                    if _equations_equivalent(candidate, cur):
                        return True
                except Exception:
                    continue
    return False


def _scaled_offset(ref: Eq, cur: Eq):
    """If d_cur == k * d_ref + c for a nonzero constant c, return (k, c).

    k == 1 means same structure, constant off -> arithmetic slip.
    k != 1 means the step was also scaled -> botched division/multiplication.
    Only attempted for single-variable linear steps, where "leading
    coefficient" is well defined.
    """
    d_ref = simplify(ref.lhs - ref.rhs)
    d_cur = simplify(cur.lhs - cur.rhs)
    syms = d_ref.free_symbols | d_cur.free_symbols
    if len(syms) != 1:
        return None
    x = syms.pop()
    try:
        if not (d_ref.as_poly(x) and d_cur.as_poly(x)):
            return None
        if d_ref.as_poly(x).degree() != 1 or d_cur.as_poly(x).degree() != 1:
            return None
        k = simplify(d_cur.coeff(x, 1) / d_ref.coeff(x, 1))
        c = simplify(d_cur - k * d_ref)
    except Exception:
        return None
    if c.is_constant() and c != 0:
        return (nsimplify(k), nsimplify(c))
    return None


def _classify(ref: Eq, cur: Eq, ref_structural) -> tuple[str, str]:
    """Name the error in `cur` relative to `ref`. Both must be Eq.
    `ref_structural` is the evaluate=False parse of the reference text
    (may be None), used only for the distribution check."""
    if _is_sign_error(ref, cur):
        return (
            "sign",
            "Flipping the sign of one term makes this step equivalent",
        )
    if _is_distribution_error(ref_structural, cur):
        return (
            "distribution",
            "Step matches a partially-distributed version of the reference",
        )
    scaled = _scaled_offset(ref, cur)
    if scaled is not None:
        k, c = scaled
        if k == 1:
            return (
                "arithmetic",
                f"Same structure as reference but off by constant {c}",
            )
        return (
            "division",
            f"Step is scaled by {k} relative to reference with offset {c}",
        )
    return ("algebraic", "Step is not equivalent to previous line")


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

        problem_symbols = (
            reference.free_symbols if hasattr(reference, "free_symbols") else set()
        )
        # Structure-preserving parse of whatever line is currently the
        # reference, for the distribution-error check.
        reference_structural = _parse_structural(problem)

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

            # A step that introduces variables the problem never had is more
            # likely a transcription misread than real math -- surface it as
            # its own category so the UI/hints can react appropriately.
            current_symbols = (
                current.free_symbols if hasattr(current, "free_symbols") else set()
            )
            extra = current_symbols - problem_symbols
            if extra:
                verdicts.append(
                    LineVerdict(
                        line_number=step.line_number,
                        valid=False,
                        error_type="unsupported",
                        detail=f"Uses variable(s) not in the problem: "
                        f"{', '.join(sorted(str(s) for s in extra))}",
                    )
                )
                continue

            # Case 1: both are equations -> check equivalence
            if isinstance(reference, Eq) and isinstance(current, Eq):
                ok = _equations_equivalent(reference, current)
                error_type, detail = (
                    (None, None)
                    if ok
                    else _classify(reference, current, reference_structural)
                )
            # Case 2: both bare expressions (pure arithmetic) -> compare values
            elif not isinstance(reference, Eq) and not isinstance(current, Eq):
                ok = simplify(reference - current) == 0
                error_type, detail = (
                    (None, None)
                    if ok
                    else ("arithmetic", "Value differs from previous line")
                )
            else:
                ok = False
                error_type, detail = (
                    "unsupported",
                    "Equation and bare expression cannot be compared",
                )

            verdicts.append(
                LineVerdict(
                    line_number=step.line_number,
                    valid=ok,
                    error_type=error_type,
                    detail=detail,
                )
            )
            if ok:
                reference = current
                reference_structural = _parse_structural(step.latex)

        return verdicts
