# Weave clipboard JSON — full schema

This is the exact structure observed when copying nodes from a real Figma Weave (weave.figma.com) canvas and pasting into a text editor. Verified against a production workflow with 81 nodes and 92 edges — every edge's handle keys matched the source/target node's declared handles with zero mismatches, so this is a reliable, deterministic format.

## Top-level shape

```json
{
  "nodes": [ /* array of node objects */ ],
  "edges": [ /* array of edge objects */ ]
}
```

That's it. No other top-level keys are required for a paste to work.

## Node object — required fields

```json
{
  "id": "<uuid-v4>",
  "isModel": false,
  "type": "<node type, see node_catalog.md>",
  "position": { "x": 0, "y": 0 },
  "data": { /* type-specific, see node_catalog.md */ },
  "width": 250,
  "height": 64,
  "dragHandle": ".node-header"
}
```

Fields seen but NOT required for a successful paste (Weave appears to regenerate/ignore them, but include them if copying from a real export for safety): `createdAt`, `originalName`, `selected`, `locked`, `draggable`, `owner` (seen as `null` in exports — internal ownership metadata, safe to omit or set `null`), `parentId` (only when grouped — see below).

`width`/`height` should roughly match the node type's natural size (see catalog) — Weave seems to re-render correctly even if slightly off, but matching real examples avoids visual glitches.

### `data` block — common sub-fields across (almost) all node types

- `name` — display label shown in the node header. This is what the user sees, not the `type`. Make it descriptive (e.g. "Remove Background — final pass", not just "Bria - Remove Background") when there are multiple instances of the same node type in one workflow, so the user can tell them apart at a glance.
- `color` — one of the Weave palette tokens (`Yambo_Orange`, `Yambo_Blue`, `Yambo_Purple`, `Yambo_Green`, `Red`, etc.). Purely cosmetic but pick *something* consistent per "stage" of the pipeline so the canvas reads well (e.g. all input/import nodes blue, all generation nodes orange, all text/prompt nodes green).
- `dark_color` / `border_color` — `"<color>_Dark"` / `"<color>_Stroke"`. Just append the suffix to whatever `color` you picked; don't invent unrelated values.
- `handles` — `{ "input": {...}, "output": {...} }`. **This is the authoritative source of valid handle keys for this node instance.** See Edge wiring below.
- `params` — the actual configured values for this node's inputs (only present on `custommodelV2`/`muxv2` nodes). Must satisfy every `"required": true` field in that node type's schema (see node_catalog.md).
- `model` — `{ "name": "...", "service": "...", "version": "..." }` for `custommodelV2` nodes. Comes straight from the catalog, don't alter.
- `version` — integer, always `3` in every observed node. Set it to `3`.

### ✅ CONFIRMED: `kind` block — required alongside `edges` for execution

Verified in a real user-exported production workflow, and in a minimal isolated test (`string` → `promptV3` → `custommodelV2` any_llm) built specifically to isolate this variable, pasted into a live Weave canvas, and run successfully. **Always generate both `edges` AND `kind` for every wired `custommodelV2` input; this is not optional.**

**⚠️ The shape of `kind` is NOT uniform across models — it depends on `kind.type`, which is NOT the same as `model.name`.** Confirmed from a second, larger real production workflow (icon-pack generator, 60+ nodes): `any_llm` uses the named-key shape below (Shape A). Every other model observed so far (`fal-ai/nano-banana-pro/edit`, `br_bgrmv`, and presumably every other `fal_imported` model in the catalog — Recraft vectorize, Rodin 3D) uses `kind.type: "wildcard"` (Shape B) — a completely different array-of-tuples shape. **Always check which shape applies before writing a node's `kind` block.**

**🔴 CORRECTION (2026-07-04): `kling` is NOT reliably Shape A.** A third real production workflow (fashion pose-matrix, 4-image garment compositing → 8-way pose fan-out → Kling video) contained a `custommodelV2` node with `model.name: "kling"` whose `kind.type` was **`"wildcard"` (Shape B)**, not the named-key Shape A previously documented here. This node was also a visibly different Kling variant from the one in `node_catalog.md` — display name "Kling First & Last Frame", `params.model` options `["O1 Pro","O1 Standard","2.1 Pro","2.5 Turbo Pro"]`, `duration` as an enum `[5,10]` (not a 3–15 integer range), and the last-frame input handle keyed `tail_image_url` (not `end_image_url`). Same `model.name`, different node preset, different `kind` shape and different field names. **Do not assume `kling`'s `kind` shape or field names from `model.name` alone** — check the actual node's `kind.type` and `handles` (from a real pasted export, or `node_catalog.md`'s matching variant) every time. See the two Kling variants documented separately in `node_catalog.md`.

**Shape A — named keys (confirmed only for `any_llm`):**
```json
"kind": {
  "type": "any_llm",
  "model": { "type": "value", "data": { "type": "string", "value": "anthropic/claude-sonnet-4-5" } },
  "temperature": { "type": "value", "data": { "type": "float", "value": 0 } },
  "thinking": { "type": "value", "data": { "type": "boolean", "value": false } },
  "prompt": { "nodeId": "<source node id>", "outputId": "<source output key>", "string": "" },
  "systemPrompt": { "nodeId": "<source node id>", "outputId": "<source output key>", "string": "" },
  "images": [["image", null]]
}
```
- `type` mirrors `model.name` for models confirmed on Shape A (e.g. `any_llm`). Do not assume this holds for `kling` — see the 🔴 correction above.
- Each configured **param** (model, temperature, thinking, etc.) gets wrapped as `{ "type": "value", "data": { "type": "<string|float|boolean|integer>", "value": <the actual value> } }` — this is a different shape from the plain `params` block, don't confuse the two.
- Each **wired input** (prompt, systemPrompt, image, etc.) gets `{ "nodeId": "<source node id>", "outputId": "<source handle key>", "string": "" }` — `nodeId`/`outputId` must match a real `edges` entry wiring the same connection. `string` is always left as an empty string (Weave appears to populate it at runtime).
- Unwired optional inputs (e.g. no image attached) still get an entry, e.g. `"images": [["image", null]]`.
- Field names inside `kind` are camelCase (`systemPrompt`) even though the matching `handles.input`/`params` key is snake_case (`system_prompt`) — don't copy the input key verbatim, translate it.

**Shape B — `wildcard` (every other `fal_imported`/generic model, e.g. Nano Banana Pro, Bria remove-bg, and by extension Recraft vectorize / Rodin 3D until proven otherwise):**
```json
"kind": {
  "type": "wildcard",
  "model": {
    "type": "predefined",
    "name": "<model id, same as data.model.name>",
    "service": "<service, if applicable>",
    "version": "<version, if applicable>",
    "description": "<model description>"
  },
  "inputs": [
    [
      { "id": "prompt", "title": "Prompt", "description": "...", "validTypes": ["text"], "required": true },
      { "nodeId": "<source node id>", "outputId": "<source output key>", "string": "" }
    ],
    [
      { "id": "image_1", "title": "image_1", "description": "...", "validTypes": ["image"], "required": false },
      { "nodeId": "<source node id>", "outputId": "<source output key>", "file": { "...": "full file object, only if the source is an import/router carrying an uploaded file — omit for generated images" } }
    ]
  ],
  "parameters": [
    [
      { "id": "resolution", "title": "Resolution", "description": "...", "constraint": { "type": "enum", "options": ["1K", "2K", "4K"] }, "defaultValue": { "type": "string", "value": "1K" } },
      { "type": "value", "data": { "type": "string", "value": "1K" } }
    ]
  ],
  "outputs": [
    { "id": "result", "title": "result", "description": "Result image", "dataType": "image" }
  ]
}
```
- Each **input** is a 2-item array: `[<field schema: id/title/description/validTypes/required>, <binding>]`. The binding is the same `{nodeId, outputId, string}` shape as Shape A, except image-typed inputs may carry a `file` key with the full file object instead of/alongside `string` when the source is an uploaded reference image.
- Each **parameter** is a 2-item array: `[<field schema: id/title/description/constraint/defaultValue>, {"type":"value","data":{"type": <param's own type>, "value": <configured value>}}]`. `constraint`/`defaultValue` replace Shape A's plain type strings — e.g. a `seed` param's value is `{"type":"seed","value":{"seed": N, "isRandom": bool}}`, not a plain number.
- `outputs` mirrors `data.handles.output` as a flat array of `{id, title, description, dataType}` objects (not the nested object shape used in `handles`).
- Models with no configurable params (e.g. `br_bgrmv`) simply have `"parameters": []`.
- For an unwired optional input, it's safe to omit that field's `inputs` entry entirely rather than including a null binding — confirmed on `br_bgrmv` nodes, which only declared their one wired `image` input and nothing else.

Also seen: `promptV3` nodes with a named/labeled input (e.g. `script`) carry the equivalent binding under `inputNodes` (array of `[key, {nodeId, outputId, string}]` tuples). `array`, `router`, and `export` nodes carry the same idea as a single `inputNode` object (`{nodeId, outputId, string}`, no array wrapper — confirmed on all three types in a real export). Add whichever variant matches the node type whenever that node has a wired input.

## Edge object — required fields

```json
{
  "id": "<uuid-v4>",
  "type": "custom",
  "source": "<source node id>",
  "target": "<target node id>",
  "sourceHandle": "<sourceNodeId>-output-<outputKey>",
  "targetHandle": "<targetNodeId>-input-<inputKey>",
  "data": {
    "sourceColor": "<color of source node>",
    "targetColor": "<color of target node>",
    "sourceHandleType": "<type of the output, e.g. image/text/any>",
    "targetHandleType": "<type of the input, e.g. image/text/any>"
  }
}
```

### The one rule that matters most: handle key matching

`outputKey` and `inputKey` are NOT arbitrary — they must be exact string matches to keys present in:
- source node's `data.handles.output` (for `outputKey`)
- target node's `data.handles.input` (for `inputKey`)

Example: connecting a `custommodelV2` "Bria - Remove Background" node's output to a `router` node's input:
- Bria's `handles.output` = `{ "image": {...} }` → so `outputKey` is `image`
- Router's `handles.input` = `{ "in": {...} }` → so `inputKey` is `in`
- Result: `sourceHandle: "<briaNodeId>-output-image"`, `targetHandle: "<routerNodeId>-input-in"`

Get this wrong (e.g. use a key that doesn't exist on that node type) and the paste either silently fails to wire that connection or Weave shows an error. Always cross-check against `node_catalog.md` before writing an edge.

`sourceHandleType`/`targetHandleType` are just copies of the `type` field from the corresponding handle definition (e.g. `image`, `text`, `array`, `any`, `3D`, `mask`). They appear cosmetic (affect wire color/style) but always fill them in correctly anyway since it costs nothing and matches real exports.

## Grouping nodes (`custom_group`)

Visual frames that organize nodes — not functionally required, but used heavily in real production workflows once they exceed ~6 nodes, and it makes the canvas far more legible for the user later.

```json
{
  "id": "<group-uuid>",
  "isModel": false,
  "type": "custom_group",
  "position": { "x": -2520, "y": 4200 },
  "data": {
    "name": "User Input",
    "type": "custom_group",
    "color": "#EDF2B3",
    "width": 520,
    "height": 904,
    "handles": { "input": [], "output": [] },
    "version": 3,
    "description": "Group of nodes",
    "labelFontSize": 16
  },
  "width": 520,
  "height": 904
}
```

Note: `custom_group` colors are raw hex strings (`#EDF2B3`), unlike regular nodes which use named tokens (`Yambo_Orange`). Don't mix these up.

### Critical: relative positioning inside a group

**Any node with a `parentId` set to a group's `id` has its `position` interpreted RELATIVE to that group's top-left corner — not absolute canvas coordinates.**

Verified example: a group at canvas position `(-2520, 4200)` with size `520x904` contains two children:
- child A at `position: {x: 30, y: 330}` (relative — meaning it's roughly 30px from the group's left edge, 330px from its top)
- child B at `position: {x: 30, y: 40}`

If you forget this and give a grouped child an absolute canvas position, it will render far outside its visual frame, looking broken even though the data is technically valid.

**Practical approach when generating a group:**
1. Decide the group's overall canvas position and size first (generous padding — at least 40-60px margin around the contents).
2. Lay out children with `x`/`y` starting near `(20-40, 20-40)` and stack/space them by their own `width`/`height` plus ~20-30px gutters.
3. Set each child's `parentId` to the group's `id`.
4. Set the group's `width`/`height` to comfortably contain all children plus padding — don't undersize it.

## ID generation

Every `node.id` and `edge.id` must be a fresh UUID (v4 format, lowercase, hyphenated, e.g. `8bfdc869-61a0-4898-bfa5-2bc875b0f518`). Never reuse IDs across nodes, and never copy IDs verbatim from this reference doc or from `assets/example_icon_workflow.json` into a new workflow — Weave may deduplicate or misbehave if it sees an ID that already exists somewhere (e.g. if the user pastes two AI-generated workflows into the same file over time).

Use `scripts/generate_uuids.py` to batch-generate as many as needed, or generate them inline — any valid v4 UUID works, they don't need to follow any special pattern beyond being unique within the pasted JSON.

## Minimal end-to-end example

A 2-node workflow: a text prompt feeding straight into an image generation node.

```json
{
  "nodes": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "isModel": false,
      "type": "promptV3",
      "position": { "x": 0, "y": 0 },
      "data": {
        "name": "Prompt",
        "color": "Yambo_Green",
        "dark_color": "Yambo_Green_Dark",
        "border_color": "Yambo_Green_Stroke",
        "output": { "type": "text", "prompt": "a minimalist line-art icon of a coffee cup, black background" },
        "handles": { "output": { "prompt": { "type": "text" } } },
        "version": 3
      },
      "width": 460,
      "height": 200,
      "dragHandle": ".node-header"
    },
    {
      "id": "22222222-2222-4222-8222-222222222222",
      "isModel": false,
      "type": "custommodelV2",
      "position": { "x": 600, "y": 0 },
      "data": {
        "name": "Gemini 3 (Nano Banana Pro)",
        "color": "Yambo_Purple",
        "dark_color": "Yambo_Purple_Dark",
        "border_color": "Yambo_Purple_Stroke",
        "model": { "name": "fal-ai/nano-banana-pro/edit", "service": "fal_imported", "version": "fal-ai/nano-banana-pro/edit" },
        "params": { "prompt": "", "num_images": 1, "resolution": "1K", "aspect_ratio": "1:1", "output_format": "png", "enable_web_search": false, "seed": { "seed": 1, "isRandom": true } },
        "handles": {
          "input": { "prompt": { "type": "text" }, "image_1": { "type": "image" }, "image_2": { "type": "image" }, "resolution": { "type": "text" } },
          "output": { "result": { "type": "image" } }
        },
        "version": 3
      },
      "width": 320,
      "height": 200,
      "dragHandle": ".node-header"
    }
  ],
  "edges": [
    {
      "id": "33333333-3333-4333-8333-333333333333",
      "type": "custom",
      "source": "11111111-1111-4111-8111-111111111111",
      "target": "22222222-2222-4222-8222-222222222222",
      "sourceHandle": "11111111-1111-4111-8111-111111111111-output-prompt",
      "targetHandle": "22222222-2222-4222-8222-222222222222-input-prompt",
      "data": {
        "sourceColor": "Yambo_Green",
        "targetColor": "Yambo_Purple",
        "sourceHandleType": "text",
        "targetHandleType": "text"
      }
    }
  ]
}
```
