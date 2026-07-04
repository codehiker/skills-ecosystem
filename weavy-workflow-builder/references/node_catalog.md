# Weave node catalog

Schemas extracted from a real, working production workflow (81 nodes, 92 edges — an icon-generation pipeline). Each entry below is the `data` block shape for that node `type` + `name` combo, ready to adapt.

**This catalog is general-purpose, not tied to any single project.** Add new entries here whenever a brief needs a node type not yet covered — see "Adding new node types" in the main SKILL.md.

---

## `custommodelV2` — model/API call nodes

This is the workhorse type. Every external AI model call (image gen, LLM, vectorize, 3D, background removal) is a `custommodelV2` node. They all share this `data` shape:

```json
{
  "type": "custommodelV2",
  "data": {
    "name": "<display name>",
    "color": "<palette token>",
    "model": { "name": "<model id>", "service": "<service>", "version": "<version>" },
    "params": { /* configured values, see each entry */ },
    "schema": { /* field definitions — required:true fields MUST be in params */ },
    "handles": { "input": {...}, "output": {...} },
    "kind": { /* execution binding — see references/json_schema.md */ }
  }
}
```

**⚠️ `data.kind` is required for execution and its shape depends on `kind.type`, NOT on `model.name`.** `any_llm` uses a named-key shape (Shape A); every other model confirmed so far (Nano Banana Pro, Bria, Recraft, Rodin) uses `kind.type: "wildcard"` (Shape B) — a structurally different array-of-tuples shape. **`kling` is ambiguous**: two different real Kling node presets have been observed, one on Shape A and one on Shape B — see the two variants below and the correction note in `references/json_schema.md`. Read the "`kind` block" section there before writing any `custommodelV2` node's `kind` — do not assume one model's shape works for another, and for `kling` specifically, check the actual node/example you're matching against rather than defaulting to either shape.

**🔴 CONFIRMED (2026-07-04): a `custommodelV2` node with a guessed/unverified `model.name` + `model.service` causes a full client-side crash on paste** — not a validation toast, a whole-app error screen ("Oops! Something went wrong," with no further detail, requiring a canvas refresh). This was reproduced directly: a workflow with a placeholder node for `"gpt-image-2"` / service `"openai"` (invented because that model wasn't in this catalog yet) crashed Weave immediately on paste. Removing that node and every reference to it (same graph, same edges elsewhere, only that node + its 2-3 edges deleted, model swapped for the confirmed Nano Banana Pro) pasted clean on the very next attempt — isolating the guessed model as the sole cause. Weave appears to try to resolve `model.name`/`model.service` against its live model registry when rendering the node, and an unrecognized combination throws an uncaught exception rather than failing gracefully.

**Practical rule: never include a guessed `model.name`/`model.service` in JSON that gets pasted into a live canvas**, even clearly labeled `[UNVERIFIED]` in the node's display name — the label is invisible to Weave's registry lookup and doesn't prevent the crash. Instead, when the brief needs a model not yet in this catalog:
1. Build the rest of the workflow using confirmed models only, and deliver that first.
2. Separately, ask the user to place the real node in Weave, configure it, copy it, and paste the raw JSON back into chat (per "Adding new node types" in SKILL.md) — do this *before* attempting to include that model in any paste-ready output, not after.
3. Only once you have the user-provided real node text should that model appear in generated JSON.

**Bisection method for isolating a crash** (used successfully here, worth repeating for any future "paste crashes the whole app" report):
1. Test the absolute minimum — a single confirmed-safe node (e.g. a static `promptV3`) pasted alone. If this also crashes, the problem isn't node content at all (clipboard format, browser extension, canvas state) — stop and investigate those instead.
2. If the minimal test pastes clean, rebuild the full intended workflow but with every uncertain/guessed node type or model swapped for a fully-confirmed equivalent (or removed). If *this* pastes clean, the guessed node(s) are confirmed as the cause.
3. Only then re-introduce the uncertain piece in isolation (its own tiny paste, 1-2 nodes) to double-confirm, rather than guessing further from the original crash report alone.

### Image generation/editing — "Gemini 3 (Nano Banana Pro)"

```json
"model": { "name": "fal-ai/nano-banana-pro/edit", "service": "fal_imported", "version": "fal-ai/nano-banana-pro/edit" },
"params": {
  "seed": { "seed": 678228, "isRandom": true },
  "prompt": "",
  "num_images": 1,
  "resolution": "1K",
  "aspect_ratio": "1:1",
  "output_format": "png",
  "enable_web_search": false
},
"handles": {
  "input": {
    "prompt": { "type": "text", "required": true, "description": "Description of the edits you want to make" },
    "image_1": { "type": "image", "required": false, "description": "The image you want to edit" },
    "image_2": { "type": "image", "required": false },
    "resolution": { "type": "text", "format": "enum" }
  },
  "output": { "result": { "type": "image" } }
}
```
- `resolution` options: `1K`, `2K`, `4K`
- `aspect_ratio` options: `auto`, `1:1`, `21:9`, `16:9`, `3:2`, `4:3`, `5:4`, `4:5`, `3:4`, `2:3`, `9:16`
- Use this whenever the brief calls for: generating an image from a prompt, editing/restyling an existing image, combining two reference images (style + subject) into a new image. `image_1`/`image_2` are optional — wire a reference image into one or both as needed, or leave unconnected for pure text-to-image.

### Generic LLM / text reasoning — "Any LLM"

Used for prompt-merging logic, brief interpretation, image description, or any "smart text" step that isn't itself an image/video model. This was the brain behind "Icon Machine" and "Pack Machine" nodes in the reference workflow (same shape, renamed).

```json
"model": { "name": "any_llm" },
"params": { "model": "google/gemini-3-pro", "temperature": 0 },
"schema": {
  "model": { "type": "enum", "title": "Model Name", "default": "google/gemini-3-pro",
    "options": ["anthropic/claude-sonnet-4-6","anthropic/claude-opus-4-7","anthropic/claude-opus-4-6","anthropic/claude-haiku-4-5","google/gemini-2.0-flash-001","google/gemini-2.5-flash","google/gemini-2.5-flash-lite","google/gemini-3-pro","openai/gpt-4o","openai/gpt-4.1","openai/gpt-5-chat","meta-llama/llama-4-maverick","meta-llama/llama-4-scout"] },
  "thinking": { "type": "boolean", "title": "Thinking", "default": false, "description": "Enhanced reasoning for complex tasks (supported models only)" },
  "temperature": { "type": "number", "min": 0, "max": 2, "title": "Temperature", "default": 0 }
},
"handles": {
  "input": {
    "image": { "type": "image" },
    "prompt": { "type": "text" },
    "image_2": { "type": "image" },
    "system_prompt": { "type": "text" }
  },
  "output": { "text": { "type": "text" } }
}
```
- Rename this node (`data.name`) to whatever its role is in the pipeline — e.g. "Icon Machine", "Brief Interpreter", "Caption Writer" — since "Any LLM" is the generic label, not a meaningful one.
- A simpler variant exists with `params: { "model": "...", "prompt": "..." }` and only `image` input (used for the "Image Describer" node — i.e. captioning/describing an uploaded image without a separate prompt input). Use this lighter shape when the step is pure image-to-text with no system prompt needed.

### Background removal — "Bria - Remove Background"

```json
"model": { "name": "br_bgrmv" },
"params": {},
"schema": {},
"handles": {
  "input": { "image": { "type": "image" } },
  "output": { "image": { "type": "image" } }
}
```
No configuration needed — pure image-in, image-out. Use whenever the brief says "remove the background", "isolate the subject", "transparent background", etc.

### Raster → vector — "Recraft Vectorizer"

```json
"model": { "name": "fal-ai/recraft/vectorize", "service": "fal_imported", "version": "fal-ai/recraft/vectorize" },
"params": { "image_url": "" },
"schema": {
  "image_url": { "type": "string", "title": "Image Url", "required": true,
    "description": "PNG, JPG or WEBP, <5MB, <16MP, max dimension <4096px, min dimension >256px" }
},
"handles": {
  "input": { "image_url": { "type": "image" } },
  "output": { "result": { "type": "image" } }
}
```
Use for "turn this into an SVG", "vectorize this icon", "convert raster to vector". Note the output type is still `image` (the vector is delivered as an image-typed asset in Weave's pipeline, downloadable as SVG via export).

### Image → 3D — "Rodin 3D V2"

```json
"model": { "name": "fal-ai/hyper3d/rodin/v2", "service": "fal_imported", "version": "fal-ai/hyper3d/rodin/v2" },
"params": {
  "seed": { "seed": 78408, "isRandom": true },
  "TAPose": false,
  "material": "All",
  "bbox_condition": "",
  "preview_render": false,
  "use_original_alpha": false,
  "quality_mesh_option": "500K Triangle",
  "geometry_file_format": "glb"
},
"schema": {
  "material": { "type": "enum", "options": ["PBR","Shaded","All"], "default": "All" },
  "TAPose": { "type": "boolean", "default": false, "description": "T-pose/A-pose for easier rigging" },
  "bbox_condition": { "type": "array", "array_type": "integer", "description": "[width, height, length]" },
  "preview_render": { "type": "boolean", "default": false },
  "use_original_alpha": { "type": "boolean", "default": false, "description": "Preserve transparency channel" },
  "quality_mesh_option": { "type": "enum", "default": "500K Triangle",
    "options": ["4K Quad","8K Quad","18K Quad","50K Quad","2K Triangle","20K Triangle","150K Triangle","500K Triangle"] }
},
"handles": {
  "input": { "image": { "type": "image" }, "prompt": { "type": "text" } },
  "output": { "image": { "type": "image" }, "3D_model": { "type": "3D" } }
}
```
Use for "turn this into a 3D model", "generate a 3D asset from this reference". Outputs BOTH a preview image and an actual 3D model file — wire `3D_model` onward to an `export` node if the user wants the downloadable mesh, or `image` onward if they just want a render.

### Image → video — "Kling 3.0 Pro"

```json
"model": { "name": "kling" },
"visibility": "private",
"menu": { "icon": "EmojiObjectsIcon", "isModel": true, "displayName": "Kling 3 Pro" },
"params": {
  "model": "3.0 Pro",
  "duration": "5",
  "cfg_scale": 0.5,
  "shot_type": "customize",
  "aspect_ratio": "9:16",
  "generate_audio": false
},
"schema": {
  "model": { "type": "enum", "title": "Model", "default": "Pro", "options": ["3.0 Pro", "3.0 Standard"] },
  "duration": { "type": "integer", "title": "Duration", "default": 5, "min": 3, "max": 15 },
  "cfg_scale": { "type": "number", "title": "Cfg Scale", "default": 0.5, "min": 0, "max": 1 },
  "shot_type": { "type": "enum", "title": "Shot Type", "default": "customize", "options": ["customize"] },
  "aspect_ratio": { "type": "enum", "title": "Aspect Ratio (T2I only)", "default": "16:9", "options": ["16:9", "9:16", "1:1"] },
  "generate_audio": { "type": "boolean", "title": "Generate Audio", "default": false }
},
"handles": {
  "input": {
    "prompt": { "type": "text", "label": "prompt", "required": true, "description": "Text prompt for video generation." },
    "image": { "type": "image", "label": "first_frame", "required": false },
    "end_image_url": { "type": "image", "label": "last_frame", "required": false },
    "negative_prompt": { "type": "text", "label": "negative_prompt", "required": false }
  },
  "output": { "video": { "type": "video", "label": "video" } }
}
```
Use for "animate this image", "turn this into a video clip", "image-to-video". `image` = first frame (optional — omit for pure text-to-video), `end_image_url` = optional last frame for first/last-frame interpolation. `duration` is in seconds (3-15). **This variant's `kind` block is Shape A** (named keys, same style as `any_llm` — see `references/json_schema.md`) — its `prompt` key binds the same way as `any_llm`'s.

### Image → video — "Kling First & Last Frame" (🔴 different variant, Shape B — see correction below)

**⚠️ This is a different Weave node preset from "Kling 3.0 Pro" above** — same `model.name: "kling"`, but different `params`/`schema`/`handles`, and critically a **different `kind` shape**. Confirmed from a real production workflow (fashion pose-matrix generator).

```json
"model": { "name": "kling" },
"menu": { "icon": "EmojiObjectsIcon", "isModel": true, "displayName": "Kling First & Last Frame" },
"params": { "model": "O1 Pro", "duration": 5, "cfg_scale": 0.5 },
"schema": {
  "model": { "type": "enum", "title": "Model", "default": "O1 Pro", "options": ["O1 Pro", "O1 Standard", "2.1 Pro", "2.5 Turbo Pro"], "description": "Kling model type" },
  "duration": { "type": "enum", "title": "Duration", "default": 5, "options": [5, 10], "description": "Length of the video - 5 or 10 seconds." },
  "cfg_scale": { "type": "number", "title": "Guidance Scale", "default": 0.5, "min": 0, "max": 1 }
},
"handles": {
  "input": {
    "prompt": { "type": "text", "label": "prompt", "required": true },
    "image": { "type": "image", "label": "first_frame", "required": true, "description": "URL of the image to be used for the video" },
    "tail_image_url": { "type": "image", "label": "last_frame", "required": false, "description": "URL of the image to be used for the end of the video" },
    "negative_prompt": { "type": "text", "label": "negative_prompt", "required": false }
  },
  "output": { "video": { "type": "video", "label": "video" } }
}
```

**🔴 `kind.type` for this variant is `"wildcard"` (Shape B)**, not the named-key Shape A used by "Kling 3.0 Pro" above — the `kind` block for this node is an array-of-tuples exactly like Nano Banana Pro's, with `prompt`/`image`/`tail_image_url`/`negative_prompt` as `[<field schema>, <binding>]` pairs inside `kind.inputs`, and `model`/`duration`/`cfg_scale` as `[<field schema>, {"type":"value","data":{...}}]` pairs inside `kind.parameters` — follow the Shape B template in `references/json_schema.md`, not Shape A.

Differences from "Kling 3.0 Pro" to watch for: `duration` is a fixed enum `[5, 10]` here (not a free 3–15 range), the last-frame handle is named **`tail_image_url`** (not `end_image_url`), and there's no `shot_type`/`aspect_ratio`/`generate_audio` params. **Never assume which Kling variant applies from `model.name` alone** — match the exact `params`/`handles`/`kind.type` shown here or in the "Kling 3.0 Pro" entry to whichever one the user's pasted node (or the brief's context) actually matches; if unsure, ask the user to paste their Kling node so you can confirm which preset it is.

---

## `string` — simple editable text value

```json
"data": {
  "name": "USER BRIEF",
  "value": "<the literal text the user typed>",
  "result": { "string": "" },
  "output": { "type": "text", "text": "", "string": "" },
  "handles": {
    "input": {},
    "output": { "text": { "type": "text", "description": "Text" } }
  }
}
```
Distinct from `promptV3`'s static variant: `string` stores its text in `data.value` (not `data.prompt`) and outputs via handle key `text` (not `prompt`). Use for short user-facing input fields meant to be edited directly in Weave after pasting — e.g. a "USER BRIEF" or "TARGET AUDIENCE" field the user fills in per-run — versus `promptV3` which is more for longer instructional/system text. Both are valid for plain literal text; pick `string` when the brief implies a single-line, user-editable input value. **Confirmed working** in a live paste-and-run test.

---



Two flavors, same `type`:

**A. Static/literal text** (no inputs) — for system prompts, fixed instructions, or any text the user dictates verbatim:
```json
"data": {
  "name": "System Prompt",
  "output": { "type": "text", "prompt": "<the literal text>" },
  "handles": { "output": { "prompt": { "type": "text" } } }
}
```
No `handles.input` key at all (empty/absent) — this node originates text, it doesn't transform it.

**B. Merge node** (2 text inputs → 1 combined output) — for combining e.g. a style brief + a subject brief into one final prompt. **✅ CONFIRMED (2026-07-02): paste + run tested clean, no crash, correct templated output.**
```json
"data": {
  "name": "Merge brief of both style and item",
  "prompt": "Ingredient A: {{variable1}}\nIngredient B: {{variable2}}",
  "result": { "prompt": "<resolved text, both variables substituted>" },
  "displayMode": "source",
  "inputNodes": [
    ["variable1", { "nodeId": "<source node id>", "outputId": "<source output key>", "string": "<literal upstream value>" }],
    ["variable2", { "nodeId": "<source node id>", "outputId": "<source output key>", "string": "<literal upstream value>" }]
  ],
  "handles": {
    "input": {
      "variable1": { "id": "<uuid, distinct from the key>", "type": "text", "label": "Variable 1", "order": 0, "format": "text", "required": false, "description": "" },
      "variable2": { "id": "<uuid, distinct from the key>", "type": "text", "label": "Variable 2", "order": 1, "format": "text", "required": false, "description": "" }
    },
    "output": { "prompt": { "type": "text", "order": 0, "format": "text", "description": "Text prompt" } }
  }
}
```
**⚠️ Do NOT use the bare shorthand `{"variable1": {"type": "text"}}` for this node's input handles** — always use the full field set (`id`/`label`/`order`/`format`/`required`/`description`) shown above. The shorthand is unverified for this specific node variant; the full shape is the one confirmed working.

Unlike the static variant, this one genuinely performs `{{variable}}` templating inside Weave itself — confirmed visually (the canvas renders "Variable 1"/"Variable 2" as inline highlighted chips inside the merged text, and running the node produces the correctly substituted string). It is not merely a passive label/concatenation point. That said, it's still common and valid to feed its output into a downstream `custommodelV2` (Any LLM) for further reasoning on top of the merged text — just don't assume the merge node itself does nothing.

**✅ CONFIRMED PATTERN (2026-07-04): a single-variable `promptV3` (only `variable1`, `variable2` omitted) can be templated from a `muxv2` `list_selector` instead of a static string — and the *same* selector node can drive `variable1` on multiple separate `promptV3` nodes at once.** Real production example (fashion pose-matrix generator): one `muxv2` node (`list_selector`, options `["white", "black"]`, i.e. a skin-tone toggle) fed `variable1` on **two different `promptV3` nodes simultaneously** — one templating a long system prompt (`"Male model with short dark hair, {{variable1}} skin\n..."`), the other templating a separate content prompt reusing the same word. Both nodes' `inputNodes` array pointed at the identical `{nodeId, outputId}` pair from the one `muxv2` node. This means: to add one control that swaps a value across an entire pipeline's worth of prompts in sync, use one `muxv2` list_selector as the single source of truth and wire its output into `variable1` on every `promptV3` node that needs that value — don't duplicate the selector per prompt.

Use static `promptV3` for: system prompts, fixed creative briefs, instructional text. Use the merge variant when two separate text sources need to converge into one input for a downstream model, or when one small controllable value (e.g. a toggle) needs to be templated into one or more prompts from a single shared `muxv2` source.

---

## `router` — pass-through / junction

```json
"data": {
  "name": "Router",
  "handles": {
    "input": { "in": { "type": "any" } },
    "output": { "out": { "type": "any" } }
  }
}
```
Purely a relay point — same value goes in `in`, comes out `out`. Used heavily in the reference workflow as: (a) a clean visual junction when one output feeds multiple downstream nodes, (b) a way to rename/relabel a value mid-pipeline for readability (e.g. a router named "Style" sitting between an import node and its consumers), (c) bridging across `custom_group` boundaries. Use whenever a value needs to fan out to 2+ destinations, or whenever you want a clearer node label at a key junction without changing the actual data. Needs a `data.inputNode: {nodeId, outputId, string}` binding alongside its `edges` entry — see `references/json_schema.md`.

---

## `muxv2` — option selector

```json
"data": {
  "name": "List",
  "params": { "options": [] },
  "schema": { "options": { "type": "array", "title": "Options", "exposed": true, "description": "Array of options to choose from" } },
  "handles": {
    "input": { "options": { "type": "array" } },
    "output": { "option": { "type": "text" } }
  },
  "selected": 0
}
```
Takes an array in, lets the user (or App Mode UI) pick one, outputs the chosen text. Used in the reference workflow both as a generic "List" (e.g. choosing a theme/style variant) and renamed "Resolution" (choosing an output resolution from a preset array). `exposed: true` in the schema means it surfaces as a user-facing control in Weave's "App Mode" simplified UI — set this when the brief implies the workflow should become a reusable mini-app with a dropdown. `selected` is the 0-based index of the currently-picked option — default to `0`.

**`isIterator: true`** (seen set at `data.isIterator`, alongside `data.type: "list_selector"`) marks this `muxv2` as an iterator rather than a static picker — confirmed in a real workflow where a single array (5 generated ad scripts) fed this node, and its output was consumed by 8 parallel downstream branches, each extracting a different fixed slice via its own system prompt. Set this flag whenever the brief implies "for each item in this list, do X" rather than "let the user pick one item".

**Alternative fan-out pattern — N static indexers instead of one iterator:** a real production workflow (icon-pack generator, 10 icons from one array) used **10 separate `muxv2` nodes**, each with `isIterator` omitted/false and `"selected": 0` through `9` respectively, all pointing at the *same* upstream `array`/`router` output — rather than one `isIterator: true` node. Each selector then feeds its own downstream branch. Prefer this pattern when the fan-out count is fixed and known at generation time (e.g. "generate exactly 10 icons") and each branch needs a distinct static index; prefer `isIterator: true` when the brief implies a dynamic, index-agnostic "for each" relationship. Both are confirmed-working; pick based on which better matches the brief's intent, not just count.

**✅ Second confirmed instance (2026-07-04):** the N-static-indexers pattern also underpins a full "1 LLM call → N images" fan-out, seen end-to-end in a real fashion pose-matrix workflow: one `custommodelV2` (`any_llm`, Gemini 3 Pro, 4 image inputs + a pose-director system prompt) generated 8 pose-variant prompts in one response, separated by `^` → one `array` node split them (`"delimiter": "^"`, confirming `^` as a second working delimiter alongside the previously-documented `,` and `§§`) → **8 separate `muxv2` nodes** with `"selected": 0`–`7` each picked one prompt → each selector fed its own `custommodelV2` (Nano Banana Pro) image-generation node, all four also wired to the same 4 upstream reference images via `router` pass-throughs. This is the general shape to reach for whenever a brief implies "generate one prompt per variant, then render each variant" — one LLM call, one `array` split, N static `muxv2` selectors, N parallel generation nodes.

---

## `array` — array builder

```json
"data": {
  "name": "Array",
  "delimiter": ",",
  "handles": {
    "input": { "text": { "type": "text" } },
    "output": { "array": { "type": "array" } }
  }
}
```
Collects text input(s) into an array, typically feeding a downstream `muxv2`. Use when the brief implies a list of options/variants needs to be assembled before selection. `delimiter` is configurable — defaults to `","` but set it to whatever the upstream node uses to separate items (e.g. an LLM instructed to separate outputs with `§§` should feed an `array` node with `"delimiter": "§§"`, confirmed working in a real script-generation pipeline).

---

## `import` — file/image upload

```json
"data": {
  "name": "Style input",
  "color": "Yambo_Blue",
  "files": [
    { "type": "image", "url": "<uploaded file url>", "width": 1024, "height": 1024, "name": "<label>", "insertionOrder": 1 }
  ],
  "output": { "file": { "type": "image", /* ...same shape as the selected file in files[] */ } },
  "selectedIndex": 0,
  "handles": { "output": { "file": { "type": "any", "format": "uri" } } }
}
```
No input handles — this is where real uploaded assets enter the workflow (reference images, style guides, etc.). **When generating a new workflow from scratch, you cannot fabricate real `url` values** — leave `files` as an empty array `[]` and tell the user they'll need to click the node in Weave and upload their actual reference image(s) after pasting. Don't invent placeholder URLs; they won't resolve to real assets.

---

## `export` — terminal output

```json
"data": {
  "name": "Export",
  "handles": { "input": { "file": { "type": "any" } } }
}
```
No output handles — terminal node. Wire the final result of any branch here so the user can download it from Weave. A workflow can have multiple `export` nodes (one per distinct final output, e.g. one for the PNG, one for the 3D model, one for the SVG). Like `router`/`array`, `export` also needs a `data.inputNode: {nodeId, outputId, string}` binding alongside the `edges` entry — see `references/json_schema.md`.

---

## `workflow_output` — App Mode output marker

```json
"data": {
  "name": "Output",
  "handles": { "input": { "workflow": null } }
}
```
Marks which result Weave's "App Mode" (the simplified end-user UI Weave can auto-generate from a workflow) should surface as THE output. Include one of these, wired to the main final result, whenever the brief implies the workflow will be turned into a reusable mini-app/tool for non-technical teammates.

---

## `compv3` — layer compositor

```json
"data": {
  "handles": {
    "input": {
      "layer_1": {"order": 1, "format": "uri", "required": false}, "layer_2": {"order": 2, "format": "uri", "required": false},
      "...": "layer_3 through layer_10, same shape, incrementing order",
      "background": {"order": 0, "format": "uri", "required": false}
    },
    "output": { "image": { "type": "image", "order": 0 } }
  },
  "params": null, "schema": null,
  "data": {
    "fps": 24, "duration": 5, "isTimelineEnabled": false,
    "stage": { "width": 5200, "height": 2080 },
    "input": [ ["layer_1", {"nodeId": "<source>", "outputId": "image", "file": {"...": "full file object"}}], "...one tuple per wired layer, plus background..." ],
    "layerOrder": [0, 5, 1, 4, 2, 3, 6, 7, 8, 9, 10],
    "layers": {
      "0": {
        "name": "Background", "position": {"x": -0.09, "y": -4.31}, "rotation": 0,
        "scale": {"x": 1, "y": 1}, "dimension": {"x": 5199.8, "y": 2088.6},
        "startTime": 0, "duration": 5, "locked": false, "visible": true,
        "color": {"r": 255, "g": 255, "b": 255, "a": 1}, "blendMode": "source-over",
        "lockedAspectRatio": false,
        "kind": { "type": "image", "inputId": "background", "imageMode": "stretch" }
      },
      "1": { "...": "same shape, one entry per placed layer, key = layer's position in layerOrder (not necessarily the layer_N number)" }
    }
  }
}
```
Up to 10 stackable layers plus a background, composited into one image on an explicit canvas (`stage.width`/`height`). This is the real internal structure confirmed from production — **the `data.data` nesting is correct, not a typo**: there's an outer `data` (the node's data block) and an inner `data.data` (the compositor's own scene graph). **✅ CONFIRMED (2026-07-02): paste + run tested clean, no crash** — a 3-layer test (background + 2 layers, all sourced from `painterV2` nodes, no AI credits spent) ran successfully end-to-end through an `export` node. This also confirms `painterV2.result` is a valid source for `compv3.background` (and any `layer_N` slot) — no special handling needed, wire it like any other image-output node. Only wire the layer slots actually needed — omit unused `layer_N` entries from both `handles.input` and `data.data.input`/`layers`, same as any other optional input. Each `layers.<key>` entry positions and sizes that layer independently (absolute pixel coordinates relative to the stage, not the canvas node position) — when arranging N images, lay them out in a grid or row across `stage.width`/`height` and set each layer's `position`/`dimension` accordingly; `layerOrder` controls z-index/stacking order top-to-bottom in the array. `duration`/`startTime`/`fps` matter only if the composite includes video layers — for a static image sheet they can all stay at the defaults shown (`5`, `0`, `24`). Use for "combine these elements into one image", "make a spec sheet / contact sheet from these results", logo/badge assembly, etc.

---

## `painterV2` — manual masking

```json
"data": {
  "name": "Painter",
  "handles": {
    "input": { "image": { "type": "image", "required": false, "description": "Image background" } },
    "output": { "mask": { "type": "mask" }, "result": { "type": "image" } }
  },
  "options": {
    "width": 2920, "height": 2080, "lockAspectRatio": false,
    "backgroundColor": {"r": 0, "g": 0, "b": 0, "a": 1},
    "brushColor": {"r": 255, "g": 255, "b": 255, "a": 1},
    "brushSize": 20, "brushHardness": 1,
    "eraserSize": 30, "eraserHardness": 1, "eraserOpacity": 1,
    "strokes": []
  }
}
```
Lets the user manually paint a mask over an image inside Weave (e.g. for targeted inpainting), or acts as a blank sizeable canvas (e.g. a solid-color background for a `compv3` composite when no `image` input is wired — confirmed usage: an unwired Painter with `backgroundColor` set feeding a compositor's `background` input). `width`/`height` in `options` set the canvas size independent of the node's own `width`/`height` on the outer object — for a compositing background, match this to the target `compv3`'s `stage.width`/`height`. Outputs both the raw `mask` and a composited `result`. `strokes: []` is correct for a freshly generated node — Weave populates it once the user actually paints.

---

## `custom_group` — organizational frame

Not a functional node — purely visual grouping. See `references/json_schema.md` for full structure and the critical relative-positioning rule for children. Use to wrap logically-related clusters (e.g. "User Input", "3D Pipeline", "Pack Render") once a workflow exceeds ~6 nodes.

---

## Color palette reference (cosmetic, but keep consistent)

Tokens observed in production: `Yambo_Orange`, `Yambo_Blue`, `Yambo_Purple`, `Yambo_Green`, `Red`. Each has a `_Dark` variant (for `dark_color`) and a `_Stroke` variant (for `border_color`) — just append the suffix. `custom_group` nodes use raw hex instead (e.g. `#EDF2B3`) — don't mix the two systems.

Suggested convention for new workflows (not enforced by Weave, just keeps things legible):
- Blue → inputs/imports
- Green → text/prompts
- Orange/Purple → model calls (alternate between consecutive stages so the pipeline reads as distinct steps)
- Red → export/output/terminal nodes
