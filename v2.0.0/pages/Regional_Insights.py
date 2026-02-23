"""
Regional Insights Page - Geographic analysis of topics, preferences, and feedback quality
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css, BYU_COLORS
from utils.data_loader import ensure_data_loaded
from utils.visualizations import (
    plot_regional_topic_preferences, plot_feedback_quality_by_region,
    plot_country_distribution
)
import plotly.graph_objects as go
import plotly.express as px

# Configure page settings (needed for direct page access)
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def plot_regional_heatmap(df: pd.DataFrame, metric: str = 'count', key: str = "regional_heatmap"):
    """
    Create a heatmap showing metrics by country and state.
    
    Args:
        df: DataFrame with country, state columns
        metric: 'count', 'unhelpful_rate', or 'avg_similarity'
        key: Unique key for the chart
    """
    if 'country' not in df.columns or 'state' not in df.columns or df.empty:
        st.info("No geographic data available for heatmap")
        return
    
    # Get top countries and states
    top_countries = df['country'].value_counts().head(10).index
    df_filtered = df[df['country'].isin(top_countries)]
    
    if metric == 'count':
        pivot_data = df_filtered.groupby(['country', 'state']).size().reset_index(name='value')
    elif metric == 'unhelpful_rate' and 'user_feedback' in df.columns:
        from utils.visualizations import _normalize_feedback
        fb_df = df_filtered.copy()
        fb_df['feedback_norm'] = fb_df['user_feedback'].apply(_normalize_feedback)
        fb_df = fb_df[fb_df['feedback_norm'].notna()]
        pivot_data = fb_df.groupby(['country', 'state']).agg({
            'feedback_norm': lambda x: (x == 'unhelpful').sum() / len(x) * 100 if len(x) > 0 else 0
        }).reset_index()
        pivot_data.columns = ['country', 'state', 'value']
    elif metric == 'avg_similarity' and 'similarity_score' in df.columns:
        pivot_data = df_filtered.groupby(['country', 'state'])['similarity_score'].mean().reset_index()
        pivot_data.columns = ['country', 'state', 'value']
    else:
        st.info(f"Metric '{metric}' not available")
        return
    
    # Get top states per country
    top_states_per_country = pivot_data.groupby('country').apply(
        lambda x: x.nlargest(5, 'value')
    ).reset_index(drop=True)
    
    if top_states_per_country.empty:
        st.info("Insufficient data for regional heatmap")
        return
    
    # Create pivot table
    heatmap_pivot = top_states_per_country.pivot(index='state', columns='country', values='value').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='Blues' if metric == 'count' else 'RdYlGn_r',
        hovertemplate='Country: %{x}<br>State: %{y}<br>Value: %{z:.1f}<extra></extra>'
    ))
    
    title_map = {
        'count': 'Question Volume by Country and State',
        'unhelpful_rate': 'Unhelpful Response Rate by Region (%)',
        'avg_similarity': 'Average Similarity Score by Region'
    }
    
    fig.update_layout(
        title=title_map.get(metric, 'Regional Heatmap'),
        xaxis_title="Country",
        yaxis_title="State/Province",
        height=500
    )
    
    st.plotly_chart(fig, width='stretch', key=key)


def analyze_regional_topics(df: pd.DataFrame, region_type: str, region_name: str):
    """
    Detailed analysis of topics for a specific region.
    
    Args:
        df: Full dataframe
        region_type: 'country' or 'state'
        region_name: Name of the region
    """
    if region_type not in df.columns or df.empty:
        st.warning(f"No {region_type} data available")
        return
    
    region_df = df[df[region_type] == region_name]
    
    if region_df.empty:
        st.warning(f"No data found for {region_name}")
        return
    
    # Overview metrics
    st.markdown(f"### 📍 {region_name} Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Questions", f"{len(region_df):,}")
    
    with col2:
        if 'classification' in region_df.columns:
            existing_pct = (len(region_df[region_df['classification'] == 'Existing Topic']) / len(region_df) * 100)
            st.metric("Matched Topics", f"{existing_pct:.1f}%")
    
    with col3:
        if 'user_feedback' in region_df.columns:
            feedback_df = region_df[region_df['user_feedback'].notna()]
            if not feedback_df.empty:
                helpful_pct = (len(feedback_df[feedback_df['user_feedback'] == 'helpful']) / len(feedback_df) * 100)
                st.metric("Helpful Rate", f"{helpful_pct:.1f}%")
    
    with col4:
        if 'similarity_score' in region_df.columns:
            avg_sim = region_df['similarity_score'].mean()
            if pd.notna(avg_sim):
                st.metric("Avg Similarity", f"{avg_sim:.3f}")
    
    st.markdown("---")
    
    # Top topics for this region
    if 'matched_topic' in region_df.columns:
        st.markdown(f"#### 🎯 Top Topics in {region_name}")
        
        topic_data = region_df[region_df['classification'] == 'Existing Topic']
        if not topic_data.empty:
            topic_counts = topic_data['matched_topic'].value_counts().head(10)
            
            fig = go.Figure(data=[go.Bar(
                x=topic_counts.values,
                y=topic_counts.index,
                orientation='h',
                marker=dict(color=BYU_COLORS['accent1']),
                text=topic_counts.values,
                textposition='outside'
            )])
            
            fig.update_layout(
                title=f"Top 10 Topics in {region_name}",
                xaxis_title="Number of Questions",
                yaxis_title="Topic",
                height=400,
                showlegend=False,
                yaxis=dict(autorange="reversed")
            )
            
            st.plotly_chart(fig, width='stretch', key=f"regional_topics_{region_name}")
            
            # Topic percentage breakdown
            with st.expander("💡 Topic Breakdown"):
                total_matched = len(topic_data)
                st.markdown(f"**Total matched questions:** {total_matched:,}")
                st.markdown("**Top 5 Topics:**")
                for i, (topic, count) in enumerate(topic_counts.head(5).items(), 1):
                    percentage = (count / total_matched * 100)
                    st.markdown(f"{i}. **{topic}**: {count} questions ({percentage:.1f}%)")
        else:
            st.info("No matched topics available for this region")


def main():
    st.title("🌍 Regional Insights")
    st.markdown("*Understand geographic patterns, regional preferences, and localization opportunities*")
    st.markdown("---")
    
    # Ensure data is loaded (handles page refresh)
    ensure_data_loaded()
    
    df = st.session_state['merged_df']
    
    if df.empty:
        st.warning("⚠️ No data available for regional analysis.")
        st.stop()
    
    # Check if geographic data is available
    has_country = 'country' in df.columns and df['country'].notna().any()
    has_state = 'state' in df.columns and df['state'].notna().any()
    
    if not has_country and not has_state:
        st.error("❌ No geographic data (country/state) available in the dataset.")
        st.stop()
    
    # Overview KPIs
    st.markdown("## 📊 Geographic Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if has_country:
            unique_countries = df['country'].nunique()
            st.metric(
                label="🌍 Countries",
                value=unique_countries,
                help="Total number of countries represented"
            )
    
    with col2:
        if has_state:
            unique_states = df['state'].nunique()
            st.metric(
                label="📍 States/Provinces",
                value=unique_states,
                help="Total number of states/provinces represented"
            )
    
    with col3:
        if has_country:
            top_country = df['country'].value_counts().index[0]
            top_country_count = df['country'].value_counts().values[0]
            st.metric(
                label="🏆 Top Country",
                value=top_country,
                delta=f"{top_country_count:,} questions",
                help="Country with most questions"
            )
    
    with col4:
        if 'user_feedback' in df.columns:
            from utils.visualizations import _normalize_feedback
            feedback_df = df[df['user_feedback'].notna()].copy()
            feedback_df['feedback_norm'] = feedback_df['user_feedback'].apply(_normalize_feedback)
            feedback_df = feedback_df[feedback_df['feedback_norm'].notna()]
            if not feedback_df.empty:
                helpful_count = (feedback_df['feedback_norm'] == 'helpful').sum()
                total_feedback = len(feedback_df)
                helpful_rate = (helpful_count / total_feedback * 100)
                st.metric(
                    label="✅ Overall Helpful Rate",
                    value=f"{helpful_rate:.1f}%",
                    help="Percentage of responses marked as helpful"
                )
    
    st.markdown("---")
    
    # Main analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌎 Country Analysis",
        "📍 State/Province Analysis",
        "📊 Feedback Quality",
        "🔍 Regional Deep Dive"
    ])
    
    with tab1:
        st.markdown("### 🌎 Country-Level Insights")
        
        if not has_country:
            st.info("No country data available")
        else:
            # Country distribution
            st.markdown("#### Question Volume by Country")
            plot_country_distribution(df, top_n=15)
            
            st.markdown("---")
            
            # Regional topic preferences by country
            st.markdown("#### Top Topics by Country")
            regional_data = plot_regional_topic_preferences(df, by='country', top_n=10, key="country_topics")
            
            if regional_data is not None:
                with st.expander("📊 Detailed Country Statistics"):
                    st.dataframe(regional_data, width='stretch', hide_index=True)
            
            st.markdown("---")
            
            # Language distribution by country
            if 'user_language' in df.columns and df['user_language'].notna().any():
                st.markdown("#### Language Distribution")
                
                lang_country = df[df['user_language'].notna()].groupby(['country', 'user_language']).size().reset_index(name='count')
                top_countries_lang = df['country'].value_counts().head(10).index
                lang_country_filtered = lang_country[lang_country['country'].isin(top_countries_lang)]
                
                if not lang_country_filtered.empty:
                    fig = px.bar(
                        lang_country_filtered,
                        x='country',
                        y='count',
                        color='user_language',
                        title="Language Distribution by Country",
                        labels={'count': 'Number of Questions', 'country': 'Country'}
                    )
                    
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, width='stretch', key="lang_country_dist")
    
    with tab2:
        st.markdown("### 📍 State/Province-Level Insights")
        
        if not has_state:
            st.info("No state/province data available")
        else:
            # State distribution
            st.markdown("#### Question Volume by State/Province")
            
            state_counts = df['state'].value_counts().head(20)
            
            fig = go.Figure(data=[go.Bar(
                x=state_counts.values,
                y=state_counts.index,
                orientation='h',
                marker=dict(color=BYU_COLORS['primary']),
                text=state_counts.values,
                textposition='outside'
            )])
            
            fig.update_layout(
                title="Top 20 States/Provinces by Question Volume",
                xaxis_title="Number of Questions",
                yaxis_title="State/Province",
                height=600,
                showlegend=False,
                yaxis=dict(autorange="reversed")
            )
            
            st.plotly_chart(fig, width='stretch', key="state_distribution")
            
            st.markdown("---")
            
            # Regional topic preferences by state
            st.markdown("#### Top Topics by State/Province")
            regional_data = plot_regional_topic_preferences(df, by='state', top_n=10, key="state_topics")
            
            if regional_data is not None:
                with st.expander("📊 Detailed State Statistics"):
                    st.dataframe(regional_data, width='stretch', hide_index=True)
    
    with tab3:
        st.markdown("### 📊 Response Quality by Region")
        st.markdown("Identify regions with higher rates of unhelpful responses for localization improvements.")
        
        if 'user_feedback' not in df.columns or not df['user_feedback'].notna().any():
            st.info("No user feedback data available for quality analysis")
        else:
            # Feedback quality by country
            if has_country:
                st.markdown("#### Unhelpful Response Rate by Country")
                country_feedback = plot_feedback_quality_by_region(df, by='country', key="country_feedback")
                
                if country_feedback is not None:
                    st.markdown("---")
                    
                    # Insights
                    with st.expander("💡 Country Feedback Insights"):
                        top_unhelpful = country_feedback.nlargest(5, 'unhelpful_rate')
                        top_helpful = country_feedback.nsmallest(5, 'unhelpful_rate')
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🔴 Highest Unhelpful Rates:**")
                            for idx, row in top_unhelpful.iterrows():
                                st.markdown(f"- **{row['country']}**: {row['unhelpful_rate']:.1f}% ({row['total_feedback']} responses)")
                        
                        with col2:
                            st.markdown("**🟢 Lowest Unhelpful Rates:**")
                            for idx, row in top_helpful.iterrows():
                                st.markdown(f"- **{row['country']}**: {row['unhelpful_rate']:.1f}% ({row['total_feedback']} responses)")
                        
                        st.markdown("---")
                        st.markdown("""
                        **Action Items:**
                        - Review responses in high-unhelpful regions for localization issues
                        - Consider translating content for non-English speaking regions
                        - Investigate cultural or contextual mismatches in responses
                        - Create region-specific FAQ sections where needed
                        """)
            
            st.markdown("---")
            
            # Feedback quality by state
            if has_state:
                st.markdown("#### Unhelpful Response Rate by State/Province")
                state_feedback = plot_feedback_quality_by_region(df, by='state', key="state_feedback")
                
                if state_feedback is not None:
                    with st.expander("📊 State Feedback Details"):
                        st.dataframe(state_feedback, width='stretch', hide_index=True)
    
    with tab4:
        st.markdown("### 🔍 Regional Deep Dive")
        st.markdown("Select a specific region for detailed analysis of topics, questions, and patterns.")
        
        # Region selector
        col1, col2 = st.columns(2)
        
        with col1:
            region_type = st.radio(
                "Region Type",
                ["country", "state"],
                format_func=lambda x: "Country" if x == "country" else "State/Province",
                help="Choose whether to analyze by country or state/province",
                key="region_type_selector"
            )
        
        with col2:
            if region_type == 'country' and has_country:
                available_regions = sorted(df['country'].dropna().unique())
            elif region_type == 'state' and has_state:
                available_regions = sorted(df['state'].dropna().unique())
            else:
                available_regions = []
            
            if available_regions:
                selected_region = st.selectbox(
                    f"Select {region_type.capitalize()}",
                    available_regions,
                    help=f"Choose a {region_type} to analyze in detail",
                    key="region_selector"
                )
            else:
                st.warning(f"No {region_type} data available")
                selected_region = None
        
        if selected_region:
            st.markdown("---")
            analyze_regional_topics(df, region_type, selected_region)
            
            st.markdown("---")
            
            # Show sample questions from this region
            region_df = df[df[region_type] == selected_region]
            
            with st.expander(f"📝 Sample Questions from {selected_region}"):
                if 'question' in region_df.columns:
                    sample_questions = region_df['question'].head(10)
                    for i, q in enumerate(sample_questions, 1):
                        st.markdown(f"{i}. {q}")
                else:
                    st.info("Question text not available")
    
    # Footer
    st.markdown("---")
    st.info("""
    ### 💡 Using Regional Insights
    
    **Localization Opportunities:**
    - Regions with high unhelpful rates may need localized content
    - Different regions may have unique concerns requiring targeted FAQs
    - Language distribution helps prioritize translation efforts
    
    **Resource Allocation:**
    - Focus support resources on high-volume regions
    - Create region-specific documentation for unique topics
    - Monitor emerging regions for early intervention
    
    **Best Practices:**
    - Review unhelpful responses for cultural or contextual issues
    - Compare similar regions to identify best practices
    - Track regional trends over time for seasonal patterns
    """)


if __name__ == "__main__":
    main()
