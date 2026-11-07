# Accuracy research: reaching ≥95% on the official Kermany test set with ResNets

Written by the Research agent for the ML agent. Every number below has a source link. Where a point is my engineering advice and not a published result, it says **(advice, not a published number)**.

---

## 1. The short answer

- **≥95% on the official 624-image test set is hard but possible.** The dataset's own authors reached **92.8%**. Plain ResNet-18/50 baselines on the official test set land at **85–88%**. The published results above 95% that really use the official test set come from **ensembles** (96.4% for one five-model ensemble).
- Most papers that report **97–99%** did **not** use the official test set. They pooled all 5,856 images and re-split them at random (or used 5-fold cross-validation). Those numbers are **not comparable** with ours. Do not use them as targets.
- On the official test set, the main failure is the **same in every paper**: recall for pneumonia is very high (≈98–99%) but **normal images get called pneumonia** (false positives). So accuracy depends mostly on **specificity** and on **where the decision threshold sits**.
- The biggest wins are therefore: (1) balance the classes in training, (2) pick the threshold on a proper validation split, (3) ensemble 2–3 ResNets and average probabilities, (4) light test-time augmentation. All of these must be fixed **before** looking at the test set.

---

## 2. The dataset facts that matter

| Fact | Value | Source |
|---|---|---|
| Paper | Kermany et al., *Cell* 172(5):1122–1131.e9, 2018 | [PubMed 29474911](https://pubmed.ncbi.nlm.nih.gov/29474911/), DOI [10.1016/j.cell.2018.02.010](https://doi.org/10.1016/j.cell.2018.02.010) |
| Patients | Paediatric cohort (1–5 years old), Guangzhou Women and Children's Medical Center | [BMC Med Inform Decis Mak 2026, PMC13267658](https://pmc.ncbi.nlm.nih.gov/articles/PMC13267658/) (dataset section) |
| Licence | CC BY 4.0 (Mendeley Data, DOI 10.17632/rscbjbr9sj.2) | [DataCite record](https://api.datacite.org/dois/10.17632/rscbjbr9sj.2) |
| Training images (Mendeley original) | 5,232: 1,349 normal, 3,883 pneumonia (2,538 bacterial, 1,345 viral) | review quoting Kermany: [Chumbita et al., J Clin Med 2020, PMC7019351](https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/) |
| Kaggle re-packaging (P. Mooney) | train 5,216 (1,341 normal / 3,875 pneumonia); test 624 (234 normal / 390 pneumonia) | [Yue et al., Comput Intell Neurosci 2020, PMC7520009](https://pmc.ncbi.nlm.nih.gov/articles/PMC7520009/) (Table 2); [BMC Med Inform Decis Mak 2026, PMC13267658](https://pmc.ncbi.nlm.nih.gov/articles/PMC13267658/) |
| Class balance | Train ≈ 74% pneumonia; test = 62.5% pneumonia (390/624) | computed from the counts above |
| Kermany's own result (pneumonia vs normal) | accuracy **92.8%**, sensitivity **93.2%**, specificity **90.1%**, ROC AUC **96.8%** | [PMC7019351](https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/) |
| Kermany's own result (bacterial vs viral) | accuracy **90.7%**, sensitivity **88.6%** | [PMC7019351](https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/) |

Note: we are not allowed to use Kaggle (login). The original release is on Mendeley Data: Kermany D., "Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for Classification", version 2, 2018, https://doi.org/10.17632/rscbjbr9sj.2. The ML agent should confirm the counts of whatever copy it downloads.

---

## 3. What published work actually got on the **official** test set

These are the honest reference points for us.

| Work | Model | Result on official 624 test | Source |
|---|---|---|---|
| Kermany et al. 2018 (dataset authors) | Inception-V3, ImageNet transfer learning | Acc 92.8%, Sens 93.2%, Spec 90.1%, AUC 96.8% | [PMC7019351](https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/) |
| Yang et al. 2023, MedMNIST v2 (PneumoniaMNIST uses the **same 624 test images**; val = 10% of train) | ResNet-18, 28 px | ACC 0.854, AUC 0.944 | [Sci Data 10:41, PMC9852451](https://pmc.ncbi.nlm.nih.gov/articles/PMC9852451/) Table 3 |
| same | ResNet-18, 224 px (upscaled from 28) | ACC 0.864, AUC 0.956 | same |
| same | ResNet-50, 28 px | ACC 0.854, AUC 0.948 | same |
| same | ResNet-50, 224 px (upscaled from 28) | ACC 0.884, AUC 0.962 | same |
| Yue et al. 2020 (Kaggle split, 226 px, 20 epochs) | ResNet-18 | Acc 85.5%, **Recall 98.9%** | [PMC7520009](https://pmc.ncbi.nlm.nih.gov/articles/PMC7520009/) Table 4 |
| same | ResNet-50 | Acc 87.5%, **Recall 98.5%** | same |
| same | MobileNet (their best) | Acc 92.79%, Recall 98.90% | same |
| Chouhan et al. 2020 | Ensemble of 5 ImageNet-pretrained CNNs (majority voting) | **Acc 96.4%, Recall 99.62%** on "unseen data from the Guangzhou ... dataset" (trained on the 5,232 training images) | abstract via [Applied Sciences 10(2):559](https://doi.org/10.3390/app10020559); voting method and 5,232 count from the comparison in [Hashmi et al. 2020, PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/) Table 7 |
| Liang & Zheng 2020 | Residual network + dilated convolutions, transfer learning | **Recall 96.7%, F1 92.7%** on the test set | [Comput Methods Programs Biomed 187:104964, PubMed 31262537](https://pubmed.ncbi.nlm.nih.gov/31262537/) |
| Mabrouk et al. 2022 | Ensemble DenseNet169 + MobileNetV2 + ViT | Acc 93.91%, F1 93.88% "on the testing phase" | [arXiv 2312.07965](https://arxiv.org/abs/2312.07965) / [Applied Sciences 12(13):6448](https://doi.org/10.3390/app12136448) |

**Reading this table:**
- AUC is already 0.94–0.97 even for weak baselines, but accuracy is only 85–88%. The model **ranks** images well; the **threshold** is in the wrong place. (Derived from MedMNIST v2 Table 3.)
- Yue et al.: recall ≈ 99% but accuracy 85–87%. That means almost all errors are normal images called pneumonia.
- Chouhan: recall 99.62% with accuracy 96.4%. Working it out: ≈1–2 missed pneumonias, ≈21 false alarms out of 234 normals (my arithmetic from their two numbers, not a reported figure). Even the best ensemble loses accuracy on normals.

---

## 4. Results that are **not** comparable (re-split data)

Use these only in the literature survey, clearly labelled. Do not chase these numbers.

| Work | What they did with the split | Reported | Source |
|---|---|---|---|
| Hashmi et al. 2020 | "the dataset was shuffled and arranged into training and test sets only": 5,136 train / 700 test (300 normal, 400 pneumonia). Image-level shuffle, so the same child can be in train and test. | Weighted ensemble (ResNet18, Xception, InceptionV3, DenseNet121, MobileNetV2): Acc 98.43%, AUC 99.76 | [PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/) |
| Kundu et al. 2021 | 5-fold cross-validation on all 5,856 images pooled | Ensemble GoogLeNet + ResNet-18 + DenseNet-121: Acc 98.81%; ResNet-18 alone 97.29% | [PLoS ONE 16(9):e0256630, PMC8423280](https://pmc.ncbi.nlm.nih.gov/articles/PMC8423280/) |
| Stephen et al. 2019 | Own CNN from scratch, reports **validation** accuracy | 93.73% (validation) | [J Healthc Eng 2019:4180949, PubMed 31049186](https://pubmed.ncbi.nlm.nih.gov/31049186/) |

Why they are higher: when you pool and re-split, train and test come from the same distribution (and often the same patients). The official test set was a separate, harder set. This is the train/test **distribution shift** in point 5.

---

## 5. Known pitfalls (read before training)

1. **The official validation folder is useless.** The Kaggle copy has a 16-image `val` folder (project brief). 16 images cannot pick a threshold or an epoch. Merge it into training and **carve your own stratified validation split (10–15%) from the training set.** MedMNIST v2 did exactly this: "We split the source training set with a ratio of 9:1 into training and validation set" ([PMC9852451](https://pmc.ncbi.nlm.nih.gov/articles/PMC9852451/)).
2. **Patient-level leakage.** Kermany's training set has many images per patient (5,232 images from fewer children). If you split at image level, the same child can be in train and val; val accuracy will look too good and the chosen threshold will be over-confident. **Split by patient ID if the file names carry one** (ML agent: check the file name pattern in the downloaded copy; do not assume). Hashmi et al. shuffled at image level ([PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/)) — a known weakness.
3. **Train/test distribution shift.** Papers that re-split the pooled data report 97–99% (section 4), while models evaluated on the official test set report 85–96% (section 3). The official test set behaves differently from the training data. Expect your val accuracy to be higher than your test accuracy (advice: plan for a few points of drop). Do not "fix" it by tuning on test.
4. **Models over-predict pneumonia on the test set.** See section 3 (recall ~99%, specificity much lower). Likely causes (advice): 74% pneumonia in train vs 62.5% in test, and the shift above. Remedies: class-balanced loss or sampler, and threshold chosen on a validation split where normals are well represented.
5. **Shortcut learning / hospital signatures.** Zech et al. 2018 showed CNNs could identify the hospital system of a chest X-ray for 99.95% (NIH) and 99.98% (MSH) of images, and that pneumonia models generalised worse to external hospitals (internal AUC 0.931 vs external 0.815) ([PLOS Med 15(11):e1002683, PubMed 30399157](https://pubmed.ncbi.nlm.nih.gov/30399157/)). For us: our numbers are for one paediatric hospital only. Grad-CAM should be checked to make sure the model looks at the lungs, not text markers or borders. Kundu et al. found misclassified cases where Grad-CAM showed attention on the spine ([PMC8423280](https://pmc.ncbi.nlm.nih.gov/articles/PMC8423280/)).
6. **Tuning on the test set.** Many online notebooks pick the epoch, threshold or ensemble weights by looking at test accuracy. That inflates results and breaks project rule 1. Hashmi et al. optimised ensemble weights on a held-out set of 400 images carved out of training — that part is the right idea ([PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/)).
7. **Resolution of 28 px is too low.** MedMNIST v2 at 28 px gives only 85.4% for ResNet-18 ([PMC9852451](https://pmc.ncbi.nlm.nih.gov/articles/PMC9852451/)). Use full-resolution source images resized to ≥224.

---

## 6. What the published recipes used (settings that worked)

| Setting | Hashmi 2020 | Kundu 2021 | MedMNIST+ (Doerrich et al.) |
|---|---|---|---|
| Input size | 224×224 (ResNet18, DenseNet121, MobileNetV2), 229×229 (Inception, Xception) | 224×224×3 | 224×224 (zero-padded) |
| Optimizer | SGD, lr 0.001, momentum 0.9, weight decay 0.0001 | Adam, lr 0.0001, ReduceLROnPlateau | AdamW, lr 0.0001, cosine schedule, batch 64 |
| Epochs | 25 | 30 | up to 100 with early stopping on validation |
| All layers trainable? | Yes ("All the layers of the networks used were trainable") | fine-tuned | end-to-end |
| Imbalance | Augmented only the normal class (each normal image augmented twice → 3,399 normal vs 3,623 pneumonia) | weights from metrics | — |
| Augmentation | rotation 45, vertical shift 0.2, horizontal shift 0.15, shear 16, crop-and-pad 0.25 | — | — |
| Ensemble | Weighted average, weights found by differential evolution on 400 held-out images; equal weights gave 97.45%, optimised 98.43% (their own split) | Weighted average, weights from precision/recall/F1/AUC via tanh | — |
| Source | [PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/) | [PMC8423280](https://pmc.ncbi.nlm.nih.gov/articles/PMC8423280/) | [arXiv 2404.15786](https://arxiv.org/abs/2404.15786) |

Other verified points:
- **Hardware:** Hashmi et al. trained all five networks on a "NVIDIA GeForce GTX 1060 6 GB GPU" ([PMC7345724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/)). So 6 GB is enough for ResNet18/50 fine-tuning at 224 px.
- **Resolution:** MedMNIST+ reports that higher resolutions do not consistently help beyond a certain point ([arXiv 2404.15786](https://arxiv.org/abs/2404.15786)). For this task 224 is a sound default; 288–320 is worth one experiment only if time allows **(advice)**.
- **Ensembles help on the official test set.** Chouhan's 5-model ensemble (96.4%) beat each single model ([doi 10.3390/app10020559](https://doi.org/10.3390/app10020559)). Kundu found the ensemble beat every single base learner, and that the weighted average beat majority voting ([PMC8423280](https://pmc.ncbi.nlm.nih.gov/articles/PMC8423280/)).
- **CLAHE:** Nneji et al. 2022 used a CLAHE channel with Inception-V3 (95.6% alone) and fused it with other channels (98.3%), but on an 80/20 re-split of combined data, so the gain is not proven for the official test ([Diagnostics 12(2):325, PMC8870748](https://pmc.ncbi.nlm.nih.gov/articles/PMC8870748/)). Treat CLAHE as an **optional experiment**, decided on validation only.

---

## 7. Recommended recipe for RTX 3050 6 GB, ~3–4 hours total

Everything below is chosen on **validation only**. Items marked (advice) are engineering judgement, not published numbers.

**Data**
1. Use the official train folder (+ the 16 val images) for training; keep the official 624 test images locked away until the very end.
2. Make a **stratified 85/15 train/val split, grouped by patient ID** if the file names allow it. Fix the random seed and save the split to a file.
3. Read images as grayscale, convert to 3 channels by copying, resize so the short side is 256, centre/random crop 224, ImageNet mean/std normalisation. (advice)

**Augmentation (train only)** (advice; lighter than Hashmi's 45° rotation)
4. RandomResizedCrop(224, scale 0.8–1.0, ratio 0.9–1.1), rotation ±10°, small translation (≤0.05), brightness/contrast ±0.1–0.2. **No vertical flip.** Horizontal flip is optional (it creates a mirror-image heart; test it on val, keep only if val AUC improves).

**Class imbalance**
5. Use class-weighted cross-entropy (weight ∝ 1/class frequency) **or** a WeightedRandomSampler — not both. This directly attacks the "too many false pneumonias" problem in section 3. Label smoothing 0.05–0.1 is a reasonable extra (advice).

**Models and schedule** (ImageNet-pretrained torchvision weights, mixed precision `torch.autocast` + `GradScaler`, `channels_last`)
6. Stage 1 – head only: freeze the backbone, train the new 2-class head for 2 epochs, AdamW lr 1e-3.
7. Stage 2 – full fine-tune: unfreeze everything, AdamW, lr 1e-4 for the backbone (1e-3 for the head), weight decay 1e-4, cosine schedule with 1 epoch warm-up, 12–15 epochs, **early stopping on validation AUC** (patience 4). Keep the best-val-AUC checkpoint. (Matches the lr range used by Kundu and MedMNIST+.)
8. Batch size: ResNet-18/34 at 224 → 64; ResNet-50 at 224 → 32 (drop to 24 or use gradient accumulation if out of memory) (advice).
9. Train **three members**: ResNet-50 (seed 1), ResNet-34 (or a second ResNet-50 with another seed), ResNet-18. Rough budget (advice, not measured): ResNet-18 ≈ 25–35 min, ResNet-34 ≈ 40–50 min, ResNet-50 ≈ 60–90 min for ~15 epochs on 4.4k images at 224 px. Total ≈ 2.5–3 h, leaving time for evaluation and Grad-CAM. If time is short, drop ResNet-34.

**Ensemble, calibration, threshold**
10. Ensemble = average of the members' **probabilities** (optionally weighted; pick weights on val only, as Hashmi did on a held-out set). Kundu found a weighted average beat majority voting.
11. **Test-time augmentation:** average predictions over the original + 2–4 mild variants (e.g., small scale/shift crops; add horizontal flip only if it was used in training). Decide on/off using val AUC (advice).
12. **Calibrate** with temperature scaling fitted on val (the app contract asks for a calibrated `prob_pneumonia`) (advice).
13. **Threshold:** choose on the val split, e.g., the point that maximises Youden's J (sensitivity + specificity − 1) or val accuracy, subject to sensitivity ≥ 95% (missing pneumonia is worse than a false alarm). Save it to `models/metrics.json`. **Never** move it after seeing test results.

**Final evaluation**
14. Run the test set **once** with the frozen pipeline. Report accuracy, precision, recall (sensitivity), specificity, F1, ROC-AUC, confusion matrix — even if accuracy is below 95%. Also report the single best ResNet next to the ensemble, so the report shows what each step bought.

**Optional experiments if time is left (all decided on val):** CLAHE preprocessing (clip limit ~2.0, 8×8 tiles), input 288–320 px for ResNet-50, a second seed of the best model.

---

## 8. Realistic expectations

- A single well-trained ResNet-50 with class balancing and a val-chosen threshold: roughly in Kermany's range (≈90–93%). (advice, based on section 3)
- A 3-ResNet ensemble + TTA + val-chosen threshold: the published official-test ensembles reach 93.9–96.4% ([Mabrouk 2022](https://arxiv.org/abs/2312.07965); [Chouhan 2020](https://doi.org/10.3390/app10020559)). 95% is reachable but **not guaranteed**. If the honest number is below 95%, report it as it is (project rule 1) and explain the distribution shift in the report.

---

## Sources (all checked)

1. Kermany DS, et al. Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning. Cell. 2018;172(5):1122–1131.e9. https://doi.org/10.1016/j.cell.2018.02.010
2. Chumbita M, et al. Can Artificial Intelligence Improve the Management of Pneumonia. J Clin Med. 2020 (review quoting Kermany's numbers). https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/
3. Yang J, et al. MedMNIST v2. Scientific Data. 2023;10:41. https://doi.org/10.1038/s41597-022-01721-8
4. Yue Z, Ma L, Zhang R. Comparison and Validation of Deep Learning Models for the Diagnosis of Pneumonia. Comput Intell Neurosci. 2020;2020:8876798. https://doi.org/10.1155/2020/8876798
5. Chouhan V, et al. A Novel Transfer Learning Based Approach for Pneumonia Detection in Chest X-ray Images. Applied Sciences. 2020;10(2):559. https://doi.org/10.3390/app10020559
6. Liang G, Zheng L. A transfer learning method with deep residual network for pediatric pneumonia diagnosis. Comput Methods Programs Biomed. 2020;187:104964. https://doi.org/10.1016/j.cmpb.2019.06.023
7. Mabrouk A, et al. Pneumonia Detection on Chest X-ray Images Using Ensemble of Deep Convolutional Neural Networks. Applied Sciences. 2022;12(13):6448. https://doi.org/10.3390/app12136448
8. Hashmi MF, et al. Efficient Pneumonia Detection in Chest Xray Images Using Deep Transfer Learning. Diagnostics. 2020;10(6):417. https://doi.org/10.3390/diagnostics10060417
9. Kundu R, et al. Pneumonia detection in chest X-ray images using an ensemble of deep learning models. PLoS ONE. 2021;16(9):e0256630. https://doi.org/10.1371/journal.pone.0256630
10. Stephen O, et al. An Efficient Deep Learning Approach to Pneumonia Classification in Healthcare. J Healthc Eng. 2019;2019:4180949. https://doi.org/10.1155/2019/4180949
11. Zech JR, et al. Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs. PLOS Medicine. 2018;15(11):e1002683. https://doi.org/10.1371/journal.pmed.1002683
12. Doerrich S, Di Salvo F, Brockmann J, Ledig C. Rethinking model prototyping through the MedMNIST+ dataset collection. arXiv:2404.15786. https://arxiv.org/abs/2404.15786
13. Nneji GU, et al. Multi-Channel Based Image Processing Scheme for Pneumonia Identification. Diagnostics. 2022;12(2):325. https://doi.org/10.3390/diagnostics12020325
14. Ensemble localized patch residual convolution neural networks for pneumonia detection using chest X-ray. BMC Med Inform Decis Mak. 2026 (used only for dataset counts/age range). https://pmc.ncbi.nlm.nih.gov/articles/PMC13267658/
15. Kermany D. Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for Classification. Mendeley Data, v2, 2018. https://doi.org/10.17632/rscbjbr9sj.2
