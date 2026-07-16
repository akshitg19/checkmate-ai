from pydantic import BaseModel


class Step(BaseModel):
    line_number: int
    latex: str  # e.g. "3x - 12 = 2x + 5"


class CheckRequest(BaseModel):
    problem: str          # original problem, e.g. "3(x - 4) = 2x + 5"
    steps: list[Step]     # every line the student has written so far


class LineVerdict(BaseModel):
    line_number: int
    valid: bool
    error_type: str | None = None   # "algebraic", "arithmetic", "parse_error"
    detail: str | None = None       # machine detail, NOT student-facing


class CheckResponse(BaseModel):
    verdicts: list[LineVerdict]
    first_wrong_line: int | None = None