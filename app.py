"""ClinixAI Home page."""

import streamlit as st

from services.assessment_service import DISCLAIMER_SHORT, get_stats

st.set_page_config(page_title="ClinixAI", page_icon="🩺", layout="wide")
st.warning(DISCLAIMER_SHORT)
st.title("ClinixAI")
st.caption("Educational clinical decision-support prototype")
st.write(
    "ClinixAI combines an illustrative knowledge base, safety checks, "
    "expert scoring, and machine-learning ranking. It does not provide diagnoses."
)

try:
    stats = get_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Assessments", stats["total_sessions"])
    col2.metric("Red flags", stats["red_flag_sessions"])
    col3.metric("Average feedback", stats["average_rating"] or "N/A")
except Exception:
    st.error("The local history database could not be loaded.")
