"""Guided and free-text symptom assessment page."""

import streamlit as st

from services.assessment_service import (
    DISCLAIMER_SHORT,
    get_all_symptom_questions,
    parse_free_text,
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
input_method = st.radio(
    "How would you like to enter symptoms?",
    ["Guided questions", "Describe your symptoms"],
    horizontal=True,
)

if input_method == "Describe your symptoms":
    st.subheader("Describe your symptoms")
    description = st.text_area(
        "Describe what you are experiencing",
        max_chars=1000,
        key="free_text_description",
    )
    if st.button("Understand my symptoms"):
        parsed = parse_free_text(description)
        st.session_state["parsed_free_text"] = {
            "symptoms": parsed.symptoms,
            "unrecognized_phrases": parsed.unrecognized_phrases,
            "warnings": parsed.warnings,
        }

    parsed_data = st.session_state.get("parsed_free_text")
    if parsed_data is not None:
        for warning in parsed_data["warnings"]:
            st.warning(warning)
        if parsed_data["unrecognized_phrases"]:
            st.write("Unrecognized phrases (not used in scoring):")
            for phrase in parsed_data["unrecognized_phrases"]:
                st.write(f"- {phrase}")

        st.subheader("Confirm detected symptoms")
        st.caption(
            "Review and edit every detected symptom before selecting Assess. "
            "Unrecognized phrases are not included in scoring."
        )
        confirmed_answers: list[dict[str, object]] = []
        with st.form("free_text_confirmation"):
            for item in parsed_data["symptoms"]:
                question = item["symptom_id"].replace("_", " ").capitalize()
                st.markdown(f"**{question}**")
                choices = ["Not sure", "Yes", "No"]
                initial = (
                    "Yes"
                    if item["present"] is True
                    else "No"
                    if item["present"] is False
                    else "Not sure"
                )
                choice = st.radio(
                    f"Confirm {question}",
                    choices,
                    index=choices.index(initial),
                    horizontal=True,
                    key=f"free_choice_{item['symptom_id']}",
                )
                present = True if choice == "Yes" else False if choice == "No" else None
                severity_options = [None] + list(range(1, 11))
                initial_severity = item["severity"]
                severity_index = (
                    severity_options.index(initial_severity)
                    if initial_severity in severity_options
                    else 0
                )
                severity = st.selectbox(
                    f"Severity for {question} (1 mild to 10 severe)",
                    severity_options,
                    index=severity_index,
                    key=f"free_severity_{item['symptom_id']}",
                )
                duration = st.number_input(
                    f"Duration in days for {question}",
                    min_value=0,
                    max_value=3650,
                    value=int(item["duration_days"] or 0),
                    step=1,
                    key=f"free_duration_{item['symptom_id']}",
                )
                confirmed_answers.append(
                    {
                        "symptom_id": item["symptom_id"],
                        "present": present,
                        "severity": severity,
                        "duration_days": int(duration),
                    }
                )
            assess_text = st.form_submit_button("Assess")

        if assess_text:
            with st.spinner("Running safety and assessment checks..."):
                try:
                    result = run_assessment(confirmed_answers, age_group, sex)
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
else:
    answers: list[dict[str, object]] = []
    with st.form("guided_assessment"):
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
