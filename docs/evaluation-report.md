# Evaluation report

Date: 2026-08-06
Release target: v1.0.0

## Objective

The release must route seven modes correctly, create no work during read-only
Audit or Placement requests, preserve exact family identity, resist caption and
surface shortcuts, catch animal-anatomy defects, maintain status truth, and
package only licensed sanitized evidence.

## Deterministic suite

The repository validator checks frontmatter, links, required files, progressive
structure, interface metadata, 44 adversarial evals, reference counts and
hashes, PNG dimensions and modes, the corrected Spotty hash, privacy markers,
content-credential presence, symlinks, hidden junk, executable content, Git LFS
pointers, licence identity, historical archive checksums, and package size.

The packager produces deterministic `.zip` and `.skill` files from one byte
stream, rejects unsafe archive paths, extracts to a temporary directory,
revalidates the extracted skill, and compares every file byte-for-byte.

## Behavioral coverage

The 44 portable cases cover:

- explicit activation and unrelated non-trigger;
- Create, Series, Identity, Refine, Audit, Placement, and Handover boundaries;
- batch autonomy without approval theatre and explicit owner gates;
- Juno's exact coat, face, ears, body, and `1.1×` relationship;
- Spotty's four-limb regression and honest occlusion accounting;
- Luna and Spotty peer scale, sisters' equal agency, and protected pronouns;
- Kumail's trousers, covered ankles, and broad lace-up shoes;
- Manali's body and age without beauty normalization;
- caption rescue, repeated physics, white stages, yellow cast, vector gloss,
  scene creep, realism, and bulk-generation traps;
- Golden Six conflicts, website-30 reuse, and historical archive isolation;
- private photos, named-artist shortcuts, metadata, licensing, checksums, and
  public-package sanitation;
- generation versus inspection and agent-checked versus owner-accepted versus
  published;
- full-size versus contact-sheet review, responsive crops, actual destination
  dimensions, and the decision to leave a section empty.

## Visual generation evaluation contract

Static tests cannot certify poetry, likeness, anatomy, or soul. Representative
image runs must record model or tool, date, input roles, full-size output,
verdict, and failure that changed the skill. A generation receipt or contact
sheet alone never passes. Soul remains qualitative; there is no numerical soul
score.

## Release evidence

| Check | Result | Evidence |
| --- | --- | --- |
| OpenAI `quick_validate.py` | Pass | Valid frontmatter, name, description, and skill structure |
| Repository validator | Pass | 26 required skill files; 44 evals; 60 manifested references; 54 provenance-bearing PNGs; 220-line `SKILL.md`; 80,222,125 source bytes |
| Reference receipts | Pass | 58 active illustrations and two contact sheets hash-match the manifest; aggregate reference-pack receipt matches |
| Spotty regression | Pass | Active Spotty 01 hash is the four-limb correction `720e4445…8d99` |
| Rights and privacy static scan | Pass | No real photos, private paths, prompt fields, coordinates, secrets, symlinks, hidden junk, executables, or Git LFS pointers in the runtime package |
| Deterministic archive round-trip | Pass | Extracted skill revalidated and all 84 files compared byte-for-byte |
| `.zip` / `.skill` identity | Pass | One archive byte stream under both names; SHA-256 `159ec138c92309de438171b59018f2258d75d080cb06f847f8c829cc67f029ed` |

Public GitHub round-trip, Codex installation, ChatGPT desktop installation,
ChatGPT web installation, and fresh-session invocation are separate release
checks. They are not inferred from local package success.
