/**
 * Client helper: generate draft vs LLM-final sketches via Next bridge → FastAPI.
 *
 * On CPU, both faces can take 20–40+ minutes total — no client abort timeout.
 */

export type CompareImage = {
  label: string;
  seed: number;
  image_base64: string;
  mime_type: string;
};

export type CompareResult =
  | {
      ok: true;
      draft_image: CompareImage;
      final_image: CompareImage;
      backend?: string;
    }
  | { ok: false; error: string; hint?: string };

export async function generateCompare(args: {
  draft: { positive: string; negative: string };
  final: { positive: string; negative: string };
  draft_seed?: number;
  final_seed?: number;
}): Promise<CompareResult> {
  try {
    const res = await fetch("/api/generate-compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(args),
      // Browser: do not abort early; server route waits for Python SD jobs
    });

    let data: CompareResult;
    try {
      data = (await res.json()) as CompareResult;
    } catch {
      return {
        ok: false,
        error: `generate-compare returned non-JSON (HTTP ${res.status})`,
        hint: "The Next.js bridge may have timed out while SD was still running. Check the uvicorn terminal; leave the tab open and retry after the worker is idle.",
      };
    }

    if (!res.ok && !("ok" in data)) {
      return {
        ok: false,
        error: `generate-compare HTTP ${res.status}`,
        hint: "Check that Next.js and the Python FastAPI worker are both running.",
      };
    }

    return data;
  } catch (err) {
    const msg = err instanceof Error ? err.message : "generate-compare network error";
    return {
      ok: false,
      error: msg,
      hint:
        msg.toLowerCase().includes("fetch failed") ||
        msg.toLowerCase().includes("network")
          ? "Connection dropped while waiting for SD (often a timeout). Keep uvicorn running on :8000, leave the tab open — CPU generation can take 10–20+ minutes per face — then try again when the worker is idle."
          : "Check that Next.js and the Python FastAPI worker are both running.",
    };
  }
}

export function imageSrc(img: CompareImage): string {
  const mime = img.mime_type || "image/png";
  return `data:${mime};base64,${img.image_base64}`;
}
