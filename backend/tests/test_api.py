from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from transcription import TranscriptionInputError, TranscriptionServiceError


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_check_accepts_equivalent_steps() -> None:
    response = client.post(
        "/check",
        json={
            "problem": "3(x - 4) = 2x + 5",
            "steps": [
                {"line_number": 1, "latex": "3x - 12 = 2x + 5"},
                {"line_number": 2, "latex": "x = 17"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["first_wrong_line"] is None
    assert all(item["valid"] for item in response.json()["verdicts"])


def test_check_reports_first_wrong_line() -> None:
    response = client.post(
        "/check",
        json={
            "problem": "3(x - 4) = 2x + 5",
            "steps": [{"line_number": 1, "latex": "3x - 12 = 2x - 5"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["first_wrong_line"] == 1
    assert response.json()["verdicts"][0]["valid"] is False


@patch("main.transcribe_line", return_value="3*x - 12 = 2*x + 5")
def test_transcribe_contract(mock_transcribe) -> None:
    response = client.post("/transcribe", json={"image_base64": "mock-image"})

    assert response.status_code == 200
    assert response.json() == {"text": "3*x - 12 = 2*x + 5"}
    mock_transcribe.assert_called_once_with("mock-image")


@patch("main.transcribe_line", side_effect=TranscriptionInputError("invalid PNG"))
def test_transcribe_maps_bad_input_to_422(_mock_transcribe) -> None:
    response = client.post("/transcribe", json={"image_base64": "bad"})

    assert response.status_code == 422
    assert response.json() == {"detail": "invalid PNG"}


@patch("main.transcribe_line", side_effect=TranscriptionServiceError("offline"))
def test_transcribe_hides_service_error(_mock_transcribe) -> None:
    response = client.post("/transcribe", json={"image_base64": "valid"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Transcription is temporarily unavailable"}
