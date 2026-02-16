"""
Weekly Insights Page - Week-by-week topic analysis and trends
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css, BYU_COLORS
from utils.data_loader import ensure_data_loaded
from utils.visualizations import (
    plot_weekly_topic_trends, plot_week_over_week_comparison, 
    plot_topic_evolution
)

# Configure page settings (needed for direct page access)
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def get_available_weeks(df: pd.DataFrame):
    """Extract list of available weeks from dataframe."""
    if 'timestamp' not in df.columns or df.empty:
        return []
    
    df_copy = df.copy()
    df_copy['week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.strftime('%Y-W%U')
    return sorted(df_copy['week'].unique(), reverse=True)


def main():
    st.title("📅 Weekly Insights")
    st.markdown("*Track topic trends and patterns week by week*")
    st.markdown("---")
    
    # Ensure data is loaded (handles page refresh)
    ensure_data_loaded()
    
    df = st.session_state['merged_df']
    
    if df.empty:
        st.warning("⚠️ No data available for weekly analysis.")
        st.stop()
    
    # Get available weeks
    available_weeks = get_available_weeks(df)
    
    if not available_weeks:
        st.warning("⚠️ No timestamp data available for weekly analysis.")
        st.stop()
    
    # Overview KPIs
    st.markdown("## 📊 Weekly Overview")
    
    df_copy = df.copy()
    df_copy['week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.strftime('%Y-W%U')
    
    # Calculate metrics
    total_weeks = len(available_weeks)
    latest_week = available_weeks[0]
    latest_week_count = len(df_copy[df_copy['week'] == latest_week])
    
    # Previous week for comparison
    if len(available_weeks) > 1:
        prev_week = available_weeks[1]
        prev_week_count = len(df_copy[df_copy['week'] == prev_week])
        week_change = latest_week_count - prev_week_count
        week_change_pct = (week_change / prev_week_count * 100) if prev_week_count > 0 else 0
    else:
        prev_week = None
        week_change = 0
        week_change_pct = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📅 Total Weeks",
            value=total_weeks,
            help="Total number of weeks with data"
        )
    
    with col2:
        st.metric(
            label="🆕 Latest Week",
            value=latest_week,
            help="Most recent week in the dataset"
        )
    
    with col3:
        st.metric(
            label="📊 Questions This Week",
            value=f"{latest_week_count:,}",
            delta=f"{week_change:+,}" if prev_week else None,
            help=f"Questions in week {latest_week}"
        )
    
    with col4:
        if prev_week:
            st.metric(
                label="📈 Week-over-Week Change",
                value=f"{week_change_pct:+.1f}%",
                delta=f"{week_change:+,} questions",
                help=f"Change from week {prev_week}"
            )
    
    st.markdown("---")
    
    # Main analysis tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Single Week Analysis",
        "🔄 Week Comparison",
        "📈 Topic Evolution"
    ])
    
    with tab1:
        st.markdown("### 📊 Analyze a Specific Week")
        st.markdown("Select a week to see the top topics and questions for that period.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_week = st.selectbox(
                "Select Week",
                available_weeks,
                index=0,
                help="Choose a week to analyze",
                key="single_week_selector"
            )
        
        with col2:
            st.markdown("#### Week Info")
            week_data = df_copy[df_copy['week'] == selected_week]
            st.metric("Questions", len(week_data))
            
            if 'country' in week_data.columns:
                unique_countries = week_data['country'].nunique()
                st.metric("Countries", unique_countries)
        
        st.markdown("---")
        
        # Show top topics for selected week
        st.markdown(f"#### Top Topics for Week {selected_week}")
        topic_counts = plot_weekly_topic_trends(df, selected_week, key=f"weekly_topics_{selected_week}")
        
        if topic_counts is not None and not topic_counts.empty:
            # Additional insights
            with st.expander("💡 Detailed Topic Breakdown"):
                st.markdown(f"**Total topics discussed this week:** {len(topic_counts)}")
                
                # Show percentage breakdown
                total_questions = topic_counts.sum()
                st.markdown("**Top 5 Topics Breakdown:**")
                for i, (topic, count) in enumerate(topic_counts.head(5).items(), 1):
                    percentage = (count / total_questions * 100)
                    st.markdown(f"{i}. **{topic}**: {count} questions ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # Week summary statistics
        st.markdown("#### 📈 Week Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Classification breakdown
            if 'classification' in week_data.columns:
                st.markdown("**Classification Distribution:**")
                class_counts = week_data['classification'].value_counts()
                for classification, count in class_counts.items():
                    pct = (count / len(week_data) * 100)
                    st.markdown(f"- {classification}: {count} ({pct:.1f}%)")
        
        with col2:
            # Geographic summary
            if 'country' in week_data.columns:
                st.markdown("**Top 5 Countries:**")
                country_counts = week_data['country'].value_counts().head(5)
                for country, count in country_counts.items():
                    pct = (count / len(week_data) * 100)
                    st.markdown(f"- {country}: {count} ({pct:.1f}%)")
    
    with tab2:
        st.markdown("### 🔄 Compare Two Weeks")
        st.markdown("Select two weeks to compare their topic distributions and identify trending topics.")
        
        if len(available_weeks) < 2:
            st.info("⚠️ Need at least 2 weeks of data for comparison. Currently only have 1 week.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                week1 = st.selectbox(
                    "First Week",
                    available_weeks,
                    index=min(1, len(available_weeks)-1),
                    help="Select the first week to compare",
                    key="week1_selector"
                )
            
            with col2:
                week2 = st.selectbox(
                    "Second Week",
                    available_weeks,
                    index=0,
                    help="Select the second week to compare",
                    key="week2_selector"
                )
            
            if week1 == week2:
                st.warning("⚠️ Please select two different weeks for comparison.")
            else:
                st.markdown("---")
                
                # Show comparison
                plot_week_over_week_comparison(df, week1, week2, key="week_comparison_chart")
                
                # Calculate insights
                week1_data = df_copy[df_copy['week'] == week1]
                week2_data = df_copy[df_copy['week'] == week2]
                
                # Topic comparison insights
                with st.expander("💡 Comparison Insights"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Week {week1}:**")
                        st.markdown(f"- Total Questions: {len(week1_data):,}")
                        
                        if 'matched_topic' in week1_data.columns:
                            week1_topics = week1_data[week1_data['classification'] == 'Existing Topic']
                            if not week1_topics.empty:
                                top_topic = week1_topics['matched_topic'].value_counts().head(1)
                                if not top_topic.empty:
                                    st.markdown(f"- Top Topic: **{top_topic.index[0]}** ({top_topic.values[0]} questions)")
                    
                    with col2:
                        st.markdown(f"**Week {week2}:**")
                        st.markdown(f"- Total Questions: {len(week2_data):,}")
                        
                        if 'matched_topic' in week2_data.columns:
                            week2_topics = week2_data[week2_data['classification'] == 'Existing Topic']
                            if not week2_topics.empty:
                                top_topic = week2_topics['matched_topic'].value_counts().head(1)
                                if not top_topic.empty:
                                    st.markdown(f"- Top Topic: **{top_topic.index[0]}** ({top_topic.values[0]} questions)")
                    
                    # Calculate change
                    change = len(week2_data) - len(week1_data)
                    change_pct = (change / len(week1_data) * 100) if len(week1_data) > 0 else 0
                    
                    st.markdown("---")
                    st.markdown(f"**Overall Change:** {change:+,} questions ({change_pct:+.1f}%)")
                    
                    # Identify trending topics
                    if 'matched_topic' in df_copy.columns:
                        week1_topic_counts = week1_data[week1_data['classification'] == 'Existing Topic']['matched_topic'].value_counts()
                        week2_topic_counts = week2_data[week2_data['classification'] == 'Existing Topic']['matched_topic'].value_counts()
                        
                        # Find topics with biggest increases
                        all_topics = set(week1_topic_counts.index) | set(week2_topic_counts.index)
                        topic_changes = {}
                        
                        for topic in all_topics:
                            w1_count = week1_topic_counts.get(topic, 0)
                            w2_count = week2_topic_counts.get(topic, 0)
                            change = w2_count - w1_count
                            topic_changes[topic] = change
                        
                        # Sort by change
                        trending_up = sorted(topic_changes.items(), key=lambda x: x[1], reverse=True)[:5]
                        trending_down = sorted(topic_changes.items(), key=lambda x: x[1])[:5]
                        
                        if any(change > 0 for _, change in trending_up):
                            st.markdown("**📈 Trending Up:**")
                            for topic, change in trending_up:
                                if change > 0:
                                    st.markdown(f"- {topic}: **+{change}** questions")
                        
                        if any(change < 0 for _, change in trending_down):
                            st.markdown("**📉 Trending Down:**")
                            for topic, change in trending_down:
                                if change < 0:
                                    st.markdown(f"- {topic}: **{change}** questions")
    
    with tab3:
        st.markdown("### 📈 Topic Evolution Over Time")
        st.markdown("Track how the popularity of top topics has changed across all weeks.")
        
        st.markdown("---")
        
        # Topic evolution chart
        plot_topic_evolution(df, top_n=5, key="topic_evolution_weekly")
        
        st.markdown("---")
        
        # Weekly statistics table
        with st.expander("📊 Weekly Statistics Table"):
            weekly_stats = []
            
            for week in available_weeks:
                week_data = df_copy[df_copy['week'] == week]
                
                stat = {
                    'Week': week,
                    'Total Questions': len(week_data),
                    'Existing Topics': len(week_data[week_data['classification'] == 'Existing Topic']),
                    'New Topics': len(week_data[week_data['classification'] == 'New Topic'])
                }
                
                if 'country' in week_data.columns:
                    stat['Countries'] = week_data['country'].nunique()
                
                weekly_stats.append(stat)
            
            stats_df = pd.DataFrame(weekly_stats)
            st.dataframe(stats_df, width='stretch', hide_index=True)
        
        # Insights
        with st.expander("💡 Evolution Insights"):
            st.markdown("""
            **How to Use This Analysis:**
            
            - **Rising Trends**: Topics with upward trajectories indicate growing concerns or interests
            - **Declining Trends**: Topics with downward slopes may indicate resolved issues or seasonal changes
            - **Stable Topics**: Consistently high volumes suggest ongoing, fundamental concerns
            - **Spikes**: Sudden increases may indicate new policies, events, or system changes
            
            **Action Items:**
            - Allocate resources to consistently high-volume topics
            - Investigate causes of sudden spikes
            - Consider creating dedicated content for rising trends
            - Monitor declining topics to ensure issues are truly resolved
            """)
    
    # Footer
    st.markdown("---")
    st.info("""
    ### 💡 Using Weekly Insights
    
    **Best Practices:**
    - Review latest week trends to understand current student concerns
    - Compare consecutive weeks to spot emerging patterns
    - Track topic evolution to inform content strategy and resource allocation
    - Use trending topics data to proactively create support materials
    
    **Tips:**
    - Week-over-week changes help identify seasonal patterns
    - Large spikes may indicate policy changes or system issues
    - Consistent topics suggest areas for improved documentation
    """)


if __name__ == "__main__":
    main()
