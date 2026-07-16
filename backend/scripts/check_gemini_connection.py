"""Manual Vertex AI connectivity check.

This script makes a real network request and may consume project quota. It is
intentionally kept outside the automated test suite.
"""

import os

from google import genai


def main() -> None:
    client = genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "cs-sail-2b08"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents="Reply with exactly the word: working",
    )
    result = (response.text or "").strip()
    if result.lower() != "working":
        raise RuntimeError(f"Unexpected Gemini response: {result!r}")
    print(result)


if __name__ == "__main__":
    main()
