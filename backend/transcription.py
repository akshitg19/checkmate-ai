import base64
import binascii
import os

from google import genai
from google.auth.exceptions import DefaultCredentialsError
from google.genai import errors
from google.genai import types

DEFAULT_PROJECT = "cs-sail-2b08"
DEFAULT_LOCATION = "us-central1"
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

PROMPT = (
    "This image shows one line of a student's handwritten math work. "
    "Transcribe it as a plain-text math expression or equation. "
    "Use standard notation (e.g. x^2, sqrt(x), 3*x). "
    "Reply with ONLY the transcribed math, nothing else. "
    "If the image is blank or unreadable, reply with exactly: UNREADABLE"
)


class TranscriptionInputError(ValueError):
    """The caller supplied an image that cannot be sent for transcription."""


class TranscriptionServiceError(RuntimeError):
    """The external transcription service could not complete the request."""


def _create_client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT", DEFAULT_PROJECT),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_LOCATION),
    )


def _decode_png(image_base64: str) -> bytes:
    try:
        image_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TranscriptionInputError("image_base64 must be valid Base64") from exc

    if not image_bytes.startswith(PNG_SIGNATURE):
        raise TranscriptionInputError("image_base64 must contain a PNG image")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise TranscriptionInputError("PNG image must be 5 MB or smaller")
    return image_bytes


def transcribe_line(image_base64: str) -> str:
    image_bytes = _decode_png(image_base64)
    client = _create_client()
    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                PROMPT,
            ],
        )
    except (errors.APIError, DefaultCredentialsError) as exc:
        raise TranscriptionServiceError("Gemini transcription request failed") from exc

    if not response.text:
        raise TranscriptionServiceError("Gemini returned an empty response")
    return response.text.strip()
