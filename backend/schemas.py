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
    # One of: "sign", "arithmetic", "division", "distribution",
    # "algebraic", "parse_error", "unsupported"
    error_type: str | None = None
    detail: str | None = None       # machine detail, NOT student-facing


class CheckResponse(BaseModel):
    verdicts: list[LineVerdict]
    first_wrong_line: int | None = None

class TranscribeRequest(BaseModel):
    image_base64: str  # PNG, base64-encoded, no data-URL prefix


class TranscribeResponse(BaseModel):
    text: str
    unreadable: bool = False  # model could not read the line at all


# NEVER pass LineVerdict.detail into a HintRequest -- it's machine-only
# (per LineVerdict's comment above) and may contain solved values.
class HintRequest(BaseModel):
    steps: list[Step]       # full step history, for line-context in level-1 hints
    line_number: int        # the flagged line, from LineVerdict.line_number
    error_type: str | None  # from LineVerdict.error_type
    level: int               # 1, 2, or 3


class HintResponse(BaseModel):
    level: int
    hint: str
    max_level: int = 3