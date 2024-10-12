import streamlit as st
import yfinance as yf
import openai
import sqlite3
import os
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set the OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize SQLite Database for logging
conn = sqlite3.connect('user_logs.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_query TEXT,
        response TEXT,
        feedback TEXT,
        timestamp TEXT
    )
''')
conn.commit()

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to log queries and responses
def log_query_response(user_query, response, feedback=None):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO logs (user_query, response, feedback, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_query, response, feedback, timestamp))
    conn.commit()

# Function to fetch ETF data
def get_etf_data(ticker):
    etf = yf.Ticker(ticker)
    growth = etf.info.get('trailingPE', 'N/A')
    value = etf.info.get('priceToBook', 'N/A')
    dividend = etf.info.get('dividendYield', 'N/A')
    return {
        "Growth (PE Ratio)": growth,
        "Value (Price to Book)": value,
        "Dividend Yield (%)": dividend * 100 if dividend != 'N/A' else dividend
    }

# Function to interact with OpenAI for natural language queries
def interpret_query(query):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Interpret the following query and fetch ETF data: {query}",
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Streamlit App Layout
st.title("ETF Search and Analysis")

# Get ETF ticker from user
ticker = st.text_input("Enter ETF ticker symbol (e.g., SPY, QQQ):").upper()

# Search for ETF data
if st.button("Search ETF"):
    if ticker:
        data = get_etf_data(ticker)
        st.write(f"### {ticker} Information")
        st.write(f"1. **Growth (PE Ratio)**: {data['Growth (PE Ratio)']}")
        st.write(f"2. **Value (Price to Book)**: {data['Value (Price to Book)']}")
        st.write(f"3. **Dividend Yield (%)**: {data['Dividend Yield (%)']}")
    else:
        st.error("Please enter a valid ETF ticker symbol")

# Ask a natural language question about an ETF
st.write("### Ask a question about an ETF:")
user_query = st.text_input("Enter your question (e.g., 'What is the growth rate of SPY?')")
if st.button("Submit Query"):
    response = interpret_query(user_query)
    st.write(f"Answer: {response}")
    
    # Feedback options
    st.write("### Did you like this response?")
    thumbs_up = st.button("👍")
    thumbs_down = st.button("👎")

    # Log feedback
    if thumbs_up:
        log_query_response(user_query, response, 'thumbs_up')
        st.success("You liked this response!")
    elif thumbs_down:
        log_query_response(user_query, response, 'thumbs_down')
        st.error("You disliked this response.")
