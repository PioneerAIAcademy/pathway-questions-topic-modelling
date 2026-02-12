"""
Trends & Analytics Page - Detailed visualizations and insights
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import PAGE_CONFIG, get_theme_css
from utils.data_loader import ensure_data_loaded
from utils.visualizations import (
    create_kpi_cards, plot_classification_distribution, plot_country_distribution,
    plot_timeline, plot_similarity_distribution, plot_top_topics,
    plot_hourly_heatmap, plot_language_distribution,
    plot_sentiment_distribution, identify_repeat_questions, 
    plot_activity_heatmap_with_insights
)

# Configure page settings (needed for direct page access)
st.set_page_config(**PAGE_CONFIG)

# Apply theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


def main():
    st.title("📈 Trends & Analytics")
    st.markdown("*Deep dive into patterns, trends, and insights from student questions*")
    st.markdown("---")
    
    # Ensure data is loaded (handles page refresh)
    ensure_data_loaded()
    
    df = st.session_state['merged_df']
    kpis = st.session_state['kpis']
    
    # KPI Cards
    st.markdown("## Key Performance Indicators")
    create_kpi_cards(kpis)
    
    st.markdown("---")
    
    # Main visualizations in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🌍 Geographic Insights",
        "⏰ Temporal Patterns",
        "🎯 Topic Analysis",
        "🔬 Advanced Insights"
    ])
    
    with tab1:
        st.markdown("### 📊 Overall Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            plot_classification_distribution(df)
        
        with col2:
            plot_similarity_distribution(df)
        
        st.markdown("---")
        
        st.markdown("### 📝 Question Volume Trends")
        plot_timeline(df)
        
        st.markdown("---")
        
        # Summary insights
        with st.expander("💡 Key Insights"):
            existing_count = len(df[df['classification'] == 'Existing Topic'])
            new_count = len(df[df['classification'] == 'New Topic'])
            total = len(df)
            
            existing_pct = (existing_count / total * 100) if total > 0 else 0
            new_pct = (new_count / total * 100) if total > 0 else 0
            
            st.markdown(f"""
            **Classification Summary:**
            - **{existing_pct:.1f}%** of questions matched existing topics
            - **{new_pct:.1f}%** of questions formed new topics
            - This suggests the current topic taxonomy covers most student questions effectively
            
            **Similarity Scores:**
            - Average similarity score: **{kpis['avg_similarity']:.3f}**
            - Higher scores indicate better matches to existing topics
            """)
    
    with tab2:
        st.markdown("### 🌍 Geographic Distribution")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            plot_country_distribution(df, top_n=15)
        
        with col2:
            if 'country' in df.columns:
                st.markdown("#### 📍 Country Statistics")
                country_stats = df['country'].value_counts().head(10)
                
                for i, (country, count) in enumerate(country_stats.items(), 1):
                    pct = (count / len(df) * 100)
                    st.markdown(f"{i}. **{country}**: {count:,} ({pct:.1f}%)")
        
        st.markdown("---")
        
        # Language distribution if available
        if 'user_language' in df.columns:
            st.markdown("### 🌐 Language Distribution")
            plot_language_distribution(df)
        
        with st.expander("💡 Geographic Insights"):
            if 'country' in df.columns:
                unique_countries = df['country'].nunique()
                mode_result = df['country'].mode()
                top_country = mode_result[0] if len(mode_result) > 0 else "N/A"
                top_country_count = df['country'].value_counts().iloc[0] if not df['country'].empty else 0
                top_country_pct = (top_country_count / len(df) * 100) if len(df) > 0 else 0
                
                st.markdown(f"""
                **Geographic Reach:**
                - Questions from **{unique_countries}** different countries
                - Top country: **{top_country}** ({top_country_count:,} questions, {top_country_pct:.1f}%)
                - This demonstrates the global reach of BYU Pathway
                """)
    
    with tab3:
        st.markdown("### ⏰ Temporal Patterns")
        
        # Timeline
        plot_timeline(df, key="timeline_temporal_tab")
        
        st.markdown("---")
        
        # Enhanced heatmap with insights
        st.markdown("### 🗓️ Activity Heatmap")
        insights = plot_activity_heatmap_with_insights(df, key="activity_heatmap_enhanced")
        
        # Display insights if available
        if insights:
            st.markdown("---")
            st.markdown("### 📊 Activity Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔥 Peak Activity:**")
                st.markdown(f"- **Peak Hour:** {insights['peak_hour']}:00 ({insights['peak_hour_count']} questions)")
                st.markdown(f"- **Peak Day:** {insights['peak_day']} ({insights['peak_day_count']} questions)")
                st.success("**💡 Tip:** Schedule support missionaries and leaders during peak hours for maximum impact")
            
            with col2:
                st.markdown("**📉 Low Activity:**")
                st.markdown(f"- **Low Hour:** {insights['low_hour']}:00 ({insights['low_hour_count']} questions)")
                st.markdown(f"- **Low Day:** {insights['low_day']} ({insights['low_day_count']} questions)")
                st.info("**💡 Tip:** Use low-activity periods for maintenance and updates")
        
        st.markdown("---")
        
        with st.expander("💡 Temporal Insights"):
            if 'timestamp' in df.columns:
                df_copy = df.copy()
                df_copy['hour'] = df_copy['timestamp'].dt.hour
                df_copy['day_of_week'] = df_copy['timestamp'].dt.day_name()
                
                # Find peak hour
                if not df_copy['hour'].isna().all():
                    hour_mode = df_copy['hour'].mode()
                    day_mode = df_copy['day_of_week'].mode()
                    
                    if len(hour_mode) > 0 and len(day_mode) > 0:
                        peak_hour = hour_mode[0]
                        peak_day = day_mode[0]
                        
                        st.markdown(f"""
                        **Activity Patterns:**
                        - Most questions are asked around **{peak_hour}:00**
                        - Most active day: **{peak_day}**
                        - Use this information to optimize scheduling for support missionaries and leaders
                        
                        **Recommendations:**
                        - Ensure adequate support coverage during peak hours
                        - Consider automated responses during low-activity periods
                        - Monitor trends for seasonal variations
                        """)

    
    with tab4:
        st.markdown("### 🎯 Topic Analysis")
        
        # Top topics
        plot_top_topics(df, top_n=15)
        
        st.markdown("---")
        
        # Topic statistics
        col1, col2 = st.columns(2)
        
        with col1:
            if 'matched_topic' in df.columns:
                st.markdown("#### 📋 Topic Coverage")
                existing_topics = df[df['classification'] == 'Existing Topic']
                if not existing_topics.empty and 'matched_topic' in existing_topics.columns:
                    unique_topics = existing_topics['matched_topic'].nunique()
                    st.metric("Unique Topics Matched", unique_topics)
                    
                    # Most common topic
                    mode_result = existing_topics['matched_topic'].mode()
                    if len(mode_result) > 0:
                        top_topic = mode_result[0]
                        top_topic_count = existing_topics['matched_topic'].value_counts().iloc[0]
                        st.metric("Most Common Topic", top_topic)
                        st.metric("Questions in Top Topic", top_topic_count)
        
        with col2:
            if 'new_topics' in st.session_state.get('raw_data', {}):
                st.markdown("#### 🆕 New Topics")
                new_topics_df = st.session_state['raw_data']['new_topics']
                if not new_topics_df.empty and 'cluster_id' in new_topics_df.columns:
                    unique_clusters = new_topics_df['cluster_id'].nunique()
                    st.metric("New Topics Discovered", unique_clusters)
                    
                    avg_questions_per_cluster = len(new_topics_df) / unique_clusters
                    st.metric("Avg Questions per New Topic", f"{avg_questions_per_cluster:.1f}")
        
        with st.expander("💡 Topic Insights"):
            st.markdown("""
            **Topic Analysis Summary:**
            - Review the most common topics to understand student priorities
            - New topics indicate emerging themes that may need attention
            - Consider adding frequently appearing new topics to the official taxonomy
            - Use topic distribution to allocate resources effectively
            """)
    
    with tab5:
        st.markdown("### 🔬 Advanced Insights")
        st.markdown("*Sentiment analysis, repeat questions, and deeper patterns*")
        
        st.markdown("---")
        
        # Sentiment Analysis
        st.markdown("#### 😊 Question Sentiment Analysis")
        st.markdown("Understanding the emotional tone of questions helps identify urgent or frustrated users.")
        
        sentiment_df = plot_sentiment_distribution(df, key="sentiment_analysis_main")
        
        if sentiment_df is not None:
            st.markdown("---")
            
            # Sentiment insights summary
            with st.expander("� Sentiment Insights"):
                sentiment_counts = sentiment_df['sentiment'].value_counts()
                total = len(sentiment_df)
                
                st.markdown("**Sentiment Breakdown:**")
                for sentiment, count in sentiment_counts.items():
                    pct = (count / total * 100)
                    st.markdown(f"- **{sentiment}**: {count:,} questions ({pct:.1f}%)")
                
                if 'Negative/Urgent' in sentiment_counts.index:
                    negative_pct = (sentiment_counts['Negative/Urgent'] / total * 100)
                    if negative_pct > 30:
                        st.warning(f"⚠️ **{negative_pct:.1f}%** of questions show negative/urgent sentiment. Consider reviewing these for priority support.")
                    else:
                        st.success(f"✅ Only **{negative_pct:.1f}%** of questions show negative/urgent sentiment.")
            
            # Filter by sentiment
            st.markdown("#### 📋 Questions by Sentiment")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                sentiment_filter = st.selectbox(
                    "Filter by Sentiment",
                    ["All"] + sorted(sentiment_df['sentiment'].unique().tolist()),
                    key="sentiment_filter"
                )
            
            with col2:
                search_term = st.text_input(
                    "Search in questions",
                    placeholder="Type to search...",
                    key="sentiment_search"
                )
            
            # Apply filters
            filtered_sentiment_df = sentiment_df.copy()
            
            if sentiment_filter != "All":
                filtered_sentiment_df = filtered_sentiment_df[filtered_sentiment_df['sentiment'] == sentiment_filter]
            
            if search_term:
                filtered_sentiment_df = filtered_sentiment_df[
                    filtered_sentiment_df['question'].str.contains(search_term, case=False, na=False)
                ]
            
            # Show count
            st.markdown(f"**Showing {len(filtered_sentiment_df):,} of {len(sentiment_df):,} questions**")
            
            # Display the table
            st.dataframe(
                filtered_sentiment_df[['question', 'sentiment']],
                use_container_width=True,
                hide_index=True,
                height=400
            )
        
        st.markdown("---")
        
        # Repeat Questions
        st.markdown("#### 🔄 Frequently Asked Questions")
        st.markdown("Identifying repeat questions helps prioritize FAQ creation and self-service content.")
        
        repeat_df = identify_repeat_questions(df, key="repeat_questions_main")
        
        if repeat_df is not None:
            with st.expander("💡 Repeat Questions Insights"):
                total_repeats = repeat_df['Times Asked'].sum()
                unique_repeats = len(repeat_df)
                total_questions = len(df)
                repeat_coverage = (total_repeats / total_questions * 100)
                
                st.markdown(f"""
                **Key Findings:**
                - **{unique_repeats}** questions are asked multiple times
                - These **{unique_repeats}** questions account for **{total_repeats:,}** total asks
                - This represents **{repeat_coverage:.1f}%** of all questions
                
                **Action Items:**
                - Create FAQ entries for top repeat questions
                - Improve search functionality to surface existing answers
                - Consider adding these to onboarding materials
                - Develop self-service content to reduce support burden
                """)
                
                # Show the data table
                st.markdown("**Detailed Repeat Questions:**")
                st.dataframe(repeat_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Response Quality Analysis
        if 'user_feedback' in df.columns and df['user_feedback'].notna().any():
            st.markdown("#### ⭐ Response Quality Analysis")
            st.markdown("Analyzing user feedback to improve response quality.")
            
            feedback_df = df[df['user_feedback'].notna()].copy()

            # Normalize feedback labels from different source conventions
            feedback_map = {
                'good': 'helpful',
                'helpful': 'helpful',
                'thumbs_up': 'helpful',
                'positive': 'helpful',
                '1': 'helpful',
                'true': 'helpful',
                'yes': 'helpful',
                'bad': 'unhelpful',
                'unhelpful': 'unhelpful',
                'thumbs_down': 'unhelpful',
                'negative': 'unhelpful',
                '-1': 'unhelpful',
                'false': 'unhelpful',
                'no': 'unhelpful'
            }

            feedback_df['feedback_norm'] = (
                feedback_df['user_feedback']
                .astype(str)
                .str.strip()
                .str.lower()
                .map(feedback_map)
            )
            feedback_df = feedback_df[feedback_df['feedback_norm'].notna()]

            if feedback_df.empty:
                st.info("Feedback exists, but no recognized Good/Bad labels were found.")
            else:
                col1, col2 = st.columns(2)
            
                with col1:
                    st.markdown("**Overall Feedback Metrics:**")
                    
                    total_feedback = len(feedback_df)
                    helpful_count = len(feedback_df[feedback_df['feedback_norm'] == 'helpful'])
                    unhelpful_count = len(feedback_df[feedback_df['feedback_norm'] == 'unhelpful'])
                    
                    helpful_rate = (helpful_count / total_feedback * 100) if total_feedback > 0 else 0
                    unhelpful_rate = (unhelpful_count / total_feedback * 100) if total_feedback > 0 else 0
                    
                    st.metric("Total Feedback", f"{total_feedback:,}")
                    st.metric("Helpful Rate", f"{helpful_rate:.1f}%", delta=f"{helpful_count:,} responses")
                    st.metric("Unhelpful Rate", f"{unhelpful_rate:.1f}%", delta=f"{unhelpful_count:,} responses")
                
                with col2:
                    st.markdown("**Feedback by Classification:**")
                    
                    if 'classification' in feedback_df.columns:
                        feedback_by_class = feedback_df.groupby(['classification', 'feedback_norm']).size().unstack(fill_value=0)
                        
                        if not feedback_by_class.empty:
                            for classification in feedback_by_class.index:
                                total = feedback_by_class.loc[classification].sum()
                                if 'helpful' in feedback_by_class.columns:
                                    helpful = feedback_by_class.loc[classification, 'helpful']
                                    rate = (helpful / total * 100) if total > 0 else 0
                                    st.markdown(f"**{classification}**: {rate:.1f}% helpful ({total} responses)")
                
                with st.expander("💡 Quality Improvement Recommendations"):
                    if unhelpful_rate > 20:
                        st.warning("""
                        **⚠️ High Unhelpful Rate Detected**
                        
                        With over 20% of responses marked as unhelpful, consider:
                        - Reviewing and improving response templates
                        - Training missionaries and leaders on common question patterns
                        - Implementing response quality checks
                        - Gathering more detailed feedback on what was unhelpful
                        """)
                    else:
                        st.success("""
                        **✅ Good Response Quality**
                        
                        Your helpful rate is strong! Continue to:
                        - Monitor feedback trends for any changes
                        - Share best practices from high-quality responses
                        - Use successful responses as templates
                        """)

    
    # Footer
    st.markdown("---")
    st.info("""
    ### 💡 How to Use These Analytics
    
    - **Track trends** over time to identify seasonal patterns
    - **Monitor geographic distribution** to understand global reach
    - **Analyze peak times** for better resource allocation
    - **Review top topics** to prioritize content creation
    - **Export data** from the Questions Table page for deeper analysis
    """)


if __name__ == "__main__":
    main()
