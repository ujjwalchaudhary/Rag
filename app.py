
import streamlit as st
import pandas as pd
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Engineer Visit Knowledge Dashboard (RAG)",
    layout="wide"
)

st.title("🛠️ Engineer Visit Knowledge Dashboard (RAG)")
st.caption("Phase 3 – Analytics + City + Asset Intelligence (Stable TF-IDF)")

# -----------------------------
# CONSTANTS
# -----------------------------
USELESS_PHRASES = [
    "all system working fine",
    "all systems working fine",
    "checked ok",
    "no issue found",
    "site ok",
    "working fine"
]

OFFLINE_KEYWORDS = [
    "offline", "down", "not working", "no connectivity",
    "network down", "router down", "power issue"
]

ASSET_MAP = {
    "router": ["router", "network", "lan", "wan"],
    "camera": ["camera", "cam"],
    "dvr": ["dvr", "nvr", "recorder"]
}

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    for p in USELESS_PHRASES:
        text = text.replace(p, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_fix_type(text):
    t = text.lower()
    if any(w in t for w in ["replace", "replaced", "changed", "new", "faulty"]):
        return "Permanent"
    if any(w in t for w in ["restart", "reset", "temporary", "reboot"]):
        return "Temporary"
    return "Unclear"


def detect_intent(query):
    q = query.lower()
    analytics_words = [
        "how many", "total", "count", "number",
        "offline", "visit", "visits"
    ]
    for w in analytics_words:
        if w in q:
            return "ANALYTICS"
    return "EXPERIENCE"


def extract_location(query, locations):
    q = query.lower()
    for loc in locations:
        if loc.lower() in q:
            return loc
    return None


def extract_asset(query):
    q = query.lower()
    for asset, words in ASSET_MAP.items():
        for w in words:
            if w in q:
                return asset
    return None


# -----------------------------
# SIDEBAR – FILE UPLOAD
# -----------------------------
st.sidebar.header("⚙️ Upload & Filters")

uploaded_file = st.sidebar.file_uploader(
    "Upload Engineer Visit Excel",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("👈 Upload an Excel file to begin.")
    st.stop()

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_excel(uploaded_file)

# Required columns (adjust names here if needed)
REMARK_COL = "Remark"
CITY_COL = "City"
ENGINEER_COL = "Engineer Name"

df = df.dropna(subset=[REMARK_COL])

df["clean_remark"] = df[REMARK_COL].apply(clean_text)
df["fix_type"] = df["clean_remark"].apply(detect_fix_type)

# -----------------------------
# BASIC ANALYTICS
# -----------------------------
st.subheader("📊 Fix Type Distribution")
fix_counts = df["fix_type"].value_counts()
st.bar_chart(fix_counts)

# -----------------------------
# TF-IDF (Experience Retrieval)
# -----------------------------
vectorizer = TfidfVectorizer(stop_words="english")
tfidf_matrix = vectorizer.fit_transform(df["clean_remark"])

# -----------------------------
# QUESTION INPUT
# -----------------------------
st.subheader("🔍 Ask a Question (Based on Past Engineer Experience)")
query = st.text_input("Ask a site / fault / solution related question")

if query:
    intent = detect_intent(query)

    # ======================================================
    # ANALYTICS MODE
    # ======================================================
    if intent == "ANALYTICS":
        st.subheader("📈 Analytical Answer")

        q = query.lower()
        location = extract_location(query, df[CITY_COL].dropna().unique())
        asset = extract_asset(query)

        df_filtered = df.copy()

        if location:
            df_filtered = df_filtered[
                df_filtered[CITY_COL].str.contains(location, case=False, na=False)
            ]

        # OFFLINE VISIT LOGIC
        if "offline" in q or "down" in q:
            offline_mask = df_filtered["clean_remark"].apply(
                lambda x: any(k in x for k in OFFLINE_KEYWORDS)
            )
            count = offline_mask.sum()

            st.metric(
                label="Total Offline Engineer Visits",
                value=int(count)
            )

            st.caption(
                "Counted visits where remarks indicate offline / down / connectivity issues."
            )

        # ASSET FAULT LOGIC
        elif asset:
            asset_words = ASSET_MAP[asset]
            asset_mask = df_filtered["clean_remark"].apply(
                lambda x: any(w in x for w in asset_words)
            )
            count = asset_mask.sum()

            st.metric(
                label=f"Total {asset.capitalize()} Related Visits",
                value=int(count)
            )

            st.caption(
                f"Counted visits mentioning {asset}-related issues."
            )

        else:
            st.warning("⚠️ This analytics question is not yet mapped.")

    # ======================================================
    # EXPERIENCE MODE (RAG)
    # ======================================================
    else:
        st.subheader("✅ Relevant Past Solutions")

        query_vec = vectorizer.transform([clean_text(query)])
        similarity = cosine_similarity(query_vec, tfidf_matrix)[0]

        top_indices = similarity.argsort()[-5:][::-1]

        for idx in top_indices:
            row = df.iloc[idx]

            with st.expander(
                f"{row.get('System', 'System')} | {row.get(CITY_COL, 'City')} | Fix: {row['fix_type']}"
            ):
                st.write(f"**Engineer:** {row.get(ENGINEER_COL, 'N/A')}")
                st.write("**Original Remark:**")
                st.write(row[REMARK_COL]) 
