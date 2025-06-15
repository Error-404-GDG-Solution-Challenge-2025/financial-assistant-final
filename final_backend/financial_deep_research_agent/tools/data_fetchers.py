from typing import Dict, List, Any
import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# API keys for financial data services
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")

def fetch_financial_data(query: str) -> Dict[str, Any]:
    """
    General-purpose financial data fetcher that routes to specific fetchers
    based on the query.
    
    Args:
        query: The financial data query
        
    Returns:
        Dict containing the fetched financial data
    """
    # Implement routing logic to specific fetchers
    if "stock" in query.lower() or "price" in query.lower():
        return fetch_stock_prices(query)
    elif "economic" in query.lower() or "indicator" in query.lower():
        return fetch_economic_indicators(query)
    elif "news" in query.lower():
        return fetch_financial_news(query)
    else:
        # Default to market data
        return fetch_market_data(query)

def fetch_stock_prices(ticker: str) -> Dict[str, Any]:
    """
    Fetches stock price data for a given ticker.
    
    Args:
        ticker: The stock ticker symbol
        
    Returns:
        Dict containing stock price data
    """
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    # Process and return the data
    return {
        "status": "success" if "Time Series (Daily)" in data else "error",
        "data": data.get("Time Series (Daily)", {}),
        "metadata": data.get("Meta Data", {})
    }

def fetch_market_data(query: str) -> Dict[str, Any]:
    """
    Fetches general market data based on the query.
    
    Args:
        query: The market data query
        
    Returns:
        Dict containing market data
    """
    # Implement market data fetching logic
    # This could include indices, sector performance, etc.
    url = f"https://financialmodelingprep.com/api/v3/quote/^GSPC,^DJI,^IXIC?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    return {
        "status": "success" if data else "error",
        "data": data,
        "query": query
    }

def fetch_economic_indicators(indicator: str) -> Dict[str, Any]:
    """
    Fetches economic indicator data.
    
    Args:
        indicator: The economic indicator to fetch
        
    Returns:
        Dict containing economic indicator data
    """
    # Map common indicator terms to API parameters
    indicator_map = {
        "gdp": "GDP",
        "inflation": "INFLATION",
        "unemployment": "UNEMPLOYMENT",
        "interest": "FEDERAL_FUNDS_RATE"
    }
    
    # Find the appropriate indicator code
    indicator_code = None
    for key, value in indicator_map.items():
        if key in indicator.lower():
            indicator_code = value
            break
    
    if not indicator_code:
        indicator_code = "GDP"  # Default
    
    url = f"https://financialmodelingprep.com/api/v4/economic?name={indicator_code}&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    return {
        "status": "success" if data else "error",
        "data": data,
        "indicator": indicator_code
    }

def fetch_financial_news(query: str) -> Dict[str, Any]:
    """
    Fetches financial news related to the query.
    
    Args:
        query: The news query
        
    Returns:
        Dict containing financial news
    """
    url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={query}&limit=50&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    return {
        "status": "success" if data else "error",
        "data": data,
        "query": query
    }
