# Machine Learning Report

## Data

The models use a seeded synthetic dataset generated from the bundled knowledge
base. Each sample is assigned a condition using priors floored at 0.03, listed
symptoms are sampled using illustrative weights, unlisted symptoms use a 0.05
background probability, and some answers are randomly marked unknown.

This data is not clinically collected. It measures internal consistency with
the same knowledge base and does **not** represent real-world accuracy.

## Methods

The default training seed is 7242 and 3000 samples are generated. Data is split
into 60% training, 20% validation, and 20% test with stratification. Logistic
Regression and Random Forest are compared; cross-validation is reported.
Features are 40 present/absent columns, with unknown answers both zero.

Run training with:

```bash
python -m machine_learning.train_model
```

The best model and metadata are saved under `models/`. Metadata includes the
knowledge-base version, exact feature list, seed, metrics, and
`"data_type": "synthetic"`.

## Limitations

Results can be optimistic because both symptoms and labels derive from the same
KB assumptions. Priors and weights are illustrative and not calibrated.
Per-class metrics, macro F1, top-3 accuracy, and confusion matrix values should
not be interpreted as clinical performance.

## Generated results

With seed 7242, the saved Logistic Regression model achieved 82.0% test
accuracy, 0.783 macro F1, and 96.17% top-3 accuracy. Three-fold cross-validation
macro F1 was 0.745 plus or minus 0.018. The Random Forest comparison and
per-class metrics are saved in `models/model_metadata.json`.
