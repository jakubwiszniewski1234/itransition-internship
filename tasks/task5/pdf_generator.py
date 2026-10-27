import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class PDFGenerator:
    def __init__(self, mine, mean_val, std_val, med_val, iqr_val, anomalies_df, chart_type, trend_degree, dataset):
        self._store_inputs(mine, mean_val, std_val, med_val, iqr_val, anomalies_df, chart_type, trend_degree, dataset)
        self._init_document_state()
        self._init_styles()
        self._extract_anomalies()

    def _store_inputs(self, mine, mean, std, med, iqr, anomalies, chart_type, trend_deg, dataset):
        self.mine, self.mean_val, self.std_val, self.med_val = mine, mean, std, med
        self.iqr_val, self.anomalies_df = iqr, anomalies
        self.chart_type, self.trend_degree = chart_type, trend_deg
        self.dataset= dataset

    def _init_document_state(self):
        self.buf = io.BytesIO()
        self.doc = SimpleDocTemplate(self.buf, pagesize=A4, rightMargin=35, leftMargin=35, topMargin=35, bottomMargin=35)
        self.elements = []

    def _init_styles(self):
        self.styles = getSampleStyleSheet()
        self.title_style = self.styles['Heading1']
        self.title_style.alignment = 1 
        self.h2_style = self.styles['Heading2']
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.spike_style = ParagraphStyle('Spike', parent=self.styles['Normal'], borderPadding=6, spaceAfter=4)
        self.drop_style = ParagraphStyle('Drop', parent=self.styles['Normal'], borderPadding=6, spaceAfter=4)

    def generate(self):
        self._add_title_section()
        self._add_summary_stats()
        self._add_production_trend()
        self._add_anomalies_breakdown()
        return self._build_and_return()

    def _build_and_return(self):
        self.doc.build(self.elements)
        self.buf.seek(0)
        return self.buf.getvalue()

    def _add_title_section(self):
        self.elements.append(Paragraph("Weyland-Yutani Corporation", self.title_style))
        self.elements.append(Paragraph(f"Mine: <b>{self.mine}</b>", self.styles['Normal']))
        self.elements.append(Spacer(1, 0.2 * inch))

    def _add_summary_stats(self):
        self.elements.append(Paragraph("1. Summary Statistics", self.h2_style))
        self.elements.append(self._create_summary_table())
        self.elements.append(Spacer(1, 0.2 * inch))

    def _create_summary_table(self):
        t = Table(self._get_table_data())
        t.setStyle(self._get_table_style())
        return t

    def _get_table_data(self):
        return [["Metric", "Value"],
                ["Mean Daily Output", str(self.mean_val)],
                ["Standard Deviation", str(self.std_val)],
                ["Median", str(self.med_val)],
                ["Interquartile Range (IQR)", str(self.iqr_val)]]

    def _get_table_style(self):
        return TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ])

    def _add_production_trend(self):
        self.elements.append(Paragraph(f"2. Production output with trend ({self.chart_type.title()}) and outliers highlighted", self.h2_style))
        self._prepare_plot_dataframe()
        img_buf = self._generate_plot_image()
        self._add_image_to_elements(img_buf)

    def _prepare_plot_dataframe(self):
        self.plot_df = self.dataset.copy()
        self.plot_df["Date"] = pd.to_datetime(self.plot_df["Date"], format="%d/%m/%Y")
        self.plot_df = self.plot_df.sort_values("Date")

    def _generate_plot_image(self):
        fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
        self._draw_chart_elements(ax)
        self._format_axes(fig, ax)
        return self._save_fig_to_buffer(fig)

    def _draw_chart_elements(self, ax):
        self._plot_main_chart(ax)
        self._plot_trendline(ax)
        self._plot_anomalies(ax)

    def _plot_main_chart(self, ax):
        if self.chart_type == "line":
            ax.plot(self.plot_df["Date"], self.plot_df[self.mine], label=self.mine, linewidth=1.5)
        elif self.chart_type == "stacked" and self.mine == "Total":
            self._plot_stacked_bar(ax)
        else:
            ax.bar(self.plot_df["Date"], self.plot_df[self.mine], label=self.mine)

    def _plot_stacked_bar(self, ax):
        bottom = np.zeros(len(self.plot_df))
        for m in [col for col in self.plot_df.columns if col not in ["Date", "Total"]]:
            ax.bar(self.plot_df["Date"], self.plot_df[m], label=m, bottom=bottom)
            bottom += self.plot_df[m].fillna(0)

    def _plot_trendline(self, ax):
        dates, trend_y = self._get_trend_data()
        label = f"Trend (Deg {self.trend_degree})"
        ax.plot(dates, trend_y, color="orange", linestyle="--", linewidth=2, label=label)

    def _get_trend_data(self):
        daily_trend = self.plot_df.groupby("Date", as_index=False)[self.mine].sum()
        x_num = np.arange(len(daily_trend))
        coeffs = np.polyfit(x_num, daily_trend[self.mine], deg=self.trend_degree)
        return daily_trend["Date"], np.polyval(coeffs, x_num)

    def _extract_anomalies(self):
        if self.anomalies_df.empty:
            self.spikes, self.drops = pd.DataFrame(), pd.DataFrame()
            return
        self.spikes = self.anomalies_df[self.anomalies_df["Type"].str.lower() == "spike"]
        self.drops = self.anomalies_df[self.anomalies_df["Type"].str.lower() == "drop"]

    def _plot_anomalies(self, ax):
        if self.anomalies_df.empty: return
        self._plot_scatter(ax, self.spikes, "red", "Spike")
        self._plot_scatter(ax, self.drops, "orange", "Drop")

    def _plot_scatter(self, ax, df, color, label):
        if not df.empty:
            dates = pd.to_datetime(df["Date"], format="%d/%m/%Y")
            ax.scatter(dates, df[self.mine], color=color, s=80, label=label, zorder=5)

    def _format_axes(self, fig, ax):
        self._format_x_axis(fig, ax)
        ax.set_ylabel("Output")
        ax.legend(loc="best", fontsize=8)
        fig.tight_layout()

    def _format_x_axis(self, fig, ax):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=20))
        fig.autofmt_xdate(rotation=45)

    def _save_fig_to_buffer(self, fig):
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format="png")
        img_buf.seek(0)
        plt.close(fig)
        return img_buf

    def _add_image_to_elements(self, img_buf):
        img = RLImage(img_buf, width=self.doc.width, height=self.doc.width * 0.45)
        self.elements.append(img)
        self.elements.append(Spacer(1, 0.2 * inch))

    def _add_anomalies_breakdown(self):
        self.elements.append(Paragraph("3. Detailed Anomalies Breakdown", self.h2_style))
        if self.anomalies_df.empty:
            self.elements.append(Paragraph("No anomalies detected by any test.", self.styles['Normal']))
        else:
            self._add_detailed_anomalies()

    def _add_detailed_anomalies(self):
        self._add_anomaly_section("Spikes", self.spikes, self.spike_style)
        self.elements.append(Spacer(1, 0.1 * inch))
        self._add_anomaly_section("Drops", self.drops, self.drop_style)

    def _add_anomaly_section(self, title, df, style):
        self.elements.append(Paragraph(title, self.styles['Heading3']))
        if df.empty:
            self.elements.append(Paragraph("None detected.", self.styles['Normal']))
        else:
            self._append_anomaly_rows(df, style, title.split()[0].upper())

    def _append_anomaly_rows(self, df, style, anomaly_type):
        for _, row in df.iterrows():
            text = self._format_anomaly_text(row, anomaly_type)
            self.elements.append(Paragraph(text, style))

    def _format_anomaly_text(self, row, anomaly_type):
        d_str = row['Date'].strftime('%d/%m/%Y') if hasattr(row['Date'], 'strftime') else str(row['Date'])
        val = round(row[self.mine], 2)
        return f"<b>[{anomaly_type}] {d_str}</b> — Output: {val}"