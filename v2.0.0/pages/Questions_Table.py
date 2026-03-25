"""
Questions Table Page - Interactive data table with filters
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CLASSIFICATION_OPTIONS, PAGE_CONFIG, get_theme_css
from utils.data_loader import filter_dataframe, ensure_data_loaded


# Fallback / refusal patterns for detecting unanswered questions.
# Used as a runtime fallback when the pre-computed is_not_answered column is missing.
# Covers: chatbot refusals, "who to contact" redirects, "contexts do not contain" responses,
# localization-manager fallback messages (20 languages).
FALLBACK_MESSAGE_PATTERNS = [
    # English refusal patterns (from chatbot engine)
    r"I only have information about BYU-Pathway Worldwide",
    r"I'm not sure about that, but",
    r"Sorry, I don't have information on that",
    r"Sorry, I don't know",
    r"Sorry, I can't answer that",
    r"I'm sorry, but I can't assist with that request",
    r"Sorry, I can't comply with that request",
    r"could you please rephrase your question",
    r"I can't assist with that",
    # LLM-generated refusals when no relevant nodes found
    r"The contexts do not (?:contain|provide|specify)",
    r"The provided contexts do not (?:contain|provide|specify)",
    r"The information (?:regarding|about) .{0,80} is not (?:available|specified)",
    r"is not available in the (?:retrieved nodes|provided contexts)",
    # Spanish
    r"Lo siento, no puedo responder eso",
    r"No tengo información",
    r"No estoy seguro",
    # Portuguese
    r"Desculpe, não posso responder isso",
    r"Não tenho informações",
    # French
    r"Désolé, je ne peux pas répondre",
    r"Je ne suis pas sûr",
    # Indonesian
    r"Saya tidak yakin",
    # German
    r"Entschuldigung, ich kann das nicht beantworten",
    # Italian
    r"Scusa, non posso rispondere a questo",
    # Russian
    r"Извините, я не могу на это ответить",
    # Chinese
    r"抱歉，我无法回答",
    # Japanese
    r"申し訳ございませんが、それにはお答えできません",
    # Korean
    r"답변할 수 없습니다",
    # Arabic
    r"آسف، لا أستطيع الإجابة",
    # Thai
    r"ขอโทษ ฉันไม่สามารถตอบได้",
    # Vietnamese
    r"Xin lỗi, tôi không thể trả lời điều đó",
    # Turkish
    r"Üzgünüm, buna cevap veremem",
    # Polish
    r"Przepraszam, nie mogę na to odpowiedzieć",
]


def is_unanswered_question(output_text: str) -> bool:
    """Check if the chatbot output contains a refusal / 'cannot answer' message.

    This is used as a runtime fallback when the pre-computed is_not_answered
    column is not available in the data.
    """
    if pd.isna(output_text) or not isinstance(output_text, str):
        return False
    for pattern in FALLBACK_MESSAGE_PATTERNS:
        if re.search(pattern, output_text, re.IGNORECASE):
            return True
    return False

# Configure page settings (needed for direct page access)
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def main():
    st.title("📋 Questions Table")
    st.markdown("*Interactive table with advanced filtering*")
    st.markdown("---")
    
    # Ensure data is loaded (handles page refresh)
    ensure_data_loaded()
    
    df = st.session_state['merged_df'].copy()
    
    # Filters in main page area
    st.markdown("## 🔍 Filters")
    
    # First row: Classification and Date Range
    col1, col2 = st.columns(2)
    
    with col1:
        classification = st.selectbox(
            "Classification",
            CLASSIFICATION_OPTIONS,
            key="classification_filter",
            help="Filter by question classification"
        )
    
    with col2:
        if 'timestamp' in df.columns:
            min_date = df['timestamp'].min().date() if not df['timestamp'].isna().all() else datetime.now().date()
            max_date = df['timestamp'].max().date() if not df['timestamp'].isna().all() else datetime.now().date()
            
            date_range = st.date_input(
                "📅 Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="date_range_filter",
                help="Filter questions by date range"
            )
            
            if len(date_range) == 2:
                date_filter = date_range
            else:
                date_filter = None
        else:
            date_filter = None
    
    # Second row: Search
    st.markdown("#### Search in Questions")
    search_query = st.text_input(
        "Search in questions",
        placeholder="Enter keywords...",
        help="Search for specific text in questions",
        label_visibility="collapsed",
        key="search_query_filter"
    )
    
    # Third row: Country and Similarity filters
    col1, col2 = st.columns(2)
    
    with col1:
        if 'country' in df.columns:
            countries = sorted(df['country'].dropna().unique().tolist())
            selected_countries = st.multiselect(
                "🌍 Countries",
                countries,
                key="countries_filter",
                help="Filter by country (leave empty for all)"
            )
            country_filter = selected_countries if selected_countries else None
        else:
            country_filter = None
    
    with col2:
        if 'similarity_score' in df.columns:
            min_similarity = st.slider(
                "📊 Minimum Similarity Score",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.05,
                key="similarity_filter",
                help="Filter by minimum similarity score (for existing topics)"
            )
        else:
            min_similarity = None
    
    # Fourth row: Unanswered questions filter
    st.markdown("#### 🚫 Unanswered Questions")
    with st.expander("ℹ️ What counts as 'not answered'?"):
        st.markdown("""
        A question is flagged as **not answered** when the chatbot replies with a refusal
        or fallback message like *"I don't have that information"* or *"please check Who to Contact."*
        This means the knowledge base didn't have what the student needed. Tracking these helps
        us find gaps in our content.
        """)
    show_unanswered_only = st.checkbox(
        "Show only questions the chatbot couldn't answer",
        value=False,
        key="unanswered_filter",
        help="Filter to show only questions where the chatbot responded with a hardcoded fallback message (detected across 20 languages)"
    )
    
    # Clear filters button
    if st.button("🔄 Clear All Filters", width='content'):
        # Clear all filter widget states
        for key in ['classification_filter', 'search_query_filter', 'countries_filter', 'similarity_filter', 'date_range_filter', 'unanswered_filter']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    
    # Apply filters
    filtered_df = filter_dataframe(
        df,
        classification=classification,
        date_range=date_filter,
        countries=country_filter,
        search_query=search_query if search_query else None,
        min_similarity=min_similarity
    )
    
    # Apply unanswered questions filter if checkbox is checked
    if show_unanswered_only:
        if 'is_not_answered' in filtered_df.columns:
            # Use pre-computed column from notebook pipeline
            filtered_df = filtered_df[filtered_df['is_not_answered'] == True].copy()
        elif 'output' in filtered_df.columns:
            # Runtime fallback for older data without pre-computed column
            filtered_df['_unanswered'] = filtered_df['output'].apply(is_unanswered_question)
            filtered_df = filtered_df[filtered_df['_unanswered'] == True].copy()
            filtered_df = filtered_df.drop(columns=['_unanswered'])
    
    # Results count
    st.markdown(f"### 📊 Showing {len(filtered_df):,} of {len(df):,} questions")
    
    # Display table with Streamlit's native interactive dataframe
    if not filtered_df.empty:
        # Create a display copy and remove newlines from output column for clean CSV downloads
        display_df = filtered_df.copy()

        # Hide internal/technical columns from stakeholder-facing table
        hidden_columns = ['tags', 'scores', 'release', 'role']
        display_df = display_df.drop(columns=[c for c in hidden_columns if c in display_df.columns], errors='ignore')

        if 'output' in display_df.columns:
            display_df['output'] = display_df['output'].astype(str).str.replace('\n', ' ', regex=False).str.replace('\r', ' ', regex=False)
        
        st.dataframe(
            display_df,
            width='stretch',
            height=600,
            hide_index=True
        )
        
        # Summary statistics
        with st.expander("📊 Summary Statistics"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Rows", f"{len(filtered_df):,}")
            
            with col2:
                if 'country' in filtered_df.columns:
                    st.metric("Unique Countries", filtered_df['country'].nunique())
            
            with col3:
                if 'similarity_score' in filtered_df.columns:
                    avg_sim = filtered_df['similarity_score'].mean()
                    st.metric("Avg Similarity", f"{avg_sim:.3f}")
            
            with col4:
                if 'classification' in filtered_df.columns:
                    new_topic_pct = (filtered_df['classification'] == 'New Topic').sum() / len(filtered_df) * 100
                    st.metric("New Topics %", f"{new_topic_pct:.1f}%")
        
        # Additional unanswered questions statistics
        if 'is_not_answered' in filtered_df.columns or 'output' in filtered_df.columns:
            with st.expander("🚫 Unanswered Questions Analysis"):
                # Prefer pre-computed column, fallback to runtime detection
                if 'is_not_answered' in filtered_df.columns:
                    unanswered_mask = filtered_df['is_not_answered'] == True
                else:
                    unanswered_mask = filtered_df['output'].apply(is_unanswered_question)
                unanswered_count = unanswered_mask.sum()
                unanswered_pct = (unanswered_count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Unanswered Questions",
                        f"{unanswered_count:,}",
                        delta=f"{unanswered_pct:.1f}% of filtered data"
                    )
                
                with col2:
                    answered_count = len(filtered_df) - unanswered_count
                    st.metric(
                        "Successfully Answered",
                        f"{answered_count:,}",
                        delta=f"{100-unanswered_pct:.1f}% success rate"
                    )
                
                # Show sample fallback messages if any
                if unanswered_count > 0:
                    st.markdown("**Sample Fallback Messages:**")
                    sample_fallbacks = filtered_df[unanswered_mask]['output'].head(3)
                    for idx, msg in enumerate(sample_fallbacks, 1):
                        if pd.notna(msg):
                            # Truncate long messages
                            display_msg = msg[:200] + "..." if len(str(msg)) > 200 else msg
                            st.text(f"{idx}. {display_msg}")

    
    else:
        st.info("ℹ️ No data to display with current filters. Try adjusting your filters.")
    
    # Tips
    st.markdown("---")
    st.info("""
    ### 💡 Tips for Using the Table

    - **Filter** questions by classification, date, country, or similarity score
    - **Search** for specific keywords in questions
    - **Find unanswered questions** using the checkbox to detect fallback responses across 20+ languages
    - **Sort** columns by clicking on the column headers
    - **Resize** columns by dragging the column borders
    - All operations happen **instantly** without page refresh!

    #### About Unanswered Questions Detection

    The system detects when the chatbot couldn't answer a question by looking for refusal patterns in the response. Detection covers:

    - **Explicit refusals:** "I only have information about BYU-Pathway Worldwide..."
    - **Knowledge gaps:** "I'm not sure about that, but you can check Who to Contact..."
    - **Context failures:** "The contexts do not contain information about..."
    - **Localized refusals** in 20+ languages (Spanish, Portuguese, French, etc.)
    """)


if __name__ == "__main__":
    main()
