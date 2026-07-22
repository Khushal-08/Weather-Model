import streamlit as st

def inject_custom_css():
    """Injects Dark Navy Mode CSS for a premium dashboard aesthetic."""
    st.markdown("""
        <style>
        /* Import Inter and JetBrains Mono Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700;800&display=swap');
        
        /* Global Typography & Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
            color: #e2e8f0 !important;
        }
        
        /* App Background */
        .stApp {
            background-color: #0b0f19 !important; 
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid #1f2937;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
            color: #f3f4f6 !important;
        }
        
        /* Capitalize Navigation Links */
        [data-testid="stSidebarNav"] span {
            text-transform: capitalize !important;
        }
        
        /* Headers */
        h1, h2, h3, h4 {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Streamlit Containers (Floating Cards) */
        div[data-testid="stVerticalBlock"] > div[style*="border-radius"], .custom-card {
            background: #111827 !important;
            border: 1px solid #1f2937 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stVerticalBlock"] > div[style*="border-radius"]:hover, .custom-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(59, 130, 246, 0.15) !important;
            border-color: #374151 !important;
        }

        /* Micro-interactions & Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in { 
            animation: fadeIn 0.4s ease-out forwards; 
        }

        @keyframes pulseLive {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.4); }
            100% { opacity: 1; transform: scale(1); }
        }
        .live-badge-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: #ef4444;
            border-radius: 50%;
            margin-right: 6px;
            animation: pulseLive 2s infinite;
        }
        .live-badge-text {
            color: #ef4444;
            font-weight: 600;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
        }

        /* Custom HTML KPI Cards */
        .kpi-card {
            background-color: #111827;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            height: 100%;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px rgba(59, 130, 246, 0.15);
            border-color: #374151;
        }
        .kpi-label {
            color: #9ca3af;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .kpi-value {
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-size: clamp(1rem, 1.5vw, 1.8rem);
            font-weight: 700;
            line-height: 1.2;
            word-break: normal;
            overflow-wrap: break-word;
            white-space: normal;
        }
        .kpi-subtext {
            color: #6b7280;
            font-size: 0.8rem;
            margin-top: 0.5rem;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Confidence Progress Bar */
        .confidence-container {
            width: 100%;
            background-color: #1f2937;
            border-radius: 4px;
            height: 6px;
            margin-top: 8px;
            overflow: hidden;
        }
        .confidence-bar {
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-out;
        }

        /* Other Custom UI classes */
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #f3f4f6;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #1f2937;
            padding-bottom: 0.5rem;
        }

        .advisory-box {
            background-color: rgba(30, 58, 138, 0.3);
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin-top: 1rem;
            color: #bfdbfe;
            font-size: 0.95rem;
        }
        
        .action-tag {
            display: inline-block;
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 0.4rem 0.8rem;
            margin-right: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            color: #e5e7eb;
            text-align: center;
        }

        .aqi-giant {
            font-family: 'JetBrains Mono', monospace;
            font-size: 5rem;
            font-weight: 800;
            line-height: 1;
            margin: 0;
        }
        /* AQI Semantic Colors */
        .aqi-good { color: #10b981; }
        .aqi-satisfactory { color: #84cc16; }
        .aqi-moderate { color: #f59e0b; }
        .aqi-poor { color: #f97316; }
        .aqi-verypoor { color: #ef4444; }
        .aqi-severe { color: #ef4444; } /* Adjusted to match Severe Crimson */
        
        .status-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: rgba(17, 24, 39, 0.9);
            backdrop-filter: blur(4px);
            border-top: 1px solid #1f2937;
            padding: 0.5rem 1rem;
            font-size: 0.75rem;
            color: #6b7280;
            display: flex;
            justify-content: space-around;
            z-index: 999;
        }
        
        .block-container {
            padding-bottom: 4rem !important;
            padding-top: 2rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

def create_kpi_card(title, value, subtitle="", icon="📊", trend_arrow=""):
    """Generates HTML for a premium KPI card."""
    trend_html = f"<span style='color: {'#10b981' if '↓' in trend_arrow or 'Good' in trend_arrow else '#ef4444'}; margin-left: 5px; font-size:1rem; vertical-align:middle;'>{trend_arrow}</span>" if trend_arrow else ""
    return f"""
    <div class="kpi-card fade-in">
        <div class="kpi-label"><span>{icon}</span> {title}</div>
        <div class="kpi-value">{value}{trend_html}</div>
        <div class="kpi-subtext">{subtitle}</div>
    </div>
    """

def create_confidence_meter(confidence_pct):
    """Generates a visual progress bar for model confidence."""
    color = "#10b981" if confidence_pct >= 80 else "#fbbf24" if confidence_pct >= 50 else "#ef4444"
    return f"""
    <div class="confidence-container fade-in">
        <div class="confidence-bar" style="width: {confidence_pct}%; background-color: {color};"></div>
    </div>
    <div style="font-size: 0.8rem; color: #9ca3af; margin-top: 4px; text-align: right; font-weight:600;">Confidence: {confidence_pct}%</div>
    """
