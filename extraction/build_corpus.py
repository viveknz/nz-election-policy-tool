"""
Batch corpus builder.

Runs the real extraction module (extraction/extract.py) across every real
policy text fetched and verified so far, and saves the results as a single
JSON corpus file. This is the actual multi-party dataset that Topic-Match and
the rest of the app will be built against -- not invented examples.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python -m extraction.build_corpus
"""

import json
import logging
import os

from extraction.extract import get_client, extract_policy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("build_corpus")

OUTPUT_PATH = "data/policies.json"

# Every entry here is real text fetched directly from the party's own page and
# verified during Phase 1 source profiling (docs/04_source_profiles.md). None
# of this is invented.
POLICIES = [
    {
        "party": "Labour",
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
    },
    {
        "party": "Te Pati Maori",
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
    },
    {
        "party": "National",
        "source_url": "https://www.national.org.nz/policies/flexible-use-of-paid-parental-leave",
        # This one is a genuine test of explicit "no cost" language, not
        # silence -- a different case from every other policy in this corpus.
        "text": """
Flexible Use of Paid Parental Leave

National will modernise paid parental leave rules by giving parents more
flexibility to share their leave entitlements.

Under current rules, a birth parent can transfer part of their leave
entitlement to their partner, but they are not allowed to take that leave at
the same time. Parents are also not entitled to alternate leave between
themselves, for example one month on and one month off each.

National will modernise outdated parental leave rules by allowing parents to
divide their paid leave between them in the way they think is best: by taking
it at the same time, one after the other or in overlapping instalments.

This is a simple, pragmatic change that will come at no extra cost to the
taxpayer. It's also a change that every political party in Parliament except
for Labour supports.
""",
    },
    {
        "party": "National",
        "source_url": "https://www.national.org.nz/news/paid-parental-leave",
        # Real, costed policy per third-party reporting (NZ Herald: $327
        # million over four years) -- but that figure does NOT appear in this
        # page's own HTML text, only in a linked PDF fact sheet. This tests
        # whether extraction correctly reports "no dollar figure in this
        # text" rather than inventing the number it doesn't have in front of
        # it. See docs/04_source_profiles.md for the open question this
        # raises about PDF-only costing.
        "text": """
National to extend and improve paid parental leave

A re-elected National Government will gradually extend paid parental leave
from 26 to 30 weeks by 2029, starting with an increase to 27 weeks in next
year's Budget and followed by further increases in the next two Budgets.

National will also give parents the option of taking some or all of their
paid parental leave at the same time, in any order or combination up to the
full entitlement.

National will fix this by making a Government contribution to a parent's
KiwiSaver while they're on paid parental leave, even if the parent is not
contributing. The contribution will be made at the default rate, applied to
the paid parental leave a person receives, from 1 July 2027.
""",
    },
]


def main():
    client = get_client()
    corpus = []

    for entry in POLICIES:
        logger.info("Extracting: %s - %s", entry["party"], entry["source_url"])
        result = extract_policy(
            client,
            party=entry["party"],
            policy_text=entry["text"],
            source_url=entry["source_url"],
        )
        if result is None:
            logger.error("Extraction failed for %s - %s, skipping.", entry["party"], entry["source_url"])
            continue
        corpus.append(result)
        logger.info("  -> %s", result)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d policies to %s", len(corpus), OUTPUT_PATH)


if __name__ == "__main__":
    main()
