/**
 * Client helper — calls server refine layer (OpenRouter stays on server).
 */

export type DraftPrompt = {
  positive: string;
  negative: string;
};

export type PromptMode = "micro" | "original";

export async function refinePromptWithLLM(input: {
  structured_values: unknown;
  structured?: unknown;
  draft: DraftPrompt;
  /** Experiment 1B: micro stays ≤~70 tokens; original = full witness style */
  prompt_mode?: PromptMode;
}): Promise<{
  ok: boolean;
  prompt?: DraftPrompt;
  model?: string;
  error?: string;
}> {
  const res = await fetch("/api/refine-prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const data = (await res.json()) as {
    ok: boolean;
    prompt?: DraftPrompt;
    model?: string;
    error?: string;
  };

  return data;
}
