"""
Extraction module.

This is the real, reusable extraction function -- not a test script. It takes
one policy page's raw text and returns the structured schema, with retry logic
for the intermittent JSON-truncation failure documented in
docs/08_extraction_schema.md (Round 4).

Design decisions baked in here, all documented in docs/08_extraction_schema.md:
- source_url and is_costed are NOT asked of the model -- source_url is known by
  the caller, is_costed is derived from whether amount or percentage_target is
  non-empty. Asking the model for either produced hallucination/contradiction
  in testing.
- percentage_target is a separate field from amount, for fiscal commitments
  stated as a share (e.g. "9% of GDP") rather than a dollar figure -- kept
  distinct because Treasury/RBNZ baselines use both formats, and merging them
  into one field would lose which kind of figure is actually being compared
  later.
- temperature=0 on the first attempt only (best default for a factual task);
  retries nudge temperature up slightly, since identical retries at
  temperature=0 can reproduce the exact same wrong output (observed directly:
  three straight retries all returning the placeholder "Launched today").
- Every free-text field is length-constrained; amount also has a regex
  pattern. Unconstrained fields produced repetition loops and hallucination in
  testing.
- Retries on JSON parse failure (typically caused by truncation), not on
  every kind of failure -- an API error is not something a retry fixes.
- amount and start_date are validated against the source text after
  extraction: any numeric content (a year, a dollar figure) that doesn't
  actually appear in the source is discarded rather than trusted. This exists
  because the model has been observed to fabricate plausible-looking values
  (a fully invented ISO date, for one) with no basis in the real text.

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
import re
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
            "description": "One to two sentence plain summary of what the party says it will do, in the party's own terms. Do not include costing, dates, or eligibility detail here -- those go in their own fields. CRITICAL: if the source text is a list of measures/actions, summarize what the list actually contains (e.g. 'raise the minimum wage and double benefit levels'), never a content-free placeholder like 'will implement the following measures' or 'has announced a policy' -- that describes the text's structure, not its substance, and is not acceptable.",
        },
        "amount": {
            "type": "string",
            "maxLength": 40,
            "pattern": "^(\\$[0-9][0-9,\\.]*\\s?(million|billion|m|bn)?)?$",
            "description": "The stated dollar figure, exactly as given in the text, wherever it appears -- including inside an action description like 'establish a $220 million fund' (extract '$220 million'), not only an explicit 'cost:' statement. Use an empty string only if no dollar figure appears anywhere in the text at all. Do NOT use this field for a percentage (e.g. '9% of GDP') -- that goes in percentage_target instead.",
        },
        "percentage_target": {
            "type": "string",
            "maxLength": 40,
            "pattern": "^([0-9]{1,3}(\\.[0-9]+)?%[^\\n]{0,30})?$",
            "description": "A stated percentage-based fiscal commitment, exactly as given (e.g. '9% of GDP'), when the policy quantifies its fiscal ambition as a share of something rather than a dollar amount. Use an empty string if no percentage figure is stated. This is distinct from amount -- a policy can have one, the other, both, or neither.",
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
        "percentage_target",
        "start_date",
    ],
    "additionalProperties": False,
}


def _validate_amount_against_source(value: str, source_text: str, party: str) -> str:
    """
    amount's only safeguard until now was the schema's format regex --
    confirming it LOOKS like a dollar figure, never confirming the actual
    digits are grounded in the source. That gap let through a fabricated
    '$9' for Opportunity's Healthy People policy (a real text that states
    percentages only, no dollar figure at all) -- the model appears to have
    cross-contaminated the '9' from a correctly-extracted '9% of GDP' into a
    fabricated dollar amount. Same fix as percentage_target: require the
    literal '$<number>' pattern in the source text, not just a
    format-valid-looking string.
    """
    if not value:
        return value

    match = re.match(r"\$([0-9][0-9,\.]*)", value)
    if not match:
        return value  # shouldn't happen given the schema's regex, but be safe

    number = match.group(1)
    if not re.search(r"\$\s?" + re.escape(number), source_text):
        logger.warning(
            "Discarding amount for %s -- '$%s' not found as a literal dollar "
            "figure in the source text (likely fabricated): %r",
            party, number, value,
        )
        return ""

    return value


def _validate_percentage_against_source(value: str, source_text: str, party: str) -> str:
    """
    Same fabrication-check principle as _validate_against_source, applied to
    percentage_target -- but checking only that the number appears somewhere
    in the source text was too permissive: it let through '0.8% FTE'
    (fabricated from real text reading '0.8 FTE', no % anywhere) and '40%'
    (fabricated from '2040', a year, by treating a substring of it as a
    percentage). Requires the literal '<number>%' pattern in the source
    text, not just the bare number in isolation.
    """
    if not value:
        return value

    match = re.match(r"([0-9]{1,3}(?:\.[0-9]+)?)%", value)
    if not match:
        return value  # shouldn't happen given the schema's regex, but be safe

    number = match.group(1)
    if not re.search(re.escape(number) + r"\s?%", source_text):
        logger.warning(
            "Discarding percentage_target for %s -- '%s%%' not found as a "
            "literal percentage in the source text (likely fabricated): %r",
            party, number, value,
        )
        return ""

    return value


def _is_placeholder_position(value: str) -> bool:
    """
    Detects a content-free structural placeholder in stated_position --
    e.g. 'The Maori Party will:' or 'will implement the following measures'
    -- observed twice on the same list-style source even after tightening
    the schema's field description, which wasn't strong enough on its own
    to stop the pattern. Treated the same as a JSON parse failure: retry the
    call rather than accept a summary that describes the text's structure
    instead of its substance.
    """
    stripped = value.strip()
    if stripped.endswith(":"):
        return True
    if len(stripped) < 15:
        return True
    return False


def get_client() -> OpenAI:
    """Create the Nebius Token Factory client. Raises if NEBIUS_API_KEY is unset."""
    api_key = os.environ.get("NEBIUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "NEBIUS_API_KEY environment variable not set. "
            "Run: export NEBIUS_API_KEY=\"your-key-here\""
        )
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def _year_tokens(text: str) -> set[str]:
    """Four-digit year-like sequences in a string, e.g. '2027' from '2027-07-01'
    or from '1 July 2027'. Deliberately narrower than 'every digit sequence':
    day/month numbers get reformatted in legitimate, correct ways (a source
    that spells out 'July' won't literally contain '07'), and checking those
    produced a false-positive rejection of a genuinely correct date. Years are
    where the real fabrication risk was actually observed."""
    return set(re.findall(r"(?<!\d)\d{4}(?!\d)", text or ""))


def _validate_against_source(value: str, source_text: str, field_name: str, party: str) -> str:
    """
    Discard a value if it contains a year that doesn't appear anywhere in the
    source text -- a direct fabrication check, added after finding the model
    invent a fully fictional ISO date ('2023-06-14T00:00:00+00:00') for a
    policy whose real text contains no dates at all (docs/08_extraction_schema.md,
    Round 5). Checks years only, not every digit (day/month numbers are
    legitimately reformatted -- e.g. 'July' becoming '07' -- and checking
    those produced a false positive on a correct date). A value with no
    4-digit year is not checked here.
    """
    if not value:
        return value

    value_years = _year_tokens(value)
    if not value_years:
        return value

    source_years = _year_tokens(source_text)
    if not value_years.issubset(source_years):
        logger.warning(
            "Discarding %s for %s -- contains a year not found in the source "
            "text (likely fabricated): %r",
            field_name, party, value,
        )
        return ""

    return value


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
        "For stated_position specifically: summarize the actual substance of "
        "what the party will do, never a content-free description of the "
        "text's structure. For example, if the source is a press release "
        "announcing a policy today, a BAD stated_position is 'Launched "
        "today' -- true, but says nothing about the policy itself. A GOOD "
        "stated_position states what the policy actually does, e.g. 'Make "
        "Crown obligations under Te Tiriti legally enforceable and fund "
        "Maori-led constitutional transformation.'\n\n"
        f"Policy text:\n{policy_text}"
    )

    for attempt in range(1, max_retries + 1):
        # Nudge temperature up on retries only. Round 5/6 found this model can
        # return the IDENTICAL output on repeated identical calls at
        # temperature=0 -- observed here as three straight retries all
        # producing "Launched today". Retrying the identical request at
        # temperature=0 can never escape a deterministic bad output; a small
        # nudge gives later attempts an actual chance to differ. The first
        # attempt stays at 0 for the consistency benefits documented earlier.
        attempt_temperature = 0 if attempt == 1 else 0.3

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
                temperature=attempt_temperature,
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

        if _is_placeholder_position(parsed.get("stated_position", "")):
            logger.warning(
                "stated_position for %s (attempt %d/%d) is a content-free "
                "placeholder, not a real summary -- retrying: %r",
                party, attempt, max_retries, parsed.get("stated_position"),
            )
            continue

        # source_url is known by the caller. amount, percentage_target, and
        # start_date are all validated against the actual source text before
        # being trusted -- see the validation helpers' docstrings.
        # is_costed is True if EITHER a dollar amount or a percentage target
        # was found and validated -- a policy quantifying its fiscal
        # ambition as "9% of GDP" is just as much a checkable claim as one
        # quantifying it in dollars, and both matter for later fiscal
        # comparison against Treasury/RBNZ baselines (which themselves use
        # both dollar and %GDP figures -- see docs/02_data_sources.md).
        parsed["amount"] = _validate_amount_against_source(
            parsed.get("amount", ""), policy_text, party
        )
        parsed["percentage_target"] = _validate_percentage_against_source(
            parsed.get("percentage_target", ""), policy_text, party
        )
        parsed["start_date"] = _validate_against_source(
            parsed.get("start_date", ""), policy_text, "start_date", party
        )
        parsed["source_url"] = source_url
        parsed["is_costed"] = bool(parsed.get("amount")) or bool(parsed.get("percentage_target"))

        return parsed

    logger.error(
        "Extraction failed for %s after %d attempts -- every attempt either "
        "returned unparseable JSON or a content-free placeholder summary.",
        party, max_retries,
    )
    return None
