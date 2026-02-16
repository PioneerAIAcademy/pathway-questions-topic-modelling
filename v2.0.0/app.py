"""
BYU Pathway Missionary Question Analysis Dashboard v2.0.0
Main Streamlit Application

A professional, scalable dashboard for analyzing student questions and topics.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from config import PAGE_CONFIG, get_theme_css
from utils.data_loader import load_data_from_s3, merge_data_for_dashboard, calculate_kpis, get_latest_file_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_page():
    """Configure Streamlit page settings"""
    st.set_page_config(**PAGE_CONFIG)
    
    # Initialize theme in session state
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    
    # Initialize data loaded flag to prevent multiple loads
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Apply theme-specific CSS
    from config import get_theme_css
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def main():
    """Main application entry point"""
    try:
        configure_page()
        
        # Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("BYU Pathway Missionary Question Analysis Dashboard")
            st.markdown("*Professional insights into missionary questions and topic discovery*")
        
    try:
        with st.spinner("🔄 Loading data from AWS S3..."):
            data = load_data_from_s3()
    except Exception as e:
        st.error(f"❌ **Error loading data from S3:** {str(e)}")
        logger.error(f"S3 data loading error: {e}", exc_info=True)
        st.info("""
        **💡 Troubleshooting steps:**
        1. Check AWS credentials in Streamlit secrets
        2. Verify S3 bucket exists and is accessible
        3. Ensure network connectivity to AWS
        """)
        st.stop
                "https://byu-pathway.brightspotcdn.com/42/2e/4d4c7b10498c84233ae51179437c/byu-pw-icon-gold-rgb-1-1.svg",
                width=100
            )
        
        st.markdown("---")
    
    # Load data
    with st.spinner("🔄 Loading data from AWS S3..."):
        data = load_data_from_s3()
    
    if not data:
        st.error("❌ **No data available.** Please ensure the notebook has uploaded files to S3.")
        st.info("""
        **💡 Tip:** Run the Jupyter notebook to process questions and upload results to S3.
        The dashboard will automatically load the most recent data.
        """)
        st.stop()
    
    # Merge data for dashboard
    merged_df = merge_data_for_dashboard(data)
    
    if merged_df.empty:
        st.warning("⚠️ No question data available in the loaded files.")
        st.stop()
    
    # Calculate KPIs
    kpis = calculate_kpis(merged_df, data)
    
    # Store in session state for use in other pages (always update to ensure fresh data)
    st.session_state['merged_df'] = merged_df
    st.session_state['raw_data'] = data
    st.session_state['kpis'] = kpis
    
    # Success message
    file_info = get_latest_file_info()
    if file_info and 'timestamp' in file_info:
        st.success(f"✅ **Data loaded successfully!** Processing {kpis['total_questions']:,} questions from S3.")
        st.caption(f"📅 Data timestamp: {file_info['timestamp']}")
    else:
        st.success(f"✅ **Data loaded successfully!** Processing {kpis['total_questions']:,} questions from S3.")
    
    # Quick overview
    st.markdown("### 📋 Quick Overview")
    
    from utils.visualizations import create_kpi_cards
    create_kpi_cards(kpis)
    
    st.markdown("---")
    
    # Navigation info
    st.info("""
    ### 🧭 Navigation
    
    Use the sidebar to navigate between different sections:
    
    - **📊 app** (Home): Overview and key metrics
    - **📋 Questions Table**: Interactive table with filters and search
    - **📈 Trends & Analytics**: Detailed visualizations and insights with advanced analytics
    - **🆕 New Topics**: Explore newly discovered topics
    - **📅 Weekly Insights**: Week-by-week topic analysis and trends
    - **🌍 Regional Insights**: Geographic patterns and localization opportunities
    - **💰 Cost & Performance**: Cost evaluation, latency analysis, and operational metrics
    - **📝 Feedback & Satisfaction**: User feedback, sessions, and engagement
    
    💡 **Tip:** All filters and sorting happen instantly without page refresh!
    """)
    
    # Sidebar - Theme toggle and Refresh button at the bottom
    st.s# Clear cache and session state data flags
        st.cache_data.clear()
        st.session_state.data_loaded = False
        logger.info("Data cache cleared by user"")
    
    # Theme toggle
    current_theme = st.session_state.get('theme', 'light')
    theme_label = "🌙 Dark Mode" if current_theme == 'light' else "☀️ Light Mode"
    if st.sidebar.button(theme_label, help="Toggle between light and dark themes", width='stretch'):
        st.session_state.theme = 'dark' if current_theme == 'light' else 'light'
        st.rerun()
    
    # Developer section - Error Report Download
    st.markdown("*For developers*")
    if st.button("📥 Download Error Report", help="Generate and download diagnostic report"):
        from utils.data_loader import generate_error_report
        
        # Generate the error report
        error_report = generate_error_report(
            st.session_state.get('merged_df', merged_df),
            st.session_state.get('raw_data', data)
        )
        
        # Create download button
        st.download_button(
            label="💾 Save Error Report",
            data=error_report,
            file_name=f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            help="Download detailed diagnostic information"
        )
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p><strong>BYU Pathway Worldwide</strong> | Topic Analysis Dashboard v2.0.0</p>
        <p>Powered by AWS S3, OpenAI, and Streamlit</p>
    </div>
    """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"⚠️ **Application Error:** {str(e)}")
        logger.error(f"Application error: {e}", exc_info=True)
        st.info("""
        **💡 The app encountered an unexpected error.**
        
        Try these steps:
        1. Refresh the page
        2. Clear your browser cache
        3. Check the error report for details
        """)
        
        # Still allow error report download even in error state
        if st.button("📥 Download Error Log"):
            st.download_button(
                label="💾 Save Error Log",
                data=str(e),
                file_name=f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


if __name__ == "__main__":
    main()
