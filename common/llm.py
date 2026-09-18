import json
import os

from openai import OpenAI

import common.config  # noqa: F401  (import side effect: loads .env)


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set - add it to .env")

    return OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_API_BASE_URL"))


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
