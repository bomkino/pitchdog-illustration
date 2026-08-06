# Prompting and tools

## Contents

- Tool choice
- Reference roles
- Production prompt
- Generation versus edit
- Iteration discipline
- Output handling

## Tool choice

Use the strongest available image-generation or image-editing tool that can accept reference images and preserve identity. Generate directly when tools permit. Return only a prompt when the user explicitly requests a prompt or image generation is genuinely unavailable.

Prefer high-fidelity settings for identity-sensitive finals. Lower-cost settings may support disposable concept probes, but this workflow usually saves more time by generating fewer, better-considered candidates.

Do not hard-code a model name as permanent authority. Model capabilities drift. The visual law and evidence gates remain stable.

## Reference roles

Label every image input:

- `Style reference A`: current approved visual authority.
- `Style reference B`: second current authority showing a different motif.
- `Identity reference 1..n`: photographs or approved depictions of the exact subject.
- `Conceptual ancestor`: optional Golden Six image used only for relationship or economy.

Use the smallest sufficient set. Start with two current style references and two to four identity references. Too many unlabelled images create reference soup.

Never attach the Golden Six as sole current style authority. Never attach source photographs without saying that they govern identity only.

## Production prompt

Use this maintainable structure:

```text
Deliverable:
Create one original pitch.dog editorial illustration for [medium and placement].
Canvas: [dimensions and aspect ratio]. No text.

Reference roles:
- Image 1: current style authority; use field, ink economy, scale, and restraint.
- Image 2: current style authority; use handmade imperfection and accent discipline.
- Images 3–5: identity evidence for [subject] only. Do not copy photographic setting, lighting, or realism.

Locked visual relationship:
[One familiar thing] behaves impossibly: [one changed physical rule].
[Subject] performs [one ordinary action].
Emotional truth: [one plain sentence].

Composition:
Full-bleed [cool pastel] field with subtle paper grain.
At least [80%] calm negative space.
One tiny lower-[position] motif.
[Exact actor/object placement, relative scale, gaze, contact, and silhouette].
One [accent colour] element carries the conceptual turn.

Identity lock:
[Verbatim decisive cues, proportions, markings, clothing, pronouns, and relationships].

Visual language:
Sparse, slightly imperfect near-black editorial ink; flat controlled colour; no polished vector finish.
One familiar thing, one impossible behaviour, one ordinary act, one remembered silhouette.

Preserve:
[Identity, scale, field family, concept, framing, and any approved elements].

Exclude:
White stage; yellow/amber/sepia cast; scenery; extra props; arrows; labels; text; symbols; glow; shadows; cinematic lighting; realism; glossy vector line; 3D; watercolour; generic cuteness; mascot pose; decorative marks.

Output:
One candidate only. Opaque full-bleed image. No border, logo, watermark, or caption.
```

Replace generic brackets with observable details. Do not add style adjectives that do no work.

## Generation versus edit

Generate from scratch when:

- the metaphor is new;
- the premise is dead;
- composition, identity, and style all drift;
- revision would preserve the wrong physics;
- previous iterations exist only because of sunk cost.

Edit when:

- the metaphor is alive and immediately legible;
- most identity cues already work;
- one failure is local and describable;
- the edit can say `change only X`;
- every invariant can be restated.

Example surgical instruction:

```text
Change only Kumail's lower body: relaxed straight men's trousers, covered ankles, broad rounded dark lace-up sneakers. Preserve face, curl silhouette, torso, pose, hand contact, metaphor, composition, field colour, line quality, and every other element exactly. Add nothing.
```

Do not use an edit to rescue a weak concept.

## Iteration discipline

- Start with a clean base prompt.
- Make one candidate.
- Diagnose before revising.
- Change one variable per edit.
- Restate identity and all invariants every time.
- Reattach or name reference roles when context may have drifted.
- Make at most one surgical revision before re-evaluating the premise.
- If the same failure survives twice, change approach rather than adding adjectives.
- Never request “more soul”, “more poetic”, or “more premium” without naming the material relationship that is missing.

## Output handling

- Keep the original generated file immutable.
- Inspect the actual pixels at full size.
- Preserve colour fidelity; export an opaque sRGB PNG unless destination requires another format.
- Keep portrait finals at exact requested dimensions where possible.
- Record model/tool, date, prompt version, reference roles, and edit lineage in private production metadata when available.
- Do not embed source photographs or private paths in public metadata.
- Never infer success from a generation receipt or thumbnail preview.
