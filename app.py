import streamlit as st
import requests
import json
from collections import defaultdict
from datetime import datetime
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@st.cache_data(ttl=600, show_spinner=False)
def fetch_feed_articles(source_name, url, max_count):
    """Fetch and parse one RSS feed. Cached for 10 minutes so re-running
    the demo doesn't re-hit every feed from scratch. Returns (articles, error)."""
    try:
        feed = feedparser.parse(url)
        if getattr(feed, "bozo", False) and not feed.entries:
            return [], f"{source_name} feed could not be parsed."
        if not feed.entries:
            return [], f"{source_name} returned no articles right now."
        articles = []
        for entry in feed.entries[:max_count]:
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:200],
                "link": entry.get("link", ""),
                "source": source_name
            })
        return articles, None
    except Exception as e:
        return [], f"{source_name} fetch failed: {e}"


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
            <div style="background: linear-gradient(135deg, #0F172A, #3b82f6); 
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

# ---- Custom CSS for a darker, more polished look ----
# This works on TOP of .streamlit/config.toml (which sets the base dark palette).
# Together they control the overall dark theme; this block adds finishing touches
# config.toml alone can't do — card styling, spacing, custom title, buttons, badges.
st.markdown("""
<style>
    /* Tighter, more premium spacing */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Header / hero band */
    .sb-hero {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        border: 1px solid #1E293B;
        border-radius: 14px;
        padding: 32px 36px;
        margin-bottom: 8px;
    }
    .sb-hero h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #F1F5F9;
        letter-spacing: -0.02em;
    }
    .sb-hero p {
        margin: 8px 0 0 0;
        color: #94A3B8;
        font-size: 0.95rem;
    }
    .sb-hero .sb-tag {
        display: inline-block;
        margin-top: 14px;
        font-size: 0.75rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #60A5FA;
        background: rgba(59, 130, 246, 0.12);
        border: 1px solid rgba(59, 130, 246, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
    }

    /* Section subheaders get a subtle accent bar */
    h2, h3 {
        color: #E2E8F0 !important;
        font-weight: 650 !important;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.01em;
        border: 1px solid rgba(59, 130, 246, 0.4);
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #3B82F6;
        box-shadow: 0 0 0 1px #3B82F6;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 16px;
    }

    /* Expanders (article cards) */
    div[data-testid="stExpander"] {
        border: 1px solid #334155;
        border-radius: 10px;
        background: #16213A;
    }

    /* Dividers a touch subtler */
    hr {
        border-color: #334155 !important;
    }

    /* Footer */
    .sb-footer {
        text-align: center;
        color: #64748B;
        font-size: 0.8rem;
        margin-top: 24px;
        letter-spacing: 0.02em;
    }
</style>
""", unsafe_allow_html=True)

SECTOR_ICONS = {
    "Technology": "💻",
    "Healthcare": "🏥",
    "Finance": "💰",
    "Retail": "🛍️",
    "Legal": "⚖️",
    "General": "📊",
    "General Business": "📊"
}

# ---- Demo dataset: used when live fetch/AI calls are skipped ----
# Pre-written, already "analyzed" so the demo path never touches
# RSS feeds, Groq, or the internet at all — only the email send stays live.
DEMO_ARTICLES = [
    {
        "title": "Fed Signals Possible Rate Pause as Inflation Cools",
        "summary": "Federal Reserve officials hinted at a pause in rate hikes following softer inflation data.",
        "link": "https://example.com/fed-rate-pause",
        "source": "CNBC Business",
        "sentiment": "positive", "urgency": "medium",
        "key_insight": "Markets read this as a signal that the tightening cycle may be near its end.",
        "recommended_action": "Monitor bond yields for confirmation before repositioning fixed-income exposure.",
        "sector": "Finance"
    },
    {
        "title": "Major Retailer Cuts Holiday Season Hiring Forecast",
        "summary": "A large national retail chain lowered its seasonal hiring target citing softer consumer demand.",
        "link": "https://example.com/retail-hiring-cut",
        "source": "CNBC Business",
        "sentiment": "negative", "urgency": "high",
        "key_insight": "Weaker seasonal hiring often foreshadows softer holiday revenue guidance.",
        "recommended_action": "Watch for follow-on guidance cuts from peer retailers this quarter.",
        "sector": "Retail"
    },
    {
        "title": "AI Startup Raises $120M Series C for Enterprise Automation",
        "summary": "The company plans to use the funding to expand its enterprise sales team and R&D.",
        "link": "https://example.com/ai-startup-series-c",
        "source": "TechCrunch AI",
        "sentiment": "positive", "urgency": "low",
        "key_insight": "Continued late-stage AI funding suggests investor appetite hasn't cooled despite broader market caution.",
        "recommended_action": "Track competitive response from incumbents in the same enterprise automation space.",
        "sector": "Technology"
    },
    {
        "title": "New FDA Guidance Tightens Rules on AI Diagnostic Tools",
        "summary": "Regulators issued updated guidance requiring more rigorous validation for AI-based diagnostic software.",
        "link": "https://example.com/fda-ai-diagnostics",
        "source": "CNBC Business",
        "sentiment": "neutral", "urgency": "high",
        "key_insight": "Companies with AI diagnostic products in the pipeline may face longer approval timelines.",
        "recommended_action": "Review current product roadmaps against the new validation requirements immediately.",
        "sector": "Healthcare"
    },
    {
        "title": "Amazon Expands Same-Day Delivery to 15 New Metro Areas",
        "summary": "The expansion adds same-day delivery coverage ahead of the holiday shopping season.",
        "link": "https://example.com/amazon-same-day",
        "source": "Amazon News",
        "sentiment": "positive", "urgency": "low",
        "key_insight": "Expanded logistics coverage strengthens competitive pressure on regional retailers.",
        "recommended_action": "Reassess delivery-speed positioning if competing in any of the newly covered metro areas.",
        "sector": "Retail"
    },
    {
        "title": "Antitrust Case Against Tech Giant Moves to Trial",
        "summary": "A federal judge ruled that the antitrust case will proceed to trial early next year.",
        "link": "https://example.com/antitrust-trial",
        "source": "TechCrunch AI",
        "sentiment": "negative", "urgency": "high",
        "key_insight": "A trial date creates a prolonged period of regulatory uncertainty for the company and its partners.",
        "recommended_action": "Flag any dependencies on this company's platform for contingency planning.",
        "sector": "Legal"
    },
]

# ---- Hero header (replaces plain st.title / st.markdown / st.caption) ----
st.markdown("""
<div class="sb-hero">
    <h1>📊 SectorBrief — Market Intelligence Agent</h1>
    <p>Automatically analyze business news and receive personalized sector intelligence, delivered straight to your inbox.</p>
    <span class="sb-tag">Live data · CNBC · TechCrunch AI · Amazon News</span>
</div>
""", unsafe_allow_html=True)

st.write("")

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
        help="Total articles analyzed across all three sources combined — 10 means roughly 3-4 articles per source"
    )
    demo_mode = st.checkbox(
        "🎬 Use demo data (skip live fetch)",
        value=False,
        help="Uses a fixed sample of pre-analyzed articles instead of live RSS + AI calls. Useful if you're presenting and don't want to depend on live feeds or API availability."
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
    st.caption("ℹ️ Articles are pulled from general business feeds, then classified into sectors by AI — this isn't sector-specific sourcing.")

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

    if demo_mode:
        status.info("🎬 Demo mode — loading sample data (no live fetch or AI calls)...")
        progress.progress(50)
        analyzed = list(DEMO_ARTICLES)[:num_articles]
        progress.progress(100)
        status.success("✅ Demo data loaded!")

    else:
        status.info("📡 Step 1/3 — Fetching articles from news sources...")
        progress.progress(25)

        articles = []
        feed_errors = []
        feeds = [
            ("CNBC Business", "https://www.cnbc.com/id/10001147/device/rss/rss.html"),
            ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
            ("Amazon News", "https://www.aboutamazon.com/news/rss")
        ]

        for source_name, url in feeds:
            source_articles, error = fetch_feed_articles(source_name, url, num_articles // 3 + 1)
            if error:
                feed_errors.append(error)
            articles.extend(source_articles)

        if feed_errors:
            st.warning("⚠️ Some sources had issues: " + " | ".join(feed_errors))

        if len(articles) == 0:
            st.error("❌ Could not fetch any articles from any source. Check your internet connection, or enable Demo Mode above and try again.")
            st.stop()

        status.info("🤖 Step 2/3 — Groq AI analyzing articles...")
        progress.progress(60)

        try:
            groq_api_key = st.secrets["GROQ_API_KEY"]
        except KeyError:
            st.error("❌ GROQ_API_KEY is not set in Streamlit secrets. Add it in your app's Settings > Secrets, or enable Demo Mode above.")
            st.stop()

        analyzed = []
        analysis_errors = []
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

                if response.status_code != 200:
                    raise RuntimeError(f"Groq API returned status {response.status_code}")

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
            except requests.exceptions.Timeout:
                analysis_errors.append(f"Timed out analyzing: {article['title'][:50]}")
                analyzed.append({**article, "sentiment": "neutral", "urgency": "low",
                                  "key_insight": "Analysis timed out", "recommended_action": "Review manually",
                                  "sector": "General"})
            except (KeyError, json.JSONDecodeError) as e:
                analysis_errors.append(f"Unexpected AI response for: {article['title'][:50]}")
                analyzed.append({**article, "sentiment": "neutral", "urgency": "low",
                                  "key_insight": "Analysis unavailable (bad response format)", "recommended_action": "Review manually",
                                  "sector": "General"})
            except Exception as e:
                analysis_errors.append(f"{article['title'][:50]}: {e}")
                analyzed.append({**article, "sentiment": "neutral", "urgency": "low",
                                  "key_insight": "Analysis unavailable", "recommended_action": "Review manually",
                                  "sector": "General"})

        if analysis_errors:
            with st.expander(f"⚠️ {len(analysis_errors)} article(s) had analysis issues (click to see why)"):
                for err in analysis_errors:
                    st.caption(err)

        progress.progress(100)
        status.success("✅ Analysis complete!")

    st.session_state.analyzed_articles = analyzed
    st.session_state.analysis_done = True

if st.session_state.analysis_done and st.session_state.analyzed_articles:

    all_articles = st.session_state.analyzed_articles

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

        sector_groups = defaultdict(list)
        for article in filtered:
            sector_groups[article["sector"]].append(article)

        st.subheader("📰 Articles by Sector")
        st.caption("💡 Use the sector dropdown above to filter — results update instantly!")

        for sector_name, sector_articles in sector_groups.items():
            icon = SECTOR_ICONS.get(sector_name, "📊")
            st.markdown(f"## {icon} {sector_name}")
            st.caption(f"{len(sector_articles)} articles")

            if len(sector_articles) == 0:
                st.info("No articles classified in this sector for this run — try running again or check back later")

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

        except KeyError:
            st.info("📧 Email not configured. Add Gmail credentials to secrets.toml")
        except Exception as e:
            st.error(f"❌ Email error: {str(e)}")

st.divider()
st.markdown('<p class="sb-footer">SectorBrief — Market Intelligence Agent V2 · Built with Streamlit + Groq AI · Gayatri Pokale</p>', unsafe_allow_html=True)
