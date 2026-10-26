import pandas as pd
import datasets as DS
import functools
import numpy as np
from networkx.utils.union_find import UnionFind
from dateutil import parser

def clean_function(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    setattr(pd, f"{func.__name__}", func)
    return inner

def refactor_publication_year(books:pd.DataFrame):
    year_str = books["year"].astype(str).str.strip()
    not_years = books[~year_str.str.match(r'^\d{4}$', na=False)]["year"].unique()
    books["year"] = books["year"].replace(not_years, np.nan).astype("Int16")
    return books

def unify_missing_publishers(books:pd.DataFrame):
    for bad_value in ['-', '', ' ', '\t', 'NULL']:
        books["publisher"] = books["publisher"].replace(bad_value, pd.NA)
    return books

def fix_publishing_errors(books:pd.DataFrame):
    return unify_missing_publishers(refactor_publication_year(books))

def correct_authors_order(books:pd.DataFrame):
    sort_authors = lambda authors: ", ".join(sorted([author.strip() for author in authors.split(",")]))
    books["author"] = books["author"].apply(sort_authors)
    return books

@clean_function
def clean_books(books:pd.DataFrame):
    books.drop_duplicates(inplace = True)
    return correct_authors_order(fix_publishing_errors(books))

def strip_missing_addresses(users:pd.DataFrame):
    users["address"] = users["address"].str.strip().replace('', None)
    return users

def unify_phones(users:pd.DataFrame):
    users["phone"] = users["phone"].str.strip().str.replace(r'\D', '', regex = True)
    return users

def find_unique_users(users:pd.DataFrame):
    users = users.sort_values(by="id").reset_index(drop=True)
    uf = UnionFind(users["id"])
    users_dict = users.to_dict("records")
    
    columns = ["name", "address", "phone", "email"]

    def matches(user1, user2) -> int:
        return sum([user1[col] == user2[col] for col in columns])
        
    for i in range(len(users_dict)):
        for j in range(i + 1, len(users_dict)):
            if matches(users_dict[i], users_dict[j]) >= 3:
                uf.union(users_dict[i]["id"], users_dict[j]["id"])
    return list(uf.to_sets())

def assign_original_ids(unique_users:list):
    return {user_id: min(unique_users_set) for unique_users_set in unique_users for user_id in unique_users_set}

def tag_original_users(users):
    unique_users = find_unique_users(users)
    original_ids = assign_original_ids(unique_users)
    users["original_id"] = users["id"].apply(lambda u: original_ids[u])
    return users

@clean_function
def clean_users(users:pd.DataFrame):
    users.drop_duplicates(inplace = True)
    users = unify_phones(strip_missing_addresses(users))
    users = tag_original_users(users)
    return users

def is_euro(price:str):
    return "€" in price or "eur" in price.lower()

def is_dollar(price:str):
    return "$" in price or "usd" in price.lower()

def remove_cents(price:str) -> str:
    if "¢" in price:
        if price[-1] == "¢":
            price = f"{price[0:2]}.{price[2:-1]}"
        else: price = price.replace("¢", ".")
    return price

def currency_rate(price:str):
    return 1.2 if is_euro(price) else 1

def currency_signs(price:str):
    if is_euro(price):
        return "€", "eur"
    else:
        return "$", "usd"

def process_price(price:str):
    symbol, acronym = currency_signs(price)
    return remove_cents(price.lower().replace(symbol, "").replace(acronym, "").strip())

def to_dollar(price:str):
    return round(currency_rate(price) * float(process_price(price)), 2)

def evaluate_paid_price(orders:pd.DataFrame):
    orders["paid_price"] = orders["unit_price"].apply(to_dollar) * orders["quantity"]
    return orders

def unify_missing_shipping(orders:pd.DataFrame):
    for ship in orders[orders["shipping"].str.len() < 15]["shipping"].unique():
        orders.replace({"shipping": ship}, pd.NA, inplace = True)
    return orders

def parse_date(date:str):
    try:
        return str(parser.parse(date.replace(",", " "), ignoretz=True, fuzzy=True)).split(".")[0]
    except (ValueError, TypeError, OverflowError):
        return pd.NaT

def add_date_column(orders:pd.DataFrame):
    orders["date"] = pd.to_datetime(orders["timestamp"].map(parse_date), errors="coerce")
    orders["date"] = orders["date"].dt.strftime("%Y-%m-%d").astype("datetime64[s]")
    return orders

@clean_function
def clean_orders(orders:pd.DataFrame):
    orders = unify_missing_shipping(evaluate_paid_price(orders))
    orders = add_date_column(orders)
    return orders

def clean_all(store:str):
    datasets = DS.loadAllDatasets(store, cleaned = False)
    return tuple([getattr(pd, f"clean_{dataset.df_name}")(dataset) for dataset in datasets])

def save_all(datasets:tuple[pd.DataFrame], store:str):
    tuple(dataset.to_csv(f"./cleaned_data/{store}/{dataset.df_name}.csv") for dataset in datasets)

def save_cleaned_data(store:str):
    save_all(clean_all(store), store)

if __name__ == "__main__":
    for store in DS.getStores():
        save_cleaned_data(store) 