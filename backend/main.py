from fastapi import FastAPI

from judge import AlgebraJudge
from schemas import CheckRequest, CheckResponse
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