
# =========================================
# Engineer Visit RAG – Phase 2
# Analytics + Intelligence (TF-IDF, Stable)
# =========================================

import streamlit as st
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Engineer Visit Knowledge Dashboard (RAG)",
    layout="wide"
)

st.title("🛠️ Engineer Visit Knowledge Dashboard (RAG)")
st.caption("Phase 2 – Analytics + Intelligence | TF-IDF (Stable, Cloud-safe)")

# -----------------------------
# Helper configuration
# -----------------------------
USELESS_PHRASES = [
    "visited site",
    "checked system",
    "working fine",
    "all ok",
    "ok",
    "done"
]

# -----------------------------
# Helper functions
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
    analytics_keywords = [
        "how many", "total", "count", "number",
        "offline", "visit", "visits"
    ]
    for k in analytics_keywords:
        if k in q:
            return "ANALYTICS"
    return "EXPERIENCE"

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("⚙️ Upload & Filters")

uploaded_file = st.sidebar.file_uploader(
    "Upload Engineer Visit Excel",
    type=["xlsx"]
)

filter_system = st.sidebar.text_input("Filter by System (optional)")
filter_city = st.sidebar.text_input("Filter by City (optional)")

# -----------------------------
# Load data
# -----------------------------
if uploaded_file is None:
    st.info("👈 Upload an Excel file to begin")
    st.stop()

df = pd.read_excel(uploaded_file)

# Normalize column names
df.columns = [c.strip().lower() for c in df.columns]

# Try to auto-detect columns
def find_col(keyword):
    for c in df.columns:
        if keyword in c:
            return c
    return None

col_remarks = find_col("remark")
col_system = find_col("system")
col_city = find_col("city")
col_engineer = find_col("engineer")

if col_remarks is None:
    st.error("❌ Engineer Remarks column not found")
    st.stop()

# Fill missing columns
if col_system is None:
    df["system"] = "Unknown"
    col_system = "system"

if col_city is None:
    df["city"] = "Unknown"
    col_city = "city"

if col_engineer is None:
    df["engineer"] = "Unknown"
    col_engineer = "engineer"

# -----------------------------
# Cleaning + features
# -----------------------------
df["clean_remarks"] = df[col_remarks].apply(clean_text)
df["fix_type"] = df[col_remarks].apply(detect_fix_type)

df = df[df["clean_remarks"] != ""]

# Apply filters
if filter_system:
    df = df[df[col_system].str.contains(filter_system, case=False, na=False)]

if filter_city:
    df = df[df[col_city].str.contains(filter_city, case=False, na=False)]

# -----------------------------
# Vectorization (TF-IDF)
# -----------------------------
vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    min_df=2
)

X = vectorizer.fit_transform(df["clean_remarks"])

st.success(f"✅ Indexed {len(df)} engineer visit experiences")

# =============================
# PHASE 2 – ANALYTICS
# =============================
st.subheader("📊 Phase 2 – Operational Analytics")

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Total Visits", len(df))

with c2:
    st.metric("Permanent Fix %",
              round((df["fix_type"] == "Permanent").mean() * 100, 1))

with c3:
    st.metric("Temporary Fix %",
              round((df["fix_type"] == "Temporary").mean() * 100, 1))

# Charts
st.subheader("📈 Key Insights")

colA, colB = st.columns(2)

with colA:
    st.caption("Top Systems")
    st.bar_chart(df[col_system].value_counts().head(10))

with colB:
    st.caption("Fix Type Distribution")
    st.bar_chart(df["fix_type"].value_counts())

# =============================
# PHASE 2 – RAG SEARCH
# =============================
st.subheader("🔍 Ask a Question (Based on Past Engineer Experience)")

query = st.text_input("Ask a site / fault / solution related question")

if query:
    intent = detect_intent(query)

    # ---------------------------
    # ANALYTICS MODE
    # ---------------------------
    if intent == "ANALYTICS":
        st.subheader("📊 Analytical Answer")

        q = query.lower()

        if "offline" in q:
            count = df[df["clean_remarks"].str.contains("offline", na=False)].shape[0]
            st.metric("Total Offline Engineer Visits", count)

            st.write("Explanation:")
            st.write("Counted visits where engineer remarks mention 'offline'.")

        elif "cctv" in q:
            count = df[df[col_system].str.contains("cctv", case=False, na=False)].shape[0]
            st.metric("Total CCTV Engineer Visits", count)

        else:
            st.warning("This analytics question is not yet mapped.")

    # ---------------------------
    # EXPERIENCE MODE (RAG)
    # ---------------------------
    else:
        q_vec = vectorizer.transform([clean_text(query)])
        scores = cosine_similarity(q_vec, X).flatten()
        top_idx = scores.argsort()[-5:][::-1]

        st.markdown("### ✅ Relevant Past Solutions")

        for i in top_idx:
            row = df.iloc[i]
            with st.expander(
                f"{row[col_system]} | {row[col_city]} | Fix: {row['fix_type']}"
            ):
                st.write("**Engineer:**", row[col_engineer])
                st.write("**Original Remark:**")
                st.write(row[col_remarks])  








