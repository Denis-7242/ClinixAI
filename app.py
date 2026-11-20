
import streamlit as st

st.set_page_config(
    page_title="ClinixAI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application branding
st.title("🩺 ClinixAI")
st.caption(
    "Intelligent Clinical Decision Support System"
)

st.sidebar.title("ClinixAI")
st.sidebar.caption("AI-powered healthcare research")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Symptom Assessment",
        "Expert System",
        "Machine Learning",
        "Model Evaluation",
        "About"
    ]
)

if page == "Dashboard":
    st.title("Welcome to ClinixAI")

    st.write(
        "An educational artificial intelligence "
        "platform combining knowledge-based reasoning "
        "and machine learning."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("AI Components", "2")
    col2.metric("Expert Rules", "0")
    col3.metric("Trained Models", "0")

    st.info(
        "Project initialization successful. "
        "The intelligent components will be developed next."
    )

elif page == "Symptom Assessment":
    st.title("Symptom Assessment")
    st.write("The symptom assessment module is under development.")

elif page == "Expert System":
    st.title("Knowledge-Based Expert System")
    st.write("The inference engine is under development.")

elif page == "Machine Learning":
    st.title("Machine Learning")
    st.write("The machine learning module is under development.")

elif page == "Model Evaluation":
    st.title("Model Evaluation")
    st.write("Model performance analysis will appear here.")

elif page == "About":
    st.title("About ClinixAI")
    st.write(
        "ClinixAI is an academic AI project demonstrating "
        "expert systems, machine learning and explainable reasoning."
    )

    st.warning(
        "This is an educational prototype, not a substitute "
        "for professional medical assessment."
    )
