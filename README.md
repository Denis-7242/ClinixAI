# ClinixAI

ClinixAI is an educational clinical decision-support prototype. It combines a
versioned knowledge base, independent red-flag safety checks, forward-chaining
expert scores, a Naive Bayes-style mathematical model, synthetic ML predictions,
anonymous SQLite history, and a Streamlit interface.

## Features

- 10-condition knowledge base with 20 symptoms and 5 red flags
- Independent urgent-symptom detection before and alongside scoring
- JSON-serializable explanations for every ranked condition
- Logistic Regression and Random Forest synthetic-data comparison
- Anonymous session history and deletion controls
- CSV result download and an educational-only results page

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Train the model

```bash
python -m machine_learning.train_model
```

Training uses a seeded, synthetic dataset generated from the knowledge base.
The generated model is for internal consistency demonstration only.

## Run

```bash
streamlit run app.py
```

Open the URL shown by Streamlit, normally `http://localhost:8501`.

## Test

```bash
pytest
pytest --cov=mathematics --cov=expert_system --cov=safety --cov=knowledge_base
```

## Architecture

```text
Streamlit pages
      |
      v
services.assessment_service
      |
      +--> safety (validation + red flags)
      +--> expert_system
      +--> mathematics
      +--> machine_learning
      +--> database.repository
```

See [architecture](docs/architecture.md) and the detailed guides in `docs/`.

## Project structure

```text
knowledge_base/  versioned JSON and validation
safety/          independent red-flag and input checks
expert_system/   weighted forward-chaining scoring
mathematics/     log-space Naive-Bayes-style posterior
machine_learning/ synthetic training and inference
services/        only application orchestration entry point
database/        SQLAlchemy anonymous session storage
pages/           Streamlit Assessment, Results, History, and Safety
tests/           unit and integration tests
docs/            implementation and limitations
```

## Limitations

Priors and symptom weights are illustrative. The condition list is small and
closed-world. The ML dataset is synthetic and generated from the same knowledge
base, so its performance does not represent real-world accuracy. ClinixAI may
return incomplete or incorrect possibilities.

## Safety statement

> ClinixAI is an educational and research prototype. It does not provide medical diagnoses, treatment, or professional medical advice. Results are informational only and may be inaccurate or incomplete. If you are experiencing a medical emergency or severe symptoms, contact your local emergency services or a qualified healthcare professional immediately.

## License

No release license has been assigned to this project. It is intended for
educational and research use.
