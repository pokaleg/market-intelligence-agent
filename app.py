import streamlit as st
import requests
import json
from collections import defaultdict
from datetime import datetime
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_sector_email(recipient_email, sector_name, articles, sender_email, app_password):
    icon = {
        "Technology": "💻",
        "Healthcare": "🏥",
        "Finance": "💰",
        "Retail": "🛍️",
        "Legal": "⚖️",
        "General": "📊"
    }.get(sector_name, "📊")
    
    article_rows = ""
    for article in articles:
        sentiment_color = {
            "positive": "#22c55e",
            "negative": "#ef4444",
            "neutral": "#94a3b8"
        }.get(article["sentiment"], "#94a3b8")
        
        urgency_color = {
            "high": "#ef4444",
            "medium": "#f59e0b",
            "low": "#22c55e"
        }.get(article["urgency"], "#94a3b8")
        
        article_rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 16px; font-weight: 600;">
                <a href="{article['link']}" style="color: #3b82f6; text-decoration: none;">
                    {article['title']}
                </a>
            </td>
            <td style="padding: 16px; text-align: center;">
                <span style="background: {sentiment_color}20; color: {sentiment_color}; 
                    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                    {article['sentiment'].upper()}
                </span>
            </td>
            <td style="padding: 16px; text-align: center;">
                <span style="background: {urgency_color}20; color: {urgency_color}; 
                    padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">
                    {article['urgency'].upper()}
                </span>
            </td>
            <td style="padding: 16px; font-size: 13px; color: #475569;">
                {article['key_insight']}
            </td>
            <td style="padding: 16px; font-size: 13px; color: #475569;">
                {article['recommended_action']}
            </td>
        </tr>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: sans-serif; background: #f8fafc; padding: 32px;">
        <div style="max-width: 1200px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #1e293b, #3b82f6); 
                color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px;">
                <h1 style="margin: 0 0 8px 0;">{icon} {sector_name} Market Intelligence</h1>
                <p style="margin: 0; opacity: 0.8;">
                    {len(articles)} articles | {datetime.now().strftime('%B %d, %Y')}
                </p>
                <p style="margin: 8px 0 0 0; opacity: 0.7;">
                    Built with Streamlit + Groq AI | Gayatri Pokale
                </p>
            </div>
            <table style="width: 100%; border-collapse: collapse; 
                background: white; border-radius: 12px; overflow: hidden;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: #f8fafc;">
                        <th style="padding: 12px 16px; text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase;">Article</th>
                        <th style="padding: 12px 16px; text-align: center; font-size: 12px; color: #64748b; text-transform: uppercase;">Sentiment</th>
                        <th style="padding: 12px 16px; text-align: center; font-size: 12px; color: #64748b; text-transform: uppercase;">Urgency</th>
                        <th style="padding: 12px 16px; text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase;">Key Insight</th>
                        <th style="padding: 12px 16px; text-align: left; font-size: 12px; color: #64748b; text-transform: uppercase;">Action</th>
                    </tr>
                </thead>
                <tbody>{article_rows}</tbody>
            </table>
            <p style="text-align: center; color: #94a3b8; font-size: 13px; margin-top: 24px;">
                Market Intelligence Agent V2 | Gayatri Pokale | Assignment 5A
            </p>
        </div>
    </body>
    </html>
    """
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"{icon} {sector_name} Intelligence — {len(articles)} articles — {datetime.now().strftime('%b %d, %Y')}"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.attach(MIMEText(html_content, 'html'))
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    
    return True


st.set_page_config(
    page_title="Market Intelligence Agent",
    page_icon="📊",
    layout="wide"
)

SECTOR_ICONS = {
    "Technology": "💻",
    "Healthcare": "🏥",
    "Finance": "💰",
    "Retail": "🛍️",
    "Legal": "⚖️",
    "General": "📊",
    "General Business": "📊"
}

st.title("📊 Market Intelligence Agent V2")
st.markdown("**Automatically analyze business news and receive personalized sector intelligence**")
st.divider()

if "analyzed_articles" not in st.session_state:
    st.session_state.analyzed_articles = []
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

col1, col2 = st.columns(2)

with col1:
    st.subheader("⚙️ Configuration")
    email = st.text_input(
        "Your Email Address",
        placeholder="yourname@email.com",
        help="The intelligence report will be sent to this email"
    )
    num_articles = st.slider(
        "Number of articles to analyze",
        min_value=5,
        max_value=20,
        value=10,
        help="More articles = more comprehensive report"
    )

with col2:
    st.subheader("🎯 Select Sectors to Monitor")
    selected_sectors = st.multiselect(
        "Choose which business sectors to include",
        options=[
            "Technology",
            "Healthcare",
            "Finance",
            "Retail",
            "Legal",
            "General Business"
        ],
        default=["Technology", "General Business"],
        help="Select sectors — results update instantly"
    )

st.divider()

run_clicked = st.button(
    "▶ Run Market Intelligence Analysis",
    type="primary",
    use_container_width=True
)

if run_clicked:
    if not email:
        st.error("❌ Please enter your email address before running.")
        st.stop()

    if "@" not in email or "." not in email:
        st.error("❌ Please enter a valid email address (example: name@company.com)")
        st.stop()

    if not selected_sectors:
        st.error("❌ Please select at least one sector to monitor.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()

    status.info("📡 Step 1/3 — Fetching articles from news sources...")
    progress.progress(25)

    articles = []
    feeds = [
        ("CNBC Business", "https://www.cnbc.com/id/10001147/device/rss/rss.html"),
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("Amazon News", "https://www.aboutamazon.com/news/rss")
    ]

    for source_name, url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:num_articles//3 + 1]:
                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:200],
                    "link": entry.get("link", ""),
                    "source": source_name
                })
        except:
            pass

    if len(articles) == 0:
        st.error("❌ Could not fetch articles. Please check your internet connection.")
        st.stop()

    status.info("🤖 Step 2/3 — Groq AI analyzing articles...")
    progress.progress(60)

    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    except:
        groq_api_key = ""

    analyzed = []
    for article in articles[:num_articles]:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a market intelligence analyst. Respond ONLY with a JSON object with these exact fields: sentiment (positive/negative/neutral), urgency (high/medium/low), key_insight (one sentence), recommended_action (one sentence), sector (must be exactly one of: Healthcare, Technology, Retail, Finance, Legal, General). No extra text."
                        },
                        {
                            "role": "user",
                            "content": f"Title: {article['title']}\nSummary: {article['summary']}"
                        }
                    ]
                },
                timeout=10
            )
            data = response.json()
            ai_text = data["choices"][0]["message"]["content"]
            cleaned = ai_text.replace("```json", "").replace("```", "").strip()
            ai_result = json.loads(cleaned)

            analyzed.append({
                **article,
                "sentiment": ai_result.get("sentiment", "neutral"),
                "urgency": ai_result.get("urgency", "low"),
                "key_insight": ai_result.get("key_insight", ""),
                "recommended_action": ai_result.get("recommended_action", ""),
                "sector": ai_result.get("sector", "General")
            })
        except:
            analyzed.append({
                **article,
                "sentiment": "neutral",
                "urgency": "low",
                "key_insight": "Analysis unavailable",
                "recommended_action": "Review manually",
                "sector": "General"
            })

    st.session_state.analyzed_articles = analyzed
    st.session_state.analysis_done = True

    progress.progress(100)
    status.success("✅ Analysis complete!")

# ── Everything below only runs after analysis is done ──
if st.session_state.analysis_done and st.session_state.analyzed_articles:

    all_articles = st.session_state.analyzed_articles

    # Filter by selected sectors
    mapped_sectors = []
    for s in selected_sectors:
        if s == "General Business":
            mapped_sectors.append("General")
        else:
            mapped_sectors.append(s)

    filtered = [
        a for a in all_articles
        if a["sector"] in mapped_sectors
    ] if mapped_sectors else all_articles

    if len(filtered) == 0:
        st.warning("⚠️ No articles found for selected sectors. Try selecting different sectors.")
    else:
        st.divider()

        # Stats
        st.subheader("📊 Overall Summary")
        c1, c2, c3, c4 = st.columns(4)
        positive = len([a for a in filtered if a["sentiment"] == "positive"])
        negative = len([a for a in filtered if a["sentiment"] == "negative"])
        high_urgency = len([a for a in filtered if a["urgency"] == "high"])

        c1.metric("📰 Total Articles", len(filtered))
        c2.metric("🟢 Positive", positive)
        c3.metric("🔴 Negative", negative)
        c4.metric("🚨 High Urgency", high_urgency)

        st.divider()

        # High urgency alerts
        urgent = [a for a in filtered if a["urgency"] == "high"]
        if urgent:
            st.subheader("🚨 High Urgency Alerts")
            for article in urgent:
                st.error(f"""
**{article['title']}**
💡 {article['key_insight']}
➡️ **Action:** {article['recommended_action']}
[Read article →]({article['link']})
                """)
            st.divider()

        # Group by sector
        sector_groups = defaultdict(list)
        for article in filtered:
            sector_groups[article["sector"]].append(article)

        # Show articles by sector
        st.subheader("📰 Articles by Sector")
        st.caption("💡 Use the sector dropdown above to filter — results update instantly!")

        for sector_name, sector_articles in sector_groups.items():
            icon = SECTOR_ICONS.get(sector_name, "📊")
            st.markdown(f"## {icon} {sector_name}")
            st.caption(f"{len(sector_articles)} articles")

            for article in sector_articles:
                sentiment_icon = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}.get(article["sentiment"], "⚪")
                urgency_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(article["urgency"], "🟢")

                with st.expander(f"{sentiment_icon} {urgency_icon} {article['title']}"):
                    left, right = st.columns(2)
                    with left:
                        st.write(f"**Source:** {article['source']}")
                        st.write(f"**Sentiment:** {sentiment_icon} {article['sentiment'].upper()}")
                        st.write(f"**Urgency:** {urgency_icon} {article['urgency'].upper()}")
                    with right:
                        st.write(f"**💡 Key Insight:** {article['key_insight']}")
                        st.write(f"**➡️ Action:** {article['recommended_action']}")
                    st.markdown(f"[Read full article →]({article['link']})")

            st.divider()

        # ── Email section ──
        st.subheader("📧 Sending Sector Reports to Your Inbox")

        try:
            sender = st.secrets["GMAIL_SENDER"]
            password = st.secrets["GMAIL_APP_PASSWORD"]

            email_progress = st.progress(0)
            total_sectors = len(sector_groups)
            emails_sent = []

            for i, (sector_name, sector_articles) in enumerate(sector_groups.items()):
                icon = SECTOR_ICONS.get(sector_name, "📊")
                with st.spinner(f"Sending {icon} {sector_name} report..."):
                    try:
                        send_sector_email(
                            email,
                            sector_name,
                            sector_articles,
                            sender,
                            password
                        )
                        emails_sent.append(sector_name)
                        st.success(f"✅ {icon} {sector_name} report sent to {email}!")
                    except Exception as e:
                        st.warning(f"⚠️ Could not send {sector_name} email. Error: {str(e)}")

                email_progress.progress((i + 1) / total_sectors)

            if emails_sent:
                st.success(f"🎉 {len(emails_sent)} sector reports delivered to {email}!")
                st.balloons()

        except KeyError:
            st.info("📧 Email not configured. Add Gmail credentials to secrets.toml")
        except Exception as e:
            st.error(f"❌ Email error: {str(e)}")

# Footer
st.divider()
st.markdown("*Market Intelligence Agent V2 | Built with Streamlit + Groq AI | Gayatri Pokale*")