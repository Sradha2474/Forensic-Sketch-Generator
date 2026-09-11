/**
 * Original (full) prompt generator — thin wrapper.
 *
 * KEEP the implementation in ../prompt-builder.ts unchanged.
 * Callers should prefer this module (or prompt_router) for Experiment 1B layout.
 */

export {
  buildPromptFromProfile as generateOriginalPrompt,
  attachPrompt as attachOriginalPrompt,
} from "../prompt-builder";
