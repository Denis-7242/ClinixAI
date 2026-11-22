# Architecture

## Data flow

```text
Streamlit UI
    |
    v
Assessment service
    |
    +--> Input validation
    +--> Red-flag safety (independent)
    +--> Expert scoring
    +--> Math posterior scoring
    +--> ML probability prediction
    |
    v
60% math / 40% ML reconciliation
    |
    v
Database repository
```

The UI does not import database or internal scoring modules. It uses service
pass-through functions for assessments and history.

If the saved ML model is unavailable or mismatched, reconciliation uses math
scores only and emits a warning. Red flags remain attached to the result and
are presented first by the UI.
