# %% COLAB FIX CELL — interrupt old uvicorn first, then paste & run this ENTIRE cell
# Requires cell [3] models already loaded: refine_pipe, DEVICE, to_canny, build_prompt,
# get_long_prompt_embeddings, image_to_b64, NEGATIVE_PROMPT, base64, io, Image, torch

import traceback
from pydantic import BaseModel
import nest_asyncio
import uvicorn
from pyngrok import ngrok
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Forensic Sketch ControlNet API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class SketchRequest(BaseModel):
    description: str
    seed: int = 42
    controlnet_scale: float = 0.75

class PhotoSketchRequest(BaseModel):
    image_base64: str
    description: str = (
        "young South Asian woman early 20s, oval soft face, thick WAVY dark hair "
        "past shoulders, dark almond eyes, subtle smile, dark eyebrows, "
        "tiny nose stud left nostril, white collared shirt, thin chain necklace"
    )
    seed: int = 42
    controlnet_scale: float = 1.0

def _resize_512(img):
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    return img.convert("RGB").resize((512, 512), resample)

def generate_from_photo(photo, description, seed=42, cn_scale=1.0):
    photo = _resize_512(photo)
    canny_img = to_canny(photo)
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    prompt = build_prompt(description)
    # Prefer Compel; fall back to plain strings if Compel fails
    try:
        p, n = get_long_prompt_embeddings(refine_pipe, prompt, NEGATIVE_PROMPT)
        refined_img = refine_pipe(
            prompt_embeds=p,
            negative_prompt_embeds=n,
            image=canny_img,
            num_inference_steps=28,
            guidance_scale=7.5,
            controlnet_conditioning_scale=float(cn_scale),
            generator=generator,
        ).images[0]
    except Exception as e1:
        print("Compel path failed, using plain prompts:", e1)
        refined_img = refine_pipe(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            image=canny_img,
            num_inference_steps=28,
            guidance_scale=7.5,
            controlnet_conditioning_scale=float(cn_scale),
            generator=generator,
        ).images[0]
    return photo, canny_img, refined_img

@app.post("/compare")
def api_compare(req: SketchRequest):
    try:
        baseline_img, canny_img, refined_img = generate_refined(
            req.description, seed=req.seed, cn_scale=req.controlnet_scale
        )
        return {
            "baseline": image_to_b64(baseline_img),
            "canny_edges": image_to_b64(canny_img),
            "controlnet_lora_refined": image_to_b64(refined_img),
        }
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

@app.post("/sketch-from-photo")
def api_sketch_from_photo(req: PhotoSketchRequest):
    try:
        raw = req.image_base64
        if "," in raw[:40]:
            raw = raw.split(",", 1)[1]
        photo = Image.open(io.BytesIO(base64.b64decode(raw))).convert("RGB")
        print("photo size", photo.size, "cn", req.controlnet_scale)
        photo_r, canny_img, refined_img = generate_from_photo(
            photo, req.description, seed=req.seed, cn_scale=req.controlnet_scale
        )
        return {
            "photo_resized": image_to_b64(photo_r),
            "canny_edges": image_to_b64(canny_img),
            "controlnet_lora_refined": image_to_b64(refined_img),
        }
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return {"ok": False, "error": str(e), "trace": tb}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": str(DEVICE),
        "endpoints": ["/compare", "/sketch-from-photo"],
        "fix": "photo-v2",
    }

nest_asyncio.apply()
# kill old tunnels if any, then new one
try:
    ngrok.kill()
except Exception:
    pass
public_url = ngrok.connect(8000)
print("=" * 60)
print("Public API URL:", public_url)
print("Update .env COLAB_API_URL to this URL, then re-run the PC script")
print("=" * 60)
uvicorn.run(app, host="0.0.0.0", port=8000)
