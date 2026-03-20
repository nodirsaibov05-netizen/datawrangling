# app.py
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import datetime

# ────────────────────────────────────────────────
#  Page config & basic styling
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-Assisted Data Wrangler & Visualizer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Немного кастомизации (опционально)
st.markdown("""
    <style>
    .stButton>button {width: 100%;}
    .reportview-container {background: #f8f9fa;}
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#  Session state initialization
# ────────────────────────────────────────────────
if "df_original" not in st.session_state:
    st.session_state.df_original = None
    st.session_state.df_working = None
    st.session_state.transform_log = []
    st.session_state.file_name = None

# ────────────────────────────────────────────────
#  Sidebar navigation
# ────────────────────────────────────────────────
st.sidebar.title("Data Wrangler")
page = st.sidebar.radio("Go to", [
    "A. Upload & Overview",
    "B. Cleaning & Preparation",
    "C. Visualization Builder",
    "D. Export & Report"
])

if st.sidebar.button("🔄 Reset everything", type="primary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ────────────────────────────────────────────────
#  Page A — Upload & Overview
# ────────────────────────────────────────────────
if page == "A. Upload & Overview":

    st.title("Upload & Data Overview")

    uploaded_file = st.file_uploader(
        "Upload your dataset (CSV, Excel, JSON)",
        type=["csv", "xlsx", "xls", "json"],
        accept_multiple_files=False
    )

    if uploaded_file is not None:

        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.session_state.file_name = uploaded_file.name

        try:
            with st.spinner("Loading file..."):
                if file_ext in ["csv"]:
                    df = pd.read_csv(uploaded_file)
                elif file_ext in ["xlsx", "xls"]:
                    df = pd.read_excel(uploaded_file)
                elif file_ext == "json":
                    df = pd.read_json(uploaded_file)
                else:
                    st.error("Unsupported file format.")
                    st.stop()

            # Сохраняем копии
            st.session_state.df_original = df.copy()
            st.session_state.df_working = df.copy()
            st.session_state.transform_log = []

            st.success(f"File loaded: **{uploaded_file.name}**  •  {df.shape[0]:,} rows × {df.shape[1]} columns")

        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    # Если данные уже загружены — показываем обзор
    if st.session_state.df_working is not None:
        df = st.session_state.df_working

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{df.shape[0]:,}")
        col2.metric("Columns", df.shape[1])
        col3.metric("File", st.session_state.file_name)
        col4.metric("Last update", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

        tab1, tab2, tab3, tab4 = st.tabs(["Columns & Types", "Summary Stats", "Missing Values", "Duplicates"])

        with tab1:
            st.subheader("Columns and inferred types")
            dtypes_df = pd.DataFrame({
                "Column": df.columns,
                "Dtype": df.dtypes.astype(str),
                "Non-null count": df.notna().sum(),
                "Non-null %": (df.notna().mean() * 100).round(1).astype(str) + " %"
            })
            st.dataframe(dtypes_df, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("Numeric summary")
            st.dataframe(df.describe().round(2), use_container_width=True)

            st.subheader("Categorical / object summary")
            cat_cols = df.select_dtypes(include=["object", "category"]).columns
            if len(cat_cols) > 0:
                for c in cat_cols[:6]:  # лимит, чтобы не перегружать
                    st.write(f"**{c}** — top values")
                    st.write(df[c].value_counts().head(8))
            else:
                st.info("No categorical columns detected.")

        with tab3:
            st.subheader("Missing values")
            miss = pd.DataFrame({
                "Column": df.columns,
                "Missing count": df.isna().sum(),
                "Missing %": (df.isna().mean() * 100).round(2).astype(str) + " %"
            }).sort_values("Missing count", ascending=False)
            miss["Missing % (num)"] = (df.isna().mean() * 100).round(2)
            st.dataframe(miss.style.bar(subset="Missing % (num)", color="#ff9800"), use_container_width=True, hide_index=True)

            total_miss = df.isna().sum().sum()
            st.metric("Total missing cells", total_miss, delta=f"{total_miss / df.size * 100:.1f}% of all cells")

        with tab4:
            st.subheader("Duplicate rows")
            dup_count = df.duplicated().sum()
            st.metric("Full row duplicates", dup_count, delta_color="inverse" if dup_count > 0 else "normal")

            if dup_count > 0:
                if st.button("Show first 5 duplicate rows"):
                    st.dataframe(df[df.duplicated(keep=False)].head(10))

# ────────────────────────────────────────────────
#  Page B — Cleaning & Preparation (начало)
# ────────────────────────────────────────────────
elif page == "B. Cleaning & Preparation":

    st.title("Cleaning & Preparation Studio")

    if st.session_state.df_working is None:
        st.warning("Please upload a dataset first on the Upload page.")
    else:
        df = st.session_state.df_working

        # Пока просто показываем текущее состояние
        st.subheader("Current dataset shape")
        st.write(f"{df.shape[0]:,} rows × {df.shape[1]} columns")

        st.divider()

        # ── MISSING VALUES ───────────────────────────────────────
        with st.expander("🧹 4.1 Missing Values Handling", expanded=True):

            miss = df.isna().sum()
            miss = miss[miss > 0]
            if len(miss) == 0:
                st.success("No missing values — great!")
            else:
                st.write("Columns with missing values:")
                st.write(miss.sort_values(ascending=False))

                action = st.radio("Choose action:", [
                    "Do nothing",
                    "Drop rows with missing in selected columns",
                    "Drop columns with > X% missing",
                    "Fill with constant",
                    "Fill with statistic (mean/median/mode)",
                    "Forward / Backward fill"
                ], horizontal=False)

                if action != "Do nothing":

                    if "Drop rows" in action:
                        cols = st.multiselect("Select columns (rows with NaN in ANY of these will be dropped)", df.columns)
                        if cols and st.button("Apply: Drop rows with missing in selected columns", type="primary"):
                            before = len(df)
                            df = df.dropna(subset=cols)
                            after = len(df)
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "dropna_rows",
                                "columns": cols,
                                "rows_before": before,
                                "rows_after": after,
                                "timestamp": pd.Timestamp.now()
                            })
                            st.success(f"Dropped {before - after} rows. New shape: {df.shape}")
                            st.rerun()

                    # ... остальные действия по missing values добавим в следующей итерации

        # ── DUPLICATES ───────────────────────────────────────────
        with st.expander("🧹 4.2 Duplicates", expanded=False):
            dup_count = df.duplicated().sum()
            st.write(f"Full-row duplicates: **{dup_count}**")

            if dup_count > 0:
                keep = st.radio("Keep", ["first", "last"])
                if st.button(f"Remove duplicates (keep {keep})", type="primary"):
                    before = len(df)
                    df = df.drop_duplicates(keep=keep)
                    after = len(df)
                    st.session_state.df_working = df
                    st.session_state.transform_log.append({
                        "step": "remove_duplicates",
                        "keep": keep,
                        "rows_before": before,
                        "rows_after": after,
                        "timestamp": pd.Timestamp.now()
                    })
                    st.success(f"Removed {before - after} duplicates.")
                    st.rerun()

        st.divider()
        st.subheader("Transformation log (last 5 steps)")
        if st.session_state.transform_log:
            log_df = pd.DataFrame(st.session_state.transform_log[-5:])
            st.dataframe(log_df)
        else:
            st.info("No transformations applied yet.")

# Заглушки для остальных страниц
elif page == "C. Visualization Builder":
    st.title("Visualization Builder")
    st.info("Coming soon...")

elif page == "D. Export & Report":
    st.title("Export & Report")
    st.info("Coming soon...")
