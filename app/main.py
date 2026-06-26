import streamlit as st

st.set_page_config(
    page_title="MRI Ops Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏥 MRI Operations Intelligence Platform")
st.markdown("""
Welcome to the MRI Operations Intelligence Platform — an end-to-end analytics
system for improving MRI scheduling accuracy and operational decision-making.

**Navigate using the sidebar to explore:**
- 📊 Executive Overview
- 🔬 Procedure & Scanner Performance
- 🤖 Model Performance
- ✅ Data Quality & Assumptions
- 💬 AI Assistant
""")

st.info("Select a page from the sidebar to get started.")