from google.adk.agents import LlmAgent
from tools.data_fetchers import fetch_market_data, fetch_stock_prices

market_data_agent = LlmAgent(
    name="market_data_agent",
    model="gemini-2.0-flash",
    description="Retrieves and analyzes financial market data",
    instruction="""
    You are a market data specialist. Your role is to:
    1. Retrieve relevant market data based on the research query
    2. Analyze price trends, trading volumes, and market indicators
    3. Identify significant patterns and anomalies
    4. Provide context on market conditions
    
    Focus on delivering accurate, data-driven insights about financial markets.
    """,
    tools=[fetch_market_data, fetch_stock_prices]
)
