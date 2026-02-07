import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

st.title("🏀 NBA Streamer's Edge")
st.markdown("### Phase 1: Defensive Matchups & Quality Games")

# 1. Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=3600) # Refresh data every hour
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/19WTtvYIW132Tzv94ktKNrkug_z975AfiLrbUcJq04uQ/edit?usp=sharing"
    # Load Schedule and Ratings
    schedule = conn.read(spreadsheet=sheet_url, worksheet="Schedule")
    ratings = conn.read(spreadsheet=sheet_url, worksheet="team_tier")
    
    # Clean data: Ensure dates are datetime objects
    schedule['Date'] = pd.to_datetime(schedule['Date'], dayfirst=True)
    return schedule, ratings

try:
    df_schedule, df_ratings = load_data()
    
    # 2. Sidebar Filters
    st.sidebar.header("Filter Range")
    start_date = st.sidebar.date_input("Start Date", df_schedule['Date'].min())
    end_date = st.sidebar.date_input("End Date", df_schedule['Date'].min() + pd.Timedelta(days=6))

    # 3. Processing Logic
    mask = (df_schedule['Date'] >= pd.to_datetime(start_date)) & (df_schedule['Date'] <= pd.to_datetime(end_date))
    filtered_sched = df_schedule[mask]

    # Map ratings for easy lookup
    # Creating a dictionary {TeamName: (Tier, Emoji)}
    rating_map = df_ratings.set_index('Team')[['Tier', 'Emoji']].to_dict('index')

    all_teams = pd.concat([df_schedule['Home Team'], df_schedule['Away Team']]).unique()
    team_stats = []

    for team in all_teams:
        # Find games for this team
        games = filtered_sched[(filtered_sched['Home Team'] == team) | (filtered_sched['Away Team'] == team)]
        num_games = len(games)
        
        if num_games > 0:
            score = 0
            matchup_details = []
            
            for _, row in games.iterrows():
                # Who is the opponent?
                opponent = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                
                # Get opponent stats
                opp_info = rating_map.get(opponent, {'Tier': 'Unknown', 'Emoji': '❓'})
                
                # Calculate Score
                if opp_info['Tier'] == 'Pushover': score += 1
                elif opp_info['Tier'] == 'Lockdown': score -= 1
                
                matchup_details.append(f"{opp_info['Emoji']} vs {opponent}")

            team_stats.append({
                "Team": team,
                "Games": num_games,
                "Score": score,
                "Matchups": " | ".join(matchup_details)
            })

    # 4. Display Results
    results_df = pd.DataFrame(team_stats).sort_values(by=["Games", "Score"], ascending=False)

    # Group by number of games
    for game_count in sorted(results_df['Games'].unique(), reverse=True):
        st.subheader(f"Teams playing {game_count} games")
        
        subset = results_df[results_df['Games'] == game_count]
        for _, row in subset.iterrows():
            # Determine overall vibe emoji
            vibe = "🔥" if row['Score'] > 0 else "❄️" if row['Score'] < 0 else "⚪"
            
            with st.expander(f"{vibe} {row['Team']} ({row['Score']} Matchup Score)"):
                st.write(f"**Matchups this week:**")
                st.write(row['Matchups'])

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Check if your Google Sheet tab names match 'Schedule' and 'team_tier' exactly.")

# Debug Section (Collapse by default)
with st.expander("🛠️ Debug Information"):
    st.write("If you see '❓', it means a team name in the Schedule doesn't match the Ratings tab.")
    st.write("Teams found in Ratings:", list(df_ratings['Team'].unique()))