from pptx import Presentation
from pptx.oxml.ns import qn
from lxml import etree
from pathlib import Path

ppt = Path(r"e:\forensic-image-transformation\presentation\Forensic_Sketch_Generator_STAAR_Presentation.pptx")
prs = Presentation(str(ppt))
for slide in prs.slides:
    # remove existing transition
    el = slide._element
    # p:transition under p:sld
    nsmap = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    for old in el.findall("p:transition", nsmap):
        el.remove(old)
    # subtle fade, fast
    tr = etree.SubElement(el, qn("p:transition"))
    tr.set("spd", "fast")
    etree.SubElement(tr, qn("p:fade"))
prs.save(str(ppt))
print("transitions added")

# copy again
import shutil
shutil.copy(ppt, Path.home() / "Desktop" / "Forensic_Sketch_Generator_STAAR_Presentation.pptx")
print("copied to Desktop")
