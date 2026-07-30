"""
Structured witness profile schema.

This is the MVP stand-in for the future Interview Agent module.
Attributes are collected via the Streamlit form and stored as JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import settings


# ---------------------------------------------------------------------------
# Controlled vocabularies used by the interview form
# ---------------------------------------------------------------------------

FACE_SHAPES = ["Oval", "Round", "Square", "Heart", "Diamond", "Rectangular", "Triangular"]
HAIR_COLORS = ["Black", "Dark brown", "Brown", "Light brown", "Blonde", "Red", "Gray", "White", "Bald"]
HAIR_LENGTHS = ["Bald", "Buzz cut", "Short", "Medium", "Long", "Shoulder-length"]
HAIR_STYLES = ["Straight", "Wavy", "Curly", "Coily", "Receding", "Thinning", "Afro", "Ponytail", "Unknown"]
FACIAL_HAIR = ["None / clean-shaven", "Stubble", "Mustache", "Goatee", "Full beard", "Soul patch", "Sideburns"]
EYE_COLORS = ["Brown", "Dark brown", "Hazel", "Green", "Blue", "Gray", "Black"]
EYE_SHAPES = ["Almond", "Round", "Hooded", "Deep-set", "Wide-set", "Close-set", "Monolid"]
EYEBROWS = ["Thin", "Medium", "Thick", "Bushy", "Arched", "Straight", "Connected"]
NOSE_SIZES = ["Small", "Medium", "Large"]
NOSE_SHAPES = ["Straight", "Aquiline / hooked", "Button", "Broad", "Narrow", "Upturned", "Flat"]
LIP_SIZES = ["Thin", "Medium", "Full"]
JAW_TYPES = ["Square", "Rounded", "Narrow", "Wide", "Angular", "Soft"]
SKIN_TONES = ["Very fair", "Fair", "Light", "Medium", "Olive", "Tan", "Brown", "Dark brown", "Deep"]
AGE_RANGES = [
    "Teen (13-19)",
    "Young adult (20-29)",
    "Adult (30-39)",
    "Middle-aged (40-54)",
    "Older adult (55-69)",
    "Elderly (70+)",
]
GENDERS = ["Male", "Female", "Non-binary / other", "Unknown"]
ETHNICITIES = [
    "Not specified",
    "South Asian / Indian",
    "East Asian",
    "Southeast Asian",
    "Middle Eastern",
    "White / Caucasian",
    "Black / African",
    "Hispanic / Latino",
    "Mixed",
    "Other",
]
ACCESSORIES = ["Glasses", "Sunglasses", "Hat / cap", "Earrings", "Nose ring", "Headscarf / hijab", "Necklace"]


@dataclass
class WitnessProfile:
    """Structured facial-attribute profile from a witness interview."""

    # Demographics
    gender: str = "Unknown"
    age_range: str = "Adult (30-39)"
    ethnicity: str = "Not specified"
    skin_tone: str = "Medium"

    # Face structure
    face_shape: str = "Oval"
    jaw: str = "Rounded"
    cheekbones: str = "Average"

    # Hair
    hair_color: str = "Black"
    hair_length: str = "Short"
    hair_style: str = "Straight"
    facial_hair: str = "None / clean-shaven"

    # Eyes
    eye_color: str = "Brown"
    eye_shape: str = "Almond"
    eyebrows: str = "Medium"

    # Nose & lips
    nose_size: str = "Medium"
    nose_shape: str = "Straight"
    lip_size: str = "Medium"

    # Distinguishing features
    accessories: list[str] = field(default_factory=list)
    scars: str = ""
    moles: str = ""
    tattoos: str = ""
    other_marks: str = ""

    # Free-text notes (optional)
    additional_notes: str = ""

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    profile_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))

    def to_dict(self) -> dict[str, Any]:
        """Nested dict suitable for JSON serialization and UI display."""
        return {
            "profile_id": self.profile_id,
            "created_at": self.created_at,
            "demographics": {
                "gender": self.gender,
                "age_range": self.age_range,
                "ethnicity": self.ethnicity,
                "skin_tone": self.skin_tone,
            },
            "face": {
                "shape": self.face_shape,
                "jaw": self.jaw,
                "cheekbones": self.cheekbones,
            },
            "hair": {
                "color": self.hair_color,
                "length": self.hair_length,
                "style": self.hair_style,
                "facial_hair": self.facial_hair,
            },
            "eyes": {
                "color": self.eye_color,
                "shape": self.eye_shape,
                "eyebrows": self.eyebrows,
            },
            "nose": {
                "size": self.nose_size,
                "shape": self.nose_shape,
            },
            "lips": {
                "size": self.lip_size,
            },
            "accessories": list(self.accessories),
            "distinguishing_marks": {
                "scars": self.scars,
                "moles": self.moles,
                "tattoos": self.tattoos,
                "other": self.other_marks,
            },
            "additional_notes": self.additional_notes,
        }

    def flat_dict(self) -> dict[str, Any]:
        """Flat attribute map (useful for prompt builder / future evaluation)."""
        return asdict(self)


def build_profile(**kwargs: Any) -> WitnessProfile:
    """Construct a WitnessProfile, ignoring unknown keys."""
    valid = {f.name for f in WitnessProfile.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    filtered = {k: v for k, v in kwargs.items() if k in valid}
    return WitnessProfile(**filtered)


def profile_to_json(profile: WitnessProfile, indent: int = 2) -> str:
    return json.dumps(profile.to_dict(), indent=indent, ensure_ascii=False)


def save_profile(profile: WitnessProfile, directory: Path | None = None) -> Path:
    """Persist the witness profile as JSON under outputs/."""
    out_dir = Path(directory or settings.outputs_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"profile_{profile.profile_id}.json"
    path.write_text(profile_to_json(profile), encoding="utf-8")
    return path
