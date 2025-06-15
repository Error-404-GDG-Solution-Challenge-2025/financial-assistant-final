from google.adk.agents import LlmAgent
from google.adk.tools import google_search
# Content Analysis Agent
content_analysis_agent = LlmAgent(
    name="content_analysis_agent",
    model="gemini-2.0-flash-exp",
    description="Analyzes search results and extracts key insights",
    instruction="""You are a content analyst. Your job is to:
    1. Read the search results from state['search_results']
    2. Identify the most important facts, concepts, and insights
    3. Look for common themes and contradicting information
    4. Evaluate the credibility of sources and information
    5. Create a structured analysis of the findings and a plan of research that will be followed sequentially
    
    Organize your analysis into sections:
    - Key Facts and Findings
    - Main Concepts and Ideas
    - Conflicting Information (if any)
    - Areas Needing Further Research
    """,
    output_key="content_analysis",
    tools=[google_search]  # Store the analysis in session state
)
