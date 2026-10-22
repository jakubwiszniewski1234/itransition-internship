import json
import os
import re
import sqlite3

from groq.types.chat.chat_completion_tool_param import ChatCompletionToolParam
import pandas as pd
import streamlit as st
from groq import Groq, Omit
from datasets import loadAllDatasets, getStores
from typing import Iterable

def establish_connection():
    connection = sqlite3.connect(":memory:", check_same_thread = False)
    connection.row_factory = sqlite3.Row
    return connection

def create_database(STORE:str):
    connection = establish_connection()
    for dataset in loadAllDatasets(STORE):
        dataset.to_sql(dataset.df_name, connection, if_exists="replace", index=False)
    connection.execute("PRAGMA query_only = ON")
    return connection

def refactor_query(query:str):
    query = query.strip()
    print(query)
    if not query:
        return query
    return query

def execute_refactored(connection, query:str):
    cursor = connection.execute(refactor_query(query))
    return {
        "columns": [column[0] for column in cursor.description or []],
        "rows": [dict(row) for row in cursor.fetchmany(200)]
    }

def execute_sql_query(connection, query):
    try:
        return execute_refactored(connection, query)
    except sqlite3.Error as error:
        return {"error": str(error)}

def reset_chat():
    st.session_state.ai_chat_messages = []
    st.session_state.store = None
    st.session_state.ai_chat_db = None



SCHEMA_INFO = "\n".join(f"{dataset.df_name}: {dataset.columns}" for dataset in loadAllDatasets(getStores()[0]))

TOOLS: Iterable[ChatCompletionToolParam] | None | Omit = [
        {
            "type": "function",
            "function": {
                "name": "execute_sql_query",
                "description": f"Run a read-only SQL SELECT query against loaded datasets.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                    "additionalProperties": False
                }
            }
        }
    ]

def setup():
    if "ai_chat_messages" not in st.session_state:
        st.session_state.ai_chat_messages = []
    if "ai_chat_db" not in st.session_state or st.session_state.ai_chat_db is None:
        try:
            st.session_state.ai_chat_db = create_database(st.session_state.storeRE)
        except Exception as error:
            st.error(f"Could not load datasets: {error}")
            return

def draw_messages():
    for message in st.session_state.ai_chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def init_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return Groq()
    return Groq(api_key = api_key)

@st.dialog("AI Chat", width = "large", position = "right", on_dismiss = reset_chat)
def show_chat(STORE:str):
    st.session_state.store = STORE
    setup()
    draw_messages()

    prompt = st.chat_input("Ask about books, orders or users")
    st.session_state.ai_chat_messages.append({"role": "user", "content": prompt})

    MESSAGES = get_messages()

    client = init_groq()
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model = "openai/gpt-oss-120b",
            messages = MESSAGES,
            tools = TOOLS,
            tool_choice = "auto"
        )

        assistant_message = response.choices[0].message

        while assistant_message.tool_calls:
            MESSAGES.append({
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

                MESSAGES.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str)
                })

            response = client.chat.completions.create(
                model = "openai/gpt-oss-120b",
                messages = MESSAGES,
                tools = TOOLS,
                tool_choice = "auto"
            )

            assistant_message = response.choices[0].message

        answer = assistant_message.content or "I couldn't generate a response."
        st.markdown(answer)
        st.session_state.ai_chat_messages.append({
            "role": "assistant",
            "content": answer
        })

def get_messages():
    return [
        {
            "role": "system",
            "content": (
                "Answer questions using the books, orders and users datasets. "
                "Use execute_sql_query when data is needed. "
                "Infer table and column names from SQL errors when necessary. "
                "Never invent query results. "
                "Only request read-only SELECT queries."
                "Do NOT explain your thought process."
                f"\nSchema info for datasets: {SCHEMA_INFO}"
            )
        },
        *st.session_state.ai_chat_messages
    ]
