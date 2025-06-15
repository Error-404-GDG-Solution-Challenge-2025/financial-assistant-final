from google.adk.agents import Agent

from tools.data_fetchers import fetch_financial_news
from google.adk.tools import google_search
news_analysis_agent = Agent(
    name="news_analysis_agent",
    model="gemini-2.5-flash-preview",
    description="Analyzes financial news and sentiment",
    instruction="""
    You are a financial news analyst. Your role is to:
    1. Retrieve relevant financial news based on the research query
    2. Analyze news sentiment and its market impact
    3. Identify emerging trends and events
    4. Provide context on news-driven market movements
    
    Focus on delivering insights on how news affects financial markets.
    """,
    tools=[fetch_financial_news, google_search]
)
