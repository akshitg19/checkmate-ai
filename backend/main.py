from fastapi import FastAPI, HTTPException
from schemas import (
    CheckRequest,
    CheckResponse,
    HintRequest,
    HintResponse,
    TranscribeRequest,
    TranscribeResponse,
)
from transcription import transcribe_line
from hints import generate_hint
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
        text, unreadable = transcribe_line(req.image_base64)
    except Exception as e:
        # Auth expiry, network failure, quota -- surface as a gateway error
        # the frontend can show, instead of an opaque 500.
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e}")
    return TranscribeResponse(text=text, unreadable=unreadable)

@app.post("/hint", response_model=HintResponse)
def hint(req: HintRequest):
    try:
        return generate_hint(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))