import pandas as pd
import numpy as np
import streamlit as st
from anomalies_detector import AnomaliesDetector

DEFAULT_TYPE = "line"

class SummaryChart:
    def __init__(self, dataset:pd.DataFrame, mine:str):
        if mine == "Total":
            self.dataset = (
                dataset.loc[:, dataset.columns != "Total"]
                .melt(id_vars="Date", var_name="Mine", value_name="Total")
            )
        else:
            self.dataset = dataset[["Date", mine]].copy()
            self.dataset["Mine"] = mine
        self.mine = mine
        self.trend = 1
        self.detector = AnomaliesDetector(dataset, self.mine)
        self.anomalies = self.detector.find_anomalies(by = "all")
        self.type = DEFAULT_TYPE
    
    def _set_line(self):
        pass

    def _set_bar(self):
        pass

    def _set_stacked(self):
        pass

    def set_type(self, type:str):
        if hasattr(self, f"_set_{type}"):
            self.type = type
            return getattr(self, f"_set_{type}")()
        raise ValueError(f"Couldn't set chart type to \"{type}\".")

    def set_trend(self, poly_degree:int):
        self.trend = poly_degree

    def _draw_stacked(self):
        return st.bar_chart(self.dataset, x = "Date", y = self.mine, stack = True, color = "Mine")

    def _draw_bar(self):
        return st.bar_chart(self.dataset, x = "Date", y = self.mine, stack = False, color = "Mine")

    def _draw_line(self):
        return st.line_chart(self.dataset, x = "Date", y = self.mine, color = "Mine")

    def draw_plot(self):
        return getattr(self, f"_draw_{self.type}")()

    def add_trend(self):
        trend_coeffs = np.polyfit(self.trend)
        
    def draw(self):
        plot = self.draw_plot()
        plot.draw_trend()
