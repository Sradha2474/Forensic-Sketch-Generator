"""Unit tests for profile + prompt builder (no GPU required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai.prompt_builder import build_face_prompt, build_prompt, build_sketch_prompt
from utils.profile import WitnessProfile, build_profile, profile_to_json, save_profile


def test_build_profile_filters_unknown_keys():
    profile = build_profile(gender="Male", age_range="Adult (30-39)", not_a_field=123)
    assert profile.gender == "Male"
    assert not hasattr(profile, "not_a_field")


def test_profile_json_roundtrip_structure():
    profile = WitnessProfile(
        gender="Male",
        age_range="Young adult (20-29)",
        face_shape="Oval",
        hair_color="Black",
        eye_color="Brown",
        scars="scar on left cheek",
        accessories=["Glasses"],
    )
    data = json.loads(profile_to_json(profile))
    assert data["demographics"]["gender"] == "Male"
    assert data["face"]["shape"] == "Oval"
    assert data["distinguishing_marks"]["scars"] == "scar on left cheek"
    assert "Glasses" in data["accessories"]


def test_save_profile(tmp_path):
    profile = WitnessProfile(gender="Female")
    path = save_profile(profile, directory=tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["demographics"]["gender"] == "Female"


def test_prompt_contains_core_attributes():
    profile = WitnessProfile(
        gender="Male",
        age_range="Adult (30-39)",
        face_shape="Square",
        hair_color="Brown",
        hair_length="Short",
        hair_style="Wavy",
        eye_color="Blue",
        eye_shape="Almond",
        jaw="Angular",
        scars="thin scar on chin",
        accessories=["Glasses"],
    )
    positive, negative = build_prompt(profile)
    assert "male" in positive.lower()
    assert "square" in positive.lower()
    assert "blue" in positive.lower()
    assert "glasses" in positive.lower()
    assert "scar" in positive.lower()
    assert "pencil" in positive.lower() or "graphite" in positive.lower()
    assert "blurry" in negative.lower()
    assert len(positive.split()) <= 75

    face_p, _ = build_face_prompt(profile)
    sketch_p, _ = build_sketch_prompt(profile)
    assert "portrait" in face_p.lower() or "photo" in face_p.lower()
    assert "pencil" in sketch_p.lower() or "graphite" in sketch_p.lower()


def test_bald_hair_handling():
    profile = WitnessProfile(hair_color="Bald", hair_length="Bald", gender="Male")
    positive, _ = build_prompt(profile)
    assert "bald" in positive.lower()
