/**
 * Face Representation Layer v0.2
 *
 * RAW INTERVIEW → ATTRIBUTE NORMALIZER → STRUCTURED PROFILE → PROMPT BUILDER
 *
 * `raw_interview` = chat audit trail (not model input)
 * `structured`    = canonical tokens + confidence (model representation)
 */

import {
  normalizeInterview,
  structuredValuesOnly,
  type NormalizedCell,
  type StructuredAttributes,
} from "./attribute-normalizer";

export type AnswerSource = "option" | "other";

export type FlatAnswer = {
  key: string;
  group: string;
  value: string;
  source: AnswerSource;
};

export type FaceProfile = {
  version: "0.2";
  pipeline: "raw_interview → attribute_normalizer → structured_profile → prompt_builder → llm_refine";
  session: {
    opened_with: string;
    completed_at: string | null;
    question_count: number;
    answered_count: number;
  };
  /** Chat / MCQ trail — audit only, NOT the model representation */
  raw_interview: FlatAnswer[];
  /** Canonical taxonomy tokens + confidence — MODEL input */
  structured: StructuredAttributes;
  /** Convenience: structured values without confidence/raw */
  structured_values: Record<string, Record<string, string>>;
  prompt?: {
    /** Mechanical draft from structured tokens */
    draft_positive: string;
    draft_negative: string;
    /** LLM-refined witness-style prompt for generation */
    positive: string;
    negative: string;
    refined_by?: string | null;
  };
};

/** @deprecated use FaceProfile.structured cells */
export type AttributeCell = NormalizedCell;

export function buildProfileFromAnswers(
  answers: FlatAnswer[],
  openedWith: string,
  questionCount: number,
  completed = false,
): FaceProfile {
  const structured = normalizeInterview(answers);

  return {
    version: "0.2",
    pipeline:
      "raw_interview → attribute_normalizer → structured_profile → prompt_builder → llm_refine",
    session: {
      opened_with: openedWith,
      completed_at: completed ? new Date().toISOString() : null,
      question_count: questionCount,
      answered_count: answers.length,
    },
    raw_interview: [...answers],
    structured,
    structured_values: structuredValuesOnly(structured),
  };
}

/** Read canonical value: structured.eyes?.shape?.value */
export function attr(
  profile: FaceProfile,
  group: string,
  field: string,
): string | undefined {
  return profile.structured[group]?.[field]?.value;
}

export function attrConfidence(
  profile: FaceProfile,
  group: string,
  field: string,
): number | undefined {
  return profile.structured[group]?.[field]?.confidence;
}
