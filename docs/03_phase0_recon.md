# Phase 0: Nebius Recon

The point of this phase is to find out what Nebius actually lets you do before writing
any extraction or retrieval code on top of it. Same reasoning as the bushfire build's
Phase 0 — cheaper to discover a platform limit now than after three days of building
against an assumption.

**Target: 60-90 minutes.**

---

## Step 1: Create an account and find Token Factory

1. Go to the hackathon page and follow the participant onboarding link — Nebius
   usually issues hackathon credits automatically on signup through the event page
   rather than a normal paid signup. Check the hackathon's Resources tab for this
   before creating an account the normal way.
2. Once in, find **Token Factory** in the console. This is the piece that matters —
   it's Nebius's hosted-model API, the equivalent of what the Genie Conversations API
   was for the bushfire build.
3. Confirm you can see a list of available models. You specifically need **at least
   one NVIDIA open-source model** listed and selectable — that's the hackathon's hard
   requirement.

**Record:** which NVIDIA models are available (the hackathon mentions Nemotron 3
Ultra, Nano, and Super as options — different sizes for different jobs).

## Step 2: Get an API key and make one call

1. Find the API key / credentials section.
2. Make the simplest possible call — send one line of text, get one line back. Nebius
   Token Factory is designed to be OpenAI-API-compatible in most cases, so if you've
   ever called any hosted LLM API before, the shape will be familiar: an endpoint URL,
   a bearer token, a JSON body with a model name and a messages array.

**Record:** does a basic call succeed, and what does a raw response look like (so you
know what you're parsing later).

## Step 3: Confirm structured output works

This is the piece the extraction pipeline depends on entirely — turning a policy
page's messy text into a clean JSON object with fields like `policy_name`,
`stated_position`, `is_costed`, `amount`, `start_date`.

1. Check whether Token Factory supports **JSON Schema-constrained output** (sometimes
   called "structured outputs" or "function calling" depending on the API), where you
   give the model a schema and it's forced to return valid JSON matching it.
2. If it does, test it with a tiny schema on a tiny piece of text — feed it two
   sentences describing a fake policy and see if it returns clean JSON.
3. If it doesn't support constrained output directly, the fallback is prompting the
   model to return JSON and then validating it yourself in code — workable, but less
   reliable, and worth knowing now rather than discovering it mid-build.

**Record:** native structured output yes/no. If no, note that a validation/retry step
must be built into the extraction pipeline from the start.

## Step 4: Confirm which model size you'll actually use where

The hackathon description suggests using different Nemotron sizes for different jobs
— the larger reasoning model for hard questions, smaller ones for routine calls. For
this project that maps to:

- **Extraction** (policy page → structured JSON): a smaller/faster model is probably
  fine, since this is closer to a formatting task than a reasoning task
- **Topic matching** (plain-English query → relevant extracted policies across six
  parties with different wording): needs more reasoning, since it has to recognise
  that "childcare" relates to "Paid Parental Leave" without being told so explicitly
- **Fiscal comparison** (does this claim sit near the Treasury baseline): needs
  careful, cautious reasoning since a wrong comparison here is the worst possible
  failure mode for this project specifically

Test the same query against two model sizes if time allows, and note whether the
larger model is worth its extra cost/latency for the topic-matching step. Don't decide
this permanently yet — just get a first impression.

## Step 5: Confirm deployment path

The hackathon submission needs a working, hosted demo URL. Check:

1. Does Nebius offer **Serverless Endpoints** for deploying the finished app itself
   (not just calling models), or is Token Factory purely an API you call from an app
   hosted somewhere else (e.g. your own small web server, or a simple free host)?
2. If the app needs to live somewhere other than Nebius, confirm what that will be
   before building — Streamlit Community Cloud, a small VM, or similar. This decision
   affects how you structure the code from day one, the same way knowing Databricks
   Apps existed shaped the bushfire build's architecture.

**Record:** where the finished app will actually run.

---

## Go/No-Go gate

Move to building the extraction pipeline only once:

- [ ] Token Factory account works, at least one NVIDIA open model is callable
- [ ] A basic API call succeeds and you understand the response shape
- [ ] Structured output capability is known (yes with native support, or no with a
      validation fallback planned)
- [ ] You know where the finished app will be hosted

Nothing else in this project can start until the second item is confirmed — every
later step calls this API.

## What to report back

```
Account/Token Factory: working / blocked
NVIDIA models available: [list]
Basic call: succeeded / failed, response shape:
Structured output: native / fallback needed
Model size test: [any first impressions]
Deployment path: 
```
