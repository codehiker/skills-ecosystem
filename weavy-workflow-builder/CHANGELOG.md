# Changelog — weavy-workflow-builder

Tracks what's changed or been newly confirmed in this skill, newest first. This exists so anyone (including a future Claude session) can scan one file and know what's evolved, instead of diffing `SKILL.md`/`references/*.md` line by line.

**Maintenance rule:** whenever you add a new 🔴/✅ CONFIRMED finding, fix a bug in the schema/scripts, or change guidance in `SKILL.md`/`references/`, add one entry here — a couple of lines is enough. Put newest entries at the top. Link to the section that has the full detail rather than duplicating it here.

**Repackage rule:** after any update to this skill, repackage it with skill-creator's `package_skill.py` into a `.skill` file and present it for download, so it can be reinstalled in Claude Desktop and stay in sync across all projects — do this automatically as part of finishing the update, not just when asked.

---

## 2026-07-04 (2)

Findings from reverse-engineering a real fashion pose-matrix production workflow (4-image garment compositing → LLM pose-director → 8-way prompt fan-out → 8 parallel Nano Banana Pro renders → Kling first/last-frame video).

- **🔴 CORRECTION: `kling` is NOT reliably Shape A for `kind`.** Previously documented as using the named-key shape alongside `any_llm`. This workflow's Kling node (`model.name: "kling"`, display name "Kling First & Last Frame") used **Shape B (`wildcard`)** instead — a structurally different node preset from the "Kling 3.0 Pro" entry already in the catalog, also differing in field names (`tail_image_url` vs `end_image_url`) and params (`duration` as enum `[5,10]` vs a 3–15 range, model options `["O1 Pro","O1 Standard","2.1 Pro","2.5 Turbo Pro"]`). Both variants are now documented separately in `references/node_catalog.md`; `references/json_schema.md`'s Shape A/B section and `SKILL.md` step 3 now warn explicitly against inferring `kind` shape or field names from `model.name` alone for `kling`.
- **✅ New confirmed pattern: single-variable `promptV3` templated from a `muxv2` `list_selector`, broadcast to multiple prompts from one shared source.** A 2-option `list_selector` (skin-tone toggle) fed `variable1` on two separate `promptV3` nodes at once (a system prompt and a content prompt), both pointing at the identical upstream `{nodeId, outputId}`. Documented in `references/node_catalog.md`'s `promptV3` section as the pattern to use for "one control, many synced prompts" instead of duplicating the selector.
- **✅ Second confirmed instance of the full "1 LLM call → N images" fan-out**, reinforcing the existing N-static-`muxv2`-indexers pattern with a new concrete case: `any_llm` (Gemini 3 Pro, 4 image inputs + pose-director system prompt) → 8 delimited prompts in one response → `array` node (delimiter `^`, confirming a third working delimiter alongside `,` and `§§`) → 8 static `muxv2` selectors (`selected: 0`–`7`) → 8 parallel `custommodelV2` (Nano Banana Pro) generations, all wired to the same 4 reference images via `router` pass-throughs. Documented in `references/node_catalog.md`'s `muxv2` section; summarized as a named pattern in `SKILL.md` step 2.

## 2026-07-04

- **🔴 New failure mode documented: guessed/unverified `custommodelV2.model` crashes the whole Weave client on paste** (full "Oops! Something went wrong" screen, not a small toast). Found by direct reproduction: a placeholder node for an unverified model (`gpt-image-2`/`openai`, invented because it wasn't in the catalog) crashed Weave on paste; removing just that node let the same workflow paste clean immediately after. Isolated via bisection: single confirmed-safe node → full workflow with only confirmed models → confirmed the guessed node as sole cause.
  - `SKILL.md` point 8 rewritten: no longer suggests a labeled-unverified guess as an acceptable fallback — now says to withhold that model entirely and ask the user for the real node first.
  - `SKILL.md` Troubleshooting: new bullet distinguishing this whole-app crash from the pre-existing "paste does nothing / small toast" case, plus the bisection method to use when diagnosing future reports of this kind.
  - `references/node_catalog.md`: new 🔴 CONFIRMED block in the `custommodelV2` intro with the full incident writeup and the "never paste a guessed model" rule.
- Added this `CHANGELOG.md`.

## 2026-07-02 — Initial build

- Created the skill: paste-based JSON workflow builder for Figma Weave (no public API/MCP exists, so this reverse-engineers the clipboard format).
- `references/node_catalog.md`: schemas for `custommodelV2` (Nano Banana Pro / Gemini 3, Any LLM, Bria background removal, Recraft Vectorizer, Rodin 3D, Kling 3.0 Pro video), `promptV3` (static + merge variants), `string`, `router`, `muxv2`, `array`, `import`, `export`, `workflow_output`, `compv3`, `painterV2`, `custom_group` — extracted from a real 81-node/92-edge production icon-generation workflow.
- `references/json_schema.md`: full `{nodes, edges}` anatomy, handle-naming convention (`{nodeId}-output-{key}` / `{nodeId}-input-{key}`), the `data.kind` binding rule, relative-positioning-under-`parentId` rule for grouped nodes.
- `scripts/node_builders.py`: builder functions (`string_node`, `prompt_static`, `any_llm`, `array_node`, `mux_iterator`, `kling`, `add_edge`/`link_named_input`) plus `validate()`/`dump()` — built to avoid hand-written wiring mistakes at scale.
- `scripts/generate_uuids.py`: batch UUID generation helper.
- `assets/example_icon_workflow.json`: a real, working production workflow kept as a structural + prompt-text reference.
- **✅ Confirmed: manual copy-paste from a chat code block works reliably** — verified across a 3-node test, a 31-node/38-edge production pipeline (CDC ad-script → 8-way shot extraction → 8 parallel Kling clips), a 60+-node icon workflow, and an isolated `promptV3` merge-node test. This refuted an earlier (incorrect) claim that only browser-automated clipboard injection works.
- **✅ Confirmed:** `promptV3` merge node genuinely templates `{{variable}}` inside Weave (not just static labels) — canvas renders variable chips and running the node substitutes correctly.
- **✅ Confirmed:** `compv3` layer compositor — a 3-layer test (background + 2 layers from `painterV2`) ran end-to-end through `export` with no crash; `painterV2.result` confirmed as a valid source for `compv3` slots.
- Documented the `muxv2` iterator pattern (`isIterator: true`, one node fans out to N branches) vs. the N-static-indexers pattern (N separate `muxv2` nodes at fixed `selected` indices) — both confirmed working, chosen based on whether fan-out count is fixed/known at generation time.
