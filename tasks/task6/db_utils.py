import os
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values

def read_env(name: str) -> str:
    name = name.replace("db", "")
    return os.getenv(f"DB_{name.upper()}")

def get_db_credentials() -> Dict[str, str]:
    return {cred: read_env(cred) for cred in ["host", "port", "dbname", "user", "password"]}

def get_db_connection():
    return psycopg2.connect(**get_db_credentials())

def insert_data(connection, query: str, data: List[Tuple]):
    if not data:
        return
    with connection.cursor() as cursor:

        execute_values(cursor, query, data)
    connection.commit()

def execute_file(connection, file_path:str):
    with open(file_path, "r") as f:
        with connection.cursor() as cursor:
            cursor.execute(f.read().strip())

def create_lookup_tables(connection):
    execute_file(connection, "create_lookup_tables.sql")