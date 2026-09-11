/**
 * Prompt router — Experiment 1B.
 *
 * CLIP-limited models → micro (≤77 tokens)
 * Longer-context models → original (full) prompt
 *
 * Does NOT modify the original prompt builder.
 */

import type { FaceProfile } from "../face-profile";
import {
  getGenerationModel,
  type GenerationModelId,
  type PromptMode,
} from "../generation-models";
import { generateMicroPrompt, approxTokenCount } from "./micro_prompt";
import { generateOriginalPrompt } from "./original_prompt";

export type RoutedPrompt = {
  model: GenerationModelId;
  mode: PromptMode;
  positive: string;
  negative: string;
  /** Always retained for research (1A vs 1B) */
  original_positive: string;
  original_negative: string;
  /** Micro draft when mode is micro; else null */
  micro_positive: string | null;
  micro_negative: string | null;
  token_count_approx: number;
};

export function promptModeForModel(model: GenerationModelId): PromptMode {
  const entry = getGenerationModel(model);
  if (entry) return entry.promptMode;
  // Fallback: treat unknown as micro (safer for CLIP)
  if (model === "flux" || model === "sd3") return "original";
  return "micro";
}

/**
 * Route structured profile → micro or original prompt by model id.
 */
export function buildPromptsForModel(
  profile: FaceProfile,
  model: GenerationModelId,
): RoutedPrompt {
  const mode = promptModeForModel(model);
  const original = generateOriginalPrompt(profile);

  if (mode === "micro") {
    const micro = generateMicroPrompt(profile);
    return {
      model,
      mode: "micro",
      positive: micro.positive,
      negative: micro.negative,
      original_positive: original.positive,
      original_negative: original.negative,
      micro_positive: micro.positive,
      micro_negative: micro.negative,
      token_count_approx: micro.token_count_approx,
    };
  }

  return {
    model,
    mode: "original",
    positive: original.positive,
    negative: original.negative,
    original_positive: original.positive,
    original_negative: original.negative,
    micro_positive: null,
    micro_negative: null,
    token_count_approx: approxTokenCount(original.positive),
  };
}
