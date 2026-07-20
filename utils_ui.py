import streamlit as st

def inject_custom_css():
    """Injects premium Enterprise Light Mode CSS for a Stripe-like aesthetic."""
    st.markdown("""
        <style>
        /* Import Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Typography & Background */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* App Background */
        .stApp {
            background-color: #f7f9fc !important; 
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e2e8f0;
            padding-top: 1rem;
        }
        [data-testid="stSidebar"] h1 {
            color: #0f172a;
            font-weight: 700;
        }
        
        /* Headers */
        h1, h2, h3, h4 {
            color: #0f172a !important;
            font-weight: 600 !important;
        }

        /* Metric Styling */
        div[data-testid="stMetricValue"] {
            font-weight: 700 !important;
            color: #0f172a !important;
            font-size: 2rem !important;
        }
        div[data-testid="stMetricLabel"] {
            font-weight: 500 !important;
            color: #64748b !important;
            text-transform: uppercase;
            font-size: 0.85rem !important;
            letter-spacing: 0.05em;
        }
        div[data-testid="stMetricDelta"] {
            font-weight: 500 !important;
        }

        /* Streamlit Containers (Floating Cards) */
        div[data-testid="stVerticalBlock"] > div[style*="border-radius"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stVerticalBlock"] > div[style*="border-radius"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04) !important;
            transform: translateY(-2px);
        }

        /* Top padding reduction */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Hide element decorations */
        MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Custom UI classes */
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 0.5rem;
        }
        .advisory-box {
            background-color: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 0 8px 8px 0;
            margin-top: 1rem;
            color: #1e3a8a;
            font-size: 0.95rem;
        }
        .aqi-giant {
            font-size: 6rem;
            font-weight: 800;
            line-height: 1;
            margin: 0;
        }
        .aqi-good { color: #10b981; }
        .aqi-satisfactory { color: #84cc16; }
        .aqi-moderate { color: #f59e0b; }
        .aqi-poor { color: #f97316; }
        .aqi-verypoor { color: #ef4444; }
        .aqi-severe { color: #b91c1c; }
        
        </style>
    """, unsafe_allow_html=True)
