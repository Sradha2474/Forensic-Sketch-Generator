"""
Map CelebA binary attributes → interview_90.json answers.

CRITICAL: only map when CelebA provides clear evidence.
Unmapped interview keys → value "not_available" (never invent "medium").
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from celeba_loader import load_celeba_attributes

ROOT = Path(__file__).resolve().parents[2]
INTERVIEW_TS = ROOT / "forenisic" / "lib" / "interview-questions.ts"

NOT_AVAILABLE = "not_available"


def load_interview_schema() -> list[dict[str, str]]:
    """Parse keys + groups from interview-questions.ts."""
    text = INTERVIEW_TS.read_text(encoding="utf-8")
    keys = re.findall(r'key:\s*"([^"]+)"', text)
    groups = re.findall(r'group:\s*"([^"]+)"', text)
    if len(keys) != len(groups):
        raise RuntimeError("Failed to parse interview keys/groups evenly")
    return [{"key": k, "group": g} for k, g in zip(keys, groups)]


def _map_celeba_to_answers(attrs: dict[str, bool]) -> dict[str, str]:
    """
    Return sparse map: interview_key → option label string (or sentinel).
    Only includes keys we can justify from CelebA.
    """
    out: dict[str, str] = {}

    # Age
    if "Young" in attrs:
        if attrs["Young"]:
            out["age.range"] = "Teen / early 20s"
            out["holistic.age_confirm"] = "Under ~25"
        else:
            out["age.range"] = "About 50 or older"
            out["holistic.age_confirm"] = "Over ~45"

    # Hair color — first positive only; conflicting positives → skip (not invent)
    color_priority = [
        ("Black_Hair", "Black / dark brown"),
        ("Brown_Hair", "Brown / auburn"),
        ("Blond_Hair", "Blonde / grey / light"),
        ("Gray_Hair", "Blonde / grey / light"),
    ]
    positives = [label for name, label in color_priority if attrs.get(name)]
    if len(positives) == 1:
        out["hair.color"] = positives[0]
    elif len(set(positives)) == 1 and positives:
        out["hair.color"] = positives[0]
    # else leave unmapped (not_available)

    # Bald
    if attrs.get("Bald"):
        out["hair.length"] = "Shaved / bald / buzz"

    # Hair texture — only if exactly one of straight/wavy
    straight = attrs.get("Straight_Hair", False)
    wavy = attrs.get("Wavy_Hair", False)
    if straight and not wavy:
        out["hair.texture"] = "Straight"
    elif wavy and not straight:
        out["hair.texture"] = "Wavy"

    # Hairline
    if attrs.get("Receding_Hairline"):
        out["hair.hairline"] = "Receding"

    # Brows — only assert when CelebA positive; false → leave not_available
    if attrs.get("Bushy_Eyebrows"):
        out["brows.thickness"] = "Thick / bushy"
    if attrs.get("Arched_Eyebrows"):
        out["brows.shape"] = "Strongly arched"

    # Eyes
    if attrs.get("Narrow_Eyes"):
        out["eyes.size"] = "Small"
    if attrs.get("Bags_Under_Eyes"):
        # no direct key — leave not_available for bags
        pass

    # Nose — only assert when Big_Nose / Pointy_Nose true; false → not_available
    if attrs.get("Big_Nose"):
        out["nose.width"] = "Wide"
        out["nose.type"] = "Large / prominent"
    if attrs.get("Pointy_Nose"):
        out["nose.tip"] = "Pointed"

    # Face
    if attrs.get("Oval_Face"):
        out["face.shape"] = "Oval"
    if attrs.get("Chubby"):
        out["cheeks.fullness"] = "Full / chubby"
    if attrs.get("High_Cheekbones"):
        out["cheeks.bones"] = "High / sharp"
    if attrs.get("Double_Chin"):
        out["chin.size"] = "Large"

    # Mouth / lips
    if attrs.get("Big_Lips"):
        out["mouth.upper_lip"] = "Full"
        out["mouth.lower_lip"] = "Full"

    # Expression
    if "Smiling" in attrs:
        out["context.expression"] = (
            "Smiling / talking" if attrs["Smiling"] else "Neutral"
        )
    if attrs.get("Mouth_Slightly_Open") and "context.expression" not in out:
        out["context.expression"] = "Smiling / talking"

    # Facial hair
    # No_Beard True → none; No_Beard False → has beard (stubble/short unknown length)
    if "No_Beard" in attrs:
        if attrs["No_Beard"]:
            out["facial_hair.beard"] = "None"
        else:
            out["facial_hair.beard"] = "Stubble / short"
    if "Mustache" in attrs:
        out["facial_hair.moustache"] = "Thick" if attrs["Mustache"] else "None"
    if "Goatee" in attrs and attrs["Goatee"]:
        # goatee implies beard present; don't invent density
        out["facial_hair.beard"] = out.get("facial_hair.beard", "Stubble / short")
    if "Sideburns" in attrs:
        out["facial_hair.sideburns"] = "Short" if attrs["Sideburns"] else "None"
    if attrs.get("5_o_Clock_Shadow") and out.get("facial_hair.beard") in (None, "None"):
        out["facial_hair.beard"] = "Stubble / short"

    # Accessories
    if "Eyeglasses" in attrs:
        out["accessories.glasses"] = (
            "Everyday / thin frames" if attrs["Eyeglasses"] else "No"
        )
    if "Wearing_Hat" in attrs:
        out["accessories.headwear"] = (
            "Cap / hat" if attrs["Wearing_Hat"] else "None"
        )
    if "Wearing_Earrings" in attrs:
        out["accessories.earrings"] = (
            "Small studs" if attrs["Wearing_Earrings"] else "No"
        )

    # Pale_Skin has no matching interview option → leave not_available

    # View: CelebA aligned faces are front-facing (dataset property, not invented identity traits)
    out["context.view_angle"] = "Straight on"

    # Male is kept in ground_truth only (no interview gender key) — do not invent.

    return out


def celeba_to_interview90(
    image_id: str,
    attrs: dict[str, bool] | None = None,
) -> list[dict[str, Any]]:
    """
    Full interview_90 list covering every schema key.
    source: "celeba" | "not_available"
    """
    attrs = attrs or load_celeba_attributes(image_id)
    mapped = _map_celeba_to_answers(attrs)
    schema = load_interview_schema()

    answers: list[dict[str, Any]] = []
    for item in schema:
        key = item["key"]
        group = item["group"]
        if key in mapped:
            answers.append(
                {
                    "key": key,
                    "group": group,
                    "value": mapped[key],
                    "source": "celeba",
                }
            )
        else:
            answers.append(
                {
                    "key": key,
                    "group": group,
                    "value": NOT_AVAILABLE,
                    "source": "not_available",
                }
            )
    return answers


def mapped_keys_summary(answers: list[dict[str, Any]]) -> dict[str, int]:
    celeba_n = sum(1 for a in answers if a["source"] == "celeba")
    na_n = sum(1 for a in answers if a["source"] == "not_available")
    return {"celeba_mapped": celeba_n, "not_available": na_n, "total": len(answers)}


if __name__ == "__main__":
    ans = celeba_to_interview90("001089.jpg")
    print(mapped_keys_summary(ans))
    for a in ans:
        if a["source"] == "celeba":
            print(f"  {a['key']}: {a['value']}")
