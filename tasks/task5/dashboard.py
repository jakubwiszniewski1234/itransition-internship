import streamlit as st
import pandas as pd
import os

def get_google_link():
    sheet_id = os.getenv("GOOGLE_SHEETS_URL").split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Data"
    
def load_dataset():
    return pd.read_csv(get_google_link(), usecols=range(8))

def extract_mines(dataset:pd.DataFrame):
    return dataset.columns.drop([f"Unnamed: {num}" for num in range(8)], errors="ignore").to_list()[1:]

dataset = load_dataset()
mines = extract_mines(dataset)
selected_mine = st.sidebar.selectbox("SHOW INFORMATION ABOUT", mines)

def calculate_mean_daily_output(mine:str):
    return dataset[mine].mean()

def calculate_sd(mine:str):
    return dataset[mine].std()

def calculate_median(mine:str):
    return dataset[mine].median()

def calculate_iqr(mine:str):
    return dataset[mine].quantile(.75) - dataset[mine].quantile(.25)

st.metric("Mean daily output", calculate_mean_daily_output(selected_mine))
st.metric("Standard deviation", calculate_sd(selected_mine))
st.metric("Median", calculate_median(selected_mine))
st.metric("IQR", calculate_iqr(selected_mine))

anomalies_container = st.container(border=True)
anomalies_container.markdown("# DETECTED ANOMALIES")
anomalies_container.markdown("## IQR TEST")
anomalies_container.markdown("Any outputs below $Q_1 - 1.5\\text{IQR}$ or above $Q_3 + 1.5\\text{IQR}$ are considered anomalies by the rule.")

from anomalies_detector import AnomaliesDetector

detector = AnomaliesDetector(dataset[selected_mine])

