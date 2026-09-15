"""
Phase 1: Extraction schema test.

Purpose: test the core extraction schema against real, actually-fetched policy
text (Labour's Graduate Nurse Job Guarantee page), not invented text. Confirms
whether native structured output (proven working in Phase 0) holds up on real,
messy, multi-section policy content -- not just a clean two-sentence example.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python test_extraction_schema.py
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
logger = logging.getLogger("extraction_schema_test")

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

# Real text fetched directly from labour.org.nz/election-policy-pages/
# graduate-nurse-job-guarantee/ on 13 Sep 2026. Trimmed to the sections relevant
# to extraction (key facts, eligibility/cost) -- the full page also has a
# district-by-district nursing data table and an FAQ section repeating the same
# facts, both left out here since this test is about the core schema, not
# every section type on the page.
REAL_POLICY_TEXT = """
Graduate Nurse Job Guarantee

Labour will offer every eligible New Zealand-trained graduate nurse a job in our
health system.

Key facts:
- Every eligible New Zealand-trained graduate nurse will be offered a job in the
  health system
- Around 2,400 nurse graduates every year will get a job offer
- Roles will be offered on graduation rather than staggered throughout the year,
  starting in 2027, and will be at least 0.8 FTE
- Graduate nurses will be offered jobs through the existing Advanced Choice of
  Employment (ACE) and primary care employment schemes
- Registered and enrolled nurses are eligible
- Double funding for graduate nursing roles in primary and community healthcare
- Costed at $525 million. Funded from the Budget's Vote Health cost-pressure
  funding

Eligibility and cost:
Job offers will depend on graduates passing their State Final examination and
required pre-employment checks. Graduates must also be a New Zealand citizen,
permanent resident, returning resident visa holder or Australian citizen, and
have completed their nursing qualification at a New Zealand tertiary
institution. The cost of the Graduate Nurse Job Guarantee is $525 million. It
will be funded from health cost-pressure funding. It will apply to graduates
sitting their State Final examination from July 2026 onwards.
"""

SOURCE_URL = "https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/"

SCHEMA = {
    "type": "object",
    "properties": {
        "policy_name": {"type": "string"},
        "party": {"type": "string"},
        "stated_position": {
            "type": "string",
            "description": "One to two sentence plain summary of what the party says it will do, in the party's own terms.",
        },
        "is_costed": {"type": "boolean"},
        "amount": {
            "type": "string",
            "maxLength": 40,
            "pattern": "^(\\$[0-9][0-9,\\.]*\\s?(million|billion|m|bn)?)?$",
            "description": "The stated dollar figure, exactly as given in the text (e.g. '$525 million'). Use an empty string only if no dollar figure is stated anywhere in the text. Do not add explanation -- the figure only.",
        },
        "start_date": {
            "type": "string",
            "description": "The stated start date or trigger condition, exactly as given in the text (e.g. 'from July 2026'). Use an empty string only if no date or trigger is stated anywhere in the text.",
        },
    },
    "required": [
        "policy_name",
        "party",
        "stated_position",
        "is_costed",
        "amount",
        "start_date",
    ],
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

    prompt = (
        "Extract the policy details from this real party policy page text.\n\n"
        "Policy text:\n" + REAL_POLICY_TEXT
    )

    logger.info("Testing extraction schema against real Labour policy text on %s", MODEL)

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
            max_tokens=800,
        )
    except BadRequestError as e:
        logger.error("Nebius rejected the request: %s", e)
        sys.exit(1)
    except APIConnectionError as e:
        logger.error("Network-level failure calling Nebius: %s", e)
        sys.exit(1)
    except APIError as e:
        logger.error("Nebius API returned an error: %s", e)
        sys.exit(1)

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Response content was not valid JSON. Raw content below:")
        print(content)
        return

    logger.info("Parsed extraction result (before attaching known metadata):")
    print(json.dumps(parsed, indent=2))

    # source_url is known -- we fetched this page ourselves -- so it's attached
    # here rather than asked of the model, removing that whole field from the
    # degenerate-repetition risk seen earlier.
    parsed["source_url"] = SOURCE_URL

    logger.info("Final result with source_url attached:")
    print(json.dumps(parsed, indent=2))

    # Sanity checks against what we know is actually true from the real page.
    checks = {
        "amount is exactly '$525 million' (no garbage/repetition)": parsed.get("amount") == "$525 million",
        "is_costed is True": parsed.get("is_costed") is True,
        "start_date mentions July 2026 or 2027": any(
            token in (parsed.get("start_date") or "") for token in ["2026", "2027"]
        ),
    }

    logger.info("Sanity checks against known-correct facts from the real page:")
    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        logger.info("  [%s] %s", status, check_name)

    if all(checks.values()):
        logger.info("All sanity checks passed.")
    else:
        logger.warning("One or more sanity checks failed -- review the extraction above.")


if __name__ == "__main__":
    api_key = get_api_key()
    run_test(api_key)
