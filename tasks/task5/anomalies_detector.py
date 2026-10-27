import pandas as pd
import numpy as np
try:
    from outliers import smirnov_grubbs as grubbs
except:
    from OUTLIERS import smirnov_grubbs as grubbs

SPIKE_TAG = "spike"
DROP_TAG = "drop"

class AnomaliesDetector:
    iqr_factor = 1.5
    zscore_threshold = 2
    ma_window = 7
    ma_percentage = 0.5
    grubbs_alpha = 0.05

    def __init__(self, dataset:pd.DataFrame, mine:str):
        self.dataset = dataset[["Date", mine]].copy()
        self.mine = mine

    def anomaly_type(output:float, threshold:float):
        if output > threshold: return SPIKE_TAG
        return DROP_TAG

    def _assign_anomaly_types(self, dataset:pd.DataFrame):
        threshold = dataset[self.mine].mean()
        dataset["Type"] = np.where(dataset[self.mine] > threshold, SPIKE_TAG, DROP_TAG)
        return dataset

    def _anomalies_by_iqr(self):
        q1, q3 = np.quantile(self.dataset[self.mine], (.25, .75))
        iqr = q3 - q1
        outliers = self.dataset[(self.dataset[self.mine] < q1 - self.iqr_factor*iqr) | (self.dataset[self.mine] > q3 + self.iqr_factor*iqr)]
        return self._assign_method(outliers, "iqr rule")
    
    def _anomalies_by_zscore(self):
        mean, sd = np.mean(self.dataset[self.mine]), np.std(self.dataset[self.mine])
        outliers = self.dataset[(abs((self.dataset[self.mine] - mean)/sd) > self.zscore_threshold)]
        return self._assign_method(outliers, "zscore")

    def _anomalies_by_ma(self):
        dataset = self.dataset.copy()
        dataset["ma"] = dataset[self.mine].rolling(self.ma_window, min_periods=1).mean()
        outliers_df = dataset[(dataset[self.mine] - dataset["ma"]).abs() / dataset["ma"].abs().replace(0, pd.NA) > self.ma_percentage][["Date", self.mine]]
        return self._assign_method(outliers_df, "moving average")

    def _anomalies_by_grubbs(self):
        outliers = grubbs.two_sided_test_indices(self.dataset[self.mine].to_numpy(), self.grubbs_alpha)
        return self._assign_method(self.dataset.loc[outliers], "grubbs test")

    def _assign_method(self, dataset, method:str):
        return pd.DataFrame(dataset).assign(Method=method)

    def _anomalies_by_all(self):
        dates = pd.concat(getattr(self, f"_anomalies_by_{by}")() for by in ["iqr", "zscore", "ma", "grubbs"])
        return self.dataset[self.dataset["Date"].isin(dates["Date"])]

    def find_anomalies(self, by:str):
        if hasattr(self, f"_anomalies_by_{by.lower()}"):
            return self._assign_anomaly_types(getattr(self, f"_anomalies_by_{by.lower()}")())
        raise ValueError(f"Unrecognized method: couldn't find anomalies by {by}.")