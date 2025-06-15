from google.adk.agents import Agent

from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Define output schema
class TableData(BaseModel):
    headers: List[str] = Field(..., description="Column headers for the table")
    rows: List[List[Any]] = Field(..., description="Data rows for the table")
    caption: str = Field(..., description="Caption explaining the table contents")

class ResearchOutput(BaseModel):
    summary: str = Field(..., description="Executive summary of the research findings")
    key_points: List[str] = Field(..., description="Key points from the research")
    market_analysis: str = Field(..., description="Analysis of market conditions")
    economic_outlook: str = Field(..., description="Economic outlook and implications")
    investment_insights: str = Field(..., description="Investment strategy insights")
    news_impact: str = Field(..., description="Impact of recent news")
    tables: List[TableData] = Field(..., description="Structured data tables")
    conclusion: str = Field(..., description="Concluding remarks and recommendations")

output_formatter_agent = Agent(
    name="output_formatter_agent",
    model="gemini-2.5-flash-preview",
    description="Formats research findings into structured output",
    instruction="""
    You are an output formatting specialist. Your role is to:
    1. Organize research findings into a coherent narrative
    2. Create structured tables for quantitative data
    3. Ensure consistency in formatting and presentation
    4. Optimize output for readability and comprehension
    
    Produce both natural language analysis and structured tables as specified in the output schema.
    """,
    output_schema=ResearchOutput
)
