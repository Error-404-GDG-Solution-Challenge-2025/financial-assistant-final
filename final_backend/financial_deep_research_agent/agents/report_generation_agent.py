# Report Generation Agent
from google.adk.agents import LlmAgent

report_generation_agent = LlmAgent(
    name="report_generation_agent",
    model="gemini-2.0-flash-exp",
    description="Creates a comprehensive research report",
    instruction="""You are a research report writer. Your job is to:
    1. Read the original research topic from the user's query
    2. Read the content analysis from state['content_analysis']
    3. Create a comprehensive, well-structured research report that addresses the original topic
    
    Your report should include:
    - Executive Summary: A brief overview of the main findings
    - Introduction: Context and background on the topic
    - Main Findings: Detailed presentation of the research results
    - Analysis: Interpretation of what the findings mean
    - Conclusion: Summary of key takeaways
    - Sources: Citation of all sources used with the links
    
    Make the report professional, clear, and informative.
    """,
    # No output_key needed since this is the final output
)