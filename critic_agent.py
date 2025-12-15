from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a Senior Research Critic specializing in ERP & AI Systems.

Your role is to challenge, validate, and stress-test research reports before delivery. You are NOT a summarizer or writer - you are a critical auditor.

CRITICAL RULES:
1. Be direct, critical, and precise - do not soften conclusions
2. If something is unclear, say so explicitly
3. Challenge assumptions, not just summarize
4. Focus on what's missing, weak, or unproven

You must perform ALL of the following tasks:

1. IDENTIFY UNPROVEN ASSUMPTIONS
   - List at least 3 assumptions made in the report that are:
     * Stated as facts but lack strong evidence, OR
     * Derived from vendor marketing language rather than technical proof
   - For each assumption:
     * Quote or paraphrase the claim
     * Explain why it is weak or unproven
     * State what kind of evidence would be required to validate it

2. SEPARATE MARKETING CLAIMS FROM TECHNICAL REALITY
   - Analyze AI capabilities attributed to systems and classify them as:
     * Marketing claim
     * Partially implemented
     * Technically verifiable
   - Explain your reasoning for each classification

3. DETECT MISSING OR AVOIDED QUESTIONS
   - Identify at least 3 critical questions that a real ERP implementer, CTO, or system architect would ask but the report did not answer
   - Examples: Agent autonomy vs. approval workflows, ERP write-back safety, Governance of AI actions, Explainability and auditability
   - Explain why each missing question is critical

4. EVALUATE AGENTIC AND MCP READINESS
   - Explicitly assess whether the system described supports:
     * Autonomous or semi-autonomous agents
     * Secure action execution on ERP data
     * Context governance across models and tools
   - If not present, state what is missing

5. CONFIDENCE SCORE
   - Provide a confidence score (0-100) answering:
     "How safe is it to base strategic or architectural ERP decisions on this report alone?"
   - Explain the score in 3-5 bullet points

OUTPUT FORMAT:
Return your answer in structured bullet points with clear section headers.
Be direct, critical, and precise.
Do not soften conclusions."""


class Assumption(BaseModel):
    claim: str = Field(description="The assumption or claim made in the report")
    weakness: str = Field(description="Why it is weak or unproven")
    required_evidence: str = Field(description="What evidence would be needed to validate it")


class CapabilityClassification(BaseModel):
    capability: str = Field(description="The AI capability mentioned")
    classification: str = Field(description="Marketing claim, Partially implemented, or Technically verifiable")
    reasoning: str = Field(description="Explanation for the classification")


class MissingQuestion(BaseModel):
    question: str = Field(description="The critical question that was not answered")
    importance: str = Field(description="Why this question is critical for ERP implementers/CTOs/architects")


class AgenticReadiness(BaseModel):
    autonomous_agents: str = Field(description="Assessment of autonomous/semi-autonomous agent support")
    secure_execution: str = Field(description="Assessment of secure action execution on ERP data")
    context_governance: str = Field(description="Assessment of context governance across models and tools")
    missing_components: str = Field(description="What is missing if not fully present")


class ConfidenceScore(BaseModel):
    score: int = Field(description="Confidence score from 0-100", ge=0, le=100)
    explanation: list[str] = Field(description="3-5 bullet points explaining the score")


class CriticalAudit(BaseModel):
    unproven_assumptions: list[Assumption] = Field(description="At least 3 unproven assumptions")
    capability_classifications: list[CapabilityClassification] = Field(description="Marketing vs technical reality analysis")
    missing_questions: list[MissingQuestion] = Field(description="At least 3 critical missing questions")
    agentic_readiness: AgenticReadiness = Field(description="Assessment of agentic and MCP readiness")
    confidence_score: ConfidenceScore = Field(description="Confidence score and explanation")
    critical_summary: str = Field(description="Overall critical assessment summary")


critic_agent = Agent(
    name="Critic Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=CriticalAudit,
)

