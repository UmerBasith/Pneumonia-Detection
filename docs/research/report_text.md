# Draft report text — PneumoScan AI: Pneumonia Detection using ResNet

Written by the Research agent for the Report writer. Formal academic English. Citation numbers [n] match the IEEE reference list in `literature_survey.md` (add [19] below to that list). Replace `[ACC]`, `[SENS]`, `[SPEC]`, `[AUC]` with the final numbers from `models/metrics.json`. Items marked **[check with ML agent]** depend on the final build.

Extra reference to add:
[19] Centers for Disease Control and Prevention, "Risk factors for pneumonia," Feb. 25, 2026. [Online]. Available: https://www.cdc.gov/pneumonia/risk-factors/index.html

---

## Abstract

Pneumonia is an infection of the lungs and a leading cause of death in young children; the World Health Organization reports 740,180 deaths of children under five in 2019 [14]. Chest X-ray imaging is the most frequently used method for diagnosing pneumonia [12], but reading X-rays needs trained radiologists, who are scarce in India [16]. This project presents PneumoScan AI, a decision-support system that classifies chest X-ray images as NORMAL or PNEUMONIA using deep residual networks (ResNet) [1]. ImageNet-pretrained ResNet models are fine-tuned with transfer learning on the publicly available paediatric chest X-ray dataset of Kermany et al. [2], [17], using class-balanced training, data augmentation and an ensemble of ResNets. The decision threshold is selected on a validation split taken from the training data, and the model is evaluated once on the official independent test set of 624 images. The system achieves an accuracy of [ACC], a sensitivity of [SENS], a specificity of [SPEC] and a ROC-AUC of [AUC]. To support trust, Grad-CAM heat maps [4] show the image regions that influenced each prediction. The model is delivered through an offline web application with patient PDF reports, a batch triage queue for doctors and a CURB-65 severity calculator [5]. The tool is intended for education and decision support only and does not replace a qualified doctor.

## 1. Introduction

Pneumonia is a form of acute respiratory infection in which the alveoli of the lungs fill with pus and fluid, making breathing painful and reducing oxygen intake [14]. It can be caused by viruses, bacteria or fungi [14]. Children younger than five years and adults aged 65 years or older are at increased risk, and people with a weakened immune system are at the greatest risk [19]. Globally, lower respiratory infections caused 2.7 million deaths in 2023 and have remained the leading cause of death in low-income countries since around 2010 [15]. Among children under five, pneumonia accounted for 14% of all deaths in 2019 [14].

A chest X-ray is commonly used to confirm pneumonia. However, interpreting a radiograph requires expertise, and radiologists are concentrated in larger cities and towns [16]. Deep learning, in particular convolutional neural networks (CNNs), has shown strong performance in image classification. Residual networks (ResNets) introduced identity shortcut connections that allow very deep networks to be trained effectively [1], and transfer learning allows networks pretrained on large natural-image datasets to be adapted to medical images with a fraction of the data [2].

This project, PneumoScan AI, applies ResNet-based transfer learning to classify paediatric chest X-rays as normal or pneumonia, explains each decision with Grad-CAM [4], and wraps the model in an easy-to-use offline application for patients, students and doctors.

## 2. Problem Statement

Manual interpretation of chest X-rays for pneumonia is time-consuming, depends on the availability of trained radiologists, and is subject to variation between readers [12]. In India there are only about 20,500 registered radiologists, roughly one per 100,000 people [16]. There is a need for an accurate, explainable and easy-to-use automated system that can analyse a chest X-ray, indicate the likelihood of pneumonia, highlight the regions that influenced the decision, and help prioritise patients, while making clear that the final decision rests with a qualified doctor.

## 3. Objectives

- To build a deep-learning classifier based on the ResNet architecture that labels a chest X-ray as NORMAL or PNEUMONIA.
- To reach a target accuracy of at least 95% on the official held-out test set of 624 images, and to report sensitivity, specificity, precision, F1-score and ROC-AUC honestly.
- To avoid any tuning on the test set by selecting the decision threshold and model settings on a validation split drawn only from the training data.
- To provide visual explanations of each prediction using Grad-CAM heat maps.
- To reject input images that are not chest X-rays.
- To develop an offline web application with single-image scanning, batch triage, patient PDF reports, scan history and a CURB-65 severity calculator.
- To present reliable, sourced health information about pneumonia for patients and families.

## 4. Scope

- Input: frontal chest X-ray images in JPG, PNG or DICOM format.
- Output: a two-class prediction (NORMAL / PNEUMONIA), a probability, a risk level, a Grad-CAM heat map and a downloadable report.
- Data: the public paediatric chest X-ray dataset of Kermany et al. (children aged 1–5 years from one hospital in Guangzhou, China) [2], [17].
- Users: medical students, doctors (as a second reader and triage aid) and patients (for education).
- Out of scope: identifying the cause (bacterial vs viral), detecting other lung diseases, validation on adults, and any use as a certified medical device.

## 5. Motivation

- Shortage of radiologists in India: about 20,500 radiologists are registered with the Indian Society of Radiology and Imaging, about one per 100,000 population compared with one per 10,000 in the United States [16]. Most radiologists work in larger cities and towns, while about sixty percent of the population lives in rural areas [16].
- High burden of disease: pneumonia caused 740,180 deaths of children under five in 2019 [14], and lower respiratory infections were the fourth leading cause of death worldwide in 2023 [15].
- Evidence that AI can help: a deep CNN exceeded average radiologist performance (F1) for pneumonia detection on chest X-rays [3], and a review of Indian radiology found that teleradiology combined with AI and mobile digital imaging units can address radiologist shortages [16].
- Need for honest and explainable tools: many published results use re-split data, which may overstate accuracy on independent data (Chapter 2), and pneumonia models can perform worse at new hospitals [13]. A transparent tool with heat maps and honestly reported test results supports appropriate trust.

## 6. Proposed System — Overview

1. Pre-processing: the X-ray is converted to grayscale, resized to the network input size (224 × 224 pixels) [check with ML agent], replicated to three channels and normalised with ImageNet statistics. An image check rejects inputs that are not chest X-rays.
2. Classification model: ImageNet-pretrained ResNet models [1] are fine-tuned on the training images using class-balanced loss and data augmentation. The probabilities of the ensemble members are averaged, calibrated on the validation split, and compared with a threshold chosen on the validation split [check with ML agent: final members and threshold].
3. Explainability: Grad-CAM [4] is applied to the last convolutional block of the ResNet to produce a heat map overlaid on the X-ray.
4. Application: a FastAPI back-end and React front-end run entirely offline, offering single-image scanning, a batch triage queue sorted by pneumonia probability with CSV export, patient PDF reports with a disclaimer, local scan history, a CURB-65 calculator [5], a Learn page with sourced health information, and a Model page showing accuracy, sensitivity, specificity, ROC-AUC, the confusion matrix and training curves.

Dataset split: the official training images are divided into stratified training and validation subsets; the official test set of 624 images (234 normal, 390 pneumonia) is used only once, for the final evaluation.

## 7. Advantages

- Quick analysis of a chest X-ray on an ordinary laptop, with or without a GPU.
- Uses ResNet, an architecture whose residual connections make deep networks easier to optimise [1].
- Transfer learning reduces the labelled data needed [2].
- Grad-CAM heat maps make decisions more transparent and can reveal dataset bias [4].
- Honest evaluation: threshold and settings are chosen on validation data, never on the test set.
- Batch triage helps doctors review the most likely pneumonia cases first.
- Works fully offline, protecting patient privacy and suiting places with poor internet.
- Combines image analysis with a standard clinical severity score (CURB-65) [5] and patient education.

## 8. Limitations

- The model was trained and tested on paediatric X-rays (ages 1–5) from a single hospital; it may perform worse on adults, other hospitals or other X-ray machines. Pneumonia-screening CNNs have been shown to perform worse on data from external hospitals (AUC 0.931 internal vs 0.815 external) [13].
- It detects only two classes and cannot identify the cause of pneumonia or other lung diseases.
- A chest X-ray alone is not enough for diagnosis; symptoms, examination and other tests are needed.
- Grad-CAM heat maps are coarse; they show where the model looked, not proof of disease [4].
- Dataset labels come from clinical grading by physicians and may contain some errors.
- The system is a student project and is not a certified medical device.

## 9. Future Enhancements

- Train and validate on larger, multi-centre and adult datasets, including data from Indian hospitals.
- Extend to multi-class classification (bacterial vs viral pneumonia and other chest findings).
- Add lung segmentation so the model focuses only on the lung fields.
- Evaluate the system prospectively alongside radiologists.
- Integrate with hospital PACS and national teleconsultation services.
- Build a lightweight mobile version for primary health centres.
- Support regional Indian languages in the patient interface.

## 10. Social Impact

PneumoScan AI shows how artificial intelligence can support, not replace, doctors where radiologists are few. A quick, explainable second opinion on a chest X-ray could help health workers decide which patients need urgent referral and help busy hospitals prioritise their reporting queues. Because the system runs offline on a normal computer, it can be used where internet access is unreliable. The Learn page and patient report give families clear, trustworthy information on danger signs and prevention, including immunisation against Hib, pneumococcus, measles and whooping cough, cleaner indoor air and exclusive breastfeeding for the first six months, which the World Health Organization identifies as key ways to protect children from pneumonia [14]. By reporting results honestly and showing a clear disclaimer, the project also promotes responsible use of AI in healthcare.
