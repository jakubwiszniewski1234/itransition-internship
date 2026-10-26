import pandas as pd
import typing
import yaml

STORES = typing.Literal["STORE1", "STORE2", "STORE3", "STORE4", "STORE5"]

def getStores()->list[str]:
    return list(typing.get_args(STORES))

DIRECTORIES = typing.Literal["data/STORE1/", "data/STORE2/", "data/STORE3/", "data/STORE4/", "data/STORE5/"]
CLEANED_DIRECTORIES = typing.Literal["cleaned_data/STORE1/", "cleaned_data/STORE2/", "cleaned_data/STORE3/", "cleaned_data/STORE4/", "cleaned_data/STORE5/"]
def getDirectories(cleaned:bool = True)->list[str]:
    return list(typing.get_args(CLEANED_DIRECTORIES if cleaned else DIRECTORIES))

FILES = typing.Literal["books.yaml", "orders.parquet", "users.csv"]
CLEANED_FILES = typing.Literal["books.csv", "orders.csv", "users.csv"]
def getFiles(cleaned = True)->list[str]:
    return list(typing.get_args(CLEANED_FILES if cleaned else FILES))

def read_yaml(path: str):
    with open(path, "r") as f:
        loaded:dict = yaml.safe_load(f)

    loaded_par = [{key[1:]: value for key, value in item.items()} for item in loaded]
    return pd.DataFrame(loaded_par)
pd.read_yaml = read_yaml


def setName(df:pd.DataFrame, df_name: str):
    df.df_name = df_name
    return df

def loadDataset(fileName:str, directory:str = "data/STORE1/") -> pd.DataFrame:
    datasetPath = directory + fileName
    name, fileType = fileName.split(".")
    df = getattr(pd, f"read_{fileType}")(datasetPath)
    return setName(df, name)

def loadAllDatasets(store:str, cleaned:bool = True):
    directory = "/".join([f"{"cleaned_" if cleaned else ""}data", store, ""])
    return tuple(loadDataset(file, directory) for file in getFiles(cleaned))