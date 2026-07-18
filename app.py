import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import io

# ---------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------
st.set_page_config(page_title="Player Tier Predictor", page_icon="⚽", layout="wide")

MODEL_DIR = Path(__file__).parent / "model"

# ---------------------------------------------------------------
# Required input schema
# ---------------------------------------------------------------
NUM_FEATURES = [
    'age', 'height_cm', 'weight_kg', 'market_value_eur', 'matches_played',
    'pass_accuracy', 'shots_on_target', 'expected_goals_xg', 'expected_assists_xa',
    'key_passes', 'successful_passes', 'total_passes', 'dribbles_attempted',
    'successful_dribbles', 'crosses', 'successful_crosses', 'tackles', 'interceptions',
    'clearances', 'blocks', 'aerial_duels_won', 'aerial_duels_lost', 'recoveries',
    'defensive_actions', 'fouls_committed', 'fouls_suffered', 'distance_covered_km',
    'sprint_distance_km', 'top_speed_kmh', 'accelerations', 'decelerations',
    'stamina_score', 'player_rating', 'performance_score', 'offensive_contribution',
    'defensive_contribution', 'possession_impact', 'pressure_resistance',
    'creativity_score', 'consistency_score', 'clutch_performance_score', 'minutes_played'
]
CAT_FEATURES = ['position', 'preferred_foot']
REQUIRED_COLUMNS = NUM_FEATURES + CAT_FEATURES
OPTIONAL_DISPLAY_COLUMNS = ['player_name', 'team', 'nationality', 'club_name']

VALID_POSITIONS = ['Forward', 'Midfielder', 'Defender', 'Goalkeeper']
VALID_FEET = ['Left', 'Right']

TIER_COLORS = {'Good': '#2ecc71', 'Average': '#f39c12', 'Below Average': '#e74c3c'}


# ---------------------------------------------------------------
# Load model (cached so it only loads once per session)
# ---------------------------------------------------------------
@st.cache_resource
def load_model():
    clf = joblib.load(MODEL_DIR / "player_tier_classifier.joblib")
    feature_columns = joblib.load(MODEL_DIR / "model_feature_columns.joblib")
    return clf, feature_columns


clf, feature_columns = load_model()


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def build_template_excel():
    """Empty template with the exact required columns."""
    template = pd.DataFrame(columns=OPTIONAL_DISPLAY_COLUMNS + REQUIRED_COLUMNS)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        template.to_excel(writer, index=False, sheet_name="players")
    buf.seek(0)
    return buf


def validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return missing


def predict(df: pd.DataFrame):
    work = df.copy()

    # Coerce numeric columns, fill anything unparsable with 0
    for c in NUM_FEATURES:
        work[c] = pd.to_numeric(work[c], errors="coerce").fillna(0)

    # Clean categorical columns
    work['position'] = work['position'].astype(str).str.strip().str.capitalize()
    work['preferred_foot'] = work['preferred_foot'].astype(str).str.strip().str.capitalize()

    X = pd.get_dummies(work[NUM_FEATURES + CAT_FEATURES], columns=CAT_FEATURES, drop_first=True)
    # Align to the exact columns/order the model was trained on
    X = X.reindex(columns=feature_columns, fill_value=0)

    preds = clf.predict(X)
    proba = clf.predict_proba(X)
    confidence = proba.max(axis=1)

    result = df.copy()
    result['predicted_tier'] = preds
    result['confidence'] = (confidence * 100).round(1)
    return result


# ---------------------------------------------------------------
# UI
# ---------------------------------------------------------------
st.title("⚽ Player Tier Predictor")
st.caption("Upload an Excel sheet of player stats — one row per player — to predict "
           "whether each player is **Good / Average / Below Average**.")

with st.expander("📋 Required columns in your Excel sheet (click to expand)", expanded=False):
    st.markdown("Your sheet must have **one row per player** with these exact column names:")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Numeric columns (41):**")
        st.code(", ".join(NUM_FEATURES), language=None)
    with col2:
        st.markdown("**Categorical columns (2):**")
        st.markdown(f"- `position` → one of: {', '.join(VALID_POSITIONS)}")
        st.markdown(f"- `preferred_foot` → one of: {', '.join(VALID_FEET)}")
        st.markdown("**Optional (for display only, not used in prediction):**")
        st.markdown(f"`{'`, `'.join(OPTIONAL_DISPLAY_COLUMNS)}`")

    st.download_button(
        "⬇️ Download blank template (.xlsx)",
        data=build_template_excel(),
        file_name="player_prediction_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.divider()

uploaded = st.file_uploader("Upload your player stats Excel file (.xlsx)", type=["xlsx", "xls"])

if uploaded is not None:
    try:
        df_input = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Couldn't read that file: {e}")
        st.stop()

    if df_input.empty:
        st.warning("The uploaded sheet has no rows.")
        st.stop()

    missing = validate_columns(df_input)
    if missing:
        st.error(
            f"❌ Missing {len(missing)} required column(s): `{'`, `'.join(missing)}`\n\n"
            "Download the template above, or check for typos / renamed columns."
        )
        st.stop()

    st.success(f"✅ Loaded {len(df_input)} player(s) — all required columns found.")

    with st.spinner("Predicting..."):
        results = predict(df_input)

    st.subheader("Predictions")

    display_cols = [c for c in OPTIONAL_DISPLAY_COLUMNS if c in results.columns]
    display_cols += ['position', 'predicted_tier', 'confidence']
    st.dataframe(
        results[display_cols].style.apply(
            lambda row: [f"background-color: {TIER_COLORS[row['predicted_tier']]}22"] * len(row),
            axis=1
        ),
        use_container_width=True,
        height=min(35 * (len(results) + 1), 500),
    )

    # Summary
    st.subheader("Summary")
    c1, c2 = st.columns([1, 2])
    tier_counts = results['predicted_tier'].value_counts().reindex(
        ['Good', 'Average', 'Below Average']
    ).fillna(0).astype(int)
    with c1:
        st.bar_chart(tier_counts, color="#3498db")
    with c2:
        for tier, count in tier_counts.items():
            st.metric(tier, int(count))

    # Download results
    out_buf = io.BytesIO()
    with pd.ExcelWriter(out_buf, engine="openpyxl") as writer:
        results.to_excel(writer, index=False, sheet_name="predictions")
    out_buf.seek(0)
    st.download_button(
        "⬇️ Download predictions (.xlsx)",
        data=out_buf,
        file_name="player_tier_predictions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.info("Upload a file to get started, or grab the template above first.")

st.divider()
st.caption(
    "Model: Random Forest classifier trained on aggregated FIFA World Cup 2026 "
    "player performance data. Tiers were derived via KMeans clustering (k=3) on "
    "playing-style features, ranked by goals + assists + Player-of-the-Match awards."
)
