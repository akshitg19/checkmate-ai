import base64

from google import genai
from google.genai import types

_client = genai.Client(
    vertexai=True,
    project="cs-sail-2b08",
    location="us-central1",
)

PROMPT = (
    "This image shows one line of a student's handwritten math work. "
    "Transcribe it as a plain-text math expression or equation. "
    "Use standard notation (e.g. x^2, sqrt(x), 3*x). "
    "Reply with ONLY the transcribed math, nothing else. "
    "If the image is blank or unreadable, reply with exactly: UNREADABLE"
)


def transcribe_line(image_base64: str) -> str:
    image_bytes = base64.b64decode(image_base64)
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            PROMPT,
        ],
    )
    return response.text.strip()