# PneumoScan AI - ML report (for the report writer)

Everything in this file is measured, not estimated, unless it says otherwise. Numbers are copied from
`models/metrics.json`, `models/xray_gate_metrics.json`, `data/dataset_summary.json` and the training logs
in `logs/`. Code lives in `ml/` (see `ml/README.md`).

## 1. Dataset

| Item | Value |
|---|---|
| Name | Kermany D., Zhang K., Goldbaum M. "Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for Classification", Mendeley Data, v2 (2018) |
| DOI / page | https://doi.org/10.17632/rscbjbr9sj.2 - https://data.mendeley.com/datasets/rscbjbr9sj/2 |
| File used | `ChestXRay2017.zip` (1,235,512,464 bytes), downloaded without login from the Mendeley public file API: `https://data.mendeley.com/public-files/datasets/rscbjbr9sj/files/f12eaf6d-6023-432f-acc9-80c9d7393433/file_downloaded` |
| Integrity | SHA-256 `13efc055629733dbab07877f8b3c9f81097840dbcdaa326a8542322c2281ce36` = the hash published by Mendeley |
| Licence | CC BY 4.0 (credit: Kermany et al. 2018, Cell 172(5):1122-1131, doi:10.1016/j.cell.2018.02.010) |
| Population | Paediatric patients (1-5 years), Guangzhou Women and Children's Medical Center; frontal (anterior-posterior) chest X-rays |
| Official train | 5,232 images: 1,349 NORMAL, 3,883 PNEUMONIA (2,538 bacterial, 1,345 viral by file name) |
| Official test | 624 images: 234 NORMAL, 390 PNEUMONIA - counts match the official release exactly |
| Image format | JPEG; 5,573 grayscale (L) + 283 RGB-encoded grayscale; median size 1281 x 888 px (width 384-2916 px) |

### Split used (patient-level, stratified)

The official test set is kept untouched. A validation set was carved out of the official TRAIN folder with
`StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=42)` grouped by patient
(`person123_...` -> patient P123; `IM-0115-0001` / `NORMAL2-IM-0115-0001` -> patient N0115, the NORMAL2 prefix is
ignored on purpose so grouping is conservative). One fold (14.3 %) became validation.

| Split | NORMAL | PNEUMONIA | Total | Patients |
|---|---|---|---|---|
| Train | 1,157 | 3,328 | 4,485 | 2,272 |
| Validation | 192 | 555 | 747 | 378 |
| Test (official) | 234 | 390 | 624 | 404 |

Leakage checks (`data/dataset_summary.json`):
* Patients in both train and validation: **0**.
* Exact duplicate files (SHA-1) between test and train/val: **0**; between val and train: **0**.
* Near duplicates (Pearson correlation of 64x64 thumbnails >= 0.99) between test and train/val: **0**
  (highest correlation 0.968, i.e. different radiographs).
* 264 patient numbers appear in both the official train and test folders. The dataset authors number patients
  separately inside each folder and state the test set comes from independent patients; the image-level checks
  above found no shared images, so this is a naming coincidence, not leakage. (An 8x8 perceptual hash first
  reported 177 "matches"; manual follow-up with the stronger correlation check showed these were hash
  collisions between different chest X-rays, so that check was replaced.)

## 2. Pre-processing

1. Any PIL mode is converted to 8-bit grayscale (`ml/common.py: to_gray_uint8`): 16/32-bit images are min-max
   scaled, transparency is composited on black, EXIF orientation is applied, colour is converted with the
   ITU-R 601 luma formula.
2. The image is squashed (not cropped) to a 512 x 512 "canonical view" with Lanczos resampling, so the whole
   chest is always visible and the heatmap maps back onto the original aspect ratio exactly. Training images are
   cached in this form (`data/processed/`).
3. Resize to the member's input size (384 or 448), replicate gray to 3 channels, normalise with ImageNet mean/std.

Training augmentation (`ml/datasets.py`): RandomResizedCrop (scale 0.75-1.0, aspect 0.9-1.1), horizontal flip
(p 0.5), rotation +-10 deg, translation +-5 %, scale 0.95-1.05, brightness/contrast +-0.2, Gaussian blur (p 0.2),
Gaussian noise sigma 0.02 (p 0.2). No vertical flips.

## 3. Model and training recipe

* Backbones: torchvision ResNet50 (`IMAGENET1K_V2` weights) and ResNet34 (`IMAGENET1K_V1`), downloaded from
  download.pytorch.org. The 1000-class layer is replaced by `Dropout(0.2) -> Linear(features, 2)`.
  All layers are fine-tuned (no frozen stages).
* Loss: cross-entropy with class weights (NORMAL 1.94, PNEUMONIA 0.67 = inverse frequency) and label smoothing 0.1.
* Optimiser: AdamW, weight decay 0.01, head lr 3e-4, backbone lr 1e-4 (0.33x), 1 warm-up epoch then cosine decay
  (per step), gradient clipping at norm 2.
* Mixed precision (fp16 autocast + GradScaler). Exponential moving average of the weights (decay 0.998, with
  warm-up); the EMA weights are the ones evaluated and saved.
* Up to 20 epochs, early stopping with patience 7 on validation ROC-AUC; the checkpoint with the best validation
  AUC is kept (ties broken by lower validation loss).
* Software: Python 3.11, PyTorch 2.11.0+cu128, torchvision 0.26.0, scikit-learn 1.9.1, Pillow 13.0, NumPy 2.4.
  Hardware: NVIDIA RTX 3050 Laptop GPU 6 GB, Intel i5-12450HX, 15.7 GB RAM, Windows 11.

### Ensemble, calibration, threshold (all fitted on VALIDATION)

1. Each member scores the image and its mirror image (flip test-time augmentation); the logit margin
   `z = logit(PNEUMONIA) - logit(NORMAL)` is averaged over the two views and over the three members.
2. Temperature scaling: `p = sigmoid(z / T)`, T fitted by minimising validation negative log-likelihood
   (T = 0.602 for the ensemble).
3. Decision threshold: the value that maximises Youden's J (sensitivity + specificity - 1, i.e. balanced
   accuracy) on validation; when a range of thresholds ties, the middle of the range (in logit space) is taken.
   Result: **t = 0.0743**. This rule was written into `ml/evaluate.py` before the test set was ever scored.
4. Risk level from the calibrated probability p (bands relative to t, stored in `models/ensemble.json`):
   **Low** p < t/2 (= 0.037), **Moderate** t/2 <= p < (1+t)/2 (= 0.537), **High** p >= 0.537.
   Moderate covers borderline cases and lower-probability positives ("possible pneumonia, see a doctor").

## 4. Experiments

All three runs use the recipe above; only architecture, input size, batch size and seed differ. Times are
wall-clock on the RTX 3050. Validation metrics use each model's own validation-fitted temperature and threshold.

| Run | Model | Input | Batch | Seed | Epochs run | Best epoch | Train time | Val AUC (best epoch, no TTA) |
|---|---|---|---|---|---|---|---|---|
| r50_384_s1 | ResNet50 | 384 | 24 | 1 | 14 (early stop) | 7 | 17.7 min | 0.9965 |
| r34_384_s2 | ResNet34 | 384 | 32 | 2 | 17 (early stop) | 10 | 13.9 min | 0.9971 |
| r50_448_s3 | ResNet50 | 448 | 16 | 3 | 14 (early stop) | 7 | 23.9 min | 0.9974 |

Total training time: 55.5 min. Training curves: `docs/figures/training_curves_<run>.png`.

### Validation and test results (flip TTA, threshold from validation)

| Model | Threshold | Val acc % | Val bal. acc % | Val AUC | **Test acc %** | Test precision % | Test sensitivity % | Test specificity % | Test F1 % | Test AUC | Test confusion (TN, FP, FN, TP) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ResNet50 @384 | 0.038 | 98.39 | 98.58 | 0.9974 | 91.99 | 88.81 | 99.74 | 79.06 | 93.96 | 0.9811 | 185, 49, 1, 389 |
| ResNet34 @384 | 0.067 | 98.13 | 98.57 | 0.9977 | 94.87 | 92.82 | 99.49 | 87.18 | 96.04 | 0.9884 | 204, 30, 2, 388 |
| ResNet50 @448 | 0.044 | 98.13 | 97.89 | 0.9972 | 91.67 | 88.41 | 99.74 | 78.21 | 93.73 | 0.9828 | 183, 51, 1, 389 |
| **Ensemble (final)** | **0.074** | **98.39** | **98.58** | **0.9980** | **94.55** | **92.18** | **99.74** | **85.90** | **95.81** | **0.9867** | **201, 33, 1, 389** |

**Final model = the 3-member ensemble.** It was chosen before the test set was scored (pre-committed plan:
ensemble of every trained member) and it is also the best model on validation (highest val AUC 0.9980, tied
best balanced accuracy). Final official-test numbers (624 images): **accuracy 94.55 % (590/624), sensitivity
99.74 % (389/390), specificity 85.90 % (201/234), precision 92.18 %, F1 95.81 %, ROC-AUC 0.9867, PR-AUC 0.9898**.
Bacterial pneumonia sensitivity 99.6 % (241/242), viral 100 % (148/148). The single missed pneumonia is
`person154_bacteria_728.jpeg` (p = 0.0008).

**The 95 % target was not reached (94.55 %, 3 images short).** Note for honesty: the ResNet34 member alone scored
94.87 % on test, but validation did not prefer it (val balanced accuracy 98.57 % vs 98.58 %, AUC 0.9977 vs 0.9980),
so switching to it after seeing test results would be test-set tuning and was not done.

### Every test-set evaluation that was run

Exactly **one** test evaluation was run (`logs/test_evaluations.jsonl`, 2026-11-07 23:22): the final ensemble
and, in the same run, each member with its own validation-chosen settings (the table above). Nothing was
re-trained, re-thresholded or re-selected after it. All earlier decisions used `--val-only`.

### Why test accuracy is lower than validation accuracy

* Validation (98.4 %) comes from the same pool as training; the official test set is known to be harder and
  differently distributed (published ResNet baselines on the same 624 images: 85-88 %; dataset authors 92.8 %;
  see `docs/research/accuracy_research.md`).
* The errors are almost all false alarms (33 NORMAL images called PNEUMONIA) - the same pattern every paper
  on this test set reports. On validation the NORMAL images were very clean (only 2 false positives out of 192),
  while a tail of pneumonia images had low scores, so the validation-optimal threshold came out low (0.074).
  On the test set that low threshold favours sensitivity (99.7 %) over specificity (85.9 %).
* Post-hoc sensitivity analysis - **for discussion only, NOT used to choose anything and NOT the reported
  result**: with the same ensemble, a threshold of 0.5 would give 95.8 % test accuracy (sens 98.7 %, spec 91.0 %),
  0.3 gives 94.9 %, 0.9 gives 94.1 %. This shows the gap is caused by the validation/test distribution shift in
  where the threshold should be, not by poor ranking (test AUC 0.987). Choosing the threshold from these test
  numbers would be cheating, so the official result remains 94.55 %.
* Grad-CAM (see `docs/figures/gradcam_examples.png`) shows the models mostly look at the lungs, but sometimes also
  at burned-in text (the "R" side marker, exposure values, time stamps). This partial shortcut learning is a
  likely contributor to errors on images from a slightly different acquisition setting.

## 5. X-ray gate (rejecting images that are not chest X-rays)

Implementation: `ml/xray_gate.py`; `check_image()` in `ml/inference.py`.
1. Heuristics: smallest side < 64 px -> "too small"; gray-level standard deviation < 8 -> "blank";
   mean HSV saturation of non-dark pixels > 0.12 or > 5 % strongly coloured pixels -> "colour photo".
2. Out-of-distribution score: 2048-d pooled layer4 features of the r50_384_s1 member; class-conditional
   Mahalanobis distance with a shared Ledoit-Wolf covariance fitted on the 4,485 TRAIN X-rays. Threshold =
   1.15 x the 99.5th percentile of VALIDATION distances = 66.04 (val median 41.0, val max 64.7).
   `score = 1 / (1 + (d / threshold)^4)` (0.5 exactly at the cut-off, about 1 for typical X-rays).

| Check | Result |
|---|---|
| Official TEST chest X-rays accepted | **620 / 624 (99.36 %)** - the 4 refused are NORMAL images (IM-0015, IM-0021, IM-0039, NORMAL2-IM-0282); the classifier would have labelled all 4 correctly |
| Non-X-ray images rejected | **33 / 33**: 22 scikit-image photos/textures (astronaut, chelsea, cat, coffee, rocket, text, camera, moon, page, coins, horse, clock, hubble, immunohistochemistry, retina, brick, grass, gravel, cell, checkerboard, colorwheel, logo), grayscale and RGB noise, 5 plain colours, a gradient, 3 synthetic text documents (one inverted) |
| Harder case: grayscale copies of the 16 colour images (only the feature-distance test can catch these) | **16 / 16 rejected** (highest score 0.165, cut-off 0.5) |

Limitation: the gate learns "looks like these paediatric chest X-rays", so other radiographs (e.g. a hand X-ray)
or adult chest films may or may not be accepted; it is a convenience, not a safety guarantee.

## 6. Grad-CAM

Grad-CAM on `layer4` (last residual stage, 12x12 maps at 384 px, 14x14 at 448 px) of every member; the map for
the ensemble's final label is computed per member with one backward pass of the logit margin (the NORMAL map is
the negated-gradient map), resized to the display image, averaged over members and normalised. The app gets:
`input_png` (grayscale, original aspect ratio, longest side 768 px), `gradcam_heatmap_png` (RGBA jet map, alpha
0.2-1.0 growing with importance) and `gradcam_overlay_png` (= heatmap over the X-ray at 60 % opacity). All three
have identical size, so they line up pixel-exactly (tested).

## 7. Inference speed and checks

| Setting | Time per image (median) |
|---|---|
| GPU (RTX 3050), 3 ResNets x 2 views + Grad-CAM, incl. pre-processing and PNG encoding | **376 ms** (p95 457 ms) |
| GPU without Grad-CAM | 233 ms |
| CPU only (i5-12450HX), with Grad-CAM | 1,248 ms |

The first call after start-up takes about 1 s extra (CUDA warm-up). Consistency check: running `predict()` on
all 624 test files one by one reproduces the batch evaluation (max probability difference 0.00047, 0 label
changes). Shipped weights are fp16 (41-46 MB each); all reported metrics were computed with these exact
fp16-rounded weights. `pytest ml/test_inference.py`: **24 passed** (contract keys/types, PNG sizes and aspect,
modes L/RGB/RGBA/LA/P/I;16/I/F/CMYK/1, 16x16 / 70x60 / 4000x3500 images, 16-bit DICOM through `load_image`,
rejection of 5 photos + blank + noise, answer key, `info()`).

## 8. Figures (`docs/figures/`, 250 dpi PNG)

| File | Content |
|---|---|
| `architecture_diagram.png` | Full pipeline: input, pre-processing, ResNet50 stages with output sizes, pooling, FC, ensemble + TTA, calibration, threshold, output, Grad-CAM branch |
| `residual_block_diagram.png` | Bottleneck residual block with identity shortcut |
| `class_distribution.png` | NORMAL / PNEUMONIA counts in train / validation / test |
| `sample_images.png` | 4 normal + 4 pneumonia training X-rays |
| `training_curves_<run>.png` | Train/validation accuracy and loss per epoch, best epoch marked (3 files) |
| `confusion_matrix_test.png` | Final ensemble on the 624 test images |
| `roc_curve_test.png` | ROC curves (ensemble + members) with AUC and the operating point |
| `pr_curve_test.png` | Precision-recall curves with average precision |
| `probability_histogram_test.png` | Distribution of ensemble probabilities per true class with the threshold |
| `gradcam_examples.png` | Grad-CAM: 2 correct pneumonia, 2 correct normal, 1 false positive, 1 false negative |

## 9. Engineering notes (problems met and fixed)

* `channels_last` memory format was 8x slower on this GPU/driver/PyTorch combination (66 vs 516 images/s for a
  ResNet18 benchmark) - removed.
* The laptop has little free memory (commit limit) while other programs run: 6 DataLoader workers (~0.6 GB each on
  Windows) caused CUDA "out of memory"/"memory allocation failure" errors at start-up; 3 workers and validation in
  the main process fixed it. `cudnn.benchmark` was switched off (no speed gain, extra memory).
* The Mendeley download was slow over one connection (~40-100 KB/s); a 24-part parallel range download was used,
  then the SHA-256 was verified against Mendeley's published hash.

## 10. Limitations

* One hospital, children aged 1-5: results do not transfer automatically to adults or other hospitals.
* Binary NORMAL / PNEUMONIA only; does not separate bacterial and viral pneumonia or detect other diseases.
* False alarms on normal X-rays (specificity 85.9 % on the official test set) are the main error type.
* Partial shortcut learning (attention to burned-in text) seen in some Grad-CAM maps.
* The validation set is from the same distribution as training, so it overestimates test performance and gave a
  threshold that is too low for the test set.
* Not a medical device; for education and decision support only.

## 11. What could raise the test accuracy honestly (future work)

* A validation set that resembles the deployment data (e.g. a separate hospital) to choose the threshold.
* Masking or cropping burned-in text/markers, or lung segmentation, to reduce shortcut learning.
* Larger / more diverse training data (e.g. adding other public paediatric datasets).
