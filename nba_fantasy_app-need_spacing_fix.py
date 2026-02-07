import streamlit as st
import pandas as pd
import base64
from streamlit_gsheets import GSheetsConnection
from datetime import date, timedelta

# Page Config
st.set_page_config(page_title="NBA Streamer's Edge", layout="centered")

# --- 1. CSS FOR READABILITY ---
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    bin_str = get_base64('background_image.png')
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        /* This tints the whole background white so text is easy to read */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(255, 255, 255, 0.85);
            z-index: -1;
        }}
        /* Header and Text Colors */
        h1, h2, h3, p, span {{
            color: #1E1E1E !important;
        }}
        /* Card-style expanders */
        .streamlit-expanderHeader {{
            background-color: white !important;
            border: 1px solid #ddd !important;
            border-radius: 10px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        }}
        </style>
        """, unsafe_allow_html=True)
except:
    st.sidebar.warning("Background image file not found.")

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
    
    # --- 4. SIDEBAR ---
    st.sidebar.header("Filter Settings")
    b2b_toggle = st.sidebar.toggle("Show Today & Tomorrow (back-to-back)", value=False)
    
    today_val = date.today()
    yesterday = today_val - timedelta(days=1)
    max_sched_date = df_schedule['Date'].max().date()
    
    if b2b_toggle:
        start_date = today_val
        end_date = today_val + timedelta(days=1)
        st.sidebar.info(f"📅 Showing back-to-back games for: {start_date} to {end_date}")
    else:
        start_date = st.sidebar.date_input("Start Date", today_val, min_value=yesterday, max_value=max_sched_date)
        end_date = st.sidebar.date_input("End Date", today_val + timedelta(days=7), min_value=yesterday, max_value=max_sched_date)

    st.sidebar.markdown("---")
    with st.sidebar.expander("ℹ️ How Quality Scores work"):
        st.write("""
            **Based on Last 15 Games:**
            * 🔥 **Pushover (+1):** Bottom 5 Defense.
            * ⚪ **Neutral (0):** League Average.
            * ❄️ **Lockdown (-1):** Top 5 Defense.
        """)

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
            team_stats.append({"Team": team, "Games": len(games), "Quality Score": score, "Matchups": " | ".join(matchups)})

    # --- 6. DISPLAY ---
    if team_stats:
        df_res = pd.DataFrame(team_stats)
        game_counts = sorted(df_res['Games'].unique(), reverse=True)
        
        for count in game_counts:
            st.header(f"📅 Teams playing {count} games")
            st.divider()
            
            subset = df_res[df_res['Games'] == count].sort_values("Quality Score", ascending=False)
            for _, row in subset.iterrows():
                vibe = "🔥" if row['Quality Score'] > 0 else "❄️" if row['Quality Score'] < 0 else "⚪"
                label = f"{vibe} {row['Team']} (Quality Score: {row['Quality Score']})"
                with st.expander(label):
                    st.write(f"**Matchups:** {row['Matchups']}")
            st.markdown("<br>", unsafe_allow_html=True) # Spacer
    else:
        st.warning("No teams found for this selection.")

except Exception as e:
    st.error(f"Error: {e}")