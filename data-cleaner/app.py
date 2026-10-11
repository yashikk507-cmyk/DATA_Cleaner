"""
app.py - Data Cleaner web app.

Run with:  streamlit run app.py
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from cleaner import clean_dataset

SAMPLE_FILE = Path(__file__).parent / "sample_messy_data.csv"

st.set_page_config(
    page_title="Data Cleaner",
    page_icon="🧹",
    layout="wide",
)

# ---------- styling ----------
st.markdown(
    """
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1200px; }
        .hero {
            background: linear-gradient(135deg, #1f4e79 0%, #2e75b6 100%);
            color: white; padding: 1.8rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
        }
        .hero h1 { color: white; margin: 0 0 .3rem 0; font-size: 2.1rem; }
        .hero p  { margin: 0; opacity: .92; font-size: 1.02rem; }
        .step-title { font-weight: 600; font-size: 1.05rem; margin: .4rem 0 .6rem 0; }
        .card {
            border: 1px solid rgba(128,128,128,.25); border-radius: 12px;
            padding: 1rem 1.2rem; margin-bottom: .6rem;
        }
        .muted { opacity: .7; font-size: .9rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.25); border-radius: 12px; padding: .8rem 1rem;
        }
        .change-item { padding: .35rem 0; border-bottom: 1px solid rgba(128,128,128,.15); }
        .change-item:last-child { border-bottom: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- header ----------
st.markdown(
    """
    <div class="hero">
        <h1>🧹 Data Cleaner</h1>
        <p>Upload a messy CSV or Excel file and get back a clean, analysis-ready table
        with a report of every change made.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- helpers ----------
def read_upload(uploaded_file):
    """Read a CSV or Excel upload, trying common text encodings for CSV."""
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    raw = uploaded_file.getvalue()
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read this file's text encoding. Try saving it as UTF-8 CSV.")


def read_sample():
    return pd.read_csv(SAMPLE_FILE)


# ---------- sidebar ----------
with st.sidebar:
    st.header("⚙️ Options")
    text_case = st.selectbox(
        "Text case",
        options=[None, "lower", "title", "upper"],
        format_func=lambda x: {
            None: "Keep as is",
            "lower": "lowercase",
            "title": "Title Case",
            "upper": "UPPERCASE",
        }[x],
        help="Makes 'AMAZON' and 'amazon' match when you analyse the data later.",
    )
    drop_dupes = st.toggle("Remove duplicate rows", value=True)

    st.divider()
    st.markdown("**🔒 Privacy**")
    st.caption(
        "Your file is processed in memory and is not saved anywhere. "
        "Run this app on your own computer to keep your data private."
    )

# ---------- input ----------
st.markdown('<div class="step-title">1. Choose your data</div>', unsafe_allow_html=True)
col_upload, col_sample = st.columns([3, 1], vertical_alignment="bottom")
with col_upload:
    uploaded = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )
with col_sample:
    use_sample = st.button("Try sample data")

if use_sample:
    st.session_state["use_sample"] = True
if uploaded is not None:
    st.session_state["use_sample"] = False

# ---------- load ----------
raw_df, source_name = None, None
try:
    if uploaded is not None:
        raw_df = read_upload(uploaded)
        source_name = uploaded.name
    elif st.session_state.get("use_sample"):
        raw_df = read_sample()
        source_name = "sample_messy_data.csv"
except Exception as error:  # show a friendly message instead of a crash
    st.error(f"We couldn't read this file: {error}")
    st.stop()

if raw_df is None:
    st.info("Upload a file or click **Try sample data** to get started.")
    st.stop()

if raw_df.empty:
    st.warning("The file is empty. Please upload a file that contains rows of data.")
    st.stop()

# ---------- clean ----------
clean_df, report = clean_dataset(raw_df, text_case=text_case, drop_duplicates=drop_dupes)

# ---------- results ----------
st.markdown('<div class="step-title">2. Results</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows in", f"{report['rows_in']:,}")
m2.metric("Rows after cleaning", f"{report['rows_out']:,}")
m3.metric("Duplicates removed", f"{report['duplicates_removed']:,}")
m4.metric("Missing cells left", f"{int(clean_df.isna().sum().sum()):,}")

# download
csv_bytes = clean_df.to_csv(index=False).encode("utf-8-sig")  # utf-8-sig keeps ₹ readable in Excel
base_name = Path(source_name).stem
st.download_button(
    label="⬇️ Download cleaned CSV",
    data=csv_bytes,
    file_name=f"{base_name}_cleaned.csv",
    mime="text/csv",
    type="primary",
)

tab_clean, tab_compare, tab_columns, tab_changes = st.tabs(
    ["Cleaned data", "Before & after", "Column details", "What changed"]
)

with tab_clean:
    st.dataframe(clean_df, hide_index=True)

with tab_compare:
    left, right = st.columns(2)
    with left:
        st.caption("Original file")
        st.dataframe(raw_df.fillna("").astype(str), hide_index=True, height=420)
    with right:
        st.caption("Cleaned file")
        st.dataframe(clean_df.fillna("").astype(str), hide_index=True, height=420)

with tab_columns:
    st.caption("Every column with its type and how many values are missing.")
    st.dataframe(report["column_summary"], hide_index=True)

with tab_changes:
    if report["changes"]:
        for change in report["changes"]:
            st.markdown(f'<div class="change-item">✅ {change}</div>', unsafe_allow_html=True)
    else:
        st.write("No changes were needed. Your data was already clean.")
