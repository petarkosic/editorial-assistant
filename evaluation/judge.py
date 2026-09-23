import json

from pydantic import BaseModel, Field

from common.config import MODEL_JUDGE
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, ResearchBrief, ScoutReport
from evaluation.evaluator import EvaluationScore


class StageEvaluation(BaseModel):
    overall_score: float = Field(..., ge=1, le=5)
    scores: list[EvaluationScore]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: str


_SCOUT_SYSTEM_PROMPT = """You are an expert editor evaluating the quality of an AI news scout's report.

The scout was given a batch of recent articles and asked to keep only the important
or breaking ones, each with a 1-10 importance score, a one-sentence summary, and brief reasoning.

Evaluate the report as a whole on these criteria, each scored 1-5 (5 = excellent):
1. Importance Score Accuracy - are the 1-10 importance scores appropriate for the stories?
2. Summary Quality - are the one-sentence summaries clear and do they capture significance?
3. Reasoning Clarity - is the reasoning logical, specific, and well-justified?
4. Consistency - do the scores align with the summaries and reasoning across findings?
5. Relevance - was the important/not-important filtering sound (nothing trivial kept, nothing major dropped)?

Return ONLY valid JSON of this exact shape:
{
  "overall_score": 4.2,
  "scores": [
    {"criterion": "Importance Score Accuracy", "score": 4, "reasoning": "..."},
    {"criterion": "Summary Quality", "score": 4, "reasoning": "..."},
    {"criterion": "Reasoning Clarity", "score": 4, "reasoning": "..."},
    {"criterion": "Consistency", "score": 4, "reasoning": "..."},
    {"criterion": "Relevance", "score": 4, "reasoning": "..."}
  ],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": "..."
}
"""


_RESEARCH_SYSTEM_PROMPT = """You are an expert editor evaluating a research brief produced by an
AI research agent that used web search and page-fetch tools to investigate a story.

Evaluate the brief on these criteria, each scored 1-5 (5 = excellent):
1. Grounding - are the key facts traceable to the fetched/searched sources provided?
2. Coverage - does the brief cover the important angles of the story?
3. Fact-Check Flag Quality - are the fact_check_flags sensible and appropriately cautious?
4. Hallucination Check - are there claims that do NOT appear to come from any source?
5. Source Usage - were the sources (URLs actually fetched) put to good use in the brief?
6. Research Strategy Quality - given the tool-call trace (if provided), were the
   search/fetch choices sensible, did the agent stop at a reasonable point, and
   were there any wasted or redundant tool calls? If no trace was available, say
   so explicitly in your reasoning for this criterion instead of guessing.

Return ONLY valid JSON of this exact shape:
{
  "overall_score": 4.1,
  "scores": [
    {"criterion": "Grounding", "score": 4, "reasoning": "..."},
    {"criterion": "Coverage", "score": 4, "reasoning": "..."},
    {"criterion": "Fact-Check Flag Quality", "score": 4, "reasoning": "..."},
    {"criterion": "Hallucination Check", "score": 4, "reasoning": "..."},
    {"criterion": "Source Usage", "score": 4, "reasoning": "..."},
    {"criterion": "Research Strategy Quality", "score": 4, "reasoning": "..."}
  ],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "suggestions": "..."
}
"""


class Judge:
    """Runtime LLM-as-judge. One class, three per-stage rubrics."""

    def __init__(self, client=None):
        self.client = client or get_client()

    def evaluate_scout(self, scout_report: ScoutReport) -> StageEvaluation:
        findings = [
            {
                "importance_score": f.importance_score,
                "summary": f.summary,
                "reasoning": f.reasoning,
                "original_title": f.original_title,
            }
            for f in scout_report.important_findings
        ]

        user_prompt = (
            f"Articles analyzed: {scout_report.analyzed_articles}\n"
            f"Important findings kept ({len(findings)}):\n"
            + json.dumps(findings, indent=2)
        )

        response = self.client.chat.completions.create(
            model=MODEL_JUDGE,
            messages=[
                {"role": "system", "content": _SCOUT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        
        data = parse_json_response(response.choices[0].message.content)

        return StageEvaluation(**data)

    def evaluate_research(
        self,
        brief: ResearchBrief,
        finding: AnalysisResult,
        trace: list[dict] | None = None,
    ) -> StageEvaluation:
        if trace:
            trace_block = "\n".join(
                f"- {t['tool']}({t.get('args', {})}) -> {t.get('result_summary', '')}"
                for t in trace
            )
        else:
            trace_block = "(no tool-call trace was available for this evaluation)"

        user_prompt = (
            f"STORY: {finding.original_title}\n"
            f"BRIEF BACKGROUND: {brief.background}\n"
            f"KEY FACTS: {json.dumps(brief.key_facts)}\n"
            f"OPEN QUESTIONS: {json.dumps(brief.open_questions)}\n"
            f"FACT-CHECK FLAGS: {json.dumps(brief.fact_check_flags)}\n"
            f"SOURCES: {json.dumps([s.model_dump() for s in brief.sources])}\n\n"
            f"TOOL-CALL TRACE:\n{trace_block}"
        )
        response = self.client.chat.completions.create(
            model=MODEL_JUDGE,
            messages=[
                {"role": "system", "content": _RESEARCH_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        data = parse_json_response(response.choices[0].message.content)
        return StageEvaluation(**data)

    def evaluate_draft(self, draft, brief) -> StageEvaluation:
        # Draft rubric: fidelity to brief, no fabricated facts/quotes,
        # structure/readability, citation validity.
        raise NotImplementedError("draft rubric")
