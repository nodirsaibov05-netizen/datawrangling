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

    st.title("A. Upload & Data Overview")

    st.markdown(
        "Upload your file in one of the following formats: **CSV**, **Excel (.xlsx)** or **JSON**.\n"
        "For coursework requirements, datasets should ideally have ≥ 1000 rows and ≥ 8 columns."
    )

    # Выбор разделителя для CSV (показываем всегда)
    separator = st.selectbox(
        "CSV delimiter (separator)",
        options=[", (comma)", "; (semicolon)", "\\t (tab)", "| (pipe)", "space"],
        index=1,  # по умолчанию semicolon
        help="Choose the character that separates columns in your CSV file"
    )

    sep_map = {
        ", (comma)": ",",
        "; (semicolon)": ";",
        "\\t (tab)": "\t",
        "| (pipe)": "|",
        "space": " "
    }

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
            with st.spinner(f"Reading file {original_name} ..."):

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
                                decimal=','
                            )
                            st.info(f"Successfully read with encoding: {enc}, separator: '{selected_sep}'")
                            break
                        except Exception:
                            continue

                    if df is None:
                        st.error("Failed to read CSV with any encoding and selected separator.")
                        st.stop()

                elif ext in ["xlsx", "xls"]:
                    df = pd.read_excel(uploaded_file, engine="openpyxl")

                elif ext == "json":
                    df = pd.read_json(uploaded_file)

                st.session_state.df_original = df.copy()
                st.session_state.df_working = df.copy()
                st.session_state.transform_log = []
                st.session_state.file_name = original_name

                st.success(f"File loaded: **{original_name}**  •  {df.shape[0]:,} rows × {df.shape[1]} columns")

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    if st.session_state.df_working is not None:
        df = st.session_state.df_working

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", f"{df.shape[0]:,}")
        col2.metric("Columns", df.shape[1])
        col3.metric("Missing cells", df.isna().sum().sum())
        col4.metric("Full duplicates", df.duplicated().sum())

        tab1, tab2, tab3, tab4 = st.tabs(["Columns & Types", "Numeric Stats", "Missing Values", "Duplicates"])

        with tab1:
            st.subheader("Columns and types")
            overview = pd.DataFrame({
                "Column": df.columns,
                "Type": df.dtypes.astype(str),
                "Non-null": df.notna().sum(),
                "% Filled": (df.notna().mean() * 100).round(1)
            })
            st.dataframe(overview, use_container_width=True)

        with tab2:
            st.subheader("Numeric statistics")
            st.dataframe(df.describe().round(2), use_container_width=True)

        with tab3:
            st.subheader("Missing values")
            miss = pd.DataFrame({
                "Column": df.columns,
                "Missing": df.isna().sum(),
                "%": (df.isna().mean() * 100).round(2)
            }).sort_values("Missing", ascending=False)
            st.dataframe(miss[miss["Missing"] > 0], use_container_width=True)

        with tab4:
            st.subheader("Duplicates")
            st.metric("Full duplicates", df.duplicated().sum())

        if st.button("Show first 500 rows"):
            st.dataframe(df.head(500), use_container_width=True)

# ────────────────────────────────────────────────
#  Page B — Cleaning & Preparation
# ────────────────────────────────────────────────
elif page == "B. Cleaning & Preparation":
    st.title("B. Cleaning & Preparation Studio")

    if st.session_state.get("df_working") is None:
        st.warning("Please upload a dataset first on the Upload & Overview page.")
    else:
        df = st.session_state.df_working
        # Preview before/after helper
        def show_preview(before_df, after_df, action_name):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Before**")
                st.metric("Rows", before_df.shape[0])
                st.dataframe(before_df.head(3))
            with col2:
                st.markdown("**After**")
                st.metric("Rows", after_df.shape[0])
                st.dataframe(after_df.head(3))

        # Transformation log display
        with st.expander("Transformation Log (last 5 steps)", expanded=False):
            if st.session_state.transform_log:
                log_df = pd.DataFrame(st.session_state.transform_log[-5:])
                st.dataframe(log_df, use_container_width=True)
            else:
                st.info("No transformations yet.")
        st.subheader("Current dataset shape")
        st.metric("Rows × Columns", f"{df.shape[0]:,} × {df.shape[1]}")

        # 4.1 Missing Values Handling
        with st.expander("🧹 4.1 Missing Values Handling", expanded=True):
            miss = pd.DataFrame({
                "Column": df.columns,
                "Missing Count": df.isna().sum(),
                "% Missing": (df.isna().mean() * 100).round(2)
            }).sort_values("Missing Count", ascending=False)

            miss_active = miss[miss["Missing Count"] > 0]
            if miss_active.empty:
                st.success("No missing values — great!")
            else:
                st.dataframe(
                    miss_active.style.bar(subset="% Missing", color="#ff9800"),
                    use_container_width=True,
                    hide_index=True
                )

            action = st.radio("Choose action:", [
                "Do nothing",
                "Drop rows with missing in selected columns",
                "Drop columns with > X% missing",
                "Fill with constant",
                "Fill with statistic (mean/median/mode)",
                "Forward / Backward fill"
            ], horizontal=False)

            if action != "Do nothing":
                selected_cols = st.multiselect("Select columns", df.columns.tolist())

                if selected_cols:
                    if action == "Drop rows with missing in selected columns":
                        if st.button("Apply: Drop rows", type="primary"):
                            before = df.shape[0]
                            df = df.dropna(subset=selected_cols)
                            st.session_state.df_working = df
                            st.success(f"Dropped {before - df.shape[0]} rows. New shape: {df.shape}")
                            # st.rerun() — убрано, чтобы не ломать переключение

                    # ... остальные действия можно добавить позже

        # DUPLICATES
        with st.expander("🧹 4.2 Duplicates", expanded=False):
            dup_count = df.duplicated().sum()
            st.write(f"Full-row duplicates: **{dup_count}**")

            if dup_count > 0:
                keep = st.radio("Keep", ["first", "last"])
                if st.button(f"Remove duplicates (keep {keep})", type="primary"):
                    before = len(df)
                    df = df.drop_duplicates(keep=keep)
                    st.session_state.df_working = df
                    st.success(f"Removed {before - len(df)} duplicates.")
                    # st.rerun() — убрано

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



# import streamlit as st
# import pandas as pd
# import numpy as np
# from io import BytesIO
# import datetime

# # ────────────────────────────────────────────────
# #  Page config & basic styling
# # ────────────────────────────────────────────────
# st.set_page_config(
#     page_title="AI-Assisted Data Wrangler & Visualizer",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Немного кастомизации (опционально)
# st.markdown("""
#     <style>
#     .stButton>button {width: 100%;}
#     .reportview-container {background: #f8f9fa;}
#     </style>
# """, unsafe_allow_html=True)

# # ────────────────────────────────────────────────
# #  Session state initialization
# # ────────────────────────────────────────────────
# if "df_original" not in st.session_state:
#     st.session_state.df_original = None
#     st.session_state.df_working = None
#     st.session_state.transform_log = []
#     st.session_state.file_name = None

# # ────────────────────────────────────────────────
# #  Sidebar navigation
# # ────────────────────────────────────────────────
# st.sidebar.title("Data Wrangler")
# page = st.sidebar.radio("Go to", [
#     "A. Upload & Overview",
#     "B. Cleaning & Preparation",
#     "C. Visualization Builder",
#     "D. Export & Report"
# ])

# if st.sidebar.button("🔄 Reset everything", type="primary"):
#     for key in list(st.session_state.keys()):
#         del st.session_state[key]
#     st.rerun()

# # ────────────────────────────────────────────────
# #  Page A — Upload & Overview
# # ────────────────────────────────────────────────
# if page == "A. Upload & Overview":

#     st.title("A. Upload & Data Overview")

#     st.markdown(
#         "Upload your file in one of the following formats: **CSV**, **Excel (.xlsx)** or **JSON**.\n"
#         "For coursework requirements, datasets should ideally have ≥ 1000 rows and ≥ 8 columns."
#     )

#     # Выбор разделителя для CSV (показываем всегда)
#     separator = st.selectbox(
#         "CSV delimiter (separator)",
#         options=[", (comma)", "; (semicolon)", "\\t (tab)", "| (pipe)", "space"],
#         index=1,  # по умолчанию semicolon
#         help="Choose the character that separates columns in your CSV file"
#     )

#     sep_map = {
#         ", (comma)": ",",
#         "; (semicolon)": ";",
#         "\\t (tab)": "\t",
#         "| (pipe)": "|",
#         "space": " "
#     }

#     selected_sep = sep_map[separator]

#     uploaded_file = st.file_uploader(
#         "Choose a file",
#         type=["csv", "xlsx", "json"],
#         accept_multiple_files=False,
#         help="Supported formats: .csv, .xlsx, .json"
#     )

#     if uploaded_file is not None:
#         ext = uploaded_file.name.split('.')[-1].lower()
#         original_name = uploaded_file.name

#         try:
#             with st.spinner(f"Reading file {original_name} ..."):

#                 if ext == "csv":
#                     encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
#                     df = None
#                     for enc in encodings:
#                         try:
#                             uploaded_file.seek(0)
#                             df = pd.read_csv(
#                                 uploaded_file,
#                                 encoding=enc,
#                                 sep=selected_sep,
#                                 on_bad_lines='skip',
#                                 decimal=','
#                             )
#                             st.info(f"Successfully read with encoding: {enc}, separator: '{selected_sep}'")
#                             break
#                         except Exception:
#                             continue

#                     if df is None:
#                         st.error("Failed to read CSV with any encoding and selected separator.")
#                         st.stop()

#                 elif ext in ["xlsx", "xls"]:
#                     df = pd.read_excel(uploaded_file, engine="openpyxl")

#                 elif ext == "json":
#                     df = pd.read_json(uploaded_file)

#                 st.session_state.df_original = df.copy()
#                 st.session_state.df_working = df.copy()
#                 st.session_state.transform_log = []
#                 st.session_state.file_name = original_name

#                 st.success(f"File loaded: **{original_name}**  •  {df.shape[0]:,} rows × {df.shape[1]} columns")

#         except Exception as e:
#             st.error(f"Error reading file: {str(e)}")

#     if st.session_state.df_working is not None:
#         df = st.session_state.df_working

#         col1, col2, col3, col4 = st.columns(4)
#         col1.metric("Rows", f"{df.shape[0]:,}")
#         col2.metric("Columns", df.shape[1])
#         col3.metric("Missing cells", df.isna().sum().sum())
#         col4.metric("Full duplicates", df.duplicated().sum())

#         tab1, tab2, tab3, tab4 = st.tabs(["Columns & Types", "Numeric Stats", "Missing Values", "Duplicates"])

#         with tab1:
#             st.subheader("Columns and types")
#             overview = pd.DataFrame({
#                 "Column": df.columns,
#                 "Type": df.dtypes.astype(str),
#                 "Non-null": df.notna().sum(),
#                 "% Filled": (df.notna().mean() * 100).round(1)
#             })
#             st.dataframe(overview, use_container_width=True)

#         with tab2:
#             st.subheader("Numeric statistics")
#             st.dataframe(df.describe().round(2), use_container_width=True)

#         with tab3:
#             st.subheader("Missing values")
#             miss = pd.DataFrame({
#                 "Column": df.columns,
#                 "Missing": df.isna().sum(),
#                 "%": (df.isna().mean() * 100).round(2)
#             }).sort_values("Missing", ascending=False)
#             st.dataframe(miss[miss["Missing"] > 0], use_container_width=True)

#         with tab4:
#             st.subheader("Duplicates")
#             st.metric("Full duplicates", df.duplicated().sum())

#         if st.button("Show first 500 rows"):
#             st.dataframe(df.head(500), use_container_width=True)

# # ────────────────────────────────────────────────
# #  Page B — Cleaning & Preparation
# # ────────────────────────────────────────────────
# elif page == "B. Cleaning & Preparation":

#     st.title("B. Cleaning & Preparation Studio")

#     if st.session_state.get("df_working") is None:
#         st.warning("Please upload a dataset first on the Upload & Overview page.")
#     else:
#         df = st.session_state.df_working

#         st.subheader("Current dataset shape")
#         st.metric("Rows × Columns", f"{df.shape[0]:,} × {df.shape[1]}")

#         st.divider()

#         # ── MISSING VALUES ───────────────────────────────────────
#         with st.expander("🧹 4.1 Missing Values Handling", expanded=True):

#             miss = df.isna().sum()
#             miss = miss[miss > 0]
#             if len(miss) == 0:
#                 st.success("No missing values – great!")
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

#                     selected_cols = st.multiselect("Select columns", df.columns.tolist())

#                     if selected_cols:

#                         if action == "Drop rows with missing in selected columns":
#                             if st.button("Apply: Drop rows with missing in selected columns", type="primary"):
#                                 before = len(df)
#                                 df = df.dropna(subset=selected_cols)
#                                 after = len(df)
#                                 st.session_state.df_working = df
#                                 st.session_state.transform_log.append({
#                                     "step": "dropna_rows",
#                                     "columns": selected_cols,
#                                     "rows_before": before,
#                                     "rows_after": after,
#                                     "timestamp": pd.Timestamp.now()
#                                 })
#                                 st.success(f"Dropped {before - after} rows. New shape: {df.shape}")

#                         # ... остальные действия по missing values можно добавить позже

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

#         st.divider()
#         st.subheader("Transformation log (last 5 steps)")
#         if st.session_state.transform_log:
#             log_df = pd.DataFrame(st.session_state.transform_log[-5:])
#             st.dataframe(log_df)
#         else:
#             st.info("No transformations applied yet.")

# # Заглушки для остальных страниц
# elif page == "C. Visualization Builder":
#     st.title("Visualization Builder")
#     st.info("Coming soon...")

# elif page == "D. Export & Report":
#     st.title("Export & Report")
#     st.info("Coming soon...")
