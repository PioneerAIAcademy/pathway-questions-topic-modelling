"""
Configuration settings for BYU Pathway Missionary Question Analysis Dashboard v2.0.0
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Try to import streamlit for secrets (fallback if .env doesn't work)
try:
    import streamlit as st
    _st_available = True
except ImportError:
    _st_available = False

# ============ AWS S3 Configuration ============
# Try .env first, then Streamlit secrets, then empty string
def get_config(key, default=""):
    """Get configuration from .env or Streamlit secrets"""
    # First try environment variable
    value = os.getenv(key, "")
    if value:
        return value
    # Then try Streamlit secrets
    if _st_available:
        try:
            return st.secrets.get(key, default)
        except:
            pass
    return default

AWS_ACCESS_KEY_ID = get_config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_config("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = get_config("AWS_S3_BUCKET", "byupathway-public")
AWS_S3_PREFIX = get_config("AWS_S3_PREFIX", "topic-modeling-data")
AWS_REGION = "us-east-1"

# ============ File Naming Patterns ============
# The notebook outputs these files with timestamp suffixes
FILE_PATTERNS = {
    "similar_questions": "similar_questions_*.parquet",
    "new_topics": "new_topics_*.parquet",
    "pathway_questions_review": "pathway_questions_review_*.parquet",
    "topic_distribution": "topic_distribution_*.parquet",
    "general_feedback": "general_feedback_*.parquet",
    "error_log": "error_log_*.json"
}

# ============ Streamlit Page Configuration ============
PAGE_CONFIG = {
    "page_title": "BYU Pathway - Topic Analysis Dashboard",
    "page_icon": "📊",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ============ Dashboard Default Columns ============
# Columns shown by default in the main table
DEFAULT_VISIBLE_COLUMNS = [
    "input",  # The question
    "timestamp",
    "country",
    "state"
]

# All available columns (user can show/hide these)
ALL_AVAILABLE_COLUMNS = [
    "input",
    "timestamp",
    "country",
    "state",
    "city",
    "matched_topic",
    "matched_subtopic",
    "similarity_score",
    "classification",
    "output",
    "user_feedback",
    "user_language",
    "is_suspicious",
    "cluster_id",
    "topic_keywords",
    "latency",
    "total_cost",
    "session_id",
    "user_id"
]

# Column display names (for better UX)
COLUMN_DISPLAY_NAMES = {
    "input": "Question",
    "timestamp": "Timestamp",
    "country": "Country",
    "state": "State/Province",
    "city": "City",
    "matched_topic": "Matched Topic",
    "matched_subtopic": "Matched Subtopic",
    "similarity_score": "Similarity Score",
    "classification": "Classification",
    "output": "Response",
    "user_feedback": "User Feedback",
    "user_language": "Language",
    "is_suspicious": "Suspicious",
    "cluster_id": "Cluster ID",
    "topic_keywords": "Keywords",
    "latency": "Latency (s)",
    "total_cost": "Cost ($)",
    "session_id": "Session ID",
    "user_id": "User ID"
}

# ============ Data Type Mappings ============
COLUMN_TYPES = {
    "similarity_score": "float",
    "timestamp": "datetime",
    "is_suspicious": "bool",
    "latency": "float",
    "total_cost": "float"
}

# ============ Filter Options ============
CLASSIFICATION_OPTIONS = ["All", "Existing Topic", "New Topic", "Uncategorized"]
SORT_OPTIONS = {
    "Timestamp (Newest First)": ("timestamp", False),
    "Timestamp (Oldest First)": ("timestamp", True),
    "Similarity Score (High to Low)": ("similarity_score", False),
    "Similarity Score (Low to High)": ("similarity_score", True),
    "Country (A-Z)": ("country", True),
    "Country (Z-A)": ("country", False)
}

# ============ Cache Settings ============
CACHE_TTL = 3600  # Cache data for 1 hour (in seconds)

# ============ Styling ============
def get_theme_css(theme='light'):
    """Get theme-specific CSS"""
    if theme == 'dark':
        return """
<style>
    /* ==================== DARK THEME ==================== */
    
    /* Main background - Dark Theme */
    .stApp {
        background-color: #0d1117 !important;
    }
    
    .main {
        background-color: #0d1117 !important;
    }
    
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Metrics - Dark Theme */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #FFB933 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #4caf50 !important;
    }
    
    /* Headers - Dark Theme */
    h1 {
        color: #FFB933 !important;
        font-weight: 700;
    }
    
    h2 {
        color: #FFB933 !important;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    h3, h4 {
        color: #b0b0b0 !important;
        font-weight: 500;
    }
    
    /* Sidebar - Dark Theme */
    /* Slightly lighter than main background so controls stand out */
    [data-testid="stSidebar"] {
        background-color: #121418 !important; /* lighter than #0d1117 */
        border-right: 1px solid rgba(255,255,255,0.03) !important;
    }

    /* Sidebar content text */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e6e6e6 !important;
    }

    /* Sidebar navigation items */
    [data-testid="stSidebar"] a, 
    [data-testid="stSidebar"] .css-1d391kg {
        color: #cfe8ff !important; /* subtle bluish highlight */
    }

    /* Sidebar section labels */
    [data-testid="stSidebar"] label {
        color: #b8c3cc !important;
    }
    
    /* General text color for dark mode */
    p, span, div {
        color: #e0e0e0 !important;
    }

    /* Top banner selectors (from inspector) */
    header.stAppHeader, .stAppToolbar, .stAppHeader {
        background-color: #0b0f12 !important;
        color: #e6e6e6 !important;
        border-bottom: 1px solid rgba(255,255,255,0.03) !important;
    }
    
    /* Info/Success/Warning boxes - Dark Theme */
    [data-testid="stAlert"] {
        background-color: #1a2332 !important;
        color: #e0e0e0 !important;
    }
    
    /* Buttons - Dark Theme */
    /* Very high-specificity selectors to override Streamlit's generated classes and inline-ish styles */
    :root [data-testid="stAppViewContainer"] [data-testid="stButton"] > button,
    :root [data-testid="stAppViewContainer"] .stButton > button,
    body [data-testid="stSidebar"] .stButton > button,
    body [data-testid="stSidebar"] button,
    [class^="css-"] .stButton > button,
    [class*="css-"] .stButton > button,
    [class^="css-"] button[data-baseweb],
    button[role="button"],
    input[type="button"],
    input[type="submit"],
    .stButton > button,
    .stButton button,
    .stDownloadButton > button {
        background-color: rgba(0,0,0,0.48) !important; /* stronger darker card */
        color: #fafbfc !important; /* very light text for max contrast */
        font-weight: 600 !important;
        border-radius: 6px !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        padding: 0.55rem 1.1rem !important;
        box-shadow: none !important;
        transition: all 0.16s ease-in-out !important;
    }

    /* Sidebar-only even stronger background to ensure separation from main */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button {
        background-color: rgba(0,0,0,0.55) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.02) !important;
    }

    /* Hover / focus states keep BYU gold accent but readable on dark bg */
    :root [data-testid="stAppViewContainer"] .stButton > button:hover,
    :root [data-testid="stAppViewContainer"] .stButton > button:focus,
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] button:hover,
    .stDownloadButton > button:hover,
    button[role="button"]:hover,
    input[type="submit"]:hover,
    input[type="button"]:hover {
        background-color: rgba(255,185,51,0.10) !important; /* more visible gold tint */
        color: #FFB933 !important;
        border-color: rgba(255,185,51,0.20) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
    }

    /* Disabled states */
    :root [data-testid="stAppViewContainer"] .stButton > button[disabled],
    :root [data-testid="stAppViewContainer"] .stButton > button[aria-disabled="true"],
    [data-testid="stSidebar"] .stButton > button[disabled],
    [data-testid="stSidebar"] .stButton > button[aria-disabled="true"],
    button[disabled],
    input[disabled] {
        background-color: rgba(255,255,255,0.02) !important;
        color: rgba(255,255,255,0.35) !important;
        border-color: rgba(255,255,255,0.02) !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
    }

    /* Primary filled buttons keep BYU gold */
    :root .stButton > button.primary, :root .stButton > button[data-primary="true"],
    .stButton > button.primary, .stButton > button[data-primary="true"] {
        background-color: #FFB933 !important;
        color: #081224 !important;
        border: none !important;
    }

    :root .stButton > button.primary:hover, :root .stButton > button[data-primary="true"]:hover,
    .stButton > button.primary:hover, .stButton > button[data-primary="true"]:hover {
        background-color: #ffca5f !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* Final catch-all: force all button-like elements inside the app and sidebar */
    [data-testid="stAppViewContainer"] button,
    [data-testid="stAppViewContainer"] button[class*="css-"],
    [data-testid="stAppViewContainer"] button[style],
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] button[class*="css-"],
    [data-testid="stSidebar"] button[style],
    [data-testid="stAppViewContainer"] [role="button"],
    [data-testid="stSidebar"] [role="button"],
    [data-testid="stAppViewContainer"] input[type="button"],
    [data-testid="stAppViewContainer"] input[type="submit"],
    [data-testid="stSidebar"] input[type="button"],
    [data-testid="stSidebar"] input[type="submit"] {
        background-color: rgba(0,0,0,0.55) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.02) !important;
        box-shadow: none !important;
        padding: 0.45rem 0.9rem !important;
    }
    
    /* Download button - Dark Theme */
    .stDownloadButton > button {
        background-color: #FFB933 !important;
        color: #002E5D !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #ffc44d !important;
    }
    
    /* Tables & chart backgrounds - Dark Theme */
    .dataframe {
        font-size: 0.9rem;
        background-color: #17181a !important; /* slightly darker */
        color: #e6e6e6 !important;
    }
    /* Plotly charts (divs) - give them a slightly darker panel */
    .js-plotly-plot, .plotly, [data-testid="stPlotlyChart"] {
        background-color: #0f1214 !important;
        border-radius: 8px !important;
    }
    
    /* Text inputs - Dark Theme */
    [data-testid="stTextInput"] input {
        background-color: #262626 !important;
        color: #e0e0e0 !important;
        border-color: #404040 !important;
    }
    
    /* Select boxes / Dropdowns - Dark Theme */
    /* Control (the closed select) */
    [data-testid="stSelectbox"] {
        color: #e6e6e6 !important;
    }
    [data-testid="stSelectbox"] .stSelectbox,
    [data-testid="stSelectbox"] div[role="button"],
    [data-testid="stSelectbox"] select,
    [data-testid="stSelectbox"] .css-1d391kg,
    [data-testid="stSelectbox"] .css-1wa3eu0-placeholder {
        background-color: rgba(0,0,0,0.50) !important;
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        border-radius: 6px !important;
        padding: 0.45rem 0.8rem !important;
    }

    /* Dropdown panel (the opened options list) */
    [data-testid="stSelectbox"] [role="listbox"],
    [data-testid="stSelectbox"] .css-1b3oln4,
    .stSelectbox [role="listbox"],
    .stSelectbox ul,
    .stSelectbox .css-1t5f0fr {
        background-color: #0f1214 !important; /* panel background */
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6) !important;
    }

    /* Options */
    [data-testid="stSelectbox"] [role="option"],
    .stSelectbox li,
    .stSelectbox .css-1n76uvr {
        color: #dfe7ee !important;
        background-color: transparent !important;
        padding: 0.45rem 0.8rem !important;
    }

    /* Hover and focus on options */
    [data-testid="stSelectbox"] [role="option"]:hover,
    .stSelectbox li:hover,
    .stSelectbox .css-1n76uvr:hover {
        background-color: rgba(255,185,51,0.08) !important; /* gold tint */
        color: #FFB933 !important;
    }

    /* Selected option */
    [data-testid="stSelectbox"] [aria-selected="true"],
    .stSelectbox li[aria-selected="true"] {
        background-color: rgba(255,185,51,0.12) !important;
        color: #FFB933 !important;
    }

    /* Make the caret/chevron visible */
    [data-testid="stSelectbox"] svg,
    [data-testid="stSelectbox"] .css-8mmkcg svg {
        fill: #e6e6e6 !important;
        color: #e6e6e6 !important;
    }

    /* Portal/overlay dropdowns often get rendered at body level with generated css- classes.
       Force any listbox/menu panels appended to body to be dark so large dropdowns are not white. */
    body div[role="listbox"],
    body .react-select__menu,
    body [class*="react-select__menu"],
    body [class*="css-"] [role="listbox"],
    body [class*="css-"] .react-select__menu,
    body .css-1b3oln4,
    body .css-1n76uvr,
    body .css-1t5f0fr,
    body .css-1pahdxg-control,
    body .css-1wa3eu0 {
        background-color: #0b0f12 !important; /* darker than before */
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        box-shadow: 0 12px 36px rgba(0,0,0,0.75) !important;
    }

    /* Options inside portal panels */
    body [role="option"],
    body .react-select__option,
    body [class*="css-"] [role="option"],
    body .css-1n76uvr {
        background-color: transparent !important;
        color: #dfe7ee !important;
    }

    body [role="option"]:hover,
    body .react-select__option--is-focused,
    body [class*="css-"] [role="option"]:hover,
    body .css-1n76uvr:hover {
        background-color: rgba(255,185,51,0.10) !important;
        color: #FFB933 !important;
    }

    /* Strong descendant overrides: force any nested children inside dropdown panels to inherit dark bg and light text.
       This addresses components that apply backgrounds/colors to inner elements (e.g., generated css-* children). */
    body [role="listbox"],
    body [role="listbox"] *,
    body [class*="react-select__menu"],
    body [class*="react-select__menu"] *,
    body [class*="css-"] [role="listbox"],
    body [class*="css-"] [role="listbox"] *,
    [data-testid="stSelectbox"],
    [data-testid="stSelectbox"] *,
    .stSelectbox [role="listbox"],
    .stSelectbox [role="listbox"] * {
        background-color: #0b0f12 !important;
        color: #e6e6e6 !important;
    }

    /* Aggressive catch-all: any element with a 'css-' class anywhere inside body or inside a selectbox will be darkened.
       This helps override components that render inner white cards using generated classes. */
    body [class*="css-"] *,
    [data-testid="stSelectbox"] [class*="css-"] *,
    .stSelectbox [class*="css-"] * {
        background-color: #0b0f12 !important;
        color: #e6e6e6 !important;
    }

    /* Specific: force native select/option elements and multiselect option chips to dark */
    [data-testid="stSelectbox"] select,
    [data-testid="stSelectbox"] option,
    .stSelectbox select,
    .stSelectbox option,
    [data-testid="stMultiselect"] select,
    [data-testid="stMultiselect"] option,
    .stMultiselect select,
    .stMultiselect option,
    .stMultiSelect, .stMultiSelect * {
        background-color: #0b0f12 !important;
        color: #e6e6e6 !important;
    }

    /* Calendar / date picker popups (common libs Streamlit may use) */
    body .flatpickr-calendar,
    body .flatpickr-wrapper,
    body .react-datepicker,
    body .react-datepicker__popper,
    body .react-datepicker__triangle,
    body .react-datepicker__month-container,
    body .rdp,
    body .rdp * {
        background-color: #0b0f12 !important;
        color: #e6e6e6 !important;
        border: 1px solid rgba(255,255,255,0.03) !important;
        box-shadow: 0 12px 36px rgba(0,0,0,0.75) !important;
    }

    /* Calendar day cells and hover/selected states */
    body .flatpickr-day,
    body .react-datepicker__day,
    body .rdp-day {
        background-color: transparent !important;
        color: #dfe7ee !important;
    }

    body .flatpickr-day:hover,
    body .react-datepicker__day:hover,
    body .react-datepicker__day--selected,
    body .react-datepicker__day--keyboard-selected,
    body .rdp-day:hover,
    body .rdp-day_selected {
        background-color: rgba(255,185,51,0.12) !important;
        color: #FFB933 !important;
    }
    
    /* Expander - Dark Theme */
    [data-testid="stExpander"] {
        background-color: #262626 !important;
        border-color: #404040 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
    else:
        # Light theme (default)
        return """
<style>
    /* ==================== LIGHT THEME ==================== */
    
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Metrics - Light Theme */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        color: #002E5D !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666 !important;
    }
    
    /* Headers - Light Theme */
    h1 {
        color: #002E5D !important;
        font-weight: 700;
    }
    
    h2 {
        color: #002E5D !important;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    
    h3, h4 {
        color: #666 !important;
        font-weight: 500;
    }
    
    /* Sidebar - Light Theme */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    
    /* Buttons - Light Theme */
    .stButton > button {
        background-color: #002E5D !important;
        color: white !important;
        font-weight: 500;
        border-radius: 4px;
        border: none;
        padding: 0.5rem 2rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #004080 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Download button - Light Theme */
    .stDownloadButton > button {
        background-color: #002E5D !important;
        color: white !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #004080 !important;
    }
    
    /* Tables - Light Theme */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""

# Keep CUSTOM_CSS for backward compatibility (defaults to light theme)
CUSTOM_CSS = get_theme_css('light')

# ============ Chart Colors ============
BYU_COLORS = {
    "primary": "#002E5D",  # BYU Navy
    "secondary": "#FFB933",  # BYU Gold
    "accent1": "#0062B8",  # BYU Blue
    "accent2": "#C5050C",  # BYU Red
    "neutral": "#666666",
    "light": "#F5F5F5"
}

CHART_COLOR_PALETTE = [
    "#002E5D", "#FFB933", "#0062B8", "#C5050C", 
    "#5D7B9D", "#FFD700", "#4A90E2", "#E74C3C",
    "#95A5A6", "#F39C12", "#3498DB", "#E67E22"
]
