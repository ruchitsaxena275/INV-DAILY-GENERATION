# save as app.py
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd

# ----------------- CONFIG -----------------
# List of inverter IPs
IPS = [
    "10.22.250.2", "10.22.250.3", "10.22.250.4", "10.22.250.5",
    "10.22.250.6", "10.22.250.7", "10.22.250.8", "10.22.250.9",
    "10.22.250.10", "10.22.250.11", "10.22.250.12", "10.22.250.13",
    "10.22.250.14", "10.22.250.15", "10.22.250.16", "10.22.250.17",
    "10.22.250.18", "10.22.250.19", "10.22.250.20", "10.22.250.21",
    "10.22.250.22", "10.22.250.23", "10.22.250.24", "10.22.250.25",
    "10.22.250.26", "10.22.250.27", "10.22.250.28", "10.22.250.29",
    "10.22.250.30", "10.22.250.31", "10.22.250.32", "10.22.250.33",
    "10.22.250.34", "10.22.250.35", "10.22.250.36", "10.22.250.37",
    "10.22.250.38", "10.22.250.39", "10.22.250.40", "10.22.250.41",
    "10.22.250.42", "10.22.250.43", "10.22.250.44", "10.22.250.45",
    "10.22.250.46", "10.22.250.47", "10.22.250.48", "10.22.250.49",
    "10.22.250.50", "10.22.250.51", "10.22.250.52", "10.22.250.53",
    "10.22.250.54", "10.22.250.55", "10.22.250.56", "10.22.250.57",
    "10.22.250.58", "10.22.250.59", "10.22.250.60", "10.22.250.61",
    "10.22.250.62", "10.22.250.63", "10.22.250.64", "10.22.250.65",
    "10.22.250.66", "10.22.250.67", "10.22.250.68", "10.22.250.69",
    "10.22.250.70", "10.22.250.71", "10.22.250.72", "10.22.250.73",
    "10.22.250.74", "10.22.250.75", "10.22.250.76", "10.22.250.77",
    "10.22.250.78", "10.22.250.79", "10.22.250.80", "10.22.250.81"
]

# ----------------- FUNCTION TO FETCH DATA -----------------
def get_inverter_yield(ip):
    """Open inverter page with Selenium and capture the daily yield"""
    options = Options()
    options.headless = True  # runs in background
    driver = webdriver.Chrome(options=options)  # make sure chromedriver is installed
    try:
        driver.get(f"http://{ip}")
        # Adjust selector if your label class is different
        element = driver.find_element(By.CSS_SELECTOR, "label.top_num")
        value = element.text
        driver.quit()
        return value
    except:
        driver.quit()
        return "Error"

# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="Inverter Dashboard", layout="wide")
st.title("Solar Plant Inverter Daily Yield Dashboard")

# Manual inverter selection
selected_ip = st.selectbox("Select Inverter IP:", IPS)

if st.button(f"Fetch Data for {selected_ip}"):
    with st.spinner(f"Fetching data from {selected_ip}..."):
        daily_yield = get_inverter_yield(selected_ip)
        st.success(f"Daily Yield for {selected_ip}: {daily_yield}")

# Optional: store fetched data in a table
if 'data' not in st.session_state:
    st.session_state.data = []

if st.button("Add to Table"):
    st.session_state.data.append({"IP": selected_ip, "DailyYield": daily_yield})
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df)
    df.to_excel("manual_yield.xlsx", index=False)
    st.info("Excel saved as manual_yield.xlsx")
