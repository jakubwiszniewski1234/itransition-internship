import os
import pandas as pd
import psycopg2
from psycopg2 import pool
import streamlit as st
from db_utils import read_env

st.set_page_config(page_title="User Generator")

@st.cache_resource
def get_db_pool():
    return psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=int(os.getenv("DB_PORT", 5432)),
        sslmode=os.getenv("DB_SSLMODE", "prefer")
    )

def fetch_users(seed: int, locale: str, batch_index: int, batch_size: int) -> pd.DataFrame:
    db_pool = get_db_pool()
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT {batch_size}*batch_index + row_index AS id, full_name, email, phone, address, height_cm, weight_kg, eye_color, hair_color, latitude, longitude FROM generate_users_batch(%s, %s, %s, %s);",
                (seed, locale, batch_index, batch_size)
            )
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(rows, columns=columns)
    finally:
        db_pool.putconn(conn)

if "batch_index" not in st.session_state:
    st.session_state.batch_index = 0

st.sidebar.title("Generator Settings")

locales = {
    "English (US)": "en_US",
    "Polish (Poland)": "pl_PL"
}
selected_locale = st.sidebar.selectbox("Locale", list(locales.keys()))
locale_code = locales[selected_locale]

seed = st.sidebar.number_input("Seed", value=123, step=1)
batch_size = st.sidebar.number_input("Rows number", value=10, min_value=1, max_value=100, step=1)

if "prev_seed" not in st.session_state or st.session_state.prev_seed != seed or st.session_state.prev_locale != locale_code:
    st.session_state.batch_index = 0
    st.session_state.prev_seed = seed
    st.session_state.prev_locale = locale_code

st.title("User generator")

col1, col2, col3, _ = st.columns([2, 1, 2, 7], vertical_alignment="center")

with col1:
    if st.button("Previous", disabled=(st.session_state.batch_index <= 0)):
        st.session_state.batch_index -= 1
        st.rerun()

with col2:
    st.write(f"Page {st.session_state.batch_index}")

with col3:
    if st.button("Next"):
        st.session_state.batch_index += 1
        st.rerun()

df = fetch_users(seed, locale_code, st.session_state.batch_index, batch_size)

if not df.empty:
    st.dataframe(df, use_container_width=True, hide_index=True)