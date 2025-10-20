import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Inverter PR Analyzer", layout="wide")

st.title("⚡ Inverter Performance Ratio (PR) Analyzer")
st.write("Easily calculate and visualize inverter-wise PR for up to 80 inverters.")

# Sidebar input
st.sidebar.header("Input Data")

# Upload DC capacity file
dc_file = st.sidebar.file_uploader("Upload inverter DC capacities (CSV or Excel)", type=["csv", "xlsx"])

if dc_file is not None:
    if dc_file.name.endswith(".csv"):
        df_caps = pd.read_csv(dc_file)
    else:
        df_caps = pd.read_excel(dc_file)
else:
    df_caps = pd.DataFrame({
        "inverter": [f"INV{i:02d}" for i in range(1, 81)],
        "dc_capacity_kwp": [3500 for _ in range(80)]  # default capacity
    })

# Editable DC capacity table
st.subheader("Step 1️⃣: Verify or Edit DC Capacities")
edited_caps = st.data_editor(df_caps, num_rows="dynamic")

st.divider()

# Input for GII and Generation
df_work = edited_caps.copy()
df_work["gii_kwh_m2"] = np.nan
df_work["generated_mwh"] = np.nan

st.subheader("Step 2️⃣: Enter GII and Generated Energy Values")
working_df = st.data_editor(df_work, num_rows="dynamic")

# --- Normalize column names to avoid KeyError ---
working_df.columns = (
    working_df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("(kwh/m2)", "kwh_m2", regex=False)
    .str.replace("(mwh)", "mwh", regex=False)
)

editable_cols = ["inverter", "dc_capacity_kwp", "gii_kwh_m2", "generated_mwh"]
working_df = working_df[[col for col in editable_cols if col in working_df.columns]]

if st.button("Calculate PR for all inverters"):
    df = working_df.copy()
    df["pr"] = (df["generated_mwh"] * 1000) / (df["dc_capacity_kwp"] * df["gii_kwh_m2"]) * 100

    st.subheader("Step 3️⃣: Results - Inverter PR Summary")
    st.dataframe(df.style.background_gradient(subset=["pr"], cmap="RdYlGn"))

    st.metric(label="Average PR (%)", value=f"{df['pr'].mean():.2f}")
    st.metric(label="Lowest PR (%)", value=f"{df['pr'].min():.2f}")

    low_performers = df[df['pr'] < df['pr'].mean() - 5]
    if not low_performers.empty:
        st.warning("⚠️ Low-performing inverters:")
        st.dataframe(low_performers[["inverter", "pr"]])

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download PR Report (CSV)", csv, "inverter_pr_report.csv", "text/csv")
