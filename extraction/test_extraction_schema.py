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

TEST_CASES = [
    {
        "name": "Labour - Graduate Nurse Job Guarantee",
        "source_url": "https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/",
        "text": """
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
""",
        "checks": lambda parsed: {
            "amount is exactly '$525 million'": parsed.get("amount") == "$525 million",
            "is_costed is True": parsed.get("is_costed") is True,
            "start_date mentions 2026 or 2027": any(
                token in (parsed.get("start_date") or "") for token in ["2026", "2027"]
            ),
        },
    },
    {
        "name": "Te Pati Maori - Te Tiriti Entrenchment Policy",
        "source_url": "https://www.maoriparty.org.nz/te_p_ti_m_ori_launches_te_tiriti_entrenchment_policy",
        "text": """
TE PATI MAORI LAUNCHES TE TIRITI ENTRENCHMENT POLICY

Te Pati Maori has today launched its Te Tiriti Entrenchment Policy, a major
constitutional reform package that will make Crown obligations arising from Te
Tiriti legally enforceable and resource the next stage of Maori-led
constitutional transformation.

The policy will:
- establish a $220 million Matike Mai Fund over four years to independently
  resource Maori-led constitutional transformation;
- establish an independent Te Tiriti Commission with powers to investigate
  serious Crown breaches, require remedial action and issue Te Tiriti
  Compliance Orders;
- make Waitangi Tribunal recommendations binding on the Crown;
- restore and resource a national action plan to implement the United Nations
  Declaration on the Rights of Indigenous Peoples within the first 100 days;
  and
- set 2040 as the target for constitutional transformation in Aotearoa.
""",
        # This is a harder case than Labour's clean "from July 2026" -- there's
        # no single clean start date, just a duration ("over four years") and a
        # separate target year (2040) for a different aspect of the policy than
        # the fund itself. This tests whether the model can correctly decline
        # to invent a clean date where the source text doesn't give one, rather
        # than forcing "2040" into start_date when it actually describes a
        # different thing (the constitutional transformation target, not the
        # fund's start).
        "checks": lambda parsed: {
            "amount is exactly '$220 million'": parsed.get("amount") == "$220 million",
            "is_costed is True": parsed.get("is_costed") is True,
            "start_date does not falsely claim a single clean start date": (
                "2040" not in (parsed.get("start_date") or "")
                or "target" in (parsed.get("start_date") or "").lower()
                or "constitutional" in (parsed.get("start_date") or "").lower()
            ),
        },
    },
]

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
        "is_costed": {
            "type": "boolean",
            "description": "True if any dollar figure appears anywhere in the text describing this policy, even if it is not explicitly labelled 'cost' -- for example 'establish a $220 million fund' counts as costed, the same as 'costed at $220 million'.",
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


def run_one_case(client: OpenAI, case: dict) -> bool:
    prompt = (
        "Extract the policy details from this real party policy page text.\n\n"
        "Policy text:\n" + case["text"]
    )

    logger.info("--- Test case: %s ---", case["name"])

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
        return False
    except APIConnectionError as e:
        logger.error("Network-level failure calling Nebius: %s", e)
        return False
    except APIError as e:
        logger.error("Nebius API returned an error: %s", e)
        return False

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Response content was not valid JSON. Raw content below:")
        print(content)
        return False

    # source_url is known -- we fetched this page ourselves -- so it's attached
    # here rather than asked of the model.
    parsed["source_url"] = case["source_url"]

    logger.info("Extraction result:")
    print(json.dumps(parsed, indent=2))

    checks = case["checks"](parsed)
    checks["policy_name is short (<80 chars, no runaway generation)"] = (
        len(parsed.get("policy_name") or "") <= 80
    )
    checks["stated_position is short (<200 chars, no runaway generation)"] = (
        len(parsed.get("stated_position") or "") <= 200
    )
    checks["start_date is short (<60 chars, no runaway generation)"] = (
        len(parsed.get("start_date") or "") <= 60
    )
    checks["start_date has no question marks (sign of hallucinated commentary)"] = (
        "?" not in (parsed.get("start_date") or "")
    )

    logger.info("Sanity checks:")
    all_passed = True
    for check_name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        logger.info("  [%s] %s", status, check_name)
        if not passed:
            all_passed = False

    return all_passed


def run_test(api_key: str) -> None:
    client = OpenAI(base_url=BASE_URL, api_key=api_key)

    results = {}
    for case in TEST_CASES:
        results[case["name"]] = run_one_case(client, case)
        print()  # spacer between cases

    logger.info("=== Summary ===")
    for name, passed in results.items():
        logger.info("  [%s] %s", "PASS" if passed else "FAIL", name)

    if all(results.values()):
        logger.info("All test cases passed.")
    else:
        logger.warning("One or more test cases failed -- review above.")


if __name__ == "__main__":
    api_key = get_api_key()
    run_test(api_key)
