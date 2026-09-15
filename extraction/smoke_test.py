"""
Smoke test for extraction/extract.py.

Confirms the real, reusable module reproduces what the exploratory
test_extraction_schema.py already proved, before this module is trusted as the
pipeline's actual extraction step. Same two real test cases, same known-correct
facts to check against.

Usage:
    export NEBIUS_API_KEY="your-key-here"
    python extraction/smoke_test.py
"""

import logging

from extraction.extract import get_client, extract_policy

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("extraction_smoke_test")

LABOUR_TEXT = """
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

TE_PATI_MAORI_TEXT = """
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
"""


def main():
    client = get_client()

    logger.info("--- Smoke test: Labour ---")
    labour_result = extract_policy(
        client,
        party="Labour",
        policy_text=LABOUR_TEXT,
        source_url="https://www.labour.org.nz/election-policy-pages/graduate-nurse-job-guarantee/",
    )
    print(labour_result)
    if labour_result is None:
        logger.error("Labour extraction returned None -- module failure.")
    else:
        assert labour_result["amount"] == "$525 million", "Labour amount mismatch"
        assert labour_result["is_costed"] is True, "Labour is_costed should be True"
        assert labour_result["source_url"].startswith("https://www.labour.org.nz"), "source_url wrong"
        logger.info("Labour smoke test PASSED")

    logger.info("--- Smoke test: Te Pati Maori ---")
    tpm_result = extract_policy(
        client,
        party="Te Pati Maori",
        policy_text=TE_PATI_MAORI_TEXT,
        source_url="https://www.maoriparty.org.nz/te_p_ti_m_ori_launches_te_tiriti_entrenchment_policy",
    )
    print(tpm_result)
    if tpm_result is None:
        logger.error("Te Pati Maori extraction returned None -- module failure.")
    else:
        assert tpm_result["amount"] == "$220 million", "Te Pati Maori amount mismatch"
        assert tpm_result["is_costed"] is True, "Te Pati Maori is_costed should be True"
        logger.info("Te Pati Maori smoke test PASSED")


if __name__ == "__main__":
    main()
