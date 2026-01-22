import { useEffect, useRef, useState } from "react";
import {
  BrainCircuit,
  ChevronRight,
  Heart,
  History,
  Loader2,
  Play,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react";

/**
 * BAEK-CHEON-2026: Kinetic Manifold Prototype v0.4
 * INTEGRATION: Gemini API Neural Audit & Strategy
 * ARCHITECTURE: MVP (Model-View-Presenter)
 */

const API_KEY = "";

type PlayerState = {
  x: number;
  y: number;
  width: number;
  height: number;
  vy: number;
  isJumping: boolean;
  currentHealth: number;
  maxHealth: number;
  minHealth: number;
};

type EnvironmentState = {
  obstacles: Array<{ x: number; y: number; width: number; height: number }>;
  speed: number;
  score: number;
};

type LedgerEntry = {
  type: "JUMP" | "DAMAGE" | "HEAL" | "RESTORE";
  timestamp: number;
  amount: number;
  actor: string;
  hash: string;
};

type ModelState = {
  player: PlayerState;
  environment: EnvironmentState;
  isPaused: boolean;
  fossilLedger: LedgerEntry[];
  currentHash: string;
  aiAnalysis: string | null;
  isAiThinking: boolean;
};

// --- MODEL: THE STATE MANIFOLD ---
const INITIAL_STATE: ModelState = {
  player: {
    x: 50,
    y: 150,
    width: 20,
    height: 20,
    vy: 0,
    isJumping: false,
    currentHealth: 100,
    maxHealth: 100,
    minHealth: 0,
  },
  environment: { obstacles: [], speed: 2, score: 0 },
  isPaused: true,
  fossilLedger: [],
  currentHash: "0x0000000000000000",
  aiAnalysis: null,
  isAiThinking: false,
};

// --- STABLE STRINGIFY LOGIC ---
const stableStringify = (data: unknown): string => {
  if (data === null) return "null";
  if (typeof data === "number") {
    if (!Number.isFinite(data)) return "0";
    return JSON.stringify(data);
  }
  if (typeof data === "string" || typeof data === "boolean") return JSON.stringify(data);
  if (Array.isArray(data)) return `[${data.map(stableStringify).join(",")}]`;
  if (typeof data === "object") {
    const record = data as Record<string, unknown>;
    return `{${Object.keys(record)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`)
      .join(",")}}`;
  }
  return "null";
};

const generateHash = async (text: string) => {
  const msgUint8 = new TextEncoder().encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return `0x${hashArray.map((b) => b.toString(16).padStart(2, "0")).join("")}`;
};

// --- GEMINI API INTEGRATION ---
const fetchAiAnalysis = async (ledger: LedgerEntry[], currentScore: number) => {
  const prompt = `You are the Chief Auditor of the Merkle Forest.\n  Analyze this kinetic manifold audit ledger: ${JSON.stringify(
    ledger,
  )}.\n  Current Score: ${currentScore}.\n  Provide a concise (2-3 sentences), high-level strategic assessment and a creative "narrative audit" status.\n  Keep it technical yet immersive in the BAEK-CHEON context.`;

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    systemInstruction: {
      parts: [
        { text: "Respond as a futuristic, slightly clinical AI auditor overseeing a physics manifold." },
      ],
    },
  };

  const callApi = async (attempt = 0): Promise<string | undefined> => {
    try {
      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${API_KEY}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );

      if (!response.ok) throw new Error("API_ERROR");
      const result = await response.json();
      return result.candidates?.[0]?.content?.parts?.[0]?.text;
    } catch (error) {
      if (attempt < 5) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise((resolve) => setTimeout(resolve, delay));
        return callApi(attempt + 1);
      }
      throw error;
    }
  };

  return callApi();
};

// --- VIEW: THE KINETIC VIEWPORT & HEALTH SLIDER ---
const GameView = ({ model, onInput }: { model: ModelState; onInput: HandleInput }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#FDFCFB";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw Ground
    ctx.strokeStyle = "#E5E7EB";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 170);
    ctx.lineTo(canvas.width, 170);
    ctx.stroke();

    // Draw Player
    ctx.fillStyle = model.player.currentHealth < 30 ? "#EF4444" : "#2563EB";
    ctx.fillRect(model.player.x, model.player.y, model.player.width, model.player.height);

    // Draw Obstacles
    ctx.fillStyle = "#D97706";
    model.environment.obstacles.forEach((obs) => {
      ctx.fillRect(obs.x, obs.y, obs.width, obs.height);
    });

    // Draw HUD
    ctx.fillStyle = "#1C1C1E";
    ctx.font = "bold 10px monospace";
    ctx.fillText(`SCORE: ${Math.floor(model.environment.score)}`, 10, 20);
  }, [model]);

  return (
    <div className="space-y-4">
      <div className="relative overflow-hidden rounded-lg border border-stone-200 bg-white shadow-inner">
        <canvas
          ref={canvasRef}
          width={400}
          height={200}
          className="h-auto w-full cursor-pointer"
          onClick={() => onInput("JUMP")}
        />
        {model.isPaused && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-sm">
            <div className="text-center">
              <p className="mb-2 text-xs font-black uppercase tracking-widest text-blue-600">
                Manifold Idle
              </p>
              <button
                onClick={() => onInput("TOGGLE_PAUSE")}
                className="rounded-full bg-blue-600 p-3 text-white shadow-lg transition-all hover:bg-blue-700"
              >
                <Play className="h-5 w-5 fill-current" />
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="space-y-2 rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-[10px] font-bold uppercase text-stone-500">
            <Heart
              className={`h-3 w-3 ${
                model.player.currentHealth < 30 ? "animate-pulse text-red-500" : "text-blue-500"
              }`}
            />
            Health Manifold Status
          </span>
          <span className="text-xs font-black text-stone-600">{model.player.currentHealth}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-stone-100">
          <div
            className={`h-full transition-all duration-300 ${
              model.player.currentHealth < 30 ? "bg-red-500" : "bg-blue-600"
            }`}
            style={{ width: `${(model.player.currentHealth / model.player.maxHealth) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};

type CommandType = "TOGGLE_PAUSE" | "JUMP" | "DAMAGE" | "HEAL" | "RESTORE";

type HandleInput = (type: CommandType, amount?: number) => Promise<void>;

// --- PRESENTER: THE KINETIC ENGINE ---
export default function JurassicPixels() {
  const [model, setModel] = useState(INITIAL_STATE);
  const [log, setLog] = useState<string[]>([
    "[SYSTEM]: Health Manifold Sync'd.",
    "[SYSTEM]: Awaiting Agent intent.",
  ]);
  const requestRef = useRef<number>();

  const addLog = (msg: string) => setLog((prev) => [msg, ...prev].slice(0, 8));

  const runAiAudit = async () => {
    if (model.fossilLedger.length === 0) {
      addLog("[AI]: Insufficient data for neural audit.");
      return;
    }

    setModel((prev) => ({ ...prev, isAiThinking: true, aiAnalysis: null }));
    try {
      const analysis = await fetchAiAnalysis(model.fossilLedger, model.environment.score);
      setModel((prev) => ({ ...prev, isAiThinking: false, aiAnalysis: analysis ?? null }));
      addLog("[AI]: Neural audit fossilized.");
    } catch {
      setModel((prev) => ({ ...prev, isAiThinking: false }));
      addLog("[ERROR]: AI integration manifold failure.");
    }
  };

  const handleInput: HandleInput = async (type, amount = 0) => {
    if (type === "TOGGLE_PAUSE") {
      setModel((prev) => ({ ...prev, isPaused: !prev.isPaused }));
      return;
    }

    if (model.isPaused) return;

    const command = {
      type,
      timestamp: Date.now(),
      amount,
      actor: "AGENT_01",
    };

    const canonical = stableStringify(command);
    const hash = await generateHash(canonical);

    setModel((prev) => {
      const nextPlayer = { ...prev.player };

      if (type === "JUMP" && !nextPlayer.isJumping) {
        nextPlayer.vy = -8;
        nextPlayer.isJumping = true;
      }

      if (type === "DAMAGE") {
        nextPlayer.currentHealth = Math.max(prev.player.minHealth, prev.player.currentHealth - amount);
      }
      if (type === "HEAL") {
        nextPlayer.currentHealth = Math.min(prev.player.maxHealth, prev.player.currentHealth + amount);
      }
      if (type === "RESTORE") {
        nextPlayer.currentHealth = prev.player.maxHealth;
      }

      const collisionState = nextPlayer.currentHealth <= 0;

      return {
        ...prev,
        isPaused: collisionState,
        player: nextPlayer,
        fossilLedger: [...prev.fossilLedger, { ...command, hash }].slice(-10),
        currentHash: hash,
      };
    });

    addLog(`[COMMAND]: ${type} processed. Hash: ${hash.slice(0, 8)}...`);
  };

  const update = () => {
    if (!model.isPaused) {
      setModel((prev) => {
        const { player, environment } = prev;

        let newVy = player.vy + 0.4;
        let newY = player.y + newVy;
        let jumping = true;

        if (newY > 150) {
          newY = 150;
          newVy = 0;
          jumping = false;
        }

        const newObstacles = environment.obstacles
          .map((o) => ({ ...o, x: o.x - environment.speed }))
          .filter((o) => o.x > -20);

        if (Math.random() < 0.01 && newObstacles.length < 2) {
          newObstacles.push({ x: 400, y: 150, width: 15, height: 20 });
        }

        const hit = newObstacles.some(
          (obs) =>
            player.x < obs.x + obs.width &&
            player.x + player.width > obs.x &&
            player.y < obs.y + obs.height &&
            player.y + player.height > obs.y,
        );

        if (hit) {
          void handleInput("DAMAGE", 10);
        }

        return {
          ...prev,
          player: { ...player, y: newY, vy: newVy, isJumping: jumping },
          environment: {
            ...environment,
            obstacles: newObstacles,
            score: environment.score + 0.1,
            speed: 2 + environment.score / 100,
          },
        };
      });
    }
    requestRef.current = requestAnimationFrame(update);
  };

  useEffect(() => {
    requestRef.current = requestAnimationFrame(update);
    return () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [model.isPaused]);

  return (
    <div className="min-h-screen bg-slate-50 p-4 font-mono text-slate-900 md:p-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="flex flex-col items-start justify-between gap-4 border-b border-stone-200 pb-6 md:flex-row md:items-center">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-black text-blue-600">
              <Zap className="h-8 w-8 fill-current" />
              JURASSIC PIXELS: KINETIC MANIFOLD
            </h1>
            <p className="mt-1 text-[10px] uppercase tracking-[0.3em] text-stone-500">
              Axiomatic Runtime v0.4 | Gemini AI Integration
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleInput("HEAL", 20)}
              className="rounded bg-white px-4 py-2 text-[10px] font-black uppercase text-emerald-600 shadow-sm transition-all hover:bg-emerald-50"
            >
              HEAL (20)
            </button>
            <button
              onClick={() => handleInput("RESTORE")}
              className="rounded bg-white px-4 py-2 text-[10px] font-black uppercase text-blue-600 shadow-sm transition-all hover:bg-blue-50"
            >
              RESTORE
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="space-y-6 lg:col-span-7">
            <GameView model={model} onInput={handleInput} />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-3 rounded-lg border border-stone-100 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-[10px] font-bold uppercase text-stone-500">
                    <BrainCircuit className="h-3 w-3 text-fuchsia-500" />
                    Neural Audit Registry
                  </span>
                  <button
                    disabled={model.isAiThinking}
                    onClick={runAiAudit}
                    className="flex items-center gap-1 rounded bg-fuchsia-100 px-2 py-1 text-[8px] font-bold text-fuchsia-600 hover:bg-fuchsia-200 disabled:opacity-50"
                  >
                    {model.isAiThinking ? (
                      <Loader2 className="h-2 w-2 animate-spin" />
                    ) : (
                      <Sparkles className="h-2 w-2" />
                    )}
                    ✨ GENERATE AUDIT
                  </button>
                </div>
                <div className="min-h-[60px] rounded border border-stone-100 bg-stone-50 p-3 text-[10px] italic leading-relaxed text-stone-600">
                  {model.aiAnalysis ||
                    (model.isAiThinking
                      ? "Auditing temporal commands..."
                      : "Awaiting neural analysis request...")}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-lg border border-stone-100 bg-white p-4 text-center shadow-sm">
                  <p className="mb-1 text-[8px] font-bold uppercase text-stone-400">Health_Axis</p>
                  <p
                    className={`text-lg font-black ${
                      model.player.currentHealth < 30 ? "text-red-500" : "text-blue-600"
                    }`}
                  >
                    {model.player.currentHealth}
                  </p>
                </div>
                <div className="rounded-lg border border-stone-100 bg-white p-4 text-center shadow-sm">
                  <p className="mb-1 text-[8px] font-bold uppercase text-stone-400">Score_Manifold</p>
                  <p className="text-lg font-black text-amber-600">
                    {Math.floor(model.environment.score)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6 lg:col-span-5">
            <div className="flex h-[280px] flex-col overflow-hidden rounded-xl bg-stone-900 text-stone-300 shadow-2xl">
              <div className="flex items-center justify-between bg-stone-800 px-4 py-2">
                <span className="flex items-center gap-2 text-[10px] font-bold uppercase">
                  <Terminal className="h-3 w-3 text-emerald-400" />
                  Kinetic Ledger (Fossilized)
                </span>
                <span className="text-[8px] text-stone-500">ASIL_D_SYNC</span>
              </div>
              <div className="flex-1 space-y-2 overflow-y-auto p-4 font-mono text-[10px]">
                {log.map((entry, i) => (
                  <div key={i} className="flex gap-2 border-b border-stone-800/50 pb-1">
                    <ChevronRight className="mt-1 h-2 w-2 text-stone-600" />
                    <span>{entry}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-stone-200 bg-white shadow-sm">
              <div className="border-b border-stone-200 bg-stone-50 px-4 py-2">
                <span className="flex items-center gap-2 text-[10px] font-bold uppercase text-stone-500">
                  <History className="h-3 w-3" />
                  Health Intent Registry
                </span>
              </div>
              <div className="max-h-[180px] space-y-2 overflow-y-auto p-4">
                {model.fossilLedger.length === 0 ? (
                  <p className="text-[10px] italic text-stone-400">Awaiting intent...</p>
                ) : (
                  model.fossilLedger
                    .slice()
                    .reverse()
                    .map((cmd, i) => (
                      <div
                        key={`${cmd.hash}-${i}`}
                        className="mb-1 flex items-center justify-between rounded border border-stone-100 bg-stone-50 p-2"
                      >
                        <div className="flex flex-col">
                          <span
                            className={`text-[10px] font-black ${
                              cmd.type === "DAMAGE" ? "text-red-500" : "text-blue-600"
                            }`}
                          >
                            {cmd.type} {cmd.amount > 0 ? `(${cmd.amount})` : ""}
                          </span>
                          <span className="text-[8px] font-mono text-stone-400">
                            {cmd.hash.slice(0, 16)}...
                          </span>
                        </div>
                        <ShieldCheck className="h-3 w-3 text-emerald-500" />
                      </div>
                    ))
                )}
              </div>
            </div>
          </div>
        </div>

        <footer className="border-t border-stone-100 py-12 text-center">
          <p className="mb-4 text-[10px] uppercase tracking-[0.4em] text-stone-400">
            Axiom: What is kinetic is measured. What is neural is analyzed.
          </p>
          <div className="flex items-center justify-center gap-6 opacity-40 grayscale">
            <ShieldAlert className="h-4 w-4" />
            <span className="text-[8px] font-black uppercase">Sovereign Vow Certified</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
