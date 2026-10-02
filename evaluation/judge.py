import json

from langfuse import observe
from pydantic import BaseModel, Field

from common.config import MODEL_JUDGE
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, ArticleDraft, ResearchBrief, ScoutReport
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
You are shown the findings it kept and, when available, the headlines it excluded. Use the
excluded headlines only to judge the Relevance criterion: did it drop anything that looks major?

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


_DRAFT_SYSTEM_PROMPT = """You are an expert editor evaluating a news article drafted by an AI writer
from a research brief. The brief is the writer's ONLY allowed source.

Evaluate the draft on these criteria, each scored 1-5 (5 = excellent):
1. Fidelity to Brief - does every claim in the draft come from the brief's background or key facts?
2. No Fabrication - are there invented facts, numbers, names, dates or quotations that are NOT in
   the brief? Does it state an answer to any OPEN QUESTION, or present a FACT-CHECK FLAG as settled?
3. Structure & Readability - is it inverted-pyramid, with a lede that carries the key facts, short
   clear paragraphs, and a headline that matches the content?
4. Neutral Tone - wire-service neutrality: attributed claims, no opinion, speculation or loaded words?
5. Citation Validity - is every URL in sources_cited a source from the brief that was read
   (fetch_status "ok"), and do those sources plausibly support the draft? A draft that cites nothing
   when readable sources exist should score low.

Return ONLY valid JSON of this exact shape:
{
  "overall_score": 4.1,
  "scores": [
    {"criterion": "Fidelity to Brief", "score": 4, "reasoning": "..."},
    {"criterion": "No Fabrication", "score": 4, "reasoning": "..."},
    {"criterion": "Structure & Readability", "score": 4, "reasoning": "..."},
    {"criterion": "Neutral Tone", "score": 4, "reasoning": "..."},
    {"criterion": "Citation Validity", "score": 4, "reasoning": "..."}
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

    @observe(name="judge.evaluate_scout")
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
        if scout_report.excluded_articles:
            user_prompt += (
                f"\n\nHeadlines the scout excluded ({len(scout_report.excluded_articles)}):\n"
                + "\n".join(f"- {title}" for title in scout_report.excluded_articles)
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

    @observe(name="judge.evaluate_research")
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

    @observe(name="judge.evaluate_draft")
    def evaluate_draft(self, draft: ArticleDraft, brief: ResearchBrief) -> StageEvaluation:
        user_prompt = (
            f"BRIEF BACKGROUND: {brief.background}\n"
            f"KEY FACTS: {json.dumps(brief.key_facts)}\n"
            f"OPEN QUESTIONS: {json.dumps(brief.open_questions)}\n"
            f"FACT-CHECK FLAGS: {json.dumps(brief.fact_check_flags)}\n"
            f"SOURCES: {json.dumps([s.model_dump() for s in brief.sources])}\n\n"
            "DRAFT ARTICLE:\n"
            + json.dumps(
                {
                    "headline": draft.headline,
                    "lede": draft.lede,
                    "body": draft.body,
                    "key_points": draft.key_points,
                    "sources_cited": draft.sources_cited,
                },
                indent=2,
            )
        )
        response = self.client.chat.completions.create(
            model=MODEL_JUDGE,
            messages=[
                {"role": "system", "content": _DRAFT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        data = parse_json_response(response.choices[0].message.content)

        return StageEvaluation(**data)
