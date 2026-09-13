"""
Phase 0, Step 3: Structured output test.

Purpose: confirm whether Nebius Token Factory supports JSON Schema-constrained
output (OpenAI's response_format={"type": "json_schema", ...}) for
Nemotron-3-Nano, before the extraction pipeline is built to depend on it.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python test_structured_output.py
"""

import os
import sys
import json
import logging

from openai import OpenAI, APIError, APIConnectionError, BadRequestError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("nebius_structured_test")

# Confirmed working in Step 2 -- do not guess these, re-copy from the
# console's playground code tab if a model or endpoint changes.
BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

FAKE_POLICY_TEXT = (
    "The Fictional Party will introduce a Free School Lunches programme, "
    "costing $200 million per year, starting in 2027."
)

# Tiny schema mirroring the real extraction fields the pipeline will need
# later: policy_name, stated_position, is_costed, amount, start_date.
SCHEMA = {
    "type": "object",
    "properties": {
        "policy_name": {"type": "string"},
        "is_costed": {"type": "boolean"},
        "amount": {"type": ["string", "null"]},
        "start_date": {"type": ["string", "null"]},
    },
    "required": ["policy_name", "is_costed", "amount", "start_date"],
    "additionalProperties": False,
}


def get_api_key() -> str:
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        logger.error(
            "NEBIUS_API_KEY environment variable not set. "
            "Run: export NEBIUS_API_KEY=\"your-key-here\""
        )
        sys.exit(1)
    return key


def run_test(api_key: str) -> None:
    client = OpenAI(base_url=BASE_URL, api_key=api_key)

    logger.info("Testing structured output (response_format=json_schema) on %s", MODEL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the policy details from this text:\n\n{FAKE_POLICY_TEXT}",
                }
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "policy_extraction",
                    "schema": SCHEMA,
                    "strict": True,
                },
            },
            max_tokens=200,
        )
    except BadRequestError as e:
        logger.error(
            "Nebius rejected the response_format parameter -- "
            "native structured output is NOT supported for this model/endpoint. "
            "Fallback: prompt for JSON and validate/retry in code."
        )
        logger.error("Raw error: %s", e)
        sys.exit(1)
    except APIConnectionError as e:
        logger.error("Network-level failure calling Nebius: %s", e)
        sys.exit(1)
    except APIError as e:
        logger.error("Nebius API returned an error: %s", e)
        sys.exit(1)

    logger.info("Call succeeded. Full raw response:")
    print(json.dumps(response.to_dict(), indent=2))

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        logger.warning(
            "Response content was not valid JSON even though the call succeeded. "
            "Native structured output may be partially supported -- inspect raw output above."
        )
        return

    logger.info("Parsed JSON: %s", parsed)

    missing = [f for f in SCHEMA["required"] if f not in parsed]
    if missing:
        logger.warning("Parsed JSON is missing required fields: %s", missing)
    else:
        logger.info(
            "SUCCESS: valid JSON matching schema returned. "
            "Native structured output appears supported."
        )


if __name__ == "__main__":
    api_key = get_api_key()
    run_test(api_key)
