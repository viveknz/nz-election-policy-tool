"""
Extraction module.

This is the real, reusable extraction function -- not a test script. It takes
one policy page's raw text and returns the structured schema, with retry logic
for the intermittent JSON-truncation failure documented in
docs/08_extraction_schema.md (Round 4).

Design decisions baked in here, all documented in docs/08_extraction_schema.md:
- source_url and is_costed are NOT asked of the model -- source_url is known by
  the caller, is_costed is derived from amount. Asking the model for either
  produced hallucination/contradiction in testing.
- temperature=0 for consistency (not a guarantee of correctness, but the best
  available default for a factual task).
- Every free-text field is length-constrained; amount also has a regex
  pattern. Unconstrained fields produced repetition loops and hallucination in
  testing.
- Retries on JSON parse failure (typically caused by truncation), not on
  every kind of failure -- an API error is not something a retry fixes.

Usage as a module:
    from extraction.extract import extract_policy, get_client

    client = get_client()
    result = extract_policy(
        client,
        party="Labour",
        policy_text="...",
        source_url="https://...",
    )
    # result is a dict matching the schema, or None if extraction failed
    # after all retries.
"""

import os
import json
import logging

from openai import OpenAI, APIError, APIConnectionError, BadRequestError

logger = logging.getLogger("extraction")

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
MAX_TOKENS = 2000
MAX_RETRIES = 3

SCHEMA = {
    "type": "object",
    "properties": {
        "policy_name": {
            "type": "string",
            "maxLength": 80,
        },
        "party": {
            "type": "string",
            "maxLength": 40,
        },
        "stated_position": {
            "type": "string",
            "maxLength": 200,
            "description": "One to two sentence plain summary of what the party says it will do, in the party's own terms. Do not include costing, dates, or eligibility detail here -- those go in their own fields.",
        },
        "amount": {
            "type": "string",
            "maxLength": 40,
            "pattern": "^(\\$[0-9][0-9,\\.]*\\s?(million|billion|m|bn)?)?$",
            "description": "The stated dollar figure, exactly as given in the text, wherever it appears -- including inside an action description like 'establish a $220 million fund' (extract '$220 million'), not only an explicit 'cost:' statement. Use an empty string only if no dollar figure appears anywhere in the text at all.",
        },
        "start_date": {
            "type": "string",
            "maxLength": 60,
            "description": "The stated start date or trigger condition, exactly as given in the text (e.g. 'from July 2026'). Use an empty string only if no date or trigger is stated anywhere in the text. State the fact only -- no explanation, no assumptions, no commentary.",
        },
    },
    "required": [
        "policy_name",
        "party",
        "stated_position",
        "amount",
        "start_date",
    ],
    "additionalProperties": False,
}


def get_client() -> OpenAI:
    """Create the Nebius Token Factory client. Raises if NEBIUS_API_KEY is unset."""
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NEBIUS_API_KEY environment variable not set. "
            "Run: export NEBIUS_API_KEY=\"your-key-here\""
        )
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def extract_policy(
    client: OpenAI,
    party: str,
    policy_text: str,
    source_url: str,
    max_retries: int = MAX_RETRIES,
) -> dict | None:
    """
    Extract structured policy data from one page's raw text.

    Returns a dict matching the schema (plus source_url and is_costed,
    attached programmatically -- not asked of the model), or None if
    extraction failed after all retries.
    """
    prompt = (
        f"Extract the policy details from this real {party} policy page text.\n\n"
        f"Policy text:\n{policy_text}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "policy_extraction",
                        "schema": SCHEMA,
                        "strict": True,
                    },
                },
                max_tokens=MAX_TOKENS,
                temperature=0,
            )
        except (BadRequestError, APIConnectionError, APIError) as e:
            # An API-level error is not something a retry on the same input
            # is likely to fix immediately -- log and stop rather than
            # burning through retries on a persistent problem.
            logger.error(
                "API error extracting policy for %s (attempt %d/%d): %s",
                party, attempt, max_retries, e,
            )
            return None

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "JSON parse failure for %s (attempt %d/%d) -- likely truncation, retrying.",
                party, attempt, max_retries,
            )
            continue

        # source_url is known by the caller; is_costed is derived from
        # amount. Neither is asked of the model -- see module docstring.
        parsed["source_url"] = source_url
        parsed["is_costed"] = bool(parsed.get("amount"))

        return parsed

    logger.error(
        "Extraction failed for %s after %d attempts -- all returned unparseable JSON.",
        party, max_retries,
    )
    return None
