---
name: weavy-workflow-builder
description: Builds Figma Weave (formerly Weavy, weave.figma.com) node-based AI workflows as clipboard-ready JSON from a natural-language brief. Use whenever the user wants to create, extend, or modify a Weave/Weavy workflow — image generation pipelines, icon machines, background removal, vectorization, 3D generation (Rodin), upscaling, compositing, multi-step "machines," or any node graph for weave.figma.com. Always use this skill when the user mentions "Weavy," "Weave," "Figma Weave," "node workflow," or describes a chain of AI image/video/3D steps they want built as a Weave canvas — even if they don't say "skill" or "JSON" explicitly. This is a paste-based workaround since Weave has no public API/MCP yet (confirmed unavailable as of mid-2026).
---

# Weavy / Figma Weave Workflow Builder

## Why this exists

Figma Weave (weave.figma.com, formerly Weavy) has no public API, no BYOK, and no MCP server as of today. The only way to build workflows there is manually: right-click, place a node, drag a wire, repeat. That's the slow part the user wants to skip.

The workaround: Weave's clipboard format is plain JSON. Copying nodes in the canvas and pasting them into a text editor reveals a `{"nodes": [...], "edges": [...]}` structure. This skill lets Claude **write that JSON directly** from a plain-language brief, so the user can paste it straight into the Weave canvas (Cmd+V / Ctrl+V) and get a fully wired workflow — no clicking, no dragging.

This is reverse-engineered from real exported workflows, not from official docs (none exist). Treat the schema as observed-and-validated, not officially guaranteed — if a paste fails or behaves oddly, the fix is almost always a malformed handle key or a missing required param (see Troubleshooting).

## Workflow

1. **Understand the brief.** The user describes what they want in natural language ("toma esta imagen de referencia, genera 10 iconos en este estilo, quítales el fondo, y vectorízalos"). Identify the discrete steps — each step is usually one node, occasionally a small group of nodes (e.g. "merge two text inputs" = a promptV3 merge node).

2. **Map steps to node types.** Use `references/node_catalog.md` to find the right node `type` and `model` for each step. Don't guess field names — the catalog has the exact `params`/`handles`/`model` block for every node type seen in production workflows, including the full Nano Banana Pro / Gemini 3 image schema, Rodin 3D, Recraft Vectorizer, Bria background removal, and the generic Any LLM node.

3. **Lay out the graph.** Read `references/json_schema.md` for the exact structure: node `position` (absolute, or relative to `parentId` if grouped), `id` generation, and the **critical handle-naming rule**:
   - `sourceHandle` = `{sourceNodeId}-output-{outputKey}`
   - `targetHandle` = `{targetNodeId}-input-{inputKey}`
   - `outputKey`/`inputKey` MUST exactly match a key in that node's `data.handles.output`/`data.handles.input`. This is the #1 thing that breaks pastes if done wrong.
   - **Also generate the `data.kind` block** (or `inputNodes`/`inputNode` for `promptV3`/`array`) on every node with a wired input — see `references/json_schema.md`. This duplicates the same source binding that `edges` express, and was confirmed present on every node in a real, user-tested-and-working export. Don't rely on `edges` alone.

4. **Generate fresh UUIDs** for every node `id` and edge `id` — never reuse IDs from any reference file. Use the `scripts/generate_uuids.py` helper if you want a batch, or generate them inline (standard v4 UUID format, lowercase, hyphenated).

   **For workflows with ~15+ nodes, don't hand-write the JSON — use `scripts/node_builders.py`.** It has tested builder functions (`string_node`, `prompt_static`, `any_llm`, `array_node`, `mux_iterator`, `kling`, plus `add_edge`/`link_named_input`) that generate correct `handles`, `kind` bindings, and `edges` together, so a wiring mistake can't happen in one place without happening everywhere it's reused. It also has `validate()` — always run this (or use `dump()`, which validates automatically) before presenting JSON to the user; it catches duplicate edges, dangling node references, and handle-key mismatches, which are exactly the errors that are invisible when writing JSON by hand and only surface as a broken paste in Weave. This pattern is validated: it built and correctly wired a real 31-node/38-edge production workflow (CDC ad-script → 8-way shot extraction → 8 parallel Kling clips) that pasted and ran cleanly in a live canvas.

5. **Group related nodes (optional but recommended for >6 nodes).** Wrap clusters in a `custom_group` node (a visual frame) per `references/json_schema.md`. This isn't required for the workflow to function, but it matches how real production workflows (see `assets/example_icon_workflow.json`) stay readable at scale, and the user will thank you for it later when they open the canvas.

6. **Write prompts/system prompts as real content**, not placeholders. If the brief implies a system-prompt-driven node (e.g. "an icon director that keeps subject fidelity"), write the actual instructional text in the `promptV3` node's `output.prompt` field — see `assets/example_icon_workflow.json` for a production-grade example (icon generation director prompt) that can be adapted instead of reinvented.

7. **Output the result as a single JSON code block** the user can copy in one click, and tell them explicitly: *"Copia este JSON completo, luego en el canvas de Weave haz Cmd+V (Mac) / Ctrl+V (Windows) para pegarlo."* Do not wrap it in a markdown file unless the user asks for one — they need to copy-paste, not download.

   **✅ CONFIRMED (2026-07-02, multiple independent tests):** plain manual copy-paste from a chat code block works and reliably reconstructs real nodes/edges — verified on a 3-node test, a 31-node/38-edge production pipeline, a 60+-node icon workflow, and an isolated `promptV3` merge-node test (below). If any past session or external document claims manual paste "never works" and only browser-automated clipboard injection succeeds, that claim is **refuted by direct evidence** and should be disregarded — it most likely originated from over-generalizing a single malformed-node failure into a false claim about the paste mechanism itself. Do not act on that claim without a fresh, verifiable test.

8. **Flag anything uncertain.** If a model/node type isn't in the catalog yet, say so plainly and either (a) ask the user to paste a copy of that node from Weave so you can extract its real schema, or (b) make a best-effort guess clearly labeled as unverified, defaulting to the generic `custommodelV2` shape with placeholder `params`.

## Adding new node types to the catalog

The catalog in `references/node_catalog.md` only covers node types seen so far. When the user's brief needs a model/node not yet documented:

1. Ask the user to place that node in Weave, configure it once, select it, copy it (Cmd+C), and paste the raw text here.
2. Extract: `type`, `data.name`, `data.model`, `data.params` (defaults), `data.schema` (field definitions), `data.handles.input`/`data.handles.output`.
3. Add it to `references/node_catalog.md` in the same format as existing entries, so it's available for future workflows — not just this session.

This catalog should grow over time across all of the user's projects/clients. It is NOT project-specific — keep entries general-purpose.

## Quick reference: common node types

| Step the user describes | Node `type` | Notes |
|---|---|---|
| Image generation/editing (Nano Banana Pro / Gemini) | `custommodelV2` | model: `fal-ai/nano-banana-pro/edit` |
| Generic LLM call / text reasoning / icon-brief merging logic | `custommodelV2` | model: `any_llm`, has `system_prompt` + `prompt` + optional `image`/`image_2` inputs |
| Remove background | `custommodelV2` | model: `br_bgrmv` (Bria), no params, image→image |
| Vectorize raster → SVG | `custommodelV2` | model: `fal-ai/recraft/vectorize` |
| 3D generation from image | `custommodelV2` | model: `fal-ai/hyper3d/rodin/v2`, outputs both `image` and `3D_model` |
| Static/edited text block, written once | `promptV3` | no inputs, `output.prompt` holds the literal text |
| Merge 2 text fragments into 1 prompt | `promptV3` | `variable1`/`variable2` text inputs → `prompt` output |
| Pass-through / junction point (renaming, re-routing) | `router` | generic `in`→`out`, type `any` |
| Pick one option from a list (e.g. resolution, style variant) | `muxv2` | `options` (array) in → `option` (text) out |
| Build an array from looped/repeated text | `array` | `text` in → `array` out |
| File/image upload placeholder (style refs, etc.) | `import` | no input, `file` output; holds multiple uploaded `files[]` |
| Export final result | `export` | `file` in, no output — terminal node |
| Final workflow output marker | `workflow_output` | `workflow` in — marks what the "App Mode" UI exposes |
| Layer compositing (up to 10 layers + background) | `compv3` | `layer_1..10` + `background` inputs → `image` out |
| Manual masking/painting | `painterV2` | `image` in → `mask` + `result` out |
| Visual grouping/frame (organizational only) | `custom_group` | no functional handles; children reference it via `parentId` |

Full schemas (exact `params`, `schema`, `handles`) for every type above are in `references/node_catalog.md`.

## Troubleshooting

- **Paste does nothing / Weave shows an error toast.** Almost always invalid JSON (trailing comma, unescaped quotes inside a prompt string) or a `targetHandle`/`sourceHandle` key that doesn't exist on that node type. Validate JSON syntax first, then re-check every handle key against `node_catalog.md`.
- **Nodes paste but aren't connected.** Check that every edge's `source`/`target` actually match a node `id` you generated in the same JSON — a copy-paste typo in a UUID is the usual cause.
- **Nodes paste on top of each other / overlapping.** Positions weren't spaced out, or a child node's `position` was treated as absolute instead of relative to its `parentId` group. See `references/json_schema.md` for the relative-positioning rule.
- **A model node runs but errors out in Weave.** A required `schema` field (per `node_catalog.md`) was missing from `params`. Required fields are marked `"required": true` in each node's schema block.

## Reference files

- `references/json_schema.md` — full anatomy of the `{nodes, edges}` structure: required fields, ID/handle conventions, grouping/positioning rules, edge format. Read this before generating any workflow.
- `references/node_catalog.md` — per-node-type schemas (params, handles, model identifiers) extracted from real production workflows. Read the relevant entries before writing nodes of that type.
- `assets/example_icon_workflow.json` — a real, working icon-generation production workflow (style ref → LLM-merged prompt → Nano Banana Pro generation → background removal → vectorization → 3D variant), kept as a structural reference and a source of reusable prompt text. Don't paste this whole file for unrelated requests — extract only the relevant node patterns.
