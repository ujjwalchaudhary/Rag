import streamlit as st
import pandas as pd
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(
    page_title="Engineer Visit RAG Dashboard (Stable)",
    layout="wide"
)

USELESS_PHRASES = [
    "all system working fine",
    "system working fine",
    "working fine",
    "ok",
    "done",
    "visited site",
    "checked",
    "resolved",
    "today i visited"
]

def clean_remarks(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    for phrase in USELESS_PHRASES:
        text = text.replace(phrase, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def split_remark(text):
    symptom = ""
    cause = ""
    solution = ""

    if "but" in text:
        parts = text.split("but", 1)
        symptom = parts[0].strip()
        cause = parts[1].strip()
    else:
        cause = text

    if any(w in text for w in ["restart", "reset", "replaced", "changed", "new"]):
        solution = text

    return symptom, cause, solution

def detect_fix_type(text):
    if any(w in text for w in ["replaced", "changed", "new unit", "new"]):
        return "Permanent Fix"
    if any(w in text for w in ["restart", "reset", "temporary"]):
        return "Temporary Fix"
    return "Unclear"

st.sidebar.title("⚙️ Upload & Filters")

uploaded_file = st.sidebar.file_uploader(
    "Upload Engineer Visit Excel",
    type=["xlsx"]
)

system_filter = st.sidebar.text_input("Filter by System (optional)")
city_filter = st.sidebar.text_input("Filter by City (optional)")

st.title("🧠 Engineer Visit Knowledge Dashboard (RAG)")
st.caption("Stable TF-IDF based retrieval (Windows safe)")

if uploaded_file is None:
    st.info("⬅️ Upload an Excel file to start")
    st.stop()

df = pd.read_excel(uploaded_file)

if "ENGINEER REMARKS" not in df.columns:
    st.error("❌ Column 'ENGINEER REMARKS' not found in Excel")
    st.stop()

texts = []
metadata = []

for _, row in df.iterrows():
    raw = row.get("ENGINEER REMARKS", "")
    cleaned = clean_remarks(raw)
    if cleaned == "":
        continue

    symptom, cause, solution = split_remark(cleaned)
    fix_type = detect_fix_type(cleaned)

    doc = f"""
    Site symptom: {symptom}
    Identified cause: {cause}
    Solution applied: {solution}
    Fix type: {fix_type}
    """

    texts.append(doc)

    metadata.append({
        "PMS ID": row.get("PMS ID"),
        "System": row.get("System"),
        "Engineer": row.get("Engineer"),
        "City": row.get("City"),
        "Fix Type": fix_type
    })

vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
tfidf_matrix = vectorizer.fit_transform(texts)

st.success(f"✅ Indexed {len(texts)} engineer experiences")

st.subheader("🔎 Ask a Question")

query = st.text_input("Example: system online but cctv not working")

if query:
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    top_indices = scores.argsort()[-5:][::-1]

    st.subheader("📋 Relevant Past Solutions")

    for i in top_indices:
        meta = metadata[i]

        if system_filter and system_filter.lower() not in str(meta.get("System", "")).lower():
            continue
        if city_filter and city_filter.lower() not in str(meta.get("City", "")).lower():
            continue

        with st.expander(
            f"PMS: {meta.get('PMS ID')} | System: {meta.get('System')} | Fix: {meta.get('Fix Type')}"
        ):
            st.text(texts[i])
            st.json(meta) 