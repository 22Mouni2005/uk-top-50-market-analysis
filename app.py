"""
Atlantic Recording Corporation
UK Top 50 Playlist — Market Structure, Artist Diversity & Content Localization Analysis
Streamlit dashboard.

Run with:  streamlit run app.py
The dataset (Atlantic_United_Kingdom.csv) ships alongside this file and loads
automatically — no upload step is required. A sidebar uploader is provided
only as an optional override.
"""

import os
from datetime import datetime
from itertools import combinations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

# --------------------------------------------------------------------------------------
# PAGE CONFIG & STYLE
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="UK Top 50 | Market Structure Analysis",
    page_icon="🇬🇧",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1DB954"     # spotify-esque green
ACCENT = "#5B2C6F"      # UK-royal purple accent
DARK = "#121212"

CUSTOM_CSS = f"""
<style>
    .main {{ background-color: #0e0e10; }}
    .stMetric {{
        background: linear-gradient(135deg, rgba(29,185,84,0.10), rgba(91,44,111,0.10));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 10px 6px 10px;
    }}
    h1, h2, h3 {{ font-family: 'Helvetica Neue', sans-serif; }}
    .badge {{
        display:inline-block; padding:3px 10px; border-radius:999px;
        background:{PRIMARY}; color:#0e0e10; font-size:0.75rem; font-weight:700;
        margin-right:6px;
    }}
    .subtle {{ color:#9a9a9a; font-size:0.85rem; }}
    div[data-testid="stTabs"] button p {{ font-size: 0.95rem; }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA_PATH = os.path.join(APP_DIR, "Atlantic_United_Kingdom.csv")


# --------------------------------------------------------------------------------------
# DATA LOADING & PREPROCESSING
# --------------------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading and standardizing UK Top 50 data...")
def load_data(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df.columns = [c.strip().lower() for c in df.columns]

    # --- Validation & standardization ---
    df["artist"] = df["artist"].astype(str).str.strip()
    df["song"] = df["song"].astype(str).str.strip()
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["date", "artist", "song"]).copy()

    df["is_explicit"] = df["is_explicit"].astype(str).str.upper().map(
        {"TRUE": True, "FALSE": False}
    ).fillna(df["is_explicit"])
    df["album_type"] = df["album_type"].astype(str).str.strip().str.lower()

    # --- Split multi-artist collaborations on "&" ---
    df["artist_list"] = df["artist"].apply(
        lambda a: [x.strip() for x in a.split("&") if x.strip()]
    )
    df["primary_artist"] = df["artist_list"].apply(lambda lst: lst[0] if lst else "Unknown")
    df["num_collaborators"] = df["artist_list"].apply(len)
    df["is_collab"] = df["num_collaborators"] > 1

    # --- Rank groups ---
    def rank_group(pos):
        if pos <= 10:
            return "Top 10"
        elif pos <= 25:
            return "11-25"
        else:
            return "26-50"
    df["rank_group"] = df["position"].apply(rank_group)
    df["top10_flag"] = df["position"] <= 10

    # --- Duration ---
    df["duration_min"] = df["duration_ms"] / 60000.0

    def duration_bucket(m):
        if m < 2.5:
            return "Short (<2.5 min)"
        elif m <= 3.5:
            return "Medium (2.5-3.5 min)"
        else:
            return "Long (>3.5 min)"
    df["duration_bucket"] = df["duration_min"].apply(duration_bucket)

    # --- Popularity bucket ---
    try:
        df["popularity_bucket"] = pd.qcut(
            df["popularity"], q=3, labels=["Low", "Medium", "High"]
        )
    except ValueError:
        df["popularity_bucket"] = pd.cut(
            df["popularity"], bins=3, labels=["Low", "Medium", "High"]
        )

    df["week"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    df["month"] = df["date"].dt.to_period("M").astype(str)

    return df


def exploded_artists(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (entry, individual artist) — used for dominance/diversity metrics."""
    ex = df.explode("artist_list").rename(columns={"artist_list": "artist_single"})
    ex["artist_single"] = ex["artist_single"].astype(str).str.strip()
    return ex


# --------------------------------------------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------------------------------------------
def compute_kpis(df: pd.DataFrame, ex: pd.DataFrame) -> dict:
    total_entries = len(df)
    if total_entries == 0:
        return {k: 0 for k in [
            "artist_concentration_index", "unique_artist_count", "collaboration_ratio",
            "explicit_share", "single_album_ratio", "content_variety_index"
        ]}

    # Artist Concentration Index: share of entries held by top-5 artists (by appearance)
    artist_counts = ex["artist_single"].value_counts()
    top5_share = artist_counts.head(5).sum() / len(ex) if len(ex) else 0

    unique_artist_count = ex["artist_single"].nunique()

    collaboration_ratio = df["is_collab"].mean()

    explicit_share = df["is_explicit"].astype(bool).mean()

    n_single = (df["album_type"] == "single").sum()
    n_album = (df["album_type"] == "album").sum()
    single_album_ratio = (n_single / n_album) if n_album else np.nan

    content_variety_index = unique_artist_count / total_entries

    return {
        "artist_concentration_index": top5_share,
        "unique_artist_count": unique_artist_count,
        "collaboration_ratio": collaboration_ratio,
        "explicit_share": explicit_share,
        "single_album_ratio": single_album_ratio,
        "content_variety_index": content_variety_index,
    }


# --------------------------------------------------------------------------------------
# SIDEBAR — DATA SOURCE + FILTERS
# --------------------------------------------------------------------------------------
st.sidebar.markdown("## 🎧 Atlantic Recording Corp.")
st.sidebar.caption("UK Top 50 — Market Structure & Content Localization")

with st.sidebar.expander("📂 Data source", expanded=False):
    st.caption(
        "The bundled dataset loads automatically. Upload a replacement CSV "
        "only if you want to analyze a different snapshot (same schema)."
    )
    uploaded = st.file_uploader("Override dataset (optional)", type=["csv"])

if uploaded is not None:
    raw_df = load_data(uploaded)
    st.sidebar.success("Using uploaded file.")
elif os.path.exists(DEFAULT_DATA_PATH):
    raw_df = load_data(DEFAULT_DATA_PATH)
else:
    st.error("No dataset found. Please upload a CSV with the expected schema.")
    st.stop()

st.sidebar.markdown("### 🔎 Filters")

min_date, max_date = raw_df["date"].min().date(), raw_df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

all_artists = sorted(exploded_artists(raw_df)["artist_single"].unique().tolist())
artist_filter = st.sidebar.multiselect("Artist filter", options=all_artists, default=[])

collab_toggle = st.sidebar.radio(
    "Solo vs. Collaboration", options=["All", "Solo only", "Collaborations only"], index=0
)

album_types = sorted(raw_df["album_type"].unique().tolist())
album_filter = st.sidebar.multiselect("Album type", options=album_types, default=album_types)

explicit_toggle = st.sidebar.radio(
    "Content type", options=["All", "Explicit only", "Clean only"], index=0
)

# --------------------------------------------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------------------------------------------
df = raw_df[
    (raw_df["date"].dt.date >= start_date) & (raw_df["date"].dt.date <= end_date)
].copy()

if artist_filter:
    df = df[df["artist_list"].apply(lambda lst: any(a in artist_filter for a in lst))]

if collab_toggle == "Solo only":
    df = df[~df["is_collab"]]
elif collab_toggle == "Collaborations only":
    df = df[df["is_collab"]]

if album_filter:
    df = df[df["album_type"].isin(album_filter)]

if explicit_toggle == "Explicit only":
    df = df[df["is_explicit"].astype(bool)]
elif explicit_toggle == "Clean only":
    df = df[~df["is_explicit"].astype(bool)]

if df.empty:
    st.warning("No data matches the current filters. Adjust filters in the sidebar.")
    st.stop()

ex = exploded_artists(df)
kpis = compute_kpis(df, ex)

# --------------------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------------------
st.markdown(
    f"""
    <span class="badge">ATLANTIC RECORDING CORP.</span>
    <span class="subtle">UK Top 50 Daily Playlist Snapshots</span>
    """,
    unsafe_allow_html=True,
)
st.title("🇬🇧 UK Top 50 — Market Structure & Content Localization")
st.caption(
    f"Analyzing **{len(df):,}** chart entries across "
    f"**{df['date'].nunique():,}** daily snapshots "
    f"({start_date} → {end_date})"
)

# --------------------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Artist Concentration Index", f"{kpis['artist_concentration_index']*100:.1f}%",
          help="Share of chart entries held by the top 5 artists")
k2.metric("Unique Artist Count", f"{kpis['unique_artist_count']:,}",
          help="Distinct individual artists across all entries")
k3.metric("Collaboration Ratio", f"{kpis['collaboration_ratio']*100:.1f}%",
          help="Share of songs with 2+ credited artists")
k4.metric("Explicit Content Share", f"{kpis['explicit_share']*100:.1f}%",
          help="Share of entries flagged explicit")
sar = kpis["single_album_ratio"]
k5.metric("Single : Album Ratio", f"{sar:.2f}" if not np.isnan(sar) else "N/A",
          help="Ratio of single-format to album-format entries")
k6.metric("Content Variety Index", f"{kpis['content_variety_index']:.3f}",
          help="Unique artists ÷ total chart entries — higher = more diverse")

st.divider()

# --------------------------------------------------------------------------------------
# TABS
# --------------------------------------------------------------------------------------
tab_overview, tab_dominance, tab_collab, tab_explicit, tab_album, tab_duration, tab_market = st.tabs(
    ["📊 Overview", "👑 Artist Dominance", "🤝 Collaboration",
     "🔞 Explicit Content", "💿 Album Structure", "⏱️ Duration", "🌍 Market Structure"]
)

# ---- OVERVIEW ----
with tab_overview:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Domestic (UK) vs International Artist Presence")
        st.caption(
            "Heuristic split — since nationality isn't in the source data, this uses "
            "known UK/Irish artists observed in the dataset as a proxy. Treat as directional."
        )
        UK_HINTS = {
            "Dua Lipa", "Ed Sheeran", "Harry Styles", "Adele", "Sam Smith", "Calvin Harris",
            "Ellie Goulding", "Stormzy", "Central Cee", "Rita Ora", "One Direction",
            "Coldplay", "David Kushner", "Jorja Smith", "Raye", "PinkPantheress",
            "David Guetta", "Chase & Status", "Charli XCX",
        }
        ex["origin"] = ex["artist_single"].apply(lambda a: "UK / Domestic (proxy)" if a in UK_HINTS else "International / Unclassified")
        origin_counts = ex["origin"].value_counts().reset_index()
        origin_counts.columns = ["Origin", "Entries"]
        fig = px.pie(origin_counts, names="Origin", values="Entries", hole=0.5,
                      color_discrete_sequence=[PRIMARY, ACCENT])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Daily Entries")
        daily = df.groupby(df["date"].dt.date).size().reset_index(name="entries")
        st.line_chart(daily.set_index("date"))

    st.subheader("Chart Composition Snapshot")
    comp_c1, comp_c2, comp_c3 = st.columns(3)
    with comp_c1:
        st.metric("Total Songs Tracked", f"{df['song'].nunique():,}")
    with comp_c2:
        st.metric("Total Distinct Credits", f"{df['artist'].nunique():,}")
    with comp_c3:
        st.metric("Avg. Popularity Score", f"{df['popularity'].mean():.1f}")

# ---- ARTIST DOMINANCE ----
with tab_dominance:
    st.subheader("Artist Dominance Leaderboard")
    top_n = st.slider("Show top N artists", 5, 40, 15, key="dom_n")
    leaderboard = (
        ex.groupby("artist_single").size().reset_index(name="appearances")
        .sort_values("appearances", ascending=False).head(top_n)
    )
    fig = px.bar(leaderboard, x="appearances", y="artist_single", orientation="h",
                 color="appearances", color_continuous_scale=["#2d2d2d", PRIMARY])
    fig.update_layout(yaxis=dict(autorange="reversed"), coloraxis_showscale=False,
                       margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Unique Artists per Day")
        daily_diversity = ex.groupby(ex["date"].dt.date)["artist_single"].nunique().reset_index(name="unique_artists")
        st.area_chart(daily_diversity.set_index("date"))
    with c2:
        st.subheader("Artist Concentration Over Time (Top 5 share, weekly)")
        def weekly_top5_share(g):
            counts = g["artist_single"].value_counts()
            return counts.head(5).sum() / len(g) if len(g) else 0
        weekly_conc = ex.groupby("week").apply(weekly_top5_share).reset_index(name="top5_share")
        fig2 = px.line(weekly_conc, x="week", y="top5_share", markers=True,
                        color_discrete_sequence=[ACCENT])
        fig2.update_layout(yaxis_tickformat=".0%", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top-Dominating Artists — Rank Group Breakdown")
    top10_artists = leaderboard["artist_single"].head(10).tolist()
    rg = ex[ex["artist_single"].isin(top10_artists)].groupby(["artist_single", "rank_group"]).size().reset_index(name="count")
    fig3 = px.bar(rg, x="artist_single", y="count", color="rank_group", barmode="stack",
                  category_orders={"rank_group": ["Top 10", "11-25", "26-50"]},
                  color_discrete_sequence=[PRIMARY, "#f1c40f", ACCENT])
    fig3.update_layout(xaxis_tickangle=-35, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)

# ---- COLLABORATION ----
with tab_collab:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Solo vs. Collaborative Tracks")
        solo_counts = df["is_collab"].map({True: "Collaboration", False: "Solo"}).value_counts().reset_index()
        solo_counts.columns = ["Type", "Entries"]
        fig = px.pie(solo_counts, names="Type", values="Entries", hole=0.5,
                      color_discrete_sequence=[ACCENT, PRIMARY])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Average Collaborators per Song")
        st.metric("Avg. artists credited per entry", f"{df['num_collaborators'].mean():.2f}")
        dist = df["num_collaborators"].value_counts().sort_index().reset_index()
        dist.columns = ["num_collaborators", "count"]
        fig2 = px.bar(dist, x="num_collaborators", y="count", color_discrete_sequence=[PRIMARY])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Collaboration Frequency by Rank Group")
    collab_rank = df.groupby("rank_group")["is_collab"].mean().reindex(["Top 10", "11-25", "26-50"]).reset_index()
    collab_rank.columns = ["rank_group", "collab_share"]
    fig3 = px.bar(collab_rank, x="rank_group", y="collab_share", color="rank_group",
                  color_discrete_sequence=[PRIMARY, "#f1c40f", ACCENT])
    fig3.update_layout(yaxis_tickformat=".0%", showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Artist Collaboration Network")
    st.caption("Nodes = artists · edges = co-appearance on a track. Showing the densest cluster for readability.")
    if HAS_NX:
        collab_songs = df[df["is_collab"]]
        edge_counts = {}
        for lst in collab_songs["artist_list"]:
            for a, b in combinations(sorted(set(lst)), 2):
                edge_counts[(a, b)] = edge_counts.get((a, b), 0) + 1

        if edge_counts:
            G = nx.Graph()
            for (a, b), w in edge_counts.items():
                G.add_edge(a, b, weight=w)

            max_nodes = st.slider("Max artists shown in network", 10, 80, 35, key="net_n")
            degree = dict(G.degree())
            keep_nodes = sorted(degree, key=degree.get, reverse=True)[:max_nodes]
            H = G.subgraph(keep_nodes)

            pos = nx.spring_layout(H, seed=42, k=0.6)
            edge_x, edge_y = [], []
            for u, v in H.edges():
                x0, y0 = pos[u]; x1, y1 = pos[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color="#555"),
                                     hoverinfo="none", mode="lines")

            node_x = [pos[n][0] for n in H.nodes()]
            node_y = [pos[n][1] for n in H.nodes()]
            node_size = [8 + degree[n] * 3 for n in H.nodes()]
            node_trace = go.Scatter(
                x=node_x, y=node_y, mode="markers+text", text=list(H.nodes()),
                textposition="top center", textfont=dict(size=9, color="#ddd"),
                hovertext=[f"{n} · {degree[n]} collaborators" for n in H.nodes()],
                hoverinfo="text",
                marker=dict(size=node_size, color=PRIMARY, line=dict(width=1, color=ACCENT)),
            )
            fig4 = go.Figure(data=[edge_trace, node_trace])
            fig4.update_layout(
                showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=600,
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No collaborations found in the current filtered selection.")
    else:
        st.info("Install `networkx` to enable the collaboration network graph (see requirements.txt).")

# ---- EXPLICIT CONTENT ----
with tab_explicit:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Explicit vs. Clean Share")
        exp_counts = df["is_explicit"].astype(bool).map({True: "Explicit", False: "Clean"}).value_counts().reset_index()
        exp_counts.columns = ["Type", "Entries"]
        fig = px.pie(exp_counts, names="Type", values="Entries", hole=0.5,
                      color_discrete_sequence=["#e74c3c", PRIMARY])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Explicit Share by Rank Group")
        exp_rank = df.groupby("rank_group")["is_explicit"].apply(lambda s: s.astype(bool).mean()).reindex(["Top 10", "11-25", "26-50"]).reset_index()
        exp_rank.columns = ["rank_group", "explicit_share"]
        fig2 = px.bar(exp_rank, x="rank_group", y="explicit_share", color="rank_group",
                      color_discrete_sequence=[PRIMARY, "#f1c40f", "#e74c3c"])
        fig2.update_layout(yaxis_tickformat=".0%", showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Explicit Content Trend Over Time")
    exp_trend = df.groupby("week")["is_explicit"].apply(lambda s: s.astype(bool).mean()).reset_index(name="explicit_share")
    fig3 = px.line(exp_trend, x="week", y="explicit_share", markers=True, color_discrete_sequence=["#e74c3c"])
    fig3.update_layout(yaxis_tickformat=".0%", margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(
        "🔎 **Cultural read:** a persistently low explicit share versus catalog norms in "
        "other markets would support the brief's premise of UK listener sensitivity to "
        "explicit content — compare this figure against your US benchmark project."
    )

# ---- ALBUM STRUCTURE ----
with tab_album:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Single vs. Album Presence")
        at_counts = df["album_type"].value_counts().reset_index()
        at_counts.columns = ["album_type", "entries"]
        fig = px.pie(at_counts, names="album_type", values="entries", hole=0.5,
                      color_discrete_sequence=[PRIMARY, ACCENT, "#f1c40f"])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Album Size (total_tracks) Distribution")
        fig2 = px.histogram(df, x="total_tracks", nbins=30, color_discrete_sequence=[PRIMARY])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Album Size vs. Chart Position")
    fig3 = px.scatter(df, x="total_tracks", y="position", color="album_type", opacity=0.5,
                      color_discrete_sequence=[PRIMARY, ACCENT, "#f1c40f"])
    fig3.update_yaxes(autorange="reversed", title="Chart Position (1 = highest)")
    fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Release Format Dominance by Rank Group")
    fmt_rank = df.groupby(["rank_group", "album_type"]).size().reset_index(name="count")
    fig4 = px.bar(fmt_rank, x="rank_group", y="count", color="album_type", barmode="group",
                  category_orders={"rank_group": ["Top 10", "11-25", "26-50"]},
                  color_discrete_sequence=[PRIMARY, ACCENT, "#f1c40f"])
    fig4.update_layout(margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig4, use_container_width=True)

# ---- DURATION ----
with tab_duration:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Track Duration Distribution")
        fig = px.histogram(df, x="duration_min", nbins=40, color_discrete_sequence=[PRIMARY])
        fig.update_layout(xaxis_title="Duration (minutes)", margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Short vs. Medium vs. Long Form")
        bucket_counts = df["duration_bucket"].value_counts().reset_index()
        bucket_counts.columns = ["bucket", "count"]
        fig2 = px.pie(bucket_counts, names="bucket", values="count", hole=0.5,
                      color_discrete_sequence=[PRIMARY, "#f1c40f", ACCENT])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Duration vs. Popularity Bucket")
    fig3 = px.box(df, x="popularity_bucket", y="duration_min", color="popularity_bucket",
                  category_orders={"popularity_bucket": ["Low", "Medium", "High"]},
                  color_discrete_sequence=[ACCENT, "#f1c40f", PRIMARY])
    fig3.update_layout(yaxis_title="Duration (minutes)", showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(
        "🔎 **UK listener indicator:** compare median duration across popularity tiers — "
        "if higher-popularity tracks cluster tighter around a duration band, that band is "
        "a strong UK format signal for release planning."
    )

# ---- MARKET STRUCTURE ----
with tab_market:
    st.subheader("Playlist Concentration Ratio (Top 5 Artist Share) — Weekly Trend")
    def weekly_top5_share(g):
        counts = g["artist_single"].value_counts()
        return counts.head(5).sum() / len(g) if len(g) else 0
    weekly_conc = ex.groupby("week").apply(weekly_top5_share).reset_index(name="top5_share")
    fig = px.area(weekly_conc, x="week", y="top5_share", color_discrete_sequence=[ACCENT])
    fig.update_layout(yaxis_tickformat=".0%", margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Diversity Score Over Time")
        st.caption("Unique artists ÷ total entries, computed weekly")
        def weekly_diversity(g):
            return g["artist_single"].nunique() / len(g) if len(g) else 0
        weekly_div = ex.groupby("week").apply(weekly_diversity).reset_index(name="diversity_score")
        fig2 = px.line(weekly_div, x="week", y="diversity_score", markers=True, color_discrete_sequence=[PRIMARY])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        st.subheader("Content Variety Index Over Time")
        st.caption("Same base metric, viewed monthly for a smoother trend")
        def monthly_variety(g):
            return g["artist_single"].nunique() / len(g) if len(g) else 0
        monthly_var = ex.groupby("month").apply(monthly_variety).reset_index(name="variety_index")
        fig3 = px.bar(monthly_var, x="month", y="variety_index", color_discrete_sequence=[PRIMARY])
        fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Market Structure Summary")
    summary_df = pd.DataFrame({
        "Metric": ["Artist Concentration Index (Top 5)", "Unique Artist Count", "Collaboration Ratio",
                   "Explicit Content Share", "Single : Album Ratio", "Content Variety Index"],
        "Value": [
            f"{kpis['artist_concentration_index']*100:.2f}%",
            f"{kpis['unique_artist_count']:,}",
            f"{kpis['collaboration_ratio']*100:.2f}%",
            f"{kpis['explicit_share']*100:.2f}%",
            f"{kpis['single_album_ratio']:.2f}" if not np.isnan(kpis['single_album_ratio']) else "N/A",
            f"{kpis['content_variety_index']:.4f}",
        ],
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------------------
# RAW DATA EXPLORER
# --------------------------------------------------------------------------------------
with st.expander("🗂️ View filtered raw data"):
    st.dataframe(
        df[["date", "position", "song", "artist", "popularity", "duration_min",
            "album_type", "total_tracks", "is_explicit", "is_collab", "rank_group"]]
        .sort_values(["date", "position"]),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Download filtered data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="uk_top50_filtered.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    f"Atlantic Recording Corporation · UK Top 50 Market Structure Analysis · "
    f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
