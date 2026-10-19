import streamlit as st
import pandas as pd
from datasets import loadDataset

col1, col2, col3 = st.columns([7, 1, 1])

books = loadDataset("books.csv", "cleaned_data/STORE1/")
orders = loadDataset("orders.csv", "cleaned_data/STORE1/")
users = loadDataset("users.csv", "cleaned_data/STORE1/")

orders_tab, books_tab, users_tab = st.tabs(("Orders summary", "Books and authors", "Users"))

# orders containers
top_5_days_container = orders_tab.container(border = True)
daily_revenue_chart_container = orders_tab.container(border = True)

earliest = orders["date"].min()
furthest = orders["date"].max()

dates_range = pd.date_range(earliest, furthest, freq="D")
dates_range_list = dates_range.to_list()
daily_revenue_summary = orders.groupby("date")["paid_price"].sum().round(2).sort_index()

daily_revenues = [0 for date in dates_range]
for date, revenue in daily_revenue_summary.items():
    idx_in_range = dates_range_list.index(pd.Timestamp(str(date)))
    daily_revenues[idx_in_range] = revenue

top_5_days_container.write("## Top five days by revenue")
top_5_days_container.write(daily_revenue_summary.sort_values(ascending=False).head(5))

line_chart_df:pd.DataFrame = pd.DataFrame({"date": dates_range, "revenue": daily_revenues})
daily_revenue_chart_container.line_chart(line_chart_df, x = "date", y = "revenue")

# books_container
unique_authors_sets = books_tab.container(border=False)
most_popular_authors = books_tab.container(border=True)



def sortAuthors(authors:str) -> str:
    return ", ".join(sorted([author.strip() for author in authors.split(",")]))

books["author"] = books["author"].apply(sortAuthors)
unique_authors_count = len(books["author"].unique())
unique_authors_metric = unique_authors_sets.metric("Unique author sets", unique_authors_count)


sold_book_count = orders.groupby("book_id")["quantity"].sum()
sold_book_quantity = books[["id", "author"]].merge(sold_book_count, how="inner", left_on="id", right_index=True)
top_authors_by_sales = sold_book_quantity[["author", "quantity"]].groupby("author").sum().sort_values(by="quantity", ascending=False)
most_popular_authors.metric("Most popular author (set)", top_authors_by_sales.head(1).index[0])
most_popular_authors.metric("who sold a book count of total", top_authors_by_sales.head(1).values[0])

# users
unique_users_container = users_tab.container(border=False)
best_buyer_container = users_tab.container(border=False)

from networkx.utils.union_find import UnionFind

all_unique_users = "..."
unique_users_metric = unique_users_container.metric("Unique users", "...")

def uniqueUsers(users:pd.DataFrame):
    users = users.sort_values(by="id")
    uf = UnionFind(users["id"])
    users_dict = users.to_dict("records")       # main speed up
    
    columns = ["name", "address", "phone", "email"]

    def matches(user1, user2) -> int:
        return sum([user1[col] == user2[col] for col in columns])
        
    for i in range(users.shape[0]):
        for j in range(i + 1, users.shape[0]):
            if matches(users_dict[i], users_dict[j]) >= 3:
                uf.union(users.loc[i, "id"], users.loc[j, "id"])
                
    return list(uf.to_sets())

all_unique_users = uniqueUsers(users)
unique_users_metric.metric("Unique users", len(all_unique_users))

top_customers = orders[["user_id", "paid_price"]].groupby("user_id", as_index=False).sum().sort_values("paid_price", ascending=False)
def uniqueUsersSum(prices:pd.DataFrame):
    all_prices = [0 for u in all_unique_users]
    
    def uniqueUserIndex(user_id:int) -> int:
        for i in range(len(all_unique_users)):
            if user_id in all_unique_users[i]:
                return i
        return -1
            
    unique_users_map = {user_id: uniqueUserIndex(user_id) for user_id in prices["user_id"]}
    
    def add_price(user_id:int):
        all_prices[unique_users_map[user_id]] += prices[prices["user_id"] == user_id]["paid_price"].to_list()[0]
        
    prices["user_id"].apply(lambda p: add_price(p))
    return pd.DataFrame({"user_id": all_unique_users, "paid_price": all_prices})

top_unique_customers = uniqueUsersSum(top_customers).sort_values("paid_price", ascending=False)
best_buyer_container.write(top_unique_customers.head(1))