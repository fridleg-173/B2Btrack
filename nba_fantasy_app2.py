import pandas as pd
import streamlit as st
from datetime import datetime

# --- Core function ---
def games_per_team_in_range(csv_path, start_date, end_date):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    if show_today_tomorrow:
        today = pd.to_datetime(date.today())
        tomorrow = today + pd.Timedelta(days=1)

        teams_today = teams_playing_on_date(df, today)
        teams_tomorrow = teams_playing_on_date(df, tomorrow)

        back_to_back_teams = sorted(teams_today & teams_tomorrow)

        st.subheader("Teams playing today & tomorrow")

    if back_to_back_teams:
        for i in range(0, len(back_to_back_teams), 3):
            st.write(", ".join(back_to_back_teams[i:i+3]))
    else:
        st.write("No teams play on both days.")

    # Convert Python date to datetime for comparison
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
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

def teams_playing_on_date(df, target_date):
    return set(
        df[df["Date"] == target_date]["Home Team"]
    ).union(
        set(df[df["Date"] == target_date]["Away Team"])
    )


# --- Streamlit UI ---
st.title("NBA Fantasy: Games Per Team")

# Use local CSV file directly
csv_file = "schedule_comma_separated.csv"

# Date range selector
from datetime import date, timedelta

show_today_tomorrow = st.checkbox(
    "Show only teams playing today & tomorrow (back-to-back)",
    value=False
)



use_today = st.checkbox("Start from today", value=False)

if not use_today:
    start_date = st.date_input("Start Date", value=date.today())
else:
    start_date = date.today()

end_date = st.date_input("End Date", value=date.today())


if st.button("Show games"):
    games_series = games_per_team_in_range(csv_file, start_date, end_date)
    grouped, batch_size = get_grouped_teams(games_series)
    formatted_text = format_grouped_teams(grouped, batch_size)
    st.markdown(formatted_text)
    
    
