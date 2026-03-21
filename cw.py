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



if page == "A. Upload & Overview":

    st.title("A. Upload & Data Overview")

    st.markdown(
        "Upload your file in one of the following formats: **CSV**, **Excel (.xlsx)** or **JSON**.\n"
        "For coursework requirements, datasets should ideally have ≥ 1000 rows and ≥ 8 columns."
    )


    # Выбор разделителя для CSV (показываем всегда)
separator = st.selectbox(
    "CSV delimiter (separator)",
    options=[", (comma)", "; (semicolon)", "\\t (tab)", "| (pipe)", "space"],
    index=1,  # по умолчанию semicolon — потому что у тебя именно он в файлах
    help="Choose the character that separates columns in your CSV file"
)

# Словарь маппинга — ОБЯЗАТЕЛЬНО ДО строки selected_sep
sep_map = {
    ", (comma)": ",",
    "; (semicolon)": ";",
    "\\t (tab)": "\t",
    "| (pipe)": "|",
    "space": " "
}

# Теперь берём значение — sep_map уже существует
selected_sep = sep_map[separator]

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "json"],
    accept_multiple_files=False,
    help="Supported formats: .csv, .xlsx, .json"
)

if uploaded_file is not None:
    ext = uploaded_file.name.split('.')[-1].lower()
    original_name = uploaded_file.name

    try:
        with st.spinner(f"Reading {original_name} ..."):
            if ext == "csv":
                encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
                df = None
                for enc in encodings:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(
                            uploaded_file,
                            encoding=enc,
                            sep=selected_sep,
                            on_bad_lines='skip',
                            decimal=','  # для русских чисел 15,5 вместо 15.5
                        )
                        st.info(f"Read successfully with encoding: {enc}, separator: '{selected_sep}'")
                        break
                    except Exception as e:
                        continue

                if df is None:
                    st.error("Failed to read CSV with any encoding and selected separator.")
                    st.stop()

            elif ext == "xlsx":
                df = pd.read_excel(uploaded_file, engine="openpyxl")

            elif ext == "json":
                try:
                    df = pd.read_json(uploaded_file, orient="records")
                except:
                    df = pd.read_json(uploaded_file, orient="columns")

        # Сохранение в session_state
        st.session_state.df_original = df.copy()
        st.session_state.df_working = df.copy()
        st.session_state.transform_log = []
        st.session_state.last_uploaded_name = original_name
        st.session_state.file_uploaded_at = pd.Timestamp.now()

        st.success(f"File loaded successfully: **{original_name}** ({df.shape[0]:,} rows × {df.shape[1]} cols)")

    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
   

    # ── Show overview if data is present in session ───────────────────────────────
    if st.session_state.get("df_working") is not None:

        df = st.session_state.df_working

        # Top metrics row — always show number of columns
        cols = st.columns([2, 2, 2, 2, 3])
        cols[0].metric("Rows", f"{df.shape[0]:,}")
        cols[1].metric("Columns", df.shape[1])
        cols[2].metric("Missing cells", df.isna().sum().sum())
        cols[3].metric("Full duplicates", df.duplicated().sum())
        cols[4].metric("Uploaded", st.session_state.file_uploaded_at.strftime("%Y-%m-%d %H:%M"))

        # Tabs for detailed profiling
        tab_overview, tab_numeric, tab_categorical, tab_missing, tab_duplicates = st.tabs([
            "Column Overview",
            "Numeric Statistics",
            "Categorical",
            "Missing Values",
            "Duplicates"
        ])

        with tab_overview:
            st.subheader("Columns and Data Types")
            overview_df = pd.DataFrame({
                "Column": df.columns,
                "Data Type": df.dtypes.astype(str),
                "Unique Values": df.nunique(),
                "Non-Null Count": df.notna().sum(),
                "% Filled": (df.notna().mean() * 100).round(1)
            })
            st.dataframe(
                overview_df.style.format({"% Filled": "{:.1f} %"}),
                use_container_width=True,
                hide_index=True
            )

            if df.shape[0] < 1000 or df.shape[1] < 8:
                st.warning(
                    f"Current dataset has {df.shape[0]:,} rows and {df.shape[1]} columns.\n"
                    "Coursework recommends ≥ 1000 rows and ≥ 8 columns."
                )

        with tab_numeric:
            st.subheader("Numeric Columns Statistics")
            num_stats = df.describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).round(2).T
            st.dataframe(num_stats, use_container_width=True)

        with tab_categorical:
            st.subheader("Categorical / Text Columns")
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

            if not cat_cols:
                st.info("No categorical columns detected.")
            else:
                selected_cat = st.selectbox("Select column to inspect", cat_cols)
                if selected_cat:
                    vc = df[selected_cat].value_counts(dropna=False).head(15).reset_index()
                    vc.columns = [selected_cat, "Count"]
                    vc["%"] = (vc["Count"] / len(df) * 100).round(1)
                    st.dataframe(vc, hide_index=True, use_container_width=True)

        with tab_missing:
            st.subheader("Missing Values by Column")
            miss_df = pd.DataFrame({
                "Column": df.columns,
                "Missing Count": df.isna().sum(),
                "% Missing": (df.isna().mean() * 100).round(2)
            })
            miss_df = miss_df[miss_df["Missing Count"] > 0].sort_values("Missing Count", ascending=False)

            if miss_df.empty:
                st.success("No missing values found — great!")
            else:
                st.dataframe(
                    miss_df.style
                       .format({"% Missing": "{:.2f} %"})
                       .bar(subset=["% Missing"], color="#ff9800", vmin=0, vmax=100),
                    use_container_width=True,
                    hide_index=True
                )

        with tab_duplicates:
            st.subheader("Full Row Duplicates")
            dup_count = df.duplicated().sum()
            st.metric("Number of duplicate rows", dup_count)

            if dup_count > 0:
                if st.button("Show sample duplicate rows (first 8)"):
                    st.dataframe(
                        df[df.duplicated(keep=False)].head(8),
                        use_container_width=True
                    )

        st.divider()

        # Data preview button
        if st.button("Show first 500 rows (preview)"):
            st.dataframe(df.head(500), use_container_width=True)

    else:
        st.info("No data loaded yet. Upload a file above.")

    st.caption("Full session reset button is available in the sidebar → «Reset everything»")




elif page == "B. Cleaning & Preparation":
    st.title("B. Cleaning & Preparation Studio")

    if st.session_state.get("df_working") is None:
        st.warning("No dataset uploaded yet. Go to A. Upload & Overview first.")
    else:
        df = st.session_state.df_working

        st.subheader("Current dataset shape")
        st.metric("Rows × Columns", f"{df.shape[0]:,} × {df.shape[1]}")

        st.subheader("Missing values summary")
        miss = df.isna().sum()
        st.write(miss[miss > 0])

        st.subheader("First 5 rows")
        st.dataframe(df.head(5))

        st.info("Cleaning tools (missing values, duplicates, etc.) will be added here step by step.")



# elif page == "B. Cleaning & Preparation":

#     st.title("Cleaning & Preparation Studio")

#     if st.session_state.df_working is None:
#         st.warning("Please upload a dataset first on the Upload page.")
#     else:
#         df = st.session_state.df_working

#         # Пока просто показываем текущее состояние
#         st.subheader("Current dataset shape")
#         st.write(f"{df.shape[0]:,} rows × {df.shape[1]} columns")

#         st.divider()

#         # ── MISSING VALUES ───────────────────────────────────────
#         with st.expander("🧹 4.1 Missing Values Handling", expanded=True):

#             miss = df.isna().sum()
#             miss = miss[miss > 0]
#             if len(miss) == 0:
#                 st.success("No missing values — great!")
#             else:
#                 st.write("Columns with missing values:")
#                 st.write(miss.sort_values(ascending=False))

#                 action = st.radio("Choose action:", [
#                     "Do nothing",
#                     "Drop rows with missing in selected columns",
#                     "Drop columns with > X% missing",
#                     "Fill with constant",
#                     "Fill with statistic (mean/median/mode)",
#                     "Forward / Backward fill"
#                 ], horizontal=False)

#                 if action != "Do nothing":

#                     if "Drop rows" in action:
#                         cols = st.multiselect("Select columns (rows with NaN in ANY of these will be dropped)", df.columns)
#                         if cols and st.button("Apply: Drop rows with missing in selected columns", type="primary"):
#                             before = len(df)
#                             df = df.dropna(subset=cols)
#                             after = len(df)
#                             st.session_state.df_working = df
#                             st.session_state.transform_log.append({
#                                 "step": "dropna_rows",
#                                 "columns": cols,
#                                 "rows_before": before,
#                                 "rows_after": after,
#                                 "timestamp": pd.Timestamp.now()
#                             })
#                             st.success(f"Dropped {before - after} rows. New shape: {df.shape}")
#                             st.rerun()

#                     # ... остальные действия по missing values добавим в следующей итерации

#         # ── DUPLICATES ───────────────────────────────────────────
#         with st.expander("🧹 4.2 Duplicates", expanded=False):
#             dup_count = df.duplicated().sum()
#             st.write(f"Full-row duplicates: **{dup_count}**")

#             if dup_count > 0:
#                 keep = st.radio("Keep", ["first", "last"])
#                 if st.button(f"Remove duplicates (keep {keep})", type="primary"):
#                     before = len(df)
#                     df = df.drop_duplicates(keep=keep)
#                     after = len(df)
#                     st.session_state.df_working = df
#                     st.session_state.transform_log.append({
#                         "step": "remove_duplicates",
#                         "keep": keep,
#                         "rows_before": before,
#                         "rows_after": after,
#                         "timestamp": pd.Timestamp.now()
#                     })
#                     st.success(f"Removed {before - after} duplicates.")
#                     st.rerun()

#         st.divider()
#         st.subheader("Transformation log (last 5 steps)")
#         if st.session_state.transform_log:
#             log_df = pd.DataFrame(st.session_state.transform_log[-5:])
#             st.dataframe(log_df)
#         else:
#             st.info("No transformations applied yet.")

# Заглушки для остальных страниц
elif page == "C. Visualization Builder":
    st.title("Visualization Builder")
    st.info("Coming soon...")

elif page == "D. Export & Report":
    st.title("Export & Report")
    st.info("Coming soon...")

