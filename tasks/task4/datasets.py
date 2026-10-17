import pandas as pd
from typing import Literal
import yaml

DIRECTORIES = Literal["./data/STORE1/", "./data/STORE2/", "./data/STORE3/", "./data/STORE4/", "./data/STORE5/"]
FILES = Literal["books.yaml", "orders.parquet", "users.csv"]
def read_csv(path: str):
    return pd.read_csv(path, sep=",")

def read_parquet(path: str):
    return pd.read_parquet(path)

def read_yaml(path: str):
    with open(path, "r") as f:
        loaded:dict = yaml.load(f.read(), yaml.loader.SafeLoader)
    
    loaded_par = [{key[1:]: value for key, value in item.items()} for item in loaded]
    return pd.DataFrame(loaded_par)

def loadDataset(fileName: FILES, directory: DIRECTORIES = "./data/STORE1/") -> pd.DataFrame:
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