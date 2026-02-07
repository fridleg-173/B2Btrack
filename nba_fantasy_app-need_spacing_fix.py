import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

# --- 1. SET UP BACKGROUND IMAGE (Placeholder for your future image) ---
# When you have your image, host it (e.g., on GitHub or Imgur) and replace the URL below
bg_img_url = "" 
if bg_img_url:
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("{bg_img_url}");
            background-size: cover;
        }}
        </style>
        """, unsafe_allow_html=True)

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
    
    # Normalize headers
    schedule.columns = schedule.columns.str.strip().str.title()
    ratings.columns = ratings.columns.str.strip().str.title()
    
    # Ensure Date is datetime
    schedule['Date'] = pd.to_datetime(schedule['Date'], dayfirst=True)
    return schedule, ratings

try:
    df_schedule, df_ratings = load_data()
    
    # --- 3. SIDEBAR FILTERS ---
    st.sidebar.header("Filter Range")
    
    # Default: Today to Today + 7 days
    today = date.today()
    default_end = today + timedelta(days=7)
    
    # Yesterday's date for logic safety (time differences)
    yesterday = today - timedelta(days=1)
    max_sched_date = df_schedule['Date'].max().date()

    start_date = st.sidebar.date_input("Start Date", today, min_value=yesterday)
    end_date = st.sidebar.date_input("End Date", default_end, max_value=max_sched_date)

    show_b2b = st.sidebar.toggle("Highlight Back-to-Backs", value=True)

    # --- 4. PROCESSING LOGIC ---
    mask = (df_schedule['Date'].dt.date >= start_date) & (df_schedule['Date'].dt.date <= end_date)
    filtered_sched = df_schedule[mask]

    # Map ratings
    rating_map = df_ratings.set_index('Team')[['Tier', 'Emoji']].to_dict('index')

    all_teams = sorted(pd.concat([df_schedule['Home Team'], df_schedule['Away Team']]).unique())
    team_stats = []

    for team in all_teams:
        games = filtered_sched[(filtered_sched['Home Team'] == team) | (filtered_sched['Away Team'] == team)].sort_values('Date')
        num_games = len(games)
        
        if num_games > 0:
            score = 0
            matchup_list = []
            has_b2b = False
            
            # B2B Logic: Check if any two games are 1 day apart
            if num_games > 1:
                dates = games['Date'].dt.date.tolist()
                for i in range(len(dates) - 1):
                    if (dates[i+1] - dates[i]).days == 1:
                        has_b2b = True
                        break

            for _, row in games.iterrows():
                opponent = row['Away Team'] if row['Home Team'] == team else row['Home Team']
                opp_info = rating_map.get(opponent, {'Tier': 'Neutral', 'Emoji': '⚪'})
                
                if opp_info['Tier'] == 'Pushover': score += 1
                elif opp_info['Tier'] == 'Lockdown': score -= 1
                
                matchup_list.append(f"{opp_info['Emoji']} vs {opponent}")

            team_stats.append({
                "Team": team,
                "Games": num_games,
                "Score": score,
                "B2B": has_b2b,
                "Matchups": " | ".join(matchup_list)
            })

    # --- 5. DISPLAY RESULTS ---
    if team_stats:
        results_df = pd.DataFrame(team_stats).sort_values(by=["Games", "Score"], ascending=False)
        
        for game_count in sorted(results_df['Games'].unique(), reverse=True):
            st.subheader(f"Teams playing {game_count} games")
            subset = results_df[results_df['Games'] == game_count]
            
            for _, row in subset.iterrows():
                vibe = "🔥" if row['Score'] > 0 else "❄️" if row['Score'] < 0 else "⚪"
                b2b_label = " 🔄 (B2B)" if (row['B2B'] and show_b2b) else ""
                
                with st.expander(f"{vibe} {row['Team']} ({row['Score']}){b2b_label}"):
                    st.write(f"**Opponents:** {row['Matchups']}")
    else:
        st.warning("No games found for this range.")

except Exception as e:
    st.error(f"Error: {e}")

# (Debug section removed for clean user experience)