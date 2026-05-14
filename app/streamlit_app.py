import streamlit as st
import sys
import os
import uuid
from fpdf import FPDF
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables with override
load_dotenv(override=True)

# Initialize Firebase
if not firebase_admin._apps:
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.warning(f"Failed to initialize Firebase: {e}")
    else:
        st.warning("Firebase credentials not found or invalid. Persistence is disabled.")

def get_db():
    if firebase_admin._apps:
        return firestore.client()
    return None

db = get_db()

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
    st.stop()

if not tavily_key or tavily_key == "your_tavily_api_key_here":
    st.error("❌ **TAVILY_API_KEY is missing or invalid!**")
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
st.subheader("An AI-powered agentic researcher built with LangGraph & Groq/Gemini")

# Initialize Session State
if "report" not in st.session_state:
    st.session_state.report = None
if "final_state" not in st.session_state:
    st.session_state.final_state = None
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# On load: check if session_id exists in URL and restore state
if "session_id" in st.query_params:
    url_session_id = st.query_params["session_id"]
    if st.session_state.session_id != url_session_id:
        st.session_state.session_id = url_session_id
        if db:
            doc_ref = db.collection("sessions").document(url_session_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                st.session_state.topic = data.get("topic", "")
                st.session_state.report = data.get("final_report", "")
                st.session_state.final_state = data
                st.success("Session restored from Firebase!")

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
        sources_count = len(fs.get("scraped_content", {})) or len(fs.get("retrieved_chunks", {}))
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
            
            # Share button
            if st.button("🔗 Share Report"):
                if db and st.session_state.session_id:
                    db.collection("sessions").document(st.session_state.session_id).update({
                        "public": True
                    })
                    st.success("Report is now public!")
                    st.info("You can now share this URL!")
    else:
        st.info("Run a research topic to see statistics.")

    st.markdown("---")
    st.title("🕒 Recent Research")
    if db:
        try:
            recent_sessions = db.collection("sessions").order_by("updated_at", direction=firestore.Query.DESCENDING).limit(5).stream()
            for s in recent_sessions:
                s_data = s.to_dict()
                s_id = s.id
                s_topic = s_data.get("topic", "Unknown Topic")
                if st.button(f"📄 {s_topic}", key=f"recent_{s_id}"):
                    st.query_params["session_id"] = s_id
                    st.rerun()
        except Exception as e:
            st.error("Could not fetch recent sessions.")

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
        
        # Generate new session ID
        new_session_id = str(uuid.uuid4())
        st.session_state.session_id = new_session_id
        st.query_params["session_id"] = new_session_id
        
        initial_state = {
            "topic": topic_input,
            "sub_questions": [],
            "search_results": [],
            "scraped_content": {},
            "contradictions": [],
            "retrieved_chunks": [],
            "final_report": "",
            "status": "Starting research process...",
            "current_step": "START",
            "complexity_score": 5,
            "search_expanded": False,
            "rewrite_count": 0
        }
        
        progress_bar = st.progress(0)
        
        # Dynamic step counting based on graph execution
        estimated_steps = 8 
        step_idx = 0
        
        current_state = initial_state.copy()
        
        with st.status("Agentic Research in Progress...", expanded=True) as status_box:
            try:
                for output in research_app.stream(initial_state):
                    for node_name, state_update in output.items():
                        current_state.update(state_update)
                        
                        step_idx += 1
                        progress_bar.progress(min(step_idx / estimated_steps, 1.0))
                        
                        status_msg = state_update.get("status", f"Completed {node_name}")
                        st.write(f"✅ **{node_name.capitalize()}**: {status_msg}")
                        
                        # Save state to Firestore
                        if db:
                            db.collection("sessions").document(new_session_id).set({
                                "topic": current_state.get("topic", topic_input),
                                "status": status_msg,
                                "current_step": node_name,
                                "final_report": current_state.get("final_report", ""),
                                "updated_at": firestore.SERVER_TIMESTAMP,
                                "public": False
                            }, merge=True)
                        
                st.session_state.final_state = current_state
                st.session_state.report = current_state.get("final_report", "")
                
                status_box.update(label="Research Complete!", state="complete", expanded=False)
                progress_bar.progress(1.0)
                st.success(f"Successfully generated report on: {topic_input}")
            except Exception as e:
                status_box.update(label=f"Error: {e}", state="error")
                st.error(f"Error during graph execution: {e}")

if st.session_state.report:
    st.markdown("---")
    st.markdown(st.session_state.report)
