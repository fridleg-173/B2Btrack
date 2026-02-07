import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

# --- 1. LOGO REPLACEMENT ---
# This replaces the text title with your image file
try:
    st.image("NBA-B2B-Track_logo.png", use_container_width=True)
except:
    # Fallback to text if the image isn't found/pushed yet
    st.title("🏀 NBA Streamer's Edge")

st.markdown("### Defensive Matchups & Quality Games")

# --- 2. DATA LOADING ---
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
    
    # --- 3. SIDEBAR FILTERS ---
    st.sidebar.header("Filter Settings")
    
    b2b_shortcut = st.sidebar.toggle("Show Today & Tomorrow B2Bs", value=False)
    
    # Date Bounds
    today_val = date.today()
    yesterday = today_val - timedelta(days=1)
    max_sched_date = df_schedule['Date'].max().date()
    
    if b2b_shortcut:
        start_date = today_val
        end_date = today_val + timedelta(days=1)
        st.sidebar.info(f"📅 Showing B2Bs for: {start_date} to {end_date}")
    else:
        # CONSTRAINTS APPLIED HERE:
        # Start date: min is yesterday, max is the end of the schedule
        start_date = st.sidebar.date_input(
            "Start Date", 
            today_val, 
            min_value=yesterday, 
            max_value=max_sched_date
        )
        
        # End date: min is yesterday (or start_date), max is end of schedule
        end_date = st.sidebar.date_input(
            "End Date", 
            today_val + timedelta(days=7), 
            min_value=yesterday, 
            max_value=max_sched_date
        )

    # --- 4. PROCESSING LOGIC ---
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
            score = 0
            matchup_list = []
            for _, row in games.iterrows():
                opponent = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                opp_info = rating_map.get(opponent, {'Tier': 'Neutral', 'Emoji': '⚪'})
                if opp_info['Tier'] == 'Pushover': score += 1
                elif opp_info['Tier'] == 'Lockdown': score -= 1
                matchup_list.append(f"{opp_info['Emoji']} vs {opponent}")

            team_stats.append({"Team": team, "Games": num_games, "Score": score, "Matchups": " | ".join(matchup_list)})

    # --- 5. DISPLAY RESULTS ---
    if team_stats:
        results_df = pd.DataFrame(team_stats).sort_values(by=["Score", "Team"], ascending=[False, True])
        for _, row in results_df.iterrows():
            vibe = "🔥" if row['Score'] > 0 else "❄️" if row['Score'] < 0 else "⚪"
            with st.expander(f"{vibe} {row['Team']} ({row['Score']})"):
                st.write(f"**Opponents:** {row['Matchups']}")
    else:
        st.warning("No teams found for this selection.")

except Exception as e:
    st.error(f"Error: {e}")