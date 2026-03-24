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
       
                # ==================== УЛУЧШЕННАЯ ФУНКЦИЯ ПРЕВЬЮ ====================
        def show_preview(before_df, after_df, action_name, column=None):
            st.markdown(f"### 📊 Preview: {action_name}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Before**")
                st.metric("Rows", before_df.shape[0])
                if column and column in before_df.columns:
                    st.dataframe(before_df[[column]].head(10), use_container_width=True)
                else:
                    st.dataframe(before_df.head(10), use_container_width=True)
            
            with col2:
                st.markdown("**After**")
                st.metric("Rows", after_df.shape[0])
                if column and column in after_df.columns:
                    st.dataframe(after_df[[column]].head(10), use_container_width=True)
                else:
                    st.dataframe(after_df.head(10), use_container_width=True)
            
            st.divider()
        # ===================================================================
        
        
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
        with st.expander("4.1 Missing Values (Null Handling)", expanded=True):

            # Summary
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
                "Choose missing values action",
                [
                    "Do nothing",
                    "Drop rows with missing in selected columns",
                    "Drop columns with > X% missing",
                    "Fill with constant value",
                    "Fill with statistic (mean / median / mode)",
                    "Forward fill / Backward fill"
                ],
                index=0
            )

            if action != "Do nothing":
                numeric_cols = df.select_dtypes(include="number").columns.tolist()
                cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        
                if action == "Fill with statistic (mean / median / mode)":
                    method = st.selectbox("Statistic method", ["mean", "median", "mode"])
                    if method in ["mean", "median"]:
                        available_cols = numeric_cols
                        help_text = "Mean и Median работают только с числовыми столбцами (int/float)"
                    else:
                        available_cols = df.columns.tolist()
                        help_text = "Mode работает со всеми типами столбцов"
                elif action in ["Fill with constant value", "Forward fill / Backward fill"]:
                    available_cols = df.columns.tolist()
                    help_text = "Подходит для всех типов столбцов"
                else:
                    available_cols = df.columns.tolist()
                    help_text = "Подходит для всех типов столбцов"

                selected_cols = st.multiselect(
                    "Select columns to apply action to",
                    options=available_cols,
                    default=[],
                    help=help_text
                )

                if selected_cols:
                    before_df = df.copy()

                if selected_cols:
                    before_df = df.copy()  # для preview

                    if action == "Drop rows with missing in selected columns":
                        if st.button("Apply: Drop rows", type="primary"):
                            df = df.dropna(subset=selected_cols)
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "dropna_rows",
                                "columns": selected_cols,
                                "rows_before": before_df.shape[0],
                                "rows_after": df.shape[0],
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            show_preview(before_df, df, "Drop rows")
                            st.success(f"Dropped {before_df.shape[0] - df.shape[0]} rows")
                            st.rerun()

                    elif action == "Drop columns with > X% missing":
                        threshold = st.slider("Threshold %", 0, 100, 50, 5)
                        if st.button("Apply: Drop columns", type="primary"):
                            to_drop = miss[miss["% Missing"] > threshold]["Column"].tolist()
                            df = df.drop(columns=to_drop)
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "drop_columns",
                                "threshold": threshold,
                                "dropped": to_drop,
                                "cols_before": before_df.shape[1],
                                "cols_after": df.shape[1]
                            })
                            show_preview(before_df, df, "Drop columns")
                            st.success(f"Dropped {len(to_drop)} columns")
                            st.rerun()



                    elif action == "Forward fill / Backward fill":
                        direction = st.radio("Direction", ["ffill (forward)", "bfill (backward)"])
                        
                        if st.button("Apply: fill ({direction})", type="primary"):
                            filled_total = 0
                            
                            for col in selected_cols:
                                before = df[col].isna().sum()
                                if before == 0:
                                    continue
                                    
                                if direction == "ffill (forward)":
                                    df[col] = df[col].ffill()
                                else:
                                    df[col] = df[col].bfill()
                                    
                                after = df[col].isna().sum()
                                filled = before - after
                                filled_total += filled
                                
                                st.write(f"{col}: заполнено {filled} из {before} пропусков")
                            
                            st.session_state.df_working = df.copy()
                            
                            st.session_state.transform_log.append({
                                "step": direction.split()[0],  # "ffill" или "bfill"
                                "columns": selected_cols.copy(),
                                "filled_count": filled_total,
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            
                            show_preview(before_df, df, f"{direction}")
                            st.success(f"Заполнено {filled_total} значений методом {direction}")
                            st.rerun()

                    
                    elif action == "Fill with constant value":
                        constant = st.text_input("Constant value", "0")
                        if st.button("Apply: Fill constant", type="primary"):
                            df[selected_cols] = df[selected_cols].fillna(constant)
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "fill_constant",
                                "value": constant,
                                "columns": selected_cols,
                                "filled": before_df[selected_cols].isna().sum().sum()
                            })
                            show_preview(before_df, df, "Fill constant")
                            st.success("Filled with constant")
                            st.rerun()


                    

                     
        
                   
                    
                    elif action == "Fill with statistic (mean / median / mode)":
                        method = st.selectbox("Statistic", ["mean", "median", "mode"])
                        if st.button(f"Apply: Fill {method}", type="primary"):
                            filled_count = 0
                            for col in selected_cols:
                                if method == "mode":
                                    val = df[col].mode()[0] if not df[col].mode().empty else None
                                elif method == "mean":
                                    val = df[col].mean()
                                else:
                                    val = df[col].median()
                                if val is not None:
                                    before_missing = df[col].isna().sum()
                                    df[col] = df[col].fillna(val)
                                    filled_count += before_missing
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": f"fill_{method}",
                                "columns": selected_cols,
                                "filled_count": filled_count,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            show_preview(before_df, df, f"Fill {method}")
                            st.success(f"Filled {filled_count} values")
                            st.rerun()


                



               # 4.2 Duplicates
        with st.expander("4.2 Duplicates", expanded=False):
            st.subheader("Duplicate Detection & Removal")

            full_dups = df.duplicated().sum()
            st.metric("Full row duplicates (completely identical rows)", full_dups)

            st.markdown("**Detect and remove duplicates by selected columns**")

            subset_cols = st.multiselect(
                "Select columns to check for duplicates",
                options=df.columns.tolist(),
                default=[],
                help="Choose one or more columns. The more columns — the fewer duplicates will be found."
            )

            if subset_cols:
                subset_dups = df.duplicated(subset=subset_cols).sum()
                st.metric("Duplicates found using selected columns", subset_dups)

                if subset_dups > 0:
                    before_df = df.copy()
                    keep = st.radio("Which duplicate to keep?", ["first", "last"], index=0, key="keep_radio")

                    if len(subset_cols) == 1:
                        st.warning("⚠️ Warning: You selected only 1 column. This may remove a large portion of your data.")

                    if st.button(f"Remove duplicates (keep {keep})", type="primary", key="remove_dups_button"):
                        df = df.drop_duplicates(subset=subset_cols, keep=keep)
                        removed = before_df.shape[0] - df.shape[0]

                        st.session_state.df_working = df
                        st.session_state.transform_log.append({
                            "step": "remove_duplicates",
                            "subset": subset_cols,
                            "keep": keep,
                            "rows_before": before_df.shape[0],
                            "rows_after": df.shape[0],
                            "duplicates_removed": removed,
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })

                        show_preview(before_df, df, "Remove duplicates")
                        st.success(f"Removed {removed} duplicate rows. New shape: {df.shape[0]} rows")
                        st.rerun()

            # Show duplicate groups — с уникальным ключом!
            if st.button("Show duplicate groups (first 10 rows)", key="show_dups_button"):
                if subset_cols:
                    dups_df = df[df.duplicated(subset=subset_cols, keep=False)].head(10)
                else:
                    dups_df = df[df.duplicated(keep=False)].head(10)
                
                if not dups_df.empty:
                    st.dataframe(dups_df, use_container_width=True)
                else:
                    st.info("No duplicates found with current selection.")

            st.caption("💡 Tip: Selecting more columns = fewer duplicates will be removed.")

       
        
        # 4.3 Data Types & Parsing
        with st.expander("4.3 Data Types & Parsing", expanded=False):
            st.subheader("Change column type")

            # Сначала выбираем желаемый тип
            desired_type = st.selectbox(
                "Desired type",
                ["numeric", "categorical", "datetime"],
                index=0
            )

            # Динамически фильтруем доступные колонки в зависимости от типа
            if desired_type == "numeric":
                available_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
                help_text = "Только текстовые столбцы (object/category) — будут очищены от $, запятых и пробелов"
            elif desired_type == "categorical":
                available_cols = df.columns.tolist()
                help_text = "Любой столбец → преобразуется в category (экономит память)"
            elif desired_type == "datetime":
                available_cols = df.columns.tolist()
                help_text = "Любой столбец → пытаемся распарсить как дату"

            col_to_change = st.selectbox(
                "Select column to convert",
                options=available_cols,
                index=0 if available_cols else None,
                help=help_text
            )

            # Если колонка выбрана — показываем действия
            if col_to_change:
                if desired_type == "numeric":
                    if st.button("Convert to numeric (clean dirty strings)", type="primary"):
                        try:
                            # Очистка типичных "грязных" символов
                            cleaned = df[col_to_change].astype(str).replace(
                                r'[\$,€£¥ ]', '', regex=True  # $, €, £, ¥, пробелы
                            ).str.replace(',', '.', regex=False)  # запятая → точка для десятичных

                            df[col_to_change] = pd.to_numeric(cleaned, errors='coerce')
                            invalid_count = df[col_to_change].isna().sum()

                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "convert_to_numeric",
                                "column": col_to_change,
                                "invalid_values": invalid_count,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })

                            st.success(f"Converted to numeric. Invalid values → NaN: {invalid_count}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Conversion failed: {str(e)}")

                elif desired_type == "categorical":
                    if st.button("Convert to categorical", type="primary"):
                        try:
                            df[col_to_change] = df[col_to_change].astype("category")
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "convert_to_categorical",
                                "column": col_to_change,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            st.success(f"Converted '{col_to_change}' to categorical")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Conversion failed: {str(e)}")

                elif desired_type == "datetime":
                    date_format = st.text_input(
                        "Datetime format (optional, e.g. %Y-%m-%d or %d/%m/%Y)",
                        value="",
                        help="Оставьте пустым для автоматического распознавания"
                    )
                    if st.button("Convert to datetime", type="primary"):
                        try:
                            df[col_to_change] = pd.to_datetime(
                                df[col_to_change],
                                format=date_format if date_format else None,
                                errors='coerce'
                            )
                            invalid_count = df[col_to_change].isna().sum()
                            st.session_state.df_working = df
                            st.session_state.transform_log.append({
                                "step": "convert_to_datetime",
                                "column": col_to_change,
                                "format_used": date_format or "auto",
                                "invalid_dates": invalid_count,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            st.success(f"Converted to datetime. Invalid dates → NaN: {invalid_count}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Conversion failed: {str(e)}")




               # 4.4 Categorical Data Tools
                # 4.4 Categorical Data Tools
        with st.expander("4.4 Categorical Data Tools", expanded=False):
            st.subheader("Categorical Data Tools")

            # Общий выбор колонки для большинства операций
            cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
            if not cat_cols:
                st.warning("No categorical columns found in the dataset.")
                st.stop()

            selected_cat_col = st.selectbox(
                "Select categorical column (for Standardization, Rare grouping, One-hot)",
                options=cat_cols,
                key="main_cat_col"
            )

            st.markdown(f"**Current selected column:** `{selected_cat_col}`")

            # 1. Standardization
            st.markdown("**1. Standardization** (trim, lower, title case)")
            std_action = st.radio("Choose action", ["Trim whitespace", "Lower case", "Title case"], horizontal=True)

            if st.button("Apply standardization", type="primary"):
                before_df = df.copy()
                if std_action == "Trim whitespace":
                    df[selected_cat_col] = df[selected_cat_col].str.strip()
                elif std_action == "Lower case":
                    df[selected_cat_col] = df[selected_cat_col].str.lower()
                elif std_action == "Title case":
                    df[selected_cat_col] = df[selected_cat_col].str.title()

                st.session_state.df_working = df
                st.session_state.transform_log.append({
                    "step": "standardize_categorical",
                    "column": selected_cat_col,
                    "action": std_action,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                show_preview(before_df, df, "Standardization")
                st.success(f"Applied {std_action} to '{selected_cat_col}'")
                st.rerun()

            # 2. Rare category grouping
            st.markdown("**2. Group rare categories into 'Other'**")
            min_freq = st.slider("Minimum frequency (below this → 'Other')", 1, 100, 10)
            if st.button("Group rare categories into 'Other'", type="primary"):
                before_df = df.copy()
                counts = df[selected_cat_col].value_counts()
                rare = counts[counts < min_freq].index
                df[selected_cat_col] = df[selected_cat_col].replace(rare, "Other")

                st.session_state.df_working = df
                st.session_state.transform_log.append({
                    "step": "group_rare_categories",
                    "column": selected_cat_col,
                    "min_freq": min_freq,
                    "rare_categories": len(rare),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                show_preview(before_df, df, "Rare grouping")
                st.success(f"Grouped {len(rare)} rare categories into 'Other'")
                st.rerun()

            # 3. Value Mapping — отдельный выбор колонки
            st.markdown("**3. Value mapping / replacement**")
            mapping_col = st.selectbox(
                "Select column for mapping",
                options=cat_cols,
                key="mapping_col_select"
            )

            mapping_input = st.text_area(
                "Enter mapping (old_value:new_value, one per line)",
                value="old_value1:new_value1\nold_value2:new_value2",
                height=100
            )

            if mapping_input and st.button("Apply mapping", type="primary"):
                before_df = df.copy()
                mapping_dict = {}
                for line in mapping_input.strip().split("\n"):
                    if ":" in line:
                        old, new = line.split(":", 1)
                        mapping_dict[old.strip()] = new.strip()

                df[mapping_col] = df[mapping_col].replace(mapping_dict)
                changed = (before_df[mapping_col] != df[mapping_col]).sum()

                st.session_state.df_working = df
                st.session_state.transform_log.append({
                    "step": "value_mapping",
                    "column": mapping_col,
                    "mapping": mapping_dict,
                    "changed_values": changed,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                show_preview(before_df, df, "Value mapping")
                st.success(f"Applied mapping to '{mapping_col}'. Changed {changed} values.")
                st.rerun()

           
           # 4. One-hot encoding
                            
            st.markdown("**4. One-hot encoding (optional)**")
            st.warning("⚠️ This will permanently delete the original column and add multiple new columns.")

            if st.button("One-hot encode selected column", type="primary"):
                before_df = df.copy()
                one_hot = pd.get_dummies(df[selected_cat_col], prefix=selected_cat_col, prefix_sep="_")
                df = pd.concat([df.drop(columns=[selected_cat_col]), one_hot], axis=1)

                st.session_state.df_working = df
                st.session_state.transform_log.append({
                    "step": "one_hot_encoding",
                    "column": selected_cat_col,
                    "new_columns": list(one_hot.columns),
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                show_preview(before_df, df, "One-hot encoding")
                st.success(f"One-hot encoded '{selected_cat_col}'. Original column deleted. Added {len(one_hot.columns)} new columns.")
                st.rerun()




        # 4.5 Numeric Cleaning - Outlier Handling
                # 4.5 Numeric Cleaning (Outliers)
        with st.expander("4.5 Numeric Cleaning (Outliers)", expanded=False):
            st.subheader("Outlier Detection & Handling")

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

            if not numeric_cols:
                st.warning("No numeric columns found.")
            else:
                col_for_outliers = st.selectbox("Select numeric column", numeric_cols)

                method = st.radio("Outlier detection method", ["IQR Method (recommended)", "Z-Score"], horizontal=True)

                if method == "IQR Method (recommended)":
                    q1 = df[col_for_outliers].quantile(0.25)
                    q3 = df[col_for_outliers].quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outliers_count = ((df[col_for_outliers] < lower) | (df[col_for_outliers] > upper)).sum()
                    st.metric("Outliers detected (IQR)", outliers_count)
                else:
                    mean = df[col_for_outliers].mean()
                    std = df[col_for_outliers].std()
                    z = np.abs((df[col_for_outliers] - mean) / std)
                    outliers_count = (z > 3).sum()
                    st.metric("Outliers detected (Z-Score > 3)", outliers_count)

                action = st.radio("Action for outliers", 
                                ["Do nothing", "Cap (Winsorize) at bounds", "Remove outlier rows"], 
                                horizontal=True)

                if action != "Do nothing" and st.button("Apply outlier handling", type="primary"):
                    before_df = df.copy()

                    if action == "Cap (Winsorize) at bounds":
                        if method == "IQR Method (recommended)":
                            df[col_for_outliers] = df[col_for_outliers].clip(lower=lower, upper=upper)
                        else:
                            df[col_for_outliers] = df[col_for_outliers].clip(lower=mean-3*std, upper=mean+3*std)
                    else:  # Remove
                        if method == "IQR Method (recommended)":
                            df = df[(df[col_for_outliers] >= lower) & (df[col_for_outliers] <= upper)]
                        else:
                            df = df[z <= 3]

                    st.session_state.df_working = df

                    st.session_state.transform_log.append({
                        "step": "outlier_handling",
                        "column": col_for_outliers,
                        "method": method,
                        "action": action,
                        "outliers_affected": outliers_count,
                        "rows_before": before_df.shape[0],
                        "rows_after": df.shape[0],
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })

                    # Показываем превью
                    show_preview(before_df, df, f"Outlier Handling - {col_for_outliers}", highlight_col=col_for_outliers)

                    st.success(f"Operation completed on '{col_for_outliers}'")
                    st.rerun()

        # 4.6 Normalization / Scaling
        with st.expander("4.6 Normalization / Scaling", expanded=False):
            st.subheader("Normalization and Scaling")

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

            if not numeric_cols:
                st.warning("No numeric columns available for scaling.")
            else:
                scaling_method = st.radio("Scaling method", ["Min-Max Scaling", "Z-Score Standardization"], horizontal=True)

                cols_to_scale = st.multiselect(
                    "Select numeric columns to scale",
                    options=numeric_cols,
                    default=numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols
                )

                if cols_to_scale and st.button("Apply scaling", type="primary"):
                    before_df = df.copy()

                    if scaling_method == "Min-Max Scaling":
                        from sklearn.preprocessing import MinMaxScaler
                        scaler = MinMaxScaler()
                        df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
                        st.success(f"Min-Max scaling applied to {len(cols_to_scale)} columns")

                    else:  # Z-Score Standardization
                        from sklearn.preprocessing import StandardScaler
                        scaler = StandardScaler()
                        df[cols_to_scale] = scaler.fit_transform(df[cols_to_scale])
                        st.success(f"Z-Score standardization applied to {len(cols_to_scale)} columns")

                    st.session_state.df_working = df
                    st.session_state.transform_log.append({
                        "step": "scaling",
                        "method": scaling_method,
                        "columns": cols_to_scale,
                        "rows_before": before_df.shape[0],
                        "rows_after": df.shape[0],
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    show_preview(before_df, df, f"{scaling_method}")
                    st.rerun()

                st.caption("Note: Scaling is applied only to selected numeric columns. Original values can be seen in Before/After preview.")





# # Заглушки для остальных страниц
# elif page == "C. Visualization Builder":
#     st.title("Visualization Builder")
#     st.info("Coming soon...")

elif page == "D. Export & Report":
    st.title("D. Export & Report")

    if st.session_state.get("df_working") is None:
        st.warning("No dataset to export. Please upload and clean data first on pages A and B.")
    else:
        df_final = st.session_state.df_working

        st.subheader("Final dataset ready for export")
        st.metric("Rows × Columns", f"{df_final.shape[0]:,} × {df_final.shape[1]}")

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Export as CSV")
            csv = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="cleaned_dataset.csv",
                mime="text/csv"
            )

        with col2:
            st.subheader("Export as Excel")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Cleaned_Data')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=excel_data,
                file_name="cleaned_dataset.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col3:
            st.subheader("Export as JSON")
            json_str = df_final.to_json(orient="records", date_format="iso")
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name="cleaned_dataset.json",
                mime="application/json"
            )

        st.divider()

        # Transformation Report
        st.subheader("Transformation Report")
        if st.session_state.transform_log:
            log_df = pd.DataFrame(st.session_state.transform_log)
            st.dataframe(log_df, use_container_width=True)

            log_csv = log_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Transformation Log (CSV)",
                data=log_csv,
                file_name="transformation_log.csv",
                mime="text/csv"
            )
        else:
            st.info("No transformations performed yet.")

        st.caption("All exports include the final cleaned version of your dataset.")



