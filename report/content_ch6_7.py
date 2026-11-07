"""Chapter 6 (Implementation) and Chapter 7 (Results and Discussion)."""
from paths import FIG, RFIG
from src_extract import between, func, read

TREE = """pneumoscan-ai/
├── start.bat                 double-click launcher (Windows)
├── data/                     raw images, 512 px cache, splits.csv, dataset summary
├── ml/                       machine-learning pipeline
│   ├── common.py             paths, image conversion, build_model, metrics
│   ├── prepare_data.py       counts, patient-level split, cache, leakage checks
│   ├── datasets.py           PyTorch Dataset + augmentation
│   ├── train.py              fine-tuning loop (AdamW, cosine, AMP, EMA)
│   ├── evaluate.py           TTA, ensemble, temperature, threshold, export
│   ├── gradcam.py            Grad-CAM on layer4
│   ├── xray_gate.py          "is this a chest X-ray?" detector
│   ├── inference.py          PneumoniaModel API used by the app
│   ├── make_figures.py       report figures
│   └── test_inference.py     pytest contract tests
├── models/                   fp16 weights (3 members), ensemble.json,
│                             metrics.json, model_card.json, xray_gate.npz
├── app/
│   ├── backend/              FastAPI server
│   │   ├── main.py           API routes + serves the built front-end
│   │   ├── model_service.py  loads the model once, warm-up
│   │   ├── imaging.py        safe decoding (JPG/PNG/BMP/WEBP/TIFF/DICOM)
│   │   ├── storage.py        SQLite history + saved images
│   │   ├── report.py         patient PDF (ReportLab)
│   │   └── tests/            pytest suite for the API
│   └── frontend/             React + TypeScript + Vite + Tailwind CSS
│       └── src/              pages/, components/, lib/, content/
├── sample_xrays/             demo X-rays from the TEST split + non-X-rays
├── docs/                     plan, research notes, figures, screenshots
└── report/                   this report (generator scripts, .docx, .pdf)"""


def ch6():
    return [
        ("chapter", 6, "Implementation"),
        ("h2", "6.1 Development Environment"),
        ("p", "The project was developed on Windows 11 with Python 3.11.9 in a virtual environment (.venv) and Node.js "
              "24 for the front-end. Training and evaluation ran on the NVIDIA RTX 3050 Laptop GPU with PyTorch 2.11.0 "
              "and CUDA 12.8 (Chapter 3, {tab:hw} and {tab:sw}). Every step of the machine-learning pipeline is a "
              "separate script that is run from the project root, for example "
              "**.venv\\Scripts\\python.exe -m ml.train --name r50_384_s1 --arch resnet50 --res 384 --bs 24 --seed 1**. "
              "This chapter explains the most important parts of the code; the complete source of the pipeline and the "
              "back-end is given in Appendix A."),
        ("h2", "6.2 Project Structure"),
        ("code", "tree", "Project folder structure", TREE),
        ("h2", "6.3 Data Preparation"),
        ("p", "ml/prepare_data.py first checks that the extracted dataset has exactly the official number of images "
              "per split and class. {lst:patient} shows how the patient identifier is parsed from the file name and how "
              "a patient-level, stratified validation fold is carved out of the training images with scikit-learn’s "
              "StratifiedGroupKFold."),
        ("code", "patient", "Patient identifier and patient-level validation split (ml/prepare_data.py)",
         func("ml/prepare_data.py", "patient_id") + "\n\n# ... inside main():\n"
         + between("ml/prepare_data.py", "# Patient-level, stratified validation split", 'df.loc[train_idx[val_pos], "split"] = "val"')),
        ("h2", "6.4 Dataset and Augmentation"),
        ("p", "{lst:aug} shows the training and evaluation transforms built with torchvision’s transforms v2. Images "
              "are read from the 512 × 512 grayscale cache, augmented, replicated to three channels and normalised."),
        ("code", "aug", "Training and evaluation transforms (ml/datasets.py)",
         func("ml/datasets.py", "train_transform") + "\n\n\n" + func("ml/datasets.py", "eval_transform")),
        ("h2", "6.5 Building the Model"),
        ("p", "{lst:build} loads a torchvision ResNet with its ImageNet weights and replaces the 1000-class layer with "
              "a dropout layer and a two-class linear layer."),
        ("code", "build", "Building a ResNet with a two-class head (ml/common.py)", func("ml/common.py", "build_model")),
        ("h2", "6.6 Training Loop"),
        ("p", "{lst:train} is the core of ml/train.py. For every step the learning rate is set from the warm-up and "
              "cosine schedule, the forward pass runs under fp16 autocast, the scaled loss is back-propagated, "
              "gradients are clipped, the optimiser steps and the EMA copy of the weights is updated. After each epoch "
              "the EMA model is evaluated on validation, and the best checkpoint by validation ROC-AUC is saved."),
        ("code", "train", "One training epoch (ml/train.py, excerpt)",
         between("ml/train.py", "for x, y in train_dl:", "seen += len(y)")),
        ("h2", "6.7 Evaluation, Calibration and Threshold"),
        ("p", "ml/evaluate.py computes the flip-TTA logit margins of every member, averages them, and then fits the "
              "temperature and the decision threshold **on the validation split only** ({lst:calib}). The test split is "
              "scored only with the --export option, and every test scoring is appended to "
              "logs/test_evaluations.jsonl so that the number of test evaluations can be audited (it is exactly one)."),
        ("code", "calib", "Temperature scaling and Youden-J threshold (ml/evaluate.py)",
         func("ml/evaluate.py", "fit_temperature") + "\n\n\n" + func("ml/evaluate.py", "pick_threshold")),
        ("h2", "6.8 Grad-CAM"),
        ("p", "{lst:gradcam} registers a forward hook on layer4 to keep its activations, runs one forward and one "
              "backward pass of the logit margin, and builds the class map from the gradient-weighted activations."),
        ("code", "gradcam", "Grad-CAM for torchvision ResNets (ml/gradcam.py)", func("ml/gradcam.py", "GradCAM")),
        ("h2", "6.9 Inference API"),
        ("p", "The application uses a single class, PneumoniaModel (ml/inference.py), which loads the three members "
              "once, checks the image with the X-ray gate and returns the label, calibrated probability, risk level and "
              "three aligned PNG images (input, heat map and overlay). {lst:predict} shows how the ensemble decision "
              "is made inside predict()."),
        ("code", "predict", "Ensemble decision inside PneumoniaModel.predict (ml/inference.py, excerpt)",
         between("ml/inference.py", "margins, explained = [], []", "label = CLASSES[int(prob >= thr)]")),
        ("h2", "6.10 X-ray Gate"),
        ("p", "The feature-distance part of the gate is shown in {lst:gate}; the parameters (class means, precision "
              "matrix and cut-off) are stored in models/xray_gate.npz."),
        ("code", "gate", "Mahalanobis distance and decision of the X-ray gate (ml/xray_gate.py)",
         func("ml/xray_gate.py", "distance", cls="XrayGate") + "\n\n" + func("ml/xray_gate.py", "score", cls="XrayGate")
         + "\n\n" + func("ml/xray_gate.py", "decide", cls="XrayGate")),
        ("h2", "6.11 Back-end API (FastAPI)"),
        ("p", "The back-end (app/backend/main.py) exposes the JSON API listed in {tab:api} and also serves the built "
              "React front-end, so the whole application runs from one local server on port 8000. Errors are always "
              "returned in the same shape, {\"error\": {\"code\", \"message\"}}, with a friendly message."),
        ("tab", "api", "REST API endpoints",
         ["Method", "Path", "Purpose"],
         [
             ["GET", "/api/health", "Status, model mode, device and model version"],
             ["GET", "/api/model-info", "metrics.json, model_card.json and figure URLs"],
             ["POST", "/api/predict", "One X-ray (+ optional patient details) → result and saved scan"],
             ["POST", "/api/batch", "Up to 50 X-rays → results sorted by pneumonia probability"],
             ["GET", "/api/history", "Search and page through saved scans"],
             ["GET / PATCH / DELETE", "/api/history/{id}", "Read, edit patient details or notes, delete a scan"],
             ["DELETE", "/api/history", "Clear all history"],
             ["GET", "/api/history/{id}/image/{kind}", "Saved input, overlay, heat-map or thumbnail image"],
             ["GET", "/api/report/{id}.pdf", "Patient PDF report"],
             ["GET", "/api/samples", "Demo X-rays from the test split"],
         ], [1.45, 2.15, 2.4], {"size": 10}),
        ("p", "{lst:api} shows the prediction endpoint. The upload is size-checked, the patient fields are validated, "
              "and the CPU/GPU-heavy analysis runs in a worker thread so that the server stays responsive."),
        ("code", "api", "Prediction endpoint (app/backend/main.py, excerpt)",
         between("app/backend/main.py", '@app.post("/api/predict")', "notes=notes_clean, ground_truth=gt)")),
        ("h2", "6.12 Front-end (React + TypeScript)"),
        ("p", "The front-end is a React 19 single-page application written in TypeScript, styled with Tailwind CSS "
              "and built with Vite into static files. All fonts are bundled, so nothing is loaded from the internet. "
              "A typed client (src/lib/api.ts) wraps every endpoint. {lst:ruler} shows the component that draws the "
              "pneumonia probability on a 0–100 ruler with the decision threshold marked, which helps users see how "
              "close a result is to the boundary."),
        ("code", "ruler", "ProbabilityRuler component (app/frontend/src/components/ProbabilityRuler.tsx)",
         read("app/frontend/src/components/ProbabilityRuler.tsx"), 8.0),
        ("h2", "6.13 Testing"),
        ("p", "Automated tests were written for both parts of the system. **ml/test_inference.py** checks the inference "
              "contract: the keys and types of the result, the PNG sizes and aspect ratio, all PIL image modes (L, RGB, "
              "RGBA, LA, P, I;16, I, F, CMYK, 1), tiny and very large images, 16-bit DICOM input, rejection of "
              "photographs, blank and noise images, the sample answer key and info(); all **24 tests passed**. In "
              "addition, running predict() one image at a time on all 624 test files reproduced the batch evaluation "
              "(maximum probability difference 0.00047, no label changes). The back-end test suite "
              "(app/backend/tests) covers every endpoint, bad and huge files, synthetic DICOM files, mixed batches, "
              "history create/read/update/delete, PDF generation with long and Unicode text, and the switch between "
              "the real model and the mock model used during development."),
    ]


def ch7():
    return [
        ("chapter", 7, "Results and Discussion"),
        ("h2", "7.1 Experimental Protocol"),
        ("p", "All decisions (number of epochs, ensemble members, test-time augmentation, temperature and threshold) "
              "were made on the 747-image validation split. The final pipeline, a pre-committed ensemble of every "
              "trained member, was then applied **once** to the official 624-image test set on 7 November 2026; in the "
              "same run each member was also scored with its own validation-chosen settings. Nothing was re-trained, "
              "re-thresholded or re-selected afterwards. All numbers below are copied from models/metrics.json."),
        ("h2", "7.2 Training Behaviour"),
        ("p", "{tab:runs} summarises the three training runs and {fig:curves1} to {fig:curves3} show the training and "
              "validation curves. All runs converged within a few epochs: validation ROC-AUC exceeded 0.99 after the "
              "first or second epoch and peaked at epoch 7–10. Afterwards training accuracy kept rising towards 99% "
              "while validation AUC flattened or fell slightly, so early stopping ended each run between epochs 14 and "
              "17. (Loss values stay around 0.3 because label smoothing prevents the loss from approaching zero.)"),
        ("tab", "runs", "Training runs on the RTX 3050 GPU",
         ["Run", "Model", "Input", "Batch", "Seed", "Epochs run", "Best epoch", "Time (min)", "Best val AUC*"],
         [
             ["r50_384_s1", "ResNet-50", "384", "24", "1", "14", "7", "17.7", "0.9965"],
             ["r34_384_s2", "ResNet-34", "384", "32", "2", "17", "10", "13.9", "0.9971"],
             ["r50_448_s3", "ResNet-50", "448", "16", "3", "14", "7", "23.9", "0.9974"],
         ], [0.95, 0.8, 0.5, 0.5, 0.45, 0.65, 0.65, 0.65, 0.85],
         {"size": 9.5, "align": ["L", "L", "C", "C", "C", "C", "C", "C", "C"],
          "note": "* Validation ROC-AUC of the EMA weights at the best epoch, single view, during training. Total training "
                  "time 55.5 minutes."}),
        ("fig", "curves1", FIG / "training_curves_r50_384_s1.png", 6.0, "Training curves of ResNet-50 at 384 px (r50_384_s1)"),
        ("fig", "curves2", FIG / "training_curves_r34_384_s2.png", 6.0, "Training curves of ResNet-34 at 384 px (r34_384_s2)"),
        ("fig", "curves3", FIG / "training_curves_r50_448_s3.png", 6.0, "Training curves of ResNet-50 at 448 px (r50_448_s3)"),
        ("h2", "7.3 Validation Results"),
        ("p", "{tab:val} gives the validation results with flip TTA and each model’s own temperature and threshold. "
              "The ensemble has the highest validation ROC-AUC (0.9980) and ties for the best balanced accuracy, which "
              "confirms the pre-committed choice of the ensemble as the final model."),
        ("tab", "val", "Validation results (747 images, flip TTA, settings fitted on validation)",
         ["Model", "T", "Threshold", "Accuracy", "Bal. acc.", "Sensitivity", "Specificity", "ROC-AUC"],
         [
             ["ResNet-50 @ 384", "0.609", "0.038", "98.39%", "98.58%", "98.20%", "98.96%", "0.9974"],
             ["ResNet-34 @ 384", "0.612", "0.067", "98.13%", "98.57%", "97.66%", "99.48%", "0.9977"],
             ["ResNet-50 @ 448", "0.618", "0.044", "98.13%", "97.89%", "98.38%", "97.40%", "0.9972"],
             ["Ensemble (final)", "0.602", "0.074", "98.39%", "98.58%", "98.20%", "98.96%", "0.9980"],
         ], [1.35, 0.5, 0.75, 0.75, 0.7, 0.8, 0.8, 0.65],
         {"size": 9.5, "align": ["L", "C", "C", "C", "C", "C", "C", "C"], "bold_last": True}),
        ("h2", "7.4 Official Test Results"),
        ("p", "{tab:test} reports the single evaluation on the official test set. The final ensemble reached an "
              "**accuracy of 94.55% (590 of 624 images)**, a **sensitivity of 99.74%** (389 of 390 pneumonia X-rays "
              "detected), a specificity of 85.90%, a precision of 92.18%, an F1-score of 95.81%, a ROC-AUC of 0.9867 "
              "and a PR-AUC of 0.9898. By pneumonia type, the sensitivity was 99.6% for bacterial pneumonia (241 of "
              "242) and 100% for viral pneumonia (148 of 148)."),
        ("tab", "test", "Official test-set results (624 images; thresholds from validation)",
         ["Model", "Accuracy", "Precision", "Sensitivity", "Specificity", "F1", "ROC-AUC", "TN / FP / FN / TP"],
         [
             ["ResNet-50 @ 384", "91.99%", "88.81%", "99.74%", "79.06%", "93.96%", "0.9811", "185 / 49 / 1 / 389"],
             ["ResNet-34 @ 384", "94.87%", "92.82%", "99.49%", "87.18%", "96.04%", "0.9884", "204 / 30 / 2 / 388"],
             ["ResNet-50 @ 448", "91.67%", "88.41%", "99.74%", "78.21%", "93.73%", "0.9828", "183 / 51 / 1 / 389"],
             ["Ensemble (final)", "94.55%", "92.18%", "99.74%", "85.90%", "95.81%", "0.9867", "201 / 33 / 1 / 389"],
         ], [1.3, 0.72, 0.72, 0.78, 0.8, 0.62, 0.62, 1.24],
         {"size": 9.5, "align": ["L", "C", "C", "C", "C", "C", "C", "C"], "bold_last": True}),
        ("p", "The ensemble improved clearly on the two ResNet-50 members (91.99% and 91.67%). The ResNet-34 member "
              "alone scored slightly higher on the test set (94.87%), but validation did not prefer it (balanced "
              "accuracy 98.57% versus 98.58%, AUC 0.9977 versus 0.9980). Switching to it after seeing the test results "
              "would be test-set tuning, so the pre-committed ensemble remains the reported model."),
        ("h2", "7.5 Confusion Matrix"),
        ("p", "{fig:cm} shows the confusion matrix of the final ensemble. Of the 34 errors, **33 are false positives** "
              "(normal X-rays labelled PNEUMONIA) and only **one is a false negative** (a missed pneumonia)."),
        ("fig", "cm", FIG / "confusion_matrix_test.png", 3.6, "Confusion matrix of the final ensemble on the test set"),
        ("h2", "7.6 ROC and Precision–Recall Curves"),
        ("p", "The ROC curves ({fig:roc}) of all models rise steeply towards the top-left corner, with AUC values "
              "between 0.981 and 0.988, and the precision–recall curves ({fig:pr}) stay high across almost the whole "
              "recall range. The marked operating point of the ensemble sits at very high sensitivity, which reflects "
              "the low validation-chosen threshold."),
        ("fig", "roc", FIG / "roc_curve_test.png", 3.9, "ROC curves on the test set (ensemble and members)"),
        ("fig", "pr", FIG / "pr_curve_test.png", 3.9, "Precision–recall curves on the test set"),
        ("h2", "7.7 Distribution of Predicted Probabilities"),
        ("p", "{fig:hist} shows the calibrated probabilities of the ensemble for each true class. Almost all pneumonia "
              "X-rays receive very high probabilities, while normal X-rays are concentrated near zero with a tail that "
              "crosses the low threshold of 0.074. This tail produces the false positives."),
        ("fig", "hist", FIG / "probability_histogram_test.png", 5.0, "Ensemble probabilities on the test set by true "
                                                                     "class, with the decision threshold"),
        ("h2", "7.8 Grad-CAM Explanations"),
        ("p", "{fig:gradcam} shows Grad-CAM maps for two correctly detected pneumonia cases, two correctly classified "
              "normal cases, one false positive and the single false negative. For the correct predictions the heat "
              "maps mostly cover the lung fields: dense regions in the pneumonia cases, and broad areas of both lungs "
              "for the normal cases. However, some maps also highlight **burned-in text**, especially the “R” side "
              "marker in the upper corner and exposure values or time stamps. This indicates partial shortcut learning "
              "of hospital-specific image features, the same risk described by Zech et al. [13]. It is a likely "
              "contributor to errors on images acquired in a slightly different way and is listed as a limitation."),
        ("fig", "gradcam", RFIG / "gradcam_examples.jpg", 6.0, "Grad-CAM explanations on test X-rays (red = regions driving the prediction)"),
        ("h2", "7.9 X-ray Gate Results"),
        ("p", "The gate was validated end-to-end with check_image() on real files ({tab:gate}). It accepted 620 of the "
              "624 test chest X-rays; the four refused images are all normal X-rays that the classifier would have "
              "labelled correctly. It rejected every one of the 33 non-X-ray images (photographs, textures, "
              "documents, noise, plain colours and a gradient) and also all 16 grayscale copies of the colour images, "
              "which only the feature-distance test can catch."),
        ("tab", "gate", "Validation of the X-ray gate",
         ["Check", "Result"],
         [
             ["Official test chest X-rays accepted", "620 / 624 (99.36%)"],
             ["Non-X-ray images rejected (22 scikit-image photographs and textures, gray and RGB noise, 5 plain "
              "colours, a gradient, 3 synthetic documents)", "33 / 33"],
             ["Grayscale copies of the 16 colour images rejected (highest score 0.165; cut-off 0.5)", "16 / 16"],
             ["Mahalanobis cut-off τ (1.15 × 99.5th percentile of validation distances)",
              "66.04 (validation median 41.0, maximum 64.7)"],
         ], [4.3, 1.7], {"size": 10, "align": ["L", "C"]}),
        ("p", "The test-set metrics in {tab:test} include all 624 images, including the four that the gate would "
              "refuse. The gate learns what the training X-rays look like, so other radiographs (for example a hand "
              "X-ray) or adult chest films may or may not be accepted; it is a convenience, not a safety guarantee."),
        ("h2", "7.10 Inference Speed"),
        ("tab", "speed", "Time per image (median, after warm-up, measured on official test images)",
         ["Setting", "Time per image"],
         [
             ["GPU (RTX 3050): 3 ResNets × 2 views + Grad-CAM, including pre-processing and PNG encoding",
              "376 ms (95th percentile 457 ms)"],
             ["GPU without Grad-CAM", "233 ms"],
             ["CPU only (Intel i5-12450HX), with Grad-CAM", "1,248 ms"],
         ], [4.2, 1.8], {"size": 10, "align": ["L", "C"]}),
        ("p", "The first prediction after start-up takes about one second longer because of CUDA warm-up; the "
              "application performs a warm-up prediction while loading so that the first real scan is fast. Even "
              "without a GPU, an X-ray is analysed in little more than a second, which is acceptable for a "
              "decision-support tool."),
        ("h2", "7.11 Comparison with Published Work"),
        ("p", "{tab:comp} compares PneumoScan AI with published results that use the **same official test set** "
              "(Chapter 2). Results on re-split data or cross-validation (97–99%) are excluded because they are not "
              "comparable."),
        ("tab", "comp", "Comparison with published results on the official Kermany test set",
         ["Work", "Model", "Accuracy", "Sensitivity", "Specificity", "Other"],
         [
             ["Kermany et al. [2]", "Inception-V3, transfer learning", "92.8%", "93.2%", "90.1%", "AUC 0.968"],
             ["Yang et al. [6]", "ResNet-18, 28 px", "85.4%", "–", "–", "AUC 0.944"],
             ["Yang et al. [6]", "ResNet-18, 224 px", "86.4%", "–", "–", "AUC 0.956"],
             ["Yang et al. [6]", "ResNet-50, 224 px", "88.4%", "–", "–", "AUC 0.962"],
             ["Liang & Zheng [11]", "Residual + dilated convolution", "–", "96.7%", "–", "F1 92.7%"],
             ["Chouhan et al. [8]", "Ensemble of 5 CNNs (voting)", "96.4%", "99.62%", "–", "–"],
             ["**This work**", "**Ensemble of 3 ResNets**", "**94.55%**", "**99.74%**", "**85.90%**",
              "**AUC 0.9867, F1 95.81%**"],
         ], [1.35, 1.65, 0.75, 0.8, 0.8, 0.95],
         {"size": 9.5, "align": ["L", "L", "C", "C", "C", "C"],
          "note": "Sensitivity = recall for the PNEUMONIA class. “–” means not reported in the cited source. "
                  "Chouhan et al. report results on “unseen data from the Guangzhou dataset” after training on the "
                  "5,232 training images."}),
        ("p", "PneumoScan AI is well above the published ResNet baselines on the same images (85.4–88.4%) and the "
              "dataset authors’ Inception-V3 (92.8%), and its sensitivity of 99.74% is the highest in the table. Only "
              "the five-CNN ensemble of Chouhan et al. reports a higher accuracy."),
        ("h2", "7.12 Error Analysis"),
        ("bullets", [
            "**False negative (1 image):** person154_bacteria_728.jpeg, a bacterial pneumonia case, received a very "
            "low probability (p = 0.0008). Its Grad-CAM map for the NORMAL decision ({fig:gradcam}, bottom right) highlights broad areas of "
            "the central chest and lungs, the pattern the model associates with normal X-rays, rather than a focal "
            "opacity.",
            "**False positives (33 images):** normal X-rays whose probability exceeded the low threshold of 0.074. "
            "Several of their heat maps highlight corner markers and text as well as the lungs. In the application, "
            "12 of these 33 images fall in the Moderate risk band (possible pneumonia, see a doctor) and 21 in the "
            "High band, so the risk level alone does not remove them; the doctor’s review remains essential.",
            "**Why validation looked better than test:** on validation the normal images were very clean (only 2 "
            "false positives out of 192), while a tail of pneumonia images had low scores. Maximising Youden’s J "
            "therefore produced a low threshold. The official test set is known to be harder and differently "
            "distributed from the training pool (published ResNet baselines reach only 85–88% on it [6]), and on the "
            "test set the low threshold favours sensitivity (99.7%) over specificity (85.9%).",
            "**Ranking is strong:** a test ROC-AUC of 0.987 shows that the model ranks pneumonia above normal images "
            "very well; the remaining gap is about where the threshold sits, not about poor features.",
        ]),
        ("h2", "7.13 Discussion of the 95% Target"),
        ("p", "The objective was at least 95% accuracy on the official test set. The honest result is **94.55%, which "
              "is three images short** of the target (95% of 624 is 593 correct images; the ensemble got 590). The "
              "result is nevertheless strong and clinically sensible:"),
        ("bullets", [
            "Only **1 of 390** pneumonia X-rays was missed (sensitivity 99.74%). For a screening and triage aid, missing "
            "pneumonia is the more dangerous error, and the validation-chosen threshold prioritises not missing it.",
            "Almost all errors are normal X-rays flagged for review, which a doctor can quickly dismiss. This matches the "
            "known behaviour of this test set in published work: Kermany et al. report lower specificity than "
            "sensitivity [2], the ResNet baselines of MedMNIST v2 have high AUC (0.944–0.962) but much lower accuracy "
            "(85.4–88.4%) [6], and the best published ensemble combines 96.4% accuracy with 99.62% recall, so its errors "
            "are also mostly false alarms [8].",
            "The evaluation is honest: the test set was scored once, with a threshold that was fixed on validation before "
            "the test set was touched.",
        ]),
        ("p", "For discussion only, a post-hoc analysis in the ML report shows how the same ensemble would have scored "
              "with other thresholds ({tab:posthoc}). With a threshold of 0.5 the test accuracy would have been 95.8%. "
              "**This threshold was not adopted:** choosing it after seeing the test results would be tuning on the test "
              "set, which would make the reported number optimistic and untrustworthy. The analysis is shown only to "
              "explain that the gap comes from where the threshold sits under the shift between the validation and "
              "test distributions. A future validation set that resembles the deployment data (for example from a "
              "different hospital) would allow a better threshold to be chosen honestly."),
        ("tab", "posthoc", "Post-hoc threshold sensitivity on the test set (discussion only; NOT the reported result)",
         ["Threshold", "Test accuracy", "Status"],
         [
             ["0.074 (chosen on validation)", "94.55%", "Official, reported result"],
             ["0.3", "94.9%", "Post-hoc, not used"],
             ["0.5", "95.8% (sensitivity 98.7%, specificity 91.0%)", "Post-hoc, not used"],
             ["0.9", "94.1%", "Post-hoc, not used"],
         ], [2.0, 2.4, 1.6], {"size": 10, "align": ["L", "C", "C"], "bold_rows": (0,)}),
    ]
