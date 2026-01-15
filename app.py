import streamlit as st
import pandas as pd
import numpy as np
import re

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Universal Excel Insight Engine",
    layout="wide"
)

st.title("🧠 Universal Excel Insight Engine")
st.caption("Schema-Aware | Evidence-Based | No Hallucination")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload ANY Excel file",
    type=["xlsx"]
)

if uploaded_file is None:
    st.stop()

df = pd.read_excel(uploaded_file)
original_df = df.copy()

st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns")

# -----------------------------
# SCHEMA DETECTION
# -----------------------------
def normalize(col):
    return re.sub(r"[^a-z0-9]", "", col.lower())

normalized_cols = {normalize(c): c for c in df.columns}

def find_column(keywords):
    for k, original in normalized_cols.items():
        for word in keywords:
            if word in k:
                return original
    return None

SCHEMA = {
    "id": find_column(["complaint", "id", "ticket", "reference"]),
    "text": find_column(["remark", "comment", "description", "body", "fault"]),
    "status": find_column(["status", "close"]),
    "tat": find_column(["tat"]),
    "date": find_column(["date", "created", "logged"]),
    "city": find_column(["city"]),
    "state": find_column(["state"]),
}

with st.expander("🔍 Detected Schema"):
    st.json(SCHEMA)

# -----------------------------
# INSIGHT ENGINE STORAGE
# -----------------------------
INSIGHTS = []

def register_insight(
    title,
    category,
    description,
    rule,
    rows,
    columns
):
    INSIGHTS.append({
        "title": title,
        "category": category,
        "description": description,
        "rule": rule,
        "row_count": len(rows),
        "rows": rows,
        "columns": columns
    })

# -----------------------------
# INSIGHT ENGINE 1: DATA QUALITY
# -----------------------------
for col in df.columns:
    missing_rows = df[df[col].isna()].index.tolist()
    if len(missing_rows) > 0:
        register_insight(
            title=f"Missing values in '{col}'",
            category="Data Quality Gap",
            description=f"{len(missing_rows)} records have missing values in {col}",
            rule="IS NULL",
            rows=missing_rows,
            columns=[col]
        )

# -----------------------------
# INSIGHT ENGINE 2: WASTE (NO MEANINGFUL TEXT)
# -----------------------------
if SCHEMA["text"]:
    useless_patterns = [
        "ok", "fine", "working", "no issue", "checked"
    ]

    def low_info(text):
        if not isinstance(text, str):
            return True
        t = text.lower()
        return any(p in t for p in useless_patterns) and len(t) < 40

    waste_rows = df[df[SCHEMA["text"]].apply(low_info)].index.tolist()

    if waste_rows:
        register_insight(
            title="Low-information activity records",
            category="Potential Waste",
            description=f"{len(waste_rows)} records lack proper explanation",
            rule="LOW_INFORMATION_TEXT",
            rows=waste_rows,
            columns=[SCHEMA["text"]]
        )

# -----------------------------
# INSIGHT ENGINE 3: TIME RISK (TAT)
# -----------------------------
if SCHEMA["tat"]:
    tat_series = pd.to_numeric(df[SCHEMA["tat"]], errors="coerce")
    median_tat = tat_series.median()

    delayed_rows = tat_series[tat_series > median_tat].index.tolist()

    if delayed_rows:
        register_insight(
            title="Long resolution time risk",
            category="Operational Risk",
            description=f"{len(delayed_rows)} records exceed median TAT",
            rule=f"TAT > {median_tat}",
            rows=delayed_rows,
            columns=[SCHEMA["tat"]]
        )

# -----------------------------
# INSIGHT ENGINE 4: REPEAT ID RISK
# -----------------------------
if SCHEMA["id"]:
    duplicates = df[df.duplicated(SCHEMA["id"], keep=False)]
    if not duplicates.empty:
        register_insight(
            title="Repeated IDs detected",
            category="Repeat Risk",
            description=f"{duplicates[SCHEMA['id']].nunique()} IDs repeat",
            rule="DUPLICATE_ID",
            rows=duplicates.index.tolist(),
            columns=[SCHEMA["id"]]
        )

# -----------------------------
# DISPLAY INSIGHTS
# -----------------------------
st.header("📌 Auto-Generated Insights")

if not INSIGHTS:
    st.info("No major risks detected.")
else:
    for i, ins in enumerate(INSIGHTS):
        with st.expander(f"🔎 {ins['title']} ({ins['category']})"):
            st.write(ins["description"])
            st.markdown(f"**Rule:** `{ins['rule']}`")
            st.markdown(f"**Rows affected:** {ins['row_count']}")
            st.markdown(f"**Columns involved:** {', '.join(ins['columns'])}")

            # -----------------------------
            # DRILL DOWN (REAL, SAFE)
            # -----------------------------
            drill = st.checkbox(
                "Show affected records",
                key=f"drill_{i}"
            )

            if drill:
                st.dataframe(
                    original_df.loc[ins["rows"], ins["columns"] + (
                        [SCHEMA["id"]] if SCHEMA["id"] else []
                    )]
                )

# -----------------------------
# EXPORT EVIDENCE
# -----------------------------
st.header("⬇️ Export Evidence")

if st.button("Download Insight Evidence"):
    report_rows = []
    for ins in INSIGHTS:
        for r in ins["rows"]:
            report_rows.append({
                "Insight": ins["title"],
                "Category": ins["category"],
                "Rule": ins["rule"],
                "Row Index": r
            })

    report_df = pd.DataFrame(report_rows)

    st.download_button(
        "Download CSV",
        report_df.to_csv(index=False),
        file_name="insight_evidence.csv"
    ) 
