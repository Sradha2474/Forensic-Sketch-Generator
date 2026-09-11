import { NextResponse } from "next/server";

/**
 * LLM refine layer (OpenRouter)
 *
 * prompt_mode:
 *   original → long witness-style (Flux / SD3 path)
 *   micro    → ≤~70 token rewrite (SD1.5 / ControlNet / SDXL)
 */

const SYSTEM_ORIGINAL = `You are a forensic prompt engineer for face-image generation (Flux / SD 3).

You receive:
1) A structured face attribute JSON (canonical tokens + confidence)
2) A draft mechanical prompt built from those attributes

Your job: rewrite into ONE clear, natural English description of a human face — as if a careful witness summarized what they saw for a composite artist / image model.

Rules:
- Keep ALL factual attributes that appear in the structured JSON (do not invent scars, tattoos, age, gender, ethnicity, glasses, etc.)
- Prefer natural phrasing over "field: value" lists
- Suitable as a positive prompt for photorealistic face generation
- Front-facing portrait / mugshot-friendly wording is OK
- If confidence is low (<0.5), phrase softly ("appeared to…", "possibly…") or omit tiny uncertain details
- Do NOT mention JSON, confidence scores, pipelines, or that you are an AI
- Also produce a short negative prompt (artifacts to avoid)

Return ONLY valid JSON with this shape:
{
  "positive": "...",
  "negative": "..."
}`;

const SYSTEM_MICRO = `You are a forensic prompt engineer for Stable Diffusion 1.5 (CLIP 77-token limit).

You receive structured face attributes and a short draft micro-prompt.

Rewrite into ONE ultra-compact positive prompt for SD 1.5.

HARD RULES:
- Positive prompt MUST be under 70 words/tokens (whitespace-separated). Prefer ~55–65.
- Keep only the strongest identity cues: age, face shape, hair, eyes, nose, jaw/chin, facial hair, glasses, scars/moles, expression.
- Dense comma-separated phrases OK. No essay. No filler.
- Do NOT invent attributes missing from the JSON.
- Do NOT mention JSON, confidence, pipelines, or that you are an AI.
- Also produce a short negative prompt.

Return ONLY valid JSON:
{
  "positive": "...",
  "negative": "..."
}`;

function getApiKey(): string | undefined {
  return (
    process.env.OPENROUTER_API_KEY ||
    process.env.openrouter_api_key ||
    undefined
  );
}

function clipWords(text: string, max: number): string {
  const tokens = text.trim().split(/\s+/).filter(Boolean);
  if (tokens.length <= max) return tokens.join(" ");
  return tokens.slice(0, max).join(" ");
}

export async function POST(req: Request) {
  try {
    const apiKey = getApiKey();
    if (!apiKey) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "Missing OPENROUTER_API_KEY in forenisic/.env (server restart required after adding it).",
        },
        { status: 500 },
      );
    }

    const body = await req.json();
    const {
      structured_values,
      structured,
      draft,
      prompt_mode,
    } = body as {
      structured_values?: unknown;
      structured?: unknown;
      draft?: { positive?: string; negative?: string };
      prompt_mode?: "micro" | "original";
    };

    if (!draft?.positive) {
      return NextResponse.json(
        { ok: false, error: "draft.positive is required" },
        { status: 400 },
      );
    }

    const mode = prompt_mode === "micro" ? "micro" : "original";
    const system = mode === "micro" ? SYSTEM_MICRO : SYSTEM_ORIGINAL;

    const model =
      process.env.OPENROUTER_MODEL || "openai/gpt-4o-mini";

    const userContent = [
      `PROMPT_MODE: ${mode}`,
      "",
      "STRUCTURED FACE ATTRIBUTES (canonical):",
      JSON.stringify(structured_values ?? structured ?? {}, null, 2),
      "",
      "DRAFT POSITIVE PROMPT:",
      draft.positive,
      "",
      "DRAFT NEGATIVE PROMPT:",
      draft.negative ?? "",
      "",
      mode === "micro"
        ? "Rewrite into the required JSON. Keep positive under 70 tokens."
        : "Rewrite into the required JSON.",
    ].join("\n");

    console.log("\n" + "─".repeat(72));
    console.log("[Forensic] LLM refine → OpenRouter", model, `mode=${mode}`);
    console.log("─".repeat(72));

    const upstream = await fetch(
      "https://openrouter.ai/api/v1/chat/completions",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "http://localhost:3000",
          "X-Title": "Forensic Sketch Generator",
        },
        body: JSON.stringify({
          model,
          temperature: mode === "micro" ? 0.2 : 0.4,
          response_format: { type: "json_object" },
          messages: [
            { role: "system", content: system },
            { role: "user", content: userContent },
          ],
        }),
      },
    );

    if (!upstream.ok) {
      const errText = await upstream.text();
      console.error("[Forensic] OpenRouter error", upstream.status, errText);
      return NextResponse.json(
        {
          ok: false,
          error: `OpenRouter ${upstream.status}`,
          detail: errText.slice(0, 500),
        },
        { status: 502 },
      );
    }

    const data = (await upstream.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const content = data.choices?.[0]?.message?.content?.trim() ?? "";

    let positive = draft.positive;
    let negative = draft.negative ?? "";

    try {
      const parsed = JSON.parse(content) as {
        positive?: string;
        negative?: string;
      };
      if (parsed.positive?.trim()) positive = parsed.positive.trim();
      if (parsed.negative?.trim()) negative = parsed.negative.trim();
    } catch {
      if (content) positive = content;
    }

    // Enforce micro budget even if the LLM overshoots
    if (mode === "micro") {
      positive = clipWords(positive, 70);
    }

    console.log("\n>>> FINAL LLM PROMPT (positive)\n");
    console.log(positive);
    console.log("\n>>> FINAL LLM PROMPT (negative)\n");
    console.log(negative);
    console.log("─".repeat(72) + "\n");

    return NextResponse.json({
      ok: true,
      prompt: { positive, negative },
      model,
      prompt_mode: mode,
    });
  } catch (err) {
    console.error("[Forensic] refine-prompt failed", err);
    return NextResponse.json(
      { ok: false, error: "refine-prompt failed" },
      { status: 500 },
    );
  }
}
