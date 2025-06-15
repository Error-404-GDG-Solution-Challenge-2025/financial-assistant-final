from google.adk.agents import LlmAgent
from google.adk.tools import google_search

# Web Search Agent
web_search_agent = LlmAgent(
    name="web_search_agent",
    model="gemini-2.0-flash-exp",
    description="Performs web searches and extracts key information",
    instruction="""You are a web search and information extraction specialist. Your job is to:
    1. Read the search queries from state['search_queries']
    2. For each query, use the google_search tool to find relevant information
    3. Extract and compile the most important facts, data, and insights from the search results
    4. For each piece of information, note the source website link
    
    Format your findings clearly, organizing them by search query.
    Be thorough but focus on quality over quantity.
    """,
    tools=[google_search],  # Use the Google Search tool
    output_key="search_results"  # Store the results in session state
)