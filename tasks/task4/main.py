import pandas as pd
import datasets as DS

DIR = "cleaned_data/STORE1/"

books = DS.loadDataset("books.csv", DIR)
orders = DS.loadDataset("orders.csv", DIR)
users = DS.loadDataset("users.csv", DIR)

