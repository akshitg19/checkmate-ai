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
5. **Cross-platform development environments.** The team develops on both macOS and Windows, so local interpreters and virtual environments are not portable between teammates. Mitigation: standardize on Python 3.11, keep dependencies in `backend/requirements.txt`, and use the platform-specific setup scripts documented in `README.md`.

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

# 12. CheckMate Team Workflow and Task Split

## 1. Git Workflow for a Three-Person Team

Now that three people will be working on the project, nobody should commit directly to `main`.

The `main` branch should only contain finished, working code that has been reviewed through a pull request.

### Branches

Each person should create a branch for the part of the project they are working on.

Example branch names:

```bash
git checkout -b frontend-canvas
git checkout -b backend-judge
git checkout -b ai-transcription
```

When the work is ready:

1. Push the branch to GitHub.
2. Open a pull request into `main`.
3. Have at least one teammate review it.
4. Confirm that the code runs before merging.

The review does not need to be extremely detailed at this stage. The main goal is to have a second person check that the changes make sense and do not break the project.

### Starting Each Work Session

Before beginning new work, update your branch with the latest version of `main`:

```bash
git checkout main
git pull origin main
git checkout your-branch-name
git merge main
```

This reduces the chance of people working on outdated versions of the project for several days.

Do not use only:

```bash
git pull origin main
```

while on a feature branch unless you understand how Git will merge the remote branch into your current branch. Switching to `main`, updating it, and then merging it into your feature branch is easier to understand and keeps the process consistent.

This workflow adds a small amount of overhead now but helps prevent a major merge problem before the demo.

---

# 2. Task Split

The work should be divided by parts of the system rather than having multiple people edit the same files.

The CheckMate pipeline is:

```text
Ink Capture
    ↓
Line Segmentation
    ↓
Transcription
    ↓
Verdict
    ↓
Hint
```

Each person should own a different section of this pipeline.

---

## Person 1 — Frontend and Ink Capture

### Main Responsibilities

Person 1 owns the tablet interface and everything involving stylus input.

Tasks include:

* Building the drawing canvas
* Capturing stylus strokes
* Recording pen position, timing, and pressure
* Displaying the handwriting on the screen
* Grouping strokes into written lines
* Detecting when a line is finished
* Rendering each completed line as a PNG image
* Sending completed lines to the backend
* Underlining incorrect lines
* Displaying transcription results and hints
* Building the overall user interface

### Main Files

Person 1 primarily owns:

```text
frontend/
```

This person should avoid editing backend logic unless a frontend-backend contract needs to change.

### Primary Goal

Make it possible for a student to write on a tablet and send a completed handwritten line through the rest of the system.

---

## Person 2 — Backend and Deterministic Judges

### Main Responsibilities

Person 2 owns the FastAPI backend and the software that determines whether a step is correct.

Tasks include:

* Maintaining the FastAPI application
* Maintaining the `/check` endpoint
* Improving the common judge interface
* Extending algebra support
* Supporting additional equation types
* Testing valid and invalid algebra transformations
* Handling unsupported mathematical steps clearly
* Building the chemistry judge
* Integrating RDKit
* Defining how molecular structures are compared
* Maintaining backend routing

### Main Files

Person 2 primarily owns:

```text
backend/judge/
backend/main.py
```

Changes to `backend/main.py` should be kept small because it connects several parts of the system.

### Primary Goal

Make the verdict system accurate, predictable, and easy to expand from algebra into chemistry.

---

## Person 3 — AI Transcription, Hints, and Testing

### Main Responsibilities

Person 3 owns the parts of the system that use Gemini or another vision model.

Tasks include:

* Building and maintaining the `/transcribe` endpoint
* Sending handwritten line images to Gemini
* Returning structured typed math
* Testing transcription with messy handwriting
* Improving the transcription prompt
* Recording common transcription failures
* Adding confidence or error handling when handwriting cannot be read
* Building the hint-generation endpoint
* Designing the three-level hint ladder
* Ensuring hints do not reveal the answer
* Organizing real-student testing
* Logging problems found during testing

### Main Files

Person 3 primarily owns:

```text
backend/transcription.py
backend/hints.py
```

This person may also own a testing folder such as:

```text
tests/transcription/
```

### Primary Goal

Make handwriting transcription reliable enough for the demo and make hints useful without solving the problem for the student.

---

# 3. Shared Files and Communication

Some files define how the frontend and backend communicate.

For example:

```text
backend/schemas.py
```

This file may contain request and response formats shared across the project.

Everyone may need to read this file, but nobody should change it casually.

Before changing a shared schema, tell the team because the change may affect:

* The frontend request
* The transcription endpoint
* The checker
* The response displayed in the interface

A schema change should usually be made through its own pull request or clearly described in the pull request that requires it.

---

# 4. Week-by-Week Plan

## Week 1 — Complete the Basic Spine

The goal is to make one algebra problem travel through the complete system:

```text
Write
→ Detect Line
→ Transcribe
→ Check
→ Flag
```

### Person 1

* Finish the drawing canvas
* Record stylus strokes
* Add ruled writing rows
* Detect or manually confirm when a line is finished
* Export a finished line as a PNG
* Send the image to `/transcribe`
* Send the returned text to `/check`
* Display the verdict on the correct handwritten line

### Person 2

* Confirm that the current `/check` endpoint is stable
* Add tests for the existing algebra judge
* Improve support for basic one-variable linear equations
* Return clear results for:

  * Correct steps
  * Incorrect steps
  * Unsupported steps
* Document the request and response expected by `/check`

### Person 3

* Confirm that `/transcribe` is running
* Test the endpoint through FastAPI `/docs`
* Test several handwritten math images
* Improve the Gemini prompt
* Return clean, structured transcription output
* Begin collecting examples of handwriting that fails

### End-of-Week Goal

A student can write one supported algebra problem and the app correctly identifies an incorrect line.

---

## Week 2 — Hints and Interface Improvement

The goal is to make the app feel like a tutoring product rather than only a technical test.

### Person 1

* Improve the canvas interface
* Show which line is currently active
* Underline flagged lines clearly
* Add controls for requesting hints
* Display the three hint levels
* Add reset and new-problem controls
* Improve loading and error states

### Person 2

* Continue expanding algebra coverage
* Add more judge tests
* Improve explanations returned by the judge
* Create structured error categories, such as:

  * Sign error
  * Arithmetic error
  * Incorrect division
  * Incorrect distribution
* Ensure the judge returns enough information for hints without returning the answer

### Person 3

* Build the hint endpoint
* Create the three hint levels:

  1. Where to look
  2. What type of mistake occurred
  3. A conceptual explanation
* Test that hints do not reveal the answer
* Add fallback hint templates
* Test transcription with more handwriting samples

### End-of-Week Goal

The algebra workflow works end to end and a student can request increasingly detailed hints for a flagged line.

---

## Week 3 — Chemistry and Student Testing

The goal is to add one narrow chemistry demonstration and test the application with real users.

### Person 1

* Add any drawing tools needed for chemistry
* Make molecular structures easy to draw
* Ensure the canvas handles lines, letters, and bonds
* Connect chemistry drawings to the transcription or recognition endpoint
* Display chemistry verdicts in the interface

### Person 2

* Build the chemistry judge
* Integrate RDKit
* Define a narrow set of supported molecule types
* Compare expected and submitted structures
* Detect simple issues such as:

  * Missing atoms
  * Incorrect bonds
  * Incorrect connectivity
* Add tests for the rehearsed chemistry examples

### Person 3

* Test recognition of hand-drawn molecular structures
* Integrate or test MolScribe if needed
* Organize a test session with approximately five students
* Record:

  * Incorrect line segmentation
  * Incorrect transcription
  * Slow responses
  * Confusing hints
  * Interface problems
* Create a prioritized list of failures to fix

### End-of-Week Goal

The app reliably demonstrates algebra and has at least one narrow chemistry example that works under controlled conditions.

---

## Week 4 — Bug Fixing and Demo Preparation

The goal is stability, not new features.

Everyone should stop adding major functionality by approximately the middle of the week.

### Person 1

* Fix interface bugs
* Improve tablet responsiveness
* Test on iPad and Samsung if available
* Improve the visual presentation
* Practice the exact demo flow

### Person 2

* Fix judge errors
* Improve handling of unsupported problems
* Confirm all demo problems return the expected verdicts
* Add regression tests for previously fixed bugs

### Person 3

* Fix transcription failures
* Improve prompt reliability
* Reduce confusing hints
* Test API latency
* Prepare backup handwriting images or typed inputs in case live transcription fails

### Team Tasks

* Select the exact demo problems
* Rehearse the presentation
* Test the project from a clean startup
* Write setup instructions
* Confirm all environment variables are documented
* Confirm the app works from the presentation device
* Prepare a fallback recorded demo
* Freeze major feature development

### End-of-Week Goal

The application works consistently for the planned demonstration and the team knows how to recover if one part fails live.

---

# 5. Suggested Branches

The team can begin with these branches:

### Person 1

```bash
git checkout -b frontend-canvas
```

### Person 2

```bash
git checkout -b backend-judge
```

### Person 3

```bash
git checkout -b ai-transcription
```

After those branches are merged, create smaller branches for later tasks, such as:

```text
frontend-hints
frontend-chemistry
judge-algebra-expansion
judge-chemistry
ai-hints
transcription-testing
demo-bugfixes
```

Branches should focus on one clear piece of work rather than remaining open for the entire project.

---

# 6. Pull Request Expectations

Every pull request should include:

* What was changed
* Why it was changed
* How to run or test it
* Any files or behavior that may affect teammates
* A screenshot or example response when relevant

A simple pull request description could look like:

```text
Added canvas stroke capture and PNG export.

How to test:
1. Run the frontend.
2. Draw inside the canvas.
3. Press Finish Line.
4. Confirm that a PNG preview appears.

This does not yet call the transcription endpoint.
```

At least one teammate should confirm that the pull request runs before it is merged.

---

# 7. Ownership Section for PROJECT_NOTES.md

Add the following section to `PROJECT_NOTES.md`:

## Ownership

### Person 1 — Frontend and Ink

Owns:

```text
frontend/
```

Responsibilities:

* Canvas
* Stylus capture
* Segmentation
* PNG export
* User interface
* Displaying verdicts and hints

### Person 2 — Backend and Judges

Owns:

```text
backend/judge/
backend/main.py
```

Responsibilities:

* FastAPI routing
* Algebra judge
* Chemistry judge
* SymPy
* RDKit
* Judge testing

### Person 3 — AI and Testing

Owns:

```text
backend/transcription.py
backend/hints.py
tests/transcription/
```

Responsibilities:

* Gemini transcription
* Prompt testing
* Hint generation
* Handwriting failure analysis
* Student testing

### Shared Files

Shared files such as:

```text
backend/schemas.py
README.md
PROJECT_NOTES.md
```

should not be changed without notifying the rest of the team.

---

# 8. Immediate Next Steps

Before starting additional feature work:

1. Make sure nobody is committing directly to `main`.
2. Make sure each person creates their own branch.
3. Add the ownership section to `PROJECT_NOTES.md`.
4. Confirm that `/transcribe` appears in FastAPI `/docs`.
5. Test `/transcribe` with one sample image.
6. Connect the frontend PNG export to `/transcribe`.
7. Connect the transcription result to `/check`.
8. Get one complete algebra example working before expanding the scope.

The highest-priority objective is still the project spine:

```text
Stroke in
→ Transcription
→ Verdict out
```

Everything else should come after that works.
