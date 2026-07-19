import { useRef, useState, useEffect, useCallback } from "react";

const LINE_HEIGHT = 64;
const API_BASE = "http://127.0.0.1:8000";
const LINE_PAD = 16;

// Group strokes into lines by which ruled row each stroke's
// vertical center falls into. Returns a map: rowIndex -> strokes[].
function segmentIntoLines(strokes) {
  const lines = new Map();
  for (const stroke of strokes) {
    let minY = Infinity, maxY = -Infinity;
    for (const pt of stroke.points) {
      if (pt.y < minY) minY = pt.y;
      if (pt.y > maxY) maxY = pt.y;
    }
    const centerY = (minY + maxY) / 2;
    const row = Math.floor(centerY / LINE_HEIGHT);
    if (!lines.has(row)) lines.set(row, []);
    lines.get(row).push(stroke);
  }
  return lines;
}

// Renders one detected line's strokes onto a fresh, tightly-cropped canvas --
// paper background + a single ruled line for context + ink only. Deliberately
// excludes the on-screen segmentation debug overlay (boxes/labels), which is
// for the writer's eyes only and previously leaked into exported PNGs when
// people screenshotted the canvas instead of using a real export path.
function renderLineToPng(lineStrokes) {
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  for (const s of lineStrokes) {
    for (const pt of s.points) {
      if (pt.x < minX) minX = pt.x;
      if (pt.x > maxX) maxX = pt.x;
      if (pt.y < minY) minY = pt.y;
      if (pt.y > maxY) maxY = pt.y;
    }
  }

  const width = maxX - minX + LINE_PAD * 2;
  const height = maxY - minY + LINE_PAD * 2;
  const off = document.createElement("canvas");
  off.width = width;
  off.height = height;
  const ctx = off.getContext("2d");

  ctx.fillStyle = "#faf8f2";
  ctx.fillRect(0, 0, width, height);

  // Same light-blue ruling used on the main canvas, positioned just below
  // the ink so the crop still looks like a line written on ruled paper.
  ctx.strokeStyle = "rgba(120, 150, 190, 0.4)";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, height - LINE_PAD / 2);
  ctx.lineTo(width, height - LINE_PAD / 2);
  ctx.stroke();

  ctx.strokeStyle = "#1a1a2e";
  ctx.lineWidth = 2.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  for (const s of lineStrokes) {
    const pts = s.points;
    if (pts.length < 2) continue;
    ctx.beginPath();
    ctx.moveTo(pts[0].x - minX + LINE_PAD, pts[0].y - minY + LINE_PAD);
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(pts[i].x - minX + LINE_PAD, pts[i].y - minY + LINE_PAD);
    }
    ctx.stroke();
  }

  return off.toDataURL("image/png");
}

export default function App() {
  const canvasRef = useRef(null);
  const [strokes, setStrokes] = useState([]); // finished strokes
  const currentStroke = useRef(null); // stroke in progress
  const [transcribing, setTranscribing] = useState(false);
  const [lastResult, setLastResult] = useState(null); // { text } | { error }

  const [problem, setProblem] = useState("");
  // One entry per finished handwritten line:
  // { row, text, unreadable } -- text is editable in the side panel, so a
  // misread transcription is a one-second typed fix instead of a dead end.
  const [lines, setLines] = useState([]);
  const [verdictsByLine, setVerdictsByLine] = useState(new Map()); // row -> LineVerdict
  const [firstWrongLine, setFirstWrongLine] = useState(null);

  const [hintLevel, setHintLevel] = useState(0); // 0 = no hint requested yet
  const [hintText, setHintText] = useState(null);
  const [hintLoading, setHintLoading] = useState(false);

  const getPoint = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      t: e.timeStamp,
      p: e.pressure,
    };
  };

  const handlePointerDown = (e) => {
    if (e.pointerType === "touch") return; // palm rejection
    canvasRef.current.setPointerCapture(e.pointerId);
    currentStroke.current = { points: [getPoint(e)], pointerType: e.pointerType };
  };

  const handlePointerMove = (e) => {
    if (!currentStroke.current) return;
    const events = e.getCoalescedEvents ? e.getCoalescedEvents() : [e];
    for (const ev of events) {
      currentStroke.current.points.push(getPoint(ev));
    }
    drawFrame();
  };

  const handlePointerUp = () => {
    if (!currentStroke.current) return;
    const finished = currentStroke.current;
    currentStroke.current = null;
    setStrokes((prev) => [...prev, finished]);
  };

  // Lines that can be sent to the judge: have text and were readable
  // (an unreadable line whose text the student typed in counts).
  const toSteps = (lineArr) =>
    lineArr
      .filter((l) => l.text.trim() && l.text !== "UNREADABLE")
      .map((l) => ({ line_number: l.row, latex: l.text }))
      .sort((a, b) => a.line_number - b.line_number);

  // Re-judge the whole page. Free (pure SymPy server-side), so it runs on
  // every finished line and every manual correction.
  const recheck = async (lineArr) => {
    // Any change to the work invalidates the current hint ladder.
    setHintLevel(0);
    setHintText(null);

    const stepList = toSteps(lineArr);
    if (!problem.trim() || stepList.length === 0) {
      setVerdictsByLine(new Map());
      setFirstWrongLine(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem, steps: stepList }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setVerdictsByLine(new Map(data.verdicts.map((v) => [v.line_number, v])));
      setFirstWrongLine(data.first_wrong_line);
    } catch (e) {
      setLastResult({ error: `Check failed: ${e.message}` });
    }
  };

  const handleFinishLine = async () => {
    const segLines = segmentIntoLines(strokes);
    if (segLines.size === 0) return;
    const lastRow = Math.max(...segLines.keys());
    const lineStrokes = segLines.get(lastRow);

    const dataUrl = renderLineToPng(lineStrokes);
    const imageBase64 = dataUrl.split(",")[1]; // strip "data:image/png;base64,"

    setTranscribing(true);
    setLastResult(null);

    let text, unreadable;
    try {
      const res = await fetch(`${API_BASE}/transcribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: imageBase64 }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `${res.status} ${res.statusText}`);
      }
      const data = await res.json();
      text = data.text;
      unreadable = data.unreadable;
    } catch (e) {
      setLastResult({ error: e.message });
      setTranscribing(false);
      return;
    }
    setTranscribing(false);

    // Upsert this line (re-finishing a row replaces its transcription).
    const newLines = [
      ...lines.filter((l) => l.row !== lastRow),
      { row: lastRow, text: unreadable ? "" : text, unreadable },
    ].sort((a, b) => a.row - b.row);
    setLines(newLines);
    await recheck(newLines);
  };

  // Manual correction in the side panel: update text, clear the unreadable
  // flag once the student has typed something, and re-judge.
  const handleLineEdit = (row, newText) => {
    setLines((prev) =>
      prev.map((l) =>
        l.row === row
          ? { ...l, text: newText, unreadable: l.unreadable && !newText.trim() }
          : l
      )
    );
  };

  const handleLineEditDone = () => {
    recheck(lines);
  };

  const handleGetHint = async () => {
    if (firstWrongLine === null || hintLevel >= 3) return;
    const nextLevel = hintLevel + 1;
    const verdict = verdictsByLine.get(firstWrongLine);

    setHintLoading(true);
    try {
      const res = await fetch(`${API_BASE}/hint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          steps: toSteps(lines),
          line_number: firstWrongLine,
          error_type: verdict?.error_type ?? null,
          level: nextLevel,
        }),
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = await res.json();
      setHintLevel(data.level);
      setHintText(data.hint);
    } catch (e) {
      setHintText(`Error: ${e.message}`);
    } finally {
      setHintLoading(false);
    }
  };

  const drawStroke = useCallback((ctx, stroke) => {
    const pts = stroke.points;
    if (pts.length < 2) return;
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      ctx.lineTo(pts[i].x, pts[i].y);
    }
    ctx.stroke();
  }, []);

  const drawFrame = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Ruled lines.
    // Previously drawn in #000000 at lineWidth 3 -- darker and thicker than
    // the ink itself, which made Gemini read the printed ruling as part of
    // the handwriting (e.g. a "=" sign touching the rule line got
    // transcribed as "-" or "<="). Using a light, distinctly-blue tone plus
    // a thinner stroke keeps the ruling visually subordinate to the ink so
    // it reads as background paper, not content.
    // See backend/tests/transcription/failures.md for the failure cases.
    ctx.strokeStyle = "rgba(120, 150, 190, 0.4)";
    ctx.lineWidth = 1;
    for (let y = LINE_HEIGHT; y < canvas.height; y += LINE_HEIGHT) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Ink strokes -- kept dark/opaque so they stay visually dominant over
    // the lighter ruling drawn above.
    ctx.strokeStyle = "#1a1a2e";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    for (const s of strokes) drawStroke(ctx, s);
    if (currentStroke.current) drawStroke(ctx, currentStroke.current);

    // Segmentation debug view: box around each detected line, colored by
    // /check's verdict once one exists -- green for a correct step, red for
    // a flagged one, the original neutral blue for lines not yet checked
    // (no problem set, or this line hasn't been sent to /check yet).
    const lines = segmentIntoLines(strokes);
    ctx.font = "11px sans-serif";
    for (const [row, lineStrokes] of lines) {
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      for (const s of lineStrokes) {
        for (const pt of s.points) {
          if (pt.x < minX) minX = pt.x;
          if (pt.x > maxX) maxX = pt.x;
          if (pt.y < minY) minY = pt.y;
          if (pt.y > maxY) maxY = pt.y;
        }
      }
      const verdict = verdictsByLine.get(row);
      const color =
        verdict === undefined
          ? "rgba(70, 130, 180, 0.8)"   // neutral blue -- not checked
          : verdict.valid
          ? "rgba(40, 160, 90, 0.9)"    // green -- correct
          : "rgba(200, 50, 50, 0.9)";   // red -- flagged
      ctx.strokeStyle = color;
      ctx.fillStyle = color;
      ctx.lineWidth = verdict && !verdict.valid ? 2 : 1;
      ctx.strokeRect(minX - 6, minY - 6, maxX - minX + 12, maxY - minY + 12);
      ctx.fillText(`line ${row}`, minX - 6, minY - 10);

      // The product's core visual: a flagged line gets a clear red
      // underline beneath the ink, like a teacher's mark.
      if (verdict && !verdict.valid) {
        ctx.strokeStyle = "rgba(200, 50, 50, 0.9)";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(minX - 4, maxY + 10);
        ctx.lineTo(maxX + 4, maxY + 10);
        ctx.stroke();
      }
    }
  }, [strokes, drawStroke, verdictsByLine]);

  // Size canvas to window
  useEffect(() => {
    const canvas = canvasRef.current;
    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      drawFrame();
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [drawFrame]);

  useEffect(() => {
    drawFrame();
  }, [strokes, drawFrame]);

  return (
    <div style={{ position: "fixed", inset: 0, background: "#faf8f2" }}>
      <canvas
        ref={canvasRef}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        style={{ touchAction: "none", display: "block" }}
      />
      <input
        type="text"
        value={problem}
        onChange={(e) => setProblem(e.target.value)}
        placeholder="Enter the problem, e.g. 3x - 12 = 2x + 5"
        style={{
          position: "fixed", top: 12, left: 12, padding: "8px 12px",
          width: 320, border: "1px solid #ccc", borderRadius: 8,
          fontFamily: "monospace",
        }}
      />
      {!problem.trim() && (
        <div
          style={{
            position: "fixed", top: 50, left: 12, fontSize: 12,
            color: "#a06a3a", fontFamily: "monospace",
          }}
        >
          Checking is off until you type a problem above -- lines will
          transcribe but won't be graded.
        </div>
      )}
      <button
        onClick={() => {
          setStrokes([]);
          setLines([]);
          setVerdictsByLine(new Map());
          setFirstWrongLine(null);
          setHintLevel(0);
          setHintText(null);
          setLastResult(null);
        }}
        style={{
          position: "fixed", top: 12, right: 12, padding: "8px 16px",
          background: "#fff", border: "1px solid #ccc", borderRadius: 8,
        }}
      >
        Clear
      </button>
      <button
        onClick={handleFinishLine}
        disabled={transcribing || strokes.length === 0}
        style={{
          position: "fixed", top: 12, right: 96, padding: "8px 16px",
          background: "#fff", border: "1px solid #ccc", borderRadius: 8,
          opacity: transcribing || strokes.length === 0 ? 0.5 : 1,
        }}
      >
        {transcribing ? "Transcribing..." : "Finish Line"}
      </button>
      {lastResult?.error && (
        <div
          style={{
            position: "fixed", bottom: 12, left: 12, padding: "10px 16px",
            background: "#fff", border: "1px solid #ccc", borderRadius: 8,
            fontFamily: "monospace", maxWidth: "80vw", color: "#b00020",
          }}
        >
          Error: {lastResult.error}
        </div>
      )}
      {lines.length > 0 && (
        <div
          style={{
            position: "fixed", top: 64, right: 12, width: 300,
            background: "#fff", border: "1px solid #ccc", borderRadius: 8,
            padding: 12, maxHeight: "60vh", overflowY: "auto",
            fontFamily: "monospace", fontSize: 13,
          }}
        >
          <div style={{ fontWeight: "bold", marginBottom: 8, fontFamily: "sans-serif" }}>
            Your work (edit if misread)
          </div>
          {lines.map((l) => {
            const verdict = verdictsByLine.get(l.row);
            const status = l.unreadable
              ? { label: "couldn't read -- type it here", color: "#a06a3a" }
              : verdict === undefined
              ? { label: "not checked", color: "#888" }
              : verdict.valid
              ? { label: "correct", color: "#28a05a" }
              : { label: verdict.error_type || "wrong", color: "#c83232" };
            return (
              <div key={l.row} style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 11, color: status.color, fontFamily: "sans-serif" }}>
                  line {l.row}: {status.label}
                </div>
                <input
                  type="text"
                  value={l.text}
                  placeholder={l.unreadable ? "type what you wrote" : ""}
                  onChange={(e) => handleLineEdit(l.row, e.target.value)}
                  onBlur={handleLineEditDone}
                  onKeyDown={(e) => e.key === "Enter" && e.target.blur()}
                  style={{
                    width: "100%", padding: "4px 8px", boxSizing: "border-box",
                    border: `1px solid ${status.color}`, borderRadius: 4,
                    fontFamily: "monospace",
                  }}
                />
              </div>
            );
          })}
        </div>
      )}
      {firstWrongLine !== null && (
        <div style={{ position: "fixed", bottom: 12, right: 12, maxWidth: "40vw" }}>
          {hintText && (
            <div
              style={{
                padding: "10px 16px", marginBottom: 8,
                background: "#fff", border: "1px solid #ccc", borderRadius: 8,
              }}
            >
              <strong>Hint {hintLevel}/3:</strong> {hintText}
            </div>
          )}
          <button
            onClick={handleGetHint}
            disabled={hintLoading || hintLevel >= 3}
            style={{
              padding: "8px 16px", background: "#fff",
              border: "1px solid #ccc", borderRadius: 8,
              opacity: hintLoading || hintLevel >= 3 ? 0.5 : 1,
            }}
          >
            {hintLoading
              ? "Loading..."
              : hintLevel === 0
              ? "Get Hint"
              : hintLevel >= 3
              ? "No more hints"
              : "Next Hint"}
          </button>
        </div>
      )}
    </div>
  );
}