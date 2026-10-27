import pandas as pd
import numpy as np
import altair as alt
import streamlit as st
from anomalies_detector import AnomaliesDetector

DEFAULT_TYPE = "line"

class SummaryChart:
    trend_degree = 1

    def __init__(self, dataset:pd.DataFrame, mine:str, detector:AnomaliesDetector = None, anomalies:pd.DataFrame = None):
        self.dataset = dataset.copy().sort_values("Date").reset_index(drop = True)
        self.mine = mine
        self.dataset["Trendline"] = self.trend()
        self.detector = (detector if detector is not None else AnomaliesDetector(dataset, self.mine))
        self.anomalies = (anomalies if anomalies is not None else self.detector.find_anomalies(by="all"))
        self.type = DEFAULT_TYPE
    
    def _set_line(self):
        pass

    def _set_bar(self):
        pass

    def _set_stacked(self):
        pass

    def set_anomalies_detector(self, detector):
        self.detector = detector

    def set_type(self, type:str):
        if hasattr(self, f"_set_{type}"):
            self.type = type
            return getattr(self, f"_set_{type}")()
        raise ValueError(f"Couldn't set chart type to \"{type}\".")

    def set_trend(self, poly_degree:int):
        self.trend_degree = poly_degree

    def trend(self):
        daily = self.dataset.groupby("Date", as_index=False)[self.mine].sum()
        coeffs = np.polyfit(np.arange(len(daily)), daily[self.mine], deg=self.trend_degree)
        daily["Trendline"] = np.polyval(coeffs, np.arange(len(daily)))
        trend_map = daily.set_index("Date")["Trendline"]
        return self.dataset["Date"].map(trend_map)
    
    def trend_line(self):
        self.dataset["Trendline"] = self.trend()
        trend_line = (
            alt.Chart(self.dataset)
            .mark_line(strokeDash=[6, 4], size=2)
            .encode(x="Date:T", y="Trendline:Q")
        )

        return trend_line

    def _draw_stacked(self):
        if self.mine == "Total":
           dataset = self.dataset.loc[:, ~self.dataset.columns.isin(["Total", "Trendline"]) ].melt(id_vars="Date", var_name="Mine", value_name="Total")
        else: dataset = self.dataset
        chart = (
            alt.Chart(dataset).mark_bar()
            .encode(x="Date:T", y=alt.Y(f"{self.mine}:Q", title=self.mine), color="Mine:N") 
        )

        return st.altair_chart((chart + self.trend_line() + self.anomaly_points()).resolve_scale(color="independent"))


    def _draw_bar(self):
        chart = (
            alt.Chart(self.dataset).mark_bar()
            .encode(x="Date:T", y=alt.Y(f"{self.mine}:Q", title=self.mine), color="Mine:N") 
        )

        return st.altair_chart((chart + self.trend_line() + self.anomaly_points()).resolve_scale(color="independent"))

    def anomaly_points(self):
        return alt.Chart(self.anomalies).mark_point(
                size=120,
                filled=True,
                stroke="black",
                strokeWidth=1.5,
            ).encode(
                x="Date:T",
                y=alt.Y(f"{self.mine}:Q"),
                color=alt.Color(
                    "Type:N",
                    scale=alt.Scale(
                        domain=["spike", "drop"],
                        range=["#dc2626", "#eab308"],
                    ),
                    legend=alt.Legend(title="Anomaly Type"),
                ),
            )

    def _draw_line(self):
        chart = (
            alt.Chart(self.dataset).mark_line()
            .encode(x="Date:T", y=alt.Y(f"{self.mine}:Q", title=self.mine), color="Mine:N")
        )

        return st.altair_chart((chart + self.trend_line() + self.anomaly_points()).resolve_scale(color="independent"))

    def draw_plot(self):
        return getattr(self, f"_draw_{self.type}")()
        
    def draw(self):
        return self.draw_plot()
