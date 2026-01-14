#Engineer Visit RAG – Phase 2

#Analytics + Intelligence (TF-IDF based, Stable)

#Mobile + Streamlit Cloud Ready

#===============================

import streamlit as st
import pandas as pd
import numpy as np
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

#-------------------------------

#Page Config

#-------------------------------

st.set_page_config( page_title="Engineer Visit Knowledge Dashboard (RAG)", layout="wide", )

st.title("🛠️ Engineer Visit Knowledge Dashboard (RAG)") st.caption("Phase 2 – Analytics + Intelligence | TF-IDF (Stable, Cloud-safe)")

#-------------------------------

#Helper Functions

#-------------------------------

USELESS_PHRASES = [ "visited site", "checked system", "ok", "working fine", "all ok", ]

def clean_text(text): if not isinstance(text, str): return "" text = text.lower() for p in USELESS_PHRASES: text = text.replace(p, "") text = re.sub(r"\s+", " ", text).strip() return text

def detect_fix_type(text): t = text.lower() if any(w in t for w in ["replace", "replaced", "changed", "new", "faulty"]): return "Permanent" if any(w in t for w in ["restart", "reset", "temporary", "reboot"]): return "Temporary" return "Unclear"

#-------------------------------

#Sidebar – Upload & Filters

#-------------------------------

with st.sidebar: st.header("⚙️ Upload & Filters") uploaded_file = st.file_uploader("Upload Engineer Visit Excel", type=["xlsx"])

filter_system = st.text_input("Filter by System (optional)")
filter_city = st.text_input("Filter by City (optional)")

#-------------------------------

#Load Data

#-------------------------------

if not uploaded_file: st.info("👈 Upload an Excel file to begin") st.stop()

try: df = pd.read_excel(uploaded_file) except Exception as e: st.error(f"Failed to read file: {e}") st.stop()

#-------------------------------

#Column Normalization

#-------------------------------

df.columns = [c.strip().lower() for c in df.columns]

REQUIRED_COLS = { "engineer remarks": "remarks", "system": "system", "city": "city", "engineer": "engineer", }

rename_map = {} for k, v in REQUIRED_COLS.items(): for col in df.columns: if k in col: rename_map[col] = v

df = df.rename(columns=rename_map)

if "remarks" not in df.columns: st.error("❌ 'Engineer Remarks' column not found") st.stop()

Fill missing

for col in ["system", "city", "engineer"]: if col not in df.columns: df[col] = "Unknown"

#-------------------------------

#Cleaning + Feature Engineering

#-------------------------------

df["clean_remarks"] = df["remarks"].apply(clean_text) df["fix_type"] = df["remarks"].apply(detect_fix_type)

Apply Filters

if filter_system: df = df[df["system"].str.contains(filter_system, case=False, na=False)]

if filter_city: df = df[df["city"].str.contains(filter_city, case=False, na=False)]

#-------------------------------

#Indexing (TF-IDF)

#-------------------------------

vectorizer = TfidfVectorizer( stop_words="english", ngram_range=(1, 2), min_df=2 )

X = vectorizer.fit_transform(df["clean_remarks"])

st.success(f"✅ Indexed {len(df)} engineer visit experiences")

#===============================

#PHASE 2 – ANALYTICS

#===============================

st.subheader("📊 Phase 2 – Operational Analytics")

col1, col2, col3 = st.columns(3)

with col1: st.metric("Total Visits", len(df))

with col2: repeat_issues = df["clean_remarks"].value_counts().iloc[0] st.metric("Most Repeated Issue Count", repeat_issues)

with col3: perm_pct = round((df["fix_type"] == "Permanent").mean() * 100, 1) st.metric("Permanent Fix %", f"{perm_pct}%")

#-------------------------------

#Charts

#-------------------------------

st.subheader("📈 Insights")

c1, c2 = st.columns(2)

with c1: st.caption("Top Systems") st.bar_chart(df["system"].value_counts().head(10))

with c2: st.caption("Fix Type Distribution") st.bar_chart(df["fix_type"].value_counts())

#===============================

#PHASE 2 – RAG QUESTIONING

#===============================

st.subheader("🔍 Ask a Question (Based on Past Engineer Experience)")

query = st.text_input("Ask a site / fault / solution related question")

if query: q_clean = clean_text(query) q_vec = vectorizer.transform([q_clean])

sims = cosine_similarity(q_vec, X).flatten()
top_idx = sims.argsort()[-5:][::-1]

st.markdown("### ✅ Relevant Past Solutions")

for i in top_idx:
    row = df.iloc[i]
    with st.expander(f"{row['system']} | {row['city']} | Fix: {row['fix_type']}"):
        st.write("**Engineer:**", row["engineer"])
        st.write("**Original Remark:**")
        st.write(row["remarks"])

#===============================

#END

#=============================== 




