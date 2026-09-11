"""
CLIP zero-shot CelebA attribute probing for Experiment 1A evaluation.

Scores generated images against available CelebA ground-truth booleans only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from PIL import Image


# (celeba_attr, prompt_if_true, prompt_if_false)
ATTR_PROBES: dict[str, tuple[str, str]] = {
    "Male": ("a photo of a man", "a photo of a woman"),
    "Young": ("a photo of a young person", "a photo of an older person"),
    "Smiling": ("a person who is smiling", "a person with a neutral expression"),
    "Black_Hair": ("a person with black hair", "a person without black hair"),
    "Brown_Hair": ("a person with brown hair", "a person without brown hair"),
    "Blond_Hair": ("a person with blond hair", "a person without blond hair"),
    "Gray_Hair": ("a person with gray hair", "a person without gray hair"),
    "Straight_Hair": ("a person with straight hair", "a person with non-straight hair"),
    "Wavy_Hair": ("a person with wavy hair", "a person without wavy hair"),
    "Bald": ("a bald person", "a person with hair"),
    "Big_Nose": ("a person with a big nose", "a person with a small nose"),
    "Big_Lips": ("a person with big lips", "a person with thin lips"),
    "Mustache": ("a person with a mustache", "a person without a mustache"),
    "No_Beard": ("a clean-shaven person with no beard", "a person with a beard"),
    "Goatee": ("a person with a goatee", "a person without a goatee"),
    "Sideburns": ("a person with sideburns", "a person without sideburns"),
    "Eyeglasses": ("a person wearing eyeglasses", "a person not wearing eyeglasses"),
    "Wearing_Hat": ("a person wearing a hat", "a person not wearing a hat"),
    "Wearing_Earrings": ("a person wearing earrings", "a person not wearing earrings"),
    "High_Cheekbones": ("a person with high cheekbones", "a person with flat cheekbones"),
    "Chubby": ("a chubby person", "a slim-faced person"),
    "Double_Chin": ("a person with a double chin", "a person without a double chin"),
    "Oval_Face": ("a person with an oval face", "a person with a non-oval face"),
    "Pointy_Nose": ("a person with a pointy nose", "a person with a rounded nose"),
    "Narrow_Eyes": ("a person with narrow eyes", "a person with wide eyes"),
    "Bushy_Eyebrows": ("a person with bushy eyebrows", "a person with thin eyebrows"),
    "Arched_Eyebrows": ("a person with arched eyebrows", "a person with straight eyebrows"),
    "Mouth_Slightly_Open": ("a person with mouth slightly open", "a person with mouth closed"),
    "Receding_Hairline": ("a person with a receding hairline", "a person with a full hairline"),
    "Pale_Skin": ("a person with pale skin", "a person with darker skin"),
    "5_o_Clock_Shadow": ("a person with five o'clock shadow", "a clean-shaven person"),
}


_clip_model = None
_clip_processor = None


def _get_clip(device: str | None = None):
    global _clip_model, _clip_processor
    if _clip_model is not None:
        return _clip_model, _clip_processor, device or ("cuda" if torch.cuda.is_available() else "cpu")

    from transformers import CLIPModel, CLIPProcessor

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model_id = "openai/clip-vit-base-patch32"
    _clip_processor = CLIPProcessor.from_pretrained(model_id)
    _clip_model = CLIPModel.from_pretrained(model_id).to(device)
    _clip_model.eval()
    return _clip_model, _clip_processor, device


@torch.inference_mode()
def probe_attribute(image: Image.Image, attr: str) -> bool:
    """Return True if CLIP prefers the positive CelebA probe for `attr`."""
    if attr not in ATTR_PROBES:
        raise KeyError(f"No CLIP probe for attribute: {attr}")
    pos, neg = ATTR_PROBES[attr]
    model, processor, device = _get_clip()
    inputs = processor(
        text=[pos, neg],
        images=image.convert("RGB"),
        return_tensors="pt",
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)[0]
    return bool(probs[0] >= probs[1])


def evaluate_image_against_gt(
    image_path: Path,
    available_attributes: dict[str, bool],
) -> dict[str, Any]:
    """
    Compare CLIP-predicted attributes to CelebA GT.
    Only evaluates attrs that exist in available_attributes AND have a probe.
    """
    image = Image.open(image_path).convert("RGB")
    rows: list[dict[str, Any]] = []
    correct = 0
    total = 0

    for attr, gt in sorted(available_attributes.items()):
        if attr not in ATTR_PROBES:
            continue
        pred = probe_attribute(image, attr)
        match = pred == gt
        total += 1
        if match:
            correct += 1
        rows.append(
            {
                "attribute": attr,
                "ground_truth": gt,
                "predicted": pred,
                "correct": match,
            }
        )

    accuracy = (correct / total) if total else None
    return {
        "image": str(image_path.name),
        "correct": correct,
        "total": total,
        "attribute_accuracy": accuracy,
        "rows": rows,
    }
