"""About and safety page."""

import streamlit as st

from services.assessment_service import DISCLAIMER_FULL, DISCLAIMER_SHORT

st.set_page_config(page_title="About and Safety", page_icon="🛡️", layout="wide")
st.warning(DISCLAIMER_SHORT)
st.title("About and Safety")

st.error(DISCLAIMER_FULL)
st.subheader("Limitations")
st.write(
    "ClinixAI is an educational prototype. Symptom weights and prior probabilities "
    "are illustrative, the condition list is small, and the synthetic ML model "
    "does not demonstrate real-world clinical accuracy."
)
st.write(
    "If you are experiencing a medical emergency or severe symptoms, contact "
    "local emergency services or a qualified healthcare professional immediately."
)
