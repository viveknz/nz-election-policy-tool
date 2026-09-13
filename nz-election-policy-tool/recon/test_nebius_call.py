"""
Phase 0, Step 2: Basic Nebius Token Factory connectivity test.

Purpose: confirm the API key works and see the raw response shape
from Nemotron-3-Nano-30B-A3B before building anything on top of it.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python test_nebius_call.py
"""

import os
import sys
import logging
import json

from openai import OpenAI, APIError, APIConnectionError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("nebius_test")

# Confirmed from Nebius's own playground "code" tab (Step 2, Phase 0 recon) --
# do not guess these; re-copy from the console if a model changes.
BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"


def get_api_key() -> str:
    key = os.environ.get("NEBIUS_API_KEY")
    if not key:
        logger.error(
            "NEBIUS_API_KEY environment variable not set. "
            "Run: export NEBIUS_API_KEY=\"your-key-here\""
        )
        sys.exit(1)
    return key


def make_test_call(api_key: str) -> None:
    client = OpenAI(base_url=BASE_URL, api_key=api_key)

    logger.info("Sending test request to model: %s", MODEL)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "Reply with exactly: hello from nebius"}
            ],
            max_tokens=50,
        )
    except APIConnectionError as e:
        logger.error("Network-level failure calling Nebius: %s", e)
        sys.exit(1)
    except APIError as e:
        logger.error("Nebius API returned an error: %s", e)
        sys.exit(1)

    logger.info("Call succeeded. Full raw response:")
    print(json.dumps(response.to_dict(), indent=2))

    try:
        reply_text = response.choices[0].message.content
        logger.info("Extracted reply text: %r", reply_text)
    except (IndexError, AttributeError):
        logger.warning(
            "Could not extract choices[0].message.content -- "
            "check the raw response above for the actual shape."
        )


if __name__ == "__main__":
    api_key = get_api_key()
    make_test_call(api_key)
