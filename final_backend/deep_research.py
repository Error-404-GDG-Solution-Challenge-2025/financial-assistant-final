# deep_research.py
import time
from tavily import TavilyClient
from agno.agent import Agent
# Using get_llm_provider to centralize model selection
from vars import get_llm_id, get_llm_provider, MAX_DEPTH, MAX_SEARCH_CALLS, NUM_SUBQUESTIONS
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from termcolor import colored
from rich.console import Console
from rich.markdown import Markdown
import re
import json
# Import YFinanceTools to use within deep research
from agno.tools.yfinance import YFinanceTools

load_dotenv()
console = Console()

tavily_api_key = os.environ.get("TAVILY_API_KEY")
if not tavily_api_key:
    raise ValueError("TAVILY_API_KEY not found in environment variables.")
tavily_client = TavilyClient(api_key=tavily_api_key)

# Initialize YFinanceTools once
yf_tool = YFinanceTools(
    stock_price=True,
    analyst_recommendations=True,
    stock_fundamentals=True,
    # historical_prices=True, # Keep tools focused unless specifically needed
    company_info=True,
    # company_news=True # Tavily is better for general news
)


class DeepResearch:
    def __init__(self, max_depth=MAX_DEPTH, max_search_calls=MAX_SEARCH_CALLS):
        self.reasoning_model = get_llm_provider(get_llm_id("reasoning"))
        # Use main model for analysis/synthesis
        self.analysis_model = get_llm_provider(get_llm_id("remote"))
        self.max_depth = max_depth
        self.max_search_calls = max_search_calls
        self.search_calls_made = 0  # Track calls across the research process
        self.debug_log = []  # Store debug logs
        self.user_prompt = ""
    def _log(self, message, color=None, attrs=None):
        """Log a message to both console and debug log."""
        if color:
            colored_msg = colored(message, color, attrs=attrs)
            print(colored_msg)
        else:
            print(message)
        # Store the original message without color formatting
        self.debug_log.append(message)

    def _parse_subquestions(self, response_content: str, num_questions: int) -> List[str]:
        """Robustly parse numbered list of subquestions from LLM response."""
        subquestions = []
        # Try finding numbered lists
        lines = response_content.strip().split('\n')
        for line in lines:
            # Match lines starting with digits, optional punctuation, and whitespace
            match = re.match(r"^\s*\d+[.)]?\s*(.*)", line)
            if match:
                question = match.group(1).strip()
                # Remove potential surrounding quotes
                question = question.strip('"\'')
                if question:
                    subquestions.append(question)

        # Fallback: If no numbered list found, try splitting by newline and cleaning
        if not subquestions:
            for line in lines:
                cleaned = line.strip()
                # Remove common list markers
                if cleaned.startswith(("- ", "* ")):
                    cleaned = cleaned[2:]
                cleaned = cleaned.strip('"\'')
                if cleaned:  # Avoid adding empty lines
                    subquestions.append(cleaned)

        # Limit to the requested number, prioritizing the first ones found
        return subquestions[:num_questions]

    def _generate_subquestions(self, query: str, num_questions=NUM_SUBQUESTIONS) -> List[str]:
        """Break down a complex query into simpler, distinct, researchable subquestions."""
        agent = Agent(
            model=self.analysis_model,
            description="You are an expert research planner. Your goal is to break down a main question into specific, answerable subquestions.",
        )

        self.user_prompt = query

        prompt = f"""
        You need to research the following complex topic: "{query}"

        Break this down into exactly {num_questions} specific, distinct, and researchable subquestions that are essential for comprehensively answering the main question.
        Each subquestion should:
        1. Cover a unique and important aspect of the main query. Avoid overlap.
        2. Be specific enough to be researched effectively using web search or financial data tools.
        3. Be answerable with factual information. Avoid overly broad or subjective questions.
        4. Collectively, these subquestions should guide the research towards a complete answer to the main query.

        Example:
        Main Query: "Is investing in NVIDIA stock a good idea right now?"
        Subquestions:
        1. What is the current stock price and recent performance trend of NVIDIA (NVDA)?
        2. What are the key financial health indicators for NVIDIA based on its latest earnings report (e.g., revenue growth, profitability, debt)?
        3. What are the main growth drivers and potential risks for NVIDIA's business in the near future?
        4. What is the consensus analyst rating and price target for NVIDIA stock?
        5. How does NVIDIA's valuation compare to its competitors in the semiconductor industry?

        Return ONLY the numbered list of subquestions, with each question on a new line. Do not include any other text, preamble, or explanation.
        """

        try:
            response = agent.run(prompt)
            content = response.content
            # Handle potential <think> tags or other LLM-specific formatting
            if "<think>" in content:
                content = content.split("</think>")[-1].strip()

            subquestions = self._parse_subquestions(content, num_questions)

            self._log(f"Generated {len(subquestions)} subquestions:", "cyan")
            for idx, q in enumerate(subquestions):
                self._log(f"  {idx+1}. {q}", "yellow")
            return subquestions

        except Exception as e:
            self._log(f"Error generating subquestions: {e}", "red")
            return []  # Return empty list on error

    def _should_decompose(self, subquestion: str, context: str) -> bool:
        """Decide if a subquestion needs further decomposition based on initial findings."""
        agent = Agent(model=self.analysis_model)
        prompt = f"""
        Consider the subquestion: "{subquestion}"
        Initial research provided this context:
        ---
        {context[:1500]}...
        ---

        Based *only* on the subquestion and the initial context, is the subquestion still too broad or complex, requiring it to be broken down into even *more specific* sub-subquestions for a thorough answer?

        Focus on whether the initial context adequately addresses the specifics of the subquestion. If key aspects seem missing or the topic is clearly multifaceted beyond the current context, then decomposition might be needed.

        Answer with only YES or NO.
        """
        try:
            response = agent.run(prompt)
            return "YES" in response.content.upper()
        except Exception as e:
            self._log(f"Error checking decomposition: {e}", "red")
            return False  # Default to no decomposition on error

    def _research_subquestion(self, subquestion: str, depth=0) -> Dict[str, Any]:
        """Research a specific subquestion using Tavily, YFinance, and potential decomposition."""
        self._log(
            f"\n{'  ' * depth}Researching (Depth {depth}): {subquestion}", "green")

        if self.search_calls_made >= self.max_search_calls:
            self._log(
                f"{'  ' * depth}Skipping research: Max search calls ({self.max_search_calls}) reached.", "red")
            return {
                "subquestion": subquestion, "summary": "Max search calls reached.",
                "search_results": None, "context": "", "additional_info": {}
            }

        context = ""
        search_results = None
        tool_outputs = {}

        # --- Tool Integration ---
        # Use LLM to determine if YFinance might be relevant
        agent = Agent(model=self.reasoning_model)
        relevance_prompt = f"""
        Analyze this question: "{subquestion}"
        
        Is this question related to stock prices, financial data, company information, 
        or anything that could be answered using YFinance (Yahoo Finance) data?
        
        Consider if it mentions stocks, prices, tickers, financials, earnings, recommendations, 
        valuations, dividends, or specific company stock symbols.
        
        Answer with only YES or NO.
        """

        try:
            relevance_response = agent.run(relevance_prompt)
            is_yfinance_relevant = "YES" in relevance_response.content.upper()

            if is_yfinance_relevant:
                self._log(
                    f"{'  ' * depth}YFinance determined to be relevant for: {subquestion}", "blue")

                # Create an agent with YFinance tools
                yf_agent = Agent(
                    model=self.reasoning_model,
                    tools=[yf_tool],
                    show_tool_calls=True,
                    markdown=True,
                )

                # Run the agent with the subquestion
                try:
                    yf_response = yf_agent.run(subquestion)
                    yf_output = yf_response.content
                    if yf_output.startswith("404 Client Error:"):
                        self._log(
                            f"{'  ' * depth}YFinance returned 404 error for: {subquestion}\n\n Falling back to Tavily", "red")
                        raise Exception("YFinance returned 404 error")

                    # Store output in context
                    tool_outputs["yfinance_data"] = yf_output
                    context += f"\nYFinance Tool Output:\n{yf_output}\n"

                    # Print debug information
                    self._log(
                        f"{'  ' * depth}YFinance Output: {yf_output}...", "magenta")
                    self.search_calls_made += 1
                except Exception as e:
                    self._log(
                        f"{'  ' * depth}YFinance agent failed: {e}", "red")
            else:
                self._log(
                    f"{'  ' * depth}YFinance determined not relevant for this query.", "yellow")
        except Exception as e:
            self._log(
                f"{'  ' * depth}Error determining YFinance relevance: {e}", "red")
            try:
                search_results = tavily_client.search(
                    query=subquestion, search_depth="advanced", max_results=5)
                self.search_calls_made += 1
                if search_results and search_results.get("results"):
                    context += "\nWeb Search Results:\n" + \
                        "\n\n".join(
                            [f"Source: {r.get('url', 'N/A')}\nContent: {r.get('content', '')}" for r in search_results["results"]])
                    self._log(
                        f"{'  ' * depth}Tavily search successful.", "magenta")
                else:
                    self._log(
                        f"{'  ' * depth}Tavily search returned no results.", "yellow")
            except Exception as e:
                self._log(f"{'  ' * depth}Tavily search failed: {e}", "red")
                context += "\nWeb search failed."

        # --- Tavily Web Search ---
        if self.search_calls_made < self.max_search_calls:
            self._log(
                f"{'  ' * depth}Performing Tavily search for: {subquestion}", "blue")
            try:
                search_results = tavily_client.search(
                    query=subquestion, search_depth="advanced", max_results=5)
                self.search_calls_made += 1
                if search_results and search_results.get("results"):
                    context += "\nWeb Search Results:\n" + \
                        "\n\n".join(
                            [f"Source: {r.get('url', 'N/A')}\nContent: {r.get('content', '')}" for r in search_results["results"]])
                    self._log(
                        f"{'  ' * depth}Tavily search successful.", "magenta")
                else:
                    self._log(
                        f"{'  ' * depth}Tavily search returned no results.", "yellow")
            except Exception as e:
                self._log(f"{'  ' * depth}Tavily search failed: {e}", "red")
                context += "\nWeb search failed."
        else:
            self._log(
                f"{'  ' * depth}Skipping Tavily search: Max search calls reached.", "red")

        # --- Recursive Decomposition ---
        additional_info = {}
        if depth < self.max_depth and self.search_calls_made < self.max_search_calls:
            # Check for decomposition *after* initial search/tool use
            if self._should_decompose(subquestion, context):
                self._log(
                    f"{'  ' * depth}Further decomposing: {subquestion}", "magenta")
                # Generate fewer sub-subquestions to control complexity
                sub_subquestions = self._generate_subquestions(
                    subquestion, num_questions=2)

                sub_findings = {}
                for sub_sq in sub_subquestions:
                    # Recursive call - increments depth
                    sub_result = self._research_subquestion(
                        sub_sq, depth=depth + 1)
                    sub_findings[sub_sq] = sub_result
                additional_info["sub_research"] = sub_findings
            else:
                self._log(
                    f"{'  ' * depth}Decomposition not needed for: {subquestion}", "yellow")

        # --- Analysis/Summarization ---
        summary = self._analyze_findings(subquestion, context, additional_info)

        return {
            "subquestion": subquestion,
            "search_results": search_results,  # Keep raw results if needed later
            "tool_outputs": tool_outputs,  # Keep tool outputs
            "context": context,  # Combined context used for summary
            "summary": summary,
            "additional_info": additional_info  # Contains sub-research summaries
        }

    def _analyze_findings(self, subquestion: str, context: str, additional_info: Dict) -> str:
        """Analyze and summarize findings for a specific subquestion, incorporating sub-research."""
        agent = Agent(
            model=self.reasoning_model,
            description="You are a research analyst. Analyse the correctness of the information provided and Synthesize the provided information into a concise, factual summary answering the specific subquestion.",
        )

        sub_research_summary = ""
        if "sub_research" in additional_info:
            sub_research_summary = "\n\n--- Findings from Deeper Analysis ---\n"
            for sub_sq, sub_result in additional_info["sub_research"].items():
                sub_research_summary += f"\nRegarding '{sub_sq}':\n{sub_result.get('summary', 'No summary available.')}\n"

        prompt = f"""
        Please analyse the correctness of the information provided and synthesize the following information to answer the specific subquestion: "{subquestion}"

        --- Information Gathered ---
        {context[:8000]}...
        {sub_research_summary}
        ---

        Instructions:
        1. Focus *only* on answering the subquestion: "{subquestion}"
        2. Analyse the correctness of the information provided.If the information is incorrect with respect to the subquestion and the user prompt (which is {self.user_prompt}) in general and does not line up with the situation the user is in or has described or has asked for, provide the correct information.
        3. Create a clear, concise, and factual summary based *only* on the provided information. 
        4. If specific data (like stock prices, financial metrics) was found, include it accurately.
        5. If the information is insufficient to fully answer, state that clearly.
        6. Do not add information not present in the context.
        7. Structure the summary logically. Use bullet points if helpful for clarity.
        8. Aim for a comprehensive yet brief summary.
        """
        try:
            response = agent.run(prompt)
            return response.content
        except Exception as e:
            self._log(
                f"Error analyzing findings for '{subquestion}': {e}", "red")
            return f"Error summarizing findings for '{subquestion}'."

    def _synthesize_research(self, main_query: str, research_results: Dict[str, Dict]) -> str:
        """Synthesize all subquestion summaries into a cohesive final answer."""
        agent = Agent(
            model=self.analysis_model,
            description="You are a senior research analyst. Combine detailed findings from various sub-reports into a single, comprehensive, well-structured final report.",
        )

        findings_context = ""
        for subq, result in research_results.items():
            findings_context += f"\n\n## Research Findings for: {subq}\n\n{result.get('summary', 'No summary available.')}"
            # Optionally include raw tool outputs if needed for synthesis
            # if result.get('tool_outputs'):
            #     findings_context += f"\nRaw Tool Data:\n{json.dumps(result['tool_outputs'], indent=2)}\n"

        prompt = f"""
        You have been tasked with researching the question: "{main_query}"
        The research was broken down into several sub-topics, and the following summaries were generated for each:
        --- Combined Research Summaries ---
        {findings_context}
        ---

        Instructions:
        1. Synthesize *all* the provided summaries into a single, cohesive, and comprehensive answer to the original main question: "{main_query}".
        2. Structure the final answer logically. Use headings, subheadings, and bullet points as appropriate for clarity and readability.
        3. Ensure the answer directly addresses the main question.
        4. Integrate information from different sub-summaries smoothly. Identify connections and potential contradictions if any.
        5. Prioritize factual accuracy and include specific data points (like financial figures, dates, performance metrics) mentioned in the summaries.
        6. Provide a balanced perspective if the research uncovered both pros and cons.
        7. Conclude with a final summary or overall takeaway related to the main question.
        8. Do not include information not present in the provided summaries.
        9. Format the output using Markdown for readability.
        """
        try:
            response = agent.run(prompt)
            return response.content
        except Exception as e:
            self._log(f"Error synthesizing final answer: {e}", "red")
            return f"Error synthesizing the final research report: {e}"

    def research(self, query: str) -> Dict[str, Any]:
        """Execute deep research on a query."""
        # Clear debug log for new research
        self.debug_log = []
        self._log(
            f"\n=== Starting Deep Research on: {query} ===", "blue", attrs=["bold"])
        self.search_calls_made = 0  # Reset counter for each new research task

        # Step 1: Generate initial subquestions
        subquestions = self._generate_subquestions(query)
        if not subquestions:
            self._log(
                "Failed to generate subquestions. Aborting deep research.", "red")
            return {
                "query": query,
                "answer": "Could not perform deep research due to an issue generating subquestions.",
                "debug_log": "\n".join(self.debug_log)
            }

        # Step 2: Research each subquestion (potentially recursively)
        subquestion_results = {}
        for sq in subquestions:
            if self.search_calls_made >= self.max_search_calls:
                self._log(
                    f"Max search calls ({self.max_search_calls}) reached during subquestion research.", "red")
                subquestion_results[sq] = {
                    "summary": "Skipped due to max search call limit."}
                continue  # Skip researching remaining questions
            subquestion_results[sq] = self._research_subquestion(sq, depth=0)

        # Step 3: Synthesize findings into the final answer
        final_answer = self._synthesize_research(query, subquestion_results)

        self._log("\n=== Deep Research Complete ===\n", "blue", attrs=["bold"])

        # Record timing information for diagnostics
        total_calls = self.search_calls_made
        self._log(f"Total search calls made: {total_calls}", "cyan")

        return {
            "query": query,
            "subquestions": subquestions,
            # Contains summaries and potentially raw data
            "subquestion_results": subquestion_results,
            "answer": final_answer,
            # Return all logged messages as a single string
            "debug_log": "\n".join(self.debug_log)
        }


deep_research = DeepResearch()

if __name__ == "__main__":
    with (open('./docs/query.md', 'r')) as f:
        query = f.readline()
    start_time = time.time()
    result = deep_research.research(query)
    end_time = time.time()

    self._log(
        f"Total time taken: {end_time - start_time:.2f} seconds", "magenta")
    console.print(Markdown(colored("\n=== Final Research Answer ===\n",
                                   "green", attrs=["bold"])))
    console.print(Markdown(result["answer"]))

    # Also save debug log
    with open('./docs/debug_log.txt', 'w') as f:
        f.write(result["debug_log"])

    with open('./docs/outputs.md', 'a') as f:
        f.write("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n" + result["answer"])
