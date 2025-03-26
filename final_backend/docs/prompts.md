I want to build a financial assistant agent that has access to a RAG database and can query relevant documents from it regarding financial topics. then the retrieved documents are graded for relevance with the question asked by the user. If the question asked by the user is satisfactorily answered by the retrieved documents, an Agno agent takes those documents and generates an answer based on those. If the docs are graded as not relevant to the user question or if the user question requires realtime data, it falls back to web search using tavily. If deep research mode is on, it uses the deep research tool instead of the web search agent. The agents have access to tools like tavily and yfinance to get realtime financial data. 

In the deep research module, several subquestions are generated which are relevant in answering the user prompt. Then each of those subquestions are researched on the web using tavily and then it is decided whether that subquestion should be decomposed into further subquestions. If yes, the decomposed subquestions get researched recursively and this goes on till all the subquestions are researched with the help of tavily and yfinance and then a summary of all the research is done and that is the final answer.

But there are several issues that I am facing. They are listed below : 
1. Many tool calls are failing, sometimes the tool call code is getting passed as the final answer
2. In the DeepResearch module, the subquestions that are generated are of poor quality and sometimes unnecessary.  This lengthens the deep research process.
3. In both tavily search, yfinance, and deepresearch, the realtime data of the stock price, company details are not found and summarization is not working properly.
4. The insights from RAG documents are taken solely for generating answers. I need to have the app take insights from the RAG document, web search using tavily on the topic and combine, summarize all of this into a final elaborate report which provides accurate numerical estimations.
5. Sometimes the RAG documents are not really relevant but is being graded as relevant.

There are many other issues besides the above. Fix them all and optimize the app for faster deep research and proper document grading. Also feel free to add any more features that you think this app needs to work beautifully. I am using streamlit as the frontend. The frontend also has issues : 

1. Whenever I press the deep research button, the chat refreshes and all the previous chat is gone.

Some features that need to be added : 
1. There is no memory or context of the previous chat messages between the user and the agent, which can be used to answer follow up questions. Need to build this using local storage solutions provided by langchain
2. Need to store all the chats using local storage solutions provided by langchain.

Implement all of these features and fix all the issues mentioned above. I am providing code to all the required files that are in my project. Rewrite them in order to make all the above changes.


deep_research.py
------------------------------------------
import time
from tavily import TavilyClient
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.groq.groq import Groq
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown
from vars import *
load_dotenv()

console = Console()

tavily_api_key = os.environ.get("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key)


class DeepResearch:
    def __init__(self, max_depth=2, search_calls=0, max_search_calls=5):
        """
        Initialize the DeepResearch class with configurable parameters.

        Args:
            llm_model_id: The ID of the LLM model to use
            max_depth: Maximum recursion depth for deep research
        """
        self.model = Groq(id=REASONING_LLM, temperature=0)
        self.max_depth = max_depth
        self.search_calls = search_calls
        self.max_search_calls = max_search_calls

    def _generate_subquestions(self, query: str, num_questions=3) -> List[str]:
        """Break down a complex query into simpler subquestions."""
        agent = Agent(
            model=self.model,
            description="You are a research expert who breaks down complex questions into simpler subquestions.",
        )

        prompt = f"""
        I need to research the following complex topic: "{query}"
        
        Break this down into {num_questions} specific, focused subquestions that would help comprehensively answer the main question.
        Each subquestion should:
        1. Cover a distinct aspect of the main question
        2. Be specific enough to research effectively
        3. Together with other subquestions, help build a complete answer
        
        Return ONLY the numbered list of subquestions, nothing else.
        """

        response = agent.run(prompt)
        # print("RESPONSE FROM GENERATE SUBQUESTIONS : ", response.content)
        if "<think>" in response.content:
            response.content = response.content.split("</think>")[1].strip()
        raw_subquestions = response.content.strip().split('\n')

        # Clean up the subquestions (remove numbering, etc.)
        subquestions = []
        for q in raw_subquestions:
            # Remove common prefixes like "1. ", "Question 1:", etc.
            cleaned = q.strip()
            if cleaned:
                for prefix in ["- ", "* ", "#. ", ". "]:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):]
                        break
                # Remove numbers at the beginning like "1", "2.", etc.
                if cleaned and cleaned[0].isdigit() and len(cleaned) > 1:
                    if cleaned[1] == '.' or cleaned[1] == ')' or cleaned[1] == ':':
                        cleaned = cleaned[2:].strip()
                    elif cleaned[1].isdigit() and len(cleaned) > 2:
                        if cleaned[2] == '.' or cleaned[2] == ')' or cleaned[2] == ':':
                            cleaned = cleaned[3:].strip()

                # Remove quotes if present
                cleaned = cleaned.strip('"\'')
                if cleaned:
                    subquestions.append(cleaned)

        print(colored(f"Generated {len(subquestions)} subquestions:", "cyan"))
        for idx, q in enumerate(subquestions):
            print(colored(f"  {idx+1}. {q}", "yellow"))

        return subquestions

    def _research_subquestion(self, subquestion: str, depth=0) -> Dict[str, Any]:
        """Research a specific subquestion using Tavily and additional decomposition if needed."""
        print(colored(f"\nResearching: {subquestion}", "green"))

        # Search the web for the subquestion
        search_results = tavily_client.search(
            query=subquestion, search_depth="advanced")
        
        # Extract content from search results
        context = "\n\n".join([r["content"]
                              for r in search_results["results"]])

        # If we haven't reached max depth and the question seems complex enough,
        # we can recursively break it down further
        additional_info = {}
        print(colored(f"CURRENT DEPTH LEVEL: {depth}", "red"))
        print(colored(f"MAX DEPTH: {self.max_depth}", "red"))
        if depth < self.max_depth:
            # Check if this subquestion needs further decomposition
            decompose_agent = Agent(model=self.model)
            decompose_prompt = f"""
            Based on the following subquestion: "{subquestion}"
            And these search results:
            {context}...
            
            Does this topic need further decomposition to be properly researched?
            Answer with just YES or NO.
            """

            decompose_response = decompose_agent.run(decompose_prompt)
            print(colored(f"SEARCH CALLS: {self.search_calls}", "red"))
            print(colored(f"MAX SEARCH CALLS: {self.max_search_calls}", "red"))
            if "YES" in decompose_response.content.upper() and self.search_calls < self.max_search_calls:
                print(
                    colored(f"Further decomposing: {subquestion}", "magenta"))
                sub_subquestions = self._generate_subquestions(
                    subquestion, num_questions=2)

                # Research each sub-subquestion recursively
                sub_findings = {}
                for sub_sq in sub_subquestions:
                    sub_result = self._research_subquestion(
                        sub_sq, depth=depth+1)
                    sub_findings[sub_sq] = sub_result

                additional_info["sub_research"] = sub_findings
                self.search_calls += 1

        summary = self._analyze_findings(subquestion, context, additional_info)

        return {
            "subquestion": subquestion,
            "search_results": search_results,
            "context": context,
            "summary": summary,
            "additional_info": additional_info
        }

    def _analyze_findings(self, subquestion: str, context: str, additional_info: Dict) -> str:
        """Analyze and summarize findings for a specific subquestion."""
        agent = Agent(
            model=self.model,
            description="You are a research analyst who synthesizes information into concise, accurate summaries.",
        )

        # Prepare additional context from sub-research if available
        sub_research_context = ""
        if "sub_research" in additional_info:
            sub_research_context = "Additional research findings:\n"
            for sub_sq, sub_result in additional_info["sub_research"].items():
                sub_research_context += f"\n- About '{sub_sq}':\n{sub_result['summary']}\n"

        prompt = f"""
        Based on research about the question: "{subquestion}"
        
        Main search results:
        {context[:3000]}...
        
        {sub_research_context}
        
        Please provide a comprehensive, well-structured summary that answers the question.
        Focus on factual information, include relevant details, and maintain accuracy.
        Structure your response with clear sections where appropriate.
        """

        response = agent.run(prompt)
        return response.content

    def _synthesize_research(self, main_query: str, research_results: Dict[str, Dict]) -> str:
        """Synthesize all research findings into a cohesive, comprehensive answer."""
        agent = Agent(
            model=self.model,
            description="You are a research synthesizer who creates comprehensive, well-structured reports from multiple sources.",
        )

        # Compile findings from all subquestions
        findings_context = ""
        for subq, result in research_results.items():
            findings_context += f"\n\n## Research on: {subq}\n{result['summary']}"

        prompt = f"""
        I've researched the following question in depth: "{main_query}"
        
        Here are the detailed findings from multiple sub-questions:
        {findings_context}
        
        Please synthesize these findings into a comprehensive, well-structured answer to the original question.
        Your response should:
        1. Be thorough yet concise
        2. Connect insights across different aspects of the research
        3. Present a coherent narrative that fully addresses the original question
        4. Include relevant details, examples, and evidence
        5. Be well-organized with appropriate sections and formatting
        
        Make sure your answer is accurate, nuanced, and addresses all important aspects of the question.
        """

        response = agent.run(prompt)
        return response.content

    def research(self, query: str, num_subquestions: int = 3) -> Dict[str, Any]:
        """
        Execute deep research on a complex query.

        Args:
            query: The complex research query to investigate
            num_subquestions: Number of subquestions to generate

        Returns:
            Dict containing the research process and final answer
        """
        print(colored(
            f"\n=== Starting Deep Research on: {query} ===\n", "blue", attrs=["bold"]))

        # Step 1: Break down into subquestions
        subquestions = self._generate_subquestions(
            query, num_questions=num_subquestions)

        # Step 2: Research each subquestion
        subquestion_results = {}
        for sq in subquestions:
            subquestion_results[sq] = self._research_subquestion(sq)

        # Step 3: Synthesize findings into comprehensive answer
        final_answer = self._synthesize_research(query, subquestion_results)

        print(colored("\n=== Deep Research Complete ===\n",
              "blue", attrs=["bold"]))

        return {
            "query": query,
            "subquestions": subquestions,
            "subquestion_results": subquestion_results,
            "answer": final_answer
        }


----------------------------------------------------------------------

retrieval_grader.py
--------------------------------------------------------------------------


from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
# from langchain_mistralai.chat_models import ChatMistralAI
from vars import *
import os

# LLM
if ENABLE_LOCAL:
    llm = ChatOllama(model=LOCAL_LLM, format="json", temperature=0)
    print("Using local LLM")
else:
    llm = ChatGroq(model=REMOTE_LLM, api_key=os.environ.get('GROQ_API_KEY'), temperature=0)
    print("Using Groq LLM")
# Prompt
prompt_for_retrieval_grading = PromptTemplate(
    template="""You are a teacher grading a quiz. You will be given: 
    1/ a QUESTION
    2/ A FACT provided by the student
    
    You are grading RELEVANCE RECALL:
    A score of 1 means that ANY of the statements in the FACT are relevant to the QUESTION. 
    A score of 0 means that NONE of the statements in the FACT are relevant to the QUESTION OR/AND the QUESTION is asking for realtime information. 
    1 is the highest (best) score. 0 is the lowest score you can give. 
    
    NOTE that if the question is asking about realtime information, the fact may not be relevant.

    Explain your reasoning in a step-by-step manner. Ensure your reasoning and conclusion are correct. 
    
    Avoid simply stating the correct answer at the outset.
    
    Question: {question} \n
    Fact: \n\n {documents} \n\n
    
    Give a binary score '1' or '0' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explanation.
    """,
    input_variables=["question", "documents"],
)

retrieval_grader = prompt_for_retrieval_grading | llm | JsonOutputParser()


----------------------------------------------------------------------------------

run.py
--------------------------------------------------------------------------------------------------
from ingest import vector_store
from agno.agent import Agent
from agno.knowledge.langchain import LangChainKnowledgeBase
from agno.models.ollama import Ollama
from agno.models.google.gemini import Gemini
from agno.models.groq.groq import Groq
from agno.tools.yfinance import YFinanceTools
from retrieval_grader import retrieval_grader, small_talk_grader
from deep_research_complicated import DeepResearch
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
import sys
from termcolor import colored
from vars import *

console = Console()

load_dotenv()

# # Get Tavily API key from environment variables or set it directly
tavily_api_key = os.environ.get("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key)

yf_tool = YFinanceTools(
    stock_price=True,
    analyst_recommendations=True,
    stock_fundamentals=True,
    historical_prices=True,
    company_info=True,
    company_news=True
)
researcher = DeepResearch(
    max_search_calls=MAX_SEARCH_CALLS, max_depth=MAX_DEPTH)

retriever = vector_store.as_retriever()
knowledge_base = LangChainKnowledgeBase(retriever=retriever)

if ENABLE_LOCAL:
    llm = Ollama(id=LOCAL_LLM)
    print("Using local LLM")
else:
    llm = Groq(REMOTE_LLM)
    print("Using Groq LLM")
# Create agent
agent = Agent(
    model=llm,
    knowledge=knowledge_base,
    description="Answer to the user question from the knowledge base",
    markdown=True,
    search_knowledge=True,
)


def display_tool_calls(tool_calls):
    """Display tool calls in a formatted way"""
    print(colored("\n=== Tool Call History ===", "cyan"))
    if not tool_calls:
        print(colored("No tool calls were made", "yellow"))
        return

    for i, call in enumerate(tool_calls, 1):
        print(colored(f"\nTool Call #{i}:", "yellow"))
        if isinstance(call, dict):
            print(colored(f"Tool: {call.get('name', 'Unknown')}", "green"))
            print(colored(f"Input: {call.get('arguments', {})}", "blue"))
            print(
                colored(f"Output: {call.get('output', 'No output')}", "magenta"))
        elif hasattr(call, 'tool'):
            print(colored(f"Tool: {call.tool}", "green"))
            print(colored(f"Input: {call.tool_input}", "blue"))
            print(colored(f"Output: {call.tool_output}", "magenta"))
        else:
            print(colored(f"Tool Call Data: {call}", "red"))
    print(colored("\n=== End Tool Call History ===\n", "cyan"))


def answer_with_grading_and_fallback(query, deep_search=False):
    """
    Process a query through the agent with retrieval grading.
    Falls back to web search if grading score is 0.
    """

    agent_response = agent.run(query)

    # Grade the retrieved documents
    retrieved_docs = agent.get_relevant_docs_from_knowledge(query)
    retrieved_docs = "\n\n".join([doc["content"] for doc in retrieved_docs])

    print(colored("RETRIEVED DOCUMENTS: ", "green"))
    print(colored(retrieved_docs, "yellow"))

    grade_result = retrieval_grader.invoke(
        {"question": query, "documents": retrieved_docs})

    print(colored(f"Retrieval grade: {grade_result}", 'cyan'))

    # If grade is 0, fall back to web search
    if grade_result['score'] == 0:
        if deep_search:
            print(colored(
                "No relevant documents found. Falling back to DEEP RESEARCH...\n\n\n\n\n\n", 'magenta'))
            deep_research_response = researcher.research(query)['answer']
            return deep_research_response
        else:
            print(colored(
                "No relevant documents found. Falling back to WEB SEARCH...\n\n\n\n\n\n", 'magenta'))

          
            web_search_agent = Agent(
                model=llm,
                description="""You are a financial assistant that can provide real-time information about stocks, markets, and financial data.
                When asked about current stock prices, market data, or financial information:
                1. Use the YFinance tools to get real-time stock data, analyst recommendations, and company information
                2. Use the Tavily search tool to get the latest news and market updates
                3. Always prioritize getting real-time data over historical information
                4. If the user asks about current prices or market conditions, make sure to use the appropriate tools to get fresh data
                5. IMPORTANT: You MUST actually execute the tools you reference. Do not just list the tool calls.
                6. For stock prices, use the yf_tool tool and wait for its response before proceeding.
                7. For market news and updates, use the Tavily search tool.
                8. When asked about multiple stocks or a list of stocks:
                - First, identify the specific stocks you need to check
                - For each stock, make a separate tool call to get its current price
                - Wait for each tool call's response before proceeding
                - Compare the current prices with previous closing prices to determine profit/loss
                9. For questions about profitable stocks:
                - Start by checking major indices (S&P 500, NASDAQ) top companies
                - Make individual tool calls for each stock's current price
                - Compare with previous closing prices to determine profit/loss
                - Present the results in a clear, organized format

                DO NOT INCLUDE ANYTHING RELATED TO TOOL CALL IN THE FINAL RESPONSE
                """,
                markdown=True,
                search_knowledge=False,
                tools=[tavily_client, YFinanceTools(
                    stock_price=True, analyst_recommendations=True, stock_fundamentals=True)],
                show_tool_calls=True,
                add_datetime_to_instructions=True,
                # max_iterations=10
            )
            try:
                web_search_agent_response = web_search_agent.run(query).content
                tool_calls = web_search_agent.get_tool_call_history()
                if not tool_calls:
                    print(colored("Warning: No tools were actually called!", "red"))
                    # return "I apologize, but I encountered an issue retrieving the real-time data. Please try again."
                display_tool_calls(tool_calls)
                return web_search_agent_response
            except Exception as e:
                print(colored(f"Error during tool execution: {str(e)}", "red"))
                return f"I encountered an error while trying to retrieve the data: {str(e)}"

    else:
        print(
            colored("Retrieved documents are relevant. Using agent response...", 'magenta'))
        return agent_response.content
---------------------------------------------------------------------------------------------------------

summarizer.py
--------------------------------------------------------------------------
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain.tools import Tool
from typing import Optional
import os

# Function to summarize text


def summarize_text(text: str, format_type: Optional[str] = None) -> str:
    """
    Summarizes the provided text in a pointwise manner.

    Args:
        text: The text to summarize (can be plaintext, markdown, HTML, JSON, etc.)
        format_type: Optional hint about the format of the text

    Returns:
        A pointwise summary of the text
    """
    if not text:
        return "No text provided to summarize."

    format_hint = f"The text is in {format_type} format. " if format_type else ""

    # This function doesn't need to do anything special - the LLM will handle the summarization
    return text


# Create a tool for the summarization function
summarize_tool = Tool(
    name="summarize_text",
    description="Summarizes text in a pointwise manner, preserving important information",
    func=summarize_text,
    args_schema=None
)

# Set up the LLM
model = ChatGroq(
    model="deepseek-r1-distill-llama-70b", 
    api_key=os.environ.get('GROQ_API_KEY'),
    temperature=0   
)

# Define the tools
tools = [summarize_tool]

# Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert summarizer that can handle text in any format (plaintext, markdown, HTML, JSON, etc.).
    
Your task is to:
1. Analyze the provided text
2. Extract all important information
3. Create a concise, pointwise summary in natural human language
4. Ensure no critical details are lost
5. Organize information logically
6. Maintain the original meaning and intent

If the text is in a structured format like HTML or JSON, extract the meaningful content before summarizing.
Always respond with a clear, well-organized summary that a human can easily understand."""),
    MessagesPlaceholder(variable_name="messages"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Create the agent
summarizer_agent = create_tool_calling_agent(model, tools, prompt)

# Create the agent executor
summarizer_agent_executor = AgentExecutor(
    agent=summarizer_agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)


def summarize(text: str, format_type: Optional[str] = None) -> str:
    """
    Main function to summarize text.

    Args:
        text: The text to summarize
        format_type: Optional hint about the format of the text

    Returns:
        A pointwise summary of the text
    """
    message_content = f"Please summarize the following text: {text}"
    if format_type:
        message_content += f"\n\nNote: This text is in {format_type} format."

    response = summarizer_agent_executor.invoke({
        "messages": [HumanMessage(content=message_content)]
    })

    return response["output"]


-----------------------------------------------------------------------------------------------
frontend.py
-------------------------------------------------------------------------------------------------------------------------



from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.runnables import RunnableConfig
from termcolor import colored
# from langchain_openai import ChatOpenAI
from run import answer_with_grading_and_fallback
import streamlit as st


st.set_page_config(page_title="Financial Assistant", page_icon="💰")
st.title("Financial Assistant ")

# openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)
if len(msgs.messages) == 0 or st.sidebar.button("Reset chat history"):
    msgs.clear()
    msgs.add_ai_message("How can I help you?")
    st.session_state.steps = {}


deep_research_button = st.sidebar.checkbox("Deep Research", key="deep_search")

avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        # Render intermediate steps if any were saved
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)


def process_input(prompt):
    # Get the input from the session state
    # user_input = st.session_state.user_input
    user_input = prompt
    # deep_search = st.session_state.get("deep_search", False)

    if not user_input.strip():
        return

    # Add user message to history
    # st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate response
    try:
        with st.spinner("Thinking..."):
            if deep_research_button:
                msg = answer_with_grading_and_fallback(
                    user_input, deep_search=True)
            else:
                msg = answer_with_grading_and_fallback(user_input)
    except Exception as e:
        msg = f"Sorry, I encountered an error: {str(e)}"

    # Add assistant response to history
    # st.session_state.messages.append({"role": "assistant", "content": msg})
    return msg
    # Clear the input
    # st.session_state.user_input = ""


if prompt := st.chat_input(placeholder="Who won the Women's U.S. Open in 2018?"):
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(
            st.container(), expand_new_thoughts=True)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_cb]
        response = process_input(prompt)
        st.write(response)
        print(colored(f"AGENT : {response}", "green"))
        # st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

---------------------------------------------------------
vars.py
--------------------------------------------------
LOCAL_LLM = "llama3.2:latest"
REASONING_LLM = "deepseek-r1-distill-llama-70b"
MAX_SEARCH_CALLS=2
MAX_DEPTH=1
ENABLE_LOCAL=False
REMOTE_LLM="qwen-2.5-coder-32b"
TOOL_CALL_LLM="qwen-2.5-coder-32b"
