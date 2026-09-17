"""
Test Topic-Match against real queries, not invented ones.

Queries are drawn from docs/05_voter_topics.md's actual sourced 2026 voter
concerns (cost of living, healthcare, housing) plus one deliberately
unrelated query (immigration) to confirm the module correctly returns an
empty list rather than forcing a match.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python -m matching.test_match
"""

import logging

from matching.match import get_client, load_corpus, match_topics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("test_match")

CORPUS_PATH = "data/policies.json"

# Real voter concerns per docs/05_voter_topics.md (Ipsos Issues Monitor,
# 2026), not invented examples. The last query is deliberately unrelated to
# anything in the corpus, to test that an empty result is returned honestly
# rather than a forced/loose match.
TEST_QUERIES = [
    "what does each party say about paid parental leave",
    "what is being done about the cost of living",
    "what are the parties doing about healthcare",
    "what does anyone say about immigration policy",  # expect: no matches
]


def main():
    client = get_client()
    corpus = load_corpus(CORPUS_PATH)
    logger.info("Loaded %d policies from %s", len(corpus), CORPUS_PATH)

    for query in TEST_QUERIES:
        logger.info("--- Query: %r ---", query)
        matches = match_topics(client, query, corpus)
        if not matches:
            logger.info("  No matches.")
        for m in matches:
            logger.info("  -> [%s] %s: %s", m["party"], m["policy_name"], m["stated_position"][:80])
        print()


if __name__ == "__main__":
    main()
