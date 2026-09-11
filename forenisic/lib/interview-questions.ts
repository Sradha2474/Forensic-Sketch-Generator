/**
 * Interview questions v0.3 — compact forensic set (40 questions).
 *
 * Reduced from ~96 by dropping holistic checks, redundant geometry,
 * and low-impact context. Keeps attributes that most affect SD face identity.
 *
 * UI shows these 3 options + a separate "Other…" free-text control.
 */

export interface InterviewQuestion {
  key: string;
  group: string;
  question: string;
  /** Exactly 3 options; "Other…" is handled in the UI */
  options: [string, string, string];
}

export const INTERVIEW_QUESTIONS: InterviewQuestion[] = [
  // 01 Age
  {
    key: "age.range",
    group: "01 · Age",
    question: "About how old did they appear?",
    options: ["Teen / early 20s", "About 30–45", "About 50 or older"],
  },
  {
    key: "age.wrinkles",
    group: "01 · Age",
    question: "Did you notice wrinkles or lines on the face?",
    options: ["Almost none", "Light lines", "Deep / many wrinkles"],
  },

  // 02 Face shape
  {
    key: "face.shape",
    group: "02 · Face shape",
    question: "What face shape comes closest?",
    options: ["Round / soft", "Oval", "Square / rectangular"],
  },
  {
    key: "face.width",
    group: "02 · Face shape",
    question: "Across the cheekbones, how wide was the face?",
    options: ["Narrow", "Medium", "Broad"],
  },
  {
    key: "face.length",
    group: "02 · Face shape",
    question: "From forehead to chin, how long was the face?",
    options: ["Short", "Medium", "Long"],
  },

  // 03 Hair
  {
    key: "hair.color",
    group: "03 · Hair",
    question: "What color was the hair?",
    options: ["Black / dark brown", "Brown / auburn", "Blonde / grey / light"],
  },
  {
    key: "hair.length",
    group: "03 · Hair",
    question: "How long was the hair?",
    options: ["Shaved / bald / buzz", "Short", "Medium / long"],
  },
  {
    key: "hair.texture",
    group: "03 · Hair",
    question: "How did the hair look in texture?",
    options: ["Straight", "Wavy", "Curly / coily"],
  },
  {
    key: "hair.hairline",
    group: "03 · Hair",
    question: "What about the hairline?",
    options: ["Straight / normal", "Receding", "Widow’s peak / uneven"],
  },

  // 04 Forehead
  {
    key: "forehead.height",
    group: "04 · Forehead",
    question: "How tall was the forehead?",
    options: ["Low", "Medium", "High"],
  },

  // 05 Eyebrows
  {
    key: "brows.thickness",
    group: "05 · Eyebrows",
    question: "How thick were the eyebrows?",
    options: ["Thin", "Medium", "Thick / bushy"],
  },
  {
    key: "brows.shape",
    group: "05 · Eyebrows",
    question: "What shape were they?",
    options: ["Straight", "Softly curved", "Strongly arched"],
  },

  // 06 Eyes
  {
    key: "eyes.size",
    group: "06 · Eyes",
    question: "How large were the eyes?",
    options: ["Small", "Medium", "Large"],
  },
  {
    key: "eyes.shape",
    group: "06 · Eyes",
    question: "What eye shape fits best?",
    options: ["Round", "Almond", "Narrow / hooded"],
  },
  {
    key: "eyes.color",
    group: "06 · Eyes",
    question: "What color were the eyes?",
    options: ["Brown / dark", "Hazel / green", "Blue / grey"],
  },
  {
    key: "eyes.spacing",
    group: "06 · Eyes",
    question: "How far apart were the eyes?",
    options: ["Close-set", "Average", "Wide-set"],
  },

  // 07 Nose
  {
    key: "nose.length",
    group: "07 · Nose",
    question: "How long was the nose?",
    options: ["Short", "Medium", "Long"],
  },
  {
    key: "nose.width",
    group: "07 · Nose",
    question: "How wide was the nose?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "nose.bridge",
    group: "07 · Nose",
    question: "How did the bridge look from the side?",
    options: ["Flat / low", "Straight", "High / bumpy"],
  },
  {
    key: "nose.tip",
    group: "07 · Nose",
    question: "How would you describe the tip?",
    options: ["Pointed", "Rounded", "Bulbous / upturned"],
  },

  // 08 Cheeks
  {
    key: "cheeks.fullness",
    group: "08 · Cheeks",
    question: "How full were the cheeks?",
    options: ["Hollow / thin", "Average", "Full / chubby"],
  },
  {
    key: "cheeks.bones",
    group: "08 · Cheeks",
    question: "How noticeable were the cheekbones?",
    options: ["Flat", "Average", "High / sharp"],
  },

  // 09 Mouth
  {
    key: "mouth.width",
    group: "09 · Mouth",
    question: "How wide was the mouth?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "mouth.upper_lip",
    group: "09 · Mouth",
    question: "How thick was the upper lip?",
    options: ["Thin", "Medium", "Full"],
  },
  {
    key: "mouth.lower_lip",
    group: "09 · Mouth",
    question: "How thick was the lower lip?",
    options: ["Thin", "Medium", "Full"],
  },

  // 10 Jaw & chin
  {
    key: "jaw.width",
    group: "10 · Jaw & chin",
    question: "How wide was the jaw?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "jaw.shape",
    group: "10 · Jaw & chin",
    question: "Soft jaw or sharp angles?",
    options: ["Soft / rounded", "Average", "Square / angular"],
  },
  {
    key: "chin.shape",
    group: "10 · Jaw & chin",
    question: "What chin shape fits best?",
    options: ["Pointed", "Rounded", "Square"],
  },
  {
    key: "chin.projection",
    group: "10 · Jaw & chin",
    question: "Did the chin stick out, sit back, or look average?",
    options: ["Receding", "Average", "Projecting"],
  },
  {
    key: "chin.cleft",
    group: "10 · Jaw & chin",
    question: "Any cleft or dimple in the chin?",
    options: ["No", "Slight", "Clear cleft"],
  },

  // 11 Facial hair
  {
    key: "facial_hair.beard",
    group: "11 · Facial hair",
    question: "Was there a beard?",
    options: ["None", "Stubble / short", "Full / long"],
  },
  {
    key: "facial_hair.moustache",
    group: "11 · Facial hair",
    question: "Was there a moustache?",
    options: ["None", "Thin", "Thick"],
  },

  // 12 Skin & marks
  {
    key: "skin.appearance",
    group: "12 · Skin & marks",
    question: "How did the skin look overall?",
    options: ["Clear / smooth", "Average", "Rough / marked"],
  },
  {
    key: "marks.scars",
    group: "12 · Skin & marks",
    question: "Any scars on the face? (If yes, you can use Other to say where.)",
    options: ["None", "Small / faint", "Clear / large scar"],
  },
  {
    key: "marks.moles",
    group: "12 · Skin & marks",
    question: "Any moles?",
    options: ["None", "One noticeable", "Several"],
  },
  {
    key: "marks.tattoos",
    group: "12 · Skin & marks",
    question: "Any visible facial or neck tattoo?",
    options: ["None", "Small", "Large / obvious"],
  },

  // 13 Accessories
  {
    key: "accessories.glasses",
    group: "13 · Accessories",
    question: "Were they wearing glasses?",
    options: ["No", "Everyday / thin frames", "Thick / dark frames"],
  },
  {
    key: "accessories.headwear",
    group: "13 · Accessories",
    question: "Hat, cap, hoodie, or other headwear?",
    options: ["None", "Cap / hat", "Hood / wrap / other cover"],
  },

  // 14 Expression & overall
  {
    key: "context.expression",
    group: "14 · Expression",
    question: "What expression do you remember?",
    options: ["Neutral", "Tense / angry", "Smiling / talking"],
  },
  {
    key: "global.character",
    group: "14 · Expression",
    question: "Overall look — what stood out most?",
    options: ["Soft / gentle", "Average / ordinary", "Sharp / striking"],
  },
];

export const INTERVIEW_QUESTION_COUNT = INTERVIEW_QUESTIONS.length;
