# Core ADK components
from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent, ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Tools
from google.adk.tools import google_search

# Content types for messages
from google.genai import types

# For file saving
import os
import re
import datetime
import asyncio

# Optional: For debugging
import logging
logging.basicConfig(level=logging.INFO)
from agents.orchestrator import main_agent

# Query Formulation Agent
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
    output_key="search_queries"  # Store the queries in session state
)


# # Web Search Agent
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

# # Content Analysis Agent
content_analysis_agent = LlmAgent(
    name="content_analysis_agent",
    model="gemini-2.0-flash-exp",
    description="Analyzes search results and extracts key insights",
    instruction="""You are a content analyst. Your job is to:
    1. Read the search results from state['search_results']
    2. Identify the most important facts, concepts, and insights
    3. Look for common themes and contradicting information
    4. Evaluate the credibility of sources and information
    5. Create a structured analysis of the findings
    
    Organize your analysis into sections:
    - Key Facts and Findings
    - Main Concepts and Ideas
    - Conflicting Information (if any)
    - Areas Needing Further Research
    """,
    output_key="content_analysis"  # Store the analysis in session state
)


# # Report Generation Agent
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


# # Create the Sequential Agent that combines all sub-agents
research_assistant = LoopAgent(
    name="research_assistant",
    description="A comprehensive research assistant that finds and analyzes information on topics",
    sub_agents=[
        query_formulation_agent,
        web_search_agent,
        content_analysis_agent,
        report_generation_agent
    ],
    max_iterations=5
)
# Set up session management
session_service = InMemorySessionService()

async def research_topic(topic, show_intermediate=True, save_report=True):
    """
    Call the research assistant to research a topic and return the final report.
    
    Args:
        topic (str): The research topic to investigate
        show_intermediate (bool): Whether to show intermediate outputs from each agent
    
    Returns:
        str: The final research report
    """
    print(f"Researching topic: '{topic}'")
    print("This may take some time as it involves multiple steps...\n")
    
    # Create user message
    user_message = types.Content(
        role='user',
        parts=[types.Part(text=f"Please research this topic: {topic}")]
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="research_assistant",
        user_id="user1234",
        session_id="research_session_123"
    )
    
    # Create a runner to execute the agent
    runner = Runner(
        agent=main_agent,
        app_name="research_assistant",
        session_service=session_service
    )
    
    # Track which agent is currently running
    current_agent = None
    final_report = None
    
    # Run the agent and show intermediate results if requested
    events = runner.run(
        user_id="user1234",
        session_id="research_session_123",
        new_message=user_message
    )
    
    for event in events:
        # Detect when a new agent starts
        if show_intermediate and event.author != current_agent:
            current_agent = event.author
            print(f"\n----- Now running: {current_agent} -----")
        if session and hasattr(current_session, 'state'):
            try:
                print(f"SEARCH QUERIES: {list(session.state['search_queries'])}")
                print(f"PLAN : {list(session.state['content_analysis'])}")
            except Exception as e:
                print(f"Error accessing session state: {e}")

        # Show final response from each sub-agent
        if show_intermediate and event.is_final_response() and event.author != "research_assistant":
            print(f"\n===== Output from {event.author} =====")
            if event.content and event.content.parts:
                print(event.content.parts[0].text[:500] + "..." if len(event.content.parts[0].text) > 500 else event.content.parts[0].text)
                print("\n")
                
                # Also show the state update
                if event.author == "query_formulation_agent":
                    print("Search queries saved to state.")
                elif event.author == "web_search_agent":
                    print("Search results saved to state.")
                elif event.author == "content_analysis_agent":
                    print("Content analysis saved to state.")
        if event.is_final_response():
            final_report = event.content.parts[0].text
    print("\n" + "="*50)
    print("FINAL RESEARCH REPORT")
    print("="*50 + "\n")
    print(final_report)
        
        # Process final overall response
    if save_report and final_report:
            # Sanitize the topic for a filename
            clean_topic = re.sub(r'[^\w\s-]', '', topic)
            clean_topic = re.sub(r'[\s-]+', '_', clean_topic).strip('_')
            clean_topic = clean_topic[:30]  # Limit length for filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_base = f"research_report_{clean_topic}_{timestamp}"
            
            # Create reports directory if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            # Save as text file
            filename = os.path.join("reports", f"{filename_base}.md")
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"RESEARCH REPORT: {topic}\n")
                    f.write("="*50 + "\n\n")
                    f.write(final_report)
                print(f"\nReport saved as: {filename}")
            except Exception as e:
                print(f"\nError saving report to text file: {e}")
    print("\n" + "="*50)
    print("FINAL SESSION STATE")
    print("="*50)
    current_session = await session_service.get_session(
        app_name="research_assistant",
        user_id="user1234",
        session_id="research_session_123"
    )
  
  # Display state keys
    if current_session and hasattr(current_session, 'state'):
        print("State keys:", list(current_session.state.keys()))

if __name__ == "__main__":
    topic = "The impact of trumps tariff on world econmony in 2025"
    asyncio.run(research_topic(topic, show_intermediate=True, save_report=True))