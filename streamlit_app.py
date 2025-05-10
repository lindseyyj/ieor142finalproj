import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime

st.set_page_config(page_title="NBA Points Over Time", layout="wide")
st.title("🏀 NBA 2025 Playoffs Performance Dashboard")
st.markdown("""
The NBA 2025 Playoffs Performance Dashboard features two interactive visualizations that explore player performance.

The first visualization is a line chart that plots each selected player’s points in every 2024–25 playoff game. The horizontal axis displays game dates, and the vertical axis shows points scored. Each player’s scoring trajectory is rendered in a distinct color, allowing you to compare, for example, LeBron James against a high-variance shooter. A sidebar lets you choose which players to include and narrow the date range, and hovering over any marker reveals the exact game date, player name, and point total. Directly beneath these controls, season-to-date averages, maxima, and minima for points update dynamically based on your selections.

Additionally, the sidebar also includes a Playoff GIFs selector powered by the Giphy API. A dropdown menu lists all available players, and when you choose one and click Load GIF, it displays an GIF from the current playoffs.

The second visualization is an interactive correlation heatmap showing coefficients among six core per-game metrics: assists, total rebounds, minutes played, turnovers, and plus/minus points. The heatmap shows relationships from strong negative to strong positive by recalculating for only the players and date range you’ve selected in the sidebar. Every cell is annotated with its correlation value to two decimal places, and you can hover to reveal the exact stat pair and r-value.
""")
st.subheader("🔍 Per-Game Points Over Time")

def load_data():
    df = pd.read_csv("final_df.csv")
    df["gameDate"] = pd.to_datetime(df["gameDate"])
    df["Player"] = df["firstName"] + " " + df["lastName"]
    df["Team"] = df["playerteamName"]
    df["Opponent"] = df["opponentteamName"]
    df = df.sort_values("gameDate")
    
    return df

df = load_data()

players = df["Player"].unique()
players = sorted(players)
default_players = []
default_players.append("LeBron James")

other_players = []
for player in players:
    if player != "LeBron James":
        other_players.append(player)
default_players.extend(other_players[:2])

selected = st.sidebar.multiselect("Select players", players, default=default_players)

df["gameDate_only"] = df["gameDate"].dt.date
min_date = df["gameDate_only"].min()
max_date = df["gameDate_only"].max()

date_range = st.sidebar.date_input("Date range", [min_date, max_date])

filtered_df = df.copy()

filtered_df = filtered_df[filtered_df["Player"].isin(selected)]

start_date = date_range[0]
end_date = date_range[1]
filtered_df = filtered_df[filtered_df["gameDate_only"] >= start_date]
filtered_df = filtered_df[filtered_df["gameDate_only"] <= end_date]

filtered_df = filtered_df.sort_values("gameDate")

fig = px.line(
    filtered_df,
    x="gameDate",
    y="points",
    color="Player",
    markers=True,
    title="Per-Game Points Over Time",
    labels={"gameDate": "Game Date", "points": "Points"}
)
fig.update_layout(legend_title_text="Player")
st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("### Season‐to‐Date Averages")
stats = (
    filtered_df
    .groupby("Player")["points"]
    .agg(Avg="mean", Max="max", Min="min")
    .round(1)
    .rename_axis("")
)
st.sidebar.dataframe(stats)

def fetch_gif_url(player_name):
    api_key = st.secrets["GIPHY_API_KEY"]
    search_query = player_name + " playoffs nba"
    
    params = {
        "api_key": api_key,
        "q": search_query,
        "limit": 1,
        "rating": "pg"
    }
    try:
        url = "https://api.giphy.com/v1/gifs/search"
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error: Got status code {response.status_code}")
            return None
            
        json_data = response.json()
        
        if "data" in json_data and len(json_data["data"]) > 0:
            # Get the URL of the first GIF
            first_gif = json_data["data"][0]
            gif_url = first_gif["images"]["downsized"]["url"]
            return gif_url
        else:
            print(f"No GIFs found for {player_name}")
            return None
            
    except Exception as e:
        print(f"Error fetching GIF: {e}")
        return None

st.sidebar.header("🏆 Playoff GIFs")
gif_player = st.sidebar.selectbox("Choose a player for GIF", options=players, index=players.index("LeBron James"))
if st.sidebar.button("Load GIF"):
    gif_url = fetch_gif_url(gif_player)
    if gif_url:
        gif_bytes = requests.get(gif_url).content
        st.sidebar.image(gif_bytes, caption=gif_player, width=300)
        st.image(
            gif_bytes,
            caption=gif_player,
            use_container_width=True
        )
    else:
        st.sidebar.write("No GIF found.")
        
if st.sidebar.checkbox("Display Raw Filtered Data"):
    st.subheader("Raw Filtered Data")
    st.dataframe(filtered_df[["gameDate", "Player", "points", "Team", "Opponent"]])

st.subheader("🔍 Correlation Matrix of Key Player Stats")

features = [
    "points",
    "assists",
    "reboundsTotal",
    "numMinutes",
    "turnovers",
    "plusMinusPoints",
]

corr = filtered_df[features].corr()

fig_corr = px.imshow(
    corr,
    x=features,
    y=features,
    text_auto=".2f", 
    zmin=-1,
    zmax=1,
    labels={"color": "Correlation (r)"},
    title="Correlation Matrix of Key Player Stats"
)
fig_corr.update_layout(
    width=600,
    height=600,
    margin=dict(l=40, r=40, t=50, b=40)
)

st.plotly_chart(fig_corr, use_container_width=True)
