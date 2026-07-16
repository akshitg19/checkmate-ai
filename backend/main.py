from fastapi import FastAPI, HTTPException
from schemas import CheckRequest, CheckResponse, TranscribeRequest, TranscribeResponse
from transcription import (
    TranscriptionInputError,
    TranscriptionServiceError,
    transcribe_line,
)
from judge import AlgebraJudge
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CheckMate API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
judge = AlgebraJudge()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/check", response_model=CheckResponse)
def check_steps(req: CheckRequest):
    verdicts = judge.check(req.problem, req.steps)
    first_wrong = next((v.line_number for v in verdicts if not v.valid), None)
    return CheckResponse(verdicts=verdicts, first_wrong_line=first_wrong)

@app.post("/transcribe", response_model=TranscribeResponse)
def transcribe(req: TranscribeRequest):
    try:
        text = transcribe_line(req.image_base64)
    except TranscriptionInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TranscriptionServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Transcription is temporarily unavailable",
        ) from exc
    return TranscribeResponse(text=text)
