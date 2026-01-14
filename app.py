import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime
from io import BytesIO

def generate_insight_report(schema_df, insights, df):
    report = []

    report.append({
        "Section": "Dataset Overview",
        "Detail": f"Rows: {df.shape[0]}, Columns: {df.shape[1]}"
    })

    for _, row in schema_df.iterrows():
        report.append({
            "Section": "Detected Schema",
            "Detail": f"{row['Column']} → {row['Detected Role']}"
        })

    for ins in insights:
        report.append({
            "Section": ins["title"],
            "Detail": ins["message"]
        })

    return pd.DataFrame(report)


# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Excel Intelligence Engine", layout="wide")
st.title("🧠 Excel Intelligence Engine")
st.caption("Schema-Agnostic | Insight-First | Enterprise Safe")

# ----------------------------
# FILE UPLOAD
# ----------------------------
uploaded_file = st.file_uploader("Upload ANY Excel file", type=["xlsx"])

if uploaded_file is None:
    st.stop()

df = pd.read_excel(uploaded_file)

st.success(f"Loaded {df.shape[0]} rows × {df.shape[1]} columns")

# ======================================================
# 1️⃣ SCHEMA INTELLIGENCE ENGINE
# ======================================================

SCHEMA = {}

def detect_column_role(col, series):
    sample = series.dropna().astype(str).head(20)

    text_ratio = sample.str.len().mean()
    numeric_ratio = pd.to_numeric(series, errors="coerce").notna().mean()

    # Date detection
    try:
        pd.to_datetime(sample.head(5))
        return "DATE_EVENT"
    except:
        pass

    # ID detection
    if series.astype(str).str.match(r"^[A-Za-z0-9\-_/]+$").mean() > 0.8:
        return "ENTITY_ID"

    # Location detection
    if series.astype(str).str.len().mean() < 20:
        return "ENTITY_LOCATION"

    # Numeric signal
    if numeric_ratio > 0.7:
        return "NUMERIC_SIGNAL"

    # Long text
    if text_ratio > 30:
        return "TEXT_EXPLANATION"

    return "UNKNOWN"

for col in df.columns:
    SCHEMA[col] = detect_column_role(col, df[col])

# Show detected schema
st.subheader("🧬 Detected Schema Roles")
schema_df = pd.DataFrame({
    "Column": SCHEMA.keys(),
    "Detected Role": SCHEMA.values()
})
st.dataframe(schema_df, use_container_width=True)

st.subheader("🧭 Schema Mapping Suggestions")

SUGGESTIONS = []

for col, role in SCHEMA.items():
    sample_values = df[col].dropna().astype(str).head(3).tolist()

    if role == "UNKNOWN":
        SUGGESTIONS.append({
            "Column": col,
            "Suggested Use": "Review manually",
            "Sample Data": " | ".join(sample_values)
        })

    if role == "TEXT_EXPLANATION" and len(sample_values) < 3:
        SUGGESTIONS.append({
            "Column": col,
            "Suggested Use": "Weak text signal (may cause poor insights)",
            "Sample Data": " | ".join(sample_values)
        })

if SUGGESTIONS:
    st.warning("⚠️ Some columns need human confirmation")
    st.dataframe(pd.DataFrame(SUGGESTIONS), use_container_width=True)
else:
    st.success("✅ Schema confidence is high") 

# ======================================================
# 2️⃣ INSIGHT ENGINES
# ======================================================

INSIGHTS = []

# ----------------------------
# Data Quality Engine
# ----------------------------
text_cols = [c for c, r in SCHEMA.items() if r == "TEXT_EXPLANATION"]

if text_cols:
    vague_phrases = ["ok", "working", "no issue", "fine", "checked"]
    vague_count = 0

    for col in text_cols:
        vague_count += df[col].astype(str).str.lower().apply(
            lambda x: any(v in x for v in vague_phrases)
        ).sum()

    INSIGHTS.append({
        "title": "🟠 Data Quality Risk",
        "message": f"{vague_count} rows contain vague or low-information text."
    })

# ----------------------------
# Process Efficiency Engine
# ----------------------------
date_cols = [c for c, r in SCHEMA.items() if r == "DATE_EVENT"]

if len(date_cols) >= 2:
    df_dates = df[date_cols].apply(pd.to_datetime, errors="coerce")
    delta = (df_dates.max(axis=1) - df_dates.min(axis=1)).dt.days

    delayed = (delta > delta.median()).sum()

    INSIGHTS.append({
        "title": "⏱ Process Delay Detected",
        "message": f"{delayed} records took longer than typical completion time."
    })

# ----------------------------
# Waste Detection Engine
# ----------------------------
if text_cols and date_cols:
    waste = df[text_cols].isna().any(axis=1).sum()

    INSIGHTS.append({
        "title": "💸 Potential Waste",
        "message": f"{waste} activities lack proper explanation or closure."
    })

# ----------------------------
# Risk Engine
# ----------------------------
id_cols = [c for c, r in SCHEMA.items() if r == "ENTITY_ID"]

if id_cols:
    repeated = df[id_cols[0]].duplicated().sum()

    INSIGHTS.append({
        "title": "⚠️ Repeat Risk",
        "message": f"{repeated} repeated IDs detected (possible recurring issues)."
    })

# ======================================================
# 3️⃣ INSIGHT DASHBOARD
# ======================================================

st.subheader("📌 Auto-Generated Insights")

if not INSIGHTS:
    st.info("No high-confidence insights detected.")
else:
    for i in INSIGHTS:
        st.warning(f"**{i['title']}**\n\n{i['message']}")

st.subheader("📤 Export Insights")

report_df = generate_insight_report(schema_df, INSIGHTS, df)

col1, col2 = st.columns(2)

with col1:
   excel_buffer = BytesIO()
report_df.to_excel(excel_buffer, index=False, engine="openpyxl")
excel_buffer.seek(0)

st.download_button(
    label="⬇️ Download Insight Report (Excel)",
    data=excel_buffer,
    file_name="insight_report.xlsx",
    mi

with col2:
    st.download_button(
        label="⬇️ Download Insight Report (CSV)",
        data=report_df.to_csv(index=False),
        file_name="insight_report.csv",
        mime="text/csv"
    ) 


# ======================================================
# 4️⃣ DRILL-DOWN QUESTIONS (OPTIONAL)
# ======================================================

st.subheader("🔎 Drill-Down (Optional)")
q = st.text_input("Ask WHY / WHERE / WHICH (not discovery)")

if q:
    st.info("This version supports insight-first analysis. Question answering is a Phase-2 add-on.") 


