"""Chapter 9, References, Appendix A (source code) and Appendix B (how to run)."""
from src_extract import read


def ch9():
    return [
        ("chapter", 9, "Conclusion and Future Enhancements"),
        ("h2", "9.1 Conclusion"),
        ("p", "This project developed **PneumoScan AI**, a complete and explainable system for detecting pneumonia in "
              "paediatric chest X-rays using deep residual networks. ImageNet-pretrained ResNet-34 and ResNet-50 "
              "models were fine-tuned with transfer learning, class-weighted and label-smoothed cross-entropy, "
              "realistic augmentation, mixed precision and weight averaging, and combined into a three-member ensemble "
              "with test-time augmentation and temperature scaling. Every choice was made on a patient-level validation "
              "split, and the official 624-image test set was evaluated only once."),
        ("p", "The final ensemble achieved an accuracy of **94.55%**, a sensitivity of **99.74%** (one missed pneumonia "
              "out of 390), a specificity of **85.90%**, a precision of **92.18%**, an F1-score of **95.81%** and a "
              "ROC-AUC of **0.9867**. These results are well above the published ResNet baselines on the same test set "
              "and above the dataset authors’ own result, although the 95% accuracy target was missed by three images. "
              "The errors are almost entirely normal X-rays flagged for review, which is the safer kind of error for a "
              "screening aid. Grad-CAM heat maps make each decision transparent, and an out-of-distribution gate "
              "rejected all non-X-ray check images. The model is packaged in an offline web application with single "
              "and batch scanning, patient PDF reports, scan history, a CURB-65 calculator and sourced patient "
              "education, which makes it useful for teaching and as a second-reader aid. The project shows that a "
              "carefully and honestly evaluated ResNet system can deliver reliable, explainable support for pneumonia "
              "screening on ordinary hardware."),
        ("h2", "9.2 Limitations"),
        ("bullets", [
            "The model was trained and tested on paediatric X-rays (ages 1–5) from a single hospital; it may perform "
            "worse on adults, other hospitals or other X-ray machines. Pneumonia-screening CNNs have been shown to "
            "perform worse on data from external hospitals (AUC 0.931 internal versus 0.815 external) [13].",
            "It detects only two classes and cannot identify the cause of pneumonia (bacterial or viral) or other lung "
            "diseases.",
            "Specificity on the official test set is 85.9%: false alarms on normal X-rays are the main type of error.",
            "Grad-CAM heat maps are coarse (computed on 12 × 12 or 14 × 14 feature maps); they show where the model "
            "looked, not proof of disease [4]. Some maps also highlight burned-in text such as the “R” side marker, "
            "exposure values or time stamps, a sign of partial shortcut learning from hospital-specific image features.",
            "The validation set comes from the same distribution as the training data, so it overestimated test "
            "performance and produced a threshold that is lower than ideal for the test set.",
            "The X-ray gate recognises images that resemble the training X-rays; other radiographs or adult chest films "
            "may or may not be accepted.",
            "A chest X-ray alone is not enough for diagnosis; symptoms, examination and other tests are needed. Dataset "
            "labels come from clinical grading by physicians and may contain some errors.",
            "The system is a student project and is not a certified medical device.",
        ]),
        ("h2", "9.3 Future Enhancements"),
        ("bullets", [
            "Train and validate on larger, multi-centre and adult datasets, including data from Indian hospitals, and "
            "choose the threshold on a validation set that resembles the deployment data.",
            "Mask or crop burned-in text and markers, or add lung segmentation, so the model focuses only on the lung "
            "fields and shortcut learning is reduced.",
            "Extend to multi-class classification (bacterial versus viral pneumonia and other chest findings).",
            "Evaluate the system prospectively alongside radiologists.",
            "Integrate with hospital PACS and national teleconsultation services.",
            "Build a lightweight mobile version for primary health centres.",
            "Support regional Indian languages in the patient interface.",
        ]),
        ("h2", "9.4 Social Impact"),
        ("p", "PneumoScan AI shows how artificial intelligence can support, not replace, doctors where radiologists "
              "are few. A quick, explainable second opinion on a chest X-ray could help health workers decide which "
              "patients need urgent referral and help busy hospitals prioritise their reporting queues. Because the "
              "system runs offline on a normal computer, it can be used where internet access is unreliable, and "
              "patient data never leave the computer. The Learn page and the patient report give families clear, "
              "trustworthy information on danger signs and prevention, including immunisation against Hib, "
              "pneumococcus, measles and whooping cough, cleaner indoor air and exclusive breastfeeding for the first "
              "six months, which the World Health Organization identifies as key ways to protect children from "
              "pneumonia [14]. By reporting results honestly and showing a clear disclaimer, the project also promotes "
              "responsible use of AI in healthcare."),
    ]


REFERENCES = [
    "K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” in ^^Proc. IEEE Conf. Comput. "
    "Vis. Pattern Recognit. (CVPR)^^, Las Vegas, NV, USA, 2016, pp. 770–778, doi: 10.1109/CVPR.2016.90.",
    "D. S. Kermany ^^et al.^^, “Identifying medical diagnoses and treatable diseases by image-based deep learning,” "
    "^^Cell^^, vol. 172, no. 5, pp. 1122–1131.e9, Feb. 2018, doi: 10.1016/j.cell.2018.02.010.",
    "P. Rajpurkar ^^et al.^^, “CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning,” "
    "arXiv:1711.05225, 2017. [Online]. Available: https://arxiv.org/abs/1711.05225",
    "R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, “Grad-CAM: Visual explanations from "
    "deep networks via gradient-based localization,” in ^^Proc. IEEE Int. Conf. Comput. Vis. (ICCV)^^, Venice, Italy, "
    "2017, pp. 618–626, doi: 10.1109/ICCV.2017.74.",
    "W. S. Lim ^^et al.^^, “Defining community acquired pneumonia severity on presentation to hospital: An "
    "international derivation and validation study,” ^^Thorax^^, vol. 58, no. 5, pp. 377–382, May 2003, "
    "doi: 10.1136/thorax.58.5.377.",
    "J. Yang ^^et al.^^, “MedMNIST v2 – A large-scale lightweight benchmark for 2D and 3D biomedical image "
    "classification,” ^^Sci. Data^^, vol. 10, no. 1, Art. no. 41, Jan. 2023, doi: 10.1038/s41597-022-01721-8.",
    "O. Stephen, M. Sain, U. J. Maduh, and D.-U. Jeong, “An efficient deep learning approach to pneumonia "
    "classification in healthcare,” ^^J. Healthc. Eng.^^, vol. 2019, Art. no. 4180949, Mar. 2019, "
    "doi: 10.1155/2019/4180949.",
    "V. Chouhan ^^et al.^^, “A novel transfer learning based approach for pneumonia detection in chest X-ray images,” "
    "^^Appl. Sci.^^, vol. 10, no. 2, Art. no. 559, Jan. 2020, doi: 10.3390/app10020559.",
    "T. Rahman ^^et al.^^, “Transfer learning with deep convolutional neural network (CNN) for pneumonia detection "
    "using chest X-ray,” ^^Appl. Sci.^^, vol. 10, no. 9, Art. no. 3233, May 2020, doi: 10.3390/app10093233.",
    "M. F. Hashmi, S. Katiyar, A. G. Keskar, N. D. Bokde, and Z. W. Geem, “Efficient pneumonia detection in chest "
    "X-ray images using deep transfer learning,” ^^Diagnostics^^, vol. 10, no. 6, Art. no. 417, Jun. 2020, "
    "doi: 10.3390/diagnostics10060417.",
    "G. Liang and L. Zheng, “A transfer learning method with deep residual network for pediatric pneumonia "
    "diagnosis,” ^^Comput. Methods Programs Biomed.^^, vol. 187, Art. no. 104964, Apr. 2020, "
    "doi: 10.1016/j.cmpb.2019.06.023.",
    "R. Kundu, R. Das, Z. W. Geem, G.-T. Han, and R. Sarkar, “Pneumonia detection in chest X-ray images using an "
    "ensemble of deep learning models,” ^^PLoS ONE^^, vol. 16, no. 9, Art. no. e0256630, Sep. 2021, "
    "doi: 10.1371/journal.pone.0256630.",
    "J. R. Zech, M. A. Badgeley, M. Liu, A. B. Costa, J. J. Titano, and E. K. Oermann, “Variable generalization "
    "performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study,” "
    "^^PLoS Med.^^, vol. 15, no. 11, Art. no. e1002683, Nov. 2018, doi: 10.1371/journal.pmed.1002683.",
    "World Health Organization, “Pneumonia,” Fact sheet, Nov. 11, 2022. [Online]. Available: "
    "https://www.who.int/news-room/fact-sheets/detail/pneumonia",
    "World Health Organization, “The top 10 causes of death,” Fact sheet, Oct. 2, 2026. [Online]. Available: "
    "https://www.who.int/news-room/fact-sheets/detail/the-top-10-causes-of-death",
    "A. Chandramohan ^^et al.^^, “Teleradiology and technology innovations in radiology: status in India and its role "
    "in increasing access to primary health care,” ^^Lancet Reg. Health Southeast Asia^^, vol. 23, Art. no. 100195, "
    "Apr. 2024, doi: 10.1016/j.lansea.2023.100195.",
    "D. Kermany, “Labeled optical coherence tomography (OCT) and chest X-ray images for classification,” Mendeley "
    "Data, v2, 2018, doi: 10.17632/rscbjbr9sj.2.",
    "M. Chumbita ^^et al.^^, “Can artificial intelligence improve the management of pneumonia,” ^^J. Clin. Med.^^, "
    "vol. 9, no. 1, Jan. 2020. [Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC7019351/",
    "Centers for Disease Control and Prevention, “Risk factors for pneumonia,” Feb. 25, 2026. [Online]. Available: "
    "https://www.cdc.gov/pneumonia/risk-factors/index.html",
    "T. Cherian ^^et al.^^, “Standardized interpretation of paediatric chest radiographs for the diagnosis of "
    "pneumonia in epidemiological studies,” ^^Bull. World Health Organ.^^, vol. 83, no. 5, pp. 353–359, 2005. "
    "[Online]. Available: https://pmc.ncbi.nlm.nih.gov/articles/PMC2626240/",
    "A. Paszke ^^et al.^^, “PyTorch: An imperative style, high-performance deep learning library,” in ^^Advances in "
    "Neural Information Processing Systems 32 (NeurIPS)^^, 2019, pp. 8024–8035.",
    "F. Pedregosa ^^et al.^^, “Scikit-learn: Machine learning in Python,” ^^J. Mach. Learn. Res.^^, vol. 12, "
    "pp. 2825–2830, 2011.",
    "J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, “ImageNet: A large-scale hierarchical image "
    "database,” in ^^Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)^^, 2009, pp. 248–255.",
    "C. Szegedy, V. Vanhoucke, S. Ioffe, J. Shlens, and Z. Wojna, “Rethinking the Inception architecture for computer "
    "vision,” in ^^Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)^^, 2016, pp. 2818–2826.",
    "I. Loshchilov and F. Hutter, “Decoupled weight decay regularization,” in ^^Proc. Int. Conf. Learn. "
    "Represent. (ICLR)^^, 2019.",
    "P. Micikevicius ^^et al.^^, “Mixed precision training,” in ^^Proc. Int. Conf. Learn. Represent. (ICLR)^^, 2018.",
    "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, “On calibration of modern neural networks,” in ^^Proc. 34th "
    "Int. Conf. Mach. Learn. (ICML)^^, 2017, pp. 1321–1330.",
    "W. J. Youden, “Index for rating diagnostic tests,” ^^Cancer^^, vol. 3, no. 1, pp. 32–35, 1950.",
    "K. Lee, K. Lee, H. Lee, and J. Shin, “A simple unified framework for detecting out-of-distribution samples and "
    "adversarial attacks,” in ^^Advances in Neural Information Processing Systems 31 (NeurIPS)^^, 2018.",
    "O. Ledoit and M. Wolf, “A well-conditioned estimator for large-dimensional covariance matrices,” ^^J. "
    "Multivariate Anal.^^, vol. 88, no. 2, pp. 365–411, 2004.",
]


def references(r):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt

    from docx_engine import add_inline
    r.front_heading("References", toc=True)
    for i, ref in enumerate(REFERENCES, 1):
        par = r.doc.add_paragraph()
        f = par.paragraph_format
        f.left_indent = Inches(0.45)
        f.first_line_indent = Inches(-0.45)
        f.tab_stops.add_tab_stop(Inches(0.45))
        f.line_spacing = 1.15
        f.space_after = Pt(6)
        f.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_inline(par, f"[{i}]\t" + ref, size=11)


APPENDIX_FILES = [
    ("ml/common.py", "Shared constants, image conversion, model builder and metrics"),
    ("ml/prepare_data.py", "Dataset verification, patient-level split, cache and leakage checks"),
    ("ml/datasets.py", "PyTorch dataset and augmentation pipelines"),
    ("ml/train.py", "Fine-tuning of one ResNet"),
    ("ml/evaluate.py", "Ensemble, calibration, threshold selection, test scoring and export"),
    ("ml/gradcam.py", "Grad-CAM"),
    ("ml/xray_gate.py", "X-ray gate (heuristics and Mahalanobis out-of-distribution detector)"),
    ("ml/inference.py", "PneumoniaModel inference API used by the application"),
    ("app/backend/model_service.py", "Back-end model loading service"),
    ("app/backend/main.py", "FastAPI application and REST endpoints"),
]


def appendix_a():
    blocks = [
        ("appendix", "A", "Appendix A: Source Code"),
        ("p", "This appendix lists the complete source code of the machine-learning pipeline (training, evaluation, "
              "explainability, X-ray gate and inference) and the main back-end files, exactly as used to produce the "
              "results in this report. The remaining files (figure and sample generation, tests, the other back-end "
              "modules and the React front-end) are included in the project folder submitted with this report."),
    ]
    for i, (path, desc) in enumerate(APPENDIX_FILES, 1):
        blocks.append(("h2", f"A.{i} {path}"))
        blocks.append(("p", desc + ".", {"after": 2}))
        blocks.append(("code", None, None, read(path), 8.0))
    return blocks


def appendix_b():
    run = r"""cd C:\PersonalProjects\pneumoscan-ai
start.bat"""
    setup = r"""cd C:\PersonalProjects\pneumoscan-ai
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install -r app\backend\requirements.txt
REM plus PyTorch 2.11 + torchvision 0.26 (CUDA 12.8 build) for the real model

cd app\frontend
npm install
npm run build"""
    pipeline = r"""set PY=.venv\Scripts\python.exe
%PY% -m ml.prepare_data
%PY% -m ml.train --name r50_384_s1 --arch resnet50 --res 384 --epochs 20 --bs 24 --seed 1
%PY% -m ml.train --name r34_384_s2 --arch resnet34 --res 384 --epochs 20 --bs 32 --seed 2
%PY% -m ml.train --name r50_448_s3 --arch resnet50 --res 448 --epochs 20 --bs 16 --seed 3
%PY% -m ml.evaluate --members r50_384_s1 r34_384_s2 r50_448_s3 --val-only
%PY% -m ml.evaluate --members r50_384_s1 r34_384_s2 r50_448_s3 --export
%PY% -m ml.xray_gate
%PY% -m ml.make_figures
%PY% -m pytest ml/test_inference.py -q"""
    single = r""".venv\Scripts\python.exe -m ml.inference sample_xrays\pneumonia_01.jpeg --save out_cam"""
    return [
        ("appendix", "B", "Appendix B: How to Run the Project"),
        ("h2", "B.1 Running the Application (Classroom Demo)"),
        ("numbered", [
            "Double-click **start.bat** in the project folder (C:\\PersonalProjects\\pneumoscan-ai).",
            "Wait a few seconds. The browser opens at http://127.0.0.1:8000/ (or the next free port up to 8010).",
            "Keep the black start.bat window open while using the application; close it (or press Ctrl+C) to stop.",
            "The status pill in the top bar shows **Model ready** once the weights are loaded. No internet connection "
            "is needed.",
        ]),
        ("code", None, None, run),
        ("h2", "B.2 First-Time Setup"),
        ("p", "Only needed if the .venv folder or the built web interface is missing. start.bat also builds the web "
              "interface automatically the first time if Node.js is installed."),
        ("code", None, None, setup),
        ("h2", "B.3 Reproducing the Machine-Learning Pipeline"),
        ("p", "The dataset (ChestXRay2017.zip, Mendeley Data DOI 10.17632/rscbjbr9sj.2) must be extracted to "
              "data/raw/chest_xray. The commands below reproduce every step; the --val-only run never touches the "
              "test split, and the --export run scores the test split once and writes the files in models/."),
        ("code", None, None, pipeline),
        ("h2", "B.4 Analysing a Single Image from the Command Line"),
        ("code", None, None, single),
        ("h2", "B.5 Running the Tests"),
        ("code", None, None, r""".venv\Scripts\python -m pytest ml\test_inference.py -q
.venv\Scripts\python -m pytest app\backend\tests -q
cd app\frontend && npm run lint && npm run build"""),
        ("p", "Interactive API documentation is available at http://127.0.0.1:8000/api/docs while the server is "
              "running. All patient details, images and notes are stored only in app/backend/storage/ on the local "
              "computer."),
    ]
