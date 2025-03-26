# run.py

from ingest import vector_store # Assuming this initializes and returns a Chroma/FAISS etc. vector store
from agno.agent import Agent
from agno.knowledge.langchain import LangChainKnowledgeBase
# Use centralized LLM providers
from vars import (
    get_llm_id, get_llm_provider,
    MAX_SEARCH_CALLS, MAX_DEPTH, VECTOR_STORE_PATH
)
from agno.tools.yfinance import YFinanceTools
# Import graders and summarizer
from retrieval_grader import retrieval_grader, small_talk_grader
from deep_research import DeepResearch
from summarizer import summarize # Import the refined summarize function
from tavily import TavilyClient

import os
from dotenv import load_dotenv
from rich.console import Console
from termcolor import colored
from langchain.memory import ConversationBufferMemory # Import memory
from langchain_core.messages import SystemMessage
from langchain.prompts import PromptTemplate

from retrieval_grader import YesNoParser 

load_dotenv()
console = Console()

# --- Initialize Tools ---
tavily_api_key = os.environ.get("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables.")
tavily_client = TavilyClient(api_key=tavily_api_key)

yf_tool = YFinanceTools(
    stock_price=True,
    analyst_recommendations=True,
    stock_fundamentals=True,
    # historical_prices=False, # Keep focused
    company_info=True,
    # company_news=False # Use Tavily for news
)
# Add .name attribute if Agno tools don't have it, needed for display
if not hasattr(yf_tool, 'name'): yf_tool.name = "YFinanceTools"
if not hasattr(tavily_client, 'name'): tavily_client.name = "TavilySearch"


researcher = DeepResearch(max_search_calls=MAX_SEARCH_CALLS, max_depth=MAX_DEPTH)

# --- Initialize Knowledge Base ---
# Ensure vector_store is loaded correctly (adjust path if needed)
# Example assumes vector_store is ready from ingest.py
try:
    # retriever = vector_store.as_retriever(search_kwargs={'k': 3}) # Retrieve top 3 docs
    # Assuming ingest.vector_store is the ready-to-use store object
     retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
except Exception as e:
    print(colored(f"Error initializing vector store/retriever: {e}", "red"))
    print(colored("Knowledge base retrieval will be unavailable.", "yellow"))
    retriever = None

knowledge_base = LangChainKnowledgeBase(retriever=retriever) if retriever else None

# --- Initialize LLMs ---
main_llm = get_llm_provider(get_llm_id("remote"))
tool_llm = get_llm_provider(get_llm_id("tool")) # Potentially specific model for tool calls

# --- Helper Function for Tool Call Display ---
def display_tool_calls(tool_calls):
    """Display tool calls in a formatted way (simplified)"""
    print(colored("\n--- Tool Call History ---", "cyan"))
    if not tool_calls:
        print(colored("No tool calls recorded for this step.", "yellow"))
        return

    # Adapt based on the actual structure of tool_calls from Agno agent
    for i, call in enumerate(tool_calls, 1):
         print(colored(f"Call #{i}:", "yellow"))
         # Try common attributes, adjust as needed for Agno's structure
         tool_name = getattr(call, 'tool', call.get('name', 'Unknown Tool'))
         tool_input = getattr(call, 'tool_input', call.get('arguments', call.get('input', {})))
         tool_output = getattr(call, 'tool_output', call.get('output', 'N/A'))

         print(colored(f"  Tool: {tool_name}", "green"))
         print(colored(f"  Input: {tool_input}", "blue"))
         print(colored(f"  Output: {str(tool_output)[:300]}...", "magenta")) # Truncate long outputs
    print(colored("--- End Tool Call History ---\n", "cyan"))


# --- Core Processing Function ---
def process_query_flow(query: str, memory: ConversationBufferMemory, deep_search: bool = False) -> str:
    """
    Processes the user query through RAG, Web Search/Deep Research, and Synthesis.
    Uses provided memory object.
    """
    print(colored(f"\nProcessing Query: '{query}' (Deep Search: {deep_search})", "white", attrs=["bold"]))
    final_answer = ""
    rag_context = ""
    web_research_context = ""
    tool_calls_history = [] # Collect tool calls across steps

    # === 1. Small Talk Check ===
    try:
        small_talk_result = small_talk_grader.invoke({"question": query})
        if small_talk_result.get("is_small_talk"):
            print(colored("Query identified as small talk.", "yellow"))
            # Use a simple conversational response (can use LLM for variety)
            conv_agent = Agent(model=main_llm, description="You are a friendly assistant.", memory=memory)
            response = conv_agent.run(f"Respond conversationally to: {query}")
            return response.content
    except Exception as e:
        print(colored(f"Error during small talk check: {e}", "red"))
        # Proceed assuming it's not small talk

    # === 2. RAG Retrieval ===
    retrieved_docs_content = "No documents found or knowledge base unavailable."
    if knowledge_base:
        try:
            print(colored("Attempting RAG retrieval...", "cyan"))
            # Use knowledge base directly, Agno agent might do this internally too
            retrieved_docs = knowledge_base.search(query) # Get List[Dict]
            if retrieved_docs:
                retrieved_docs_content = "\n\n".join([doc.get("content", "") for doc in retrieved_docs])
                print(colored(f"Retrieved {len(retrieved_docs)} snippets from knowledge base.", "green"))
                # print(colored(retrieved_docs_content[:500] + "...", "yellow")) # Print snippet preview
            else:
                print(colored("No relevant documents found in knowledge base.", "yellow"))
        except Exception as e:
            print(colored(f"Error during RAG retrieval: {e}", "red"))
            retrieved_docs_content = "Error retrieving documents from knowledge base."
    else:
        print(colored("Knowledge base not available, skipping RAG.", "yellow"))


    # === 3. Relevance Grading ===
    grade = 0 # Default to not relevant
    if knowledge_base and retrieved_docs: # Only grade if docs were found
        try:
            print(colored("Grading retrieved documents...", "cyan"))
            grade_result = retrieval_grader.invoke({"question": query, "documents": retrieved_docs_content})
            grade = grade_result.get('score', 0)
            print(colored(f"Retrieval grade: {grade}", 'magenta'))
            if grade == 1:
                rag_context = retrieved_docs_content # Use RAG context if relevant
            else:
                print(colored("Documents deemed not relevant or real-time data needed.", "yellow"))
                rag_context = "" # Discard irrelevant RAG context
        except Exception as e:
            print(colored(f"Error during retrieval grading: {e}", "red"))
            rag_context = "" # Discard context on error

    # === 4. Web Search / Deep Research ===
    # Perform this step UNLESS RAG was perfect AND no real-time data needed (hard to determine perfectly, so often do it)
    # Simplification: Always do web search/deep research unless RAG grade is 1 AND query seems purely conceptual.
    # Let's implement a check: Does the query ask for current data/prices?
    needs_realtime_check_prompt = PromptTemplate(
        template="Does the following question ask for current, real-time information like stock prices, latest news, or current market conditions? Answer YES or NO in a JSON object {{'score': YES/NO}}.\n\nQuestion: {question}",
        input_variables=["question"]
    )
    print(colored("Checking for real-time data need...", "cyan"))
    realtime_check_llm = get_llm_provider(get_llm_id("remote"), framework="langchain")
    needs_realtime_parser = YesNoParser() # Re-use the parser
    needs_realtime_chain = needs_realtime_check_prompt | realtime_check_llm | needs_realtime_parser

    needs_realtime = True # Default to assuming real-time might be needed
    try:
         needs_realtime_result = needs_realtime_chain.invoke({"question": query})
         needs_realtime = needs_realtime_result.get("is_small_talk") # Reusing parser, key is misleading here
         print(colored(f"Needs real-time data check: {needs_realtime}", "cyan"))
    except Exception as e:
         print(colored(f"Error checking for real-time need: {e}", "red"))

    # Decide whether to perform web search/deep research
    perform_web_step = True
    if grade == 1 and not needs_realtime:
        print(colored("Relevant RAG found and no real-time data needed. Potentially skipping web search.", "green"))
        # We could skip here, but combining often yields better results. Let's proceed.
        # perform_web_step = False # Uncomment to skip web search in this specific case

    if perform_web_step:
        if deep_search:
            # --- Deep Research Path ---
            print(colored("Initiating Deep Research...", 'magenta'))
            try:
                research_result = researcher.research(query)
                web_research_context = research_result.get("answer", "Deep research failed to produce an answer.")
                # Potentially extract tool calls if DeepResearch class logs them
                # tool_calls_history.extend(researcher.get_tool_calls()) # If implemented
                print(colored("Deep Research completed.", "green"))
            except Exception as e:
                print(colored(f"Error during Deep Research: {e}", "red"))
                web_research_context = f"Deep research encountered an error: {str(e)}"
        else:
            # --- Standard Web Search Path ---
            print(colored("Initiating Web Search using Tavily/YFinance...", 'magenta'))
            # Use a dedicated agent for web search + tools
            web_search_agent = Agent(
                model=tool_llm, # Use the tool-focused LLM
                # memory=memory, # Pass memory for context
                description="""You are a Financial Assistant specialized in retrieving real-time and web-based information.
                Your primary goal is to answer the user's query using the provided tools (Tavily Search, YFinance).

                Instructions:
                1. Analyze the query: {query}
                2. Determine if real-time financial data (stock price, fundamentals) is needed. If yes, use yf_tool. Extract tickers/company names accurately.
                3. Determine if recent news, general information, or broader context is needed. If yes, use tavily_client. Formulate a concise search query.
                4. Execute the necessary tool calls. You MUST call the tools; do not just mention them.
                5. If multiple stocks are mentioned, call yf_tool for each.
                6. Synthesize the results from the tool calls into a factual answer to the original query.
                7. If a tool fails, report that it failed but try to answer with other available information.
                8. Respond *only* with the synthesized answer. Do not include descriptions of tool calls in the final output.
                Current time: {current_datetime}
                """,
                markdown=True,
                search_knowledge=False, # Don't use RAG within this agent
                tools=[tavily_client, yf_tool], # Pass tool instances
                show_tool_calls=True, # Enable logging within Agno if it supports it
                add_datetime_to_instructions=True,
                # max_iterations=5 # Limit iterations to prevent loops
                # error_handler=lambda e: print(f"Web search agent error: {e}") # Basic error handler
            )
            try:
                # Pass query with memory context (Agno might handle memory implicitly if passed at init)
                # response = web_search_agent.run(query) # Check Agno docs for memory usage
                # If memory needs explicit passing in run:
                history = memory.load_memory_variables({})["chat_history"]
                response = web_search_agent.run(query, chat_history=history)

                web_research_context = response.content
                print(colored(f"Web Search Response: {web_research_context}", "magenta"))
                # Try to get tool calls if Agno agent provides a method
                # if hasattr(web_search_agent, 'get_tool_call_history'):
                #     calls = web_search_agent.get_tool_call_history()
                #     tool_calls_history.extend(calls)
                    # display_tool_calls(calls) # Display calls from this step
                print(colored("Web Search completed.", "green"))
            except Exception as e:
                print(colored(f"Error during Web Search Agent execution: {str(e)}", "red"))
                web_research_context = f"Web search encountered an error: {str(e)}"
                # Log the exception traceback for debugging if needed
                import traceback
                traceback.print_exc()


    # === 5. Synthesis ===
    print(colored("Synthesizing final answer...", "cyan"))
    synthesis_agent = Agent(
        model=main_llm,
        # memory=memory, # Pass memory for conversational context
        description="""You are a Financial Analyst Synthesizer. Your task is to combine information from different sources (internal knowledge, web research) into a single, comprehensive, and accurate answer to the user's query.

        Instructions:
        1. Review the original user query: {query}
        2. Review the information retrieved from the internal knowledge base (RAG): {rag_context}
        3. Review the information gathered from web search or deep research: {web_research_context}
        4. Synthesize these pieces of information into a single, cohesive response.
        5. Prioritize accuracy and relevance to the original query.
        6. If both sources provide relevant information, integrate them smoothly. If one source is clearly more relevant or up-to-date (e.g., web search for real-time data), give it appropriate weight.
        7. If RAG context exists, mention that the information is based on available documents and supplement/verify with web findings.
        8. If numerical data (prices, metrics) is available from web/tools, include it accurately.
        9. Structure the answer clearly using Markdown (headings, bullets).
        10. If neither source provided a good answer, state that you couldn't find the information.
        11. Respond directly to the user. Do not mention the internal steps (RAG, web search) unless clarifying the source of information.
        """,
        markdown=True,
        # search_knowledge=False # Synthesis step doesn't need further searching
    )

    try:
        # Prepare context for the synthesis prompt
        synthesis_prompt_input = f"""Original Query: {query}

        --- Information from Knowledge Base ---
        {rag_context if rag_context else "No relevant information found in internal documents."}

        --- Information from Web/Deep Research ---
        {web_research_context if web_research_context else "No information gathered from web search or deep research."}

        ---

        Synthesize the above information to answer the original query comprehensively and accurately.
        """
        # Pass history if needed by Agno agent run method
        history = memory.load_memory_variables({})["chat_history"]
        final_response = synthesis_agent.run(synthesis_prompt_input, chat_history=history)
        final_answer = final_response.content

    except Exception as e:
        print(colored(f"Error during final synthesis: {e}", "red"))
        final_answer = f"Sorry, I encountered an error while synthesizing the final answer: {str(e)}"

    # Display all collected tool calls at the end (optional)
    # print(colored("\n=== Full Tool Call Summary ===", "blue"))
    # display_tool_calls(tool_calls_history)

    print(colored("Processing complete.", "white", attrs=["bold"]))
    return final_answer
