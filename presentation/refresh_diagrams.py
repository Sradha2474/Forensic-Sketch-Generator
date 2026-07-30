from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from pptx import Presentation
from pptx.oxml.ns import qn
from lxml import etree

assets = Path(r"e:\forensic-image-transformation\presentation\assets")
BLUE=(91,155,213); DARK=(68,114,196); NAVY=(68,84,106); WHITE=(255,255,255)
ORANGE=(237,125,49); GREEN=(112,173,71); GOLD=(255,192,0); LIGHT=(236,244,252)

def fonts():
    try:
        return (
            ImageFont.truetype(r"C:\Windows\Fonts\timesbd.ttf", 30),
            ImageFont.truetype(r"C:\Windows\Fonts\times.ttf", 20),
            ImageFont.truetype(r"C:\Windows\Fonts\timesbd.ttf", 18),
            ImageFont.truetype(r"C:\Windows\Fonts\times.ttf", 16),
        )
    except Exception:
        f = ImageFont.load_default()
        return f,f,f,f

lg, md, md_b, sm = fonts()

# Workflow
wf = Image.new("RGB", (1600, 420), WHITE)
d = ImageDraw.Draw(wf)
d.rectangle([0,0,1600,60], fill=DARK)
d.text((40,14), "End-to-End Operational Workflow", fill=WHITE, font=lg)
steps = [("1. Interview","Module A",BLUE),("2. Profile","Module B",DARK),("3. Compose","Module C",ORANGE),
         ("4. Sketch","Module D",GREEN),("5. Refine","Module E",GOLD),("6. Export","Session Out",NAVY)]
for i,(t,s,c) in enumerate(steps):
    x=40+i*260
    d.rounded_rectangle([x,130,x+220,300], radius=16, fill=c)
    d.text((x+28,175), t, fill=WHITE, font=md_b)
    d.text((x+45,230), s, fill=WHITE, font=sm)
    if i<5:
        d.polygon([(x+228,205),(x+252,215),(x+228,225)], fill=NAVY)
d.text((40,340), "Mirrors forensic practice: Cognitive Interview -> catalog features -> construct -> refine -> approve", fill=NAVY, font=sm)
wf.save(assets/"workflow_diagram.png")

# Architecture
arch = Image.new("RGB", (1600, 900), WHITE)
d = ImageDraw.Draw(arch)
d.rectangle([0,0,1600,70], fill=DARK)
d.text((40,18), "System Architecture — AI-Assisted Forensic Sketch Framework", fill=WHITE, font=lg)
mods=[
 (50,110,520,300,"A — Interactive Interview Agent","CI / H-CI protocol state machine","LLM + deterministic phase control",BLUE),
 (540,110,1010,300,"B — Face Feature Profile","Living structured attributes","Sole conditioning interface",DARK),
 (1030,110,1540,300,"C — Controllable Face Composer","Attribute -> latent projection","StyleGAN2-ADA / SD prior",ORANGE),
 (50,360,520,550,"D — Forensic Sketch Renderer","Edge / dodge OR Pix2Pix","Pencil-style composite",GREEN),
 (540,360,1010,550,"E — Guided Refinement","Selective attribute edits","Witness remains authority",GOLD),
 (1030,360,1540,550,"Optional Validation Layer","FID · CLIP · ArcFace","Research metrics only",NAVY),
]
for x1,y1,x2,y2,t,s1,s2,c in mods:
    d.rounded_rectangle([x1,y1,x2,y2], radius=18, fill=(245,248,252), outline=c, width=4)
    d.rectangle([x1,y1,x2,y1+52], fill=c)
    d.text((x1+16,y1+12), t, fill=WHITE, font=md_b)
    d.text((x1+20,y1+90), s1, fill=NAVY, font=md)
    d.text((x1+20,y1+130), s2, fill=NAVY, font=sm)
for x in [285,775,1285]:
    d.line([(x,300),(x,360)], fill=NAVY, width=5)
    d.polygon([(x-8,350),(x+8,350),(x,368)], fill=NAVY)
d.rounded_rectangle([50,600,1540,850], radius=16, fill=LIGHT, outline=BLUE, width=3)
d.text((80,630), "Product Interface", fill=DARK, font=md_b)
d.text((80,690), "Planned: Investigator-facing Next.js (App Router) + FastAPI / Route Handlers", fill=NAVY, font=md)
d.text((80,740), "Current MVP: Streamlit form -> JSON profile -> Prompt builder -> Stable Diffusion v1.5 -> OpenCV sketch", fill=NAVY, font=md)
d.text((80,790), "Repo: github.com/Sradha2474/Forensic-Sketch-Generator   |   Assistive tool — not legal evidence", fill=DARK, font=sm)
arch.save(assets/"architecture_diagram.png")

# AI pipeline
pipe = Image.new("RGB", (1600, 700), WHITE)
d = ImageDraw.Draw(pipe)
d.rectangle([0,0,1600,70], fill=BLUE)
d.text((40,18), "AI Pipeline — From Witness Attributes to Forensic Sketch", fill=WHITE, font=lg)
boxes = [
 (80,140,"JSON Profile","13+ facial attributes"),
 (420,140,"Prompt Builder","Attribute -> SD prompt"),
 (760,140,"Stable Diffusion","Photoreal face prior"),
 (1100,140,"OpenCV Sketch","Edge + dodge blend"),
]
for i,(x,y,t,s) in enumerate(boxes):
    d.rounded_rectangle([x,y,x+280,y+180], radius=14, fill=LIGHT, outline=DARK, width=3)
    d.rectangle([x,y,x+280,y+50], fill=DARK)
    d.text((x+16,y+12), t, fill=WHITE, font=md_b)
    d.text((x+20,y+95), s, fill=NAVY, font=md)
    if i<3:
        d.polygon([(x+286,y+80),(x+320,y+95),(x+286,y+110)], fill=BLUE)
d.text((80,380), "Full Research Pipeline (in progress)", fill=DARK, font=md_b)
fut = ["LLM Interview Agent","Attribute Latent Map","StyleGAN2-ADA","Pix2Pix Sketch","Guided Refinement"]
for i,t in enumerate(fut):
    x=80+i*300
    d.rounded_rectangle([x,430,x+270,560], radius=12, fill=(255,248,230), outline=ORANGE, width=2)
    d.text((x+18,480), t, fill=NAVY, font=sm)
pipe.save(assets/"ai_pipeline.png")
print("diagrams refreshed")
