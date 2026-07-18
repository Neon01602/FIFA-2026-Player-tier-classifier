# Player Tier Predictor — Streamlit App

Predicts whether a player is **Good / Average / Below Average** from an
uploaded Excel sheet of per-player stats, using a Random Forest model
trained on the FIFA World Cup 2026 player performance dataset.

## Folder contents
```
streamlit_app/
├── app.py                      # the Streamlit app
├── requirements.txt            # dependencies
├── sample_test_data.xlsx       # 15 real-format rows to test with
└── model/
    ├── player_tier_classifier.joblib
    └── model_feature_columns.joblib
```

## Run it locally
```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL it prints (usually http://localhost:8501),
and upload `sample_test_data.xlsx` to try it out.

## Deploy for free — Streamlit Community Cloud
This app has no server-side dependencies beyond what's in
`requirements.txt`, so Streamlit Community Cloud (free) is the
easiest option:

1. **Create a GitHub repo** and push this entire `streamlit_app/`
   folder to it (keep the folder structure — `app.py` and
   `requirements.txt` at the repo root, `model/` as a subfolder).
   ```bash
   cd streamlit_app
   git init
   git add .
   git commit -m "Player tier predictor app"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```
2. Go to **https://share.streamlit.io** and sign in with GitHub.
3. Click **"New app"**, pick your repo/branch, and set the main file
   path to `app.py`.
4. Click **Deploy**. It builds from `requirements.txt` automatically
   and gives you a public URL like
   `https://<your-app-name>.streamlit.app`.

That's it — no server config needed, the two `.joblib` model files
are small enough to live directly in the repo.

## How the tiers were built

**PCA projection of the 3 clusters** — the 24-dimensional feature space
compressed to 2D. Tiers are visually separated, with some overlap
between Average and Good:

![PCA cluster scatter](assets/pca_cluster_scatter.png)

**Tier boxplots** — `player_rating` and `total_goals` step up cleanly
from Below Average → Average → Good; `defensive_actions` is highest
for Average rather than Good, since goalkeepers and low-minute
defenders cluster there:

![Tier boxplots](assets/tier_boxplots.png)

**Correlation heatmap** of the clustering features, useful for
spotting redundant inputs (e.g. `distance_covered_km`,
`sprint_distance_km`, and `minutes_played` are tightly correlated):

![Correlation heatmap](assets/correlation_heatmap.png)

## Required columns for prediction
The uploaded Excel file needs **one row per player** with these
columns (also shown inside the app, and downloadable as a blank
template from the app itself):

**Numeric (41):** age, height_cm, weight_kg, market_value_eur,
matches_played, pass_accuracy, shots_on_target, expected_goals_xg,
expected_assists_xa, key_passes, successful_passes, total_passes,
dribbles_attempted, successful_dribbles, crosses, successful_crosses,
tackles, interceptions, clearances, blocks, aerial_duels_won,
aerial_duels_lost, recoveries, defensive_actions, fouls_committed,
fouls_suffered, distance_covered_km, sprint_distance_km,
top_speed_kmh, accelerations, decelerations, stamina_score,
player_rating, performance_score, offensive_contribution,
defensive_contribution, possession_impact, pressure_resistance,
creativity_score, consistency_score, clutch_performance_score,
minutes_played

**Categorical (2):** position (Forward/Midfielder/Defender/Goalkeeper),
preferred_foot (Left/Right)

**Optional, display only:** player_name, team, nationality, club_name
