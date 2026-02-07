import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

st.title("🏀 NBA Streamer's Edge")
st.markdown("### Phase 1: Defensive Matchups & Quality Games")

# 1. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3600)
def load_data():
    schedule_url = "https://docs.google.com/spreadsheets/d/19WTtvYIW132Tzv94ktKNrkug_z975AfiLrbUcJq04uQ/edit?gid=1678584316#gid=1678584316"
    ratings_url = "https://docs.google.com/spreadsheets/d/19WTtvYIW132Tzv94ktKNrkug_z975AfiLrbUcJq04uQ/edit?gid=1403257463#gid=1403257463"
    
    # Load raw data
    schedule = conn.read(spreadsheet=schedule_url)
    ratings = conn.read(spreadsheet=ratings_url)
    
    # 1. CLEAN HEADERS: Make everything Title Case and remove extra spaces
    # This ensures "TEAM" or "teams" both become "Team"
    schedule.columns = schedule.columns.str.strip().str.title()
    ratings.columns = ratings.columns.str.strip().str.title()

    # 2. DATE CLEANING: Ensure the Schedule date is usable
    # NBA.com/other sources use different formats, so we handle those here
    schedule['Date'] = pd.to_datetime(schedule['Date'], dayfirst=True)
    
    return schedule, ratings

# Initialise variables to None to prevent NameErrors
df_schedule, df_ratings = None, None

try:
    df_schedule, df_ratings = load_data()
    
    # 2. Sidebar Filters
    st.sidebar.header("Filter Range")
    start_date = st.sidebar.date_input("Start Date", df_schedule['Date'].min())
    end_date = st.sidebar.date_input("End Date", df_schedule['Date'].max()) # Changed to max to see the full list

    # 3. Processing Logic
    mask = (df_schedule['Date'] >= pd.to_datetime(start_date)) & (df_schedule['Date'] <= pd.to_datetime(end_date))
    filtered_sched = df_schedule[mask]

    # Map ratings, make sure name headers match
    rating_map = df_ratings.set_index('Team')[['Tier', 'Emoji']].to_dict('index')

    all_teams = pd.concat([df_schedule['Home Team'], df_schedule['Away Team']]).unique()
    team_stats = []

    for team in all_teams:
        games = filtered_sched[(filtered_sched['Home Team'] == team) | (filtered_sched['Away Team'] == team)]
        num_games = len(games)
        
        if num_games > 0:
            score = 0
            matchup_details = []
            for _, row in games.iterrows():
                opponent = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                opp_info = rating_map.get(opponent, {'Tier': 'Unknown', 'Emoji': '❓'})
                
                if opp_info['Tier'] == 'Pushover': score += 1
                elif opp_info['Tier'] == 'Lockdown': score -= 1
                matchup_details.append(f"{opp_info['Emoji']} vs {opponent}")

            team_stats.append({"Team": team, "Games": num_games, "Score": score, "Matchups": " | ".join(matchup_details)})

    # 4. Display Results
    if team_stats:
        results_df = pd.DataFrame(team_stats).sort_values(by=["Games", "Score"], ascending=False)
        for game_count in sorted(results_df['Games'].unique(), reverse=True):
            st.subheader(f"Teams playing {game_count} games")
            subset = results_df[results_df['Games'] == game_count]
            for _, row in subset.iterrows():
                vibe = "🔥" if row['Score'] > 0 else "❄️" if row['Score'] < 0 else "⚪"
                with st.expander(f"{vibe} {row['Team']} ({row['Score']} Matchup Score)"):
                    st.write(f"**Matchups this week:**")
                    st.write(row['Matchups'])
    else:
        st.warning("No games found for this date range.")

    # Move Debug inside the try block so it only runs if df_ratings exists
    with st.expander("🛠️ Debug Information"):
        st.write("Teams found in Ratings:", list(df_ratings['Team'].unique()))

except Exception as e:
    st.error("⚠️ Data Loading Error")
    st.write(f"Specific Error: {e}")
    st.info("Tip: Double-check your Google Sheet tab names are exactly 'Schedule' and 'team_tier' (case sensitive).")