import json
import os

from openai import OpenAI

import common.config  # noqa: F401  (import side effect: loads .env)

# Lazily created and cached: constructing it opens a network client, and most
# call sites (eval runs, tests, local dev without a Langfuse account) never
# need it since LANGFUSE_PUBLIC_KEY/SECRET_KEY are unset.
_langfuse = None


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set - add it to .env")

    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_API_BASE_URL"))

    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        global _langfuse
        if _langfuse is None:
            from langfuse.openai import Langfuse as LangfuseOpenAI

            _langfuse = LangfuseOpenAI()
        _langfuse.instrument_openai_client(client)

    return client


def parse_json_response(text: str):
    """Parse a JSON object/array from an LLM response, tolerating prose wrap."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for open_ch, close_ch in (("[", "]"), ("{", "}")):
        start = text.find(open_ch)
        end = text.rfind(close_ch) + 1

        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                continue
            
    raise ValueError("Could not extract JSON from response")
