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

dataset = load_dataset()
mines = extract_mines(dataset)
dataset = filter_unnamed_mines(dataset).dropna()
dataset = add_total_column(dataset)
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

summary_chart = SummaryChart(dataset, selected_mine)
selected_chart_type = summary_chart_container.radio("Chart type", ["line", "bar", "stacked"], horizontal = True)
summary_chart.set_type(selected_chart_type)
selected_polynomial_degree = summary_chart_container.radio("Chart type", range(1, 5), index = 0, horizontal = True)
summary_chart.set_trend(selected_polynomial_degree)

summary_chart.draw()

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle

def generate_pdf(mine, mean_val, std_val, med_val, iqr_val, anomalies_df, chart_type, trend_degree):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    title_style.alignment = 1 
    h2_style = styles['Heading2']
    
    spike_style = ParagraphStyle('Spike', parent=styles['Normal'], borderPadding=6, spaceAfter=4)
    drop_style = ParagraphStyle('Drop', parent=styles['Normal'], borderPadding=6, spaceAfter=4)
    
    elements.append(Paragraph("Weyland-Yutani Corporation", title_style))
    elements.append(Paragraph(f"Mine: <b>{mine}</b>", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("1. Summary Statistics", h2_style))
    table_data = [
        ["Metric", "Value"],
        ["Mean Daily Output", str(mean_val)],
        ["Standard Deviation", str(std_val)],
        ["Median", str(med_val)],
        ["Interquartile Range (IQR)", str(iqr_val)]
    ]
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#334155")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"2. Production Trend ({chart_type.title()}) & Anomalies", h2_style))
    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    
    plot_df = dataset.copy()
    plot_df["Date"] = pd.to_datetime(plot_df["Date"], format = "%d/%m/%Y")
    plot_df = plot_df.sort_values("Date")
    
    if chart_type == "line":
        ax.plot(plot_df["Date"], plot_df[mine], label=mine, linewidth=1.5)
    elif chart_type == "stacked" and selected_mine == "Total":
        bottom = np.zeros(len(plot_df))
        for m in [col for col in plot_df.columns if col not in ["Date", "Total"]]:
            ax.bar(plot_df["Date"], plot_df[m], label=m, bottom=bottom)
            bottom += plot_df[m].fillna(0)
    else:
        ax.bar(plot_df["Date"], plot_df[mine], label=mine)
        
    daily_trend = plot_df.groupby("Date", as_index=False)[mine].sum()
    x_num = np.arange(len(daily_trend))
    coeffs = np.polyfit(x_num, daily_trend[mine], deg=trend_degree)
    trend_y = np.polyval(coeffs, x_num)
    ax.plot(daily_trend["Date"], trend_y, color="orange", linestyle="--", linewidth=2, label=f"Trend (Deg {trend_degree})")
    
    if not anomalies_df.empty:
        print(anomalies_df)
        spikes = anomalies_df[anomalies_df["Type"].str.lower() == "spike"]
        drops = anomalies_df[anomalies_df["Type"].str.lower() == "drop"]
        if not spikes.empty:
            ax.scatter(pd.to_datetime(spikes["Date"], format = "%d/%m/%Y"), spikes[mine], color="red", s=80, label="Spike", zorder=5)
        if not drops.empty:
            ax.scatter(pd.to_datetime(drops["Date"], format = "%d/%m/%Y"), drops[mine], color="orange", s=80, label="Drop", zorder=5)
            
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=20))
    fig.autofmt_xdate(rotation=45)
    
    ax.set_ylabel("Output")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format="png")
    img_buf.seek(0)
    plt.close(fig)
    
    elements.append(RLImage(img_buf, width=doc.width, height=doc.width * 0.45))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("3. Detailed Anomalies Breakdown", h2_style))
    
    if anomalies_df.empty:
        elements.append(Paragraph("No anomalies detected by any test.", styles['Normal']))
    else:
        elements.append(Paragraph("Spike Anomalies (Unexpectedly High)", styles['Heading3']))
        if spikes.empty:
            elements.append(Paragraph("None detected.", styles['Normal']))
        else:
            for _, row in spikes.iterrows():
                d_str = row['Date'].strftime('%d/%m/%Y') if hasattr(row['Date'], 'strftime') else str(row['Date'])
                v = round(row[mine], 2)
                tests = row['Detected By']
                elements.append(Paragraph(f"<b>[SPIKE] {d_str}</b> — Output: {v} | Tests: <i>{tests}</i>", spike_style))
                
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("Drop Anomalies (Unexpectedly Low)", styles['Heading3']))
        if drops.empty:
            elements.append(Paragraph("None detected.", styles['Normal']))
        else:
            for _, row in drops.iterrows():
                d_str = row['Date'].strftime('%d/%m/%Y') if hasattr(row['Date'], 'strftime') else str(row['Date'])
                v = round(row[mine], 2)
                tests = row['Detected By']
                elements.append(Paragraph(f"<b>[DROP] {d_str}</b> — Output: {v} | Tests: <i>{tests}</i>", drop_style))
                
    doc.build(elements)
    buf.seek(0)
    return buf.getvalue()

if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None

all_anomalies_list = []
for df, t_name in zip(
    [iqr_anomalies, zscore_anomalies, ma_anomalies, grubbs_anomalies], 
    ["IQR", "Z-Score", "Moving Average", "Grubbs"]
):
    if df is not None and not df.empty:
        df_copy = df.copy()
        df_copy["Detected By"] = t_name
        all_anomalies_list.append(df_copy)

if all_anomalies_list:
    combined_anomalies = pd.concat(all_anomalies_list)
    combined_anomalies = combined_anomalies.groupby(["Date", "Type", selected_mine], as_index=False).agg({
        "Detected By": lambda x: ", ".join(x.unique())
    })
else:
    combined_anomalies = pd.DataFrame(columns=["Date", "Type", selected_mine, "Detected By"])


col1, col2 = st.columns([1, 3])

with col1:
    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Compiling PDF Layout..."):
            st.session_state.pdf_data = generate_pdf(
                selected_mine, 
                calculate_mean_daily_output(selected_mine),
                calculate_sd(selected_mine),
                calculate_median(selected_mine),
                calculate_iqr(selected_mine),
                combined_anomalies,
                selected_chart_type,
                selected_polynomial_degree
            )

with col2:
    if st.session_state.pdf_data:
        st.download_button(
            label="Download PDF Report",
            data=st.session_state.pdf_data,
            file_name=f"Weyland_Yutani_{selected_mine}_Report.pdf",
            mime="application/pdf",     
        )