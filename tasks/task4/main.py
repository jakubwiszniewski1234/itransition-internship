import pandas as pd
import datasets as DS

books = DS.loadDataset("books.yaml")
orders = DS.loadDataset("orders.parquet")
users = DS.loadDataset("users.csv")

# prepare data
# print(books.dtypes)
# id            int64
# title           str
# author          str
# genre           str
# publisher       str
# year         object

books = books.drop_duplicates()
books["year"] = books["year"]
books["year"] = books["year"].astype("Int16")
print(books["year"].isna().sum())
