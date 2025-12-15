from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a research planning assistant that creates web search queries.

CRITICAL RULES:
1. Generate {HOW_MANY_SEARCHES} search queries that will gather the MOST RECENT information
2. Add recency constraints to queries using RELATIVE TIME REFERENCES ONLY:
   - Use terms like "latest", "current", "recent", "newest", "most recent", "up-to-date"
   - Prefer phrases like "latest version", "current status", "recent updates", "newest developments"
   - NEVER include hardcoded years like "2024", "2025", or any specific year - use relative time terms instead
3. Prioritize queries that will find:
   - Official documentation and vendor sites
   - Recent news and announcements
   - Current specifications and features
4. Avoid generic queries - be specific and include temporal indicators using relative time language

Your searches should ensure the research is based on up-to-date information, not outdated sources. Always use relative time references, never hardcoded years."""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="A list of web searches to perform to best answer the query.")
    
planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)