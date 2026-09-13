# NZ Election Policy vs Economic Reality

Built for the **Nebius x NVIDIA Global AI Hackathon** (Best Apps and Agents track).

A voter can ask, in plain English, what any of New Zealand's political parties say
about a topic — and get back each party's own stated position, with a link to their
own page. No opinions, no rankings, no verdicts. Where a party has attached a cost or
date to a claim, the tool can also show how that figure compares to Treasury's or
RBNZ's own published baseline — stated as fact vs. fact, never as a judgement.

See [`docs/00_project_overview.md`](docs/00_project_overview.md) and
[`docs/01_framing.md`](docs/01_framing.md) for the full problem statement and design
rationale.

## The one rule that must never break

**No verdicts. No scores. No ranking parties against each other.**

Every output is: claim → baseline → the comparison, stated plainly, sourced both ways.

## Stack

- **Inference**: [Nebius Token Factory](https://tokenfactory.nebius.com), using NVIDIA
  Nemotron open-source models (Nano for extraction, Super for topic-matching, Ultra for
  fiscal comparison)
- **App**: Streamlit, deployed on Streamlit Community Cloud

## Repo layout

```
recon/    Phase 0 platform recon scripts (Nebius connectivity + structured output tests)
app/      The Streamlit application
docs/     Project framing, data source notes, and recon findings
```

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/viveknz/nz-election-policy-tool.git
   cd nz-election-policy-tool
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Nebius API key as an environment variable:
   ```bash
   export NEBIUS_API_KEY="your-key-here"
   ```
4. Run a recon script to confirm connectivity:
   ```bash
   python recon/test_nebius_call.py
   ```

## Status

Phase 0 (platform recon) complete — see `docs/03_phase0_recon.md`. Phase 1 (data
source profiling and extraction pipeline) in progress.

## License

MIT — see [LICENSE](LICENSE).
