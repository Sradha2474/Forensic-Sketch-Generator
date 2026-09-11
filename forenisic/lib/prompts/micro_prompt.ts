/**
 * Micro prompt generator — Experiment 1B.
 *
 * Structured profile → short identity-first prompt ≤ ~70–77 CLIP tokens.
 * Does NOT modify the original full prompt builder.
 */

import type { FaceProfile } from "../face-profile";
import { attr } from "../face-profile";

const CLIP_SOFT_MAX = 70;

const SKIP = new Set(["none", "unknown", "not_available", ""]);

function v(profile: FaceProfile, group: string, field: string): string | undefined {
  const raw = attr(profile, group, field);
  if (!raw || SKIP.has(raw)) return undefined;
  return raw.replace(/_/g, " ");
}

/** Approximate CLIP token count (whitespace split; good enough for soft budget). */
export function approxTokenCount(text: string): number {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

export function clipTruncate(text: string, maxTokens: number = CLIP_SOFT_MAX): string {
  const tokens = text.trim().split(/\s+/).filter(Boolean);
  if (tokens.length <= maxTokens) return tokens.join(" ");
  return tokens.slice(0, maxTokens).join(" ");
}

/**
 * Build a dense ≤77-token forensic face prompt from structured attributes.
 */
export function generateMicroPrompt(profile: FaceProfile): {
  positive: string;
  negative: string;
  token_count_approx: number;
} {
  const parts: string[] = [
    "forensic face portrait",
    "front view",
    "mugshot",
  ];

  const age = v(profile, "age", "range");
  if (age) parts.push(age);

  const wrinkles = v(profile, "age", "wrinkles");
  if (wrinkles) parts.push(`${wrinkles} wrinkles`);

  const shape = v(profile, "face", "shape");
  if (shape) parts.push(`${shape} face`);

  const faceW = v(profile, "face", "width");
  if (faceW) parts.push(`${faceW} width`);

  const faceL = v(profile, "face", "length");
  if (faceL) parts.push(`${faceL} length`);

  const hairColor = v(profile, "hair", "color");
  const hairLen = v(profile, "hair", "length");
  const hairTex = v(profile, "hair", "texture");
  const hairBits = [hairColor, hairLen, hairTex].filter(Boolean);
  if (hairBits.length) parts.push(`${hairBits.join(" ")} hair`);

  const hairline = v(profile, "hair", "hairline");
  if (hairline) parts.push(`${hairline} hairline`);

  const forehead = v(profile, "forehead", "height");
  if (forehead) parts.push(`${forehead} forehead`);

  const browT = v(profile, "brows", "thickness");
  const browS = v(profile, "brows", "shape");
  if (browT || browS) {
    parts.push(`${[browT, browS].filter(Boolean).join(" ")} brows`);
  }

  const eyeSize = v(profile, "eyes", "size");
  const eyeShape = v(profile, "eyes", "shape");
  const eyeColor = v(profile, "eyes", "color");
  const eyeSpace = v(profile, "eyes", "spacing");
  const eyeBits = [eyeSize, eyeShape, eyeColor, eyeSpace].filter(Boolean);
  if (eyeBits.length) parts.push(`${eyeBits.join(" ")} eyes`);

  const noseL = v(profile, "nose", "length");
  const noseW = v(profile, "nose", "width");
  const noseBridge = v(profile, "nose", "bridge");
  const noseTip = v(profile, "nose", "tip");
  const noseBits = [noseL, noseW, noseBridge, noseTip].filter(Boolean);
  if (noseBits.length) parts.push(`${noseBits.join(" ")} nose`);

  const cheekF = v(profile, "cheeks", "fullness");
  const cheekB = v(profile, "cheeks", "bones");
  if (cheekF || cheekB) {
    parts.push(`${[cheekF, cheekB].filter(Boolean).join(" ")} cheeks`);
  }

  const mouthW = v(profile, "mouth", "width");
  const upper = v(profile, "mouth", "upper_lip");
  const lower = v(profile, "mouth", "lower_lip");
  if (mouthW || upper || lower) {
    const lip = [upper && `upper ${upper}`, lower && `lower ${lower}`]
      .filter(Boolean)
      .join(" ");
    parts.push(
      [mouthW && `${mouthW} mouth`, lip].filter(Boolean).join(", "),
    );
  }

  const jawW = v(profile, "jaw", "width");
  const jawS = v(profile, "jaw", "shape");
  if (jawW || jawS) {
    parts.push(`${[jawW, jawS].filter(Boolean).join(" ")} jaw`);
  }

  const chinS = v(profile, "chin", "shape");
  const chinP = v(profile, "chin", "projection");
  const chinC = v(profile, "chin", "cleft");
  if (chinS || chinP || chinC) {
    parts.push(
      `${[chinS, chinP, chinC && chinC !== "no" ? `cleft ${chinC}` : null]
        .filter(Boolean)
        .join(" ")} chin`,
    );
  }

  const beard = v(profile, "facial_hair", "beard");
  const moustache = v(profile, "facial_hair", "moustache");
  if (beard) parts.push(`${beard} beard`);
  if (moustache) parts.push(`${moustache} moustache`);

  const skin = v(profile, "skin", "appearance");
  if (skin) parts.push(`${skin} skin`);

  const scars = v(profile, "marks", "scars");
  if (scars) parts.push(`scar ${scars}`);
  const moles = v(profile, "marks", "moles");
  if (moles) parts.push(`moles ${moles}`);
  const tattoos = v(profile, "marks", "tattoos");
  if (tattoos) parts.push(`tattoo ${tattoos}`);

  const glasses = v(profile, "accessories", "glasses");
  if (glasses && glasses !== "no") parts.push(`glasses ${glasses}`);
  const headwear = v(profile, "accessories", "headwear");
  if (headwear) parts.push(headwear);

  const expression = v(profile, "context", "expression");
  if (expression) parts.push(expression);

  const character = v(profile, "global", "character");
  if (character) parts.push(character);

  const rawPositive = parts.join(", ");
  const positive = clipTruncate(rawPositive, CLIP_SOFT_MAX);
  const negative =
    "cartoon, anime, blurry, deformed, extra faces, watermark, text, low quality";

  return {
    positive,
    negative,
    token_count_approx: approxTokenCount(positive),
  };
}
