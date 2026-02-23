"""
Visualization components for charts and analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from config import BYU_COLORS, CHART_COLOR_PALETTE


def _normalize_feedback(value):
    """Map raw feedback values to helpful/unhelpful."""
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {'good', 'helpful', 'thumbs_up', 'positive', '1', 'true', 'yes'}:
        return 'helpful'
    if text in {'bad', 'unhelpful', 'thumbs_down', 'negative', '-1', 'false', 'no'}:
        return 'unhelpful'
    return None


def create_kpi_cards(kpis: Dict[str, any]):
    """
    Display KPI cards in a grid layout.
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Questions Processed",
            value=f"{kpis['total_questions']:,}",
            help="Total number of questions analyzed"
        )
    
    with col2:
        matched_pct = (kpis['matched_existing'] / kpis['total_questions'] * 100) if kpis['total_questions'] > 0 else 0
        st.metric(
            label="✅ Matched to Existing Topics",
            value=f"{kpis['matched_existing']:,}",
            delta=f"{matched_pct:.1f}%",
            help="Questions successfully matched to existing topics"
        )
    
    with col3:
        st.metric(
            label="🆕 New Topics Discovered",
            value=f"{kpis['new_topics_discovered']:,}",
            delta=f"{kpis['questions_in_new_topics']} questions",
            help="Unique new topics identified by clustering"
        )
    
    with col4:
        st.metric(
            label="🌍 Countries",
            value=f"{kpis['countries']:,}",
            help="Number of unique countries represented"
        )
    
    # Second row of KPIs
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        if kpis['avg_similarity'] > 0:
            st.metric(
                label="📈 Avg Similarity Score",
                value=f"{kpis['avg_similarity']:.3f}",
                help="Average similarity score for matched questions"
            )
    
    with col6:
        if kpis['last_updated']:
            last_updated_str = kpis['last_updated'].strftime("%Y-%m-%d %H:%M")
            st.metric(
                label="🕐 Last Updated",
                value=last_updated_str,
                help="Last time data was updated"
            )


def plot_classification_distribution(df: pd.DataFrame):
    """
    Pie chart showing distribution of existing vs new topics.
    """
    if 'classification' not in df.columns or df.empty:
        st.info("No classification data available")
        return
    
    classification_counts = df['classification'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=classification_counts.index,
        values=classification_counts.values,
        hole=0.4,
        marker=dict(colors=[BYU_COLORS['primary'], BYU_COLORS['secondary']]),
        textinfo='label+percent+value',
        textfont=dict(size=14)
    )])
    
    fig.update_layout(
        title="Question Classification Distribution",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, width='stretch', key="classification_distribution_pie")


def plot_country_distribution(df: pd.DataFrame, top_n: int = 10):
    """
    Bar chart showing top countries by question volume.
    """
    if 'country' not in df.columns or df.empty:
        st.info("No country data available")
        return
    
    country_counts = df['country'].value_counts().head(top_n)
    
    fig = go.Figure(data=[go.Bar(
        x=country_counts.values,
        y=country_counts.index,
        orientation='h',
        marker=dict(color=BYU_COLORS['primary']),
        text=country_counts.values,
        textposition='outside'
    )])
    
    fig.update_layout(
        title=f"Top {top_n} Countries by Question Volume",
        xaxis_title="Number of Questions",
        yaxis_title="Country",
        height=400,
        showlegend=False,
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, width='stretch', key="country_distribution_bar")


def plot_timeline(df: pd.DataFrame, key: str = "timeline_line_chart"):
    """
    Line chart showing questions over time.
    
    Args:
        df: DataFrame with timestamp and classification columns
        key: Unique key for the plotly chart (required if used multiple times)
    """
    if 'timestamp' not in df.columns or df.empty:
        st.info("No timestamp data available")
        return
    
    # Group by date and classification
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.date
    
    timeline_data = df_copy.groupby(['date', 'classification']).size().reset_index(name='count')
    
    fig = px.line(
        timeline_data,
        x='date',
        y='count',
        color='classification',
        color_discrete_map={
            'Existing Topic': BYU_COLORS['primary'],
            'New Topic': BYU_COLORS['secondary']
        },
        markers=True
    )
    
    fig.update_layout(
        title="Question Volume Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Questions",
        height=400,
        hovermode='x unified',
        legend=dict(
            title="Classification",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, width='stretch', key=key)


def plot_similarity_distribution(df: pd.DataFrame):
    """
    Histogram showing distribution of similarity scores.
    """
    if 'similarity_score' not in df.columns or df.empty:
        st.info("No similarity score data available")
        return
    
    # Filter to only existing topics (which have similarity scores)
    df_filtered = df[df['classification'] == 'Existing Topic']
    
    if df_filtered.empty:
        st.info("No similarity scores available for existing topics")
        return
    
    fig = go.Figure(data=[go.Histogram(
        x=df_filtered['similarity_score'],
        nbinsx=30,
        marker=dict(color=BYU_COLORS['primary']),
        hovertemplate='Similarity Score: %{x:.3f}<br>Count: %{y}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Similarity Score Distribution (Existing Topics)",
        xaxis_title="Similarity Score",
        yaxis_title="Number of Questions",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch', key="similarity_distribution_histogram")


def plot_top_topics(df: pd.DataFrame, top_n: int = 10):
    """
    Bar chart showing most common matched topics.
    """
    if 'matched_topic' not in df.columns or df.empty:
        st.info("No topic data available")
        return
    
    # Filter to existing topics only
    df_filtered = df[df['classification'] == 'Existing Topic']
    
    if df_filtered.empty:
        st.info("No matched topics available")
        return
    
    topic_counts = df_filtered['matched_topic'].value_counts().head(top_n)
    
    fig = go.Figure(data=[go.Bar(
        x=topic_counts.values,
        y=topic_counts.index,
        orientation='h',
        marker=dict(color=BYU_COLORS['accent1']),
        text=topic_counts.values,
        textposition='outside'
    )])
    
    fig.update_layout(
        title=f"Top {top_n} Most Common Topics",
        xaxis_title="Number of Questions",
        yaxis_title="Topic",
        height=500,
        showlegend=False,
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, width='stretch', key="top_topics_bar")


def plot_hourly_heatmap(df: pd.DataFrame):
    """
    Heatmap showing question volume by day of week and hour.
    """
    if 'timestamp' not in df.columns or df.empty:
        st.info("No timestamp data available")
        return
    
    df_copy = df.copy()
    df_copy['hour'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.hour
    df_copy['day_of_week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.day_name()
    
    # Create pivot table
    heatmap_data = df_copy.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex([day for day in day_order if day in heatmap_pivot.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='Blues',
        hovertemplate='Day: %{y}<br>Hour: %{x}:00<br>Questions: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Question Volume Heatmap (Day × Hour)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )
    
    st.plotly_chart(fig, width='stretch', key="hourly_heatmap")


def plot_language_distribution(df: pd.DataFrame):
    """
    Pie chart showing distribution of user languages.
    """
    if 'user_language' not in df.columns or df.empty:
        st.info("No language data available")
        return
    
    language_counts = df['user_language'].value_counts().head(10)
    
    fig = go.Figure(data=[go.Pie(
        labels=language_counts.index,
        values=language_counts.values,
        hole=0.3,
        marker=dict(colors=CHART_COLOR_PALETTE),
        textinfo='label+percent',
        textfont=dict(size=12)
    )])
    
    fig.update_layout(
        title="User Language Distribution",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, width='stretch', key="language_distribution_pie")


# ============ NEW VISUALIZATION FUNCTIONS FOR ENHANCED INSIGHTS ============

def plot_weekly_topic_trends(df: pd.DataFrame, selected_week: str = None, key: str = "weekly_topic_trends"):
    """
    Show top topics for a specific week.
    
    Args:
        df: DataFrame with timestamp and matched_topic columns
        selected_week: Week string in format 'YYYY-WW' or None for latest week
        key: Unique key for the plotly chart
    """
    if 'timestamp' not in df.columns or 'matched_topic' not in df.columns or df.empty:
        st.info("No timestamp or topic data available")
        return None
    
    df_copy = df[df['classification'] == 'Existing Topic'].copy()
    if df_copy.empty:
        st.info("No topic data available for the selected period")
        return None
    
    df_copy['week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.strftime('%Y-W%U')
    
    if selected_week:
        weekly_data = df_copy[df_copy['week'] == selected_week]
    else:
        # Use the most recent week
        latest_week = df_copy['week'].max()
        weekly_data = df_copy[df_copy['week'] == latest_week]
        selected_week = latest_week
    
    if weekly_data.empty:
        st.warning(f"No data available for week {selected_week}")
        return None
    
    topic_counts = weekly_data['matched_topic'].value_counts().head(10)
    
    fig = go.Figure(data=[go.Bar(
        x=topic_counts.values,
        y=topic_counts.index,
        orientation='h',
        marker=dict(color=BYU_COLORS['accent1']),
        text=topic_counts.values,
        textposition='outside'
    )])
    
    fig.update_layout(
        title=f"Top 10 Topics for Week {selected_week}",
        xaxis_title="Number of Questions",
        yaxis_title="Topic",
        height=500,
        showlegend=False,
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    return topic_counts


def plot_week_over_week_comparison(df: pd.DataFrame, week1: str, week2: str, key: str = "week_comparison"):
    """
    Compare top topics between two weeks.
    
    Args:
        df: DataFrame with timestamp and matched_topic columns
        week1: First week string in format 'YYYY-WW'
        week2: Second week string in format 'YYYY-WW'
        key: Unique key for the plotly chart
    """
    if 'timestamp' not in df.columns or 'matched_topic' not in df.columns or df.empty:
        st.info("No timestamp or topic data available")
        return
    
    df_copy = df[df['classification'] == 'Existing Topic'].copy()
    df_copy['week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.strftime('%Y-W%U')
    
    week1_data = df_copy[df_copy['week'] == week1]['matched_topic'].value_counts().head(10)
    week2_data = df_copy[df_copy['week'] == week2]['matched_topic'].value_counts().head(10)
    
    # Get all topics from both weeks
    all_topics = set(week1_data.index) | set(week2_data.index)
    
    comparison_data = pd.DataFrame({
        week1: [week1_data.get(topic, 0) for topic in all_topics],
        week2: [week2_data.get(topic, 0) for topic in all_topics]
    }, index=list(all_topics))
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=f'Week {week1}',
        y=comparison_data.index,
        x=comparison_data[week1],
        orientation='h',
        marker=dict(color=BYU_COLORS['primary'])
    ))
    fig.add_trace(go.Bar(
        name=f'Week {week2}',
        y=comparison_data.index,
        x=comparison_data[week2],
        orientation='h',
        marker=dict(color=BYU_COLORS['secondary'])
    ))
    
    fig.update_layout(
        title=f"Topic Comparison: Week {week1} vs Week {week2}",
        xaxis_title="Number of Questions",
        yaxis_title="Topic",
        height=500,
        barmode='group',
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, width='stretch', key=key)


def plot_regional_topic_preferences(df: pd.DataFrame, by: str = 'country', top_n: int = 5, key: str = "regional_topics"):
    """
    Show top topics by region (country or state).
    
    Args:
        df: DataFrame with geographic and topic columns
        by: 'country' or 'state' for grouping
        top_n: Number of top regions to show
        key: Unique key for the plotly chart
    """
    if by not in df.columns or 'matched_topic' not in df.columns or df.empty:
        st.info(f"No {by} or topic data available")
        return
    
    df_copy = df[df['classification'] == 'Existing Topic'].copy()
    if df_copy.empty:
        st.info("No topic data available")
        return
    
    # Get top N regions by question count
    top_regions = df_copy[by].value_counts().head(top_n).index
    
    regional_data = []
    for region in top_regions:
        region_df = df_copy[df_copy[by] == region]
        top_topic = region_df['matched_topic'].value_counts().head(1)
        if not top_topic.empty:
            regional_data.append({
                'Region': region,
                'Top Topic': top_topic.index[0],
                'Question Count': top_topic.values[0],
                'Total Questions': len(region_df)
            })
    
    if not regional_data:
        st.info("No regional topic data available")
        return
    
    regional_df = pd.DataFrame(regional_data)
    
    fig = go.Figure(data=[go.Bar(
        x=regional_df['Region'],
        y=regional_df['Question Count'],
        text=regional_df['Top Topic'],
        textposition='outside',
        marker=dict(color=BYU_COLORS['accent1']),
        hovertemplate='<b>%{x}</b><br>Top Topic: %{text}<br>Questions: %{y}<br>Total: ' + 
                      regional_df['Total Questions'].astype(str) + '<extra></extra>'
    )])
    
    fig.update_layout(
        title=f"Top Topic by {by.capitalize()} (Top {top_n} Regions)",
        xaxis_title=by.capitalize(),
        yaxis_title="Questions for Top Topic",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    return regional_df


def plot_feedback_quality_by_region(df: pd.DataFrame, by: str = 'country', key: str = "feedback_quality"):
    """
    Show unhelpful response rates by region.
    
    Args:
        df: DataFrame with geographic and user_feedback columns
        by: 'country' or 'state' for grouping
        key: Unique key for the plotly chart
    """
    if by not in df.columns or 'user_feedback' not in df.columns or df.empty:
        st.info(f"No {by} or feedback data available")
        return None
    
    df_copy = df.copy()
    df_copy['feedback_norm'] = df_copy['user_feedback'].apply(_normalize_feedback)
    df_copy = df_copy[df_copy['feedback_norm'].notna()]
    
    if df_copy.empty:
        st.info("No feedback data available")
        return None
    
    # Calculate unhelpful rate by region
    regional_feedback = df_copy.groupby(by).agg({
        'feedback_norm': lambda x: (x == 'unhelpful').sum() / len(x) * 100 if len(x) > 0 else 0,
        'question': 'count'
    }).reset_index()
    regional_feedback.columns = [by, 'unhelpful_rate', 'total_feedback']
    
    # Filter regions with at least 10 feedback responses
    regional_feedback = regional_feedback[regional_feedback['total_feedback'] >= 10]
    regional_feedback = regional_feedback.sort_values('unhelpful_rate', ascending=False).head(15)
    
    if regional_feedback.empty:
        st.info("Insufficient feedback data for regional analysis")
        return None
    
    fig = go.Figure(data=[go.Bar(
        x=regional_feedback[by],
        y=regional_feedback['unhelpful_rate'],
        marker=dict(
            color=regional_feedback['unhelpful_rate'],
            colorscale=[[0, '#4caf50'], [0.5, '#FFB933'], [1, '#C5050C']],
            showscale=True,
            colorbar=dict(title="Unhelpful %")
        ),
        text=[f"{rate:.1f}%" for rate in regional_feedback['unhelpful_rate']],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Unhelpful Rate: %{y:.1f}%<br>Total Feedback: ' + 
                      regional_feedback['total_feedback'].astype(str) + '<extra></extra>'
    )])
    
    fig.update_layout(
        title=f"Unhelpful Response Rate by {by.capitalize()}",
        xaxis_title=by.capitalize(),
        yaxis_title="Unhelpful Rate (%)",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    return regional_feedback


def plot_sentiment_distribution(df: pd.DataFrame, key: str = "sentiment_dist"):
    """
    Analyze and display sentiment distribution of questions.
    Simple sentiment based on question characteristics.
    
    Args:
        df: DataFrame with question column
        key: Unique key for the plotly chart
    """
    if 'question' not in df.columns or df.empty:
        st.info("No question data available")
        return None
    
    df_copy = df.copy()
    
    # Simple sentiment detection based on keywords and punctuation
    def detect_sentiment(question):
        if pd.isna(question):
            return 'Neutral'
        question_lower = str(question).lower()
        
        # Negative indicators
        negative_words = ['not', 'no', 'never', 'can\'t', 'cannot', 'won\'t', 'don\'t', 'problem', \
                  'issue', 'error', 'fail', 'failed', 'failure', 'wrong', 'difficult', \
                  'confused', 'help', 'frustrated', 'unable', 'delay', 'late', 'missing', \
                  'lost', 'broken', 'bug', 'crash', 'slow', 'unresponsive', 'disconnect', \
                  'timeout', 'cancel', 'cancelled', 'reject', 'rejected', 'incomplete', \
                  'conflict', 'error message', 'blocked', 'denied', 'unavailable', 'complain']

        # Positive indicators
        positive_words = ['thank', 'great', 'good', 'excellent', 'appreciate', 'perfect', 'love']
        
        negative_count = sum(1 for word in negative_words if word in question_lower)
        positive_count = sum(1 for word in positive_words if word in question_lower)
        
        # Questions with multiple question marks or exclamation marks suggest urgency/frustration
        if question.count('?') > 1 or question.count('!') > 0:
            negative_count += 1
        
        if negative_count > positive_count:
            return 'Negative/Urgent'
        elif positive_count > negative_count:
            return 'Positive'
        else:
            return 'Neutral'
    
    df_copy['sentiment'] = df_copy['question'].apply(detect_sentiment)
    sentiment_counts = df_copy['sentiment'].value_counts()
    
    colors = {
        'Negative/Urgent': BYU_COLORS['accent2'],
        'Neutral': BYU_COLORS['neutral'],
        'Positive': '#4caf50'
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=sentiment_counts.index,
        values=sentiment_counts.values,
        hole=0.4,
        marker=dict(colors=[colors.get(label, BYU_COLORS['primary']) for label in sentiment_counts.index]),
        textinfo='label+percent+value',
        textfont=dict(size=14)
    )])
    
    fig.update_layout(
        title="Question Sentiment Distribution",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    return df_copy[['question', 'sentiment']]


def plot_topic_evolution(df: pd.DataFrame, top_n: int = 5, key: str = "topic_evolution"):
    """
    Show how topic popularity has evolved over time.
    
    Args:
        df: DataFrame with timestamp and matched_topic columns
        top_n: Number of top topics to track
        key: Unique key for the plotly chart
    """
    if 'timestamp' not in df.columns or 'matched_topic' not in df.columns or df.empty:
        st.info("No timestamp or topic data available")
        return
    
    df_copy = df[df['classification'] == 'Existing Topic'].copy()
    if df_copy.empty:
        st.info("No topic data available")
        return
    
    # Get top N topics overall
    top_topics = df_copy['matched_topic'].value_counts().head(top_n).index
    
    df_copy['week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.to_period('W').astype(str)
    
    # Create weekly counts for each top topic
    evolution_data = []
    for week in sorted(df_copy['week'].unique()):
        week_data = df_copy[df_copy['week'] == week]
        for topic in top_topics:
            count = len(week_data[week_data['matched_topic'] == topic])
            evolution_data.append({
                'Week': week,
                'Topic': topic,
                'Count': count
            })
    
    evolution_df = pd.DataFrame(evolution_data)
    
    fig = px.line(
        evolution_df,
        x='Week',
        y='Count',
        color='Topic',
        markers=True,
        color_discrete_sequence=CHART_COLOR_PALETTE
    )
    
    fig.update_layout(
        title=f"Topic Evolution Over Time (Top {top_n} Topics)",
        xaxis_title="Week",
        yaxis_title="Number of Questions",
        height=500,
        hovermode='x unified',
        legend=dict(
            title="Topic",
            orientation="h",
            yanchor="bottom",
            y=-0.7,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, width='stretch', key=key)


def identify_repeat_questions(df: pd.DataFrame, similarity_threshold: float = 0.9, key: str = "repeat_questions"):
    """
    Identify and display frequently repeated questions.
    
    Args:
        df: DataFrame with question column
        similarity_threshold: Threshold for considering questions as repeats (0-1)
        key: Unique key for display
    """
    if 'question' not in df.columns or df.empty:
        st.info("No question data available")
        return None
    
    df_copy = df.copy()
    
    # Normalize questions for comparison
    df_copy['normalized_question'] = df_copy['question'].str.lower().str.strip()
    
    # Count exact duplicates
    question_counts = df_copy['normalized_question'].value_counts()
    
    # Filter to questions asked more than once
    repeat_questions = question_counts[question_counts > 1].head(20)
    
    if repeat_questions.empty:
        st.info("No repeat questions found")
        return None
    
    # Create display dataframe with original question text
    repeat_data = []
    for norm_q, count in repeat_questions.items():
        original_q = df_copy[df_copy['normalized_question'] == norm_q]['question'].iloc[0]
        repeat_data.append({
            'Question': original_q,
            'Times Asked': count,
            'Percentage': (count / len(df_copy) * 100)
        })
    
    repeat_df = pd.DataFrame(repeat_data)
    
    fig = go.Figure(data=[go.Bar(
        x=repeat_df['Times Asked'],
        y=repeat_df['Question'].str[:60] + '...',  # Truncate for display
        orientation='h',
        marker=dict(color=BYU_COLORS['accent1']),
        text=repeat_df['Times Asked'],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Asked: %{x} times<br>Percentage: %{customdata:.2f}%<extra></extra>',
        customdata=repeat_df['Percentage']
    )])
    
    fig.update_layout(
        title="Top 20 Most Frequently Asked Questions",
        xaxis_title="Times Asked",
        yaxis_title="Question",
        height=600,
        showlegend=False,
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    return repeat_df


def plot_activity_heatmap_with_insights(df: pd.DataFrame, key: str = "activity_heatmap"):
    """
    Enhanced heatmap with peak/low activity insights.
    
    Args:
        df: DataFrame with timestamp column
        key: Unique key for the plotly chart
    """
    if 'timestamp' not in df.columns or df.empty:
        st.info("No timestamp data available")
        return None
    
    df_copy = df.copy()
    df_copy['hour'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.hour
    df_copy['day_of_week'] = pd.to_datetime(df_copy['timestamp'], format='ISO8601').dt.day_name()
    
    # Create pivot table
    heatmap_data = df_copy.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex([day for day in day_order if day in heatmap_pivot.index])
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale='Blues',
        hovertemplate='Day: %{y}<br>Hour: %{x}:00<br>Questions: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Question Activity Heatmap (Day × Hour)",
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        height=400
    )
    
    st.plotly_chart(fig, width='stretch', key=key)
    
    # Calculate insights
    total_by_hour = df_copy.groupby('hour').size()
    peak_hour = total_by_hour.idxmax()
    low_hour = total_by_hour.idxmin()
    
    total_by_day = df_copy.groupby('day_of_week').size()
    # Reorder for proper comparison
    total_by_day = total_by_day.reindex(day_order)
    peak_day = total_by_day.idxmax()
    low_day = total_by_day.idxmin()
    
    insights = {
        'peak_hour': peak_hour,
        'peak_hour_count': total_by_hour[peak_hour],
        'low_hour': low_hour,
        'low_hour_count': total_by_hour[low_hour],
        'peak_day': peak_day,
        'peak_day_count': total_by_day[peak_day],
        'low_day': low_day,
        'low_day_count': total_by_day[low_day]
    }
    
    return insights

