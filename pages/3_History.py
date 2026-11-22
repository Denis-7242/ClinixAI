"""Anonymous assessment history page."""

import streamlit as st

from services.assessment_service import (
    DISCLAIMER_SHORT,
    delete_assessment,
    delete_all_assessments,
    get_history,
)

st.set_page_config(page_title="History", page_icon="🗂️", layout="wide")
st.warning(DISCLAIMER_SHORT)
st.title("Assessment History")

history = get_history()
if not history:
    st.info("No saved assessments.")
else:
    for session in history:
        with st.expander(
            f"{session['created_at']} — {session['id']} "
            f"{'Red flag' if session['red_flag_triggered'] else ''}"
        ):
            st.write("Knowledge base:", session["kb_version"])
            st.write("Model:", session["model_version"])
            if st.button("Delete this assessment", key=f"delete_{session['id']}"):
                delete_assessment(session["id"])
                st.rerun()

st.divider()
confirm = st.checkbox("I confirm deletion of all locally saved assessment data")
if st.button("Delete all my data", disabled=not confirm):
    delete_all_assessments()
    st.success("All assessment data deleted.")
    st.rerun()
