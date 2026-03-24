"""
Calendar Analytics Page - Academic calendar question analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css, BYU_COLORS, CHART_COLOR_PALETTE
from utils.data_loader import ensure_data_loaded

# Configure page settings
st.set_page_config(**PAGE_CONFIG)

if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def main():
    st.title("📅 Calendar Analytics")
    st.markdown("*Academic calendar question patterns, success rates, and usage insights*")
    st.markdown("---")

    ensure_data_loaded()

    df = st.session_state['merged_df'].copy()

    if df.empty:
        st.warning("No data available.")
        st.stop()

    has_calendar = 'is_calendar_question' in df.columns and df['is_calendar_question'].any()

    if not has_calendar:
        st.info("""
        ### No calendar data available yet

        Calendar analytics require data processed after the calendar pipeline was
        deployed (March 19, 2026). Run the notebook with recent Langfuse trace data
        to populate this page.
        """)
        st.stop()

    cal_df = df[df['is_calendar_question'] == True].copy()
    rag_df = df[(df.get('source_type', pd.Series(['rag'] * len(df))) == 'rag')]
    total = len(df)
    cal_count = len(cal_df)
    rag_count = total - cal_count

    # ── KPI Cards ──
    st.markdown("## Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Calendar Questions", f"{cal_count:,}",
                   delta=f"{cal_count / total * 100:.1f}% of all questions")

    with col2:
        if 'calendar_pipeline_status' in cal_df.columns:
            success = (cal_df['calendar_pipeline_status'] == 'success').sum()
            rate = success / cal_count * 100 if cal_count > 0 else 0
            st.metric("Success Rate", f"{rate:.1f}%",
                       delta=f"{success:,} successful")
        else:
            st.metric("Success Rate", "N/A")

    with col3:
        if 'calendar_cache_hit' in cal_df.columns:
            cache_hits = cal_df['calendar_cache_hit'].sum()
            cache_rate = cache_hits / cal_count * 100 if cal_count > 0 else 0
            st.metric("Cache Hit Rate", f"{cache_rate:.1f}%",
                       delta=f"{int(cache_hits)} cached")
        else:
            st.metric("Cache Hit Rate", "N/A")

    with col4:
        st.metric("RAG Questions", f"{rag_count:,}",
                   delta=f"{rag_count / total * 100:.1f}% of all questions")

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2, tab3 = st.tabs([
        "📊 Question Breakdown",
        "⚡ Performance",
        "📋 Calendar Questions Table"
    ])

    # ── TAB 1: Question Breakdown ──
    with tab1:
        col_left, col_right = st.columns(2)

        with col_left:
            # Query type distribution
            if 'calendar_query_type' in cal_df.columns:
                st.markdown("### Query Types")
                type_counts = cal_df['calendar_query_type'].value_counts().reset_index()
                type_counts.columns = ['Query Type', 'Count']

                fig = go.Figure(data=[go.Pie(
                    labels=type_counts['Query Type'],
                    values=type_counts['Count'],
                    hole=0.4,
                    marker=dict(colors=CHART_COLOR_PALETTE[:len(type_counts)]),
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
                )])
                fig.update_layout(height=350, showlegend=False,
                                   title="Calendar Query Types")
                st.plotly_chart(fig, width='stretch', key="cal_query_types_pie")

                st.markdown("**Query type descriptions:**")
                type_info = {
                    'block': 'Single block dates (e.g., "When does Block 3 start?")',
                    'semester': 'Full semester overview (e.g., "Show me Winter 2026")',
                    'deadline': 'Specific deadline (e.g., "Registration deadline Block 2")',
                    'graduation': 'Graduation/commencement dates',
                }
                for qt, desc in type_info.items():
                    count = (cal_df['calendar_query_type'] == qt).sum()
                    if count > 0:
                        st.markdown(f"- **{qt}**: {count} — {desc}")

        with col_right:
            # Season distribution
            if 'calendar_season' in cal_df.columns:
                st.markdown("### Seasons Asked About")
                season_counts = cal_df['calendar_season'].dropna().value_counts().reset_index()
                season_counts.columns = ['Season', 'Count']

                season_colors = {
                    'winter': '#1E88E5',
                    'spring': '#43A047',
                    'fall': '#E65100',
                }

                if not season_counts.empty:
                    fig = go.Figure(data=[go.Bar(
                        x=season_counts['Season'],
                        y=season_counts['Count'],
                        marker=dict(color=[season_colors.get(s, BYU_COLORS['primary'])
                                           for s in season_counts['Season']]),
                        text=season_counts['Count'],
                        textposition='outside',
                    )])
                    fig.update_layout(height=350, showlegend=False,
                                       title="Questions by Season",
                                       xaxis_title="Season", yaxis_title="Count")
                    st.plotly_chart(fig, width='stretch', key="cal_seasons_bar")

            # Block distribution
            if 'calendar_block_number' in cal_df.columns:
                st.markdown("### Blocks Asked About")
                block_counts = cal_df['calendar_block_number'].dropna().astype(int).value_counts().sort_index().reset_index()
                block_counts.columns = ['Block', 'Count']

                if not block_counts.empty:
                    fig = go.Figure(data=[go.Bar(
                        x=[f"Block {b}" for b in block_counts['Block']],
                        y=block_counts['Count'],
                        marker=dict(color=BYU_COLORS['primary']),
                        text=block_counts['Count'],
                        textposition='outside',
                    )])
                    fig.update_layout(height=300, showlegend=False,
                                       title="Questions by Block",
                                       xaxis_title="Block", yaxis_title="Count")
                    st.plotly_chart(fig, width='stretch', key="cal_blocks_bar")

        st.markdown("---")

        # Specific deadlines asked about
        if 'calendar_specific_deadline' in cal_df.columns:
            deadline_df = cal_df[cal_df['calendar_specific_deadline'].notna()]
            if len(deadline_df) > 0:
                st.markdown("### Specific Deadlines Asked About")
                deadline_counts = deadline_df['calendar_specific_deadline'].value_counts().reset_index()
                deadline_counts.columns = ['Deadline Type', 'Count']

                fig = go.Figure(data=[go.Bar(
                    x=deadline_counts['Deadline Type'],
                    y=deadline_counts['Count'],
                    marker=dict(color=BYU_COLORS['secondary']),
                    text=deadline_counts['Count'],
                    textposition='outside',
                )])
                fig.update_layout(height=350, showlegend=False,
                                   title="Most Asked Deadline Types",
                                   xaxis_title="Deadline", yaxis_title="Count")
                st.plotly_chart(fig, width='stretch', key="cal_deadlines_bar")

        # Timeline of calendar questions
        if 'timestamp' in cal_df.columns:
            st.markdown("### Calendar Questions Over Time")
            cal_df['date'] = pd.to_datetime(cal_df['timestamp'], errors='coerce').dt.date
            daily = cal_df.groupby('date').size().reset_index(name='count')

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily['date'], y=daily['count'],
                mode='lines+markers', fill='tozeroy',
                line=dict(color=BYU_COLORS['primary'], width=2),
                fillcolor='rgba(0, 46, 93, 0.1)',
            ))
            fig.update_layout(height=300, showlegend=False,
                               title="Daily Calendar Question Volume",
                               xaxis_title="Date", yaxis_title="Questions")
            st.plotly_chart(fig, width='stretch', key="cal_timeline")

    # ── TAB 2: Performance ──
    with tab2:
        has_latency = 'latency' in cal_df.columns and cal_df['latency'].notna().any()
        has_cost = 'total_cost' in cal_df.columns and cal_df['total_cost'].notna().any()

        if has_latency:
            st.markdown("### Calendar vs RAG Latency")
            cal_lat = cal_df[cal_df['latency'] > 0]['latency']
            rag_lat = rag_df[rag_df['latency'] > 0]['latency'] if 'latency' in rag_df.columns else pd.Series(dtype=float)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Calendar Avg", f"{cal_lat.mean():.2f}s" if len(cal_lat) > 0 else "N/A")
                st.metric("Calendar P95", f"{cal_lat.quantile(0.95):.2f}s" if len(cal_lat) > 0 else "N/A")
            with col2:
                st.metric("RAG Avg", f"{rag_lat.mean():.2f}s" if len(rag_lat) > 0 else "N/A")
                st.metric("RAG P95", f"{rag_lat.quantile(0.95):.2f}s" if len(rag_lat) > 0 else "N/A")
            with col3:
                if len(cal_lat) > 0 and len(rag_lat) > 0:
                    diff = cal_lat.mean() - rag_lat.mean()
                    st.metric("Latency Difference",
                              f"{abs(diff):.2f}s",
                              delta=f"Calendar is {'slower' if diff > 0 else 'faster'}")

            st.markdown("---")

            # Pipeline status breakdown
            if 'calendar_pipeline_status' in cal_df.columns:
                st.markdown("### Pipeline Status")
                status_counts = cal_df['calendar_pipeline_status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']

                status_colors = {
                    'success': '#43A047',
                    'error': '#E53935',
                    'skipped_no_args': '#FFA726',
                    'no_nodes': '#78909C',
                }

                fig = go.Figure(data=[go.Bar(
                    x=status_counts['Status'],
                    y=status_counts['Count'],
                    marker=dict(color=[status_colors.get(s, '#9E9E9E') for s in status_counts['Status']]),
                    text=status_counts['Count'],
                    textposition='outside',
                )])
                fig.update_layout(height=300, showlegend=False,
                                   title="Pipeline Execution Status",
                                   xaxis_title="Status", yaxis_title="Count")
                st.plotly_chart(fig, width='stretch', key="cal_status_bar")

        if has_cost:
            st.markdown("### Calendar vs RAG Cost")
            cal_cost = cal_df[cal_df['total_cost'] > 0]['total_cost']
            rag_cost_data = rag_df[rag_df['total_cost'] > 0]['total_cost'] if 'total_cost' in rag_df.columns else pd.Series(dtype=float)

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Calendar Total Cost", f"${cal_cost.sum():.4f}" if len(cal_cost) > 0 else "N/A")
                st.metric("Calendar Avg Cost", f"${cal_cost.mean():.6f}" if len(cal_cost) > 0 else "N/A")
            with col2:
                st.metric("RAG Total Cost", f"${rag_cost_data.sum():.4f}" if len(rag_cost_data) > 0 else "N/A")
                st.metric("RAG Avg Cost", f"${rag_cost_data.mean():.6f}" if len(rag_cost_data) > 0 else "N/A")

    # ── TAB 3: Questions Table ──
    with tab3:
        st.markdown("### Calendar Questions")

        display_cols = ['question', 'timestamp', 'calendar_query_type', 'calendar_card_title',
                         'calendar_pipeline_status', 'latency', 'total_cost', 'country']
        available = [c for c in display_cols if c in cal_df.columns]

        if available:
            display = cal_df[available].copy()
            display = display.sort_values('timestamp', ascending=False) if 'timestamp' in display.columns else display

            st.dataframe(display, width='stretch', height=500, hide_index=True)

            st.markdown(f"**Total:** {len(display):,} calendar questions")
        else:
            st.info("No calendar question data to display.")


if __name__ == "__main__":
    main()
