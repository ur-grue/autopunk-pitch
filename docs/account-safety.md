# Account Safety & Isolation (Roadmap P0)

> The prime directive of P0: **one AI-flagged title can terminate the whole Amazon account and
> withhold all accrued royalties.** The catalog is a portfolio with *perfectly correlated tail risk*.
> This document is the blast-radius model the orchestrator enforces. Read before publishing anything.

## 1. Blast-radius model

- **The risk unit is the Amazon ACCOUNT, not the book or the pen name.** Termination kills every
  title, every pen name, and every accrued-but-unpaid royalty under that account at once.
- **Pen names under one account share fate.** Pen-name separation is a *branding* tool, not a *risk*
  isolation tool. Do not mistake "many pen names" for safety.
- **True isolation = separate accounts — but multiple KDP accounts violate KDP ToS** (one account per
  person) and is itself a termination trigger. So we do **not** build an account farm.

**Decision (P0):** **one account · few pen names · low per-account volume · high per-title quality +
disclosure.** Concentrate quality, not volume. This aligns with the roadmap's "one brand deep" (P4):
fewer pen names + deeper read-through = lower detection/velocity surface and a real owned asset.

## 2. AI disclosure posture

- **AI disclosure = YES on every title** (entire work, with extensive editing; tool: Claude /
  Anthropic for text, gpt-image-1 for cover). Non-disclosure is the fast path to termination.
- **Accept the possible ranking cost.** Survival beats a ranking bump.
- **Resolve the disclosure-vs-stigma tension with quality, not concealment:** disclosed work must not
  *read* as AI — that's why the P2 de-patterning gate (AI-tell removal, human-signature revision)
  exists. Disclose honestly; make the prose indistinguishable from a careful human's.

## 3. Cadence (ENFORCED — see `scripts/kdp_orchestrate.py`)

- **≤ 2 publishes / 24h** per account. The orchestrator's `publish-check` refuses the 3rd.
- **≥ 48h between bursts**; stagger series releases 2–3 days apart for new-release visibility.
- **Human-paced.** Robotic submission velocity is itself a detection signal — never batch-publish.

## 4. Clean-read-profile awareness

- KU bot-farm sweeps ban accounts for **suspicious read patterns — even when the author did not cause
  them.** The defense is to never create suspicious patterns:
  - **Never** buy reads/clicks, use click-farms, or incentivize fake KU reads. Organic only.
  - Treat a sudden read spike concentrated in few accounts/regions as a **red flag to watch**, not a
    win — it can get you swept up with the scammers.

## 5. The termination patterns — never do these

Wide multi-account farms · high daily upload velocity · undisclosed AI · click-farm / KU-bot reads ·
mass near-duplicate titles · keyword/category stuffing.

## 6. Per-title pre-publish checklist (the orchestrator gates on these)

- [ ] AI disclosure set = **Yes** (text + cover)
- [ ] `kdp_orchestrate.py publish-check` **passes** (cadence OK)
- [ ] P2 de-patterning gate passed (does **not** read as AI)
- [ ] Human eyeball on cover + blurb
- [ ] Organic launch only (no paid reads/click incentives)
