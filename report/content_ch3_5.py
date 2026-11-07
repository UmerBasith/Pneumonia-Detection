"""Chapter 3 (System Analysis & Design), Chapter 4 (Dataset), Chapter 5 (Architecture & Methodology)."""
from paths import FIG, RFIG
from docx_engine import mbar, mfrac, mnary, mp, mparen, mrad, msub, msubsup, msup, mt


def ch3():
    return [
        ("chapter", 3, "System Analysis and Design"),
        ("h2", "3.1 Existing System"),
        ("p", "In current practice a chest X-ray is read manually by a radiologist or by the treating doctor. This "
              "works well where specialists are available, but it has several drawbacks:"),
        ("bullets", [
            "Reporting depends on the availability of trained radiologists, who are few and concentrated in cities [16].",
            "Films are usually read in the order in which they arrive; a severe case may wait behind routine ones.",
            "Interpretation varies between readers, especially for subtle or patchy changes in children [12], [20].",
            "Most published deep-learning models are research prototypes: they are evaluated on re-split data, often "
            "tuned on the test set, give no explanation for their output, accept any image (even a photograph) and "
            "are not packaged as a tool that a doctor or student can actually use.",
        ]),
        ("h2", "3.2 Proposed System"),
        ("p", "PneumoScan AI is an offline decision-support application that analyses a chest X-ray with an ensemble "
              "of ResNets and explains its output. Its main parts are:"),
        ("numbered", [
            "**Pre-processing:** any image mode (8/16-bit, RGB, RGBA, DICOM) is converted to 8-bit grayscale, squashed "
            "to a square canonical view, resized to the network input size (384 or 448 pixels), replicated to three "
            "channels and normalised with ImageNet statistics.",
            "**X-ray gate:** simple colour, blank and size checks plus an out-of-distribution distance on ResNet "
            "features reject images that are not chest X-rays.",
            "**Classification:** three fine-tuned ResNets score the image and its mirror image; their logit margins "
            "are averaged, calibrated by temperature scaling and compared with a threshold chosen on validation data.",
            "**Explainability:** Grad-CAM heat maps from the last residual stage of every member are averaged and "
            "overlaid on the X-ray.",
            "**Application:** a FastAPI back-end and a React front-end provide scanning, batch triage, PDF reports, "
            "scan history, a CURB-65 calculator, a Learn page and a Model page, all running on the local computer.",
        ]),
        ("p", "{tab:compare} compares the existing approach with the proposed system."),
        ("tab", "compare", "Comparison of the existing and proposed systems",
         ["Aspect", "Existing system", "Proposed system (PneumoScan AI)"],
         [
             ["Reading", "Manual reading of every film by a specialist",
              "Automatic second reading in about 0.4 s per image on the GPU"],
             ["Availability", "Depends on radiologist availability", "Runs offline on an ordinary laptop (GPU or CPU)"],
             ["Prioritisation", "Usually first come, first served",
              "Triage queue sorted by pneumonia probability, urgent cases flagged"],
             ["Explanation", "Not applicable / black-box models", "Grad-CAM heat map for every prediction"],
             ["Evaluation", "Often re-split data or test-set tuning",
              "All choices on validation; official test set scored once"],
             ["Input check", "Models accept any image", "X-ray gate rejects photographs, documents and blanks"],
             ["Reporting", "Separate, manual", "One-click patient PDF with heat map and disclaimer"],
             ["Clinical context", "Separate tools", "Built-in CURB-65 calculator and sourced patient education"],
         ], [1.25, 2.1, 2.65], {"size": 10}),
        ("h2", "3.3 Feasibility Study"),
        ("bullets", [
            "**Technical feasibility:** the dataset is public, ImageNet-pretrained ResNets are available in "
            "torchvision, and fine-tuning three ResNets took 55.5 minutes in total on a 6 GB laptop GPU.",
            "**Economic feasibility:** only free and open-source software and an openly licensed dataset are used; no "
            "paid service or cloud resource is needed.",
            "**Operational feasibility:** the application starts with a double-click (start.bat), runs in a web "
            "browser, needs no internet connection and stores data only on the local computer.",
        ]),
        ("h2", "3.4 Requirement Specification"),
        ("h3", "3.4.1 Hardware Requirements"),
        ("tab", "hw", "Hardware used for development, training and testing",
         ["Component", "Specification"],
         [
             ["GPU", "NVIDIA GeForce RTX 3050 Laptop GPU, 6 GB (CUDA)"],
             ["CPU", "Intel Core i5-12450HX"],
             ["Memory", "16 GB RAM (15.7 GB usable)"],
             ["Storage", "About 1.2 GB for the dataset archive, plus the extracted images, cache and model weights "
                         "(three fp16 weight files of 41–46 MB each)"],
             ["Operating system", "Windows 11"],
             ["Minimum to run the app", "Any Windows computer that can run Python 3.11; the GPU is optional "
                                        "(CPU-only inference measured at about 1.25 s per image)"],
         ], [1.8, 4.2]),
        ("h3", "3.4.2 Software Requirements"),
        ("tab", "sw", "Software used in the project",
         ["Software", "Version", "Purpose"],
         [
             ["Python", "3.11.9", "Programming language for the ML pipeline and back-end"],
             ["PyTorch + CUDA", "2.11.0 (CUDA 12.8)", "Deep-learning framework, GPU training and inference [21]"],
             ["torchvision", "0.26.0", "ResNet models, ImageNet weights, image transforms"],
             ["timm", "1.0.31", "Installed in the environment; the final models use torchvision ResNets"],
             ["scikit-learn", "1.9.1", "Metrics, patient-level split, Ledoit-Wolf covariance [22]"],
             ["NumPy / SciPy / pandas", "2.4 / 1.17 / 3.1", "Numerical work, temperature fitting, split tables"],
             ["Pillow / OpenCV / pydicom", "13.0 / 5.0 / 3.0", "Image reading, colour maps, DICOM support"],
             ["matplotlib / scikit-image", "3.11 / 0.26", "Report figures; non-X-ray test images for the gate"],
             ["FastAPI / Uvicorn", "0.162 / 0.54", "REST API back-end and web server"],
             ["SQLite (sqlite3)", "bundled with Python", "Local scan history database"],
             ["ReportLab", "5.1", "Patient PDF reports"],
             ["Node.js", "24", "Building the front-end"],
             ["React / TypeScript / Vite", "19.1 / 5.8 / 7.3", "Front-end user interface and build tool"],
             ["Tailwind CSS / React Router / Motion", "4.1 / 7.18 / 12.43", "Styling, page routing and animation"],
             ["pytest", "–", "Automated tests of the inference contract and the API"],
         ], [1.9, 1.35, 2.75], {"size": 10}),
        ("h3", "3.4.3 Functional Requirements"),
        ("bullets", [
            "Accept a chest X-ray by drag-and-drop, file browsing, paste or a built-in sample gallery (JPG, PNG, BMP, "
            "WEBP, TIFF or DICOM, up to 25 MB).",
            "Reject images that are not chest X-rays with a friendly message, without saving them.",
            "Return the label, calibrated probability, confidence, decision threshold, risk level, inference time "
            "and a Grad-CAM heat map with an opacity slider and side-by-side view.",
            "Store each scan with optional patient details and doctor’s notes; allow search, edit and deletion.",
            "Generate a patient PDF report with the result, heat map and disclaimer.",
            "Analyse up to 50 X-rays at once and sort them by pneumonia probability, with CSV export.",
            "Compute the CURB-65 / CRB-65 score with the recommended care setting.",
            "Show the model’s test performance, figures, limitations and sourced patient information.",
        ]),
        ("h3", "3.4.4 Non-Functional Requirements"),
        ("bullets", [
            "**Offline and private:** no internet access at runtime; the server listens on 127.0.0.1 only and all data "
            "stay on the local computer.",
            "**Performance:** a full analysis (three ResNets, two views each, Grad-CAM) in well under one second on the "
            "GPU.",
            "**Reliability:** weights loaded once at start-up with a warm-up prediction; clear error messages for "
            "corrupt, empty or oversized files.",
            "**Usability:** light and dark themes, keyboard accessible, readable on a laptop screen and a projector.",
            "**Safety and honesty:** a disclaimer on every result screen and PDF; honest reporting of metrics.",
        ]),
        ("h2", "3.5 System Architecture"),
        ("p", "{fig:sysarch} shows the overall architecture. It has three layers. The **presentation layer** is a "
              "React single-page application that runs in the browser. The **application layer** is a FastAPI server "
              "that exposes a JSON REST API, decodes and validates uploaded images, manages the model and builds PDF "
              "reports. The **model and data layer** contains the X-ray gate, the ResNet ensemble with calibration and "
              "threshold, Grad-CAM and the SQLite database with saved images."),
        ("fig", "sysarch", RFIG / "system_architecture.png", 6.0, "Overall system architecture of PneumoScan AI"),
        ("h2", "3.6 Use-Case Diagram"),
        ("p", "{fig:usecase} shows the three kinds of users and what they can do. A **patient** uploads an X-ray, sees "
              "the result with its heat map, downloads a report and reads the Learn page. A **doctor** additionally "
              "uses the batch triage queue, manages the scan history and uses the CURB-65 calculator. A **student** "
              "mainly uses the scanner, the heat maps, the Learn page and the Model page to understand how the system "
              "works."),
        ("fig", "usecase", RFIG / "use_case_diagram.png", 5.2, "Use-case diagram"),
        ("h2", "3.7 Data Flow"),
        ("p", "{fig:workflow} shows how data flows from the raw dataset to the deployed application. The prediction "
              "data flow for a single upload is:"),
        ("fig", "workflow", RFIG / "training_workflow.png", 6.0, "Training, validation and deployment data flow"),
        ("numbered", [
            "The browser sends the image and optional patient details to POST /api/predict as multipart form data.",
            "The server checks the size, decodes the image (including DICOM) and applies the EXIF orientation.",
            "The X-ray gate runs; if the image is not a chest X-ray, a rejection with the reason is returned and "
            "nothing is stored.",
            "Each of the three ResNets scores the image and its mirror image; the averaged logit margin is calibrated "
            "into a probability and compared with the threshold to give the label and risk level.",
            "Grad-CAM maps for the final label are computed, averaged and turned into overlay and heat-map PNG images.",
            "The scan record and images are saved in SQLite and on disk, and the full result is returned as JSON for "
            "display; the PDF report can then be downloaded from /api/report/{id}.pdf.",
        ]),
        ("h2", "3.8 Module Description"),
        ("tab", "modules", "Modules of the system",
         ["Module", "Source files", "Responsibility"],
         [
             ["Data preparation", "ml/prepare_data.py", "Verify image counts, patient-level validation split, 512 × 512 "
              "grayscale cache, leakage checks"],
             ["Dataset and augmentation", "ml/datasets.py", "PyTorch dataset, training augmentation, evaluation transform"],
             ["Model building and training", "ml/common.py, ml/train.py", "ResNet with a 2-class head; fine-tuning "
              "with AdamW, cosine schedule, AMP, EMA, early stopping"],
             ["Evaluation and calibration", "ml/evaluate.py", "Flip TTA, ensemble, temperature scaling, Youden-J "
              "threshold on validation, single test scoring, export"],
             ["Explainability", "ml/gradcam.py", "Grad-CAM on layer4, colour map and overlay"],
             ["X-ray gate", "ml/xray_gate.py", "Heuristics and Mahalanobis out-of-distribution detector"],
             ["Inference API", "ml/inference.py", "PneumoniaModel: check_image, predict, info"],
             ["Back-end API", "app/backend/main.py, model_service.py, imaging.py",
              "REST endpoints, model loading and warm-up, safe image decoding"],
             ["Storage and reports", "app/backend/storage.py, report.py", "SQLite history and images; PDF reports"],
             ["Front-end", "app/frontend/src", "Scan, Triage, History, CURB-65, Learn, Model and About pages"],
         ], [1.45, 1.75, 2.8], {"size": 10}),
    ]


def ch4():
    return [
        ("chapter", 4, "Dataset Details"),
        ("h2", "4.1 Source of the Dataset"),
        ("p", "The project uses the paediatric chest X-ray dataset released by Kermany et al. together with their "
              "^^Cell^^ paper [2], [17]. The images were collected at Guangzhou Women and Children’s Medical Center "
              "from children aged one to five years, and the labels were assigned by expert physicians. The original "
              "release was downloaded from Mendeley Data without any login and its integrity was verified against "
              "the SHA-256 hash published by Mendeley. {tab:dataset} summarises the dataset."),
        ("tab", "dataset", "Summary of the dataset",
         ["Item", "Value"],
         [
             ["Name", "Labeled Optical Coherence Tomography (OCT) and Chest X-Ray Images for Classification, "
                      "Mendeley Data, version 2 (2018) [17]"],
             ["DOI", "10.17632/rscbjbr9sj.2"],
             ["File used", "ChestXRay2017.zip (1,235,512,464 bytes)"],
             ["Licence", "CC BY 4.0 (credit: Kermany et al., Cell, 2018 [2])"],
             ["Population", "Paediatric patients (1–5 years), Guangzhou Women and Children’s Medical Center; "
                            "frontal (anterior–posterior) chest X-rays"],
             ["Official training set", "5,232 images: 1,349 NORMAL and 3,883 PNEUMONIA (2,538 bacterial and 1,345 "
                                       "viral by file name)"],
             ["Official test set", "624 images: 234 NORMAL and 390 PNEUMONIA (matches the official release exactly)"],
             ["Image format", "JPEG; 5,573 grayscale and 283 RGB-encoded grayscale images"],
             ["Image size", "Median 1281 × 888 pixels; width from 384 to 2916 pixels"],
         ], [1.7, 4.3], {"size": 10}),
        ("h2", "4.2 Class Distribution and Split"),
        ("p", "The official test set is kept untouched until the final evaluation. A validation set was carved out of "
              "the official training folder with stratified group K-fold (seven folds, shuffled, random seed 42), "
              "grouping the images **by patient** so that no child appears in both training and validation. Patient "
              "identifiers were parsed from the file names (person123_bacteria_456.jpeg → patient P123; "
              "IM-0115-0001.jpeg or NORMAL2-IM-0115-0001.jpeg → patient N0115). One fold (14.3% of the training "
              "images) became the validation set. {tab:split} and {fig:classdist} show the resulting split."),
        ("tab", "split", "Images and patients in each split",
         ["Split", "NORMAL", "PNEUMONIA", "Total", "Patients", "Pneumonia share"],
         [
             ["Train", "1,157", "3,328", "4,485", "2,272", "74.2%"],
             ["Validation", "192", "555", "747", "378", "74.3%"],
             ["Test (official)", "234", "390", "624", "404", "62.5%"],
             ["Total", "1,583", "4,273", "5,856", "–", "73.0%"],
         ], [1.3, 0.85, 1.05, 0.75, 0.85, 1.2], {"align": ["L", "R", "R", "R", "R", "R"], "bold_last": True}),
        ("fig", "classdist", FIG / "class_distribution.png", 4.6, "Class distribution in the training, validation and "
                                                                  "test splits"),
        ("p", "The training data are imbalanced (about three pneumonia images for every normal image), while the test "
              "set has a different balance (62.5% pneumonia). This difference matters for the choice of the decision "
              "threshold and is discussed in Chapter 7."),
        ("h2", "4.3 Sample Images"),
        ("p", "{fig:samples} shows typical training images. Normal X-rays show clear, dark lung fields with sharp "
              "borders of the heart and diaphragm, while pneumonia X-rays show hazy or dense white areas. Many images "
              "also contain burned-in text such as the “R” side marker and exposure values."),
        ("fig", "samples", RFIG / "sample_images.jpg", 6.0, "Sample training X-rays: four NORMAL (top) and four "
                                                            "PNEUMONIA (bottom)"),
        ("h2", "4.4 Pre-processing"),
        ("p", "The same pre-processing code (ml/common.py) is used for training, evaluation and the application, so "
              "the network always sees images in the same way:"),
        ("numbered", [
            "Any PIL image mode is converted to 8-bit grayscale: 16- and 32-bit images (for example from DICOM) are "
            "min–max scaled, transparent pixels are composited on black, the EXIF orientation is applied and colour "
            "is converted with the ITU-R 601 luma formula.",
            "The image is **squashed** (not cropped) to a 512 × 512 canonical view with Lanczos resampling, so the "
            "whole chest is always visible and the heat map maps back exactly onto the original aspect ratio. "
            "Training images are cached in this form to speed up loading.",
            "The canonical view is resized to the member’s input size (384 × 384 or 448 × 448), the gray channel is "
            "replicated to three channels, and the values are normalised with the ImageNet mean (0.485, 0.456, 0.406) "
            "and standard deviation (0.229, 0.224, 0.225), because the backbones were pretrained on colour ImageNet "
            "photographs [23].",
        ]),
        ("h2", "4.5 Data Augmentation"),
        ("p", "To reduce over-fitting, every training image is randomly transformed each time it is used. The "
              "augmentations ({tab:aug}) imitate realistic variation between X-ray acquisitions; vertical flips are "
              "not used because an upside-down chest X-ray is not realistic."),
        ("tab", "aug", "Training augmentation (torchvision transforms v2)",
         ["Transform", "Setting", "Purpose"],
         [
             ["RandomResizedCrop", "scale 0.75–1.0, aspect ratio 0.9–1.1", "Small changes of framing and zoom"],
             ["RandomHorizontalFlip", "p = 0.5", "Left–right variation"],
             ["RandomAffine", "rotation ±10°, translation ±5%, scale 0.95–1.05", "Patient tilt and position"],
             ["ColorJitter", "brightness ±0.2, contrast ±0.2", "Exposure differences"],
             ["GaussianBlur", "kernel 5, σ 0.1–1.2, p = 0.2", "Slight motion or focus blur"],
             ["Gaussian noise", "σ = 0.02, p = 0.2", "Sensor noise"],
         ], [1.7, 2.3, 2.0], {"size": 10}),
        ("h2", "4.6 Handling Class Imbalance"),
        ("p", "Instead of discarding images, the loss is weighted by inverse class frequency, w_c = N / (2 N_c), where "
              "N is the number of training images and N_c the number in class c. With 1,157 normal and 3,328 pneumonia "
              "training images this gives weights of **1.94 for NORMAL** and **0.67 for PNEUMONIA**, so mistakes on the "
              "minority class cost about three times more."),
        ("h2", "4.7 Leakage Checks"),
        ("p", "Data leakage (the same image or patient in training and evaluation data) would make the results look "
              "better than they really are. The checks in {tab:leak} were run automatically by ml/prepare_data.py."),
        ("tab", "leak", "Leakage checks",
         ["Check", "Result"],
         [
             ["Patients in both train and validation", "0"],
             ["Exact duplicate files (SHA-1) between test and train/validation", "0"],
             ["Exact duplicate files between validation and train", "0"],
             ["Near duplicates between test and train/validation (correlation of 64 × 64 thumbnails ≥ 0.99)",
              "0 (highest correlation 0.968)"],
             ["Patient numbers appearing in both official train and test folders",
              "264 numbers, but no shared images (see text)"],
         ], [4.2, 1.8], {"size": 10, "align": ["L", "C"]}),
        ("p", "The dataset authors number patients separately inside the training and test folders and state that "
              "the test set comes from independent patients. Because the exact-hash and near-duplicate checks found "
              "no shared images, the 264 matching numbers are a naming coincidence, not leakage."),
    ]


def ch5():
    x = mt("x")
    Fx = mt("F") + mparen(mt("x") + mt(", {") + msub(mt("W"), mt("i")) + mt("}"))
    return [
        ("chapter", 5, "Model Architecture and Methodology"),
        ("h2", "5.1 Convolutional Neural Networks"),
        ("p", "A convolutional neural network is built from a few kinds of layers. A **convolution layer** slides "
              "small learnable filters (kernels) over the input and computes, at every position, a weighted sum of "
              "the pixels under the filter ({eq:conv}). Early filters respond to edges and textures; deeper filters "
              "combine them into larger patterns such as rib outlines or opacities."),
        ("eq", "conv", mparen(mt("I") + mt(" * ") + mt("K")) + mparen(mt("i, j")) + mt(" = ")
         + mnary("∑", mt("m"), "", mnary("∑", mt("n"), "", mt("I") + mparen(mt("i + m, j + n")) + mt(" K")
                                           + mparen(mt("m, n"))))),
        ("p", "**Batch normalisation** standardises the activations of each channel during training, which stabilises "
              "and speeds up learning. The **ReLU** activation, ReLU(x) = max(0, x), adds non-linearity. **Pooling** "
              "layers reduce the spatial size, and at the end **global average pooling** turns each feature map into "
              "a single number. A **fully connected** layer maps these features to one score (logit) per class, and "
              "the softmax function turns the logits into probabilities."),
        ("h2", "5.2 Residual Learning"),
        ("p", "Simply stacking more layers does not keep improving a plain CNN: deeper plain networks show higher "
              "training error than shallower ones (the degradation problem) [1]. A residual block lets a few layers "
              "learn a residual function F and adds the input x back through an identity shortcut ({eq:res}). When "
              "the number of channels or the spatial size changes, a 1 × 1 projection W_s is used on the shortcut "
              "({eq:proj}) [1]."),
        ("eq", "res", mt("y = ") + Fx + mt(" + x")),
        ("eq", "proj", mt("y = ") + Fx + mt(" + ") + msub(mt("W"), mt("s")) + mt("x")),
        ("p", "If the best mapping is close to the identity, the block only needs to push F towards zero, which is "
              "easy. During back-propagation the gradient also flows directly through the shortcut, so very deep "
              "networks remain trainable."),
        ("h2", "5.3 Basic and Bottleneck Blocks"),
        ("p", "ResNet-18 and ResNet-34 use the **basic block**: two 3 × 3 convolutions, each followed by batch "
              "normalisation, with ReLU after the first and after the addition. ResNet-50 uses the **bottleneck "
              "block** shown in {fig:resblock}: a 1 × 1 convolution reduces the number of channels, a 3 × 3 "
              "convolution works on the reduced representation, and a second 1 × 1 convolution restores the channels "
              "(for example 256 → 64 → 64 → 256) before the shortcut is added. This keeps deep networks affordable."),
        ("fig", "resblock", FIG / "residual_block_diagram.png", 3.0, "Bottleneck residual block with identity shortcut"),
        ("h2", "5.4 ResNet-18, ResNet-34 and ResNet-50"),
        ("p", "All three depths share the same design: a 7 × 7 stride-2 convolution and a 3 × 3 max-pool, four "
              "residual stages (layer1 to layer4) with 64, 128, 256 and 512 base channels, global average pooling "
              "and a fully connected layer. They differ in the number and type of blocks ({tab:resnets}). The "
              "training code supports all three; the final ensemble uses ResNet-34 and ResNet-50."),
        ("tab", "resnets", "Comparison of the ResNet variants used in this work",
         ["Property", "ResNet-18", "ResNet-34", "ResNet-50"],
         [
             ["Block type", "Basic (2 × 3×3)", "Basic (2 × 3×3)", "Bottleneck (1×1, 3×3, 1×1)"],
             ["Blocks in layer1–layer4", "2, 2, 2, 2", "3, 4, 6, 3", "3, 4, 6, 3"],
             ["Weighted layers", "18", "34", "50"],
             ["Channels after layer4", "512", "512", "2048"],
             ["Parameters with our 2-class head", "11.18 M", "21.29 M", "23.51 M"],
             ["FLOPs at 224 × 224 [1]", "1.8 × 10⁹", "3.6 × 10⁹", "3.8 × 10⁹"],
             ["ImageNet weights (torchvision)", "IMAGENET1K_V1", "IMAGENET1K_V1", "IMAGENET1K_V2"],
             ["Used in final ensemble", "No", "Yes (384 px)", "Yes (384 px and 448 px)"],
         ], [2.1, 1.25, 1.25, 1.4], {"size": 10, "align": ["L", "C", "C", "C"]}),
        ("h2", "5.5 Transfer Learning"),
        ("p", "Training a deep network from random weights needs far more labelled images than the 4,485 training "
              "X-rays available. Transfer learning starts instead from weights learned on ImageNet [23], whose early "
              "filters (edges, textures, shapes) are useful for almost any image. The 1000-class ImageNet layer is "
              "replaced by a new head, Dropout(0.2) followed by Linear(features, 2), and **all layers are fine-tuned** "
              "end-to-end. The pretrained backbone uses a learning rate three times smaller than the new head, so the "
              "useful pretrained features are adapted gently while the head learns quickly."),
        ("h2", "5.6 Complete Pipeline"),
        ("p", "{fig:arch} shows the full pipeline with the output size of every ResNet-50 stage at 384 × 384 input. "
              "The X-ray is pre-processed, passed through three fine-tuned ResNets (each on the original and the "
              "mirrored image), the logit margins are averaged and calibrated, the threshold gives the decision, and "
              "Grad-CAM uses the layer4 activations and gradients to produce the heat map."),
        ("fig", "arch", RFIG / "architecture_diagram_rotated.png", 3.95, "Architecture of the PneumoScan AI pipeline "
                                                                "(ResNet-50 member shown; rotated to fit the page)"),
        ("h2", "5.7 Training Setup"),
        ("h3", "5.7.1 Loss Function"),
        ("p", "The loss is cross-entropy with class weights w_c (Section 4.6) and label smoothing ε = 0.1 [24]. Label "
              "smoothing replaces the one-hot target with q_c = (1 − ε)·1[c = y] + ε/K, with K = 2 classes, which "
              "discourages over-confident predictions:"),
        ("eq", "loss", mt("L = −") + mnary("∑", mt("c=1"), mt("K"), msub(mt("w"), mt("c")) + mt(" ") + msub(mt("q"), mt("c"))
                                                         + mt(" ") + mp("log ") + msub(mt("p"), mt("c")))),
        ("h3", "5.7.2 Optimiser and Learning-Rate Schedule"),
        ("p", "AdamW [25] (Adam with decoupled weight decay 0.01) is used with a base learning rate of 3 × 10⁻⁴ for "
              "the head and 1 × 10⁻⁴ (0.33×) for the backbone. The learning rate rises linearly during one warm-up "
              "epoch and then follows a cosine decay that is updated every step ({eq:cos}), where s is the current "
              "step, s_w the number of warm-up steps and S the total number of steps. Gradients are clipped to a "
              "maximum norm of 2."),
        ("eq", "cos", msub(mt("η"), mt("s")) + mt(" = ") + msub(mt("η"), mt("0")) + mt(" · ") + mfrac(mt("1"), mt("2"))
         + mparen(mt("1 + ") + mp("cos") + mparen(mt("π ") + mfrac(mt("s − ") + msub(mt("s"), mt("w")),
                                                                   mt("S − ") + msub(mt("s"), mt("w")))))),
        ("h3", "5.7.3 Mixed Precision, EMA and Early Stopping"),
        ("p", "Training uses automatic mixed precision (fp16 autocast with a gradient scaler) [26] to save memory and "
              "time on the 6 GB GPU. An exponential moving average (EMA) of the weights ({eq:ema}, decay d = 0.998 with "
              "a short warm-up) gives a smoother model; the EMA weights are the ones evaluated and saved. After every "
              "epoch the validation ROC-AUC is computed; the checkpoint with the best validation AUC (ties broken by "
              "lower validation loss) is kept, and training stops early after 7 epochs without improvement."),
        ("eq", "ema", msub(mt("θ"), mp("EMA")) + mt(" ← d · ") + msub(mt("θ"), mp("EMA")) + mt(" + ")
         + mparen(mt("1 − d")) + mt(" · θ")),
        ("p", "{tab:hyper} lists the complete training configuration."),
        ("tab", "hyper", "Training hyperparameters (identical for all members unless stated)",
         ["Parameter", "Value"],
         [
             ["Members", "ResNet-50 at 384 px (batch 24, seed 1); ResNet-34 at 384 px (batch 32, seed 2); "
                         "ResNet-50 at 448 px (batch 16, seed 3)"],
             ["Classification head", "Dropout(0.2) → Linear(features, 2); all layers trainable"],
             ["Loss", "Weighted cross-entropy (NORMAL 1.94, PNEUMONIA 0.67), label smoothing 0.1"],
             ["Optimiser", "AdamW, weight decay 0.01"],
             ["Learning rate", "Head 3 × 10⁻⁴, backbone 1 × 10⁻⁴; 1 warm-up epoch, then per-step cosine decay"],
             ["Gradient clipping", "Maximum norm 2.0"],
             ["Precision", "Mixed precision (fp16 autocast + GradScaler)"],
             ["Weight averaging", "EMA, decay 0.998 (with warm-up); EMA weights evaluated and saved"],
             ["Epochs", "Up to 20; early stopping with patience 7 on validation ROC-AUC"],
             ["Data loading", "Shuffled, drop last incomplete batch, 3 worker processes"],
             ["Shipped weights", "fp16 state dictionaries (41–46 MB each); all metrics computed with these weights"],
         ], [1.7, 4.3], {"size": 10}),
        ("h2", "5.8 Ensemble and Test-Time Augmentation"),
        ("p", "For each member m and view v (the original image and its horizontal mirror), the network outputs two "
              "logits; their difference is the **logit margin** ({eq:margin}). The margins of the M = 3 members and "
              "V = 2 views are averaged ({eq:avg}). Averaging several models that make different mistakes reduces the "
              "variance of the prediction, and the ensemble of all trained members was fixed as the final model "
              "before the test set was scored."),
        ("eq", "margin", msub(mt("z"), mt("m,v")) + mt(" = ") + msub(mt("ℓ"), mp("PNEUMONIA")) + mt(" − ")
         + msub(mt("ℓ"), mp("NORMAL"))),
        ("eq", "avg", mbar(mt("z")) + mt(" = ") + mfrac(mt("1"), mt("M V")) + mnary("∑", mt("m=1"), mt("M"),
                                                                              mnary("∑", mt("v=1"), mt("V"), msub(mt("z"), mt("m,v"))))),
        ("h2", "5.9 Temperature Scaling"),
        ("p", "Modern networks are often over-confident. Temperature scaling [27] divides the averaged margin by a "
              "single temperature T before the sigmoid ({eq:temp}). T is fitted by minimising the negative "
              "log-likelihood on the **validation** set ({eq:nll}); for the ensemble T = 0.602. Temperature scaling "
              "does not change the ranking of images, only how well the probability values match reality."),
        ("eq", "temp", mt("p = σ") + mparen(mfrac(mbar(mt("z")), mt("T"))) + mt(" = ")
         + mfrac(mt("1"), mt("1 + ") + msup(mt("e"), mt("−") + mbar(mt("z")) + mt("/T")))),
        ("eq", "nll", msup(mt("T"), mt("*")) + mt(" = ") + msub(mp("arg min"), mt("T")) + mt(" − ")
         + mfrac(mt("1"), mt("N")) + mnary("∑", mt("n=1"), mt("N"), mparen(msub(mt("y"), mt("n")) + mt(" ") + mp("log ")
                                                                          + msub(mt("p"), mt("n")) + mt(" + ")
                                                                          + mparen(mt("1 − ") + msub(mt("y"), mt("n")))
                                                                          + mt(" ") + mp("log") + mparen(mt("1 − ") + msub(mt("p"), mt("n")))
                                                                          , "[", "]"))),
        ("h2", "5.10 Threshold Selection and Risk Levels"),
        ("p", "The decision threshold t is chosen on the validation set to maximise Youden’s J statistic [28] "
              "({eq:youden}), which is equivalent to maximising balanced accuracy. When a whole interval of thresholds "
              "gives the same best J, the middle of the interval (in logit space) is taken. This rule was written into "
              "ml/evaluate.py before the test set was ever scored, and it gave **t = 0.0743**. An image is labelled "
              "PNEUMONIA when p ≥ t."),
        ("eq", "youden", mt("J") + mparen(mt("t")) + mt(" = ") + mp("Sensitivity") + mparen(mt("t")) + mt(" + ")
         + mp("Specificity") + mparen(mt("t")) + mt(" − 1")),
        ("p", "Because the threshold is low, a PNEUMONIA label can come with a modest probability. The application "
              "therefore also reports a **risk level** whose bands are defined relative to t ({tab:risk})."),
        ("tab", "risk", "Risk levels derived from the calibrated probability p (t = 0.0743)",
         ["Risk level", "Rule", "Probability range", "Meaning"],
         [
             ["Low", "p < t / 2", "p < 0.037", "Normal side, well below the threshold"],
             ["Moderate", "t / 2 ≤ p < (1 + t) / 2", "0.037 ≤ p < 0.537", "Borderline or possible pneumonia; see a doctor"],
             ["High", "p ≥ (1 + t) / 2", "p ≥ 0.537", "Pneumonia likely; prompt medical review"],
         ], [1.0, 1.55, 1.5, 1.95], {"size": 10}),
        ("h2", "5.11 Grad-CAM Explanations"),
        ("p", "Grad-CAM [4] explains a prediction by finding which regions of the last convolutional feature maps "
              "increased the class score. Let A^k be the k-th feature map of layer4 (2048 maps of 12 × 12 for "
              "ResNet-50 at 384 px) and y^c the score for class c. The importance of each map is the spatial average "
              "of the gradient ({eq:alpha}), where Z is the number of positions, and the heat map is the ReLU of the "
              "weighted sum of the maps ({eq:gradcam})."),
        ("eq", "alpha", msubsup(mt("α"), mt("k"), mt("c")) + mt(" = ") + mfrac(mt("1"), mt("Z"))
         + mnary("∑", mt("i"), "", mnary("∑", mt("j"), "", mfrac(mt("∂") + msup(mt("y"), mt("c")),
                                                                mt("∂") + msubsup(mt("A"), mt("ij"), mt("k")))))),
        ("eq", "gradcam", msubsup(mt("L"), mp("Grad-CAM"), mt("c")) + mt(" = ") + mp("ReLU")
         + mparen(mnary("∑", mt("k"), "", msubsup(mt("α"), mt("k"), mt("c")) + mt(" ") + msup(mt("A"), mt("k"))))),
        ("p", "In this project the score for PNEUMONIA is the logit margin z, and the score for NORMAL is −z, so one "
              "backward pass gives the map for either class. The map for the ensemble’s final label is computed for "
              "every member, resized to the display image, averaged over the members and normalised to [0, 1]. It is "
              "drawn with a “jet” colour map (blue = low, red = high) whose transparency grows with importance, and "
              "overlaid on the X-ray at 60% opacity."),
        ("h2", "5.12 X-ray Gate (Out-of-Distribution Detection)"),
        ("p", "A classifier trained only on chest X-rays will still output NORMAL or PNEUMONIA for a photograph of a "
              "cat. To prevent this, every image first passes two checks. (1) **Heuristics:** images smaller than 64 "
              "pixels, nearly uniform images (gray-level standard deviation below 8) and colourful images (mean "
              "saturation above 0.12 or more than 5% strongly coloured pixels) are rejected. (2) **Feature distance:** "
              "the 2048-dimensional pooled layer4 features f(x) of the first ResNet-50 member are compared with the "
              "class means μ_c of the training X-rays using a Mahalanobis distance with a shared Ledoit-Wolf "
              "covariance Σ [29], [30] ({eq:maha}). The cut-off τ is 1.15 times the 99.5th percentile of the "
              "validation distances (τ = 66.04), and the distance is mapped to a score between 0 and 1 ({eq:gate}), "
              "which equals 0.5 exactly at the cut-off."),
        ("eq", "maha", mt("d") + mparen(mt("x")) + mt(" = ") + msub(mp("min"), mt("c")) + mrad(
            msup(mparen(mt("f") + mparen(mt("x")) + mt(" − ") + msub(mt("μ"), mt("c"))), mt("T")) + mt(" ")
            + msup(mt("Σ"), mt("−1")) + mparen(mt("f") + mparen(mt("x")) + mt(" − ") + msub(mt("μ"), mt("c"))))),
        ("eq", "gate", mt("s") + mparen(mt("x")) + mt(" = ") + mfrac(mt("1"), mt("1 + ") + msup(mparen(mfrac(mt("d") + mparen(mt("x")), mt("τ"))), mt("4")))),
        ("h2", "5.13 Evaluation Metrics"),
        ("p", "With PNEUMONIA as the positive class, TP, TN, FP and FN denote true positives, true negatives, false "
              "positives and false negatives. The metrics reported in Chapter 7 are:"),
        ("eq", "acc", mp("Accuracy") + mt(" = ") + mfrac(mt("TP + TN"), mt("TP + TN + FP + FN"))
         + mt(",    ") + mp("Precision") + mt(" = ") + mfrac(mt("TP"), mt("TP + FP"))),
        ("eq", "sens", mp("Sensitivity") + mt(" = ") + mfrac(mt("TP"), mt("TP + FN"))
         + mt(",    ") + mp("Specificity") + mt(" = ") + mfrac(mt("TN"), mt("TN + FP"))),
        ("eq", "f1", msub(mt("F"), mt("1")) + mt(" = ") + mfrac(mt("2 · Precision · Sensitivity"),
                                                                 mt("Precision + Sensitivity"))),
        ("p", "Sensitivity (recall) is the share of pneumonia X-rays that are detected, and specificity is the share "
              "of normal X-rays correctly called normal. The **ROC-AUC** is the area under the curve of sensitivity "
              "against (1 − specificity) over all thresholds; it measures how well the model ranks pneumonia above "
              "normal images, independent of the threshold. The **PR-AUC** (average precision) summarises the "
              "precision–recall curve."),
    ]
