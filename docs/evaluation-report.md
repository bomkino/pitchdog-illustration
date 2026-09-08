# Evaluation report — v1.0.1 historical receipt

This dated report preserves the original counts, hashes, and observations.
It does not certify later releases. See the [current release](https://github.com/bomkino/pitchdog-illustration/releases/latest)
for its package receipts and checks; v1.0.2 contains 46 evaluation specifications.

Date: 2026-08-06
Release target: v1.0.1

## Objective

The release must route seven modes correctly, create no work during read-only
Audit or Placement requests, preserve exact family identity, resist caption and
surface shortcuts, catch animal-anatomy defects, maintain status truth, and
package only licensed sanitized evidence.

## Validation and same-environment reproducibility

The repository validator checks frontmatter, links, required files, progressive
structure, interface metadata, 45 adversarial evals, reference counts and
hashes, PNG dimensions and modes, the corrected Spotty hash, privacy markers,
content-credential presence, symlinks, hidden junk, executable content, Git LFS
pointers, licence identity, historical archive checksums, and package size.

The packager produces same-environment reproducible full-resolution and ChatGPT-portable
`.zip`/`.skill` twin pairs, rejects unsafe archive paths, extracts each to a
temporary directory, revalidates it, and compares every file byte-for-byte.
The portable profile keeps every reference, enforces 800 px illustration and
1280 px contact-sheet long edges, strips stale embedded provenance payloads,
adds a perceptual sRGB declaration, reconstructs immutable canonical source
receipts, and enforces the 25,000,000-byte repository budget. CI builds twice
in one pinned Python 3.12/Pillow 11.3.0 environment and compares every archive;
no cross-platform byte-identity claim is made.

CI therefore proves reproducibility by comparing two builds made on the same
Ubuntu runner. It does not compare those bytes with the macOS-built public
release receipts. `validate_skill.py --release-dist dist` checks the pinned
v1.0.1 published hashes. It is not a general validator for newer release archives.

## Behavioral coverage

The 45 portable cases cover:

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
- Golden Six conflicts, website-30 collision/reuse, the two legacy-Juno
  current-use prohibitions, and historical archive isolation;
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
| OpenAI `quick_validate.py` | Pass in CI target | Canonical source and extracted portable archive are checked against the pinned OpenAI validator commit; the public run is the release receipt |
| Repository validator | Pass | 26 required skill files; 45 evals; 60 manifested references; 54 C2PA/JUMBF marker-bearing canonical PNGs; marker presence is recorded, not cryptographic signature verification; canonical packaged bytes checked by the final release run |
| ChatGPT-portable validator | Pass | 58 illustrations and two contact sheets retained; 22,543,648 unpacked bytes; perceptual sRGB chunks and canonical receipts verified; stale embedded provenance stripped from derivatives |
| Reference receipts | Pass | 58 active illustrations and two contact sheets hash-match the manifest; aggregate reference-pack receipt matches |
| Portable source-tamper regression | Pass | A plausible one-character `sourceSha256` mutation was rejected because all 60 source lines no longer reconstructed the immutable canonical aggregate |
| Spotty regression | Pass | Active Spotty 01 hash is the four-limb correction `720e4445…8d99` |
| Rights and privacy static scan | Pass | No real photos, private paths, prompt fields, coordinates, secrets, symlinks, hidden junk, executables, or Git LFS pointers in the runtime package; all nine public historical PNGs also pass signature, CRC, symlink, checksum, and sensitive-marker checks |
| Same-environment archive round-trip | Pass | Both extracted profiles revalidated; all 84 files in each compared byte-for-byte; independent rebuild reproduced both hashes in one pinned environment |
| ChatGPT `.zip` / `.skill` identity | Pass | 22,441,582 bytes each; SHA-256 `68e6c9288f70ae2fb5fe8d68df8f8caef9d6cfba730af2070d73628a604a8977` |
| Full-resolution `.zip` / `.skill` identity | Pass | 75,923,083 bytes each; SHA-256 `ec06bd9298487626bf6bb471f04eb7c95eb6f068a0ab928b9d436976bcb3e24a` |
| ChatGPT web / Cloud Work install and invocation | Pass | Listed under both Installed and Created by me; a fresh Work-mode Audit invocation returned all reference counts and the Juno, Spotty, Kumail, and status locks exactly |

Public GitHub v1.0.1 round-trip, refreshed Codex installation, and native-app
receipt remain separate release checks. They are not inferred from local
package or web success.
