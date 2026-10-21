import json
import os
import re
import sqlite3

from groq.types.chat.chat_completion_tool_param import ChatCompletionToolParam
import pandas as pd
import streamlit as st
from groq import Groq, Omit
from datasets import loadDataset, STORES
from typing import Iterable

def create_database(STORE):
    tables = {
        os.path.splitext(name)[0]: loadDataset(name, f"cleaned_data/{STORE}/") 
        for name in ["books.csv", "users.csv", "orders.csv"]
    }

    connection = sqlite3.connect(":memory:", check_same_thread = False)
    connection.row_factory = sqlite3.Row

    for name, value in tables.items():
        table_name = re.sub(r'\W+', "_", str(name)).strip("_") or "dataset"
        if isinstance(value, pd.DataFrame):
            frame = value
        elif isinstance(value, dict):
            frame = pd.DataFrame(value)
        else:
            frame = pd.DataFrame(value)

        frame.to_sql(table_name, connection, if_exists = "replace", index = False)

    connection.execute("PRAGMA query_only = ON")
    return connection

def execute_sql_query(connection, query):
    query = query.strip()
    if not query or ";" in query or not re.match(r"^(SELECT|WITH)\b", query, re.I):
        return {"error": "Only a single read-only SELECT query is allowed."}

    try:
        cursor = connection.execute(query)
        return {
            "columns": [column[0] for column in cursor.description or []],
            "rows": [dict(row) for row in cursor.fetchmany(200)]
        }
    except sqlite3.Error as error:
        return {"error": str(error)}

def reset_chat():
    st.session_state.ai_chat_messages.clear()
    st.session_state.ai_chat_db.close()
    st.session_state.store = None

@st.dialog("AI Chat", width = "large", position = "right", on_dismiss = reset_chat)
def show_chat(STORE:str):
    st.session_state.store = STORE
    if "ai_chat_messages" not in st.session_state:
        st.session_state.ai_chat_messages = []
    if "ai_chat_db" not in st.session_state or st.session_state.ai_chat_db is None:
        try:
            st.session_state.ai_chat_db = create_database(STORE)
        except Exception as error:
            st.error(f"Could not load datasets: {error}")
            return

    for message in st.session_state.ai_chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about books, orders or users")
    if not prompt:
        return

    st.session_state.ai_chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY is not configured.")
        return

    tools: Iterable[ChatCompletionToolParam] | None | Omit = [
        {
            "type": "function",
            "function": {
                "name": "execute_sql_query",
                "description": "Run a read-only SQL SELECT query against loaded datasets.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "Answer questions using the books, orders and users datasets. "
                "Use execute_sql_query when data is needed. "
                "Infer table and column names from SQL errors when necessary. "
                "Never invent query results. "
                "Only request read-only SELECT queries."
                "Do NOT explain your thought process."
                "Just give straight-to-the-point answer"
            )
        },
        *st.session_state.ai_chat_messages
    ]

    try:
        client = Groq(api_key = api_key)
        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model = "openai/gpt-oss-120b",
                messages = messages,
                tools = tools,
                tool_choice = "auto"
            )

            assistant_message = response.choices[0].message

            while assistant_message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in assistant_message.tool_calls
                    ]
                })

                for call in assistant_message.tool_calls:
                    if call.function.name == "execute_sql_query":
                        arguments = json.loads(call.function.arguments)
                        result = execute_sql_query(st.session_state.ai_chat_db, arguments.get("query", ""))
                    else:
                        result = {"error": "Unknown tool."}

                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, default=str)
                    })

                response = client.chat.completions.create(
                    model = "openai/gpt-oss-120b",
                    messages = messages,
                    tools = tools,
                    tool_choice = "auto"
                )

                assistant_message = response.choices[0].message

            answer = assistant_message.content or "I couldn't generate a response."
            st.markdown(answer)
            st.session_state.ai_chat_messages.append({
                "role": "assistant",
                "content": answer
            })
    except Exception as error:
        st.error(f"Chat request failed: {error}")