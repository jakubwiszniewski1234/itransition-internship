import streamlit as st
import pandas as pd
from datasets import loadDataset

col1, col2, col3 = st.columns([7, 1, 1])

books:pd.DataFrame = loadDataset("books.csv", "cleaned_data/STORE1/")
orders:pd.DataFrame = loadDataset("orders.csv", "cleaned_data/STORE1/")

orders_tab, books_tab, users_tab = st.tabs(("Orders summary", "Books and authors", "Users"))


# best days by revenue
# orders containers
top_5_days_container = orders_tab.container(border = True)
daily_revenue_chart_container = orders_tab.container(border = True)

earliest = orders["date"].min()
furthest = orders["date"].max()

dates_range = pd.date_range(earliest, furthest, freq="D")
dates_range_list = dates_range.to_list()
daily_revenue_summary:pd.DataFrame = orders.groupby("date")["paid_price"].sum().round(2).sort_index()

daily_revenues = [0 for date in dates_range]
for date, revenue in daily_revenue_summary.items():
    idx_in_range = dates_range_list.index(pd.Timestamp(str(date)))
    daily_revenues[idx_in_range] = revenue

top_5_days_container.write("## Top five days by revenue")
top_5_days_container.write(daily_revenue_summary.sort_values(ascending=False).head(5))

line_chart_df:pd.DataFrame = pd.DataFrame({"date": dates_range, "revenue": daily_revenues})
daily_revenue_chart_container.line_chart(line_chart_df, x = "date", y = "revenue")