/**
 * Generation model catalog — Experiment 1B model picker.
 *
 * promptMode:
 *   micro    → CLIP-limited models (SD 1.5 / ControlNet / SDXL)
 *   original → longer-context models (Flux / SD 3)
 */

export type GenerationModelId =
  | "sd15"
  | "sd15_controlnet"
  | "sdxl"
  | "flux"
  | "sd3";

export type PromptMode = "micro" | "original";

export type GenerationModel = {
  id: GenerationModelId;
  label: string;
  description: string;
  promptMode: PromptMode;
  /** Wired to a live worker today */
  available: boolean;
};

export const GENERATION_MODELS: GenerationModel[] = [
  {
    id: "sd15",
    label: "SD 1.5",
    description: "Stable Diffusion 1.5 · micro prompt (CLIP ≤77)",
    promptMode: "micro",
    available: true,
  },
  {
    id: "sd15_controlnet",
    label: "SD 1.5 + ControlNet",
    description: "Coming soon · micro prompt",
    promptMode: "micro",
    available: false,
  },
  {
    id: "sdxl",
    label: "SDXL",
    description: "Coming soon · micro prompt (CLIP ≤77)",
    promptMode: "micro",
    available: false,
  },
  {
    id: "flux",
    label: "Flux",
    description: "FLUX.1-schnell · full original prompt (CLIP+T5)",
    promptMode: "original",
    available: true,
  },
  {
    id: "sd3",
    label: "SD 3",
    description: "Coming soon · full original prompt",
    promptMode: "original",
    available: false,
  },
];

export function getGenerationModel(
  id: GenerationModelId,
): GenerationModel | undefined {
  return GENERATION_MODELS.find((m) => m.id === id);
}
