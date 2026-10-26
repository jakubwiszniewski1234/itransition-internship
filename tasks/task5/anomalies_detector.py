import pandas as pd
import numpy as np

class AnomaliesDetector:
    ma_window = 7
    ma_percentage = 0.5

    def __init__(self, dataset:pd.DataFrame, mine:str):
        self.dataset = dataset[["Date", mine]]
        self.mine = mine
        

    def _anomalies_by_iqr(self):
        q1, q3 = np.quantile(self.dataset[self.mine], (.25, .75))
        iqr = q3 - q1
        return self.dataset[(self.dataset[self.mine] < q1 - 1.5*iqr) | (self.dataset[self.mine] > q3 + 1.5*iqr)]

    def _anomalies_by_zscore(self):
        mean, sd = np.mean(self.dataset[self.mine]), np.std(self.dataset[self.mine])
        print((abs((self.dataset[self.mine].sort_values() - mean)/sd)))
        return self.dataset[(abs((self.dataset[self.mine] - mean)/sd) > 3)]

    def _anomalies_by_ma(self):
        dataset = self.dataset
        dataset["ma"] = dataset[self.mine].rolling(self.ma_window).mean()
        return dataset[(dataset[self.mine] - dataset["ma"]).abs() / dataset["ma"].abs().where(dataset["ma"].abs() > 0) > self.ma_percentage][["Date", self.mine]]


    def _anomalies_by_grubbs(self):
        pass

    def find_anomalies(self, by:str):
        if hasattr(self, f"_anomalies_by_{by.lower()}"):
            return getattr(self, f"_anomalies_by_{by.lower()}")()
        raise ValueError(f"Unrecognized method: couldn't find anomalies by {by}.")