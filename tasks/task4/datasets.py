import pandas as pd
from pathlib import Path

DATA_FOLDER = "./data/STORE1"

DS_BOOKS = "books.yaml"
DS_ORDERS = "orders.parquet"
DS_USERS = "users.csv"

def loadDataset(fileName: str, directory: str | Path = DATA_FOLDER) -> pd.DataFrame:
    datasetPath = directory + fileName

    fileType = fileName.split(".")[-1]
    read = {
        "yaml": read_yaml,
        "csv": read_csv,
        "parquet": read_parquet
    }
    try:
        dataset = read[fileType]
        return dataset
    except FileNotFoundError:
        print(f"File {datasetPath} not found.")
