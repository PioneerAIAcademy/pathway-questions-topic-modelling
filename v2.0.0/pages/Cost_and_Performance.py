"""
Cost & Performance Page - Cost evaluation, latency analysis, and operational metrics
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

# Configure page settings (needed for direct page access)
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def main():
    st.title("💰 Cost & Performance")
    st.markdown("*Monitor spending, latency, and operational efficiency*")
    st.markdown("---")

    # Ensure data is loaded
    ensure_data_loaded()

    df = st.session_state['merged_df'].copy()

    if df.empty:
        st.warning("⚠️ No data available.")
        st.stop()

    # Check data availability
    has_cost = 'total_cost' in df.columns and df['total_cost'].notna().any()
    has_latency = 'latency' in df.columns and df['latency'].notna().any()

    if not has_cost and not has_latency:
        st.info("""
        ### ℹ️ No cost or latency data available yet

        Cost and latency tracking was recently added to the chatbot. Once you run
        the notebook with newer trace data, this page will populate with:
        - Weekly cost breakdowns
        - Latency distribution and percentiles
        - Cost per question analysis
        - Performance trends over time
        """)
        st.stop()

    # ── KPI Cards ──
    st.markdown("## 📊 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if has_cost:
            total_cost = df['total_cost'].sum()
            st.metric(
                label="💰 Total Cost",
                value=f"${total_cost:.4f}",
                help="Total cost across all traces"
            )

    with col2:
        if has_cost:
            cost_per_q = df[df['total_cost'] > 0]['total_cost'].mean()
            st.metric(
                label="📊 Avg Cost / Question",
                value=f"${cost_per_q:.6f}" if pd.notna(cost_per_q) else "N/A",
                help="Average cost per question (non-zero only)"
            )

    with col3:
        if has_latency:
            nonzero_lat = df[df['latency'] > 0]['latency']
            avg_lat = nonzero_lat.mean() if len(nonzero_lat) > 0 else 0
            st.metric(
                label="⚡ Avg Latency",
                value=f"{avg_lat:.2f}s" if avg_lat > 0 else "N/A",
                help="Average response time (non-zero only)"
            )

    with col4:
        if has_latency:
            nonzero_lat = df[df['latency'] > 0]['latency']
            p95 = nonzero_lat.quantile(0.95) if len(nonzero_lat) > 0 else 0
            st.metric(
                label="📈 P95 Latency",
                value=f"{p95:.2f}s" if p95 > 0 else "N/A",
                help="95th percentile response time"
            )

    # Second row of KPIs
    col5, col6, col7 = st.columns(3)

    with col5:
        if has_cost:
            questions_with_cost = df[df['total_cost'] > 0].shape[0]
            st.metric(
                label="📋 Traces with Cost",
                value=f"{questions_with_cost:,}",
                delta=f"{questions_with_cost / len(df) * 100:.1f}% of total",
                help="Number of traces that have cost data"
            )

    with col6:
        if has_latency:
            nonzero_lat = df[df['latency'] > 0]['latency']
            median_lat = nonzero_lat.median() if len(nonzero_lat) > 0 else 0
            st.metric(
                label="⏱️ Median Latency",
                value=f"{median_lat:.2f}s" if median_lat > 0 else "N/A",
                help="Median response time"
            )

    with col7:
        if has_latency:
            nonzero_lat = df[df['latency'] > 0]['latency']
            p99 = nonzero_lat.quantile(0.99) if len(nonzero_lat) > 0 else 0
            st.metric(
                label="🔴 P99 Latency",
                value=f"{p99:.2f}s" if p99 > 0 else "N/A",
                help="99th percentile response time"
            )

    st.markdown("---")

    # ── Tabs ──
    tab1, tab2, tab3 = st.tabs([
        "💰 Cost Analysis",
        "⚡ Latency Analysis",
        "📊 Operational Overview"
    ])

    # ── TAB 1: Cost Analysis ──
    with tab1:
        if not has_cost:
            st.info("No cost data available in the current dataset.")
        else:
            cost_df = df[df['total_cost'].notna() & (df['total_cost'] > 0)].copy()

            st.markdown("### 💰 Weekly Cost Breakdown")

            if 'timestamp' in cost_df.columns:
                cost_df['week'] = pd.to_datetime(cost_df['timestamp'], format='ISO8601', errors='coerce').dt.strftime('%Y-W%U')
                weekly_cost = cost_df.groupby('week').agg(
                    total_cost=('total_cost', 'sum'),
                    question_count=('total_cost', 'count'),
                    avg_cost=('total_cost', 'mean'),
                    max_cost=('total_cost', 'max')
                ).reset_index().sort_values('week')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=weekly_cost['week'],
                    y=weekly_cost['total_cost'],
                    name='Weekly Cost',
                    marker=dict(color=BYU_COLORS['primary']),
                    text=[f"${c:.4f}" for c in weekly_cost['total_cost']],
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Cost: $%{y:.6f}<br>Questions: %{customdata[0]}<br>Avg: $%{customdata[1]:.6f}<extra></extra>',
                    customdata=weekly_cost[['question_count', 'avg_cost']].values
                ))

                fig.update_layout(
                    title="Weekly Cost",
                    xaxis_title="Week",
                    yaxis_title="Total Cost ($)",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch', key="weekly_cost_bar")

                # Weekly cost table
                with st.expander("📋 Weekly Cost Details"):
                    display_weekly = weekly_cost.copy()
                    display_weekly.columns = ['Week', 'Total Cost ($)', 'Questions', 'Avg Cost ($)', 'Max Cost ($)']
                    st.dataframe(display_weekly, width='stretch', hide_index=True)

            st.markdown("---")

            # Cumulative cost
            st.markdown("### 📈 Cumulative Cost Over Time")
            if 'timestamp' in cost_df.columns:
                cost_time = cost_df.sort_values('timestamp').copy()
                cost_time['cumulative_cost'] = cost_time['total_cost'].cumsum()

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cost_time['timestamp'],
                    y=cost_time['cumulative_cost'],
                    mode='lines',
                    fill='tozeroy',
                    line=dict(color=BYU_COLORS['primary'], width=2),
                    fillcolor='rgba(0, 46, 93, 0.1)',
                    hovertemplate='%{x}<br>Cumulative: $%{y:.6f}<extra></extra>'
                ))

                fig.update_layout(
                    title="Cumulative Cost",
                    xaxis_title="Time",
                    yaxis_title="Cumulative Cost ($)",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig, width='stretch', key="cumulative_cost_line")

            st.markdown("---")

            # Cost distribution
            st.markdown("### 📊 Cost Distribution")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=cost_df['total_cost'],
                nbinsx=50,
                marker=dict(color=BYU_COLORS['accent1']),
                hovertemplate='Cost: $%{x:.6f}<br>Count: %{y}<extra></extra>'
            ))

            fig.update_layout(
                title="Cost Distribution (per question)",
                xaxis_title="Cost ($)",
                yaxis_title="Number of Questions",
                height=350,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch', key="cost_distribution_hist")

            # Cost summary stats
            with st.expander("📊 Cost Statistics"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Min", f"${cost_df['total_cost'].min():.8f}")
                with col2:
                    st.metric("Median", f"${cost_df['total_cost'].median():.6f}")
                with col3:
                    st.metric("Mean", f"${cost_df['total_cost'].mean():.6f}")
                with col4:
                    st.metric("Max", f"${cost_df['total_cost'].max():.6f}")

    # ── TAB 2: Latency Analysis ──
    with tab2:
        if not has_latency:
            st.info("No latency data available in the current dataset.")
        else:
            lat_df = df[df['latency'].notna() & (df['latency'] > 0)].copy()

            st.markdown("### ⚡ Latency Distribution")

            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=lat_df['latency'],
                nbinsx=50,
                marker=dict(color=BYU_COLORS['secondary']),
                hovertemplate='Latency: %{x:.2f}s<br>Count: %{y}<extra></extra>'
            ))

            # Add percentile lines
            p50 = lat_df['latency'].median()
            p95 = lat_df['latency'].quantile(0.95)
            p99 = lat_df['latency'].quantile(0.99)

            for pval, plabel, pcolor in [
                (p50, 'P50 (Median)', '#4caf50'),
                (p95, 'P95', '#FFB933'),
                (p99, 'P99', '#C5050C')
            ]:
                fig.add_vline(
                    x=pval, line_dash="dash", line_color=pcolor,
                    annotation_text=f"{plabel}: {pval:.2f}s",
                    annotation_position="top right"
                )

            fig.update_layout(
                title="Latency Distribution",
                xaxis_title="Latency (seconds)",
                yaxis_title="Number of Questions",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch', key="latency_distribution_hist")

            # Percentile summary
            st.markdown("### 📊 Latency Percentiles")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Min", f"{lat_df['latency'].min():.3f}s")
            with col2:
                st.metric("P50 (Median)", f"{p50:.3f}s")
            with col3:
                st.metric("P90", f"{lat_df['latency'].quantile(0.90):.3f}s")
            with col4:
                st.metric("P95", f"{p95:.3f}s")
            with col5:
                st.metric("P99", f"{p99:.3f}s")

            st.markdown("---")

            # Latency over time
            st.markdown("### 📈 Latency Trend Over Time")
            if 'timestamp' in lat_df.columns:
                lat_df['date'] = pd.to_datetime(lat_df['timestamp'], format='ISO8601', errors='coerce').dt.date
                daily_lat = lat_df.groupby('date').agg(
                    avg_latency=('latency', 'mean'),
                    median_latency=('latency', 'median'),
                    p95_latency=('latency', lambda x: x.quantile(0.95)),
                    count=('latency', 'count')
                ).reset_index()

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_lat['date'], y=daily_lat['avg_latency'],
                    name='Average', mode='lines+markers',
                    line=dict(color=BYU_COLORS['primary'], width=2),
                    hovertemplate='%{x}<br>Avg: %{y:.3f}s<extra></extra>'
                ))
                fig.add_trace(go.Scatter(
                    x=daily_lat['date'], y=daily_lat['median_latency'],
                    name='Median', mode='lines+markers',
                    line=dict(color='#4caf50', width=2),
                    hovertemplate='%{x}<br>Median: %{y:.3f}s<extra></extra>'
                ))
                fig.add_trace(go.Scatter(
                    x=daily_lat['date'], y=daily_lat['p95_latency'],
                    name='P95', mode='lines+markers',
                    line=dict(color=BYU_COLORS['accent2'], width=2, dash='dash'),
                    hovertemplate='%{x}<br>P95: %{y:.3f}s<extra></extra>'
                ))

                fig.update_layout(
                    title="Daily Latency Trend",
                    xaxis_title="Date",
                    yaxis_title="Latency (seconds)",
                    height=400,
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, width='stretch', key="latency_trend_line")

            st.markdown("---")

            # Weekly latency breakdown
            st.markdown("### 📅 Weekly Latency Summary")
            if 'timestamp' in lat_df.columns:
                lat_df['week'] = pd.to_datetime(lat_df['timestamp'], format='ISO8601', errors='coerce').dt.strftime('%Y-W%U')
                weekly_lat = lat_df.groupby('week').agg(
                    avg_latency=('latency', 'mean'),
                    median_latency=('latency', 'median'),
                    p95_latency=('latency', lambda x: x.quantile(0.95)),
                    count=('latency', 'count')
                ).reset_index().sort_values('week')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=weekly_lat['week'], y=weekly_lat['avg_latency'],
                    name='Average',
                    marker=dict(color=BYU_COLORS['primary']),
                    hovertemplate='<b>%{x}</b><br>Avg: %{y:.3f}s<br>Count: %{customdata}<extra></extra>',
                    customdata=weekly_lat['count']
                ))
                fig.add_trace(go.Scatter(
                    x=weekly_lat['week'], y=weekly_lat['p95_latency'],
                    name='P95',
                    mode='lines+markers',
                    line=dict(color=BYU_COLORS['accent2'], width=2),
                    hovertemplate='<b>%{x}</b><br>P95: %{y:.3f}s<extra></extra>'
                ))

                fig.update_layout(
                    title="Weekly Latency",
                    xaxis_title="Week",
                    yaxis_title="Latency (seconds)",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, width='stretch', key="weekly_latency_bar")

    # ── TAB 3: Operational Overview ──
    with tab3:
        st.markdown("### 📊 Operational Overview")

        # Cost vs Volume correlation
        if has_cost and 'timestamp' in df.columns:
            st.markdown("#### 💰 Cost vs Question Volume")
            cost_nonzero = df[df['total_cost'].notna() & (df['total_cost'] > 0)].copy()
            cost_nonzero['week'] = pd.to_datetime(cost_nonzero['timestamp'], format='ISO8601', errors='coerce').dt.strftime('%Y-W%U')

            weekly_corr = cost_nonzero.groupby('week').agg(
                total_cost=('total_cost', 'sum'),
                question_count=('total_cost', 'count')
            ).reset_index()

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=weekly_corr['question_count'],
                y=weekly_corr['total_cost'],
                mode='markers+text',
                text=weekly_corr['week'],
                textposition='top center',
                marker=dict(
                    color=BYU_COLORS['primary'],
                    size=12,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>%{text}</b><br>Questions: %{x}<br>Cost: $%{y:.6f}<extra></extra>'
            ))

            fig.update_layout(
                title="Cost vs Question Volume (by Week)",
                xaxis_title="Number of Questions",
                yaxis_title="Total Cost ($)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch', key="cost_vs_volume_scatter")

        st.markdown("---")

        # Efficiency insights
        if has_cost and has_latency:
            st.markdown("---")
            st.markdown("#### 💡 Efficiency Insights")

            cost_data = df[df['total_cost'] > 0]['total_cost']
            lat_data = df[df['latency'] > 0]['latency']

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Cost Efficiency:**")
                if len(cost_data) > 0:
                    st.markdown(f"- **Total spend:** ${cost_data.sum():.4f}")
                    st.markdown(f"- **Cost per question:** ${cost_data.mean():.6f} avg")
                    if cost_data.sum() > 0:
                        daily_rate = cost_data.sum() / max(1, (df['timestamp'].max() - df['timestamp'].min()).days)
                        monthly_estimate = daily_rate * 30
                        st.markdown(f"- **Estimated monthly:** ${monthly_estimate:.4f}")

            with col2:
                st.markdown("**Latency Performance:**")
                if len(lat_data) > 0:
                    fast_count = (lat_data < 1.0).sum()
                    fast_pct = fast_count / len(lat_data) * 100
                    st.markdown(f"- **Under 1s:** {fast_count} ({fast_pct:.1f}%)")
                    slow_count = (lat_data > 2.0).sum()
                    slow_pct = slow_count / len(lat_data) * 100
                    st.markdown(f"- **Over 2s:** {slow_count} ({slow_pct:.1f}%)")
                    st.markdown(f"- **Avg response:** {lat_data.mean():.2f}s")


if __name__ == "__main__":
    main()
