import pandas as pd
import streamlit as st

# --- Core function ---
def games_per_team_in_range(csv_path, start_date, end_date):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

    home = df["Home Team"].value_counts()
    away = df["Away Team"].value_counts()
    return home.add(away, fill_value=0).astype(int).sort_values(ascending=False)

# --- Pretty print / grouping ---
def get_grouped_teams(games_series, batch_size=3):
    grouped = {}
    for team, games in games_series.items():
        grouped.setdefault(games, []).append(team)
    return grouped, batch_size

def format_grouped_teams(grouped, batch_size=3):
    output = ""
    for games_count in sorted(grouped.keys(), reverse=True):
        teams = grouped[games_count]
        output += f"**Teams playing {games_count} games:**\n"
        for i in range(0, len(teams), batch_size):
            output += ", ".join(teams[i:i+batch_size]) + "\n"
        output += "\n"
    return output

# --- Streamlit UI ---
st.title("NBA Fantasy: Games Per Team")

# File uploader (optional) or hardcoded CSV
csv_file = st.file_uploader("Upload NBA games CSV", type="csv")
if csv_file is None:
    csv_file = "nba_games.csv"  # fallback if you have a default CSV

# Date range selector
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

if st.button("Show games"):
    from datetime import datetime
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    games_series = games_per_team_in_range(csv_file, start_dt, end_dt)
    grouped, batch_size = get_grouped_teams(games_series)
    formatted_text = format_grouped_teams(grouped, batch_size)
    st.markdown(formatted_text)
