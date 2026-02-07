import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

# --- 1. BACKGROUND IMAGE & STYLING ---
# This applies your background image and adds a slight overlay to keep text readable
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("background_image.png");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Adds a semi-transparent dark layer so text remains easy to read */
    [data-testid="stVerticalBlock"] {{
        background-color: rgba(255, 255, 255, 0.05); 
        padding: 10px;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ---
try:
    st.image("NBA-B2B-Track_logo.png", use_container_width=True)
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
    
    # --- 4. SIDEBAR FILTERS & INFO ---
    st.sidebar.header("Filter Settings")
    b2b_shortcut = st.sidebar.toggle("Show Today & Tomorrow (back-to-back)", value=False)
    
    today_val = date.today()
    yesterday = today_val - timedelta(days=1)
    max_sched_date = df_schedule['Date'].max().date()
    
    if b2b_shortcut:
        start_date = today_val
        end_date = today_val + timedelta(days=1)
        st.sidebar.info(f"📅 Showing B2B games for: {start_date} to {end_date}")
    else:
        start_date = st.sidebar.date_input("Start Date", today_val, min_value=yesterday, max_value=max_sched_date)
        end_date = st.sidebar.date_input("End Date", today_val + timedelta(days=7), min_value=yesterday, max_value=max_sched_date)

    st.sidebar.markdown("---")
    # THE METHODOLOGY MOVED TO SIDEBAR
    with st.sidebar.expander("❓ How Quality Scores work"):
        st.write("""
            **Based on Last 15 Games:**
            * 🔥 **Pushover (+1):** Bottom 5 Defense.
            * ⚪ **Neutral (0):** League Average.
            * ❄️ **Lockdown (-1):** Top 5 Defense.
            
            **Quality Score** is the sum of these values for all games in your selected range.
        """)

    # --- 5. PROCESSING LOGIC ---
    mask = (df_schedule['Date'].dt.date >= start_date) & (df_schedule['Date'].dt.date <= end_date)
    filtered_sched = df_schedule[mask]

    rating_map = df_ratings.set_index('Team')[['Tier', 'Emoji']].to_dict('index')
    all_teams = sorted(pd.concat([df_schedule['Home Team'], df_schedule['Away Team']]).unique())
    team_stats = []

    for team in all_teams:
        games = filtered_sched[(filtered_sched['Home Team'] == team) | (filtered_sched['Away Team'] == team)].sort_values('Date')
        
        if b2b_shortcut and len(games) < 2:
            continue
            
        num_games = len(games)
        if num_games > 0:
            quality_score = 0
            matchup_list = []
            for _, row in games.iterrows():
                opponent = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                opp_info = rating_map.get(opponent, {'Tier': 'Neutral', 'Emoji': '⚪'})
                if opp_info['Tier'] == 'Pushover': quality_score += 1
                elif opp_info['Tier'] == 'Lockdown': quality_score -= 1
                matchup_list.append(f"{opp_info['Emoji']} vs {opponent}")

            team_stats.append({
                "Team": team, 
                "Games": num_games, 
                "Quality Score": quality_score, 
                "Matchups": " | ".join(matchup_list)
            })

    # --- 6. DISPLAY RESULTS ---
    if team_stats:
        results_df = pd.DataFrame(team_stats)
        game_counts = sorted(results_df['Games'].unique(), reverse=True)
        
        for count in game_counts:
            st.markdown(f"## 📅 Teams playing {count} games")
            subset = results_df[results_df['Games'] == count].sort_values(by="Quality Score", ascending=False)
            
            for _, row in subset.iterrows():
                vibe = "🔥" if row['Quality Score'] > 0 else "❄️" if row['Quality Score'] < 0 else "⚪"
                label = f"{vibe} {row['Team']} (Quality Score: {row['Quality Score']})"
                with st.expander(label):
                    st.write(f"**Matchups:** {row['Matchups']}")
    else:
        st.warning("No teams found for this selection.")

except Exception as e:
    st.error(f"Error: {e}")