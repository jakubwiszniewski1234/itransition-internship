import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def get_google_link():
    sheet_id = os.getenv("GOOGLE_SHEETS_URL").split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Data"

def load_dataset():
    return pd.read_csv(get_google_link(), usecols=range(8))

def extract_columns(dataset:pd.DataFrame):
    return dataset.columns.drop([f"Unnamed: {num}" for num in range(8)], errors="ignore").to_list()

def extract_mines(dataset:pd.DataFrame):
    return extract_columns(dataset)[1:]

def filter_unnamed_mines(dataset:pd.DataFrame):
    return dataset[extract_columns(dataset)]

def add_total_column(dataset:pd.DataFrame):
    dataset["Total"] = dataset[extract_mines(dataset)].sum(axis = 1)
    return dataset

def format_date(dataset:pd.DataFrame):
    dataset["Date"] = pd.to_datetime(dataset["Date"], format="%d/%m/%Y")
    return dataset

dataset = load_dataset()
mines = extract_mines(dataset)
dataset = filter_unnamed_mines(dataset).dropna()
dataset = format_date(add_total_column(dataset))
selected_mine = st.sidebar.selectbox("SHOW INFORMATION ABOUT", ["Total"] + mines)

def rounded(number:float):
    return round(number, 2)

def calculate_mean_daily_output(mine:str):
    return rounded(dataset[mine].mean())

def calculate_sd(mine:str):
    return rounded(dataset[mine].std())

def calculate_median(mine:str):
    return rounded(dataset[mine].median())

def calculate_iqr(mine:str):
    return rounded(dataset[mine].quantile(.75) - dataset[mine].quantile(.25))

metrics = st.container(border = True, horizontal = True)

metrics.metric("Mean daily output", calculate_mean_daily_output(selected_mine))
metrics.metric("Standard deviation", calculate_sd(selected_mine))
metrics.metric("Median", calculate_median(selected_mine))
metrics.metric("IQR", calculate_iqr(selected_mine))

anomalies_container = st.container(border=True)
anomalies_container.markdown("# DETECTED ANOMALIES")
anomalies_container.markdown("## IQR TEST")
anomalies_container.markdown("Any outputs below $Q_1 - k\\times\\text{IQR}$ or above $Q_3 + k\\times\\text{IQR}$, where $k$ is a narrowing factor, are considered anomalies by the rule. By deafult rule definition, $k=1.5$.")

from anomalies_detector import AnomaliesDetector

detector = AnomaliesDetector(dataset, selected_mine)

detector.iqr_factor = anomalies_container.slider("IQR Multiplication factor", .5, 3., step = 0.5, value=1.5)
iqr_anomalies = detector.find_anomalies(by="iqr")
anomalies_container.write(iqr_anomalies)

anomalies_container.markdown("## z-score")
anomalies_container.markdown("Any outputs outside the $(\\mu - 3\\sigma, \\mu + 3\\sigma)$ are considered anomalies")
detector.zscore_threshold = anomalies_container.slider("$\\sigma$ threshold", 1., 3., step = 0.5, value=2.)
zscore_anomalies = detector.find_anomalies(by="zscore")
anomalies_container.write(zscore_anomalies)

anomalies_container.markdown("## Distance from MA")
anomalies_container.markdown("...")
detector.ma_window = anomalies_container.selectbox("Moving Average window", [1, 3, 7, 14], index = 2)
detector.ma_percentage = anomalies_container.slider("Distance percentage", 0.05, 1., step = 0.05, value = 0.6)
ma_anomalies = detector.find_anomalies(by="ma")
anomalies_container.write(ma_anomalies)

anomalies_container.markdown("## Grubbs test")
anomalies_container.markdown("...")
detector.grubbs_alpha = anomalies_container.slider("Confidence level $\\alpha$", .05, 1., step = 0.05)
grubbs_anomalies = detector.find_anomalies(by="grubbs")
anomalies_container.write(grubbs_anomalies)


from summary_chart import SummaryChart
summary_chart_container = st.container(border = True)

summary_chart = SummaryChart(dataset, selected_mine, anomalies = detector.find_anomalies(by="all"))
selected_chart_type = summary_chart_container.radio("Chart type", ["line", "bar", "stacked"], horizontal = True)
summary_chart.set_type(selected_chart_type)
selected_polynomial_degree = summary_chart_container.radio("Chart type", range(1, 5), index = 0, horizontal = True)
summary_chart.set_trend(selected_polynomial_degree)

summary_chart.draw()

from pdf_generator import PDFGenerator

pdf_generator = PDFGenerator(selected_mine, calculate_mean_daily_output(selected_mine), calculate_sd(selected_mine), calculate_median(selected_mine), calculate_iqr(selected_mine), detector.find_anomalies(by="all"), selected_chart_type, selected_polynomial_degree, dataset)

buttons_container = st.container()
buttons_col1, buttons_col2 = buttons_container.columns([1, 1])

if buttons_col1.button("Generate Report", use_container_width=True, type="tertiary"):
    with buttons_col2.spinner("Generating report..."):
        pdf_generator = PDFGenerator(
            selected_mine, 
            calculate_mean_daily_output(selected_mine), 
            calculate_sd(selected_mine), 
            calculate_median(selected_mine), 
            calculate_iqr(selected_mine), 
            detector.find_anomalies(by="all"), 
            selected_chart_type, 
            selected_polynomial_degree, 
            dataset
        )
    
        st.session_state.pdf_data = pdf_generator.generate()
        st.dialog("PDF generated successfully!")

if 'pdf_data' in st.session_state:
    buttons_col2.download_button(
        label="Download PDF",
        data=st.session_state.pdf_data,
        file_name=f"{selected_mine}_production_report.pdf",
        mime="application/pdf", 
        use_container_width=True, 
        type="primary"
    )