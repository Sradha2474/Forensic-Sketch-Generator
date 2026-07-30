import os
from pathlib import Path
try:
    import win32com.client  # type: ignore
except ImportError:
    import subprocess
    subprocess.check_call([r"e:\forensic-image-transformation\.venv\Scripts\python.exe", "-m", "pip", "install", "pywin32", "-q"])
    import win32com.client

ppt_path = str(Path(r"e:\forensic-image-transformation\presentation\Forensic_Sketch_Generator_STAAR_Presentation.pptx").resolve())
out_dir = Path(r"e:\forensic-image-transformation\presentation\previews")
out_dir.mkdir(exist_ok=True)

app = win32com.client.Dispatch("PowerPoint.Application")
app.Visible = 1
pres = app.Presentations.Open(ppt_path, WithWindow=False)
# Export selected slides: 1 title, 7 solution, 9 architecture, 16 demo, 20 thanks
for idx in [1, 7, 9, 16, 20]:
    dest = str(out_dir / f"slide_{idx:02d}.png")
    pres.Slides(idx).Export(dest, "PNG", 1280, 720)
    print("exported", dest, "exists", os.path.exists(dest))
pres.Close()
app.Quit()
print("done")
