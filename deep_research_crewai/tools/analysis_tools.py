from typing import Dict, Any
import pandas as pd
import numpy as np
from crewai.tools import tool

@tool("analyze_investment_opportunity_tool")
def analyze_investment_opportunity(ticker: str, time_period: str = "1y") -> Dict[str, Any]:
    """
    Analyzes an investment opportunity for a given ticker using yfinance data.
    
    Args:
        ticker: The stock ticker symbol
        time_period: Time period for analysis (e.g., "1m", "3m", "1y")
        
    Returns:
        Dict containing investment analysis
    """
    import yfinance as yf
    from google.adk.tools import google_search
    
    # Fetch stock data
    stock = yf.Ticker(ticker)
    hist = stock.history(period=time_period)
    
    # Calculate key metrics
    current_price = hist['Close'][-1]
    avg_price = hist['Close'].mean()
    volatility = hist['Close'].pct_change().std() * np.sqrt(252)
    
    # Get company info
    info = stock.info
    pe_ratio = info.get('trailingPE', None)
    dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
    beta = info.get('beta', 1.0)
    market_cap = info.get('marketCap', 0)
    
    # Calculate risk level
    if volatility < 0.15:
        risk_level = "low"
    elif volatility < 0.25:
        risk_level = "medium"
    else:
        risk_level = "high"
    
    # Calculate potential return
    price_change = (current_price - hist['Close'][0]) / hist['Close'][0] * 100
    if price_change > 10:
        potential_return = "high"
    elif price_change > 0:
        potential_return = "moderate"
    else:
        potential_return = "low"
    
    # Generate recommendation
    if pe_ratio and pe_ratio < 15 and price_change > 0:
        recommendation = "buy"
    elif price_change < -10:
        recommendation = "sell"
    else:
        recommendation = "hold"
    
    # Search for recent news
    news_query = f"{ticker} stock news analysis"
    news_results = google_search(news_query)
    
    return {
        "ticker": ticker,
        "time_period": time_period,
        "analysis": {
            "risk_level": risk_level,
            "potential_return": potential_return,
            "recommendation": recommendation,
            "key_metrics": {
                "pe_ratio": pe_ratio,
                "dividend_yield": dividend_yield,
                "beta": beta,
                "market_cap": market_cap,
                "volatility": volatility,
                "price_change": price_change
            },
            "recent_news": news_results[:3] if news_results else []
        }
    }
