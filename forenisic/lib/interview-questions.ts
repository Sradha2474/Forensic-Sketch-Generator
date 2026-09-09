/**
 * Interview questions v0.1 — sourced from
 * workspaces/tushar/phase-02-interview/deliverables/interview_spec_v0.1.md
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
  // 01 Global
  {
    key: "global.character",
    group: "01 · Overall appearance",
    question: "Thinking of the whole face — what stood out about their overall look?",
    options: ["Soft / gentle", "Average / ordinary", "Sharp / striking"],
  },
  {
    key: "global.width",
    group: "01 · Overall appearance",
    question: "Was the face overall narrow, medium, or wide?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "global.length",
    group: "01 · Overall appearance",
    question: "Did the face look short, average length, or long?",
    options: ["Short", "Average", "Long"],
  },
  {
    key: "global.symmetry",
    group: "01 · Overall appearance",
    question: "How even did the two sides of the face look?",
    options: ["Very even", "Slightly uneven", "Clearly uneven"],
  },
  {
    key: "global.distinctiveness",
    group: "01 · Overall appearance",
    question: "How easy would it be to pick this face out of a crowd?",
    options: ["Hard to notice", "Somewhat memorable", "Very distinctive"],
  },

  // 02 Age
  {
    key: "age.range",
    group: "02 · Age",
    question: "About how old did they appear?",
    options: ["Teen / early 20s", "About 30–45", "About 50 or older"],
  },
  {
    key: "age.wrinkles",
    group: "02 · Age",
    question: "Did you notice wrinkles or lines on the face?",
    options: ["Almost none", "Light lines", "Deep / many wrinkles"],
  },
  {
    key: "age.cues",
    group: "02 · Age",
    question: "Beyond wrinkles, any other aging cues (sagging, hollows)?",
    options: ["No", "Mild", "Strong"],
  },

  // 03 Face shape
  {
    key: "face.shape",
    group: "03 · Face shape",
    question: "What face shape comes closest?",
    options: ["Round / soft", "Oval", "Square / rectangular"],
  },
  {
    key: "face.width",
    group: "03 · Face shape",
    question: "Across the cheekbones, how wide was the face?",
    options: ["Narrow", "Medium", "Broad"],
  },
  {
    key: "face.length",
    group: "03 · Face shape",
    question: "From forehead to chin, how long was the face?",
    options: ["Short", "Medium", "Long"],
  },
  {
    key: "face.thirds",
    group: "03 · Face shape",
    question: "Comparing forehead, mid-face, and jaw — which felt widest?",
    options: ["Forehead wider", "Mid-face wider", "Jaw wider"],
  },
  {
    key: "face.jaw_relationship",
    group: "03 · Face shape",
    question: "How did the jaw relate to the upper face?",
    options: ["Narrower than top", "Balanced", "Wider / heavier jaw"],
  },

  // 04 Hair
  {
    key: "hair.color",
    group: "04 · Hair",
    question: "What color was the hair?",
    options: ["Black / dark brown", "Brown / auburn", "Blonde / grey / light"],
  },
  {
    key: "hair.length",
    group: "04 · Hair",
    question: "How long was the hair?",
    options: ["Shaved / bald / buzz", "Short", "Medium / long"],
  },
  {
    key: "hair.texture",
    group: "04 · Hair",
    question: "How did the hair look in texture?",
    options: ["Straight", "Wavy", "Curly / coily"],
  },
  {
    key: "hair.density",
    group: "04 · Hair",
    question: "How thick was the hair?",
    options: ["Thin / sparse", "Average", "Thick / dense"],
  },
  {
    key: "hair.style",
    group: "04 · Hair",
    question: "How was it styled?",
    options: ["Neat / parted", "Messy / unkempt", "Tied back / covered"],
  },
  {
    key: "hair.hairline",
    group: "04 · Hair",
    question: "What about the hairline?",
    options: ["Straight / normal", "Receding", "Widow’s peak / uneven"],
  },

  // 05 Forehead
  {
    key: "forehead.height",
    group: "05 · Forehead",
    question: "How tall was the forehead?",
    options: ["Low", "Medium", "High"],
  },
  {
    key: "forehead.width",
    group: "05 · Forehead",
    question: "How wide was the forehead?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "forehead.shape",
    group: "05 · Forehead",
    question: "What shape was the forehead area?",
    options: ["Flat", "Rounded", "Angular"],
  },
  {
    key: "forehead.slope",
    group: "05 · Forehead",
    question: "Did the forehead slope back or stay upright?",
    options: ["Upright", "Mild slope", "Strong slope"],
  },

  // 06 Eyebrows
  {
    key: "brows.thickness",
    group: "06 · Eyebrows",
    question: "How thick were the eyebrows?",
    options: ["Thin", "Medium", "Thick / bushy"],
  },
  {
    key: "brows.shape",
    group: "06 · Eyebrows",
    question: "What shape were they?",
    options: ["Straight", "Softly curved", "Strongly arched"],
  },
  {
    key: "brows.arch",
    group: "06 · Eyebrows",
    question: "Where was the highest point of the arch?",
    options: ["Near the inner eye", "Middle", "Outer third"],
  },
  {
    key: "brows.length",
    group: "06 · Eyebrows",
    question: "How long were the brows across the eye?",
    options: ["Short", "Medium", "Long"],
  },
  {
    key: "brows.spacing",
    group: "06 · Eyebrows",
    question: "How far apart were the eyebrows?",
    options: ["Close / almost joined", "Average", "Wide apart"],
  },
  {
    key: "brows.position",
    group: "06 · Eyebrows",
    question: "How high sat the brows on the face?",
    options: ["Low / close to eyes", "Average", "High"],
  },

  // 07 Eyes
  {
    key: "eyes.size",
    group: "07 · Eyes",
    question: "How large were the eyes?",
    options: ["Small", "Medium", "Large"],
  },
  {
    key: "eyes.shape",
    group: "07 · Eyes",
    question: "What eye shape fits best?",
    options: ["Round", "Almond", "Narrow / hooded"],
  },
  {
    key: "eyes.color",
    group: "07 · Eyes",
    question: "What color were the eyes?",
    options: ["Brown / dark", "Hazel / green", "Blue / grey"],
  },
  {
    key: "eyes.spacing",
    group: "07 · Eyes",
    question: "How far apart were the eyes?",
    options: ["Close-set", "Average", "Wide-set"],
  },
  {
    key: "eyes.position",
    group: "07 · Eyes",
    question: "How were the eyes placed on the face?",
    options: ["Higher than average", "Average", "Lower than average"],
  },
  {
    key: "eyes.orientation",
    group: "07 · Eyes",
    question: "Did the outer corners tilt up or down?",
    options: ["Upturned", "Level", "Downturned"],
  },
  {
    key: "eyes.depth",
    group: "07 · Eyes",
    question: "How deep-set were the eyes?",
    options: ["Deep-set", "Average", "More protruding"],
  },
  {
    key: "eyes.eyelids",
    group: "07 · Eyes",
    question: "Anything notable about the eyelids?",
    options: ["Heavy / hooded", "Average", "Prominent crease / monolid look"],
  },

  // 08 Nose
  {
    key: "nose.type",
    group: "08 · Nose",
    question: "Overall, what kind of nose stood out?",
    options: ["Small / delicate", "Average", "Large / prominent"],
  },
  {
    key: "nose.length",
    group: "08 · Nose",
    question: "How long was the nose?",
    options: ["Short", "Medium", "Long"],
  },
  {
    key: "nose.width",
    group: "08 · Nose",
    question: "How wide was the nose?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "nose.bridge",
    group: "08 · Nose",
    question: "How did the bridge look from the side?",
    options: ["Flat / low", "Straight", "High / bumpy"],
  },
  {
    key: "nose.bridge_width",
    group: "08 · Nose",
    question: "How wide was the bridge between the eyes?",
    options: ["Narrow", "Medium", "Broad"],
  },
  {
    key: "nose.tip",
    group: "08 · Nose",
    question: "How would you describe the tip?",
    options: ["Pointed", "Rounded", "Bulbous / upturned"],
  },
  {
    key: "nose.projection",
    group: "08 · Nose",
    question: "How far did the nose stick out from the face?",
    options: ["Flat / low", "Average", "Strong projection"],
  },
  {
    key: "nose.nostrils",
    group: "08 · Nose",
    question: "How did the nostrils look?",
    options: ["Narrow", "Medium", "Flared / wide"],
  },

  // 09 Cheeks
  {
    key: "cheeks.fullness",
    group: "09 · Cheeks",
    question: "How full were the cheeks?",
    options: ["Hollow / thin", "Average", "Full / chubby"],
  },
  {
    key: "cheeks.bones",
    group: "09 · Cheeks",
    question: "How noticeable were the cheekbones?",
    options: ["Flat", "Average", "High / sharp"],
  },
  {
    key: "cheeks.mid_width",
    group: "09 · Cheeks",
    question: "Across the mid-face, how wide?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "cheeks.contour",
    group: "09 · Cheeks",
    question: "Soft curve or more angular mid-face?",
    options: ["Soft / rounded", "Mixed", "Angular / carved"],
  },

  // 10 Mouth
  {
    key: "mouth.width",
    group: "10 · Mouth",
    question: "How wide was the mouth?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "mouth.position",
    group: "10 · Mouth",
    question: "Was the mouth set high or low on the face?",
    options: ["High", "Average", "Low"],
  },
  {
    key: "mouth.upper_lip",
    group: "10 · Mouth",
    question: "How thick was the upper lip?",
    options: ["Thin", "Medium", "Full"],
  },
  {
    key: "mouth.lower_lip",
    group: "10 · Mouth",
    question: "How thick was the lower lip?",
    options: ["Thin", "Medium", "Full"],
  },
  {
    key: "mouth.lip_ratio",
    group: "10 · Mouth",
    question: "Which lip looked bigger?",
    options: ["Upper bigger", "About equal", "Lower bigger"],
  },
  {
    key: "mouth.cupids_bow",
    group: "10 · Mouth",
    question: "Was there a clear cupid’s bow on the upper lip?",
    options: ["Soft / flat", "Moderate", "Very defined"],
  },
  {
    key: "mouth.corners",
    group: "10 · Mouth",
    question: "How did the mouth corners sit?",
    options: ["Upturned", "Neutral", "Downturned"],
  },

  // 11 Jaw
  {
    key: "jaw.width",
    group: "11 · Jaw",
    question: "How wide was the jaw?",
    options: ["Narrow", "Medium", "Wide"],
  },
  {
    key: "jaw.shape",
    group: "11 · Jaw",
    question: "Soft jaw or sharp angles?",
    options: ["Soft / rounded", "Average", "Square / angular"],
  },
  {
    key: "jaw.definition",
    group: "11 · Jaw",
    question: "How defined was the jawline?",
    options: ["Soft / unclear", "Average", "Very defined"],
  },
  {
    key: "jaw.angle",
    group: "11 · Jaw",
    question: "How sharp was the jaw angle near the ear?",
    options: ["Soft", "Medium", "Sharp / strong"],
  },

  // 12 Chin
  {
    key: "chin.size",
    group: "12 · Chin",
    question: "How large was the chin?",
    options: ["Small", "Medium", "Large"],
  },
  {
    key: "chin.width",
    group: "12 · Chin",
    question: "How wide was the chin?",
    options: ["Narrow", "Medium", "Broad"],
  },
  {
    key: "chin.shape",
    group: "12 · Chin",
    question: "What chin shape fits best?",
    options: ["Pointed", "Rounded", "Square"],
  },
  {
    key: "chin.projection",
    group: "12 · Chin",
    question: "Did the chin stick out, sit back, or look average?",
    options: ["Receding", "Average", "Projecting"],
  },
  {
    key: "chin.cleft",
    group: "12 · Chin",
    question: "Any cleft or dimple in the chin?",
    options: ["No", "Slight", "Clear cleft"],
  },

  // 13 Ears
  {
    key: "ears.size",
    group: "13 · Ears",
    question: "How large were the ears?",
    options: ["Small", "Medium", "Large"],
  },
  {
    key: "ears.shape",
    group: "13 · Ears",
    question: "Overall ear shape?",
    options: ["Oval / regular", "Wide", "Unusual / pointed"],
  },
  {
    key: "ears.position",
    group: "13 · Ears",
    question: "How high were the ears on the head?",
    options: ["High", "Mid", "Low"],
  },
  {
    key: "ears.protrusion",
    group: "13 · Ears",
    question: "Did the ears stick out?",
    options: ["Close to head", "Average", "Clearly protruding"],
  },
  {
    key: "ears.lobes",
    group: "13 · Ears",
    question: "What about the earlobes?",
    options: ["Attached", "Average", "Large / hanging"],
  },

  // 14 Facial hair
  {
    key: "facial_hair.beard",
    group: "14 · Facial hair",
    question: "Was there a beard?",
    options: ["None", "Stubble / short", "Full / long"],
  },
  {
    key: "facial_hair.moustache",
    group: "14 · Facial hair",
    question: "Was there a moustache?",
    options: ["None", "Thin", "Thick"],
  },
  {
    key: "facial_hair.sideburns",
    group: "14 · Facial hair",
    question: "Any sideburns?",
    options: ["None", "Short", "Long"],
  },
  {
    key: "facial_hair.density",
    group: "14 · Facial hair",
    question: "How dense was the facial hair?",
    options: ["Patchy / light", "Average", "Thick"],
  },
  {
    key: "facial_hair.color",
    group: "14 · Facial hair",
    question: "Color of the facial hair?",
    options: ["Same as head hair", "Darker", "Lighter / grey"],
  },

  // 15 Skin
  {
    key: "skin.appearance",
    group: "15 · Skin",
    question: "How did the skin look overall?",
    options: ["Clear / smooth", "Average", "Rough / marked"],
  },
  {
    key: "skin.texture",
    group: "15 · Skin",
    question: "Skin texture?",
    options: ["Fine / soft", "Normal", "Coarse / oily / dry look"],
  },
  {
    key: "skin.wrinkles",
    group: "15 · Skin",
    question: "Visible wrinkles beyond age lines already noted?",
    options: ["No", "Mild", "Heavy"],
  },
  {
    key: "skin.age_marks",
    group: "15 · Skin",
    question: "Age spots or surface marks?",
    options: ["None noticed", "A few", "Many"],
  },

  // 16 Distinctive
  {
    key: "marks.scars",
    group: "16 · Distinctive marks",
    question: "Any scars on the face? (If yes, you can use Other to say where.)",
    options: ["None", "Small / faint", "Clear / large scar"],
  },
  {
    key: "marks.moles",
    group: "16 · Distinctive marks",
    question: "Any moles?",
    options: ["None", "One noticeable", "Several"],
  },
  {
    key: "marks.birthmarks",
    group: "16 · Distinctive marks",
    question: "Any birthmark?",
    options: ["None", "Small", "Large / obvious"],
  },
  {
    key: "marks.tattoos",
    group: "16 · Distinctive marks",
    question: "Any visible facial or neck tattoo?",
    options: ["None", "Small", "Large / obvious"],
  },
  {
    key: "marks.piercings",
    group: "16 · Distinctive marks",
    question: "Any piercings?",
    options: ["None", "Ear only", "Face / multiple"],
  },
  {
    key: "marks.dimples",
    group: "16 · Distinctive marks",
    question: "Dimples when they spoke or rested?",
    options: ["None", "Slight", "Clear dimples"],
  },
  {
    key: "marks.asymmetry",
    group: "16 · Distinctive marks",
    question: "Anything clearly uneven (eye, smile, nose)?",
    options: ["No", "Mild", "Strong asymmetry"],
  },

  // 17 Accessories
  {
    key: "accessories.glasses",
    group: "17 · Accessories",
    question: "Were they wearing glasses?",
    options: ["No", "Everyday / thin frames", "Thick / dark frames"],
  },
  {
    key: "accessories.earrings",
    group: "17 · Accessories",
    question: "Any earrings?",
    options: ["No", "Small studs", "Large / dangling"],
  },
  {
    key: "accessories.headwear",
    group: "17 · Accessories",
    question: "Hat, cap, hoodie, or other headwear?",
    options: ["None", "Cap / hat", "Hood / wrap / other cover"],
  },

  // 18 Context
  {
    key: "context.view_angle",
    group: "18 · Viewing context",
    question: "From which angle did you mainly see the face?",
    options: ["Straight on", "Slight three-quarter", "Side / profile"],
  },
  {
    key: "context.head_position",
    group: "18 · Viewing context",
    question: "How was the head held?",
    options: ["Level", "Tilted", "Chin up / down"],
  },
  {
    key: "context.expression",
    group: "18 · Viewing context",
    question: "What expression do you remember?",
    options: ["Neutral", "Tense / angry", "Smiling / talking"],
  },
  {
    key: "context.lighting",
    group: "18 · Viewing context",
    question: "How was the lighting when you saw them?",
    options: ["Bright / clear", "Average", "Dim / hard to see"],
  },

  // 19 Holistic
  {
    key: "holistic.distinctiveness",
    group: "19 · Holistic check",
    question: "Looking back, how unique does this face feel now?",
    options: ["Ordinary", "Somewhat unique", "Very unique"],
  },
  {
    key: "holistic.age_confirm",
    group: "19 · Holistic check",
    question: "Confirming age — which band still feels right?",
    options: ["Under ~25", "About 25–45", "Over ~45"],
  },
  {
    key: "holistic.impression",
    group: "19 · Holistic check",
    question: "One overall impression — which feels closest?",
    options: ["Soft / approachable", "Hard / stern", "Ordinary / forgettable"],
  },
];

export const INTERVIEW_QUESTION_COUNT = INTERVIEW_QUESTIONS.length;
