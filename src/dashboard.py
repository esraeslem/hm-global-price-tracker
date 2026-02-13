import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from database import DB_PATH

st.set_page_config(page_title="H&M Global Strategy", layout="wide")

def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT p.name, p.article_code, pr.region, pr.price_original, pr.currency, pr.price_in_usd, pr.date_scraped
        FROM prices pr
        JOIN products p ON pr.article_code = p.article_code
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

st.title("🌍 H&M Global Price Intelligence Tracker")
st.markdown("Comparing real-time pricing strategies across Turkey, US, and EU.")

try:
    df = load_data()
    
    if not df.empty:
        # Key Metrics
        avg_price = df.groupby('region')['price_in_usd'].mean().reset_index()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Price Parity (USD Converted)")
            fig = px.bar(avg_price, x='region', y='price_in_usd', color='region', title="Average Dress Price by Region (USD)")
            st.plotly_chart(fig)
            
        with col2:
            st.subheader("Arbitrage Opportunities")
            st.dataframe(df[['name', 'region', 'price_original', 'currency', 'price_in_usd']].sort_values(by='price_in_usd'))

    else:
        st.warning("No data found. Run 'src/collect_data.py' first!")

except Exception as e:
    st.error(f"Database error: {e}. Run 'src/collect_data.py' to initialize.")
