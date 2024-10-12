import streamlit as st
import yfinance as yf
import openai
import sqlite3
import time

# Use Streamlit's secrets management
openai.api_key = st.secrets["OPENAI_API_KEY"]

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
    
    # Some fields may be missing, so we need to handle missing data carefully
    growth = etf.info.get('trailingPE', 'N/A')
    value = etf.info.get('priceToBook', 'N/A')
    dividend = etf.info.get('dividendYield', 'N/A')
    
    # Handle the case where dividend or value is None
    if dividend is not None and dividend != 'N/A':
        dividend_display = dividend * 100  # Convert to percentage
    else:
        dividend_display = 'N/A'

    if value is None or value == 'N/A':
        value_display = 'N/A'
    else:
        value_display = value
    
    return {
        "Growth (PE Ratio)": growth if growth else 'N/A',
        "Value (Price to Book)": value_display,
        "Dividend Yield (%)": dividend_display
    }
    
# Function to interact with OpenAI for natural language queries
def interpret_query(query):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant for analyzing ETFs."},
                {"role": "user", "content": f"Fetch ETF data for this query: {query}"}
            ],
            max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error fetching data from OpenAI: {str(e)}"

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

# Display a section explaining why 'N/A' may appear for certain ETF values
st.write("### Why Some Values Show 'N/A'")
st.write("""
- **Inconsistent Data**: Some ETFs may not report specific financial metrics, such as price-to-book ratio or dividend yield.
- **Data Delays**: There might be delays in updating certain data fields, especially for newly listed ETFs.
- **Not Applicable**: Certain metrics may not be applicable to all ETFs or are harder to calculate compared to individual stocks.
- **API Limitations**: The data available through the Yahoo Finance API may not always include every field, even if it exists on their website.
""")
