# PneumoScan AI — Classroom Demo Guide

A 5-minute script for presenting the project. Practise it once before class.

## Before class (2 minutes)
1. Plug in the laptop charger (the GPU makes each scan take under 1 second; on battery it may be slower).
2. Double-click **`start.bat`** in `C:\PersonalProjects\pneumoscan-ai`. Wait for "Model ready". The browser opens by itself.
3. Make the browser full screen (F11). For a projector, light mode is easier to read (moon/sun icon, top right).
4. Works fully **offline**: no internet needed.

## The demo (about 5 minutes)

| Step | Do this | Say this |
|---|---|---|
| 1. The problem | Show the home page | "Pneumonia kills about 7 lakh children under five every year. India has only about one radiologist per 1 lakh people. PneumoScan gives a fast second read of a chest X-ray." |
| 2. A pneumonia X-ray | Click **X-ray 07–12** in "Try a sample X-ray" | "A ResNet ensemble gives the pneumonia probability, a risk level and an answer in under a second." |
| 3. Explainability | Switch **Heatmap** / **Side by side**, move the opacity slider, zoom | "Grad-CAM shows *where* the model looked, so a doctor can check its reasoning instead of trusting a black box." |
| 4. A normal X-ray | **New scan** → click **X-ray 01** | "Low risk, no pneumonia detected. The ground truth confirms it." |
| 5. Safety check | Click the **cat** or **coffee** image under "Not X-rays" | "It refuses images that are not chest X-rays, so it never gives nonsense results." |
| 6. Patient report | Fill a patient name and age, click **Download PDF report** | "A one-page report the doctor can sign, with a clear disclaimer." |
| 7. Doctor triage | **Triage** page → select all 12 files in `sample_xrays` | "For a busy hospital: many X-rays at once, sorted so the most urgent cases are seen first. Export to CSV." |
| 8. Severity score | **CURB-65** page → tick a few criteria | "The standard clinical pneumonia severity score from the British Thoracic Society research (Lim et al., 2003)." |
| 9. The model | **Model** page | "Tested once on 624 X-rays it never saw: 94.6% accuracy, and it caught 389 of 390 pneumonia cases (99.7% sensitivity), AUC 0.987." |

The sample X-rays: `normal_01–06` and `pneumonia_01–06` are in `sample_xrays/` (in the app's gallery: X-ray 01–06 are the normal ones, X-ray 07–12 the pneumonia ones; the labels are hidden so the class can guess first). `answer_key.csv` lists the true labels.

## Likely questions — short answers

- **Why ResNet?** Skip connections (output = F(x) + x) let very deep networks train well; the gradient flows straight back through the shortcut.
- **Why 3 models?** Two ResNet50s and one ResNet34; averaging them is more stable than any single model.
- **Why is the threshold only 7.4%?** It was chosen on the validation set to rarely miss pneumonia. Missing a sick child is worse than a false alarm that a doctor double-checks.
- **Did you reach 95%?** 94.55% on the official test set, 3 images short. A higher number was possible only by tuning on the test set, which would be cheating, so the honest number is reported.
- **Where is the data from?** Kermany et al., *Cell* 2018: 5,856 paediatric chest X-rays, public licence (CC BY 4.0).
- **Limitations?** Trained on children aged 1–5 from one hospital; may be less accurate on adults or other machines. Grad-CAM sometimes looks at the "R" marker on the film. It is a decision-support tool, not a diagnosis.

## After the demo
Clear patient data: **History → Clear all**.
