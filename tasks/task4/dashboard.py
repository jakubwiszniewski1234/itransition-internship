import streamlit as st
import pandas as pd
from datasets import loadDataset, getStores, getDirectories, CLEANED_DIRECTORIES, STORES

sidebar = st.sidebar
selected_store = sidebar.selectbox("Pick store to collect data from", getStores())
cleaned_data_store_paths = getDirectories()

books = loadDataset("books.csv", cleaned_data_store_paths[int(selected_store[-1]) - 1])
orders = loadDataset("orders.csv", cleaned_data_store_paths[int(selected_store[-1]) - 1])
users = loadDataset("users.csv", cleaned_data_store_paths[int(selected_store[-1]) - 1])

st.write(f"# {selected_store}")

orders_tab, books_tab, users_tab, bot_tab = st.tabs(("Orders summary", "Books and authors", "Users", "Ask about data"))

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

unique_users_metric = unique_users_container.metric("Unique users", "...")

all_unique_users = users["original_id"].unique().tolist()
unique_users_metric.metric("Unique users", len(all_unique_users))

top_customers = orders[["user_id", "paid_price"]].groupby("user_id", as_index=False).sum().sort_values("paid_price", ascending=False)

prices = {original_id: 0 for original_id in all_unique_users}
master_customers = top_customers[["user_id", "paid_price"]].merge(right=users[["id", "original_id"]], how="inner", left_on="user_id", right_on="id")
top_unique_customers = master_customers[["original_id", "paid_price"]].groupby("original_id").sum().sort_values(by="paid_price", ascending=False)

best_buyer_container.write("Top customer (all encounters):")
best_buyer_container.write(top_unique_customers.head(1))

best_buyer_container.write("All occurences of user:")
best_buyer_container.write(users[users["original_id"] == top_unique_customers.head(1).index[0]][users.columns[:-1]].set_index("id"))


bottom = st.bottom
chat_open_button = sidebar.button("Ask about anything")

from ai_chat import show_chat
if chat_open_button:
    show_chat(selected_store)