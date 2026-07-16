# CheckMate: Project Notes

Working doc for the team. Plain language, kept current as decisions change.
Last updated: July 16, 2026.

---

## 1. What we are building

CheckMate is a web app for tablets (iPad and Samsung). A student does their homework on it by writing with a stylus, the same way they would write in a paper notebook or a notes app. As they write, the app checks each line of their work. If a line contains a mistake, the app underlines that line and offers a small hint about where to look. It never shows the answer.

The product exists because current homework apps only check the final answer. Photomath and similar apps give the full solution, which is why schools ban them. Chat tutors like Khanmigo cannot see the student's written work at all. Nobody today can tell a student "your mistake is on line 3, and it is a sign error." That is the gap we fill.

## 2. What makes it different (in one sentence each)

- We see the student's work as they write it, not a photo of it afterward.
- The correctness decision is made by math software that cannot be wrong, not by an AI that can be.
- The AI is only used for two jobs where it is strong: reading handwriting, and writing a friendly hint sentence.
- Hints never contain the answer. This is a product rule, not a technical limitation.

## 3. Known competition and our honest position

Products already exist that check math steps and claim "no hallucinations" (MathPad, Math-Tutor AI on iPad). Both work step by step and use the same class of math-verification software we do. We do not pretend otherwise.

Our differences are:

1. **Live stroke input.** Competitors work from a photo or a finished page. We work from the pen strokes themselves, live, which allows checking while the student writes.
2. **Chemistry.** No shipped product checks hand-drawn molecular structures live. This is our strongest demo moment.
3. **Teacher and parent visibility.** Later features (see roadmap) show which lines a student rewrote and struggled with. No product surfaces that today.

When presenting, lead with points 1 and 2. Do not claim "nobody checks steps," because that claim is false and easy to disprove.

## 4. How the system works, end to end

The pipeline has five stages. Each stage only depends on the one before it.

1. **Ink capture.** The browser records the stylus. A stroke is the set of points the pen touched between touching down and lifting up, with timing and pressure. This works the same on iPad and Samsung because it uses a web standard (Pointer Events), which is the reason we build a web app instead of two native apps.

2. **Line segmentation.** Strokes are grouped into written lines: line 1, line 2, line 3. Rule used: a pen lift followed by a clear vertical gap starts a new line. The interface shows faint ruled lines to encourage writing in rows, which makes this rule reliable. This stage is the highest technical risk in the project.

3. **Transcription.** A finished line is converted to an image and sent to an AI vision model (Claude), which returns the math as text. This is the only place AI touches the student's work, and its only job is reading, not judging.

4. **Verdict.** The transcribed line is checked by deterministic math software. For algebra, SymPy confirms whether the new line really follows from the previous line. For chemistry, RDKit confirms whether a drawn structure has the correct bonds. These tools compute the answer; they do not guess. If the checker says a line is wrong, it is wrong.

5. **Hint.** Only after the checker flags a line, the AI writes one short sentence pointing the student toward the mistake. Three hint levels: where to look, what kind of mistake, and an explanation. The student asks for each level; nothing is volunteered beyond the underline.

## 5. Current state (as of this doc)

Done:
- GitHub repo created (`checkmate-ai`), team added as collaborators.
- Backend running locally: a FastAPI server with two endpoints.
  - `GET /health` confirms the server is up.
  - `POST /check` accepts a problem and a list of written steps, returns a per-line verdict and the first wrong line. Algebra and plain arithmetic are supported through SymPy.
- The judge is written behind a common interface, so adding a chemistry judge later does not require changing the rest of the system.

Not started:
- The frontend (drawing canvas), line segmentation, transcription, hints, chemistry.

## 6. Build order and why

1. **Canvas (next).** A drawing surface in the browser that records strokes. Tested on a real tablet by opening the laptop's local address in the tablet browser over shared WiFi.
2. **Segmentation.** Group strokes into lines and draw faint boxes around each detected line so we can see mistakes in the grouping immediately.
3. **Transcription.** Send each finished line to the vision model, show the returned text next to the handwriting.
4. **Wire to the checker.** Connect transcription output to the existing `/check` endpoint. At this point the full loop works: write, check, flag.
5. **Hints, then chemistry, then polish.**

The verdict stage was built first, out of order, because it was the only stage with zero unknowns and it gives every later stage something real to connect to.

## 7. Technology choices and reasons

| Piece | Choice | Reason |
|---|---|---|
| App | Web app, React, canvas element | One codebase covers iPad and Samsung; no app store; demo by sharing a URL |
| Ink | Pointer Events API | Web standard; gives full stylus data including pressure; pen lift marks line ends |
| Transcription | Claude API (vision), MathPix as fallback | Strokes render to clean images, so accuracy is high without training our own model |
| Verdict | SymPy (algebra), RDKit + MolScribe (chemistry), plain Python (arithmetic) | Deterministic; cannot hallucinate |
| Hints | Claude API with a strict prompt: locate, nudge, never solve | Cheap; one call per flagged line |
| Backend | FastAPI with websockets | Team already knows it; fast to build |
| On-device (stretch) | Qualcomm edge hardware for transcription | Lower latency and privacy; only if weeks 1-6 go well |

## 8. Timeline (8 weeks total, demo-ready spine at week 4)

- **Week 1:** Prove the spine on one problem type: stroke in, verdict out. Nothing else.
- **Week 2:** Hint ladder and the canvas interface.
- **Week 3:** Chemistry judge. Put the app in front of five real students.
- **Week 4:** Polish, latency, demo script. This is the presentation checkpoint.
- **Weeks 5-6:** Expand algebra coverage to precalculus. Begin error-pattern tracking and the teacher/parent replay view.
- **Weeks 7-8:** On-device transcription on the Qualcomm hardware (stretch). Final report and demo. Cut anything not essential.

## 9. Risks, stated plainly

1. **Line segmentation.** Knowing where one written line ends and the next begins in freeform handwriting is the genuinely hard problem. Mitigation: the pen-lift-plus-gap rule, plus ruled lines in the interface that nudge students to write in rows. If week 1 shows this works, the rest of the project is execution.
2. **Handwriting variety.** The transcription model must handle messy real student writing, not just ours. Mitigation: test with deliberately bad handwriting early, and keep MathPix as a fallback reader.
3. **Chemistry recognition.** Reading hand-drawn molecules is an unsolved research problem beyond simple structures. Mitigation: the demo covers a narrow, rehearsed set of structure types, not open-ended organic chemistry.
4. **Latency.** "Checks as you write" requires fast round trips. Mitigation: the app only checks when a line is finished (pen lift), never on every stroke.
5. **Python 3.14 on the dev laptop.** Very new version; some libraries may not have Windows builds yet. Mitigation: if an install fails, add Python 3.12 alongside and point the project at it.

## 10. Product rules (do not violate these)

- The app never shows the answer, at any hint level, under any phrasing.
- The AI never decides whether work is correct. Only the deterministic checker does.
- A wrong line is flagged once and gently. The student fixes it themselves; that is the learning.
- Anything that would make a teacher ban the app is out of scope by definition.

## 11. Glossary

- **Stroke:** the path the stylus draws between touching the screen and lifting off.
- **Segmentation:** deciding which strokes belong to which written line.
- **Transcription:** converting a written line into typed math text.
- **Judge / checker:** the software that decides whether a line is mathematically valid.
- **SymPy:** a Python library that does exact symbolic math. Used to verify algebra steps.
- **RDKit:** a Python library for chemistry. Used to verify molecular structures.
- **Hint ladder:** the three escalating hint levels a student can request for a flagged line.
- **The spine:** shorthand for the minimal end-to-end path: stroke in, verdict out.
