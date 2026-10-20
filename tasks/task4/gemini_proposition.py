import json
import os
import duckdb
import pandas as pd
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq Client (Reads GROQ_API_KEY from environment)
client = Groq()

# ----------------------------------------------------
# 1. Load Datasets & Register to DuckDB
# ----------------------------------------------------
@st.cache_resource
def setup_database():
    """
    Loads dataset files into memory and exposes them as SQL tables in DuckDB.
    """
    # Dummy load function matching your snippet
    def loadDataset(file_name, path):
        return pd.read_csv(path + file_name)

    # Load DataFrames
    books = loadDataset("books.csv", "cleaned_data/STORE1/")
    orders = loadDataset("orders.csv", "cleaned_data/STORE1/")
    users = loadDataset("users.csv", "cleaned_data/STORE1/")

    # Create an in-memory DuckDB connection and register DataFrames as SQL tables
    con = duckdb.connect(database=":memory:")
    con.register("books", books)
    con.register("orders", orders)
    con.register("users", users)

    return con, books, orders, users

con, books_df, orders_df, users_df = setup_database()

# ----------------------------------------------------
# 2. Define the Query Tool Function for AI
# ----------------------------------------------------
def execute_sql_query(query: str) -> str:
    """
    Executes a SELECT query against DuckDB and returns JSON results.
    """
    try:
        # Enforce read-only / SELECT security check
        cleaned_query = query.strip()
        if not cleaned_query.lower().startswith("select") and not cleaned_query.lower().startswith("with"):
            return json.dumps({"error": "Only SELECT queries are allowed."})
        
        # Execute query via DuckDB
        result_df = con.execute(cleaned_query).df()
        
        # Convert result to JSON format for the model
        return result_df.to_json(orient="records")
    except Exception as e:
        return json.dumps({"error": str(e)})

# Map function names to executable Python functions
available_tools = {
    "execute_sql_query": execute_sql_query
}

# ----------------------------------------------------
# 3. Tool Schema Definition for Groq API
# ----------------------------------------------------
schema_info = f"""
Table: books (columns: {", ".join(books_df.columns)})
Table: orders (columns: {", ".join(orders_df.columns)})
Table: users (columns: {", ".join(users_df.columns)})
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "execute_sql_query",
            "description": f"Execute a SQL SELECT query against DuckDB to count, aggregate, or filter data from books, orders, or users tables.\nAvailable schema:\n{schema_info}",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Valid SQL SELECT query to compute exact results (e.g., SELECT count(*) FROM users WHERE country='Poland')"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# ----------------------------------------------------
# 4. Agent Function to Process Question using Groq
# ----------------------------------------------------
def ask_ai_with_tools(messages):
    """
    Calls Groq API with Tool Calling enabled.
    Executes SQL tools if requested, then asks LLM to format final answer.
    """
    system_prompt = (
        "You are an analytical assistant for an e-commerce platform. "
        "You do not calculate statistics yourself. Always use the `execute_sql_query` tool "
        "to answer questions about users, books, and orders."
    )
    
    # Format message payload
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    # We use Groq's high-performance model supporting tool calls
    MODEL_NAME = "openai/gpt-oss-120b"

    # First API call: Groq decides whether to call a tool
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=full_messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls

    # Check if the AI decided to invoke the SQL tool
    if tool_calls:
        full_messages.append(response_message)
        
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            
            # Execute the function locally in DuckDB
            if func_name in available_tools:
                sql_result = available_tools[func_name](query=func_args.get("query"))
                
                # Append tool execution output back into context
                full_messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": sql_result
                })

        # Second API call: Groq generates natural language response from SQL output
        second_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=full_messages
        )
        return second_response.choices[0].message.content
    else:
        return response_message.content

# ----------------------------------------------------
# 5. Streamlit Chat Interface
# ----------------------------------------------------
st.title("📊 E-Commerce Analytics Dashboard (Powered by Groq)")

# Streamlit Chat Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display prior chat messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
if user_input := st.chat_input("Ask a question about books, orders, or users..."):
    # Append user question to history & render
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Executing SQL query and generating answer via Groq..."):
            assistant_response = ask_ai_with_tools(st.session_state.chat_history)
            st.markdown(assistant_response)

    # Store assistant response in session state
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})