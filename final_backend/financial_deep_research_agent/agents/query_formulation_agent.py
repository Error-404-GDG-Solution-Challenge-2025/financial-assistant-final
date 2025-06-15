from google.adk.agents import LlmAgent
from google.adk.tools import google_search

query_formulation_agent = LlmAgent(
    name="query_formulation_agent",
    model="gemini-2.0-flash-exp",  # Using a capable Gemini model
    description="Creates effective search queries based on the research topic",
    instruction="""You are a query formulation expert. Your job is to:
    1. Analyze the user's research topic
    2. Break it down into 3-5 specific, effective search queries that will yield the most relevant information
    3. For each query, add a brief explanation of what information you're trying to find
    
    Format your response as a numbered list of queries, with each query on a separate line.
    Don't include any other text in your response besides the numbered queries and their explanations.
    """,
    tools=[google_search],
    output_key="search_queries"  # Store the queries in session state
)