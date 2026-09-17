"""
Test the Fetch module against two known real cases:
- a page that should fetch successfully (Labour's Graduate Nurse page)
- a page that should be correctly skipped due to robots.txt (NZ First,
  confirmed blocked in docs/04_source_profiles.md)

Usage:
    python -m fetch.test_fetch
"""

import logging

from fetch.fetch import fetch_policy_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("test_fetch")


def main():
    logger.info("--- Test: should succeed ---")
    text = fetch_policy_text(
        "https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/"
    )
    if text:
        logger.info("Fetched %d characters. First 300:\n%s", len(text), text[:300])
    else:
        logger.error("Expected success but got None -- check output above for the reason.")

    print()
    logger.info("--- Test: should be blocked by robots.txt ---")
    blocked = fetch_policy_text("https://www.nzfirst.nz/policy")
    if blocked is None:
        logger.info("Correctly returned None -- robots.txt block respected.")
    else:
        logger.error("Expected None (robots.txt block) but got content -- investigate.")


if __name__ == "__main__":
    main()
