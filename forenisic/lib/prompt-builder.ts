/**
 * Prompt Builder v0.2
 *
 * Builds prompts from STRUCTURED PROFILE (canonical tokens),
 * NOT from the raw 90 interview strings.
 *
 * Pipeline: raw interview → normalizer → structured → prompt builder
 */

import type { FaceProfile } from "./face-profile";
import type { StructuredAttributes } from "./attribute-normalizer";

const SKIP_NONE = new Set(["none", "unknown"]);

const GROUP_ORDER = [
  "age",
  "global",
  "face",
  "hair",
  "forehead",
  "brows",
  "eyes",
  "nose",
  "cheeks",
  "mouth",
  "jaw",
  "chin",
  "ears",
  "facial_hair",
  "skin",
  "marks",
  "accessories",
  "context",
  "holistic",
] as const;

function phrase(group: string, field: string, value: string): string | null {
  if (SKIP_NONE.has(value)) {
    // Keep explicit "no beard" style only for facial hair
    if (group === "facial_hair") return `${field.replace(/_/g, " ")}: none`;
    return null;
  }
  return `${group.replace(/_/g, " ")} ${field.replace(/_/g, " ")}: ${value}`;
}

function linesFromStructured(structured: StructuredAttributes): string[] {
  const lines: string[] = [];
  const seen = new Set<string>();

  for (const group of GROUP_ORDER) {
    const fields = structured[group];
    if (!fields) continue;
    for (const [field, cell] of Object.entries(fields)) {
      const p = phrase(group, field, cell.value);
      if (!p) continue;
      // Prefer higher-confidence if somehow duplicated
      const id = `${group}.${field}`;
      if (seen.has(id)) continue;
      seen.add(id);
      // Only include reasonably confident attributes in the generation prompt
      if (cell.confidence < 0.45) continue;
      lines.push(p);
    }
  }

  // Any leftover groups not in ORDER
  for (const [group, fields] of Object.entries(structured)) {
    if ((GROUP_ORDER as readonly string[]).includes(group)) continue;
    for (const [field, cell] of Object.entries(fields)) {
      const p = phrase(group, field, cell.value);
      if (p && cell.confidence >= 0.45) lines.push(p);
    }
  }

  return lines;
}

export function buildPromptFromProfile(profile: FaceProfile): {
  positive: string;
  negative: string;
} {
  const attributeLines = linesFromStructured(profile.structured);

  const positive = [
    "forensic facial composite portrait",
    "photorealistic face",
    "front-facing mugshot style",
    "neutral studio lighting",
    "high detail",
    "identity-focused",
    ...attributeLines,
  ].join(", ");

  const negative = [
    "cartoon",
    "anime",
    "sketch lines only",
    "blurry",
    "low resolution",
    "deformed face",
    "extra limbs",
    "watermark",
    "text overlay",
    "crowd",
    "multiple faces",
  ].join(", ");

  return { positive, negative };
}

export function attachPrompt(profile: FaceProfile): FaceProfile {
  const prompt = buildPromptFromProfile(profile);
  return { ...profile, prompt };
}
