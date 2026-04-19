import streamlit as st
import sys
import os
from fpdf import FPDF
from dotenv import load_dotenv

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables with override
load_dotenv(override=True)

# Startup Check
groq_key = os.getenv("GROQ_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

st.set_page_config(
    page_title="Autonomous Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not groq_key or groq_key == "your_groq_api_key_here":
    st.error("❌ **GROQ_API_KEY is missing or invalid!**")
    st.markdown("""
    Please follow these steps:
    1. Open the `.env` file in the project root.
    2. Replace `your_groq_api_key_here` with your actual Groq API key.
    3. Save the file and refresh this page.
    """)
    st.info("You can get a Groq API key at [console.groq.com](https://console.groq.com/keys).")
    st.stop()

if not tavily_key or tavily_key == "your_tavily_api_key_here":
    st.error("❌ **TAVILY_API_KEY is missing or invalid!**")
    st.markdown("""
    Please follow these steps:
    1. Open the `.env` file in the project root.
    2. Replace `your_tavily_api_key_here` with your actual Tavily API key.
    3. Save the file and refresh this page.
    """)
    st.info("You can get a Tavily API key at [tavily.com](https://tavily.com/).")
    st.stop()

from graph.research_graph import app as research_app

# Custom CSS for chip buttons
st.markdown("""
    <style>
    .stButton>button {
        border-radius: 20px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Autonomous Research Agent")
st.subheader("An AI-powered agentic researcher built with LangGraph & Groq")

# Initialize Session State
if "report" not in st.session_state:
    st.session_state.report = None
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "topic" not in st.session_state:
    st.session_state.topic = ""

def create_pdf(text: str) -> bytes:
    """Helper to convert text to PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    text = text.replace("’", "'").replace("‘", "'").replace("”", '"').replace("“", '"')
    text = text.replace("–", "-").replace("—", "-").replace("…", "...")
    text = text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 7, text)
    return bytes(pdf.output())

# --- Sidebar ---
with st.sidebar:
    st.title("📊 Research Stats")
    
    if st.session_state.final_state:
        fs = st.session_state.final_state
        sources_count = len(fs.get("scraped_content", {}))
        contradictions_count = len(fs.get("contradictions", []))
        
        confidence_score = 100 - (contradictions_count * 15)
        confidence_score = max(min(confidence_score, 100), 10)
        
        st.metric("Sources Analyzed", sources_count)
        st.metric("Contradictions Found", contradictions_count)
        st.metric("Report Confidence", f"{confidence_score}%")
        
        st.markdown("---")
        
        if st.session_state.report:
            pdf_bytes = create_pdf(st.session_state.report)
            st.download_button(
                label="📄 Download Report as PDF",
                data=pdf_bytes,
                file_name=f"Research_Report_{st.session_state.topic.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Run a research topic to see statistics.")

# --- Main Layout ---
st.markdown("### Try an example topic:")
cols = st.columns(4)
topics = ["Quantum Computing", "CRISPR Gene Editing", "Climate Tipping Points", "AGI Timeline Predictions"]

for i, col in enumerate(cols):
    with col:
        if st.button(topics[i], key=f"btn_{i}", use_container_width=True):
            st.session_state.topic = topics[i]
            st.rerun()

topic_input = st.text_input("Enter your research topic:", value=st.session_state.topic)

if st.button("🚀 Run Research", type="primary"):
    if not topic_input:
        st.warning("Please enter a topic.")
    else:
        st.session_state.topic = topic_input
        
        initial_state = {
            "topic": topic_input,
            "sub_questions": [],
            "search_results": [],
            "scraped_content": {},
            "contradictions": [],
            "final_report": "",
            "status": "Starting research process...",
            "current_step": "START"
        }
        
        progress_bar = st.progress(0)
        steps = ["planner", "searcher", "reader", "critic", "writer"]
        current_state = initial_state.copy()
        
        with st.status("Agentic Research in Progress...", expanded=True) as status_box:
            try:
                for output in research_app.stream(initial_state):
                    for node_name, state_update in output.items():
                        current_state.update(state_update)
                        
                        if node_name in steps:
                            idx = steps.index(node_name)
                            progress_bar.progress((idx + 1) / len(steps))
                        
                        status_msg = state_update.get("status", f"Completed {node_name}")
                        st.write(f"✅ **{node_name.capitalize()}**: {status_msg}")
                        
                st.session_state.final_state = current_state
                st.session_state.report = current_state.get("final_report", "")
                
                status_box.update(label="Research Complete!", state="complete", expanded=False)
                progress_bar.empty()
                st.success(f"Successfully generated report on: {topic_input}")
            except Exception as e:
                status_box.update(label=f"Error: {e}", state="error")
                st.error(f"Error during graph execution: {e}")

if st.session_state.report:
    st.markdown("---")
    st.markdown(st.session_state.report)
