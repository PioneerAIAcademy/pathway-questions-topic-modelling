# BYU Pathway Dashboard v2.0.0

Interactive Streamlit dashboard for analyzing student questions and discovering topics with advanced insights.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure .env file
echo "AWS_ACCESS_KEY_ID=your_key" > ../.env
echo "AWS_SECRET_ACCESS_KEY=your_secret" >> ../.env

# Run dashboard
streamlit run app.py
```

## Features

### Core Analytics
- **Comprehensive Data Analysis**: Analyze thousands of questions from Langfuse data
- **Advanced Filtering**: Filter by classification, date, country, similarity, and text search
- **Rich Visualizations**: Distributions, timelines, heatmaps, and more
- **Topic Discovery**: Explore newly discovered topics through clustering
- **Dark/Light Theme**: Toggle between themes for comfortable viewing

### New Enhanced Features ✨
- **📅 Weekly Insights**: 
  - Week-by-week topic analysis
  - Week-over-week comparison
  - Topic evolution tracking
  - Trending topics identification

- **🌍 Regional Insights**: 
  - Geographic topic preferences by country and state
  - Regional feedback quality analysis
  - Localization opportunity identification
  - Unhelpful response tracking by region

- **🔬 Advanced Analytics**:
  - Sentiment analysis on questions
  - Repeat question identification
  - Response quality metrics
  - Peak/low activity insights with scheduling recommendations

## Pages

1. **📊 Home** - KPIs and overview dashboard
2. **📋 Questions Table** - Interactive table with filters and search
3. **📈 Trends & Analytics** - Detailed visualizations with 5 analysis tabs:
   - Overview
   - Geographic Insights
   - Temporal Patterns (with activity heatmap insights)
   - Topic Analysis
   - Advanced Insights (NEW: sentiment, repeat questions, quality metrics)
4. **🆕 New Topics** - Explore discovered topics from clustering
5. **📅 Weekly Insights** (NEW) - Week-by-week analysis and comparisons
6. **🌍 Regional Insights** (NEW) - Geographic patterns and feedback quality

## Configuration

Edit `config.py` for:
- Cache TTL (default: 3600s)
- Display columns
- BYU brand colors
- S3 bucket settings
- Theme customization

## Data Files (from S3)

- `pathway_questions_review_*.parquet` - All questions with classifications
- `similar_questions_*.parquet` - Questions matched to existing topics
- `new_topics_*.parquet` - Discovered topics from clustering
- `topic_distribution_*.parquet` - Topic statistics

Dashboard automatically loads the most recent files with timestamp suffixes.

## Key Insights Provided

### Weekly Analysis
- Identify trending topics week by week
- Compare consecutive weeks for pattern detection
- Track topic evolution over time
- Seasonal trend identification

### Regional Analysis
- Understand regional topic preferences
- Identify localization opportunities
- Track response quality by geography
- Optimize content for specific regions

### Advanced Analytics
- Question sentiment distribution (Positive, Neutral, Negative/Urgent)
- Most frequently asked questions (FAQ candidates)
- Response quality metrics and improvement recommendations
- Peak activity times for resource allocation

## Best Practices

1. **Resource Allocation**: Use peak activity insights to schedule support missionaries and leaders
2. **Content Strategy**: Create FAQs from repeat questions
3. **Localization**: Address regions with high unhelpful response rates
4. **Trend Monitoring**: Track weekly trends to identify emerging concerns
5. **Quality Improvement**: Monitor sentiment and feedback metrics

## Troubleshooting

- **No data**: Check AWS credentials and S3 bucket name in `.env` file
- **Slow performance**: Increase `CACHE_TTL` in config.py or refresh data
- **Missing columns**: Verify parquet files from notebook contain all expected fields
- **Visualization errors**: Ensure data has required columns (timestamp, country, etc.)

## Development Notes

- All visualizations are in `utils/visualizations.py`
- Data loading and caching in `utils/data_loader.py`
- Page-specific logic in `pages/` directory
- Theme styling in `config.py` (supports dark/light modes)

See main project README for full documentation and notebook integration details.

