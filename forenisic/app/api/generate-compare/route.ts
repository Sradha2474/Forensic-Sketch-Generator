import { NextResponse } from "next/server";

/**
 * Bridge: draft + final prompts → Python FastAPI SD worker in parallel.
 *
 * Env: PYTHON_BACKEND_URL=http://127.0.0.1:8000
 */

const BACKEND =
  process.env.PYTHON_BACKEND_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

type PromptPair = { positive?: string; negative?: string };

type GenerateBody = {
  draft?: PromptPair;
  final?: PromptPair;
  draft_seed?: number;
  final_seed?: number;
};

async function callGenerate(
  label: string,
  prompt: PromptPair,
  seed: number,
): Promise<{
  label: string;
  seed: number;
  image_base64: string;
  mime_type?: string;
}> {
  const res = await fetch(`${BACKEND}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: prompt.positive,
      negative_prompt: prompt.negative ?? null,
      seed,
      label,
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      `Python /generate (${label}) failed: ${res.status} ${detail.slice(0, 400)}`,
    );
  }

  return res.json();
}

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as GenerateBody;
    const { draft, final } = body;

    if (!draft?.positive?.trim() || !final?.positive?.trim()) {
      return NextResponse.json(
        {
          ok: false,
          error: "draft.positive and final.positive are required",
        },
        { status: 400 },
      );
    }

    // Same seed for both → only intentional variable is the prompt (controlled A/B).
    const compareSeed = body.draft_seed ?? body.final_seed ?? 42;

    console.log("\n" + "─".repeat(72));
    console.log("[Forensic] generate-compare →", BACKEND);
    console.log("  shared seed", compareSeed, "(draft + LLM; prompt is the only variable)");
    console.log("─".repeat(72));

    const [draftRes, finalRes] = await Promise.all([
      callGenerate("draft", draft, compareSeed),
      callGenerate("final", final, compareSeed),
    ]);

    console.log("[Forensic] generate-compare OK — both images received");
    console.log("─".repeat(72) + "\n");

    return NextResponse.json({
      ok: true,
      draft_image: {
        label: draftRes.label,
        seed: draftRes.seed,
        image_base64: draftRes.image_base64,
        mime_type: draftRes.mime_type ?? "image/png",
      },
      final_image: {
        label: finalRes.label,
        seed: finalRes.seed,
        image_base64: finalRes.image_base64,
        mime_type: finalRes.mime_type ?? "image/png",
      },
      backend: BACKEND,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "generate-compare failed";
    console.error("[Forensic] generate-compare failed", message);
    return NextResponse.json(
      {
        ok: false,
        error: message,
        hint: `Is the Python worker running? uvicorn api.main:app --port 8000 (PYTHON_BACKEND_URL=${BACKEND})`,
      },
      { status: 502 },
    );
  }
}
