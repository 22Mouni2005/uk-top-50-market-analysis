# 🇬🇧 UK Top 50 — Market Structure & Content Analytics

An interactive **Streamlit analytics dashboard** for exploring UK Top 50 playlist data through artist concentration, diversity, collaboration patterns, content characteristics, album structure, track duration, and market-level trends.

> **Project type:** Data Analytics / Data Visualization / Streamlit  
> **Core technologies:** Python, Pandas, NumPy, Plotly, Streamlit, NetworkX

## 📌 Project Overview

This project transforms UK Top 50 playlist snapshots into an interactive analytical dashboard.

Instead of looking at a chart only as a ranked list of songs, the application analyzes the underlying market structure and answers questions such as:

- How concentrated is the chart among the most frequently appearing artists?
- How diverse is the artist mix?
- How common are collaborations?
- What proportion of chart entries contain explicit content?
- How does single-vs-album representation vary across the chart?
- What is the distribution of track duration?
- How does content structure change over time and across rank groups?
- How does artist concentration compare with market diversity?

The dashboard recalculates its metrics dynamically whenever filters are changed.

## ✨ Key Features

### 📊 Executive KPIs
The dashboard calculates:

- **Artist Concentration Index** — share of chart entries associated with the top five artists.
- **Unique Artist Count** — number of distinct artists represented.
- **Collaboration Ratio** — percentage of entries credited to multiple artists.
- **Explicit Content Share** — percentage of entries marked explicit.
- **Single : Album Ratio** — relative representation of single and album formats.
- **Content Variety Index** — unique artists divided by total chart entries.

### 📈 Interactive Analysis

The application contains seven analytical sections:

1. **Overview**
   - Domestic vs international artist presence using a clearly labelled proxy.
   - Daily chart-entry volume.

2. **Artist Dominance**
   - Artist leaderboard.
   - Artist diversity over time.
   - Concentration trends.
   - Rank-group analysis.

3. **Collaboration**
   - Solo vs collaboration distribution.
   - Average collaborators per song.
   - Collaboration rate by rank group.
   - Artist collaboration network.

4. **Explicit Content**
   - Explicit vs clean distribution.
   - Rank-group comparison.
   - Trend analysis.

5. **Album Structure**
   - Single vs album distribution.
   - Album-size distribution.
   - Album size vs chart position.
   - Format dominance by rank group.

6. **Duration**
   - Track-duration distribution.
   - Short / medium / long classification.
   - Duration compared with popularity tiers.

7. **Market Structure**
   - Weekly concentration.
   - Diversity score trends.
   - Monthly content-variety analysis.
   - Summary tables.

## 🎛️ Interactive Filters

Use the sidebar to dynamically filter the dashboard by:

- Date range
- Artist
- Solo vs collaboration
- Album type
- Explicit vs clean content

The KPIs and visualizations update automatically based on the selected filters.

## 🗂️ Project Structure

```text
UK_Top_50_Analytics/
│
├── app.py
├── Atlantic_United_Kingdom.csv
├── requirements.txt
├── README.md
└── .gitignore
```

### File descriptions

| File | Purpose |
|---|---|
| `app.py` | Main Streamlit dashboard and analytics logic |
| `Atlantic_United_Kingdom.csv` | UK Top 50 playlist dataset |
| `requirements.txt` | Python package dependencies |
| `README.md` | Project documentation |
| `.gitignore` | Prevents unnecessary/local files from being committed |

## 🧰 Tech Stack

- **Python** — application and analytical logic
- **Pandas** — data cleaning, transformation and analysis
- **NumPy** — numerical calculations
- **Plotly** — interactive charts and visualizations
- **Streamlit** — dashboard interface
- **NetworkX** — artist collaboration network analysis

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/uk-top-50-market-analysis.git
cd uk-top-50-market-analysis
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

### 5. Open the application

Streamlit normally opens the dashboard automatically.

If it does not, open:

```text
http://localhost:8501
```

## 📊 Dataset

The included CSV contains **27,800 UK Top 50 chart entries** with fields covering:

- Date
- Chart position
- Song
- Artist
- Popularity
- Duration
- Album type
- Total tracks
- Explicit-content flag
- Album artwork URL

The dashboard performs preprocessing such as:

- Date conversion and validation
- Artist-name standardization
- Collaboration splitting
- Rank grouping
- Duration bucketing
- Popularity tiering
- Weekly and monthly aggregation

## 🔬 Analytical Methodology

### Artist Concentration

The concentration metric measures the share of artist appearances associated with the five most frequently appearing artists.

A higher value indicates a more concentrated chart.

### Content Variety

The Content Variety Index is calculated as:

```text
Unique Artists / Total Chart Entries
```

A higher value indicates greater artist variety relative to the number of chart entries.

### Collaboration Analysis

Artists separated by `&` are treated as individual collaborators for diversity and network calculations.

### Rank Groups

Chart positions are grouped into:

- **Top 10**
- **11–25**
- **26–50**

This makes it easier to compare market characteristics across different levels of chart performance.

## ⚠️ Important Methodological Note

The source dataset does not contain an explicit artist-nationality field.

Therefore, the **UK / Domestic vs International** analysis uses a predefined artist-name proxy and should be interpreted as **directional rather than authoritative nationality classification**.

For production or research publication, this classification should be replaced with a verified artist-nationality dataset or authoritative metadata source.

## 🔐 Data & Security

Before publishing the repository:

- Do not commit API keys, passwords, access tokens, or `.env` files.
- Do not commit private credentials.
- Review the dataset and confirm that you have permission to redistribute it.
- If the CSV is not redistributable, remove it from the repository and provide instructions for obtaining the data separately.

## 🌐 Optional: Deploy the Dashboard

The application can be deployed using a Streamlit-compatible hosting service.

After deployment, add the live application URL to the top of this README so recruiters can try the dashboard without installing Python.

## 🎯 Future Improvements

Potential enhancements include:

- Automated data ingestion from an approved data source
- Verified artist nationality metadata
- More advanced concentration metrics such as HHI
- Artist-level time-series forecasting
- Exportable analytical reports
- Authentication for private datasets
- Deployment with automated CI/CD
- Automated data-quality checks
- Additional market and geographic comparisons

## 💼 Resume Description

**UK Top 50 Market Structure & Content Analytics Dashboard**  
Developed an interactive Streamlit dashboard to analyze 27,800 UK Top 50 playlist entries using Python, Pandas, NumPy, Plotly, and NetworkX. Implemented data preprocessing, artist concentration and diversity metrics, collaboration-network analysis, content classification, album-structure analysis, duration analysis, interactive filtering, and time-series market insights.

## 👩‍💻 Author

**Mounika Karri**  
B.Tech — Computer Science and Engineering

GitHub: `https://github.com/YOUR_USERNAME`

---

⭐ If you find this project useful, consider starring the repository.
