/**
 * Attribute Normalizer v0.1
 *
 * RAW INTERVIEW  →  ATTRIBUTE NORMALIZER  →  STRUCTURED PROFILE
 *
 * The 90 chat answers are NOT the model representation.
 * This layer maps free text / option labels → canonical taxonomy tokens + confidence.
 *
 * Example:
 *   Q: nose.width  raw: "Quite wide"
 *   → { value: "broad", confidence: 0.8, raw: "Quite wide" }
 */

export type NormalizedCell = {
  /** Canonical taxonomy token (model input) */
  value: string;
  /** 0–1; option clicks are high, fuzzy free-text is lower */
  confidence: number;
  /** Original witness / option text (audit only) */
  raw: string;
};

export type StructuredAttributes = Record<
  string,
  Record<string, NormalizedCell>
>;

type Rule = {
  /** Canonical value */
  value: string;
  /** Substrings / regexes that map to this value (lowercase) */
  match: Array<string | RegExp>;
  /** Confidence when matched from free text */
  confidence?: number;
};

/** Exact option-label → canonical (high confidence) */
const OPTION_MAP: Record<string, Record<string, string>> = {
  "global.character": {
    "Soft / gentle": "soft",
    "Average / ordinary": "average",
    "Sharp / striking": "striking",
  },
  "global.width": { Narrow: "narrow", Medium: "medium", Wide: "wide" },
  "global.length": { Short: "short", Average: "average", Long: "long" },
  "global.symmetry": {
    "Very even": "symmetric",
    "Slightly uneven": "slightly_asymmetric",
    "Clearly uneven": "asymmetric",
  },
  "global.distinctiveness": {
    "Hard to notice": "low",
    "Somewhat memorable": "medium",
    "Very distinctive": "high",
  },
  "age.range": {
    "Teen / early 20s": "young_adult",
    "About 30–45": "middle_adult",
    "About 50 or older": "older_adult",
  },
  "age.wrinkles": {
    "Almost none": "none",
    "Light lines": "light",
    "Deep / many wrinkles": "deep",
  },
  "age.cues": { No: "none", Mild: "mild", Strong: "strong" },
  "face.shape": {
    "Round / soft": "round",
    Oval: "oval",
    "Square / rectangular": "square",
  },
  "face.width": { Narrow: "narrow", Medium: "medium", Broad: "broad" },
  "face.length": { Short: "short", Medium: "medium", Long: "long" },
  "face.thirds": {
    "Forehead wider": "forehead_dominant",
    "Mid-face wider": "midface_dominant",
    "Jaw wider": "jaw_dominant",
  },
  "face.jaw_relationship": {
    "Narrower than top": "narrower",
    Balanced: "balanced",
    "Wider / heavier jaw": "heavier",
  },
  "hair.color": {
    "Black / dark brown": "black",
    "Brown / auburn": "brown",
    "Blonde / grey / light": "light",
  },
  "hair.length": {
    "Shaved / bald / buzz": "bald_or_buzz",
    Short: "short",
    "Medium / long": "long",
  },
  "hair.texture": {
    Straight: "straight",
    Wavy: "wavy",
    "Curly / coily": "curly",
  },
  "hair.density": {
    "Thin / sparse": "thin",
    Average: "average",
    "Thick / dense": "thick",
  },
  "hair.style": {
    "Neat / parted": "neat",
    "Messy / unkempt": "messy",
    "Tied back / covered": "tied_back",
  },
  "hair.hairline": {
    "Straight / normal": "straight",
    Receding: "receding",
    "Widow’s peak / uneven": "widows_peak",
  },
  "forehead.height": { Low: "low", Medium: "medium", High: "high" },
  "forehead.width": { Narrow: "narrow", Medium: "medium", Wide: "wide" },
  "forehead.shape": { Flat: "flat", Rounded: "rounded", Angular: "angular" },
  "forehead.slope": {
    Upright: "upright",
    "Mild slope": "mild",
    "Strong slope": "strong",
  },
  "brows.thickness": {
    Thin: "thin",
    Medium: "medium",
    "Thick / bushy": "thick",
  },
  "brows.shape": {
    Straight: "straight",
    "Softly curved": "curved",
    "Strongly arched": "arched",
  },
  "brows.arch": {
    "Near the inner eye": "inner",
    Middle: "middle",
    "Outer third": "outer",
  },
  "brows.length": { Short: "short", Medium: "medium", Long: "long" },
  "brows.spacing": {
    "Close / almost joined": "close",
    Average: "average",
    "Wide apart": "wide",
  },
  "brows.position": {
    "Low / close to eyes": "low",
    Average: "average",
    High: "high",
  },
  "eyes.size": { Small: "small", Medium: "medium", Large: "large" },
  "eyes.shape": {
    Round: "round",
    Almond: "almond",
    "Narrow / hooded": "hooded",
  },
  "eyes.color": {
    "Brown / dark": "brown",
    "Hazel / green": "hazel_green",
    "Blue / grey": "blue_grey",
  },
  "eyes.spacing": {
    "Close-set": "close",
    Average: "average",
    "Wide-set": "wide",
  },
  "eyes.position": {
    "Higher than average": "high",
    Average: "average",
    "Lower than average": "low",
  },
  "eyes.orientation": {
    Upturned: "upturned",
    Level: "level",
    Downturned: "downturned",
  },
  "eyes.depth": {
    "Deep-set": "deep",
    Average: "average",
    "More protruding": "protruding",
  },
  "eyes.eyelids": {
    "Heavy / hooded": "hooded",
    Average: "average",
    "Prominent crease / monolid look": "monolid_or_crease",
  },
  "nose.type": {
    "Small / delicate": "small",
    Average: "average",
    "Large / prominent": "large",
  },
  "nose.length": { Short: "short", Medium: "medium", Long: "long" },
  "nose.width": { Narrow: "narrow", Medium: "medium", Wide: "broad" },
  "nose.bridge": {
    "Flat / low": "flat",
    Straight: "straight",
    "High / bumpy": "high",
  },
  "nose.bridge_width": { Narrow: "narrow", Medium: "medium", Broad: "broad" },
  "nose.tip": {
    Pointed: "pointed",
    Rounded: "rounded",
    "Bulbous / upturned": "bulbous",
  },
  "nose.projection": {
    "Flat / low": "low",
    Average: "average",
    "Strong projection": "strong",
  },
  "nose.nostrils": {
    Narrow: "narrow",
    Medium: "medium",
    "Flared / wide": "flared",
  },
  "cheeks.fullness": {
    "Hollow / thin": "hollow",
    Average: "average",
    "Full / chubby": "full",
  },
  "cheeks.bones": {
    Flat: "flat",
    Average: "average",
    "High / sharp": "high",
  },
  "cheeks.mid_width": { Narrow: "narrow", Medium: "medium", Wide: "wide" },
  "cheeks.contour": {
    "Soft / rounded": "soft",
    Mixed: "mixed",
    "Angular / carved": "angular",
  },
  "mouth.width": { Narrow: "narrow", Medium: "medium", Wide: "wide" },
  "mouth.position": { High: "high", Average: "average", Low: "low" },
  "mouth.upper_lip": { Thin: "thin", Medium: "medium", Full: "full" },
  "mouth.lower_lip": { Thin: "thin", Medium: "medium", Full: "full" },
  "mouth.lip_ratio": {
    "Upper bigger": "upper_dominant",
    "About equal": "balanced",
    "Lower bigger": "lower_dominant",
  },
  "mouth.cupids_bow": {
    "Soft / flat": "soft",
    Moderate: "moderate",
    "Very defined": "defined",
  },
  "mouth.corners": {
    Upturned: "upturned",
    Neutral: "neutral",
    Downturned: "downturned",
  },
  "jaw.width": { Narrow: "narrow", Medium: "medium", Wide: "wide" },
  "jaw.shape": {
    "Soft / rounded": "soft",
    Average: "average",
    "Square / angular": "square",
  },
  "jaw.definition": {
    "Soft / unclear": "soft",
    Average: "average",
    "Very defined": "defined",
  },
  "jaw.angle": { Soft: "soft", Medium: "medium", "Sharp / strong": "sharp" },
  "chin.size": { Small: "small", Medium: "medium", Large: "large" },
  "chin.width": { Narrow: "narrow", Medium: "medium", Broad: "broad" },
  "chin.shape": { Pointed: "pointed", Rounded: "rounded", Square: "square" },
  "chin.projection": {
    Receding: "receding",
    Average: "average",
    Projecting: "projecting",
  },
  "chin.cleft": { No: "none", Slight: "slight", "Clear cleft": "clear" },
  "ears.size": { Small: "small", Medium: "medium", Large: "large" },
  "ears.shape": {
    "Oval / regular": "oval",
    Wide: "wide",
    "Unusual / pointed": "pointed",
  },
  "ears.position": { High: "high", Mid: "mid", Low: "low" },
  "ears.protrusion": {
    "Close to head": "close",
    Average: "average",
    "Clearly protruding": "protruding",
  },
  "ears.lobes": {
    Attached: "attached",
    Average: "average",
    "Large / hanging": "hanging",
  },
  "facial_hair.beard": {
    None: "none",
    "Stubble / short": "short",
    "Full / long": "full",
  },
  "facial_hair.moustache": { None: "none", Thin: "thin", Thick: "thick" },
  "facial_hair.sideburns": { None: "none", Short: "short", Long: "long" },
  "facial_hair.density": {
    "Patchy / light": "light",
    Average: "average",
    Thick: "thick",
  },
  "facial_hair.color": {
    "Same as head hair": "matched",
    Darker: "darker",
    "Lighter / grey": "lighter",
  },
  "skin.appearance": {
    "Clear / smooth": "clear",
    Average: "average",
    "Rough / marked": "rough",
  },
  "skin.texture": {
    "Fine / soft": "fine",
    Normal: "normal",
    "Coarse / oily / dry look": "coarse",
  },
  "skin.wrinkles": { No: "none", Mild: "mild", Heavy: "heavy" },
  "skin.age_marks": {
    "None noticed": "none",
    "A few": "few",
    Many: "many",
  },
  "marks.scars": {
    None: "none",
    "Small / faint": "small",
    "Clear / large scar": "large",
  },
  "marks.moles": {
    None: "none",
    "One noticeable": "one",
    Several: "several",
  },
  "marks.birthmarks": {
    None: "none",
    Small: "small",
    "Large / obvious": "large",
  },
  "marks.tattoos": {
    None: "none",
    Small: "small",
    "Large / obvious": "large",
  },
  "marks.piercings": {
    None: "none",
    "Ear only": "ear",
    "Face / multiple": "face",
  },
  "marks.dimples": {
    None: "none",
    Slight: "slight",
    "Clear dimples": "clear",
  },
  "marks.asymmetry": { No: "none", Mild: "mild", "Strong asymmetry": "strong" },
  "accessories.glasses": {
    No: "none",
    "Everyday / thin frames": "thin",
    "Thick / dark frames": "thick",
  },
  "accessories.earrings": {
    No: "none",
    "Small studs": "studs",
    "Large / dangling": "dangling",
  },
  "accessories.headwear": {
    None: "none",
    "Cap / hat": "hat",
    "Hood / wrap / other cover": "hood",
  },
  "context.view_angle": {
    "Straight on": "frontal",
    "Slight three-quarter": "three_quarter",
    "Side / profile": "profile",
  },
  "context.head_position": {
    Level: "level",
    Tilted: "tilted",
    "Chin up / down": "chin_tilt",
  },
  "context.expression": {
    Neutral: "neutral",
    "Tense / angry": "tense",
    "Smiling / talking": "smiling",
  },
  "context.lighting": {
    "Bright / clear": "bright",
    Average: "average",
    "Dim / hard to see": "dim",
  },
  "holistic.distinctiveness": {
    Ordinary: "ordinary",
    "Somewhat unique": "unique",
    "Very unique": "very_unique",
  },
  "holistic.age_confirm": {
    "Under ~25": "under_25",
    "About 25–45": "25_45",
    "Over ~45": "over_45",
  },
  "holistic.impression": {
    "Soft / approachable": "soft",
    "Hard / stern": "stern",
    "Ordinary / forgettable": "ordinary",
  },
};

/** Free-text synonym rules (field-specific first, then generic) */
const FREE_TEXT_RULES: Record<string, Rule[]> = {
  "nose.width": [
    { value: "broad", match: ["quite wide", "very wide", "broad", "wide", "big nose", "large width"], confidence: 0.8 },
    { value: "narrow", match: ["narrow", "thin", "skinny", "small width"], confidence: 0.8 },
    { value: "medium", match: ["medium", "average", "normal", "not sure"], confidence: 0.6 },
  ],
  "nose.length": [
    { value: "long", match: ["long", "lengthy"], confidence: 0.8 },
    { value: "short", match: ["short", "small"], confidence: 0.8 },
    { value: "medium", match: ["medium", "average"], confidence: 0.6 },
  ],
  "face.shape": [
    { value: "oval", match: ["oval"], confidence: 0.9 },
    { value: "round", match: ["round", "circular", "chubby face"], confidence: 0.85 },
    { value: "square", match: ["square", "rectangular", "boxy"], confidence: 0.85 },
    { value: "heart", match: ["heart"], confidence: 0.9 },
    { value: "diamond", match: ["diamond"], confidence: 0.9 },
  ],
  "eyes.shape": [
    { value: "almond", match: ["almond"], confidence: 0.9 },
    { value: "round", match: ["round"], confidence: 0.85 },
    { value: "hooded", match: ["hooded", "narrow"], confidence: 0.8 },
  ],
};

const GENERIC_SIZE: Rule[] = [
  { value: "narrow", match: ["narrow", "thin", "slim"], confidence: 0.75 },
  { value: "broad", match: ["broad", "quite wide", "very wide", "wide"], confidence: 0.75 },
  { value: "wide", match: ["wide"], confidence: 0.7 },
  { value: "medium", match: ["medium", "average", "normal"], confidence: 0.65 },
  { value: "small", match: ["small", "tiny"], confidence: 0.75 },
  { value: "large", match: ["large", "big", "huge"], confidence: 0.75 },
  { value: "none", match: ["none", "no", "nothing", "not sure", "unsure", "don't remember", "dont remember"], confidence: 0.55 },
];

function slugifyRaw(raw: string): string {
  return raw
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 48) || "unknown";
}

function matchRules(rawLower: string, rules: Rule[]): NormalizedCell | null {
  for (const rule of rules) {
    for (const m of rule.match) {
      const hit =
        typeof m === "string"
          ? rawLower.includes(m)
          : m.test(rawLower);
      if (hit) {
        return {
          value: rule.value,
          confidence: rule.confidence ?? 0.75,
          raw: rawLower, // overwritten by caller
        };
      }
    }
  }
  return null;
}

/**
 * Normalize one raw interview answer into a canonical attribute cell.
 */
export function normalizeAnswer(
  key: string,
  raw: string,
  source: "option" | "other",
): NormalizedCell {
  const trimmed = raw.trim();
  const rawOut = trimmed;

  // Experiment / GT sentinel — do not invent taxonomy tokens
  const lowerSentinel = trimmed.toLowerCase();
  if (
    lowerSentinel === "not_available" ||
    lowerSentinel === "unknown" ||
    lowerSentinel === "n/a"
  ) {
    return {
      value: "not_available",
      confidence: 0,
      raw: rawOut,
    };
  }

  // 1) Exact option map (MCQ click)
  const optionCanon = OPTION_MAP[key]?.[trimmed];
  if (optionCanon) {
    return {
      value: optionCanon,
      confidence: source === "option" ? 0.9 : 0.85,
      raw: rawOut,
    };
  }

  // Case-insensitive option lookup
  const optionTable = OPTION_MAP[key];
  if (optionTable) {
    const found = Object.entries(optionTable).find(
      ([label]) => label.toLowerCase() === trimmed.toLowerCase(),
    );
    if (found) {
      return { value: found[1], confidence: 0.88, raw: rawOut };
    }
  }

  const lower = trimmed.toLowerCase();

  // 2) Field-specific free-text rules
  const fieldHit = FREE_TEXT_RULES[key]
    ? matchRules(lower, FREE_TEXT_RULES[key]!)
    : null;
  if (fieldHit) {
    return { ...fieldHit, raw: rawOut };
  }

  // 3) Generic size / none heuristics
  const genericHit = matchRules(lower, GENERIC_SIZE);
  if (genericHit) {
    // Prefer "broad" over "wide" for *width fields when matched via quite/very wide
    if (
      key.endsWith(".width") &&
      genericHit.value === "wide" &&
      /broad|quite wide|very wide/.test(lower)
    ) {
      return { value: "broad", confidence: 0.8, raw: rawOut };
    }
    return { ...genericHit, raw: rawOut };
  }

  // 4) Fallback — keep a slug so we don't drop data, but low confidence
  return {
    value: slugifyRaw(trimmed),
    confidence: 0.4,
    raw: rawOut,
  };
}

export type RawAnswer = {
  key: string;
  group: string;
  value: string;
  source: "option" | "other";
};

/**
 * Normalize a full raw interview into structured attributes.
 * This is the MODEL representation (canonical tokens), not the chat log.
 */
export function normalizeInterview(rawAnswers: RawAnswer[]): StructuredAttributes {
  const structured: StructuredAttributes = {};

  for (const a of rawAnswers) {
    const [group, field] = a.key.split(".");
    if (!group || !field) continue;
    const cell = normalizeAnswer(a.key, a.value, a.source);
    if (!structured[group]) structured[group] = {};
    structured[group][field] = cell;
  }

  return structured;
}

/** Compact view for logging / prompt: { nose: { width: "broad", ... } } style values only */
export function structuredValuesOnly(
  structured: StructuredAttributes,
): Record<string, Record<string, string>> {
  const out: Record<string, Record<string, string>> = {};
  for (const [g, fields] of Object.entries(structured)) {
    out[g] = {};
    for (const [f, cell] of Object.entries(fields)) {
      out[g]![f] = cell.value;
    }
  }
  return out;
}
