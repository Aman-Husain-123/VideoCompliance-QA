import streamlit as st
import uuid
import os
import json
import logging
from dotenv import load_dotenv

# Load dependencies
load_dotenv(override=True)

# Import the workflow graph
from backend.src.graph.workflow import app as compliance_graph

# Configure logging to suppress verbose output in the UI
logging.basicConfig(level=logging.ERROR)

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Brand Guardian AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a premium look
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #0e1117;
    }
    
    /* Title and Header */
    .stHeadingContainer h1 {
        color: #00d4ff;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        text-shadow: 0px 0px 10px rgba(0, 212, 255, 0.3);
    }
    
    /* Result Cards */
    .compliance-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.05);
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    .compliance-card:hover {
        transform: translateY(-5px);
        border-color: #00d4ff;
    }
    
    /* Severity Badges */
    .badge-critical { color: #ff4b4b; font-weight: bold; border: 1px solid #ff4b4b; padding: 2px 8px; border-radius: 4px; }
    .badge-high { color: #ffa500; font-weight: bold; border: 1px solid #ffa500; padding: 2px 8px; border-radius: 4px; }
    .badge-low { color: #00ff00; font-weight: bold; border: 1px solid #00ff00; padding: 2px 8px; border-radius: 4px; }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3233/3233514.png", width=80)
    st.title("Settings")
    
    st.markdown("---")
    video_url = st.text_input(
        "YouTube URL", 
        value="https://youtu.be/dT7S75eYhcQ",
        help="Paste a YouTube video link to audit for compliance."
    )
    
    st.markdown("---")
    st.info("💡 **How it works:** \n\nOur AI extracts audio & on-screen text, then audits it against your brand's regulatory knowledge base using LangGraph.")
    
    if st.button("Reset Session", use_container_width=True):
        st.cache_data.clear()
        st.session_state["results"] = None
        st.rerun()

# ==========================================
# MAIN DASHBOARD
# ==========================================
st.title("🛡️ Brand Guardian AI")
st.subheader("Automated Video Compliance Audit Pipeline")

# Initialize Session State
if "results" not in st.session_state:
    st.session_state["results"] = None

# Input area
cols = st.columns([4, 1])
with cols[0]:
    input_url = st.text_input("Analyze Video Content", value=video_url, label_visibility="collapsed", placeholder="https://www.youtube.com/watch?v=...")
with cols[1]:
    run_btn = st.button("🚀 Run Audit", use_container_width=True, type="primary")

if run_btn:
    session_id = str(uuid.uuid4())
    initial_inputs = {
        "video_url": input_url,
        "video_id": f"vid_{session_id[:8]}",
        "compliance_results": [],
        "errors": []
    }
    
    with st.status("🔍 Auditing Video Pipeline...", expanded=True) as status:
        # Step 1: Ingestion & Indexing
        st.write("📥 Downloading & Extracting Insights (Azure Video Indexer)...")
        # Step 2: Running through the graph
        try:
            final_state = compliance_graph.invoke(initial_inputs)
            st.session_state["results"] = final_state
            status.update(label="✅ Audit Complete!", state="complete", expanded=False)
        except Exception as e:
            status.update(label="❌ Audit Failed", state="error")
            st.error(f"Execution Error: {str(e)}")

# ==========================================
# DISPLAY RESULTS
# ==========================================
if st.session_state["results"]:
    res = st.session_state["results"]
    
    # Header Metrics
    m1, m2, m3 = st.columns(3)
    status_val = res.get("final_status", "UNKNOWN")
    m1.metric("Final Status", status_val, delta=None if status_val == "PASS" else "VIOLATIONS DETECTED", delta_color="inverse")
    m2.metric("Violations Found", len(res.get("compliance_results", [])))
    m3.metric("Video ID", res.get("video_id"))
    
    tab1, tab2, tab3 = st.tabs(["📝 Compliance Report", "🎙️ Transcripts & OCR", "⚙️ Raw Data"])
    
    with tab1:
        st.markdown("### 📋 Detailed Findings")
        
        # Display the Natural Language Summary
        st.success(res.get("final_report", "No report generated."))
        
        # Display individual violations
        violations = res.get("compliance_results", [])
        if violations:
            for issue in violations:
                severity = issue.get('severity', 'LOW').upper()
                badge_class = f"badge-{severity.lower()}"
                
                st.markdown(f"""
                <div class="compliance-card">
                    <span class="{badge_class}">{severity}</span>
                    <h4 style="margin: 10px 0;">{issue.get('category')}</h4>
                    <p style="color: #b9bbbe;">{issue.get('description')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No compliance violations were detected in this video content.")

    with tab2:
        st.markdown("### 🎙️ Extracted Insights")
        col_t, col_o = st.columns(2)
        
        with col_t:
            st.markdown("**Transcript (Speech-to-Text)**")
            st.text_area("Full Transcript", res.get("transcript", "No transcript found."), height=300, disabled=True)
            
        with col_o:
            st.markdown("**On-Screen Text (OCR)**")
            ocrs = res.get("ocr_text", [])
            if ocrs:
                st.write(", ".join(ocrs))
            else:
                st.write("No on-screen text detected.")

    with tab3:
        st.markdown("### ⚙️ Raw System Metadata")
        st.json(res)

else:
    # Empty state
    st.markdown("---")
    st.markdown("<center><h4>👈 Please enter a URL and start the audit in the sidebar</h4></center>", unsafe_allow_html=True)
    st.image("https://img.freepik.com/free-vector/video-upload-concept-illustration_114360-4702.jpg", width=400)
