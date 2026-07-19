import base64
import re

from google import genai
from google.genai import types

_client = genai.Client(
    vertexai=True,
    project="cs-sail-2b08",
    location="us-central1",
)

PROMPT = (
    "This image shows one line of a student's handwritten algebra work, "
    "written on ruled notebook paper. Transcribe it as a plain-text math "
    "expression or equation.\n"
    "Rules:\n"
    "- Use only: digits 0-9, lowercase latin letters, + - * / ^ = ( ) . and spaces "
    "(e.g. x^2, sqrt(x), 3*x). Never use Greek letters, LaTeX commands, or $ delimiters.\n"
    "- The paper has printed horizontal ruling lines in the background. These are NOT "
    "part of the student's handwriting. Do not let a ruling line change a handwritten "
    "'=' into '-' or '<='; only ink strokes the student wrote count.\n"
    "- If part of the line is crossed out or scribbled over, ignore the crossed-out part "
    "and transcribe only what remains legible.\n"
    "- Reply with ONLY the transcribed math, nothing else, no markdown or LaTeX formatting.\n"
    "- If the image is blank or truly unreadable, reply with exactly: UNREADABLE"
)

_WRAPPER_RE = re.compile(r"^\$+|\$+$")
# \frac{a}{b} -> (a)/(b), before generic command stripping eats the braces
_FRAC_RE = re.compile(r"\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")
_LATEX_CMD_RE = re.compile(r"\\([a-zA-Z]+)")

# Unicode math the model sometimes emits despite the prompt, mapped to the
# ASCII the SymPy judge can parse. Anything not mapped here that isn't
# plain ASCII math will surface as a parse_error verdict, which is the
# correct failure mode (visible, not silent).
_UNICODE_MAP = str.maketrans({
    "−": "-",   # minus sign
    "–": "-",   # en dash
    "—": "-",   # em dash
    "×": "*",   # multiplication x
    "⋅": "*",   # dot operator
    "·": "*",   # middle dot
    "÷": "/",   # division sign
    "²": "^2",  # superscript two  (via replace below; translate needs 1-char)
    "³": "^3",
})


def _clean(text: str) -> str:
    text = text.strip()
    text = _WRAPPER_RE.sub("", text).strip()
    text = _FRAC_RE.sub(r"(\1)/(\2)", text)
    text = _LATEX_CMD_RE.sub(r"\1", text)
    text = text.replace("²", "^2").replace("³", "^3")
    text = text.translate(_UNICODE_MAP)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transcribe_line(image_base64: str) -> tuple[str, bool]:
    """Returns (text, unreadable). Raises on API/auth failure -- the caller
    (main.py) turns that into an HTTP error instead of a raw 500."""
    image_bytes = base64.b64decode(image_base64)
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            PROMPT,
        ],
        # thinking_budget=0: 2.5 Flash "thinks" by default and thinking tokens
        # bill as output -- pure waste for OCR. max_output_tokens caps a
        # runaway response; one transcribed line is ~15 tokens.
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=64,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    text = _clean(response.text or "")
    unreadable = text == "UNREADABLE" or not text
    return text, unreadable