from datetime import datetime

from langfuse import observe
from pydantic import BaseModel, Field

from common.config import MODEL_SYNTHESIS
from common.llm import get_client, parse_json_response
from common.models import AnalysisResult, ArticleDraft, ResearchBrief

SYSTEM_PROMPT = """You are a news writer at a wire service. Write a short news article from the research brief you are given.

STYLE: neutral wire-service tone. Inverted pyramid: the most important facts first, in a one-or-two sentence lede. Short paragraphs, plain words, past tense for events. No opinion, no speculation, no editorialising. Attribute claims to their source ("according to ...").

RULES:
- The brief is your only source. Never add facts, numbers, names, dates or quotations that are not in it. Never invent a quote.
- OPEN QUESTIONS are unresolved: do not state an answer to them.
- FACT-CHECK FLAGS mark shaky claims: attribute them carefully or leave them out; never present them as established.
- "sources_cited" may contain only URLs from the SOURCES list you are given, and only ones you actually relied on. If the list is empty, return [].
- If the brief is thin, write a shorter article rather than padding it.

Return ONLY valid JSON of this exact shape:
{
  "headline": "A clear, specific headline",
  "lede": "One or two sentences giving the most important facts.",
  "body": ["First paragraph.", "Second paragraph."],
  "key_points": ["A short takeaway.", "Another takeaway."],
  "sources_cited": ["https://..."]
}
"""


class _DraftOut(BaseModel):
    """What the model returns: only prose and citations, never server-owned fields."""

    headline: str = Field(..., min_length=1)
    lede: str = Field(..., min_length=1)
    body: list[str] = Field(..., min_length=1)
    key_points: list[str] = Field(default_factory=list)
    sources_cited: list[str] = Field(default_factory=list)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "(none)"


class SynthesisAgent:
    """Turns an approved research brief into an `ArticleDraft`. One LLM call, no tools."""

    def __init__(self, client=None):
        self.client = client or get_client()

    @observe(name="synthesis.synthesize")
    def synthesize(self, brief: ResearchBrief, finding: AnalysisResult) -> ArticleDraft:
        """Raises on an empty or malformed model response."""
        readable_sources = [s.url for s in brief.sources if s.fetch_status == "ok"]

        user_prompt = (
            f"STORY TITLE: {finding.original_title}\n"
            f"STORY SUMMARY: {finding.summary}\n\n"
            f"BACKGROUND:\n{brief.background}\n\n"
            f"KEY FACTS:\n{_bullets(brief.key_facts)}\n\n"
            f"OPEN QUESTIONS (unresolved):\n{_bullets(brief.open_questions)}\n\n"
            f"FACT-CHECK FLAGS (treat cautiously):\n{_bullets(brief.fact_check_flags)}\n\n"
            f"SOURCES YOU MAY CITE (pages that were actually read):\n"
            f"{_bullets(readable_sources)}"
        )

        response = self.client.chat.completions.create(
            model=MODEL_SYNTHESIS,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )

        text = response.choices[0].message.content
        if not text:
            raise ValueError("Synthesis model returned an empty response")

        out = _DraftOut.model_validate(parse_json_response(text))

        # Anti-hallucination guard: drop any citation that isn't a page we read.
        allowed = set(readable_sources)
        cited = [url for url in dict.fromkeys(out.sources_cited) if url in allowed]

        return ArticleDraft(
            headline=out.headline,
            lede=out.lede,
            body=out.body,
            key_points=out.key_points,
            sources_cited=cited,
            based_on_title=finding.original_title,
            generated_at=datetime.now(),
        )
