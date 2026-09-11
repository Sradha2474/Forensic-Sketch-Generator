import { NextResponse } from "next/server";
import http from "node:http";
import https from "node:https";
import { URL } from "node:url";

/**
 * Bridge: draft + final prompts → Python FastAPI SD worker.
 *
 * Env: PYTHON_BACKEND_URL=http://127.0.0.1:8000
 *
 * CPU SD jobs often take 10–20+ minutes per face. Node's default fetch
 * (undici) aborts around ~5 minutes → UI shows "fetch failed" while uvicorn
 * is still working. Use node:http with no timeout + sequential generates.
 */

export const maxDuration = 1800; // 30 minutes (App Router)

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

type GenerateOk = {
  label: string;
  seed: number;
  image_base64: string;
  mime_type?: string;
};

/** POST JSON with no socket timeout (CPU SD can run 20+ min). */
function postJsonNoTimeout(
  urlStr: string,
  body: unknown,
): Promise<{ status: number; text: string }> {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const payload = Buffer.from(JSON.stringify(body), "utf8");
    const lib = url.protocol === "https:" ? https : http;

    const req = lib.request(
      {
        protocol: url.protocol,
        hostname: url.hostname,
        port: url.port || (url.protocol === "https:" ? 443 : 80),
        path: `${url.pathname}${url.search}`,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": payload.length,
        },
        timeout: 0,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c) => chunks.push(c));
        res.on("end", () => {
          resolve({
            status: res.statusCode ?? 0,
            text: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );

    req.on("timeout", () => {
      req.destroy(new Error("socket timeout"));
    });
    req.on("error", reject);
    // Disable inactivity timeouts on the socket
    req.setTimeout(0);
    req.write(payload);
    req.end();
  });
}

async function callGenerate(
  label: string,
  prompt: PromptPair,
  seed: number,
): Promise<GenerateOk> {
  const { status, text } = await postJsonNoTimeout(`${BACKEND}/generate`, {
    prompt: prompt.positive,
    negative_prompt: prompt.negative ?? null,
    seed,
    label,
  });

  if (status < 200 || status >= 300) {
    throw new Error(
      `Python /generate (${label}) failed: ${status} ${text.slice(0, 400)}`,
    );
  }

  return JSON.parse(text) as GenerateOk;
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

    const compareSeed = body.draft_seed ?? body.final_seed ?? 42;

    console.log("\n" + "─".repeat(72));
    console.log("[Forensic] generate-compare →", BACKEND);
    console.log(
      "  shared seed",
      compareSeed,
      "(draft then LLM sequentially; CPU may take 10–20+ min each)",
    );
    console.log("─".repeat(72));

    console.log("[Forensic] generating draft …");
    const draftRes = await callGenerate("draft", draft, compareSeed);
    console.log("[Forensic] draft OK — generating LLM/final …");
    const finalRes = await callGenerate("final", final, compareSeed);

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
        hint: `Is the Python worker running? uvicorn api.main:app --port 8000 (PYTHON_BACKEND_URL=${BACKEND}). On CPU, each face can take 10–20+ minutes — leave the tab open.`,
      },
      { status: 502 },
    );
  }
}
