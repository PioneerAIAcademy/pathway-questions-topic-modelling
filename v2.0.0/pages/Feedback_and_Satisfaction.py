"""
Feedback & Satisfaction Page - User feedback and engagement analytics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css, BYU_COLORS
from utils.data_loader import ensure_data_loaded

# Configure page settings
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def normalize_feedback_label(value):
    """Normalize feedback values into helpful/unhelpful buckets."""
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {'good', 'helpful', 'thumbs_up', 'positive', '1', 'true', 'yes'}:
        return 'helpful'
    if text in {'bad', 'unhelpful', 'thumbs_down', 'negative', '-1', 'false', 'no'}:
        return 'unhelpful'
    return None


def extract_feedback_reason(row: pd.Series):
    """Get feedback reason from new feedback_comment field or legacy user_feedback text."""
    comment = row.get('feedback_comment', None)
    if pd.notna(comment) and str(comment).strip() != '':
        return str(comment).strip()

    value = row.get('user_feedback', None)
    if pd.notna(value):
        text = str(value).strip()
        if ':' in text:
            reason = text.split(':', 1)[1].strip()
            return reason if reason else None

    return None


def main():
    st.title("📝 Feedback & Satisfaction")
    st.markdown("*Simple user feedback and engagement overview*")
    st.markdown("---")

    # Ensure data is loaded
    ensure_data_loaded()

    df = st.session_state['merged_df'].copy()
    raw_data = st.session_state.get('raw_data', {})

    if df.empty:
        st.warning("⚠️ No data available.")
        st.stop()

    has_sessions = 'session_id' in df.columns and df['session_id'].notna().any()
    has_users = 'user_id' in df.columns and df['user_id'].notna().any()
    has_feedback = 'user_feedback' in df.columns and df['user_feedback'].notna().any()
    has_general_feedback = 'general_feedback' in raw_data and not raw_data['general_feedback'].empty

    if not has_sessions and not has_users and not has_feedback and not has_general_feedback:
        st.info("""
        ### ℹ️ No feedback data available yet

        This page will populate once users start interacting with the chatbot
        and sending feedback.
        """)
        st.stop()

    # ── KPI Cards ──
    st.markdown("## 📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if has_users:
            unique_users = df['user_id'].nunique()
            st.metric("👥 Unique Users", f"{unique_users:,}")

    with col2:
        if has_sessions:
            unique_sessions = df['session_id'].nunique()
            st.metric("💬 Unique Sessions", f"{unique_sessions:,}")

    with col3:
        if has_sessions:
            questions_per_session = df[df['session_id'].notna()].groupby('session_id').size()
            avg_per_session = questions_per_session.mean() if not questions_per_session.empty else 0
            st.metric("📊 Avg Q/Session", f"{avg_per_session:.1f}")

    with col4:
        if has_feedback:
            normalized = df['user_feedback'].apply(normalize_feedback_label)
            total_feedback = normalized.notna().sum()
            st.metric("⭐ Feedback Entries", f"{total_feedback:,}")

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2 = st.tabs([
        "👥 User & Session Analytics",
        "📋 General Feedback"
    ])

    # ── TAB 1: User & Session Analytics ──
    with tab1:
        if not has_sessions and not has_users and not has_feedback:
            st.info("No user, session, or feedback data available in the current dataset.")
        else:
            st.markdown("### 👥 User & Session Analytics")

            # Session-level indicators (chart removed for simplicity)
            if has_sessions:
                session_df = df[df['session_id'].notna()].copy()
                session_counts = session_df.groupby('session_id').size().reset_index(name='question_count')

                st.markdown("#### 💬 Session Indicators")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Single-Question Sessions", f"{(session_counts['question_count'] == 1).sum()}")
                with col2:
                    st.metric("Multi-Question Sessions", f"{(session_counts['question_count'] > 1).sum()}")
                with col3:
                    st.metric("Avg Questions/Session", f"{session_counts['question_count'].mean():.1f}")
                with col4:
                    st.metric("Max Questions in Session", f"{session_counts['question_count'].max()}")

                st.markdown("---")

            # User engagement chart
            if has_users:
                user_df = df[df['user_id'].notna()].copy()
                user_counts = user_df.groupby('user_id').size().reset_index(name='question_count')

                st.markdown("#### 🧑 User Engagement")
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=user_counts['question_count'],
                    nbinsx=min(30, max(1, int(user_counts['question_count'].max()))),
                    marker=dict(color=BYU_COLORS['secondary']),
                    hovertemplate='Questions: %{x}<br>Users: %{y}<extra></extra>'
                ))
                fig.update_layout(
                    title="Distribution of Questions per User",
                    xaxis_title="Number of Questions",
                    yaxis_title="Number of Users",
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch', key="questions_per_user")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Tracked Users", f"{user_counts.shape[0]:,}")
                with col2:
                    st.metric("Avg Questions/User", f"{user_counts['question_count'].mean():.1f}")
                with col3:
                    st.metric("One-Time Users", f"{(user_counts['question_count'] == 1).sum():,}")
                with col4:
                    st.metric("Repeat Users", f"{(user_counts['question_count'] > 1).sum():,}")

                st.markdown("---")

            # Feedback quality summary
            if has_feedback:
                st.markdown("#### ⭐ Response Quality")
                feedback_df = df[df['user_feedback'].notna()].copy()
                feedback_df['feedback_norm'] = feedback_df['user_feedback'].apply(normalize_feedback_label)
                feedback_df = feedback_df[feedback_df['feedback_norm'].notna()]

                if feedback_df.empty:
                    st.info("Feedback entries exist, but none could be interpreted as Good/Bad yet.")
                else:
                    total_feedback = len(feedback_df)
                    helpful_count = (feedback_df['feedback_norm'] == 'helpful').sum()
                    unhelpful_count = (feedback_df['feedback_norm'] == 'unhelpful').sum()

                    helpful_rate = helpful_count / total_feedback * 100
                    unhelpful_rate = unhelpful_count / total_feedback * 100

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Feedback", f"{total_feedback:,}")
                    with col2:
                        st.metric("Helpful Rate", f"{helpful_rate:.1f}%", delta=f"{helpful_count:,} responses")
                    with col3:
                        st.metric("Unhelpful Rate", f"{unhelpful_rate:.1f}%", delta=f"{unhelpful_count:,} responses")

                    # Show reasons users gave for unhelpful responses
                    feedback_df['feedback_reason'] = feedback_df.apply(extract_feedback_reason, axis=1)
                    unhelpful_with_reason = feedback_df[
                        (feedback_df['feedback_norm'] == 'unhelpful') &
                        (feedback_df['feedback_reason'].notna())
                    ].copy()

                    if not unhelpful_with_reason.empty:
                        st.markdown("#### 🗒️ Unhelpful Feedback Reasons")
                        reason_cols = ['timestamp', 'question', 'feedback_reason']
                        available_reason_cols = [c for c in reason_cols if c in unhelpful_with_reason.columns]
                        reason_view = unhelpful_with_reason[available_reason_cols].copy()
                        if 'question' in reason_view.columns:
                            reason_view['question'] = reason_view['question'].astype(str).str.slice(0, 140)
                        reason_view = reason_view.rename(columns={
                            'question': 'Question',
                            'timestamp': 'Timestamp',
                            'feedback_reason': 'Reason'
                        })
                        st.dataframe(reason_view, width='stretch', hide_index=True)

            # Sessions over time
            if has_sessions and 'timestamp' in df.columns:
                st.markdown("---")
                st.markdown("#### 📈 Sessions Over Time")
                session_time = df[df['session_id'].notna()].copy()
                session_time['date'] = pd.to_datetime(session_time['timestamp'], format='ISO8601', errors='coerce').dt.date
                daily_sessions = session_time.groupby('date')['session_id'].nunique().reset_index(name='sessions')

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_sessions['date'],
                    y=daily_sessions['sessions'],
                    mode='lines+markers',
                    line=dict(color=BYU_COLORS['primary'], width=2),
                    hovertemplate='%{x}<br>Sessions: %{y}<extra></extra>'
                ))
                fig.update_layout(
                    title="Daily Unique Sessions",
                    xaxis_title="Date",
                    yaxis_title="Unique Sessions",
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch', key="sessions_over_time")

    # ── TAB 2: General Feedback ──
    with tab2:
        if not has_general_feedback:
            st.info("""
            No general feedback submissions yet.

            When users submit general feedback through the chatbot's feedback form,
            it will appear here as a searchable table.
            """)
        else:
            st.markdown("### 📋 General Feedback Submissions")

            gf_df = raw_data['general_feedback'].copy()
            st.metric("Total Submissions", f"{len(gf_df):,}")

            # Keep table simple: hide technical/redundant columns
            hidden_cols = ['id', 'trace_id', 'name', 'output', 'tags']
            display_cols = [c for c in gf_df.columns if c not in hidden_cols]

            search = st.text_input("🔍 Search feedback", placeholder="Type to filter...", key="gf_search")
            if search:
                mask = gf_df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)
                gf_df = gf_df[mask]

            if display_cols:
                st.dataframe(gf_df[display_cols], width='stretch', hide_index=True)
            else:
                st.dataframe(gf_df, width='stretch', hide_index=True)

            if 'timestamp' in gf_df.columns and len(gf_df) > 1:
                st.markdown("#### 📈 Submissions Over Time")
                gf_df['date'] = pd.to_datetime(gf_df['timestamp'], errors='coerce').dt.date
                daily_gf = gf_df.groupby('date').size().reset_index(name='count')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=daily_gf['date'],
                    y=daily_gf['count'],
                    marker=dict(color=BYU_COLORS['primary']),
                    text=daily_gf['count'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Daily Feedback Submissions",
                    xaxis_title="Date",
                    yaxis_title="Submissions",
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch', key="gf_over_time")


if __name__ == "__main__":
    main()
