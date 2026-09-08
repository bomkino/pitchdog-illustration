# pitch.dog Illustration

A production-grade Agent Skill for making pitch.dog's tiny editorial visual
poems: one impossible relationship, one ordinary act, exact identity, imperfect
ink, a restrained accent, and enough empty field for the thought to breathe.

> Find one impossible truth. Draw only what it needs. Stop.

[![License: 0BSD](https://img.shields.io/badge/license-0BSD-111111.svg)](LICENSE)

![Current 22 illustration contact sheet](skills/pitchdog-illustration/assets/references/approved-22-contact-sheet.png)

## What it does

- conceives one poetic visual metaphor before prompting;
- generates one candidate at a time and inspects it at actual-pixel size;
- preserves exact human and dog identity without drifting into portrait realism;
- audits or surgically refines supplied images without approval theatre;
- maps website narrative needs before making decorative filler;
- rejects caption rescue, yellow AI cast, white stages, glossy vectors, generic
  dogs, extra limbs, unequal groups, and polished emptiness;
- records status, rationale, placement, alt text, dimensions, and SHA-256.

It is not a pastel filter, mascot system, named-artist shortcut, prompt suffix,
or licence to make unrelated work look like pitch.dog.

## Reference pack

The source skill includes 58 full-resolution active references:

- **22 current locked finals:** execution, identity, and mature visual-law gate;
- **30 approved website illustrations:** narrative breadth, reuse, placement,
  and metaphor-collision map;
- **6 Golden Six:** conceptual ancestry for wit and editorial economy.

Two contact sheets provide fast series scans. Every file has SHA-256,
dimensions, tier, status authority, source lineage, and rights basis in
[`assets/reference-manifest.json`](skills/pitchdog-illustration/assets/reference-manifest.json).

Across project history there are 67 unique approved-baseline-or-current-locked
artworks: 48 in the dated owner-approved baseline plus 22 current locked
finals, minus three shared Manali works. This arithmetic does not invent owner
acceptance for every current file. Nine superseded dog solos remain in
[`archive/historical-approved-dogs-superseded/`](archive/historical-approved-dogs-superseded/)
for provenance only; they are not live likeness or style authority.

Known acceptance evidence covers 53 unique works across eras: all 48 baseline
works plus five new current approvals. Within the current 22, eight files are
owner-accepted—the three reused Manali standards, Juno 01, and Kumail 01–04;
the other 14 remain honestly labelled current locked finals.

Real family photos and the third-party original reference are excluded.

Two dated website files—`28-go-get-em.png` and `30-lost-page.png`—remain in the
owner-approved historical set as metaphor and placement evidence, but the
manifest prohibits their pre-rebuild Juno as current identity/scale authority.
Current Juno work must use the locked 22-piece set.

![Approved website 30 contact sheet](skills/pitchdog-illustration/assets/references/website-30-contact-sheet.png)

## Install

### Codex and Agent Skills clients

Install for Codex:

```bash
npx skills add bomkino/pitchdog-illustration \
  --skill pitchdog-illustration \
  -g \
  -a codex \
  -y
```

Install for every agent supported by the `skills` CLI:

```bash
npx skills add bomkino/pitchdog-illustration \
  --skill pitchdog-illustration \
  -g \
  -a '*' \
  -y
```

The package follows the open [Agent Skills specification](https://agentskills.io/specification).

Current release: [v1.0.2 notes](https://github.com/bomkino/pitchdog-illustration/releases/tag/v1.0.2).

### ChatGPT desktop

1. Download [`pitchdog-illustration.skill`](https://github.com/bomkino/pitchdog-illustration/releases/latest/download/pitchdog-illustration.skill).
2. Open it with ChatGPT.
3. Review the scan and install.

This is the documented/intended desktop flow. Native desktop installation was
not independently receipt-verified for v1.0.1; web / Cloud Work was.

### ChatGPT web / Cloud Work

1. Download [`pitchdog-illustration.zip`](https://github.com/bomkino/pitchdog-illustration/releases/latest/download/pitchdog-illustration.zip).
2. Open **Profile → Skills → Create → Upload from your computer**. Some
   workspaces expose the same page under **Plugins → Skills**.
3. Review the scan and install.

The repository keeps the default ChatGPT-portable archives below 25,000,000
bytes, a budget based on the Skills uploader gate observed in the tested
ChatGPT web / Cloud Work workspace on 6 August 2026. Product and workspace
limits can change. The package retains all 58 references as sRGB display
derivatives plus each immutable canonical source SHA-256. Nothing is omitted. Download
[`pitchdog-illustration-full.skill`](https://github.com/bomkino/pitchdog-illustration/releases/latest/download/pitchdog-illustration-full.skill)
or [`pitchdog-illustration-full.zip`](https://github.com/bomkino/pitchdog-illustration/releases/latest/download/pitchdog-illustration-full.zip)
for the full-resolution archival edition.

OpenAI documents separate desktop and web installation. Workspace permissions
may control uploading, sharing, and installation. See OpenAI's current
[Skills in ChatGPT](https://help.openai.com/en/articles/20001066) guide.

## Use

```text
Use $pitchdog-illustration to create one website illustration for this exact copy. Inspect the current library first and make only a proven narrative gap.
```

```text
Use $pitchdog-illustration in Audit mode. Inspect this candidate at full size. Do not edit it.
```

```text
Use $pitchdog-illustration in Refine mode. Change only the accidental extra paw; preserve the face, metaphor, field, scale, and composition.
```

```text
Use $pitchdog-illustration to map this site master to make, reuse, move, hold, or leave-empty decisions before generating anything.
```

Supported modes: Create, Series, Identity, Refine, Audit, Placement, and
Handover.

## Repository

```text
skills/pitchdog-illustration/
├── SKILL.md
├── agents/openai.yaml
├── assets/
│   ├── reference-manifest.json
│   └── references/
├── evals/evals.json
├── references/
└── templates/
```

The skill uses progressive disclosure: core routing stays compact; detailed
metaphor, identity, prompting, placement, QA, and production law loads only
when the task needs it.

## Validate and package

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/validate_skill.py
.venv/bin/python scripts/package_skill.py
.venv/bin/python scripts/validate_skill.py --release-dist dist
```

The packager creates a ChatGPT-portable pair within the 25,000,000-byte
repository budget and a full-resolution archival pair. Builds are reproducible
when repeated in the same pinned environment; no cross-platform byte-identity
claim is made. Each `.zip` and `.skill` twin is byte-identical and contains one
top-level `pitchdog-illustration/` folder.

## Contribute

Read [CONTRIBUTING.md](CONTRIBUTING.md). New references need explicit public
rights, provenance, and a real quality reason. A competent image is not a new
canon.

## Licence

[0BSD](LICENSE): use, copy, change, distribute, bundle, or sell the repository
material for any purpose, with or without attribution.

The copyright licence does not grant trademark, privacy, publicity,
personality, moral, or endorsement rights. See [NOTICE.md](NOTICE.md).
