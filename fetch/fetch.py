"""
Fetch module.

Retrieves the full raw text of a policy page automatically, replacing the
manual copy-paste-and-trim process used to build the corpus so far. No
chunking, no vectorization -- Nemotron-3-Nano's 262K token context window
(confirmed in docs/03_phase0_recon.md) comfortably fits a full real party
page, so there's no context-length problem to solve here.

Respects robots.txt before fetching -- NZ First's site (docs/04_source_profiles.md)
already disallows automated access, and this module needs to recognize and
skip that the same way, not silently ignore it.

Usage:
    from fetch.fetch import fetch_policy_text

    text = fetch_policy_text("https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/")
"""

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("fetch")

USER_AGENT = (
    "Mozilla/5.0 (compatible; NZElectionPolicyBot/1.0; "
    "+https://github.com/viveknz/nz-election-policy-tool)"
)
TIMEOUT_SECONDS = 15

# Tags whose text is noise, not policy content -- scripts, styles, and
# site chrome (nav/footer/header) repeat across every page on a site and
# would otherwise pollute every extraction with the same boilerplate.
NOISE_TAGS = ["script", "style", "nav", "footer", "header"]


def _check_robots(url: str) -> bool:
    """
    Returns False if the site's robots.txt disallows fetching this URL for
    our user agent. If robots.txt itself can't be read (missing, network
    error), errs toward allowing the fetch rather than blocking on an
    unrelated failure -- but logs clearly either way, since a silent
    assumption here is exactly the kind of thing this project's discipline
    has caught before.

    Deliberately does NOT use RobotFileParser.read(), which fetches
    robots.txt internally via urllib.request using Python's default user
    agent -- a generic string many WAFs/CDNs block or challenge, causing a
    false "disallow everything" even on sites that allow normal crawling
    (confirmed: Labour's real page fetches fine via our own requests
    session, but was wrongly reported as robots.txt-blocked before this
    fix). Instead, robots.txt is fetched with the same working session and
    user agent used for the real page, then handed to RobotFileParser.parse().
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = RobotFileParser()
    try:
        response = requests.get(
            robots_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
        )
        if response.status_code == 404:
            # No robots.txt at all -- per spec, this means everything is
            # allowed, not that everything is disallowed.
            return True
        response.raise_for_status()
        rp.parse(response.text.splitlines())
    except requests.exceptions.RequestException as e:
        logger.warning(
            "Could not read robots.txt at %s (%s) -- proceeding, since an "
            "unreadable robots.txt is not the same as an explicit disallow.",
            robots_url, e,
        )
        return True

    return rp.can_fetch(USER_AGENT, url)


def fetch_policy_text(url: str, timeout: int = TIMEOUT_SECONDS) -> str | None:
    """
    Fetch a policy page and return its cleaned, full text. Returns None if
    robots.txt disallows the fetch, the request fails, or the response isn't
    usable -- never guesses or returns partial/placeholder content.
    """
    if not _check_robots(url):
        logger.error(
            "robots.txt disallows fetching %s -- skipping. If this party "
            "must stay in scope, see docs/07_backlog.md for the manual-"
            "capture pattern already used for NZ First.",
            url,
        )
        return None

    try:
        response = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=timeout
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("Fetch failed for %s: %s", url, e)
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    cleaned = "\n".join(lines)

    if not cleaned:
        logger.warning("Fetched %s but extracted no text content -- check the page manually.", url)
        return None

    return cleaned
