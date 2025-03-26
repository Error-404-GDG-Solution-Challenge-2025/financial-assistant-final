# retrieval_grader.py

from typing import Dict
from langchain.prompts import PromptTemplate
# Using Langchain's ChatGroq/ChatOllama for consistency if preferred
# from langchain_community.chat_models import ChatOllama
# from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from vars import get_llm_id, get_llm_provider  # Use centralized provider
import os
from dotenv import load_dotenv

load_dotenv()

# LLM for Grading - needs good instruction following and JSON output
# Using the main LLM provider, assuming it's capable.
# Or specify a different one if needed
grading_llm = get_llm_provider(get_llm_id("remote"), "langchain")
# Ensure the provider can handle JSON output mode if available/needed
# e.g., for ChatOllama: llm = ChatOllama(model=..., format="json", temperature=0)
# e.g., for ChatGroq: llm = ChatGroq(model=..., temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
# Note: Agno models might handle JSON output via prompt instructions. Check Agno docs.

# Improved Prompt for Retrieval Grading
prompt_for_retrieval_grading = PromptTemplate(
    template="""You are a strict relevance grader. You will evaluate if the provided FACT contains information that DIRECTLY and SPECIFICALLY answers the given QUESTION.

    **Evaluation Criteria:**

    1.  **Direct Relevance:** Does the FACT contain statements that directly address the core subject of the QUESTION?
    2.  **Specificity:** Does the FACT provide specific details relevant to the QUESTION, or is it too general?
    3.  **Real-time Data Need:** Does the QUESTION explicitly or implicitly ask for *current*, time-sensitive information (e.g., "What is the stock price *now*?", "latest news", "current market cap")?
        *   If the QUESTION needs real-time data, and the FACT only contains general, historical, or outdated information, the FACT is NOT relevant (Score 0).

    **Scoring:**

    *   **Score 1 (Relevant):** The FACT contains specific information that directly addresses the main point of the QUESTION. If the question requires real-time data, the fact *must* contain plausible real-time data points (even if simulated in this context).
    *   **Score 0 (Not Relevant):** NONE of the statements in the FACT directly and specifically address the QUESTION, OR the QUESTION requires real-time data that the FACT clearly lacks.

    **Instructions:**

    1.  Analyze the QUESTION to understand its core intent and whether it requires real-time data.
    2.  Analyze the FACT to see if it contains directly relevant and specific information.
    3.  Compare the FACT against the QUESTION based on the criteria above.
    4.  Provide a step-by-step reasoning for your decision (internal thought process, not for the final output).
    5.  Output *only* a JSON object with a single key 'score' and a value of either 1 or 0. Do not include any preamble, explanation, or markdown formatting in the final JSON output.

    **QUESTION:**
    {question}

    **FACT:**
    {documents}

    **JSON Output:**
    """,
    input_variables=["question", "documents"],
)

retrieval_grader = prompt_for_retrieval_grading | grading_llm | JsonOutputParser()

# --- Small Talk Grader (NEW) ---
# This helps identify queries that don't need complex processing.

prompt_for_small_talk = PromptTemplate(
    template="""You are classifying user input. Determine if the following input is simple small talk, a greeting, a thank you, or a basic conversational phrase, rather than a request for financial information, analysis, or research.

    Examples of Small Talk:
    - "Hello"
    - "How are you?"
    - "Thanks!"
    - "Okay"
    - "Who are you?"
    - "What can you do?"

    Examples of NOT Small Talk (Requires Financial Processing):
    - "What's the price of Apple stock?"
    - "Tell me about Tesla's latest earnings."
    - "Should I invest in Bitcoin?"
    - "Explain diversification."

    Analyze the user input below.

    USER INPUT:
    {question}

    Is this input simple small talk, a greeting, or a basic conversational phrase? Answer with only YES or NO.
    """,
    input_variables=["question"],
)

# Simple Output Parser for YES/NO


class YesNoParser(JsonOutputParser):
    def parse(self, text: str) -> Dict[str, bool]:
        text_upper = text.strip().upper()
        if "YES" in text_upper:
            return {"score": True}
        elif "NO" in text_upper:
            return {"score": False}
        else:
            # Default or raise error - defaulting to False (not small talk) is safer
            print(
                f"Warning: Grader returned ambiguous output: {text}. Defaulting to NO.")
            return {"score": False}


small_talk_grader = prompt_for_small_talk | grading_llm | YesNoParser()
