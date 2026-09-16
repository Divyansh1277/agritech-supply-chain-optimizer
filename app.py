import streamlit as st
from src.visualization.filters import build_sidebar
from src.visualization import pages

st.set_page_config(
    page_title="AgriTech Mandi-to-Market Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.kpi-card {
    background: linear-gradient(135deg, #1a2f1e 0%, #0f1f12 100%);
    border-radius: 12px; padding: 16px 20px; margin: 6px 0;
    border-left: 4px solid #2E8B57; color: #f9fafb;
}
.kpi-value { font-size: 2rem; font-weight: 700; color: #f9fafb; }
.kpi-label { font-size: 0.78rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-delta-pos { color: #10B981; font-size: 0.85rem; }
.kpi-delta-neg { color: #DC143C; font-size: 0.85rem; }
.empty-state { text-align: center; padding: 48px; color: #6B7280; font-size: 1.1rem; }

section[data-testid="stSidebar"] { background: #0f1f12; }
section[data-testid="stSidebar"] * { color: #e5e7eb !important; }
section[data-testid="stSidebar"] .stMultiSelect label, 
section[data-testid="stSidebar"] .stRadio label { color: #9ca3af !important; }

/* Circular AI button at leftmost corner */
.ai-circle-wrap {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding-top: 4px;
}
.ai-circle-wrap button {
    width: 52px !important;
    height: 52px !important;
    min-width: 52px !important;
    max-width: 52px !important;
    min-height: 52px !important;
    max-height: 52px !important;
    border-radius: 50% !important;
    background: linear-gradient(135deg, #059669 0%, #2563EB 100%) !important;
    color: #ffffff !important;
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em !important;
    border: 2px solid rgba(255, 255, 255, 0.4) !important;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0 !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s ease, border-color 0.2s ease !important;
}

.ai-circle-wrap button:hover {
    transform: scale(1.12) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.7) !important;
    border-color: #93C5FD !important;
}

.ai-circle-wrap.active button {
    border: 2.5px solid #34D399 !important;
    box-shadow: 0 0 16px #10B981, 0 0 32px rgba(16, 185, 129, 0.6) !important;
    animation: ai-pulse 2s infinite !important;
}

@keyframes ai-pulse {
    0% { box-shadow: 0 0 12px rgba(16, 185, 129, 0.6); }
    50% { box-shadow: 0 0 26px rgba(37, 99, 235, 0.85); }
    100% { box-shadow: 0 0 12px rgba(16, 185, 129, 0.6); }
}

.ai-circle-wrap button p {
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin: 0 !important;
    line-height: 1 !important;
}

.ai-header-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #f9fafb;
    margin-left: 2px;
    line-height: 1.2;
}
.ai-header-sub {
    font-size: 0.75rem;
    color: #9ca3af;
    margin-left: 2px;
}
</style>
""", unsafe_allow_html=True)

# State initialization
if "is_ai_active" not in st.session_state:
    st.session_state["is_ai_active"] = False

# ─────────────────────────────────────────────────────────────────
# LEFTMOST CORNER NAVIGATION & AI BUTTON
# ─────────────────────────────────────────────────────────────────
NAV_PAGES = [
    "Executive Overview",
    "Price & MSP",
    "Arrivals & Anomalies",
    "Weather Impact",
    "Logistics",
    "Data Quality"
]

def on_nav_change():
    """Switch back to dashboard pages when any navigation item is selected."""
    st.session_state["is_ai_active"] = False

with st.sidebar:
    # 1. Left-most corner: Circular "AI" button + Title Header
    corner_col1, corner_col2 = st.columns([1, 3], vertical_alignment="center")
    
    is_active_class = "active" if st.session_state["is_ai_active"] else ""
    with corner_col1:
        st.markdown(f'<div class="ai-circle-wrap {is_active_class}">', unsafe_allow_html=True)
        ai_clicked = st.button("AI", key="ai_circle_btn", help="Click to open / close AgentIQ Natural Language Assistant")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with corner_col2:
        st.markdown("""
        <div>
            <div class="ai-header-title">🌾 Mandi-to-Market</div>
            <div class="ai-header-sub">TransOrg AgentIQ Datathon</div>
        </div>
        """, unsafe_allow_html=True)

    if ai_clicked:
        st.session_state["is_ai_active"] = not st.session_state["is_ai_active"]
        st.rerun()

    # If AI Agent is currently active, show a badge with return button
    if st.session_state["is_ai_active"]:
        st.info("🤖 **AI Agent Mode Active**")
        if st.button("← Back to Dashboard Pages", key="btn_exit_ai", width="stretch"):
            st.session_state["is_ai_active"] = False
            st.rerun()

    st.markdown("---")

    # 2. Navigation positioned right at top-left corner
    st.markdown("### 🧭 Navigation")
    selected_page = st.radio(
        "Navigate to:",
        NAV_PAGES,
        key="nav_page",
        label_visibility="collapsed",
        on_change=on_nav_change
    )

# 3. Global Filters rendered underneath the navigation
filters = build_sidebar(show_title=False)
compare = st.session_state.get("compare_previous", False)

# ─────────────────────────────────────────────────────────────────
# MAIN PAGE ROUTING
# ─────────────────────────────────────────────────────────────────
page_titles = {
    "Executive Overview": "🌾 Executive Overview",
    "Price & MSP": "💰 Price & MSP Discovery",
    "Arrivals & Anomalies": "📦 Arrivals & Anomalies",
    "Weather Impact": "☁️ Weather Impact",
    "Logistics": "🚚 Logistics Performance",
    "Data Quality": "✅ Data Quality",
    "AI Agent": "🤖 AgentIQ Graph Assistant"
}

if st.session_state["is_ai_active"]:
    st.title("🤖 AgentIQ Graph Assistant")
    pages.page_ai_agent(filters, compare)
else:
    st.title(page_titles.get(selected_page, selected_page))
    if selected_page == "Executive Overview":
        pages.page_executive_overview(filters, compare)
    elif selected_page == "Price & MSP":
        pages.page_price_msp(filters, compare)
    elif selected_page == "Arrivals & Anomalies":
        pages.page_arrivals_anomalies(filters, compare)
    elif selected_page == "Weather Impact":
        pages.page_weather_impact(filters, compare)
    elif selected_page == "Logistics":
        pages.page_logistics(filters, compare)
    elif selected_page == "Data Quality":
        pages.page_data_quality(filters, compare)
