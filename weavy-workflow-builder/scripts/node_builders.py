#!/usr/bin/env python3
"""
Reusable node/edge builder functions for Weave clipboard JSON.

Why this exists: hand-writing large workflows (20+ nodes) node-by-node in raw JSON
is where handle-key typos and duplicate/missing edges creep in. This script is the
generation *pattern*, not a fixed template — copy the functions you need into a new
build script per workflow, call them in whatever graph shape the brief calls for,
then dump to JSON. Validated on a real 31-node/38-edge production workflow (script
generation -> 8-way shot extraction -> 8 parallel Kling clips), confirmed working
after pasting into a live Weave canvas.

Always validate before handing the JSON to the user — see `validate()` at the bottom.
This catches the two most common self-inflicted errors: duplicate edges (usually from
calling a helper that already adds an edge, then adding it again manually) and
handle-key mismatches (edge references a key not declared in that node's data.handles).

Only a subset of node types have builders below (the ones most often needed at scale:
string, promptV3, any_llm, array, muxv2 iterator, kling). For every other type in
references/node_catalog.md, write the node dict directly following that entry's shape
-- these functions are a starting point, not the full catalog in code form.
"""
import json
import uuid


def new_graph():
    """Fresh nodes/edges accumulator + id generator, scoped per workflow."""
    return {"nodes": [], "edges": []}


def nid():
    return str(uuid.uuid4())


def add_edge(graph, src, tgt, out_key, in_key, src_color, tgt_color, htype="text"):
    """Add one edge. Does NOT check for an existing identical edge -- call this
    exactly once per logical connection. If a helper below already adds an edge
    for a given input (see docstrings), do not call add_edge again for that same
    input or you'll get a duplicate wire."""
    graph["edges"].append({
        "id": nid(), "source": src, "target": tgt, "type": "custom",
        "sourceHandle": f"{src}-output-{out_key}",
        "targetHandle": f"{tgt}-input-{in_key}",
        "data": {"sourceColor": src_color, "targetColor": tgt_color,
                 "sourceHandleType": htype, "targetHandleType": htype}
    })


def string_node(graph, name, value, x, y):
    """User-editable single text value. Confirmed working (paste + run test)."""
    i = nid()
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "string",
        "visibility": None, "isModel": False,
        "data": {
            "handles": {"input": {}, "output": {"text": {"type": "text", "order": 0, "format": "text", "description": "Text"}}},
            "name": name, "description": "", "color": "Yambo_Green", "label": None, "menu": None,
            "params": None, "schema": None, "version": 3, "result": {"string": ""},
            "dark_color": "Yambo_Green_Dark", "border_color": "Yambo_Green_Stroke",
            "value": value, "output": {"type": "text", "text": "", "string": ""}
        },
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 268
    })
    return i


def prompt_static(graph, name, prompt, x, y, named_input=None):
    """promptV3 node. Pass named_input='script' (or similar) to give it one labeled
    text input (e.g. for a template that references {{script}}); leave None for a
    pure static/system-prompt node with no inputs. Does NOT add an edge or set
    inputNodes -- call link_named_input() separately once you know the source."""
    i = nid()
    handles_input = [] if not named_input else {
        named_input: {"description": "", "format": "text", "id": nid(), "order": 0,
                       "required": False, "label": named_input.capitalize(), "type": "text"}
    }
    data = {
        "handles": {"input": handles_input, "output": {"prompt": {"type": "text", "order": 0, "format": "text", "description": "Text prompt"}}},
        "name": name, "description": None, "color": "Yambo_Green", "label": "prompt", "menu": None,
        "params": None, "schema": None, "version": 3, "prompt": prompt, "result": {"prompt": prompt},
        "dark_color": "Yambo_Green_Dark", "border_color": "Yambo_Green_Stroke",
        "inputNodes": [], "displayMode": "source-value", "output": {"type": "text", "prompt": prompt}
    }
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "promptV3",
        "visibility": None, "isModel": False, "data": data,
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 335
    })
    return i


def link_named_input(graph, node_id, input_key, source_node_id, output_id):
    """Set data.inputNodes on a promptV3 node with a named input (see prompt_static
    named_input=), AND add the matching edge. Call this once per named input --
    it handles both the `inputNodes` binding and the `edges` entry, so don't add
    a separate add_edge() call for the same connection."""
    for n in graph["nodes"]:
        if n["id"] == node_id:
            n["data"]["inputNodes"] = [[input_key, {"nodeId": source_node_id, "outputId": output_id, "string": ""}]]
    add_edge(graph, source_node_id, node_id, output_id, input_key, "Yambo_Green", "Yambo_Green")


def any_llm(graph, name, x, y, prompt_src, prompt_out, prompt_src_color, system_src=None, system_out=None):
    """custommodelV2 / any_llm node. Adds the `prompt` edge AND kind binding
    automatically. If system_src is given, ALSO adds the `system_prompt` edge --
    don't add either manually afterward, or you'll duplicate them."""
    i = nid()
    kind = {
        "type": "any_llm", "images": [["image", None]],
        "model": {"type": "value", "data": {"type": "string", "value": "anthropic/claude-sonnet-4-5"}},
        "temperature": {"type": "value", "data": {"type": "float", "value": 0}},
        "thinking": {"type": "value", "data": {"type": "boolean", "value": False}},
        "prompt": {"nodeId": prompt_src, "outputId": prompt_out, "string": ""},
    }
    if system_src:
        kind["systemPrompt"] = {"nodeId": system_src, "outputId": system_out, "string": ""}
    data = {
        "handles": {
            "input": {
                "prompt": {"type": "text", "order": 0, "format": "text", "required": True, "description": "Describe your request from the model"},
                "system_prompt": {"type": "text", "order": 1, "format": "text", "required": False, "description": "Describe the purpose of the model"},
                "image": {"type": "image", "label": "image 1", "order": 2, "format": "uri", "required": False, "description": "Image to analyse"}
            },
            "output": {"text": {"type": "text", "order": 0, "format": "text", "description": "The LLM response"}}
        },
        "name": name, "description": "Run any large language model.", "color": "Yambo_Purple", "label": None, "menu": None,
        "model": {"name": "any_llm"}, "params": {"model": "anthropic/claude-sonnet-4-5", "temperature": 0},
        "schema": {
            "model": {"type": "enum", "order": 0, "title": "Model Name", "default": "google/gemini-3-pro",
                "options": ["anthropic/claude-sonnet-4-5", "anthropic/claude-opus-4-6", "anthropic/claude-opus-4-5",
                            "anthropic/claude-3-haiku", "google/gemini-2.0-flash-001", "google/gemini-2.5-flash",
                            "google/gemini-2.5-flash-lite", "google/gemini-3-pro", "openai/gpt-4o", "openai/gpt-4.1",
                            "openai/gpt-5-chat", "meta-llama/llama-4-maverick", "meta-llama/llama-4-scout"],
                "description": "Name of the model to use"},
            "thinking": {"type": "boolean", "order": 5, "title": "Thinking", "default": False, "required": False, "description": "Enhanced reasoning for complex tasks (supported models only)"},
            "temperature": {"max": 2, "min": 0, "type": "number", "title": "Temperature", "default": 0, "description": "Lower = more predictable, higher = more diverse responses."}
        },
        "version": 3, "dark_color": "Yambo_Purple_Dark", "border_color": "Yambo_Purple_Stroke",
        "kind": kind, "generations": [], "selectedIndex": 0, "cameraLocked": False, "result": [], "output": {}, "selectedOutput": 0
    }
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "custommodelV2",
        "visibility": None, "isModel": True, "data": data,
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 562
    })
    add_edge(graph, prompt_src, i, prompt_out, "prompt", prompt_src_color, "Yambo_Purple")
    if system_src:
        add_edge(graph, system_src, i, system_out, "system_prompt", "Yambo_Green", "Yambo_Purple")
    return i


def array_node(graph, name, source_node_id, source_output_id, x, y, delimiter=","):
    """array node with a configurable split delimiter. Adds its own edge."""
    i = nid()
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "array",
        "visibility": None, "isModel": False,
        "data": {
            "handles": {
                "input": {"text": {"id": nid(), "type": "text", "order": 0, "format": "text", "required": False, "description": "Text to split into array"}},
                "output": {"array": {"id": nid(), "type": "array", "order": 0, "format": "text", "description": "Array of text items"}}
            },
            "name": name, "description": "Array of elements", "color": "Yambo_Green", "label": None, "menu": None,
            "params": None, "schema": None, "version": 3, "array": [""], "result": [], "delimiter": delimiter,
            "dark_color": "Yambo_Green_Dark", "border_color": "Yambo_Green_Stroke",
            "output": {"type": "array", "array": []},
            "inputNode": {"nodeId": source_node_id, "outputId": source_output_id, "string": ""}
        },
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 278
    })
    add_edge(graph, source_node_id, i, source_output_id, "text", "Yambo_Purple", "Yambo_Green", "text")
    return i


def mux_iterator(graph, name, source_array_node_id, x, y):
    """muxv2 with isIterator=True -- set this when the brief implies 'for each item
    in this list, do X' (fan-out) rather than a single user-facing dropdown pick."""
    i = nid()
    graph["nodes"].append({
        "id": i, "type": "muxv2",
        "data": {
            "version": 3, "description": "Select an option from a list", "type": "list_selector", "name": name,
            "handles": {
                "input": {"options": {"id": nid(), "type": "array", "label": "Options", "format": "array", "required": False, "order": 0, "description": "Array of options to choose from"}},
                "output": {"option": {"id": nid(), "type": "text", "label": "Text", "order": 0, "format": "text", "description": "The selected option", "required": False}}
            },
            "options": {"nodeId": source_array_node_id, "outputId": "array", "stringArray": []},
            "delimiter": ",", "list": [], "selected": 0,
            "schema": {"options": {"order": 0, "type": "array", "title": "Options", "exposed": True, "required": False, "description": "Array of options to choose from"}},
            "isIterator": True, "color": "Yambo_Green", "result": "", "output": {"type": "text", "option": ""}, "params": {"options": []}
        },
        "isModel": False, "owner": None, "visibility": "public", "locked": False,
        "position": {"x": x, "y": y}, "createdAt": "2026-01-01T00:00:00.000Z",
        "selected": False, "width": 250, "height": 102
    })
    add_edge(graph, source_array_node_id, i, "array", "options", "Yambo_Green", "Yambo_Green", "array")
    return i


def kling(graph, name, x, y, prompt_src, prompt_out, prompt_src_color):
    """custommodelV2 / kling (image-to-video). Adds its own `prompt` edge + kind
    binding. Leaves `image` (first_frame) unwired -- wire it separately (or tell
    the user they need to attach a reference image per clip after pasting)."""
    i = nid()
    data = {
        "handles": {
            "input": {
                "prompt": {"id": nid(), "type": "text", "label": "prompt", "order": 0, "format": "text", "required": True, "description": "Text prompt for video generation."},
                "image": {"id": nid(), "type": "image", "label": "first_frame", "order": 1, "format": "text", "required": False, "description": "The image to be used for the video"},
                "end_image_url": {"id": nid(), "type": "image", "label": "last_frame", "order": 2, "format": "text", "required": False, "description": "The image to be used for the end of the video"},
                "negative_prompt": {"id": nid(), "type": "text", "label": "negative_prompt", "order": 3, "format": "text", "required": False}
            },
            "output": {"video": {"type": "video", "label": "video", "order": 0, "format": "uri", "description": "The video result"}}
        },
        "name": name, "description": "Kling 3.0 Pro: Top-tier image-to-video.", "color": "Red", "label": None,
        "menu": {"icon": "EmojiObjectsIcon", "isModel": True, "displayName": "Kling 3 Pro"},
        "model": {"name": "kling"},
        "params": {"model": "3.0 Pro", "duration": "5", "cfg_scale": 0.5, "shot_type": "customize", "aspect_ratio": "9:16", "generate_audio": False},
        "schema": {
            "model": {"type": "enum", "order": 0, "title": "Model", "default": "Pro", "options": ["3.0 Pro", "3.0 Standard"], "required": False},
            "duration": {"max": 15, "min": 3, "type": "integer", "title": "Duration", "default": 5, "required": False},
            "cfg_scale": {"max": 1, "min": 0, "type": "number", "title": "Cfg Scale", "default": 0.5, "required": False},
            "shot_type": {"type": "enum", "title": "Shot Type", "default": "customize", "options": ["customize"], "required": False},
            "aspect_ratio": {"type": "enum", "title": "Aspect Ratio (T2I only)", "default": "16:9", "options": ["16:9", "9:16", "1:1"], "required": False},
            "generate_audio": {"type": "boolean", "title": "Generate Audio", "default": False, "required": False}
        },
        "version": 3,
        "kind": {
            "type": "kling",
            "model": {"type": "value", "data": {"type": "string", "value": "3.0 Pro"}},
            "duration": {"type": "value", "data": {"type": "integer", "value": 5}},
            "cfgScale": {"type": "value", "data": {"type": "float", "value": 0.5}},
            "shotType": {"type": "value", "data": {"type": "string", "value": "customize"}},
            "aspectRatio": {"type": "value", "data": {"type": "string", "value": "9:16"}},
            "generateAudio": {"type": "value", "data": {"type": "boolean", "value": False}},
            "elements": [],
            "prompt": {"nodeId": prompt_src, "outputId": prompt_out, "string": ""}
        },
        "generations": [], "selectedIndex": 0, "cameraLocked": False, "result": [], "output": {}, "selectedOutput": 0
    }
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "custommodelV2",
        "visibility": "private", "isModel": True, "data": data,
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 560
    })
    add_edge(graph, prompt_src, i, prompt_out, "prompt", prompt_src_color, "Red")
    return i


def wildcard_model(graph, name, x, y, model_name, model_meta, input_specs, param_specs, output_specs, color="Red"):
    """custommodelV2 node using kind.type == 'wildcard' -- the shape used by every
    generic/fal_imported model EXCEPT any_llm and kling (e.g. nano-banana-pro/edit,
    br_bgrmv, recraft/vectorize, hyper3d/rodin). Confirmed from a real export;
    structurally different from any_llm()'s named-key kind -- do not reuse any_llm()
    for these models.

    model_meta: dict like {"service": "fal_imported", "version": "...", "description": "..."}
      (omit keys that don't apply to this model)
    input_specs: list of (field_schema_dict, source_node_id, source_output_id) tuples.
      field_schema_dict is the {id, title, description, validTypes, required} shape
      copied from the model's catalog entry. Pass source_node_id=None for an unwired
      optional input -- it will be omitted entirely (matches confirmed behavior).
    param_specs: list of (field_schema_dict, param_type, param_value) tuples.
      field_schema_dict is {id, title, description, constraint, defaultValue}.
    output_specs: list of {id, title, description, dataType} dicts, mirrors handles.output.
    """
    i = nid()
    inputs = []
    for field_schema, src_node, src_output in input_specs:
        if src_node is None:
            continue
        inputs.append([field_schema, {"nodeId": src_node, "outputId": src_output, "string": ""}])
        add_edge(graph, src_node, i, src_output, field_schema["id"], "Yambo_Purple", color)
    parameters = [
        [field_schema, {"type": "value", "data": {"type": param_type, "value": param_value}}]
        for field_schema, param_type, param_value in param_specs
    ]
    kind = {
        "type": "wildcard",
        "model": {"type": "predefined", "name": model_name, **model_meta},
        "inputs": inputs,
        "parameters": parameters,
        "outputs": output_specs,
    }
    handles_input = {
        spec[0]["id"]: {"type": spec[0]["validTypes"][0], "label": spec[0]["title"],
                         "order": idx, "required": spec[0].get("required", False),
                         "description": spec[0].get("description", "")}
        for idx, spec in enumerate(input_specs)
    }
    handles_output = {o["id"]: {"type": o["dataType"], "order": idx, "description": o.get("description", "")}
                       for idx, o in enumerate(output_specs)}
    data = {
        "handles": {"input": handles_input, "output": handles_output},
        "name": name, "description": model_meta.get("description", ""), "color": color, "label": None, "menu": None,
        "model": {"name": model_name, **{k: v for k, v in model_meta.items() if k in ("service", "version")}},
        "params": {}, "schema": {}, "version": 3,
        "dark_color": f"{color}_Dark", "border_color": f"{color}_Stroke",
        "kind": kind, "generations": [], "selectedIndex": 0, "cameraLocked": False, "result": [], "output": {}, "selectedOutput": 0
    }
    graph["nodes"].append({
        "id": i, "dragHandle": ".node-header", "owner": None, "type": "custommodelV2",
        "visibility": None, "isModel": True, "data": data,
        "createdAt": "2026-01-01T00:00:00.000Z", "updatedAt": "2026-01-01T00:00:00.000Z",
        "locked": False, "position": {"x": x, "y": y}, "selected": False, "width": 460, "height": 552
    })
    return i


def validate(graph):
    """Run before handing JSON to the user. Returns a list of problems (empty = clean).
    Catches: duplicate node/edge ids, edges pointing to nonexistent nodes, duplicate
    wiring (same source+target+handles more than once), and handle keys used in an
    edge that aren't declared in that node's data.handles."""
    problems = []
    node_ids = [n["id"] for n in graph["nodes"]]
    if len(node_ids) != len(set(node_ids)):
        problems.append("duplicate node ids")
    edge_ids = [e["id"] for e in graph["edges"]]
    if len(edge_ids) != len(set(edge_ids)):
        problems.append("duplicate edge ids")

    by_id = {n["id"]: n for n in graph["nodes"]}
    combos = set()
    for e in graph["edges"]:
        if e["source"] not in by_id:
            problems.append(f"edge {e['id']} source {e['source']} not found")
            continue
        if e["target"] not in by_id:
            problems.append(f"edge {e['id']} target {e['target']} not found")
            continue
        combo = (e["source"], e["target"], e["sourceHandle"], e["targetHandle"])
        if combo in combos:
            problems.append(f"duplicate wiring: {combo}")
        combos.add(combo)

        out_key = e["sourceHandle"].split("-output-")[-1]
        in_key = e["targetHandle"].split("-input-")[-1]
        out_handles = by_id[e["source"]]["data"]["handles"]["output"]
        in_handles = by_id[e["target"]]["data"]["handles"]["input"]
        if isinstance(out_handles, list):
            out_handles = {}
        if isinstance(in_handles, list):
            in_handles = {}
        if out_key not in out_handles:
            problems.append(f"'{by_id[e['source']]['data']['name']}' has no output handle '{out_key}'")
        if in_key not in in_handles:
            problems.append(f"'{by_id[e['target']]['data']['name']}' has no input handle '{in_key}'")
    return problems


def dump(graph, path):
    """Validate, then write. Raises if validate() finds anything -- fix the graph
    before writing, don't hand broken JSON to the user."""
    problems = validate(graph)
    if problems:
        raise ValueError("Graph failed validation:\n" + "\n".join(problems))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False)
    return path
