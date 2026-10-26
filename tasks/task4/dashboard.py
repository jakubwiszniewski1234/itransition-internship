import streamlit as st
import pandas as pd
from datasets import loadAllDatasets, getStores
from ai_chat import show_chat

sidebar = st.sidebar
selected_store = sidebar.selectbox("Pick store to collect data from", getStores())
chat_open_button = sidebar.button(f"ASK ABOUT {selected_store}")

st.write(f"# {selected_store}")

books, orders, users = loadAllDatasets(selected_store)
orders_tab, books_tab, users_tab = st.tabs(("Orders summary", "Books and authors", "Users"))

# orders containers
top_5_days_container = orders_tab.container(border = True)
daily_revenue_chart_container = orders_tab.container(border = True)

def get_daily_revenues(dates_range:list[pd.Timestamp]) -> list[float]:
    daily_revenue_summary = orders.groupby("date")["paid_price"].sum().round(2).sort_index()
    daily_revenues = [0. for _ in dates_range]
    for date, revenue in daily_revenue_summary.items():
        daily_revenues[dates_range.index(pd.Timestamp(str(date)))] = revenue
    return daily_revenues

def get_orders_summary():
    dates_range = pd.date_range(orders["date"].min(), orders["date"].max(), freq="D").to_list()
    daily_revenue = get_daily_revenues(dates_range)
    return pd.DataFrame({"Date": dates_range, "Revenue": daily_revenue}).sort_values(by="Revenue", ascending=False)

def show_top_five_days(df:pd.DataFrame):
    top_5_days_container.write("## Top five days by revenue")
    top_5_days_container.write(df.head())

def plot_daily_revenue(df:pd.DataFrame):
    daily_revenue_chart_container.line_chart(df, x = "Date", y = "Revenue")

def show_orders_summary():
    df = get_orders_summary()
    show_top_five_days(df)
    plot_daily_revenue(df)

# books_container
unique_authors_sets = books_tab.container(border=False)
most_popular_authors = books_tab.container(border=True)

def show_unique_authors():
    unique_authors_sets.metric("Unique author sets", len(books["author"].unique()))

def show_most_popular_authors():
    top_authors = find_top_authors()
    most_popular_authors.metric("Most popular author (set)", top_authors.head(1).index[0])
    most_popular_authors.metric("who sold a book count of total", top_authors.head(1).values[0])

def show_books_summary():
    show_unique_authors()
    show_most_popular_authors()
    

def find_top_authors():
    sold_book_count = orders.groupby("book_id")["quantity"].sum()
    sold_book_quantity = books[["id", "author"]].merge(sold_book_count, how="inner", left_on="id", right_index=True)
    return sold_book_quantity[["author", "quantity"]].groupby("author").sum().sort_values(by="quantity", ascending=False)

# users
unique_users_container = users_tab.container(border=False)
best_buyer_container = users_tab.container(border=False)

def get_unique_users():
    return users["original_id"].unique()

def show_unique_users_count():
    unique_users = get_unique_users()
    unique_users_container.metric("Unique users", len(unique_users))

top_customers = orders[["user_id", "paid_price"]].groupby("user_id", as_index=False).sum().sort_values("paid_price", ascending=False)

def get_top_unique_customers():
    original_customers = top_customers[["user_id", "paid_price"]].merge(right=users[["id", "original_id"]], how="inner", left_on="user_id", right_on="id")
    top_unique_customers = original_customers[["original_id", "paid_price"]].groupby("original_id").sum().sort_values(by="paid_price", ascending=False)
    return top_unique_customers

def show_top_unique_customers():
    best_buyer_container.write("Top customer (all encounters):")
    best_buyer_container.write(get_top_unique_customers().head(1))
    best_buyer_container.write("All occurences of user:")
    best_buyer_container.write(users[users["original_id"] == get_top_unique_customers().index[0]][users.columns[:-1]].set_index("id"))

def show_users_summary():
    show_unique_users_count()
    show_top_unique_customers()


show_orders_summary()
show_books_summary()
show_users_summary()

if chat_open_button:
    show_chat(selected_store)