import sqlalchemy
import pandas as pd
from getpass import getpass

try:
    with open("./task3.5.json", "r") as f:
        pass
except FileNotFoundError:
    raise FileNotFoundError("Please run Ruby script first.")

db_password = getpass("provide password")

connection = sqlalchemy.create_engine(
    url = f"postgresql+psycopg2://postgres:{db_password}@localhost:5432/tasks"
)


def parseToUSD(price:str) -> float:
    RATE = 1.2
    if(price[0]=="€"):
        return round(RATE * float(price[1:]), 2)
    
    return round(float(price[1:]), 2)

def parseToEUR(price:str) -> float:
    RATE = 1 / 1.2
    if(price[0]=="$"):
        return round(RATE * float(price[1:]), 2)
    
    return round(float(price[1:]), 2)

def ingestJSON():
    data = pd.read_json("./task3.5.json")
    
    data["id"] = data["id"].astype("str")
    data["price_usd"] = data["price"].apply(parseToUSD)
    data["price_eur"] = data["price"].apply(parseToEUR)
    data.to_sql("books", connection, if_exists="replace")
    
def createSummaryTable():
    with connection.connect() as cursor:
        SQL_SUMMARY_TABLE = sqlalchemy.text("""
        DROP TABLE IF EXISTS summary; 
        CREATE TABLE summary AS 
        SELECT 
            year, 
            COUNT(title) AS book_count, 
            ROUND(CAST(AVG(price_usd) AS numeric), 2) AS average_price 
        FROM books 
        GROUP BY year ORDER BY year DESC                                    
        """)
        
        cursor.execute(SQL_SUMMARY_TABLE)
        cursor.commit()

def run(wait:bool = True):
    ingestJSON()
    createSummaryTable()
    
    if(wait): input()

run()

summary = pd.read_sql_table("summary", connection)
summary.to_clipboard()