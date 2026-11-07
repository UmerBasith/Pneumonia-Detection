"""Build report/PneumoScan_AI_Report.docx from the content modules.

Run:  .venv\\Scripts\\python.exe report\\build_report.py
Then: powershell -File report\\word_finalize.ps1   (updates TOC / lists in Word and exports the PDF)
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from PIL import Image  # noqa: E402

from content_ch1_2 import ch1, ch2  # noqa: E402
from content_ch3_5 import ch3, ch4, ch5  # noqa: E402
from content_ch6_7 import ch6, ch7  # noqa: E402
from content_ch8 import ch8  # noqa: E402
from content_end import appendix_a, appendix_b, ch9, references  # noqa: E402
from content_front import front_blocks  # noqa: E402
from docx_engine import Report  # noqa: E402
from paths import FIG, RFIG  # noqa: E402

OUT = HERE / "PneumoScan_AI_Report.docx"


def prep_images():
    RFIG.mkdir(exist_ok=True)
    for src, dst, width in ((FIG / "sample_images.png", RFIG / "sample_images.jpg", 2400),
                            (FIG / "gradcam_examples.png", RFIG / "gradcam_examples.jpg", 2600)):
        im = Image.open(src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)
        im.save(dst, quality=92, optimize=True)
    Image.open(FIG / "architecture_diagram.png").convert("RGB").rotate(90, expand=True).save(
        RFIG / "architecture_diagram_rotated.png", optimize=True)


def main():
    prep_images()
    blocks = (front_blocks() + ch1() + ch2() + ch3() + ch4() + ch5() + ch6() + ch7() + ch8() + ch9()
              + [("raw", references)] + appendix_a() + appendix_b())
    r = Report()
    r.render(blocks)
    r.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    main()
