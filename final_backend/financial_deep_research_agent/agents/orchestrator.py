from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search, agent_tool

from agents.market_data_agent import market_data_agent
from agents.economic_analysis_agent import economic_analysis_agent
from agents.news_analysis_agent import news_analysis_agent
from agents.output_formatter_agent import output_formatter_agent
from agents.query_formulation_agent import query_formulation_agent
from agents.web_search_agent import web_search_agent
from agents.content_analysis_agent import content_analysis_agent
from agents.report_generation_agent import report_generation_agent

from tools.data_fetchers import fetch_financial_data
from dotenv import load_dotenv
load_dotenv()

# Define the orchestrator agent
orchestrator_agent = SequentialAgent(
    name="financial_research_orchestrator",
    description="""
    You are a financial research orchestrator. Your role is to:
    1. Analyze the user's financial research query using content_analysis_agent
    2. Break it down into specific research tasks using query_formulation_agent
    3. Pass down the tasks to the subsequent agents
   
    
    Ensure thorough research by continuing iterations until the topic is fully explored.
    """,
    # tools=[agent_tool.AgentTool(agent=web_search_agent), fetch_financial_data]
    sub_agents=[content_analysis_agent, query_formulation_agent] 
)

# Create the Sequential Agent that combines all sub-agents
# research_assistant = ParallelAgent(
#     name="research_assistant",
#     description="A comprehensive research assistant that finds and analyzes information on topics",
#     # sub_agents=[
#     #     query_formulation_agent,
#     #     web_search_agent,
#     #     content_analysis_agent,
#     #     report_generation_agent
#     # ],
#     tools=[agent_tool.AgentTool(agent=query_formulation_agent), agent_tool.AgentTool(agent=web_search_agent),agent_tool.AgentTool(agent=content_analysis_agent), agent_tool.AgentTool(agent=report_generation_agent)]
# )

# Define the research loop agent
research_loop_agent = LoopAgent(
    name="financial_research_loop",
    description="""
    1. Coordinate specialized agents to perform the tasks created by query_formulation_agent using content_analysis_agent, economic_analysis_agent, market_data_agent, news_analysis_agent and web_search_agent
    2. Synthesize their findings into a comprehensive response using report_generation_agent
    3. Continue iterations until the research topic is fully explored
""",
    sub_agents=[
        ParallelAgent(
            name="research_sequence",
            description="""
            1. If market data is needed in order to answer the query, use market_data_agent to fetch and analyze financial market data
            2. If economic analysis and/or investment strategy is needed, use economic_analysis_agent to analyze economic indicators and trends
            3. If recent or historical financial news analysis is needed, use news_analysis_agent to analyze financial news 
            4. For any other web search tasks, use web_search_agent to find relevant information
""",
            sub_agents=[
                # research_assistant,
                web_search_agent,
                market_data_agent,
                economic_analysis_agent,
                news_analysis_agent
            ]
        )
    ],
    max_iterations=2  # Can be adjusted based on research depth requirements
)

# Define the main agent workflow
main_agent = SequentialAgent(
    name="financial_research_workflow",
    description="Coordinates the entire financial research workflow step by step and finally formats the output using output_formatter_agent",
    sub_agents=[
        orchestrator_agent,
        research_loop_agent,
        output_formatter_agent
    ]
)
