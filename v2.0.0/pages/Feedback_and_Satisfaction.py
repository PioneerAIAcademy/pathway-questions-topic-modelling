"""
Feedback & Satisfaction Page - User feedback analysis, scores, and satisfaction metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css, BYU_COLORS, CHART_COLOR_PALETTE
from utils.data_loader import ensure_data_loaded

# Configure page settings
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def parse_scores(scores_val):
    """Parse the scores field (may be JSON string or list)."""
    if pd.isna(scores_val) or scores_val == '' or scores_val == '[]':
        return []
    if isinstance(scores_val, list):
        return scores_val
    if isinstance(scores_val, str):
        try:
            return json.loads(scores_val)
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def parse_tags(tags_val):
    """Parse the tags field (may be JSON string or list)."""
    if pd.isna(tags_val) or tags_val == '' or tags_val == '[]':
        return []
    if isinstance(tags_val, list):
        return tags_val
    if isinstance(tags_val, str):
        try:
            return json.loads(tags_val)
        except (json.JSONDecodeError, TypeError):
            return [t.strip() for t in tags_val.split(',') if t.strip()]
    return []


def safe_hist_bins(series: pd.Series, default: int = 10, max_bins: int = 30) -> int:
    """Return a valid integer bin count for Plotly histograms."""
    if series is None or len(series) == 0:
        return default

    numeric = pd.to_numeric(series, errors='coerce').dropna()
    if numeric.empty:
        return default

    max_value = numeric.max()
    if pd.isna(max_value):
        return default

    try:
        bins = int(max_value)
    except (TypeError, ValueError):
        return default

    if bins < 1:
        return 1

    return min(max_bins, bins)


def main():
    st.title("📝 Feedback & Satisfaction")
    st.markdown("*Analyze user feedback, satisfaction scores, and engagement patterns*")
    st.markdown("---")

    # Ensure data is loaded
    ensure_data_loaded()

    df = st.session_state['merged_df'].copy()
    raw_data = st.session_state.get('raw_data', {})

    if df.empty:
        st.warning("⚠️ No data available.")
        st.stop()

    # Check data availability
    has_scores = 'scores' in df.columns and df['scores'].apply(
        lambda x: len(parse_scores(x)) > 0
    ).any()
    has_tags = 'tags' in df.columns and df['tags'].apply(
        lambda x: len(parse_tags(x)) > 0
    ).any()
    has_sessions = 'session_id' in df.columns and df['session_id'].notna().any()
    has_users = 'user_id' in df.columns and df['user_id'].notna().any()
    has_general_feedback = 'general_feedback' in raw_data and not raw_data['general_feedback'].empty

    if not has_scores and not has_tags and not has_sessions and not has_general_feedback:
        st.info("""
        ### ℹ️ No feedback data available yet

        Feedback tracking was recently added to the chatbot. Once users start
        providing feedback (thumbs up/down), this page will populate with:
        - Satisfaction scores and trends
        - User engagement analytics
        - Feedback breakdown by topic
        - General feedback submissions
        """)
        st.stop()

    # ── KPI Cards ──
    st.markdown("## 📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if has_users:
            unique_users = df['user_id'].nunique()
            st.metric(
                label="👥 Unique Users",
                value=f"{unique_users:,}",
                help="Number of unique users tracked"
            )

    with col2:
        if has_sessions:
            unique_sessions = df['session_id'].nunique()
            st.metric(
                label="💬 Unique Sessions",
                value=f"{unique_sessions:,}",
                help="Number of unique chat sessions"
            )

    with col3:
        if has_sessions:
            questions_per_session = df[df['session_id'].notna()].groupby('session_id').size()
            avg_per_session = questions_per_session.mean()
            st.metric(
                label="📊 Avg Q/Session",
                value=f"{avg_per_session:.1f}",
                help="Average questions per session"
            )

    with col4:
        if has_scores:
            # Count total feedback entries
            total_scores = df['scores'].apply(lambda x: len(parse_scores(x))).sum()
            st.metric(
                label="⭐ Feedback Entries",
                value=f"{total_scores:,}",
                help="Total thumbs up/down feedback submissions"
            )

    st.markdown("---")

    # ── Tabs ──
    tabs = st.tabs([
        "⭐ Feedback Scores",
        "👥 User & Session Analytics",
        "🏷️ Tag Analysis",
        "📋 General Feedback"
    ])

    # ── TAB 1: Feedback Scores ──
    with tabs[0]:
        if not has_scores:
            st.info("""
            No per-question feedback scores have been recorded yet.

            Once users start using the thumbs up/down buttons on chatbot responses,
            score data will appear here.
            """)
        else:
            st.markdown("### ⭐ Per-Question Feedback Scores")

            # Extract scores into rows
            score_rows = []
            for idx, row in df.iterrows():
                scores_list = parse_scores(row.get('scores', ''))
                for score in scores_list:
                    if isinstance(score, dict):
                        score_rows.append({
                            'question_id': row.get('trace_id', idx),
                            'input': row.get('input', ''),
                            'topic': row.get('topic_name', 'Unknown'),
                            'score_name': score.get('name', 'unknown'),
                            'score_value': score.get('value', None),
                            'score_comment': score.get('comment', ''),
                            'timestamp': row.get('timestamp', None)
                        })

            if score_rows:
                scores_df = pd.DataFrame(score_rows)

                # Score distribution
                if 'score_value' in scores_df.columns and scores_df['score_value'].notna().any():
                    st.markdown("#### 📊 Score Distribution")

                    score_counts = scores_df['score_value'].value_counts().sort_index()

                    fig = go.Figure()
                    colors = ['#C5050C' if v <= 0 else '#4caf50' for v in score_counts.index]
                    fig.add_trace(go.Bar(
                        x=[str(v) for v in score_counts.index],
                        y=score_counts.values,
                        marker=dict(color=colors),
                        text=score_counts.values,
                        textposition='outside',
                        hovertemplate='Score: %{x}<br>Count: %{y}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Score Value Distribution",
                        xaxis_title="Score Value",
                        yaxis_title="Count",
                        height=350,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, key="score_distribution")

                # Feedback by score name
                if 'score_name' in scores_df.columns:
                    st.markdown("#### 📋 Feedback by Type")
                    name_counts = scores_df['score_name'].value_counts()

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=name_counts.index,
                        y=name_counts.values,
                        marker=dict(color=BYU_COLORS['primary']),
                        text=name_counts.values,
                        textposition='outside'
                    ))
                    fig.update_layout(
                        title="Feedback Entries by Type",
                        xaxis_title="Feedback Type",
                        yaxis_title="Count",
                        height=350,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, key="feedback_by_type")

                # Feedback trend over time
                if scores_df['timestamp'].notna().any():
                    st.markdown("#### 📈 Feedback Trend Over Time")
                    scores_df['date'] = pd.to_datetime(scores_df['timestamp'], format='ISO8601', errors='coerce').dt.date
                    daily_feedback = scores_df.groupby('date').size().reset_index(name='count')

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=daily_feedback['date'],
                        y=daily_feedback['count'],
                        mode='lines+markers',
                        line=dict(color=BYU_COLORS['primary'], width=2),
                        marker=dict(size=6),
                        hovertemplate='%{x}<br>Feedback: %{y}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Daily Feedback Volume",
                        xaxis_title="Date",
                        yaxis_title="Feedback Count",
                        height=350,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, key="feedback_trend")

                # Feedback by topic
                if 'topic' in scores_df.columns and scores_df['topic'].notna().any():
                    st.markdown("#### 🏷️ Feedback by Topic")
                    topic_feedback = scores_df.groupby('topic').agg(
                        count=('score_value', 'count'),
                        avg_score=('score_value', 'mean')
                    ).sort_values('count', ascending=False).head(15).reset_index()

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=topic_feedback['topic'],
                        x=topic_feedback['count'],
                        orientation='h',
                        marker=dict(color=BYU_COLORS['primary']),
                        hovertemplate='<b>%{y}</b><br>Feedback Count: %{x}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Top 15 Topics with Feedback",
                        xaxis_title="Feedback Count",
                        yaxis_title="",
                        height=500,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, key="feedback_by_topic")

                # Raw feedback table
                with st.expander("📋 All Feedback Entries"):
                    display_cols = ['timestamp', 'input', 'topic', 'score_name', 'score_value', 'score_comment']
                    display_scores = scores_df[[c for c in display_cols if c in scores_df.columns]].copy()
                    if 'input' in display_scores.columns:
                        display_scores['input'] = display_scores['input'].str[:100] + '...'
                    st.dataframe(display_scores, use_container_width=True, hide_index=True)
            else:
                st.info("Score fields exist but no structured feedback data found.")

    # ── TAB 2: User & Session Analytics ──
    with tabs[1]:
        if not has_sessions and not has_users:
            st.info("No user or session data available in the current dataset.")
        else:
            st.markdown("### 👥 User & Session Analytics")

            if has_sessions:
                session_df = df[df['session_id'].notna()].copy()

                # Questions per session distribution
                st.markdown("#### 💬 Questions per Session")
                session_counts = session_df.groupby('session_id').size().reset_index(name='question_count')

                if session_counts.empty:
                    st.info("No session counts available for histogram.")
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=session_counts['question_count'],
                        nbinsx=safe_hist_bins(session_counts['question_count']),
                        marker=dict(color=BYU_COLORS['primary']),
                        hovertemplate='Questions: %{x}<br>Sessions: %{y}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Distribution of Questions per Session",
                        xaxis_title="Number of Questions",
                        yaxis_title="Number of Sessions",
                        height=350,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, key="questions_per_session")

                # Session size stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Single-Question Sessions",
                              f"{(session_counts['question_count'] == 1).sum()}")
                with col2:
                    st.metric("Multi-Question Sessions",
                              f"{(session_counts['question_count'] > 1).sum()}")
                with col3:
                    st.metric("Avg Questions/Session",
                              f"{session_counts['question_count'].mean():.1f}")
                with col4:
                    st.metric("Max Questions in Session",
                              f"{session_counts['question_count'].max()}")

                st.markdown("---")

            if has_users:
                user_df = df[df['user_id'].notna()].copy()

                st.markdown("#### 🧑 User Engagement")

                # Questions per user
                user_counts = user_df.groupby('user_id').size().reset_index(name='question_count')

                if user_counts.empty:
                    st.info("No user counts available for histogram.")
                else:
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(
                        x=user_counts['question_count'],
                        nbinsx=safe_hist_bins(user_counts['question_count']),
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
                    st.plotly_chart(fig, use_container_width=True, key="questions_per_user")

                # User activity stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Tracked Users", f"{user_counts.shape[0]:,}")
                with col2:
                    st.metric("Avg Questions/User", f"{user_counts['question_count'].mean():.1f}")
                with col3:
                    one_time = (user_counts['question_count'] == 1).sum()
                    st.metric("One-Time Users", f"{one_time:,}")
                with col4:
                    repeat = (user_counts['question_count'] > 1).sum()
                    st.metric("Repeat Users", f"{repeat:,}")

                st.markdown("---")

                # Top users table (anonymized)
                with st.expander("📊 Top Users by Activity"):
                    top_users = user_counts.nlargest(20, 'question_count').reset_index(drop=True)
                    top_users.index = top_users.index + 1
                    top_users.columns = ['User ID', 'Questions Asked']
                    # Truncate user IDs for privacy
                    top_users['User ID'] = top_users['User ID'].apply(
                        lambda x: str(x)[:8] + '...' if len(str(x)) > 8 else str(x)
                    )
                    st.dataframe(top_users, use_container_width=True)

            # Session/User over time
            if has_sessions and 'timestamp' in df.columns:
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
                st.plotly_chart(fig, use_container_width=True, key="sessions_over_time")

    # ── TAB 3: Tag Analysis ──
    with tabs[2]:
        if not has_tags:
            st.info("No tag data available in the current dataset.")
        else:
            st.markdown("### 🏷️ Tag Analysis")
            st.markdown("Tags provide structured metadata about each trace (e.g., language, role, feature).")

            # Extract all tags
            all_tags = []
            for tags_val in df['tags']:
                all_tags.extend(parse_tags(tags_val))

            if all_tags:
                tag_counts = pd.Series(all_tags).value_counts().reset_index()
                tag_counts.columns = ['Tag', 'Count']

                # Categorize tags
                tag_categories = {}
                for tag in tag_counts['Tag']:
                    parts = str(tag).split(':')
                    category = parts[0] if len(parts) > 1 else 'other'
                    if category not in tag_categories:
                        tag_categories[category] = []
                    tag_categories[category].append(tag)

                # Tag category breakdown
                st.markdown("#### 📊 Tag Categories")
                category_counts = {cat: len(tags) for cat, tags in tag_categories.items()}
                cat_df = pd.DataFrame(list(category_counts.items()), columns=['Category', 'Unique Tags']).sort_values('Unique Tags', ascending=False)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=cat_df['Category'],
                    y=cat_df['Unique Tags'],
                    marker=dict(color=BYU_COLORS['primary']),
                    text=cat_df['Unique Tags'],
                    textposition='outside'
                ))
                fig.update_layout(
                    title="Tag Categories",
                    xaxis_title="Category",
                    yaxis_title="Unique Tag Values",
                    height=350,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, key="tag_categories")

                # All tags table
                st.markdown("#### 📋 All Tags")
                fig = go.Figure()
                top_tags = tag_counts.head(20)
                fig.add_trace(go.Bar(
                    y=top_tags['Tag'],
                    x=top_tags['Count'],
                    orientation='h',
                    marker=dict(color=BYU_COLORS['secondary']),
                    text=top_tags['Count'],
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
                ))
                fig.update_layout(
                    title="Top 20 Tags by Frequency",
                    xaxis_title="Count",
                    yaxis_title="",
                    height=600,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True, key="top_tags")

                with st.expander("📋 Full Tag Table"):
                    st.dataframe(tag_counts, use_container_width=True, hide_index=True)

                # Language breakdown from tags
                lang_tags = [t for t in all_tags if str(t).startswith('language:')]
                if lang_tags:
                    st.markdown("#### 🌐 Language Distribution (from tags)")
                    lang_counts = pd.Series(lang_tags).value_counts().reset_index()
                    lang_counts.columns = ['Language Tag', 'Count']
                    lang_counts['Language'] = lang_counts['Language Tag'].str.replace('language:', '', regex=False)

                    fig = go.Figure()
                    fig.add_trace(go.Pie(
                        labels=lang_counts['Language'],
                        values=lang_counts['Count'],
                        hole=0.4,
                        marker=dict(colors=CHART_COLOR_PALETTE[:len(lang_counts)]),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Language Distribution",
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True, key="language_dist_tags")

                # Role breakdown from tags
                role_tags = [t for t in all_tags if str(t).startswith('role:')]
                if role_tags:
                    st.markdown("#### 👤 Role Distribution (from tags)")
                    role_counts = pd.Series(role_tags).value_counts().reset_index()
                    role_counts.columns = ['Role Tag', 'Count']
                    role_counts['Role'] = role_counts['Role Tag'].str.replace('role:', '', regex=False)

                    fig = go.Figure()
                    fig.add_trace(go.Pie(
                        labels=role_counts['Role'],
                        values=role_counts['Count'],
                        hole=0.4,
                        marker=dict(colors=CHART_COLOR_PALETTE[:len(role_counts)]),
                        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
                    ))
                    fig.update_layout(
                        title="Role Distribution",
                        height=400,
                    )
                    st.plotly_chart(fig, use_container_width=True, key="role_dist_tags")

    # ── TAB 4: General Feedback ──
    with tabs[3]:
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

            # Display the general feedback table
            display_cols = [c for c in gf_df.columns if c not in ['id', 'trace_id']]
            if display_cols:
                # Search filter
                search = st.text_input("🔍 Search feedback", placeholder="Type to filter...", key="gf_search")
                if search:
                    mask = gf_df.apply(lambda row: search.lower() in str(row.values).lower(), axis=1)
                    gf_df = gf_df[mask]

                st.dataframe(gf_df[display_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(gf_df, use_container_width=True, hide_index=True)

            # Feedback over time if timestamp exists
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
                st.plotly_chart(fig, use_container_width=True, key="gf_over_time")


if __name__ == "__main__":
    main()
