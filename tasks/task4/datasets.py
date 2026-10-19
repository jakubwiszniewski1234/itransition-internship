import pandas as pd
from typing import Literal
import yaml

DIRECTORIES = Literal["data/STORE1/", "data/STORE2/", "data/STORE3/", "data/STORE4/", "data/STORE5/"]
CLEANED_DIRECTORIES = Literal["cleaned_data/STORE1/", "cleaned_data/STORE2/", "cleaned_data/STORE3/", "cleaned_data/STORE4/", "cleaned_data/STORE5/"]

FILES = Literal["books.yaml", "orders.parquet", "users.csv"]
CLEANED_FILES = Literal["books.csv", "orders.csv", "users.csv"]
def read_csv(path: str):
    return pd.read_csv(path, sep=",")

def read_parquet(path: str):
    return pd.read_parquet(path)

def read_yaml(path: str):
    with open(path, "r") as f:
        loaded:dict = yaml.load(f.read(), yaml.loader.SafeLoader)
    
    loaded_par = [{key[1:]: value for key, value in item.items()} for item in loaded]
    return pd.DataFrame(loaded_par)

def loadDataset(fileName: FILES | CLEANED_FILES, directory: DIRECTORIES | CLEANED_DIRECTORIES = "data/STORE1/") -> pd.DataFrame:
    datasetPath = directory + fileName
    fileType = fileName.split(".")[-1]
    read = {
        "yaml": read_yaml,
        "csv": read_csv,
        "parquet": read_parquet
    }

    try:
        dataset = read[fileType](datasetPath)
    except FileNotFoundError:
        print(f"File {datasetPath} not found.")
    return dataset