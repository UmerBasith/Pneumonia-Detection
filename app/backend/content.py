"""Text used in the PDF report. Wording comes from docs/research/medical_content.md.

Keep this in sync with app/frontend/src/content/medical.ts (the UI uses the same wording).
"""
from __future__ import annotations

# Section 13, "PDF footer version" + the short version's safety line.
DISCLAIMER = (
    "This report was produced by PneumoScan AI, a student research project that analyses chest X-ray images "
    "with a deep-learning model. It is not a certified medical device and does not provide a diagnosis. "
    "All results must be reviewed and confirmed by a qualified medical professional before any clinical "
    "decision is made. If you feel very unwell or have trouble breathing, seek emergency care immediately."
)

MODEL_LIMITATION = (
    "The model was trained and tested on paediatric chest X-rays (ages 1–5) from a single hospital in "
    "Guangzhou, China. It may perform worse on adults, other hospitals or other X-ray machines."
)

EXPLANATION = {
    "PNEUMONIA": (
        "The model found patterns in this X-ray that it learned to associate with pneumonia. "
        "The heatmap shows the regions that most influenced this decision. This is a screening "
        "signal for a doctor to review, not a diagnosis."
    ),
    "NORMAL": (
        "The model did not find the patterns it associates with pneumonia in this X-ray. "
        "The result can be wrong: if symptoms are present or getting worse, a doctor should still "
        "assess the patient."
    ),
}

URGENT = (
    "Call an ambulance (India: 108, or 112) for struggling to breathe, pale, blue or blotchy skin, lips or "
    "tongue, coughing up blood, or sudden confusion."
)

NEXT_STEPS = {
    "PNEUMONIA": [
        "Show this result and the original X-ray to a qualified doctor. Only a doctor can confirm or rule out pneumonia.",
        "Doctors confirm pneumonia with the history, a physical exam and tests such as pulse oximetry and blood tests.",
        "For adults, the doctor may use a severity score such as CURB-65 to decide where care should happen.",
        URGENT,
    ],
    "NORMAL": [
        "If there are symptoms such as cough, fever or shortness of breath, see a doctor anyway.",
        "See a doctor the same day for a cough with yellow or green phlegm, chest pain that comes and goes, "
        "or shortness of breath.",
        URGENT,
    ],
}

THRESHOLD_NOTE = (
    "The decision threshold is set low on purpose: the model is tuned to rarely miss pneumonia, "
    "so borderline cases are flagged for a doctor to review."
)
