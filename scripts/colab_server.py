# scripts/colab_server.py
# Run ENTIRELY INSIDE GOOGLE COLAB (Runtime -> GPU). Paste each "# %%"
# block as its own Colab cell.

# %% [1] Install deps
# !pip install -q diffusers transformers accelerate safetensors peft controlnet-aux \
#     opencv-python-headless compel fastapi uvicorn pyngrok python-multipart

# %% [2] ngrok auth -- free account at https://dashboard.ngrok.com/signup
from pyngrok import ngrok
NGROK_AUTH_TOKEN = "PASTE_YOUR_NGROK_TOKEN_HERE"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# %% [3] Imports + model loading
import io, base64
import cv2
import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import nest_asyncio
import uvicorn

from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    UniPCMultistepScheduler,
)
from compel import Compel

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
BASE_MODEL = "runwayml/stable-diffusion-v1-5"

base_pipe = StableDiffusionPipeline.from_pretrained(
    BASE_MODEL, torch_dtype=DTYPE, safety_checker=None
).to(DEVICE)
base_pipe.scheduler = UniPCMultistepScheduler.from_config(base_pipe.scheduler.config)

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny", torch_dtype=DTYPE
)
refine_pipe = StableDiffusionControlNetPipeline.from_pretrained(
    BASE_MODEL, controlnet=controlnet, torch_dtype=DTYPE, safety_checker=None
).to(DEVICE)
refine_pipe.scheduler = UniPCMultistepScheduler.from_config(refine_pipe.scheduler.config)
refine_pipe.load_lora_weights("jordanhilado/sd-1-5-sketch-lora")
refine_pipe.fuse_lora(lora_scale=0.8)

QUALITY_TAGS = (
    "forensic pencil sketch, monochrome, detailed linework, "
    "front-facing police composite portrait, high detail, sharp focus"
)
NEGATIVE_PROMPT = (
    "color, colour, cartoon, anime, painting, blurry, extra limbs, deformed, "
    "watermark, text, low detail, jpeg artifacts, multiple faces, disfigured"
)

def build_prompt(desc: str) -> str:
    return f"{desc.strip().rstrip('.')}, {QUALITY_TAGS}"

def get_long_prompt_embeddings(pipe, prompt, negative_prompt):
    compel_proc = Compel(tokenizer=pipe.tokenizer, text_encoder=pipe.text_encoder)
    p = compel_proc.build_conditioning_tensor(prompt)
    n = compel_proc.build_conditioning_tensor(negative_prompt)
    [p, n] = compel_proc.pad_conditioning_tensors_to_same_length([p, n])
    return p, n

def to_canny(image: Image.Image) -> Image.Image:
    arr = np.array(image.convert("RGB"))
    edges = cv2.Canny(arr, 100, 200)
    return Image.fromarray(np.stack([edges] * 3, axis=-1))

def image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def generate_baseline(description: str, seed: int = 42) -> Image.Image:
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    p, n = get_long_prompt_embeddings(base_pipe, build_prompt(description), NEGATIVE_PROMPT)
    return base_pipe(
        prompt_embeds=p, negative_prompt_embeds=n,
        num_inference_steps=30, guidance_scale=7.5, generator=generator,
    ).images[0]

def generate_refined(description: str, seed: int = 42, cn_scale: float = 0.75):
    baseline_img = generate_baseline(description, seed=seed)
    canny_img = to_canny(baseline_img)
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    p, n = get_long_prompt_embeddings(refine_pipe, build_prompt(description), NEGATIVE_PROMPT)
    refined_img = refine_pipe(
        prompt_embeds=p, negative_prompt_embeds=n, image=canny_img,
        num_inference_steps=30, guidance_scale=7.5,
        controlnet_conditioning_scale=cn_scale, generator=generator,
    ).images[0]
    return baseline_img, canny_img, refined_img

# %% [4] FastAPI app
app = FastAPI(title="Forensic Sketch ControlNet API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class SketchRequest(BaseModel):
    description: str
    seed: int = 42
    controlnet_scale: float = 0.75

@app.post("/compare")
def api_compare(req: SketchRequest):
    baseline_img, canny_img, refined_img = generate_refined(
        req.description, seed=req.seed, cn_scale=req.controlnet_scale
    )
    return {
        "baseline": image_to_b64(baseline_img),
        "canny_edges": image_to_b64(canny_img),
        "controlnet_lora_refined": image_to_b64(refined_img),
    }

@app.get("/health")
def health():
    return {"status": "ok", "device": DEVICE}

# %% [5] Launch (blocks -- keep this Colab tab open while the app is using it)
nest_asyncio.apply()
public_url = ngrok.connect(8000)
print("=" * 60)
print(f"Public API URL: {public_url}")
print("Paste this into the Python backend's .env as COLAB_API_URL")
print("=" * 60)
uvicorn.run(app, host="0.0.0.0", port=8000)
