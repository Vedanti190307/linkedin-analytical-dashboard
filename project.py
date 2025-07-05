import streamlit as st
import pandas as pd
import plotly.express as px
import re
import io

# Set page layout
st.set_page_config(page_title="LinkedIn Analytics", layout="wide")

# Title
st.markdown("<h1 style='text-align: center; font-size: 50px;'>📊 LinkedIn Analytics Dashboard</h1>", unsafe_allow_html=True)

# File uploader
if 'uploaded' not in st.session_state:
    uploaded_file = st.file_uploader("📤 Upload your LinkedIn Excel file", type=["xlsx"])
    if uploaded_file:
        st.session_state.uploaded = uploaded_file
else:
    uploaded_file = st.session_state.uploaded

# Process uploaded file
if uploaded_file:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Info
    platform = df['Platform'].dropna().iloc[0] if 'Platform' in df.columns else "Unknown"
    person = df['Person'].dropna().iloc[0] if 'Person' in df.columns else "N/A"

    # Date Range Selector (Safe)
    min_date = df['Date'].min()
    max_date = df['Date'].max()

    date_range = st.date_input(
        "📅 Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
    else:
        st.warning("Please select a valid start and end date.")

    # Keyword Filter
    keyword = st.text_input("🔍 Search for Keyword in Posts")
    if keyword:
        df = df[df['Post'].astype(str).str.contains(keyword, case=False, na=False)]

    # Metrics Calculation
    df['Likes'] = pd.to_numeric(df['Likes'], errors='coerce')
    df['Comments'] = pd.to_numeric(df['Comments'], errors='coerce')
    df['Shares'] = pd.to_numeric(df['Shares'], errors='coerce')
    df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce')
    df['Total Engagement'] = df['Likes'] + df['Comments'] + df['Shares']

    total_likes = df['Likes'].sum()
    total_comments = df['Comments'].sum()
    total_shares = df['Shares'].sum()
    total_clicks = df['Clicks'].sum()
    total_impressions = df['Impressions'].sum()

    engagement_rate = round(((total_likes + total_comments + total_shares) / total_impressions) * 100, 2) if total_impressions > 0 else 0
    ctr = round((total_clicks / total_impressions) * 100, 2) if total_impressions > 0 else 0
    avg_engagement = round(df['Total Engagement'].mean(), 2)

    top_post = df.loc[df['Likes'].idxmax()]
    top_engaging_post = df.loc[df['Total Engagement'].idxmax()]

    df['Short Post'] = df['Post'].astype(str).str.slice(0, 25) + "..."

    # Educational Post Classification
    educational_keywords = ['learn', 'educational', 'knowledge', 'tips', 'tutorial', 'training', 'course']

    def classify_post_type(post):
        post = str(post).lower()
        if any(keyword in post for keyword in educational_keywords):
            return 'Educational'
        else:
            return 'Other'

    df['Post Type'] = df['Post'].apply(classify_post_type)

    # Count the distribution of each post type
    post_type_counts = df['Post Type'].value_counts().reset_index()
    post_type_counts.columns = ['Post Type', 'Count']

    # Hashtag Analysis
    df['Hashtags'] = df['Post'].astype(str).apply(lambda x: [tag for tag in re.findall(r"#\w+", x)])
    df_exploded = df.explode('Hashtags')
    top_hashtags = df_exploded['Hashtags'].value_counts().head(10).reset_index()
    top_hashtags.columns = ['Hashtag', 'Count']

    # Prepare chart data
    df_time = df.groupby('Date')[['Likes', 'Comments', 'Shares']].sum().reset_index()
    df_area = df.groupby('Date')[['Impressions', 'Clicks']].sum().reset_index()

    # Layout: 3 columns
    st.markdown("📊 Visual Insights")
    col1, col2, col3 = st.columns([1.3, 2, 2])

    with col1:
        st.markdown(" 👤 Person Info")
        st.markdown(f"*Name:* {person}")
        st.markdown(f"*Platform:* {platform}")
        st.markdown(f"*File:* {uploaded_file.name}")

        st.markdown("---")
        st.markdown(" 📊 Metrics")
        st.metric("👍 Likes", int(total_likes))
        st.metric("💬 Comments", int(total_comments))
        st.metric("🔁 Shares", int(total_shares))
        st.metric("👁 Impressions", int(total_impressions))
        st.metric("🔗 Clicks", int(total_clicks))
        st.metric("📈 Engagement Rate", f"{engagement_rate} %")
        st.metric("⚡ CTR", f"{ctr} %")
        st.metric("📊 Avg. Engagement/Post", avg_engagement)

        st.markdown("---")
        st.markdown("🏆 Top Post")
        st.write(f"{top_post['Post']}")
        st.write(f"👍 {top_post['Likes']} | 💬 {top_post['Comments']} | 🔁 {top_post['Shares']}")

        st.markdown("💎 Most Engaging Post")
        st.write(f"{top_engaging_post['Post']}")
        st.write(f"Total Engagement: {top_engaging_post['Total Engagement']}")

    with col2:
        st.markdown(" 📝 Post Type Distribution (Educational vs Other)")
        fig_post_type = px.bar(post_type_counts, x='Post Type', y='Count', title="Distribution of Post Types")
        fig_post_type.update_layout(height=300, title_font_size=18)
        st.plotly_chart(fig_post_type, use_container_width=True)

        st.markdown(" 👍 Likes per Post")
        fig_likes = px.bar(df, x='Short Post', y='Likes', title="Likes per Post")
        fig_likes.update_layout(height=300, title_font_size=18)
        fig_likes.update_xaxes(tickangle=45)
        st.plotly_chart(fig_likes, use_container_width=True)

        st.markdown(" 🥧 Engagement Distribution")
        fig_pie = px.pie(df, names='Short Post', values='Total Engagement', title="Engagement by Post")
        fig_pie.update_layout(height=300, title_font_size=18, legend_title=None)
        st.plotly_chart(fig_pie, use_container_width=True)

       # st.markdown(" 🏷 Top Hashtags")
       # if not top_hashtags.empty:
       #     fig_tags = px.bar(top_hashtags, x='Hashtag', y='Count', title="Top Hashtags")
        #    fig_tags.update_layout(height=300, title_font_size=18)
         #   st.plotly_chart(fig_tags, use_container_width=True)
       # else:
         #   st.info("No hashtags found in posts.")

    with col3:
        st.markdown("📈 Engagement Over Time")
        fig_time = px.line(df_time, x='Date', y=['Likes', 'Comments', 'Shares'], title="Engagement Over Time")
        fig_time.update_layout(height=300, title_font_size=18)
        st.plotly_chart(fig_time, use_container_width=True)

        st.markdown(" 📉 Impressions & Clicks")
        fig_area = px.area(df_area, x='Date', y=['Impressions', 'Clicks'], title="Impressions & Clicks Over Time")
        fig_area.update_layout(height=300, title_font_size=18)
        st.plotly_chart(fig_area, use_container_width=True)

    # Performance Table
    st.markdown(" 📋 Post Performance Table")
    display_cols = ['Date', 'Post', 'Likes', 'Comments', 'Shares', 'Impressions', 'Clicks', 'Total Engagement', 'Post Type']
    st.dataframe(df[display_cols].sort_values(by='Total Engagement', ascending=False).reset_index(drop=True))

    # Download filtered data
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button("📥 Download Filtered Data", buffer.getvalue(), file_name="filtered_linkedin_data.xlsx")