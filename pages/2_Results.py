"""Results and explanation page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from services.assessment_service import DISCLAIMER_FULL, DISCLAIMER_SHORT

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
st.warning(DISCLAIMER_SHORT)
st.title("Results")

result = st.session_state.get("latest_assessment")
if not result:
    st.info("Complete an assessment before viewing results.")
    st.stop()
if not result["valid"]:
    st.error("This assessment is invalid.")
    for error in result["errors"]:
        st.write(error)
    st.stop()

if result["red_flag_triggered"]:
    st.error(result["red_flag_message"])

if result["models_disagree"]:
    st.warning("The math and ML rankings differ; these are informational suggestions.")

for item in result["results"][:10]:
    with st.expander(f"{item['disease_name']} — confidence {item['confidence']:.3f}"):
        explanation = item["explanation"]
        matched = explanation["symptoms_matched"]
        contradicted = explanation["symptoms_contradicted"]
        st.write(
            "Matched symptoms: " + (", ".join(matched) if matched else "none")
        )
        st.write(
            "Contradicted expected symptoms: "
            + (", ".join(contradicted) if contradicted else "none")
        )
        st.write("Suggested next step: " + item["advice"])

top = result["results"][:5]
chart = pd.DataFrame(
    {
        "Condition": [item["disease_name"] for item in top],
        "Final score": [item["final_score"] for item in top],
    }
)
st.plotly_chart(px.bar(chart, x="Final score", y="Condition", orientation="h"))

st.subheader("Suggested follow-up questions")
if result["suggested_questions"]:
    for question in result["suggested_questions"]:
        st.write(question["question"])
else:
    st.write("No additional questions are suggested.")

csv = pd.DataFrame(result["results"]).to_csv(index=False)
st.download_button("Download CSV", csv, "clinixai_results.csv", "text/csv")
st.caption(DISCLAIMER_FULL)
