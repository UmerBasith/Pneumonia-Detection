# Screenshots changed by the QA agent (2026-11-08)

Refresh these in the report:

| File | Why |
|---|---|
| `15_pdf_report_page1.png` | PDF report fix: the two image captions ("Chest X-ray as analysed by the model" / "Grad-CAM heatmap ...") now start on the same line. Regenerated from the same scan (PS-20261107-0DFC08), same 150 dpi render. |
| `sample_patient_report.pdf` | Same PDF as above (same scan, same content, only the caption alignment changed). |

No app screen changed visually, so screenshots `01`–`14` (all sizes, light and dark) are still current.
To regenerate any of them later: `tests/make_screenshots.py` (same flows and file names as before).
