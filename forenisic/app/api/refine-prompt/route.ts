import { NextResponse } from "next/server";

/**
 * LLM refine layer (OpenRouter)
 *
 * draft prompt (from structured profile)
 *        ↓
 * OpenRouter chat (gpt-4o-mini by default)
 *        ↓
 * natural witness-style FINAL prompt for SDXL / FLUX
 *
 * API key stays server-side only (never sent to the browser).
 */

const SYSTEM = `You are a forensic prompt engineer for face-image generation (SDXL / FLUX).

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

function getApiKey(): string | undefined {
  return (
    process.env.OPENROUTER_API_KEY ||
    process.env.openrouter_api_key ||
    undefined
  );
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
    } = body as {
      structured_values?: unknown;
      structured?: unknown;
      draft?: { positive?: string; negative?: string };
    };

    if (!draft?.positive) {
      return NextResponse.json(
        { ok: false, error: "draft.positive is required" },
        { status: 400 },
      );
    }

    const model =
      process.env.OPENROUTER_MODEL || "openai/gpt-4o-mini";

    const userContent = [
      "STRUCTURED FACE ATTRIBUTES (canonical):",
      JSON.stringify(structured_values ?? structured ?? {}, null, 2),
      "",
      "DRAFT POSITIVE PROMPT:",
      draft.positive,
      "",
      "DRAFT NEGATIVE PROMPT:",
      draft.negative ?? "",
      "",
      "Rewrite into the required JSON.",
    ].join("\n");

    console.log("\n" + "─".repeat(72));
    console.log("[Forensic] LLM refine → OpenRouter", model);
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
          temperature: 0.4,
          response_format: { type: "json_object" },
          messages: [
            { role: "system", content: SYSTEM },
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
      // If model returned prose, use it as positive
      if (content) positive = content;
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
    });
  } catch (err) {
    console.error("[Forensic] refine-prompt failed", err);
    return NextResponse.json(
      { ok: false, error: "refine-prompt failed" },
      { status: 500 },
    );
  }
}
