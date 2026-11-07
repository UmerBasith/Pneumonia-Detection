# Literature Survey (draft for the report, Chapter 2)

Written by the Research agent. Every paper below was checked against PubMed, Crossref, arXiv or the open-access full text. Numbers are quoted from the papers (or, where stated, from a peer-reviewed paper that quotes them). Reference numbers [1]–[13] match the IEEE list at the end.

**Important note for the report writer:** Several papers report very high accuracy (97–99%) on the Kermany data, but they **re-split** the images or used cross-validation instead of the official 624-image test set. Their numbers cannot be compared directly with ours. This is pointed out under each paper and in the summary table.

---

## 2.1 Deep Residual Learning for Image Recognition — He et al., 2016 [1]

- **Citation:** K. He, X. Zhang, S. Ren, J. Sun, "Deep Residual Learning for Image Recognition," *Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778. DOI: 10.1109/CVPR.2016.90
- **Summary:** Very deep networks are hard to train because accuracy saturates and then degrades as layers are added. The authors reformulate layers to learn *residual functions* with reference to the layer input, using identity "shortcut" connections. This makes very deep networks easier to optimise, so they gain accuracy from depth. Residual networks up to 152 layers were trained on ImageNet — 8× deeper than VGG nets but with lower complexity.
- **Method:** Residual blocks (two 3×3 convolutions, or 1×1–3×3–1×1 "bottleneck" blocks in deeper models) with identity skip connections, batch normalisation, global average pooling.
- **Dataset:** ImageNet (ILSVRC); also CIFAR-10 and COCO.
- **Result:** An ensemble of residual nets reached **3.57% top-5 error** on the ImageNet test set and won 1st place in the ILSVRC 2015 classification task; 28% relative improvement on COCO object detection.
- **Relation to this project:** ResNet is the backbone of PneumoScan AI. We use ImageNet-pretrained ResNet-18/34/50 and fine-tune them on chest X-rays.

## 2.2 Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning — Kermany et al., 2018 [2]

- **Citation:** D. S. Kermany *et al.*, "Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep Learning," *Cell*, vol. 172, no. 5, pp. 1122–1131.e9, 2018. DOI: 10.1016/j.cell.2018.02.010
- **Summary:** The authors built a transfer-learning diagnostic tool, first for retinal OCT images and then for paediatric chest X-rays. Transfer learning let a network trained on general images be adapted with a fraction of the usual data. They also highlighted image regions used by the network to make decisions more interpretable. The chest X-ray data they released is the dataset used in this project.
- **Method:** Inception-V3 pretrained on ImageNet, fine-tuned (transfer learning).
- **Dataset:** Paediatric chest X-rays from Guangzhou Women and Children's Medical Center; 5,232 training images (1,349 normal; 3,883 pneumonia, of which 2,538 bacterial and 1,345 viral) and an independent test set (624 images).
- **Result:** Pneumonia vs normal — accuracy **92.8%**, sensitivity **93.2%**, specificity **90.1%**, AUC **96.8%**. Bacterial vs viral — accuracy **90.7%**, sensitivity 88.6%, specificity 90.9%, AUC 94.0% (as reported in the review by Chumbita et al., *J Clin Med* 2020).
- **Relation:** Source of our dataset and the main baseline on the same official test split.

## 2.3 CheXNet: Radiologist-Level Pneumonia Detection on Chest X-Rays with Deep Learning — Rajpurkar et al., 2017 [3]

- **Citation:** P. Rajpurkar, J. Irvin, K. Zhu, B. Yang, H. Mehta, T. Duan, D. Ding, A. Bagul, C. Langlotz, K. Shpanskaya, M. P. Lungren, A. Y. Ng, "CheXNet: Radiologist-Level Pneumonia Detection on Chest X-Rays with Deep Learning," arXiv:1711.05225, 2017.
- **Summary:** CheXNet is a 121-layer convolutional network (DenseNet) trained to detect pneumonia from frontal chest X-rays. Four practising academic radiologists labelled a test set so the model could be compared with human readers. CheXNet exceeded the average radiologist on the F1 metric. The model was then extended to all 14 diseases in the dataset.
- **Method:** 121-layer DenseNet, trained end-to-end.
- **Dataset:** ChestX-ray14 — over 100,000 frontal-view X-ray images with 14 disease labels (adult patients).
- **Result:** F1 above the average of four radiologists for pneumonia; state-of-the-art on all 14 diseases at the time.
- **Relation:** Shows that deep CNNs can approach expert reading of chest X-rays; motivates our CNN approach and our comparison with clinical practice.

## 2.4 Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization — Selvaraju et al., 2017 [4]

- **Citation:** R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, D. Batra, "Grad-CAM: Visual Explanations from Deep Networks via Gradient-Based Localization," *Proc. IEEE Int. Conf. Computer Vision (ICCV)*, 2017, pp. 618–626. DOI: 10.1109/ICCV.2017.74
- **Summary:** Grad-CAM produces "visual explanations" for CNN decisions. It uses the gradients of the target class flowing into the final convolutional layer to build a coarse heat map of the image regions that matter for the prediction. It works with many CNN families, including ResNets, without changing or retraining the model. Human studies showed Grad-CAM helps users build appropriate trust and can reveal dataset bias.
- **Method:** Gradient-weighted class activation mapping on the last convolutional feature maps.
- **Dataset:** ImageNet classification, image captioning and visual question answering benchmarks.
- **Result:** Better localisation than earlier methods; more faithful to the model; helped untrained users tell a stronger model from a weaker one.
- **Relation:** PneumoScan AI shows a Grad-CAM heat map for every X-ray so doctors can check that the model looks at the lungs.

## 2.5 Defining community acquired pneumonia severity on presentation to hospital (CURB-65) — Lim et al., 2003 [5]

- **Citation:** W. S. Lim, M. M. van der Eerden, R. Laing, W. G. Boersma, N. Karalus, G. I. Town, S. A. Lewis, J. T. Macfarlane, "Defining community acquired pneumonia severity on presentation to hospital: an international derivation and validation study," *Thorax*, vol. 58, no. 5, pp. 377–382, 2003. DOI: 10.1136/thorax.58.5.377
- **Summary:** The authors pooled three prospective studies from the UK, New Zealand and the Netherlands (1,068 adults, 30-day mortality 9%) to build a simple severity score. One point each for Confusion, Urea > 7 mmol/L, Respiratory rate ≥ 30/min, low Blood pressure (systolic < 90 or diastolic ≤ 60 mmHg) and age ≥ 65 gives the six-point CURB-65 score. The score stratified patients into low, intermediate and high-risk groups with different management. A version without urea (CRB-65) was proposed for the community.
- **Method:** Multiple logistic regression on an 80% derivation cohort, tested on a 20% validation cohort.
- **Dataset:** 1,068 hospitalised adults with community-acquired pneumonia.
- **Result:** Derivation cohort 30-day mortality: score 0–1 → 1.5%, score 2 → 9.2%, score 3–5 → 22%; the validation cohort showed a similar pattern.
- **Relation:** PneumoScan AI includes a CURB-65 calculator so a doctor can combine the X-ray result with a standard clinical severity score.

## 2.6 MedMNIST v2 — Yang et al., 2023 [6]

- **Citation:** J. Yang, R. Shi, D. Wei, Z. Liu, L. Zhao, B. Ke, H. Pfister, B. Ni, "MedMNIST v2 – A large-scale lightweight benchmark for 2D and 3D biomedical image classification," *Scientific Data*, vol. 10, art. no. 41, 2023. DOI: 10.1038/s41597-022-01721-8
- **Summary:** MedMNIST v2 is a collection of 12 2D and 6 3D standardised biomedical datasets with small images (28×28) for benchmarking. One subset, PneumoniaMNIST, is built from the Kermany chest X-rays. It keeps the **official 624 test images** and splits the original training set 9:1 into training and validation. ResNets and AutoML tools are benchmarked on every subset.
- **Method:** ResNet-18 and ResNet-50 at 28×28 and 224×224 (upscaled) input, plus AutoML tools.
- **Dataset:** PneumoniaMNIST — 4,708 train / 524 validation / 624 test.
- **Result (PneumoniaMNIST):** ResNet-18 (28): ACC 0.854, AUC 0.944; ResNet-18 (224): ACC 0.864, AUC 0.956; ResNet-50 (224): ACC 0.884, AUC 0.962.
- **Relation:** A clean, honest ResNet baseline on the same test images, and a model for our own validation split (carved from training data).

## 2.7 An Efficient Deep Learning Approach to Pneumonia Classification in Healthcare — Stephen et al., 2019 [7]

- **Citation:** O. Stephen, M. Sain, U. J. Maduh, D.-U. Jeong, "An Efficient Deep Learning Approach to Pneumonia Classification in Healthcare," *Journal of Healthcare Engineering*, vol. 2019, art. no. 4180949, 2019. DOI: 10.1155/2019/4180949
- **Summary:** The authors designed a CNN trained from scratch rather than using transfer learning. Because pneumonia data is limited, they used heavy data augmentation (rotation up to 40°, shifts, shear, zoom). They also studied the effect of input size from 100×100 to 300×300 pixels. They rearranged the dataset into 3,722 training and 2,134 validation images.
- **Method:** Custom CNN (convolution + max-pooling feature extractor, dense sigmoid classifier).
- **Dataset:** Kermany chest X-rays (5,856 images), re-split into training and validation only.
- **Result:** Validation accuracy **93.73%** (training accuracy 95.31%).
- **Relation:** Shows a from-scratch CNN baseline; but results are on a re-split validation set, not the official test set, so they are not directly comparable to ours.

## 2.8 A Novel Transfer Learning Based Approach for Pneumonia Detection in Chest X-ray Images — Chouhan et al., 2020 [8]

- **Citation:** V. Chouhan, S. K. Singh, A. Khamparia, D. Gupta, P. Tiwari, C. Moreira, R. Damaševičius, V. H. C. de Albuquerque, "A Novel Transfer Learning Based Approach for Pneumonia Detection in Chest X-ray Images," *Applied Sciences*, vol. 10, no. 2, art. no. 559, 2020. DOI: 10.3390/app10020559
- **Summary:** The authors extracted features from chest X-rays using several neural networks pretrained on ImageNet and fed them to classifiers. They prepared five different models and compared them. An ensemble combining the outputs of all five models (majority voting, as described by Hashmi et al. [10]) outperformed every single model. The model was tested on unseen data from the Guangzhou dataset.
- **Method:** Transfer learning with five ImageNet-pretrained CNNs + ensemble.
- **Dataset:** Kermany (Guangzhou) chest X-rays; 5,232 training images.
- **Result:** Ensemble accuracy **96.4%**, recall **99.62%**.
- **Relation:** Closest published evidence that an ensemble of pretrained CNNs can exceed 95% on held-out Guangzhou test data; supports our ResNet-ensemble design.

## 2.9 Transfer Learning with Deep CNN for Pneumonia Detection Using Chest X-ray — Rahman et al., 2020 [9]

- **Citation:** T. Rahman, M. E. H. Chowdhury, A. Khandakar, K. R. Islam, K. F. Islam, Z. B. Mahbub, M. A. Kadir, S. Kashem, "Transfer Learning with Deep Convolutional Neural Network (CNN) for Pneumonia Detection Using Chest X-ray," *Applied Sciences*, vol. 10, no. 9, art. no. 3233, 2020. DOI: 10.3390/app10093233
- **Summary:** Four pretrained CNNs — AlexNet, ResNet18, DenseNet201 and SqueezeNet — were fine-tuned to detect bacterial and viral pneumonia. A total of 5,247 chest X-ray images were preprocessed for the task. Three schemes were studied: normal vs pneumonia, bacterial vs viral, and normal vs bacterial vs viral. The paper also reviews earlier pneumonia-detection work.
- **Method:** Transfer learning with four ImageNet-pretrained CNNs (including ResNet18).
- **Dataset:** 5,247 chest X-rays (bacterial, viral, normal) from the Kermany data, using the authors' own split (not the official 624-image test set).
- **Result:** Accuracy **98%** (normal vs pneumonia), **95%** (bacterial vs viral), **93.3%** (three classes).
- **Relation:** Shows ResNet18 is a common, strong choice; but its split differs from ours, so numbers are not directly comparable.

## 2.10 Efficient Pneumonia Detection in Chest X-ray Images Using Deep Transfer Learning — Hashmi et al., 2020 [10]

- **Citation:** M. F. Hashmi, S. Katiyar, A. G. Keskar, N. D. Bokde, Z. W. Geem, "Efficient Pneumonia Detection in Chest Xray Images Using Deep Transfer Learning," *Diagnostics*, vol. 10, no. 6, art. no. 417, 2020. DOI: 10.3390/diagnostics10060417
- **Summary:** Five pretrained networks — ResNet18, Xception, InceptionV3, DenseNet121 and MobileNetV2 — were fine-tuned (SGD, lr 0.001, momentum 0.9, 25 epochs). A weighted classifier combined their predictions, with weights found by differential evolution on 400 images held out from training. Only the minority (normal) class was augmented to balance the data. Class activation maps were used to show the regions behind each decision.
- **Method:** Transfer learning + weighted-average ensemble.
- **Dataset:** Kermany images shuffled and re-split into 5,136 training and 700 test images.
- **Result:** Weighted ensemble accuracy **98.43%**, AUC **99.76%** (equal weights: 97.45%). Trained on a GTX 1060 6 GB GPU.
- **Relation:** Directly inspires our ensemble-weighting on a validation split and shows 6 GB GPUs are enough. Its re-split test set is not the official one.

## 2.11 A Transfer Learning Method with Deep Residual Network for Pediatric Pneumonia Diagnosis — Liang & Zheng, 2020 [11]

- **Citation:** G. Liang, L. Zheng, "A transfer learning method with deep residual network for pediatric pneumonia diagnosis," *Computer Methods and Programs in Biomedicine*, vol. 187, art. no. 104964, 2020. DOI: 10.1016/j.cmpb.2019.06.023
- **Summary:** The authors propose a framework that combines residual structure with dilated convolution for childhood pneumonia. Residual connections fight over-fitting and the degradation problem of deep models, while dilated convolution keeps spatial information that is otherwise lost with depth. The model is initialised from parameters learned on a large dataset in the same field (transfer learning). It is designed to cope with low image resolution and partly hidden inflamed areas in children's X-rays.
- **Method:** Residual network with dilated convolutions + transfer learning.
- **Dataset:** Paediatric chest X-rays (Kermany data), test set.
- **Result:** Recall **96.7%**, F1-score **92.7%** on the test set.
- **Relation:** The closest prior work to ours: a residual network for paediatric pneumonia on the same data.

## 2.12 Pneumonia Detection in Chest X-ray Images Using an Ensemble of Deep Learning Models — Kundu et al., 2021 [12]

- **Citation:** R. Kundu, R. Das, Z. W. Geem, G.-T. Han, R. Sarkar, "Pneumonia detection in chest X-ray images using an ensemble of deep learning models," *PLoS ONE*, vol. 16, no. 9, art. no. e0256630, 2021. DOI: 10.1371/journal.pone.0256630
- **Summary:** Three pretrained CNNs — GoogLeNet, ResNet-18 and DenseNet-121 — were combined with a weighted-average ensemble. The weights were computed from each model's precision, recall, F1-score and AUC using a tanh function, instead of being set by trial and error. The method was evaluated with five-fold cross-validation on two datasets. Grad-CAM was used to analyse correct and wrong predictions.
- **Method:** Transfer learning (Adam, lr 0.0001, 30 epochs) + metric-weighted ensemble.
- **Dataset:** Kermany (5,856 images pooled, 5-fold CV) and RSNA Pneumonia Detection Challenge.
- **Result:** Accuracy **98.81%** / sensitivity 98.80% (Kermany); 86.85% / 87.02% (RSNA). ResNet-18 alone: 97.29% (Kermany).
- **Relation:** Shows ensembles of ResNet-18 with other CNNs beat single models, and a weighted average beats majority voting. Cross-validation numbers are not comparable with the official test split.

---

## 2.13 Summary table

| # | Work | Year | Model | Data / evaluation | Main result |
|---|---|---|---|---|---|
| [1] | He et al. | 2016 | ResNet (up to 152 layers) | ImageNet | 3.57% top-5 error (ensemble) |
| [2] | Kermany et al. | 2018 | Inception-V3, transfer learning | Kermany, **official test** | Acc 92.8%, Sens 93.2%, Spec 90.1%, AUC 96.8% |
| [3] | Rajpurkar et al. | 2017 | DenseNet-121 (CheXNet) | ChestX-ray14 (adults) | F1 above average radiologist |
| [4] | Selvaraju et al. | 2017 | Grad-CAM | ImageNet, VQA, captioning | Class-discriminative heat maps |
| [5] | Lim et al. | 2003 | CURB-65 score | 1,068 adults with CAP | Mortality 1.5% / 9.2% / 22% by group |
| [6] | Yang et al. | 2023 | ResNet-18/50 | PneumoniaMNIST, **official test** | ResNet-50 (224): ACC 88.4%, AUC 0.962 |
| [7] | Stephen et al. | 2019 | CNN from scratch | Re-split, validation | Val acc 93.73% |
| [8] | Chouhan et al. | 2020 | 5-CNN ensemble | Guangzhou unseen test data | Acc 96.4%, recall 99.62% |
| [9] | Rahman et al. | 2020 | AlexNet/ResNet18/DenseNet201/SqueezeNet | Own split, 5,247 images | Acc 98% (normal vs pneumonia) |
| [10] | Hashmi et al. | 2020 | Weighted 5-CNN ensemble | Re-split (700 test) | Acc 98.43%, AUC 99.76% |
| [11] | Liang & Zheng | 2020 | Residual + dilated conv | Kermany test set | Recall 96.7%, F1 92.7% |
| [12] | Kundu et al. | 2021 | GoogLeNet + ResNet-18 + DenseNet-121 | 5-fold CV | Acc 98.81% |

**Research gap (for the report):** Most high-accuracy results use re-split data or cross-validation, so they do not show how a model behaves on the official, independent test set. Several papers also tune on the test data. Few works combine a ResNet ensemble, an honest validation-only threshold, visual explanation (Grad-CAM) and clinical tools (CURB-65, triage) in one offline application for doctors and patients. PneumoScan AI addresses this gap.

An additional reference used in the report's Limitations section:
- Zech et al. 2018 [13] showed that pneumonia-screening CNNs trained at one hospital system performed worse at an external hospital (internal AUC 0.931 vs external 0.815) and could recognise which hospital an image came from (99.95% of NIH images).

---

## References (IEEE style)

[1] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Las Vegas, NV, USA, 2016, pp. 770–778, doi: 10.1109/CVPR.2016.90.

[2] D. S. Kermany *et al.*, "Identifying medical diagnoses and treatable diseases by image-based deep learning," *Cell*, vol. 172, no. 5, pp. 1122–1131.e9, Feb. 2018, doi: 10.1016/j.cell.2018.02.010.

[3] P. Rajpurkar *et al.*, "CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning," arXiv:1711.05225, 2017. [Online]. Available: https://arxiv.org/abs/1711.05225

[4] R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, "Grad-CAM: Visual explanations from deep networks via gradient-based localization," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, Venice, Italy, 2017, pp. 618–626, doi: 10.1109/ICCV.2017.74.

[5] W. S. Lim *et al.*, "Defining community acquired pneumonia severity on presentation to hospital: An international derivation and validation study," *Thorax*, vol. 58, no. 5, pp. 377–382, May 2003, doi: 10.1136/thorax.58.5.377.

[6] J. Yang *et al.*, "MedMNIST v2 – A large-scale lightweight benchmark for 2D and 3D biomedical image classification," *Sci. Data*, vol. 10, no. 1, Art. no. 41, Jan. 2023, doi: 10.1038/s41597-022-01721-8.

[7] O. Stephen, M. Sain, U. J. Maduh, and D.-U. Jeong, "An efficient deep learning approach to pneumonia classification in healthcare," *J. Healthc. Eng.*, vol. 2019, Art. no. 4180949, Mar. 2019, doi: 10.1155/2019/4180949.

[8] V. Chouhan *et al.*, "A novel transfer learning based approach for pneumonia detection in chest X-ray images," *Appl. Sci.*, vol. 10, no. 2, Art. no. 559, Jan. 2020, doi: 10.3390/app10020559.

[9] T. Rahman *et al.*, "Transfer learning with deep convolutional neural network (CNN) for pneumonia detection using chest X-ray," *Appl. Sci.*, vol. 10, no. 9, Art. no. 3233, May 2020, doi: 10.3390/app10093233.

[10] M. F. Hashmi, S. Katiyar, A. G. Keskar, N. D. Bokde, and Z. W. Geem, "Efficient pneumonia detection in chest X-ray images using deep transfer learning," *Diagnostics*, vol. 10, no. 6, Art. no. 417, Jun. 2020, doi: 10.3390/diagnostics10060417.

[11] G. Liang and L. Zheng, "A transfer learning method with deep residual network for pediatric pneumonia diagnosis," *Comput. Methods Programs Biomed.*, vol. 187, Art. no. 104964, Apr. 2020, doi: 10.1016/j.cmpb.2019.06.023.

[12] R. Kundu, R. Das, Z. W. Geem, G.-T. Han, and R. Sarkar, "Pneumonia detection in chest X-ray images using an ensemble of deep learning models," *PLoS ONE*, vol. 16, no. 9, Art. no. e0256630, Sep. 2021, doi: 10.1371/journal.pone.0256630.

[13] J. R. Zech, M. A. Badgeley, M. Liu, A. B. Costa, J. J. Titano, and E. K. Oermann, "Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study," *PLoS Med.*, vol. 15, no. 11, Art. no. e1002683, Nov. 2018, doi: 10.1371/journal.pmed.1002683.

**Other sources the report may cite** (used in `medical_content.md` and `report_text.md`):

[14] World Health Organization, "Pneumonia," Fact sheet, Nov. 11, 2022. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/pneumonia

[15] World Health Organization, "The top 10 causes of death," Fact sheet, Oct. 2, 2026. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/the-top-10-causes-of-death

[16] A. Chandramohan *et al.*, "Teleradiology and technology innovations in radiology: status in India and its role in increasing access to primary health care," *Lancet Reg. Health Southeast Asia*, vol. 23, Art. no. 100195, Apr. 2024, doi: 10.1016/j.lansea.2023.100195.

[17] D. Kermany, "Labeled optical coherence tomography (OCT) and chest X-ray images for classification," Mendeley Data, v2, 2018, doi: 10.17632/rscbjbr9sj.2.

[18] M. Chumbita *et al.*, "Can artificial intelligence improve the management of pneumonia," *J. Clin. Med.*, vol. 9, no. 1, Jan. 2020. [Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/
