import pandas as pd
import streamlit as st
from datetime import date, timedelta
from PIL import Image



# =========================
# Data helpers (NO Streamlit here)
# =========================

def load_schedule(csv_path):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    return df


def games_per_team_in_range(df, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    home = df["Home Team"].value_counts()
    away = df["Away Team"].value_counts()

    return home.add(away, fill_value=0).astype(int).sort_values(ascending=False)


def teams_playing_on_date(df, target_date):
    return set(
        df[df["Date"] == target_date]["Home Team"]
    ).union(
        set(df[df["Date"] == target_date]["Away Team"])
    )


def get_back_to_back_teams(df, base_date):
    today = pd.to_datetime(base_date)
    tomorrow = today + pd.Timedelta(days=1)

    teams_today = teams_playing_on_date(df, today)
    teams_tomorrow = teams_playing_on_date(df, tomorrow)

    return sorted(teams_today & teams_tomorrow)


def group_teams_by_games(games_series):
    grouped = {}
    for team, games in games_series.items():
        grouped.setdefault(games, []).append(team)
    return grouped


# =========================
# Streamlit UI
# =========================
import base64
import pandas as pd
import streamlit as st
from datetime import date

# 1. Helper to encode image
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# 2. Inject CSS for Background and Glass Effect
def apply_custom_styles(bin_file):
    bin_str = get_base64_of_bin_file(bin_file)
    css = f'''
    <style>
    /* 1. The Background with a Dark Overlay */
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), 
                    url("data:image/jpg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* 2. Darker, More Solid Glass Container */
    .glass-box {{
        background: rgba(15, 15, 25, 0.85); /* Deep dark blue/black, mostly solid */
        border: 2px solid #5d3fd3;         /* Neon Purple border to match your vibe */
        border-radius: 15px;
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }}

    /* 3. Force White Text Everywhere in the box */
    .glass-box p, .glass-box h1, .glass-box h2, .glass-box h3, .glass-box div {{
        color: #FFFFFF !important;
    }}

    /* 4. Make Streamlit Widgets (Inputs/Checkboxes) readable */
    .stCheckbox label, .stDateInput label {{
        color: white !important;
        font-weight: bold;
    }}
    </style>
    '''
    st.markdown(css, unsafe_allow_html=True)
# Apply styles
apply_custom_styles('background_court.jpg')

# 3. Use the "Glass" Container for your UI
# Wrap your main title in a div with the glass-container class
st.markdown('<div class="glass-container">', unsafe_allow_html=True)

st.markdown("## 🏀 NBA Game Tracker", unsafe_allow_html=True)
st.write("Select your date range to see which teams are busiest.")

# ... (Place your interactive widgets like date_input or checkboxes here) ...

st.markdown('</div>', unsafe_allow_html=True) # End of top glass box




CSV_FILE = "schedule_comma_separated.csv"
df = load_schedule(CSV_FILE)

# ---- Back-to-back toggle ----
show_back_to_back = st.checkbox(
    "Show teams playing today & tomorrow (back-to-back)",
    value=False
)

st.divider()

# =========================
# BACK-TO-BACK MODE (IMMEDIATE)
# =========================
if show_back_to_back:
    st.subheader("Teams playing today & tomorrow")

    back_to_back_teams = get_back_to_back_teams(df, date.today())

    if back_to_back_teams:
        for i in range(0, len(back_to_back_teams), 3):
            st.write(", ".join(back_to_back_teams[i:i+3]))
    else:
        st.write("No teams play on both days.")

# =========================
# DATE RANGE MODE (BUTTON)
# =========================
else:
    use_today = st.checkbox("Start from today", value=False)

    if use_today:
        start_date = date.today()
    else:
        start_date = st.date_input("Start Date", value=date.today())

    end_date = st.date_input("End Date", value=date.today())

    if st.button("Show games"):
        games_series = games_per_team_in_range(df, start_date, end_date)
        grouped = group_teams_by_games(games_series)

        for games_count in sorted(grouped.keys(), reverse=True):
            st.markdown(f"### Teams playing {games_count} games")
            teams = grouped[games_count]

            for i in range(0, len(teams), 3):
                st.write(", ".join(teams[i:i+3]))

        #st.divider()
        #st.bar_chart(games_series)
