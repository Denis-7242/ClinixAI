# Safety and Ethics

ClinixAI's safety layer runs independently of scoring and cannot be
suppressed by low model confidence.

The red flags are evaluated from the knowledge-base rules. A rule fires only
when every required symptom is explicitly marked present. Unknown answers do
not count as present. A red flag never prevents scoring; it is returned with
the assessment so the interface can show urgent guidance first.

Input validation is defensive and never raises for malformed user data. Invalid
input is reported and is not persisted or scored.

Red flags in the current knowledge base cover chest pain with breathlessness,
fever with stiff neck, confusion with fever, blood in stool or vomit, and
severe breathing difficulty. The last is represented by a single
shortness-of-breath symptom and is intentionally broad: assessment users
should seek emergency care based on severity and rapid worsening.

## Disclaimer

> ClinixAI is an educational and research prototype. It does not provide medical diagnoses, treatment, or professional medical advice. Results are informational only and may be inaccurate or incomplete. If you are experiencing a medical emergency or severe symptoms, contact your local emergency services or a qualified healthcare professional immediately.

ClinixAI stores only anonymous assessment data and provides deletion controls.
