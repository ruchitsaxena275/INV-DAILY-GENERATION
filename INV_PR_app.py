import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Inverter PR Analyzer", layout="wide")

HEADER = "# Inverter Performance Ratio (PR) Analyzer"

st.title("Inverter Performance Ratio (PR) Analyzer")
st.caption("Upload permanent DC capacities for your 80 inverters once, then enter GII and Generation each day. Exports to Excel and shows a heatmap for quick low-performer detection.")

# ----------------- Helper functions -----------------

def make_default_capacities(n=80, default_capacity=4380):
    names = [f"INV{str(i+1).zfill(2)}" for i in range(n)]
    return pd.DataFrame({"inverter": names, "dc_capacity_kWp": [default_capacity]*n})


def load_capacities_from_file(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file)
    # normalize column names
    df = df.rename(columns={c: c.strip().lower().replace(' ', '_') for c in df.columns})
    # required columns: inverter, dc_capacity_kWp (or dc_capacity)
    if 'inverter' not in df.columns:
        st.error("Uploaded capacities file must have an 'inverter' column.")
        return None
    if 'dc_capacity_kwp' not in df.columns and 'dc_capacity' in df.columns:
        df = df.rename(columns={'dc_capacity': 'dc_capacity_kwp'})
    if 'dc_capacity_kwp' not in df.columns:
        st.error("Uploaded capacities file must have a 'dc_capacity_kWp' or 'dc_capacity' column.")
        return None
    df = df[['inverter', 'dc_capacity_kwp']].copy()
    df['inverter'] = df['inverter'].astype(str)
    df['dc_capacity_kwp'] = pd.to_numeric(df['dc_capacity_kwp'], errors='coerce').fillna(0)
    return df


def calculate_pr(df):
    # PR (%) = (Generated (MWh) * 1000) / (DC Capacity (kWp) * GII (kWh/m^2)) * 100
    gen_kwh = df['generated_mwh'].fillna(0) * 1000.0
    dc_kwp = df['dc_capacity_kwp'].replace(0, np.nan)
    gii = df['gii_kwh_m2'].replace(0, np.nan)
    pr = (gen_kwh / (dc_kwp * gii)) * 100.0
    pr = pr.replace([np.inf, -np.inf], np.nan)
    return pr


def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='PR_results')
        writer.save()
    processed_data = output.getvalue()
    return processed_data

# ----------------- Layout: Left panel for config -----------------
with st.sidebar:
    st.header("Configuration")
    st.write("1. Upload / set the permanent DC capacities for your inverters (do this once).\n2. On the main page enter GII and Generation, then calculate PR.")
    cap_upload = st.file_uploader("Upload DC capacities CSV/Excel (columns: inverter, dc_capacity_kWp)", type=['csv', 'xlsx', 'xls'])
    use_default = st.checkbox("Generate default 80 inverters (INV01..INV80) with placeholder DC capacity", value=True)
    default_capacity = st.number_input("Default DC capacity (kWp)", value=4380, step=1)
    save_caps = st.button("Save capacities to local file (capacities.csv)")

# Load capacities
if 'capacities_df' not in st.session_state:
    if cap_upload is not None:
        df_caps = load_capacities_from_file(cap_upload)
        if df_caps is None:
            df_caps = make_default_capacities(80, default_capacity)
    else:
        if use_default:
            df_caps = make_default_capacities(80, default_capacity)
        else:
            df_caps = make_default_capacities(80, default_capacity)
    st.session_state['capacities_df'] = df_caps

if cap_upload is not None and 'capacities_df' in st.session_state:
    # if user uploads, replace
    df_caps = load_capacities_from_file(cap_upload)
    if df_caps is not None:
        st.session_state['capacities_df'] = df_caps

if save_caps:
    df_caps = st.session_state['capacities_df']
    bytes_data = to_excel_bytes(df_caps)
    st.download_button("Download capacities as Excel", data=bytes_data, file_name="capacities.xlsx")

# ----------------- Main area -----------------
st.subheader("Step A — Review / Edit Permanent DC Capacities (one-time)")
st.write("You can edit DC capacities below if needed. These are saved only for this Streamlit session — upload the file again to re-load permanently.")

df_caps = st.session_state['capacities_df'].copy()
# Show editable capacities table
edited_caps = st.experimental_data_editor(df_caps, num_rows="dynamic")
st.session_state['capacities_df'] = edited_caps

st.markdown("---")

st.subheader("Step B — Enter today's GII and Generated Energy (manual or upload)")
st.write("Enter **GII (kWh/m²)** and **Generation (MWh)** for each inverter. You can also upload a CSV/Excel with columns: inverter, gii_kwh_m2, generated_mwh to pre-fill values.")

data_upload = st.file_uploader("Optional: Upload today's data CSV/Excel (inverter, gii_kwh_m2, generated_mwh)", type=['csv', 'xlsx', 'xls'], key='data_upload')

# create working df merging capacities with user inputs
working_df = st.session_state['capacities_df'].copy()
working_df['gii_kwh_m2'] = np.nan
working_df['generated_mwh'] = np.nan

if data_upload is not None:
    try:
        try:
            df_data = pd.read_csv(data_upload)
        except Exception:
            data_upload.seek(0)
            df_data = pd.read_excel(data_upload)
        df_data = df_data.rename(columns={c: c.strip().lower().replace(' ', '_') for c in df_data.columns})
        # accept multiple possible column names
        if 'generated_mwh' not in df_data.columns and 'generation_mwh' in df_data.columns:
            df_data = df_data.rename(columns={'generation_mwh': 'generated_mwh'})
        if 'gii_kwh_m2' not in df_data.columns and 'gii' in df_data.columns:
            df_data = df_data.rename(columns={'gii': 'gii_kwh_m2'})
        df_data = df_data[['inverter', 'gii_kwh_m2', 'generated_mwh']]
        df_data['inverter'] = df_data['inverter'].astype(str)
        # merge
        working_df = working_df.merge(df_data, on='inverter', how='left', suffixes=('', '_y'))
    except Exception as e:
        st.error(f"Failed to read uploaded data: {e}")

# Editable table for GII and Generation
st.write("Edit values directly in the table. Keep units: GII in kWh/m^2, Generation in MWh.")
editable_cols = ['inverter', 'dc_capacity_kwp', 'gii_kwh_m2', 'generated_mwh']
working_df = working_df[editable_cols]
working_df['gii_kwh_m2'] = pd.to_numeric(working_df['gii_kwh_m2'], errors='coerce')
working_df['generated_mwh'] = pd.to_numeric(working_df['generated_mwh'], errors='coerce')

edited_working = st.experimental_data_editor(working_df, num_rows='dynamic')

# Calculation
st.markdown("---")
if st.button("Calculate PR for all inverters"):
    df_results = edited_working.copy()
    df_results['PR_pct'] = calculate_pr(df_results)
    df_results['PR_pct'] = df_results['PR_pct'].round(2)

    # Summary stats
    st.subheader("Results Summary")
    avg_pr = df_results['PR_pct'].mean()
    min_row = df_results.loc[df_results['PR_pct'].idxmin()] if df_results['PR_pct'].notna().any() else None
    max_row = df_results.loc[df_results['PR_pct'].idxmax()] if df_results['PR_pct'].notna().any() else None
    col1, col2, col3 = st.columns(3)
    col1.metric("Average PR (%)", f"{avg_pr:.2f}" if not np.isnan(avg_pr) else "—")
    if min_row is not None:
        col2.metric("Lowest PR (%)", f"{min_row['PR_pct']:.2f}", label=min_row['inverter'])
    else:
        col2.metric("Lowest PR (%)", "—")
    if max_row is not None:
        col3.metric("Highest PR (%)", f"{max_row['PR_pct']:.2f}", label=max_row['inverter'])
    else:
        col3.metric("Highest PR (%)", "—")

    st.markdown("---")
    st.subheader("Inverter PR Table — Heatmap / Conditional Formatting")

    display_df = df_results.copy()
    display_df['dc_capacity_kwp'] = display_df['dc_capacity_kwp'].astype(float)

    # Style: heatmap on PR_pct
    styler = display_df.style.format({
        'dc_capacity_kwp': '{:,.0f}',
        'gii_kwh_m2': '{:.3f}',
        'generated_mwh': '{:.3f}',
        'PR_pct': '{:.2f}'
    })
    # Use a background gradient where lower PR is reddish and higher is greenish
    try:
        styler = styler.background_gradient(subset=['PR_pct'], cmap='RdYlGn')
    except Exception:
        # fallback
        styler = styler

    st.write("*Heatmap legend: lower PR -> warmer color (red), higher PR -> cooler color (green).*)")
    st.dataframe(styler, use_container_width=True)

    # Highlight low performers with a threshold control
    threshold = st.slider("Highlight inverters with PR below (%)", min_value=0.0, max_value=200.0, value=75.0)
    low_perf = df_results[df_results['PR_pct'] < threshold]
    st.write(f"Inverters below {threshold}% PR: {len(low_perf)}")
    if not low_perf.empty:
        st.dataframe(low_perf.sort_values('PR_pct').reset_index(drop=True))

    # Download results
    bytes_xl = to_excel_bytes(df_results)
    st.download_button("Download results as Excel", data=bytes_xl, file_name="inverter_pr_results.xlsx")

    # Small chart
    st.subheader("PR Distribution")
    pr_series = df_results['PR_pct'].dropna()
    if not pr_series.empty:
        st.bar_chart(pr_series)
    else:
        st.info("No PR values to chart. Make sure GII and Generation are entered.")
else:
    st.info("Fill the GII and Generation fields above and click 'Calculate PR for all inverters' to see results and heatmap.")

st.markdown("---")
st.caption("Built for solar plant inverter PR checking. If you want custom features (auto save, historical tracking, or inline notes per inverter), tell me and I will extend the app.")
