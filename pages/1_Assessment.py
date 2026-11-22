"""Guided symptom assessment page."""

import streamlit as st

from services.assessment_service import (
    DISCLAIMER_SHORT,
    get_all_symptom_questions,
    run_assessment,
)

st.set_page_config(page_title="Assessment", page_icon="🩺", layout="wide")
st.warning(DISCLAIMER_SHORT)
st.title("Symptom Assessment")

age_group = st.selectbox(
    "Age group (optional)",
    [None, "under_18", "18-29", "30-49", "50-64", "65_plus", "unknown"],
)
sex = st.selectbox(
    "Sex (optional)",
    [None, "female", "male", "intersex", "prefer_not_to_say", "unknown"],
)

answers: list[dict[str, object]] = []
with st.form("assessment_form"):
    for item in get_all_symptom_questions():
        st.subheader(item["question"])
        choice = st.radio(
            item["symptom_id"],
            ["Not sure", "Yes", "No"],
            horizontal=True,
            label_visibility="collapsed",
            key=f"choice_{item['symptom_id']}",
        )
        present = True if choice == "Yes" else False if choice == "No" else None
        severity_value = st.selectbox(
            "Severity, if applicable (1 mild to 10 severe)",
            [None] + list(range(1, 11)),
            key=f"severity_{item['symptom_id']}",
        )
        duration_value = st.number_input(
            "Duration in days",
            min_value=0,
            max_value=3650,
            value=0,
            step=1,
            key=f"duration_{item['symptom_id']}",
        )
        answers.append(
            {
                "symptom_id": item["symptom_id"],
                "present": present,
                "severity": severity_value,
                "duration_days": int(duration_value) if present is True else None,
            }
        )
    submitted = st.form_submit_button("Assess")

if submitted:
    with st.spinner("Running safety and assessment checks..."):
        try:
            result = run_assessment(answers, age_group, sex)
            st.session_state["latest_assessment"] = result
        except Exception:
            st.error("Assessment could not be completed. Please try again.")
            st.stop()
    if not result["valid"]:
        for error in result["errors"]:
            st.error(error)
    elif result["red_flag_triggered"]:
        st.error(result["red_flag_message"])
    else:
        st.success("Assessment completed.")
        st.page_link("pages/2_Results.py", label="View ranked results")
