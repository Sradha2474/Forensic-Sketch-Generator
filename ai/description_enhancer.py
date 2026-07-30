"""
Rule-based witness description enhancer.

MVP stand-in for an LLM interview agent: expands short notes into a
structured forensic description before prompt engineering / SD generation.
"""

from __future__ import annotations

import re


def enhance_description(raw: str) -> str:
    """
    Improve a short witness note into a detailed structured description.

    Example:
      "Man with beard." →
      "Male, approximately 35 years old, oval face, ..."
    """
    text = (raw or "").strip()
    if not text:
        return (
            "Male, approximately 30 years old, oval face, medium complexion, "
            "short black hair, thick eyebrows, brown eyes, straight nose, "
            "medium lips, front-facing view"
        )

    lower = text.lower()

    # If already reasonably detailed, lightly normalize and return
    if len(text.split()) >= 18 and any(k in lower for k in ("face", "hair", "eye", "nose", "lip")):
        cleaned = re.sub(r"\s+", " ", text).strip()
        if cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        if not cleaned.endswith("."):
            cleaned += "."
        return cleaned

    gender = "Male"
    if any(w in lower for w in ("woman", "female", "lady", "girl")):
        gender = "Female"
    elif any(w in lower for w in ("man", "male", "guy", "boy")):
        gender = "Male"

    age = "approximately 30 years old"
    if re.search(r"\b(1[89]|2\d)\b", lower) or "young" in lower or "20" in lower:
        age = "approximately 25 years old"
    elif re.search(r"\b(3\d)\b", lower) or "30" in lower:
        age = "approximately 35 years old"
    elif re.search(r"\b(4\d)\b", lower) or "40" in lower or "middle" in lower:
        age = "approximately 45 years old"
    elif re.search(r"\b(5\d|60|elderly|old)\b", lower):
        age = "approximately 55 years old"

    face = "oval face"
    for shape in ("oval", "round", "square", "heart", "diamond", "rectangular"):
        if shape in lower:
            face = f"{shape} face"
            break

    skin = "medium complexion"
    for tone, label in (
        ("fair", "fair complexion"),
        ("light", "light complexion"),
        ("olive", "olive complexion"),
        ("brown", "medium brown complexion"),
        ("dark", "dark complexion"),
        ("black skin", "dark complexion"),
    ):
        if tone in lower:
            skin = label
            break

    hair = "short black hair"
    if "bald" in lower:
        hair = "bald head"
    else:
        color = "black"
        for c in ("blonde", "blond", "brown", "red", "gray", "grey", "white"):
            if c in lower:
                color = "blonde" if c in ("blonde", "blond") else c
                break
        length = "short"
        for L in ("long", "medium", "buzz", "curly", "wavy", "straight"):
            if L in lower:
                length = L
                break
        if "curly" in lower:
            hair = f"short curly {color} hair" if length == "short" else f"{length} curly {color} hair"
        elif "wavy" in lower:
            hair = f"{length} wavy {color} hair"
        else:
            hair = f"{length} {color} hair"

    facial_hair = ""
    if "beard" in lower:
        facial_hair = "full black beard" if gender == "Male" else "light facial hair"
    elif "mustache" in lower or "moustache" in lower:
        facial_hair = "thin mustache"
    elif "stubble" in lower:
        facial_hair = "light stubble"

    brows = "thick eyebrows" if "brow" in lower or "eyebrow" in lower else "medium eyebrows"
    if "thick" in lower and "brow" in lower:
        brows = "thick eyebrows"
    elif "thin" in lower and "brow" in lower:
        brows = "thin eyebrows"

    eyes = "brown eyes"
    for c in ("blue", "green", "hazel", "gray", "grey", "black", "brown"):
        if f"{c} eye" in lower or f"{c}-eye" in lower:
            eyes = f"{c} eyes"
            break

    nose = "straight nose"
    for n in ("straight", "broad", "narrow", "hooked", "button", "aquiline"):
        if n in lower and "nose" in lower:
            nose = f"{n} nose"
            break
    else:
        if "nose" in lower:
            nose = "medium nose"

    lips = "medium lips"
    if "thin lip" in lower:
        lips = "thin lips"
    elif "full lip" in lower:
        lips = "full lips"

    accessories = []
    if "glass" in lower:
        if "rectangular" in lower:
            accessories.append("wearing rectangular glasses")
        else:
            accessories.append("wearing glasses")
    if "hoodie" in lower:
        accessories.append("wearing a black hoodie")
    if "hat" in lower or "cap" in lower:
        accessories.append("wearing a cap")

    marks = []
    scar = re.search(r"scar[^.]*", lower)
    if scar:
        marks.append(scar.group(0).strip())
    if "mole" in lower:
        marks.append("mole on the face")

    # Defaults that match the user's example style when input is very short
    if len(text.split()) <= 6:
        if gender == "Male" and "beard" in lower:
            return (
                "Male, approximately 35 years old, oval face, medium complexion, "
                "full black beard, short black hair, thick eyebrows, straight nose, "
                "brown eyes, wearing a black hoodie."
            )
        if gender == "Female":
            return (
                "Female, approximately 30 years old, oval face, medium complexion, "
                "shoulder-length brown hair, arched eyebrows, brown eyes, straight nose, "
                "medium lips, front-facing view."
            )

    parts = [
        gender,
        age,
        face,
        skin,
        hair,
    ]
    if facial_hair:
        parts.append(facial_hair)
    parts.extend([brows, eyes, nose, lips])
    parts.extend(accessories)
    parts.extend(marks)

    result = ", ".join(parts)
    if not result.endswith("."):
        result += "."
    return result[0].upper() + result[1:]
