"""
Batch corpus builder.

Fetches each party's real policy pages automatically (fetch/fetch.py -- no
manual copy-paste, no chunking, no vectorization; Nemotron-3-Nano's 262K
token context window comfortably fits a full real page) and runs the real
extraction module across all of them, saving the results as a single JSON
corpus file.

NZ First is deliberately excluded -- robots.txt disallows automated access
(confirmed by Anthropic's own fetch tool; our own Fetch module's generic
user agent wasn't blocked, but using that to route around what's clearly an
intentional block would go against this project's transparency standard --
see docs/07_backlog.md and docs/08_extraction_schema.md Round 8). NZ First
is tracked as a manual-capture backlog item, not fetched here.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python -m extraction.build_corpus
"""

import json
import logging
import os
import re

from extraction.extract import get_client, extract_policy
from fetch.fetch import fetch_policy_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("build_corpus")

OUTPUT_PATH = "data/policies.json"

# Real URLs, verified during Phase 1 source profiling (docs/04_source_profiles.md).
# NZ First excluded -- see module docstring.
SOURCES = [
    ("Labour", "https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/"),
    ("Te Pati Maori", "https://www.maoriparty.org.nz/te_p_ti_m_ori_launches_te_tiriti_entrenchment_policy"),
    ("Te Pati Maori", "https://www.maoriparty.org.nz/income"),
    ("National", "https://www.national.org.nz/policies/flexible-use-of-paid-parental-leave"),
    ("National", "https://www.national.org.nz/news/paid-parental-leave"),
    ("Greens", "https://www.greens.org.nz/children_policy"),
    ("Opportunity", "https://www.opportunity.org.nz/healthy_people"),
]


def _slugify(text: str) -> str:
    """Lowercase, alphanumeric-and-dashes only, collapsed. Used to build a
    stable id from party + policy_name -- computed here, never asked of the
    model, same principle as every other derived field."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug


def main():
    client = get_client()
    corpus = []

    for party, url in SOURCES:
        logger.info("Fetching: %s - %s", party, url)
        text = fetch_policy_text(url)
        if text is None:
            logger.error("Fetch failed for %s - %s, skipping.", party, url)
            continue

        logger.info("Extracting: %s - %s (%d chars fetched)", party, url, len(text))
        result = extract_policy(
            client,
            party=party,
            policy_text=text,
            source_url=url,
        )
        if result is None:
            logger.error("Extraction failed for %s - %s, skipping.", party, url)
            continue

        # Stable id, computed here rather than asked of the model -- used by
        # Topic-Match to reference a policy without ever needing to echo
        # back or reconstruct its content.
        result["id"] = _slugify(f"{party}-{result['policy_name']}")

        corpus.append(result)
        logger.info("  -> %s", result)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d policies to %s", len(corpus), OUTPUT_PATH)


if __name__ == "__main__":
    main()
