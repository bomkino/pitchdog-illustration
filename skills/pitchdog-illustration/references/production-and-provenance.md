# Production and provenance

## Contents

- Status vocabulary
- Folder discipline
- Naming
- Final metadata
- Checksums and manifests
- Contact-sheet QA
- Public/private boundary
- Handover checklist

## Status vocabulary

Keep these distinct:

- **Concept-locked:** verbal relationship selected; no image evidence yet.
- **Generated:** candidate file exists.
- **Inspected:** actual pixels opened at 100% for the active profile; canonical
  source used when exact-pixel evidence matters.
- **Agent-checked:** defined gates passed in the current review.
- **Owner-accepted:** owner explicitly accepted this exact file or checksum.
- **Promoted:** copied into a finals location under current authority.
- **Published:** exact promoted file is live at a verified destination.
- **Superseded:** once-current file replaced; preserve lineage.
- **Rejected:** explicit evidence not to promote or repeat.

Do not use `approved` without naming who approved what.

## Folder discipline

Adapt to the project, but preserve these boundaries:

```text
illustrations/
├── 00-authority/       # immutable locks and reference index
├── 01-briefs/          # placement, character, and concept records
├── qa/                 # generated candidates; never implicit finals
├── rejected/           # explicit failures and superseded candidates
├── finals/             # promoted files only
└── reports/            # metadata, manifests, contact sheets, QA
```

- Copy into finals; do not destroy candidate lineage.
- Never edit an authority image in place.
- Keep rejected work because it prevents repeated mistakes.
- Preserve owner changes and unrelated files.
- Use absolute paths during production; remove private paths from public packages and metadata.

## Naming

Use stable lowercase names:

```text
NN-subject-short-metaphor.png
candidate-subject-short-metaphor-vNN.png
```

Examples:

```text
01-juno-loose-end-of-impossible.png
candidate-sisters-heavy-thing-lightly-v04.png
```

Names describe the relationship, not visual adjectives. Do not include `final-final`, model names, dates without a purpose, or `approved` before acceptance.

## Final metadata

Every promoted final records:

- title;
- filename and relative path;
- caption;
- metaphor rationale;
- subject and pronouns;
- identity lock version;
- proposed or verified placement;
- dimensions and colour mode;
- source candidate and edit lineage;
- reference roles used;
- inspection date;
- status and acceptance authority;
- alt text;
- SHA-256 checksum.

Use [final metadata template](../templates/final-metadata.md). Keep private prompts or photo paths in internal production records only when needed; never publish them by accident.

## Checksums and manifests

Compute SHA-256 from the exact final bytes:

```bash
shasum -a 256 path/to/final.png
```

Create a manifest with one line per final:

```text
<sha256><two spaces><relative/path.png>
```

Verify from the directory that owns the relative paths:

```bash
shasum -a 256 -c FINAL-ILLUSTRATION-MANIFEST.sha256
```

Regenerate metadata and contact-sheet receipts after any byte change. A filename staying the same does not preserve identity of the file.

## Contact-sheet QA

Build a contact sheet only after individual actual-pixel checks. It should show:

- every required final exactly once;
- stable ordering by subject and sequence;
- enough size to inspect silhouette and palette;
- filename or short ID outside the artwork;
- neutral surrounding UI that does not alter colour judgment.

Use it to check:

- series rhythm and colour balance;
- repeated silhouette, object, verb, and accent role;
- relative character scale;
- accidental outliers in density, realism, or warmth;
- missing or duplicate files.

A contact sheet never replaces actual-pixel inspection.

## Public/private boundary

Before packaging or publishing:

- include only assets owner authorized for public release;
- exclude source photos and EXIF/location data;
- exclude third-party inspiration images unless their licence permits redistribution;
- exclude private absolute paths, account names, generation IDs, and hidden prompts;
- document the licence of every included asset family;
- preserve trademarks separately from the content licence;
- verify the public archive by downloading and inspecting it.

The current bundled reference illustrations are owner-authorized under 0BSD. The `pitch.dog` name and marks are not granted for endorsement or source confusion.

## Handover checklist

1. Required matrix count matches finals count.
2. Every final passes actual-pixel and contact-sheet review.
3. Exact identity and group ratios pass.
4. Candidate, rejected, and final boundaries remain clear.
5. Metadata record count matches finals count.
6. SHA-256 manifest verifies.
7. Contact sheet checksum is recorded.
8. No private or third-party restricted asset entered the public package.
9. Status separates agent-check, owner acceptance, promotion, and publication.
10. Next operator can find authority, current truth, and exact remaining work in five minutes.

Completion means no required work remains, not merely that files exist.
