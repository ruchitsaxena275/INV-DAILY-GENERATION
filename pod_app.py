import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ----------------- IPs -----------------
ips = [
    '10.22.250.2','10.22.250.3','10.22.250.4','10.22.250.5',
    '10.22.250.13','10.22.250.14','10.22.250.15','10.22.250.16',
    '10.22.250.24','10.22.250.25','10.22.250.26','10.22.250.27',
    '10.22.250.35','10.22.250.36','10.22.250.37','10.22.250.38',
    '10.22.250.46','10.22.250.47','10.22.250.48','10.22.250.49',
    '10.22.250.57','10.22.250.58','10.22.250.59','10.22.250.60',
    '10.22.250.68','10.22.250.69','10.22.250.70','10.22.250.71',
    '10.22.250.79','10.22.250.80','10.22.250.81','10.22.250.82',
    '10.22.250.90','10.22.250.91','10.22.250.92','10.22.250.93',
    '10.22.250.101','10.22.250.102','10.22.250.103','10.22.250.104',
    '10.22.250.112','10.22.250.113','10.22.250.114','10.22.250.115',
    '10.22.250.123','10.22.250.124','10.22.250.125','10.22.250.126',
    '10.22.250.134','10.22.250.135','10.22.250.136','10.22.250.137',
    '10.22.250.145','10.22.250.146','10.22.250.147','10.22.250.148',
    '10.22.250.156','10.22.250.157','10.22.250.158','10.22.250.159',
    '10.22.250.167','10.22.250.168','10.22.250.169','10.22.250.170',
    '10.22.250.178','10.22.250.179','10.22.250.180','10.22.250.181',
    '10.22.250.189','10.22.250.190','10.22.250.191','10.22.250.192',
    '10.22.250.200','10.22.250.201','10.22.250.202','10.22.250.203',
    '10.22.250.211','10.22.250.212','10.22.250.213','10.22.250.214'
]

# ----------------- Prepare DataFrame -----------------
data_list = []
for i in range(20):  # 20 ITCs
    for j in range(4):  # 4 inverters per ITC
        idx = i*4 + j
        data_list.append({
            "ITC": f"ITC-{i+1}",
            "Inverter": f"INV-{j+1}",
            "IP": ips[idx],
            "Export_kW": None
        })

df = pd.DataFrame(data_list)

# ----------------- Scraping Function -----------------
def fetch_export(ip):
    try:
        response = requests.get(f"http://{ip}", timeout=2)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        value = soup.find("label", class_="top_num").text
        return float(value)
    except Exception as e:
        return None

# ----------------- Streamlit UI -----------------
st.title("Solar Inverter Export Dashboard")

if st.button("Refresh Data"):
    for idx, row in df.iterrows():
        df.at[idx, "Export_kW"] = fetch_export(row["IP"])
    st.success("Data Updated!")

# Display Inverter Table
st.subheader("Inverter-wise Export (kW)")
st.dataframe(df)

# ITC Summary
itc_summary = df.groupby("ITC")["Export_kW"].sum().reset_index()
st.subheader("ITC Total Export (kW)")
st.dataframe(itc_summary)
