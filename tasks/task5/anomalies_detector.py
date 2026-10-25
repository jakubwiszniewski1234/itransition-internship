import pandas as pd

class AnomaliesDetector:
    def __init__(self, dataset:pd.DataFrame):
        self.dataset = dataset

    def _anomalies_by_IQR(self):
        pass

    def _anomalies_by_zscore(self):
        pass

    def _anomalies_by_ma(self):
        pass

    def _anomalies_by_grubbs(self):
        pass

    def find_anomalies(self, by:str):
        if hasattr(self, f"_anomalies_by_{by}"):
            return getattr(self, f"_anomalies_by_{by}")()
        raise ValueError(f"Unrecognized method: couldn't find anomalies by {by}.")