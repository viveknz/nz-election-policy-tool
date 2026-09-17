"""
Topic-Match module.

Given a voter's plain-English query and the real extracted policy corpus
(data/policies.json), returns the subset of policies relevant to that query
-- across all parties, no ranking, no verdict, just "these are relevant."

Design, following the architecture decision in docs/09_architecture.md and
the fabrication lessons in docs/08_extraction_schema.md:

- The model NEVER generates policy content. It only selects ids from a list
  it's given. The schema's `enum` is built dynamically from the corpus's real
  ids each call, so the model is structurally constrained to choose only from
  ids that actually exist -- it cannot select (or invent) an id that isn't
  real, the same way earlier extraction fields were constrained to prevent
  fabrication, but enforced at the schema level this time rather than only
  checked after the fact.
- A post-hoc filter (discard any returned id not in the known set) is kept as
  defense in depth even though the enum constraint should already prevent
  this -- cheap insurance, consistent with every other module in this
  project never trusting a single layer of protection alone.
- The app renders the actual policy content (party, stated position, source
  link) straight from the validated corpus for whichever ids matched -- never
  from anything the model said in free text. This means Topic-Match can only
  ever be wrong about *relevance* (missed or over-included a real policy); it
  cannot misquote a position or fabricate a source, because it never touches
  that content at all.

MODEL NOTE: this currently uses the same Nemotron-3-Nano model already
confirmed working in Phase 0/1, NOT the Nemotron-3-Super model the
architecture doc calls for. The exact Super model string has not been
confirmed against the Nebius console the way Nano's was (and Nano's initial
guess was wrong -- see docs/03_phase0_recon.md). Swap MODEL below once you've
confirmed Super's exact string from the console's "Set up and chat as code"
tab, the same way we found Nano's.

Usage:
    from matching.match import get_client, load_corpus, match_topics

    client = get_client()
    corpus = load_corpus("data/policies.json")
    matches = match_topics(client, "what does each party say about housing", corpus)
"""

import json
import logging

from openai import OpenAI, APIError, APIConnectionError, BadRequestError

logger = logging.getLogger("topic_match")

BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
# TODO: confirm the real Nemotron-3-Super model string from the Nebius
# console and swap it in here -- do NOT guess it, per the lesson in
# docs/03_phase0_recon.md.
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
MAX_TOKENS = 1000
MAX_RETRIES = 3


def get_client() -> OpenAI:
    """Re-exported from extraction.extract for convenience -- same client,
    same Nebius endpoint, one place the API key check lives."""
    from extraction.extract import get_client as _get_client
    return _get_client()


def load_corpus(path: str) -> list[dict]:
    """Load the real extracted policy corpus built by extraction/build_corpus.py."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _lightweight_view(corpus: list[dict]) -> list[dict]:
    """Only what the model needs to judge relevance -- id, party, policy
    name, and the short stated position. Deliberately excludes amount,
    percentage_target, start_date, and source_url: none of those help judge
    topical relevance, and keeping them out keeps the prompt small (the
    context-saving goal from the architecture decision) and keeps this
    module from ever touching fields it has no reason to see."""
    return [
        {
            "id": p["id"],
            "party": p["party"],
            "policy_name": p["policy_name"],
            "stated_position": p["stated_position"],
        }
        for p in corpus
    ]


def match_topics(
    client: OpenAI,
    query: str,
    corpus: list[dict],
    max_retries: int = MAX_RETRIES,
) -> list[dict]:
    """
    Return the subset of corpus entries relevant to the query.

    Returns full corpus records (not just ids) for whichever policies
    matched, in the same order they appear in the corpus (not a ranking --
    just a stable, neutral order). Returns an empty list if nothing matches
    or if extraction fails after retries -- never guesses.
    """
    known_ids = [p["id"] for p in corpus]
    if not known_ids:
        logger.warning("Empty corpus passed to match_topics -- nothing to match against.")
        return []

    lightweight = _lightweight_view(corpus)

    schema = {
        "type": "object",
        "properties": {
            "matched_ids": {
                "type": "array",
                "items": {"type": "string", "enum": known_ids},
                "maxItems": len(known_ids),
                "description": "Ids of policies relevant to the query. Empty array if none are relevant -- do not force a match.",
            },
        },
        "required": ["matched_ids"],
        "additionalProperties": False,
    }

    prompt = (
        "A voter asked the following question. Select every policy below that "
        "is genuinely relevant to what they're asking about, across all "
        "parties. A voter's question may not use the same words a party uses "
        "for its own policy -- match on genuine topical relevance, not exact "
        "keyword overlap. Do not select a policy that is only loosely or "
        "tangentially related. If nothing is relevant, return an empty list.\n\n"
        f"Voter's question: {query}\n\n"
        f"Policies:\n{json.dumps(lightweight, indent=2)}"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "topic_match",
                        "schema": schema,
                        "strict": True,
                    },
                },
                max_tokens=MAX_TOKENS,
                temperature=0,
            )
        except (BadRequestError, APIConnectionError, APIError) as e:
            logger.error("API error during topic match (attempt %d/%d): %s", attempt, max_retries, e)
            return []

        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("JSON parse failure on topic match (attempt %d/%d), retrying.", attempt, max_retries)
            continue

        matched_ids = parsed.get("matched_ids", [])

        # Defense in depth: even though the schema's enum should already
        # constrain this, never trust a single layer alone (docs/08_extraction_schema.md).
        valid_ids = [i for i in matched_ids if i in known_ids]
        if len(valid_ids) != len(matched_ids):
            logger.warning(
                "Model returned %d id(s) not in the known corpus -- discarded.",
                len(matched_ids) - len(valid_ids),
            )

        id_to_policy = {p["id"]: p for p in corpus}
        return [id_to_policy[i] for i in valid_ids]

    logger.error("Topic match failed after %d attempts -- all returned unparseable JSON.", max_retries)
    return []
