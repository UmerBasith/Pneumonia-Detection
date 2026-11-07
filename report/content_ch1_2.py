"""Chapter 1 (Introduction) and Chapter 2 (Literature Survey)."""


def ch1():
    return [
        ("section", "main"),
        ("chapter", 1, "Introduction"),
        ("h2", "1.1 Background"),
        ("p", "Pneumonia is a form of acute respiratory infection in which the alveoli (the tiny air sacs of the lungs) "
              "fill with pus and fluid, making breathing painful and reducing the amount of oxygen the body can take "
              "in [14]. It can be caused by viruses, bacteria or fungi [14]. In children, ^^Streptococcus pneumoniae^^ "
              "is the most common bacterial cause and respiratory syncytial virus the most common viral cause [14]. "
              "Children younger than five years and adults aged 65 years or older are at increased risk, and people "
              "with a weakened immune system are at the greatest risk [19]."),
        ("p", "The disease burden is very large. Pneumonia caused 740,180 deaths of children under five in 2019, "
              "which is 14% of all deaths in that age group [14]. Across all ages, lower respiratory infections "
              "caused 2.7 million deaths in 2023, were the fourth leading cause of death worldwide and have remained "
              "the leading cause of death in low-income countries since around 2010 [15]. Pneumonia can be prevented "
              "by immunisation, adequate nutrition and cleaner indoor air, and pneumonia caused by bacteria can be "
              "treated with antibiotics [14], so early and correct diagnosis matters."),
        ("h2", "1.2 Role of the Chest X-ray"),
        ("p", "A doctor diagnoses pneumonia from the history, the physical examination (temperature, breathing rate, "
              "listening to the chest) and investigations. The chest X-ray (radiograph) is the most frequently used "
              "imaging test to confirm pneumonia [12]. On a frontal chest X-ray, pneumonia typically appears as "
              "**consolidation**: a white (opaque) area where the air in the alveoli has been replaced by fluid or "
              "pus. The World Health Organization standard for reading children’s chest radiographs counts alveolar "
              "consolidation or pleural effusion as the primary end-point for pneumonia [20]. Other signs include air "
              "bronchograms inside the opacity and loss of the normal sharp borders of the heart or diaphragm."),
        ("p", "Reading radiographs correctly needs training and experience, and different readers can disagree, "
              "especially for subtle or patchy changes in children [12], [20]. An X-ray also cannot tell which germ "
              "caused the infection, so it is always interpreted together with the clinical picture."),
        ("h2", "1.3 Deep Learning for Medical Images"),
        ("p", "Deep learning is a branch of machine learning in which a neural network with many layers learns useful "
              "features directly from raw data. Convolutional neural networks (CNNs) learn small filters that detect "
              "edges and textures in the first layers and progressively more complex patterns in deeper layers, which "
              "makes them very effective for image classification. CheXNet, a 121-layer CNN trained on more than "
              "100,000 adult chest X-rays, exceeded the average performance of four radiologists (F1 metric) for "
              "pneumonia detection [3]. Kermany et al. showed that **transfer learning**, which starts from a network "
              "pretrained on a large collection of everyday photographs (ImageNet) and adapts it to medical images, "
              "can produce an accurate paediatric pneumonia classifier with a fraction of the data normally "
              "required [2]."),
        ("h2", "1.4 Residual Networks (ResNet)"),
        ("p", "Very deep networks are hard to train: beyond a certain depth, adding more layers makes the training "
              "accuracy saturate and then degrade. He et al. [1] solved this **degradation problem** with residual "
              "learning. Instead of asking a stack of layers to learn a desired mapping H(x) directly, a residual block "
              "learns the residual F(x) = H(x) − x and adds the input back through an identity **shortcut "
              "connection**, so that the block outputs F(x) + x. The shortcut gives gradients a direct path through "
              "the network, which made it possible to train networks with up to 152 layers; an ensemble of residual "
              "networks won the ILSVRC 2015 classification task with a 3.57% top-5 error [1]. ResNets are now one of "
              "the most widely used backbones for transfer learning in medical imaging, and they are the backbone of "
              "this project. They are explained in detail in Chapter 5."),
        ("h2", "1.5 Problem Statement"),
        ("p", "Manual interpretation of chest X-rays for pneumonia is time-consuming, depends on the availability of "
              "trained radiologists, and is subject to variation between readers [12]. In India there are only about "
              "20,500 registered radiologists, roughly one per 100,000 people [16]. There is a need for an accurate, "
              "explainable and easy-to-use automated system that can analyse a chest X-ray, indicate the likelihood "
              "of pneumonia, highlight the regions that influenced the decision and help to prioritise patients, "
              "while making clear that the final decision rests with a qualified doctor."),
        ("h2", "1.6 Objectives"),
        ("bullets", [
            "To build a deep-learning classifier based on the ResNet architecture that labels a frontal chest X-ray as "
            "NORMAL or PNEUMONIA.",
            "To reach a target accuracy of at least 95% on the official held-out test set of 624 images, and to report "
            "sensitivity, specificity, precision, F1-score and ROC-AUC honestly, whatever the outcome.",
            "To avoid any tuning on the test set by selecting every setting (epochs, ensemble, calibration and decision "
            "threshold) on a validation split drawn only from the training data.",
            "To provide a visual explanation of each prediction using Grad-CAM heat maps.",
            "To reject input images that are not chest X-rays.",
            "To develop an offline web application with single-image scanning, batch triage, patient PDF reports, "
            "scan history and a CURB-65 severity calculator.",
            "To present reliable, sourced health information about pneumonia for patients and families.",
        ]),
        ("h2", "1.7 Scope"),
        ("bullets", [
            "**Input:** frontal chest X-ray images in JPG, PNG, BMP, WEBP, TIFF or DICOM format.",
            "**Output:** a two-class prediction (NORMAL / PNEUMONIA), a calibrated probability, a risk level "
            "(Low / Moderate / High), a Grad-CAM heat map and a downloadable PDF report.",
            "**Data:** the public paediatric chest X-ray dataset of Kermany et al. (children aged 1–5 years from one "
            "hospital in Guangzhou, China) [2], [17].",
            "**Users:** medical students (learning), doctors (second reader and triage aid) and patients (education).",
            "**Out of scope:** identifying the cause (bacterial or viral), detecting other lung diseases, validation "
            "on adults, and any use as a certified medical device.",
        ]),
        ("h2", "1.8 Motivation"),
        ("bullets", [
            "**Shortage of radiologists in India:** about one radiologist per 100,000 population compared with one per "
            "10,000 in the United States; most radiologists work in larger cities and towns, while about sixty percent "
            "of the population lives in rural areas [16].",
            "**High burden of disease:** pneumonia caused 740,180 deaths of children under five in 2019 [14], and lower "
            "respiratory infections were the fourth leading cause of death worldwide in 2023 [15].",
            "**Evidence that AI can help:** a deep CNN exceeded average radiologist performance (F1) for pneumonia "
            "detection [3], and a review of Indian radiology found that teleradiology combined with AI and mobile "
            "digital imaging can address radiologist shortages [16].",
            "**Need for honest and explainable tools:** many published results use re-split data, which may overstate "
            "accuracy on independent data (Chapter 2), and pneumonia models can perform worse at new hospitals [13]. "
            "A transparent tool with heat maps and honestly reported test results supports appropriate trust.",
        ]),
        ("h2", "1.9 Organisation of the Report"),
        ("p", "The rest of this report is organised as follows. **Chapter 2** reviews related work on ResNets, "
              "pneumonia detection and explainability, and identifies the research gap. **Chapter 3** analyses the "
              "existing and proposed systems, lists the requirements and presents the system architecture, use-case "
              "diagram, data flow and modules. **Chapter 4** describes the dataset, the patient-level split, "
              "pre-processing, augmentation and leakage checks. **Chapter 5** explains the ResNet architecture and "
              "the complete methodology, including training, ensembling, calibration, threshold selection, Grad-CAM "
              "and the X-ray gate. **Chapter 6** presents the implementation with key code listings. **Chapter 7** "
              "reports and discusses the results. **Chapter 8** walks through the application with screenshots. "
              "**Chapter 9** concludes the report with limitations, future enhancements and social impact. The "
              "complete source code of the machine-learning pipeline and backend is given in **Appendix A**, and "
              "instructions to run the project are in **Appendix B**."),
    ]


def ch2():
    lit = [
        ("2.2 Deep Residual Learning for Image Recognition (He et al., 2016) [1]",
         "He et al. observed that very deep plain networks suffer from a degradation problem: accuracy saturates and "
         "then falls as layers are added, even on the training set. They reformulated layers to learn residual "
         "functions with reference to the layer input, using identity shortcut connections, batch normalisation and "
         "global average pooling, with two 3 × 3 convolutions per block in shallower models and 1 × 1–3 × 3–1 × 1 "
         "“bottleneck” blocks in deeper ones. Networks up to 152 layers (eight times deeper than VGG nets, but with "
         "lower complexity) were trained on ImageNet; an ensemble reached a **3.57% top-5 error** and won first place "
         "in ILSVRC 2015, with a 28% relative improvement on COCO object detection. **Relation:** ResNet is the "
         "backbone of PneumoScan AI, which fine-tunes ImageNet-pretrained ResNet-34 and ResNet-50 models."),
        ("2.3 Identifying Medical Diagnoses by Image-Based Deep Learning (Kermany et al., 2018) [2]",
         "The authors built a transfer-learning diagnostic tool, first for retinal OCT images and then for paediatric "
         "chest X-rays, by fine-tuning an ImageNet-pretrained Inception-V3. Transfer learning allowed a network "
         "trained on general images to be adapted with a fraction of the usual data, and image regions used by the "
         "network were highlighted to improve interpretability. The chest X-ray data (5,232 training images: 1,349 "
         "normal and 3,883 pneumonia; and an independent 624-image test set) come from Guangzhou Women and Children’s "
         "Medical Center. For pneumonia versus normal they reported **accuracy 92.8%, sensitivity 93.2%, specificity "
         "90.1% and AUC 96.8%** (as quoted in the review by Chumbita et al. [18]). **Relation:** this is the dataset "
         "used in this project and the main baseline on the same official test set."),
        ("2.4 CheXNet: Radiologist-Level Pneumonia Detection (Rajpurkar et al., 2017) [3]",
         "CheXNet is a 121-layer DenseNet trained end-to-end on ChestX-ray14, a set of more than 100,000 frontal adult "
         "chest X-rays with 14 disease labels. Four practising academic radiologists labelled a test set so that the "
         "model could be compared with human readers, and CheXNet **exceeded the average radiologist on the F1 "
         "metric** for pneumonia; it was then extended to all 14 diseases. **Relation:** it shows that deep CNNs can "
         "approach expert reading of chest X-rays and motivates the CNN approach used here."),
        ("2.5 Grad-CAM: Visual Explanations from Deep Networks (Selvaraju et al., 2017) [4]",
         "Grad-CAM produces class-discriminative visual explanations for CNN decisions. It uses the gradients of the "
         "target class score flowing into the final convolutional layer to weight its feature maps and build a coarse "
         "heat map of the regions that matter for the prediction. It works with many CNN families, including ResNets, "
         "without changing or retraining the model. Human studies showed that Grad-CAM helps users build appropriate "
         "trust and can reveal dataset bias. **Relation:** PneumoScan AI shows a Grad-CAM heat map for every X-ray so "
         "that a doctor can check whether the model looks at the lungs."),
        ("2.6 Defining Pneumonia Severity: the CURB-65 Score (Lim et al., 2003) [5]",
         "The authors pooled three prospective studies from the UK, New Zealand and the Netherlands (1,068 adults with "
         "community-acquired pneumonia, 30-day mortality 9%) to build a simple severity score. One point each for "
         "Confusion, Urea > 7 mmol/L, Respiratory rate ≥ 30/min, low Blood pressure (systolic < 90 or diastolic "
         "≤ 60 mmHg) and age ≥ 65 gives the six-point CURB-65 score. In the derivation cohort, 30-day mortality was "
         "**1.5%** for scores 0–1, **9.2%** for score 2 and **22%** for scores 3–5. A version without urea (CRB-65) "
         "was proposed for use in the community. **Relation:** the application includes a CURB-65 calculator so that "
         "a doctor can combine the X-ray result with a standard clinical severity score."),
        ("2.7 MedMNIST v2 (Yang et al., 2023) [6]",
         "MedMNIST v2 is a collection of standardised 2D and 3D biomedical datasets for benchmarking. Its "
         "PneumoniaMNIST subset is built from the Kermany chest X-rays, **keeps the official 624 test images** and "
         "splits the original training set 9:1 into training and validation. ResNet baselines on the official test "
         "set reached ACC 0.854 / AUC 0.944 (ResNet-18, 28 px), ACC 0.864 / AUC 0.956 (ResNet-18, 224 px) and "
         "**ACC 0.884 / AUC 0.962 (ResNet-50, 224 px)**. **Relation:** a clean, honest ResNet baseline on the same "
         "test images, and a model for carving the validation split from the training data."),
        ("2.8 An Efficient Deep Learning Approach to Pneumonia Classification (Stephen et al., 2019) [7]",
         "The authors designed a CNN trained from scratch and, because the data are limited, used heavy augmentation "
         "(rotation up to 40°, shifts, shear and zoom) and studied input sizes from 100 × 100 to 300 × 300 pixels. "
         "The Kermany images were rearranged into 3,722 training and 2,134 validation images, giving a **validation "
         "accuracy of 93.73%**. **Relation:** a from-scratch baseline; its result is on a re-split validation set, "
         "not the official test set, so it is not directly comparable."),
        ("2.9 A Novel Transfer Learning Based Approach for Pneumonia Detection (Chouhan et al., 2020) [8]",
         "Features were extracted with five ImageNet-pretrained networks and their outputs were combined by majority "
         "voting. The ensemble outperformed every single model and reached **accuracy 96.4% and recall 99.62%** on "
         "unseen test data from the Guangzhou dataset, after training on the 5,232 training images. **Relation:** the "
         "closest published evidence that an ensemble of pretrained CNNs can exceed 95% on held-out Guangzhou test "
         "data; it supports the ResNet-ensemble design of this project."),
        ("2.10 Transfer Learning with Deep CNN for Pneumonia Detection (Rahman et al., 2020) [9]",
         "AlexNet, ResNet-18, DenseNet-201 and SqueezeNet were fine-tuned on 5,247 chest X-rays for three schemes: "
         "normal versus pneumonia, bacterial versus viral, and three classes. Reported accuracies were **98%**, 95% "
         "and 93.3% respectively, using the authors’ own split rather than the official 624-image test set. "
         "**Relation:** it shows that ResNet-18 is a common, strong choice, but the numbers are not directly "
         "comparable with ours."),
        ("2.11 Efficient Pneumonia Detection using Deep Transfer Learning (Hashmi et al., 2020) [10]",
         "Five pretrained networks (ResNet-18, Xception, Inception-V3, DenseNet-121 and MobileNetV2) were fine-tuned "
         "(SGD, learning rate 0.001, momentum 0.9, 25 epochs) and combined by a weighted classifier whose weights were "
         "found on 400 images held out from training. Only the minority (normal) class was augmented, and class "
         "activation maps showed the regions behind each decision. The images were shuffled and re-split into 5,136 "
         "training and 700 test images, giving **98.43% accuracy and 99.76% AUC** (97.45% with equal weights) on a "
         "6 GB GTX 1060 GPU. **Relation:** it inspired the idea of fitting ensemble settings on held-out training "
         "data and shows that a 6 GB GPU is sufficient; its test set is not the official one."),
        ("2.12 A Transfer Learning Method with Deep Residual Network for Pediatric Pneumonia (Liang & Zheng, 2020) [11]",
         "This framework combines residual connections with dilated convolutions for childhood pneumonia. Residual "
         "connections counter over-fitting and the degradation problem, dilated convolutions keep spatial information "
         "that is otherwise lost with depth, and the model is initialised by transfer learning. On the test set it "
         "reached **recall 96.7% and F1-score 92.7%**. **Relation:** the closest prior work, a residual network for "
         "paediatric pneumonia on the same data."),
        ("2.13 Pneumonia Detection using an Ensemble of Deep Learning Models (Kundu et al., 2021) [12]",
         "GoogLeNet, ResNet-18 and DenseNet-121 were combined with a weighted-average ensemble whose weights are "
         "computed from each model’s precision, recall, F1-score and AUC. With five-fold cross-validation, it reached "
         "**98.81% accuracy** on the pooled Kermany data (ResNet-18 alone 97.29%) and 86.85% on the RSNA pneumonia "
         "dataset; Grad-CAM was used to analyse correct and wrong predictions. **Relation:** ensembles beat single "
         "models, but cross-validation numbers are not comparable with the official test split."),
        ("2.14 Variable Generalisation of Pneumonia Models (Zech et al., 2018) [13]",
         "Zech et al. trained pneumonia-screening CNNs on chest X-rays from several hospital systems and showed that "
         "performance dropped on an external hospital (**internal AUC 0.931 versus external 0.815**). The CNNs could "
         "even recognise which hospital an image came from (for example 99.95% of NIH images), which means they can "
         "learn hospital-specific shortcuts. **Relation:** this motivates the limitations, the Grad-CAM inspection "
         "and the clear disclaimer in this project."),
    ]
    blocks = [
        ("chapter", 2, "Literature Survey"),
        ("h2", "2.1 Introduction"),
        ("p", "This chapter reviews the work that this project builds on: the ResNet architecture, transfer learning "
              "for chest X-rays, ensembles of CNNs, explainability with Grad-CAM, generalisation across hospitals and "
              "the CURB-65 clinical score. Every paper was checked against PubMed, Crossref, arXiv or the open-access "
              "full text. An important observation is that several papers report very high accuracy (97–99%) on the "
              "Kermany data, but they **re-split** the images or used cross-validation instead of the official "
              "624-image test set. Such numbers are not directly comparable with results on the official test set, "
              "and this is pointed out for each paper."),
    ]
    for head, text in lit:
        blocks += [("h3", head), ("p", text)]
    blocks += [
        ("h2", "2.15 Summary of the Literature"),
        ("p", "{tab:lit} summarises the reviewed works. Results marked “official test” use the same 624 test images "
              "as this project; the others use different evaluation data and are listed for context only."),
        ("tab", "lit", "Summary of the literature survey",
         ["Ref.", "Authors (year)", "Model / method", "Data / evaluation", "Main result"],
         [
             ["[1]", "He et al. (2016)", "ResNet, up to 152 layers", "ImageNet", "3.57% top-5 error (ensemble)"],
             ["[2]", "Kermany et al. (2018)", "Inception-V3, transfer learning", "Kermany, official test",
              "Acc 92.8%, Sens 93.2%, Spec 90.1%, AUC 96.8%"],
             ["[3]", "Rajpurkar et al. (2017)", "DenseNet-121 (CheXNet)", "ChestX-ray14 (adults)",
              "F1 above average radiologist"],
             ["[4]", "Selvaraju et al. (2017)", "Grad-CAM", "ImageNet, VQA, captioning", "Class-discriminative heat maps"],
             ["[5]", "Lim et al. (2003)", "CURB-65 score", "1,068 adults with CAP", "Mortality 1.5% / 9.2% / 22% by group"],
             ["[6]", "Yang et al. (2023)", "ResNet-18 / ResNet-50", "PneumoniaMNIST, official test",
              "ResNet-50 (224): Acc 88.4%, AUC 0.962"],
             ["[7]", "Stephen et al. (2019)", "CNN from scratch", "Re-split, validation", "Val acc 93.73%"],
             ["[8]", "Chouhan et al. (2020)", "5-CNN ensemble (voting)", "Guangzhou unseen test data",
              "Acc 96.4%, recall 99.62%"],
             ["[9]", "Rahman et al. (2020)", "AlexNet / ResNet-18 / DenseNet-201 / SqueezeNet", "Own split, 5,247 images",
              "Acc 98% (normal vs pneumonia)"],
             ["[10]", "Hashmi et al. (2020)", "Weighted 5-CNN ensemble", "Re-split (700 test)", "Acc 98.43%, AUC 99.76%"],
             ["[11]", "Liang & Zheng (2020)", "Residual + dilated convolution", "Kermany test set", "Recall 96.7%, F1 92.7%"],
             ["[12]", "Kundu et al. (2021)", "GoogLeNet + ResNet-18 + DenseNet-121", "5-fold cross-validation",
              "Acc 98.81%"],
             ["[13]", "Zech et al. (2018)", "CNN, multi-hospital", "Internal vs external hospitals",
              "AUC 0.931 internal vs 0.815 external"],
         ], [0.45, 1.15, 1.55, 1.4, 1.45], {"size": 9.5, "align": ["C", "L", "L", "L", "L"]}),
        ("h2", "2.16 Research Gap"),
        ("p", "From the survey, the following gaps are identified:"),
        ("bullets", [
            "Most high-accuracy results use re-split data or cross-validation, so they do not show how a model behaves "
            "on the official, independent test set, which is known to be harder [2], [6].",
            "On the official test set, reported errors are dominated by normal X-rays called pneumonia (for example "
            "Kermany et al. report a specificity of 90.1% against a sensitivity of 93.2% [2]), which makes the choice "
            "of decision threshold critical; yet thresholds and model selection are rarely fixed on a separate "
            "validation split.",
            "Models can learn hospital-specific shortcuts and generalise poorly [13], so visual explanations and honest "
            "limitations are essential.",
            "Few works combine a ResNet ensemble, a validation-only threshold, Grad-CAM explanations, rejection of "
            "non-X-ray inputs and clinical tools (CURB-65, triage, patient reports) in one offline application for "
            "doctors and patients.",
        ]),
        ("p", "PneumoScan AI addresses these gaps with a patient-level validation split, a three-member ResNet ensemble "
              "whose every setting is chosen on validation, a single logged evaluation on the official test set, "
              "Grad-CAM explanations, an out-of-distribution X-ray gate and a complete offline application."),
    ]
    return blocks
