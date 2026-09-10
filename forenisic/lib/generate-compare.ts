/**
 * Client helper: generate draft vs LLM-final sketches via Next bridge → FastAPI.
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
    });
    const data = (await res.json()) as CompareResult;
    return data;
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "generate-compare network error",
      hint: "Check that Next.js and the Python FastAPI worker are both running.",
    };
  }
}

export function imageSrc(img: CompareImage): string {
  const mime = img.mime_type || "image/png";
  return `data:${mime};base64,${img.image_base64}`;
}
