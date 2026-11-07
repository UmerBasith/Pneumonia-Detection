# Sample X-rays for the PneumoScan AI demo

* `normal_01.jpeg` ... `normal_06.jpeg` and `pneumonia_01.jpeg` ... `pneumonia_06.jpeg` are copied unchanged
  from the **official TEST split** of the dataset below (never used for training or for choosing any setting).
  Pneumonia 01-03 are bacterial cases, 04-06 viral cases.
* They were picked among test images the final model classifies correctly with a clear margin, so the demo is
  representative of typical cases, not of the hard ones. The model is **not** perfect: on the full test set it
  makes mistakes (mostly normal X-rays flagged as pneumonia); see `docs/ML_REPORT.md`.
* `answer_key.csv`: true label, the model's prediction, its probability and risk level, and the original file name.
* `not_xray/`: three ordinary photos (astronaut, cat "Chelsea", coffee cup) from the `scikit-image` sample data
  (public domain / free to use) to demonstrate that the app refuses images that are not chest X-rays.

## Credit

Chest X-ray images: Kermany D., Zhang K., Goldbaum M. (2018). *Labeled Optical Coherence Tomography (OCT) and Chest
X-Ray Images for Classification*, Mendeley Data, v2, https://doi.org/10.17632/rscbjbr9sj.2 - licence
**CC BY 4.0**. Paper: Kermany et al., *Identifying Medical Diagnoses and Treatable Diseases by Image-Based Deep
Learning*, Cell 172(5):1122-1131, 2018, https://doi.org/10.1016/j.cell.2018.02.010.

For education only. Not for diagnosing real patients.
