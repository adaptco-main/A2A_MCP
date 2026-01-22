import React, { useEffect, useMemo, useRef, useState } from "react";

const fixture = {
  schema_version: "ReplayCourtConvictionFixture.v1",
  fixture_id: "rcf:demo",
  created_at_unix_ms: Date.now(),
  frames: [
    {
      tick: 0,
      world_hash: "00".repeat(32),
      frame_hash: "11".repeat(32),
      merkle_root: "22".repeat(32),
      prev_root: "00".repeat(32),
      phase: { progress: 0.0, pressure: 0.0 },
      scene: {
        width: 48,
        height: 48,
        pixels_rle: [
          ...Array.from({ length: 48 * 48 }, (_, i) => {
            const x = i % 48;
            const y = Math.floor(i / 48);
            const on = (x + y) % 2 === 0;
            return [1, on ? 240 : 20, on ? 240 : 20, on ? 240 : 20, 255];
          }),
        ],
      },
    },
    {
      tick: 1,
      world_hash: "00".repeat(32),
      frame_hash: "33".repeat(32),
      merkle_root: "44".repeat(32),
      prev_root: "22".repeat(32),
      phase: { progress: 0.25, pressure: 0.1 },
      scene: {
        width: 48,
        height: 48,
        pixels_rle: [
          ...Array.from({ length: 48 * 48 }, (_, i) => {
            const x = i % 48;
            const y = Math.floor(i / 48);
            const cx = 24;
            const cy = 24;
            const d = Math.hypot(x - cx, y - cy);
            const v = Math.max(0, 255 - Math.floor(d * 12));
            return [1, v, 40, 80, 255];
          }),
        ],
      },
    },
  ],
};

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

const hexShort = (value: string | undefined, length = 10) => {
  if (!value) return "";
  return value.length <= length ? value : `${value.slice(0, length)}…`;
};

const decodeRle = (pixelsRle: number[][], totalPixels: number) => {
  const out = new Uint8ClampedArray(totalPixels * 4);
  let offset = 0;

  for (const entry of pixelsRle) {
    const [count, r, g, b, a] = entry;
    for (let i = 0; i < count; i += 1) {
      out[offset++] = r;
      out[offset++] = g;
      out[offset++] = b;
      out[offset++] = a;
    }
  }

  return out;
};

const JurassicPixels: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [fps, setFps] = useState(12);
  const [idx, setIdx] = useState(0);

  const frames = fixture.frames ?? [];
  const frame = frames[idx] ?? null;

  const decoded = useMemo(() => {
    if (!frame) return null;
    const { width, height, pixels_rle } = frame.scene;
    const total = width * height;
    const rgba = decodeRle(pixels_rle, total);
    return { width, height, rgba };
  }, [frame]);

  useEffect(() => {
    if (!decoded) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const scale = 8;
    canvas.width = decoded.width * scale;
    canvas.height = decoded.height * scale;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.imageSmoothingEnabled = false;

    const offscreen = document.createElement("canvas");
    offscreen.width = decoded.width;
    offscreen.height = decoded.height;
    const offscreenCtx = offscreen.getContext("2d");
    if (!offscreenCtx) return;

    const imageData = offscreenCtx.createImageData(decoded.width, decoded.height);
    imageData.data.set(decoded.rgba);
    offscreenCtx.putImageData(imageData, 0, 0);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(offscreen, 0, 0, canvas.width, canvas.height);
  }, [decoded]);

  useEffect(() => {
    if (!playing || frames.length <= 1) return;

    const interval = Math.max(10, Math.floor(1000 / Math.max(1, fps)));
    const timer = window.setInterval(() => {
      setIdx((current) => (current + 1) % frames.length);
    }, interval);

    return () => window.clearInterval(timer);
  }, [playing, fps, frames.length]);

  const reset = () => {
    setPlaying(false);
    setIdx(0);
  };

  const progress = frames.length <= 1 ? 0 : idx / (frames.length - 1);

  return (
    <div className="max-w-6xl space-y-4">
      <header>
        <p className="text-sm uppercase tracking-wide text-slate-400">Playback</p>
        <h2 className="text-2xl font-semibold text-white">Jurassic Pixels</h2>
        <p className="text-sm text-slate-300">
          Fixture: <span className="font-mono">{fixture.fixture_id}</span>
        </p>
      </header>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex gap-2">
              <button
                className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500"
                onClick={() => setPlaying((current) => !current)}
              >
                {playing ? "Pause" : "Play"}
              </button>
              <button
                className="rounded-full border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-500"
                onClick={reset}
              >
                Reset
              </button>
            </div>
            <div className="text-sm text-slate-400">
              Frame {idx + 1} of {Math.max(1, frames.length)}
            </div>
          </div>

          <div className="flex items-center justify-center rounded-xl bg-black/80 p-3">
            <canvas ref={canvasRef} className="rounded-lg" />
          </div>

          <div className="space-y-4">
            <div>
              <label className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
                <span>Frame scrub</span>
                <span className="font-mono text-slate-200">{idx + 1}</span>
              </label>
              <input
                className="mt-2 w-full accent-indigo-500"
                type="range"
                min={0}
                max={frames.length <= 1 ? 0 : frames.length - 1}
                value={idx}
                onChange={(event) => setIdx(Number(event.target.value))}
              />
            </div>
            <div>
              <label className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
                <span>FPS</span>
                <span className="font-mono text-slate-200">{fps}</span>
              </label>
              <input
                className="mt-2 w-full accent-indigo-500"
                type="range"
                min={1}
                max={60}
                value={fps}
                onChange={(event) => setFps(Number(event.target.value))}
              />
            </div>
          </div>
        </section>

        <aside className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-200">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Tick</p>
            <p className="text-lg font-semibold font-mono">{frame?.tick ?? "—"}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Phase</p>
            <p className="font-mono">progress={frame?.phase?.progress ?? "—"}</p>
            <p className="font-mono">pressure={frame?.phase?.pressure ?? "—"}</p>
          </div>
          <div className="space-y-2">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">world_hash</p>
              <p className="font-mono">{hexShort(frame?.world_hash, 16)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">frame_hash</p>
              <p className="font-mono">{hexShort(frame?.frame_hash, 16)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">merkle_root</p>
              <p className="font-mono">{hexShort(frame?.merkle_root, 16)}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">prev_root</p>
              <p className="font-mono">{hexShort(frame?.prev_root, 16)}</p>
            </div>
          </div>
          <p className="border-t border-slate-800 pt-4 text-xs text-slate-400">
            Tip: Keep pixels compressed (RLE) and deterministic when building real fixtures.
          </p>
        </aside>
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
        <h3 className="text-base font-semibold text-white">Fixture metadata</h3>
        <dl className="mt-2 space-y-2">
          <div className="flex items-center justify-between">
            <dt className="text-slate-400">Schema</dt>
            <dd className="font-mono text-slate-200">{fixture.schema_version}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-slate-400">Created</dt>
            <dd className="font-mono text-slate-200">
              {new Date(fixture.created_at_unix_ms).toISOString()}
            </dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-slate-400">Frames</dt>
            <dd className="font-mono text-slate-200">{frames.length}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="text-slate-400">Progress</dt>
            <dd className="font-mono text-slate-200">{clamp01(progress).toFixed(2)}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
};

export default JurassicPixels;
