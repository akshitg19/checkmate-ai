import { useRef, useState, useEffect, useCallback } from "react";

const LINE_HEIGHT = 64;

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

export default function App() {
  const canvasRef = useRef(null);
  const [strokes, setStrokes] = useState([]); // finished strokes
  const currentStroke = useRef(null); // stroke in progress

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

    // Ruled lines
    // Ink
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 3;
    for (let y = LINE_HEIGHT; y < canvas.height; y += LINE_HEIGHT) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Ink
    ctx.strokeStyle = "#1a1a2e";
    ctx.lineWidth = 2.5;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    for (const s of strokes) drawStroke(ctx, s);
    if (currentStroke.current) drawStroke(ctx, currentStroke.current);

    // Segmentation debug view: box around each detected line
    const lines = segmentIntoLines(strokes);
    ctx.strokeStyle = "rgba(70, 130, 180, 0.35)";
    ctx.lineWidth = 1;
    ctx.font = "11px sans-serif";
    ctx.fillStyle = "rgba(70, 130, 180, 0.8)";
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
      ctx.strokeRect(minX - 6, minY - 6, maxX - minX + 12, maxY - minY + 12);
      ctx.fillText(`line ${row}`, minX - 6, minY - 10);
    }
  }, [strokes, drawStroke]);

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
      <button
        onClick={() => setStrokes([])}
        style={{
          position: "fixed", top: 12, right: 12, padding: "8px 16px",
          background: "#fff", border: "1px solid #ccc", borderRadius: 8,
        }}
      >
        Clear
      </button>
    </div>
  );
}