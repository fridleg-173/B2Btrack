import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

# --- 1. ROBUST CSS (Works on Mobile & Desktop) ---
st.markdown("""
    <style>
    /* Force the main area to be a light grey so white cards pop */
    [data-testid="stAppViewContainer"] {
        background-color: #F0F2F6 !important;
    }
    
    /* Target the container that Streamlit uses for 'border=True' */
    /* This selector is more robust for mobile browsers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white !important;
        border-radius: 15px !important;
        border: 1px solid #DDE1E7 !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }

    /* Keep text black and readable */
    h1, h2, h3, p, span, label {
        color: #1E1E1E !important;
    }

    /* Style the expanders inside the cards */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #F0F2F6 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    st.image("NBA-B2B-Track_logo.png", width='stretch')
except:
    st.title("🏀 NBA Streamer's Edge")

# --- 3. DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3600)
def load_data():
    schedule_url = "https://docs.google.com/spreadsheets/d/19WTtvYIW132Tzv94ktKNrkug_z975AfiLrbUcJq04uQ/edit?gid=1678584316#gid=1678584316"
    ratings_url = "https://docs.google.com/spreadsheets/d/19WTtvYIW132Tzv94ktKNrkug_z975AfiLrbUcJq04uQ/edit?gid=1403257463#gid=1403257463"
    schedule = conn.read(spreadsheet=schedule_url)
    ratings = conn.read(spreadsheet=ratings_url)
    schedule.columns = schedule.columns.str.strip().str.title()
    ratings.columns = ratings.columns.str.strip().str.title()
    schedule['Date'] = pd.to_datetime(schedule['Date'], dayfirst=True)
    return schedule, ratings

try:
    df_schedule, df_ratings = load_data()
    
    # --- 4. TOP-LEVEL FILTERS (BETTER FOR MOBILE) ---
    # We move these out of the sidebar so they are the first thing mobile users see
    with st.container(border=True):
        st.subheader("🗓️ Filter Games")
        col1, col2 = st.columns(2)
        
        with col1:
            b2b_toggle = st.toggle("Show Back-to-Backs Only", value=False)
        
        today_val = date.today()
        yesterday = today_val - timedelta(days=1)
        max_date = df_schedule['Date'].max().date()

        if not b2b_toggle:
            with col2:
                # Combining range into a single input to save space on mobile
                date_range = st.date_input(
                    "Select Date Range",
                    value=(today_val, today_val + timedelta(days=7)),
                    min_value=yesterday,
                    max_value=max_date
                )
                if len(date_range) == 2:
                    start_date, end_date = date_range
                else:
                    start_date = end_date = date_range[0]
        else:
            start_date, end_date = today_val, today_val + timedelta(days=1)
            st.info(f"Showing games for {start_date} and {end_date}")

    # --- 5. PROCESSING ---
    mask = (df_schedule['Date'].dt.date >= start_date) & (df_schedule['Date'].dt.date <= end_date)
    filtered = df_schedule[mask]
    rating_map = df_ratings.set_index('Team')[['Tier', 'Emoji']].to_dict('index')
    all_teams = sorted(pd.concat([df_schedule['Home Team'], df_schedule['Away Team']]).unique())
    
    team_stats = []
    for team in all_teams:
        games = filtered[(filtered['Home Team'] == team) | (filtered['Away Team'] == team)].sort_values('Date')
        if b2b_toggle and len(games) < 2: continue
        if not games.empty:
            score = 0
            matchups = []
            for _, row in games.iterrows():
                opp = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                info = rating_map.get(opp, {'Tier': 'Neutral', 'Emoji': '⚪'})
                if info['Tier'] == 'Pushover': score += 1
                elif info['Tier'] == 'Lockdown': score -= 1
                matchups.append(f"{info['Emoji']} vs {opp}")
            team_stats.append({"Team": team, "Games": len(games), "Score": score, "Matchups": " | ".join(matchups)})

    # --- 6. DISPLAY ---
    if team_stats:
        df_res = pd.DataFrame(team_stats)
        for count in sorted(df_res['Games'].unique(), reverse=True):
            with st.container(border=True):
                st.header(f"📅 Teams playing {count} games")
                subset = df_res[df_res['Games'] == count].sort_values("Score", ascending=False)
                for _, row in subset.iterrows():
                    vibe = "🔥" if row['Score'] > 0 else "❄️" if row['Score'] < 0 else "⚪"
                    with st.expander(f"{vibe} {row['Team']} (Quality Score: {row['Score']})"):
                        st.write(f"**Matchups:** {row['Matchups']}")
    else:
        st.warning("No teams found for this selection.")

    # Methodology at the very bottom for mobile accessibility
    with st.expander("ℹ️ How Quality Scores work"):
        st.write("Score is based on opponent defensive ratings from the last 15 games (+1 for Pushover, -1 for Lockdown).")

except Exception as e:
    st.error(f"Error: {e}")