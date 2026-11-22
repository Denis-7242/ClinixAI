# ClinixAI Knowledge Base Guide

## Scope

This educational knowledge base currently covers malaria, typhoid fever,
influenza, the common cold, pneumonia, urinary tract infection,
gastroenteritis, hypertension, COVID-19, and tuberculosis. It is not a
diagnostic tool and is not exhaustive.

## Schema

- `Source`: cited publisher, title, URL, and year.
- `Symptom`: stable id, display name, and a plain-language question.
- `SymptomWeight`: symptom id, weight from 0 to 1, and an optional specificity note.
- `RedFlag`: combination of symptoms and an urgency message.
- `Disease`: description, prior probability, severity, symptoms, risk factors,
  next-step category, advice, source ids, and an `illustrative` flag.

The valid next-step categories are `self_care`, `see_clinician`,
`urgent_care`, and `emergency`.

## Adding a condition

Add or edit entries only in `knowledge_base/knowledge_base.json`; no Python
code change is required. Add any source under `sources`, any symptoms under
`symptoms`, and then add the disease with valid symptom and source ids. Run
`load_knowledge_base()` and the knowledge base tests.

## Illustrative values

The symptom weights, disease prior probabilities, and specificity assumptions
in this prototype are not population estimates or clinical thresholds. They
are educational, illustrative values used for ranking and may be inaccurate.
The following are illustrative:

- Every symptom weight in every bundled disease.
- Every disease `prior_probability`.
- The use of these weights and priors for scoring without real-world calibration.
- The source-linked descriptions and symptoms do not make the uncalibrated
  weights clinically validated.

Every bundled disease has `illustrative: true`. For a future sourced
calibrated estimate, update the disease or affected values and document the
citation and estimation method before clearing `illustrative`.
