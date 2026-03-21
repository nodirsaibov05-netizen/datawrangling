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
#if page == "A. Upload & Overview":

    # st.title("Upload & Data Overview")

    # uploaded_file = st.file_uploader(
    #     "Upload your dataset (CSV, Excel, JSON)",
    #     type=["csv", "xlsx", "xls", "json"],
    #     accept_multiple_files=False
    # )

    # if uploaded_file is not None:

    #     file_ext = uploaded_file.name.split(".")[-1].lower()
    #     st.session_state.file_name = uploaded_file.name

    #     try:
    #         with st.spinner("Loading file..."):
    #             if file_ext in ["csv"]:
    #                 df = pd.read_csv(uploaded_file)
    #             elif file_ext in ["xlsx", "xls"]:
    #                 df = pd.read_excel(uploaded_file)
    #             elif file_ext == "json":
    #                 df = pd.read_json(uploaded_file)
    #             else:
    #                 st.error("Unsupported file format.")
    #                 st.stop()

    #         # Сохраняем копии
    #         st.session_state.df_original = df.copy()
    #         st.session_state.df_working = df.copy()
    #         st.session_state.transform_log = []

    #         st.success(f"File loaded: **{uploaded_file.name}**  •  {df.shape[0]:,} rows × {df.shape[1]} columns")

    #     except Exception as e:
    #         st.error(f"Error reading file: {e}")
    #         st.stop()

    # # Если данные уже загружены — показываем обзор
    # if st.session_state.df_working is not None:
    #     df = st.session_state.df_working

    #     col1, col2, col3, col4 = st.columns(4)
    #     col1.metric("Rows", f"{df.shape[0]:,}")
    #     col2.metric("Columns", df.shape[1])
    #     col3.metric("File", st.session_state.file_name)
    #     col4.metric("Last update", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    #     tab1, tab2, tab3, tab4 = st.tabs(["Columns & Types", "Summary Stats", "Missing Values", "Duplicates"])

    #     with tab1:
    #         st.subheader("Columns and inferred types")
    #         dtypes_df = pd.DataFrame({
    #             "Column": df.columns,
    #             "Dtype": df.dtypes.astype(str),
    #             "Non-null count": df.notna().sum(),
    #             "Non-null %": (df.notna().mean() * 100).round(1).astype(str) + " %"
    #         })
    #         st.dataframe(dtypes_df, use_container_width=True, hide_index=True)

    #     with tab2:
    #         st.subheader("Numeric summary")
    #         st.dataframe(df.describe().round(2), use_container_width=True)

    #         st.subheader("Categorical / object summary")
    #         cat_cols = df.select_dtypes(include=["object", "category"]).columns
    #         if len(cat_cols) > 0:
    #             for c in cat_cols[:6]:  # лимит, чтобы не перегружать
    #                 st.write(f"**{c}** — top values")
    #                 st.write(df[c].value_counts().head(8))
    #         else:
    #             st.info("No categorical columns detected.")

    #     with tab3:
    #         st.subheader("Missing values")
    #         miss = pd.DataFrame({
    #             "Column": df.columns,
    #             "Missing count": df.isna().sum(),
    #             "Missing %": (df.isna().mean() * 100).round(2).astype(str) + " %"
    #         }).sort_values("Missing count", ascending=False)
    #         miss["Missing % (num)"] = (df.isna().mean() * 100).round(2)
    #         st.dataframe(miss.style.bar(subset="Missing % (num)", color="#ff9800"), use_container_width=True, hide_index=True)

    #         total_miss = df.isna().sum().sum()
    #         st.metric("Total missing cells", total_miss, delta=f"{total_miss / df.size * 100:.1f}% of all cells")

    #     with tab4:
    #         st.subheader("Duplicate rows")
    #         dup_count = df.duplicated().sum()
    #         st.metric("Full row duplicates", dup_count, delta_color="inverse" if dup_count > 0 else "normal")

    #         if dup_count > 0:
    #             if st.button("Show first 5 duplicate rows"):
    #                 st.dataframe(df[df.duplicated(keep=False)].head(10))

if page == "A. Upload & Overview":

    st.title("A. Upload & Data Overview")

    st.markdown(
        "Upload your file in one of the following formats: **CSV**, **Excel (.xlsx)** or **JSON**.\n"
        "For coursework requirements, datasets should ideally have ≥ 1000 rows and ≥ 8 columns."
    )


    separator = st.selectbox(
    "CSV delimiter (separator)",
    options=[", (comma)", "; (semicolon)", "\\t (tab)", "| (pipe)", "space"],
    index=1,  # по умолчанию semicolon — потому что у тебя именно он в файлах
    help="Choose the character that separates columns in your CSV file"
)

# Словарь маппинга: ключ — отображаемый текст в selectbox, значение — реальный символ
sep_map = {
    ", (comma)": ",",
    "; (semicolon)": ";",
    "\\t (tab)": "\t",
    "| (pipe)": "|",
    "space": " "
}

# Получаем реальный разделитель по выбранному тексту
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
                        uploaded_file.seek(0)  # обязательно сбрасываем позицию в начало файла
                        df = pd.read_csv(
                            uploaded_file,
                            encoding=enc,
                            sep=selected_sep,
                            on_bad_lines='skip',  # пропускаем проблемные строки
                            decimal=','           # если в числах запятая вместо точки
                        )
                        st.info(f"Successfully read CSV with encoding: {enc}, separator: '{selected_sep}'")
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

            else:
                st.error("Unsupported file format.")
                st.stop()

        # Сохраняем в session_state
        st.session_state.df_original = df.copy()
        st.session_state.df_working = df.copy()
        st.session_state.transform_log = []
        st.session_state.last_uploaded_name = original_name
        st.session_state.file_uploaded_at = pd.Timestamp.now()

        st.success(f"File successfully loaded: **{original_name}** ({df.shape[0]:,} rows × {df.shape[1]} columns)")

    except Exception as e:
        st.error(f"Failed to read file: {str(e)}")
    # # File uploader — only required formats
    # uploaded_file = st.file_uploader(
    #     "Choose a file",
    #     type=["csv", "xlsx", "json"],
    #     accept_multiple_files=False,
    #     help="Supported formats: .csv, .xlsx, .json"
    # )

    # if uploaded_file is not None:

    #     ext = uploaded_file.name.split('.')[-1].lower()
    #     original_name = uploaded_file.name

    #     try:
    #                 with st.spinner(f"Reading file {original_name} ..."):

    #                     if ext == "csv":
    #                         encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    #                         df = None
    #                         error_msg = ""
    #                         for enc in encodings:
    #                             try:
    #                                 uploaded_file.seek(0)  # Reset file pointer to the beginning
    #                                 df = pd.read_csv(uploaded_file, encoding=enc)
    #                                 st.info(f"Successfully read with encoding: {enc}")
    #                                 break
    #                             except UnicodeDecodeError as e:
    #                                 error_msg = str(e)
    #                                 continue
                    
    #                         if df is None:
    #                             st.error(f"Could not read CSV with any encoding.\nLast error: {error_msg}")
    #                             st.stop()

    #                     elif ext == "xlsx":
    #                         df = pd.read_excel(uploaded_file, engine="openpyxl")

    #                     elif ext == "json":
    #                         try:
    #                             df = pd.read_json(uploaded_file, orient="records")
    #                         except ValueError:
    #                             df = pd.read_json(uploaded_file, orient="columns")

    #                     else:
    #                         st.error("Unsupported file format.")
    #                         st.stop()

    #     # After successful reading — save to session state
    #                 st.session_state.df_original = df.copy()
    #                 st.session_state.df_working = df.copy()
    #                 st.session_state.transform_log = []
    #                 st.session_state.last_uploaded_name = original_name
    #                 st.session_state.file_uploaded_at = pd.Timestamp.now()

    #                 st.success(f"File successfully loaded: **{original_name}**")

    #     except Exception as e:
    #         st.error(f"Failed to read the file.\n\n{str(e)}")
    #         st.info(
    #         "Possible reasons:\n"
    #         "• File is corrupted\n"
    #         "• Wrong encoding (for CSV try UTF-8)\n"
    #         "• JSON is not in tabular format"
    #         )
    #         st.stop()

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
# ────────────────────────────────────────────────
#  Page B — Cleaning & Preparation (начало)
# ────────────────────────────────────────────────
# ================================================
#   Page B — Cleaning & Preparation Studio
# ================================================
elif page == "B. Cleaning & Preparation Studio":

    st.title("B. Cleaning & Preparation Studio")

    if st.session_state.get("df_working") is None:
        st.warning("Please upload a dataset first on the Upload & Overview page.")
        st.stop()

    # Working copy — always use this for modifications
    df = st.session_state.df_working.copy()

    st.subheader("Current dataset shape")
    st.metric("Rows × Columns", f"{df.shape[0]:,} × {df.shape[1]}")

    # Transformation Log (visible always)
    with st.sidebar.expander("Transformation Log", expanded=False):
        if st.session_state.transform_log:
            log_df = pd.DataFrame(st.session_state.transform_log)
            st.dataframe(log_df, use_container_width=True)
        else:
            st.info("No transformations applied yet.")

    # Reset all transformations
    if st.sidebar.button("Reset all transformations", type="primary"):
        st.session_state.df_working = st.session_state.df_original.copy()
        st.session_state.transform_log = []
        st.rerun()

    # ────────────────────────────────────────────────
    #  4.1 Missing Values Handling
    # ────────────────────────────────────────────────
    with st.expander("4.1 Missing Values (Null Handling)", expanded=True):

        miss = pd.DataFrame({
            "Column": df.columns,
            "Missing Count": df.isna().sum(),
            "% Missing": (df.isna().mean() * 100).round(2)
        }).sort_values("Missing Count", ascending=False)

        miss_active = miss[miss["Missing Count"] > 0]
        if miss_active.empty:
            st.success("No missing values detected.")
        else:
            st.dataframe(
                miss_active.style.bar(subset="% Missing", color="#ff9800", vmin=0, vmax=100),
                use_container_width=True,
                hide_index=True
            )

        action = st.radio(
            "Choose action",
            ["No action",
             "Drop rows (selected columns)",
             "Drop columns (> threshold %)",
             "Fill with constant",
             "Fill with statistic (mean/median/mode)",
             "Forward / Backward fill"],
            horizontal=True
        )

        if action != "No action":
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            selected_cols = st.multiselect("Select columns", df.columns.tolist())

            if selected_cols:
                if st.button("Preview before", type="secondary"):
                    st.write("Preview of selected columns:")
                    st.dataframe(df[selected_cols].head(5))

                if action == "Drop rows (selected columns)":
                    if st.button("Apply Drop rows", type="primary"):
                        before = df.shape[0]
                        df = df.dropna(subset=selected_cols)
                        st.session_state.df_working = df
                        st.session_state.transform_log.append({
                            "step": "dropna_rows",
                            "columns": selected_cols,
                            "rows_before": before,
                            "rows_after": df.shape[0],
                            "timestamp": pd.Timestamp.now()
                        })
                        st.rerun()

                # ... остальные действия для 4.1 (fill constant, mean/median/mode, ffill/bfill)
                # можно добавить аналогично, с before/after

    # ────────────────────────────────────────────────
    #  4.2 Duplicates
    # ────────────────────────────────────────────────
    with st.expander("4.2 Duplicates"):

        full_dups = df.duplicated().sum()
        st.metric("Full row duplicates", full_dups)

        subset = st.multiselect("Check duplicates by subset of columns", df.columns.tolist())
        if subset:
            subset_dups = df.duplicated(subset=subset).sum()
            st.metric("Duplicates by selected columns", subset_dups)

            if st.button("Remove duplicates (keep first)"):
                before = df.shape[0]
                df = df.drop_duplicates(keep="first")
                st.session_state.df_working = df
                st.session_state.transform_log.append({
                    "step": "remove_duplicates",
                    "subset": subset if subset else "all",
                    "rows_before": before,
                    "rows_after": df.shape[0]
                })
                st.rerun()

        if full_dups > 0 and st.button("Show duplicate groups"):
            st.dataframe(df[df.duplicated(keep=False)].head(10))

    # ────────────────────────────────────────────────
    #  4.3 Data Types & Parsing
    # ────────────────────────────────────────────────
    with st.expander("4.3 Data Types & Parsing"):

        col_to_change = st.selectbox("Select column to convert", df.columns)
        new_type = st.selectbox("New type", ["numeric", "categorical", "datetime"])

        if new_type == "numeric":
            if st.button("Convert to numeric"):
                try:
                    df[col_to_change] = pd.to_numeric(df[col_to_change].replace({',': '', '$': ''}, regex=True), errors='coerce')
                    st.session_state.df_working = df
                    st.success("Converted to numeric (dirty strings cleaned)")
                except Exception as e:
                    st.error(f"Conversion failed: {e}")

        elif new_type == "datetime":
            fmt = st.text_input("Datetime format (optional)", value="%Y-%m-%d")
            if st.button("Convert to datetime"):
                df[col_to_change] = pd.to_datetime(df[col_to_change], format=fmt if fmt else None, errors='coerce')
                st.session_state.df_working = df
                st.success("Converted to datetime")

        elif new_type == "categorical":
            if st.button("Convert to categorical"):
                df[col_to_change] = df[col_to_change].astype("category")
                st.session_state.df_working = df
                st.success("Converted to categorical")

    # ────────────────────────────────────────────────
    #  4.4 Categorical Tools (basic version)
    # ────────────────────────────────────────────────
    with st.expander("4.4 Categorical Data Tools"):

        cat_col = st.selectbox("Select categorical column", cat_cols)
        if cat_col:
            # Standardization
            if st.button("Trim & lower case"):
                df[cat_col] = df[cat_col].str.strip().str.lower()
                st.session_state.df_working = df
                st.success("Applied trim and lower case")

            # Rare categories to Other
            threshold = st.slider("Min frequency for 'Other'", 1, 100, 10)
            if st.button("Group rare categories"):
                counts = df[cat_col].value_counts()
                rare = counts[counts < threshold].index
                df[cat_col] = df[cat_col].replace(rare, "Other")
                st.session_state.df_working = df
                st.success(f"Grouped {len(rare)} rare categories into 'Other'")

    # ────────────────────────────────────────────────
    #  4.5 Numeric Cleaning (Outliers)
    # ────────────────────────────────────────────────
    with st.expander("4.5 Numeric Cleaning (Outliers)"):

        num_col = st.selectbox("Select numeric column", numeric_cols)
        if num_col:
            Q1 = df[num_col].quantile(0.25)
            Q3 = df[num_col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            outliers_count = ((df[num_col] < lower) | (df[num_col] > upper)).sum()

            st.metric("Outliers (IQR method)", outliers_count)

            outlier_action = st.radio("Outlier action", ["Do nothing", "Cap (winsorize)", "Remove rows"])
            if st.button("Apply"):
                if outlier_action == "Cap (winsorize)":
                    df[num_col] = df[num_col].clip(lower=lower, upper=upper)
                elif outlier_action == "Remove rows":
                    df = df[(df[num_col] >= lower) & (df[num_col] <= upper)]
                st.session_state.df_working = df
                st.success("Outliers handled")
                st.rerun()

    # ────────────────────────────────────────────────
    #  4.6 Normalization / Scaling
    # ────────────────────────────────────────────────
    with st.expander("4.6 Normalization / Scaling"):

        scale_cols = st.multiselect("Columns to scale", numeric_cols)
        method = st.radio("Method", ["Min-Max Scaling", "Z-score Standardization"])
        if st.button("Apply scaling"):
            if method == "Min-Max Scaling":
                df[scale_cols] = (df[scale_cols] - df[scale_cols].min()) / (df[scale_cols].max() - df[scale_cols].min())
            else:
                df[scale_cols] = (df[scale_cols] - df[scale_cols].mean()) / df[scale_cols].std()
            st.session_state.df_working = df
            st.success("Scaling applied")
            st.rerun()

    # ────────────────────────────────────────────────
    #  4.7 Column Operations
    # ────────────────────────────────────────────────
    with st.expander("4.7 Column Operations"):

        # Rename
        rename_col = st.selectbox("Rename column", df.columns)
        new_name = st.text_input("New name")
        if st.button("Rename") and new_name:
            df = df.rename(columns={rename_col: new_name})
            st.session_state.df_working = df
            st.success("Column renamed")

        # Drop column
        drop_col = st.selectbox("Drop column", df.columns)
        if st.button("Drop column"):
            df = df.drop(columns=[drop_col])
            st.session_state.df_working = df
            st.success("Column dropped")

        # New column (simple formula)
        new_col_name = st.text_input("New column name")
        formula = st.text_input("Formula (e.g. colA + colB)")
        if st.button("Create new column") and new_col_name and formula:
            try:
                df[new_col_name] = df.eval(formula)
                st.session_state.df_working = df
                st.success("New column created")
            except Exception as e:
                st.error(f"Formula error: {e}")

    # ────────────────────────────────────────────────
    #  4.8 Data Validation Rules (basic)
    # ────────────────────────────────────────────────
    with st.expander("4.8 Data Validation Rules"):

        st.info("Basic validation: non-null + range check (expand later)")

        check_col = st.selectbox("Column to validate", df.columns)
        min_val = st.number_input("Min allowed", value=float(df[check_col].min()))
        max_val = st.number_input("Max allowed", value=float(df[check_col].max()))

        if st.button("Check violations"):
            violations = df[(df[check_col] < min_val) | (df[check_col] > max_val)]
            st.metric("Violations count", len(violations))
            if not violations.empty:
                st.dataframe(violations.head(10))



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
