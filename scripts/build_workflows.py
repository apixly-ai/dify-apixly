"""Build importable Dify workflows from the exact package content checksum.

Node and loop shapes follow Dify's official workflow fixtures. Native host
validation/import is required in addition to the safety regression tests.
"""

from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path

import yaml

AUTHOR = "apixly-ai"
PLUGIN = "apixly_media"
PROVIDER = "apixly_media"
PROVIDER_ID = f"{AUTHOR}/{PLUGIN}/{PROVIDER}"


def variable(name, label, default="", required=False, kind="text-input"):
    return {
        "variable": name,
        "label": label,
        "type": kind,
        "required": required,
        "default": default,
        "max_length": 12000 if kind == "paragraph" else 256,
        "options": [],
    }


def binding(selector):
    return {"type": "variable", "value": selector}


def string_binding(selector):
    return {"type": "mixed", "value": "{{#" + ".".join(selector) + "#}}"}


def constant(value):
    return {"type": "constant", "value": value}


def build_workflow(kind: str, plugin_checksum: str, version: str = "0.1.1") -> dict:
    if kind not in {"image", "edit", "video"}:
        raise ValueError("kind must be image, edit, or video")
    if not re.fullmatch(r"[a-f0-9]{64}", plugin_checksum):
        raise ValueError("Use the exact 64-character checksum from dify plugin checksum")
    identifier = f"{AUTHOR}/{PLUGIN}:{version}@{plugin_checksum}"
    task_kind = "video" if kind == "video" else "image"
    submit_name = {"image": "generate_image", "edit": "edit_image", "video": "create_video"}[kind]
    title = {
        "image": "Image generation · 文生图",
        "edit": "Reference image edit · 参考图编辑",
        "video": "Video generation · 视频生成",
    }[kind]
    model = {
        "image": "grok-imagine-image",
        "edit": "gemini-3.1-flash-image",
        "video": "grok-imagine-video",
    }[kind]
    prompt = {
        "image": "A single blue ceramic cup on a clean white table, studio product photograph, no text.",
        "edit": "Keep the product unchanged and replace only its background with a soft gray studio backdrop.",
        "video": "A gentle cinematic pan across a blue ceramic cup on a white table. No text.",
    }[kind]
    inputs = [
        variable("model", "Exact model ID / 精确模型 ID", model, True),
        variable("prompt", "Prompt / 提示词", prompt, True, "paragraph"),
        variable("advanced_parameters", "Advanced JSON / 高级参数", "{}", False, "paragraph"),
    ]
    submit_params = {
        "model": binding(["start", "model"]),
        "prompt": binding(["start", "prompt"]),
        "parameters_json": binding(["start", "advanced_parameters"]),
    }
    if kind == "image":
        inputs.append(variable("aspect_ratio", "Aspect ratio / 画面比例", "1:1"))
        submit_params.update(aspect_ratio=binding(["start", "aspect_ratio"]), n=constant(1))
    elif kind == "edit":
        inputs += [
            variable(
                "reference_image",
                "Reference URL or data URL / 参考图 URL 或 data URL",
                "",
                True,
                "paragraph",
            ),
            variable(
                "additional_images",
                "Additional reference JSON / 更多参考图数组",
                "[]",
                False,
                "paragraph",
            ),
        ]
        for item in inputs:
            if item["variable"] in {"reference_image", "additional_images"}:
                item["max_length"] = 1_048_576
        submit_params.update(
            reference_image=binding(["start", "reference_image"]),
            reference_images=binding(["start", "additional_images"]),
            n=constant(1),
        )
    else:
        inputs += [
            variable("seconds", "Duration in seconds / 视频秒数", 1, True, "number"),
            variable("resolution", "Resolution / 分辨率", "720p"),
            variable("aspect_ratio", "Aspect ratio / 画面比例", "16:9"),
        ]
        submit_params.update(
            seconds=binding(["start", "seconds"]),
            resolution=binding(["start", "resolution"]),
            aspect_ratio=binding(["start", "aspect_ratio"]),
        )

    nodes = []
    edges = []

    def node(node_id, typ, label, x, y, *, parent=None, **data):
        result = {
            "id": node_id,
            "type": "custom",
            "width": 244,
            "height": 110,
            "position": {"x": x, "y": y},
            "positionAbsolute": {"x": x, "y": y},
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
            "data": {"type": typ, "title": label, "desc": "", "selected": False, **data},
        }
        if parent:
            result["parentId"] = parent
            result["zIndex"] = 1002
            result["data"].update(isInLoop=True, loop_id=parent, isInIteration=False)
        nodes.append(result)
        return result

    def tool(node_id, name, label, params, x, y, *, parent=None):
        params = copy.deepcopy(params)
        for field in (
            "model",
            "prompt",
            "parameters_json",
            "reference_image",
            "reference_images",
            "resolution",
            "aspect_ratio",
            "task_id",
        ):
            value = params.get(field)
            if value and value["type"] == "variable":
                params[field] = string_binding(value["value"])
        return node(
            node_id,
            "tool",
            label,
            x,
            y,
            parent=parent,
            provider_id=PROVIDER_ID,
            provider_name=PROVIDER_ID,
            provider_type="builtin",
            plugin_id=f"{AUTHOR}/{PLUGIN}",
            plugin_unique_identifier=identifier,
            tool_name=name,
            tool_label=label,
            tool_description="Apixly media API tool; use the provider's secret credential.",
            tool_node_version="2",
            tool_configurations={},
            tool_parameters=params,
            is_team_authorization=True,
            retry_config={"retry_enabled": False, "max_retries": 1, "retry_interval": 1000},
        )

    def edge(source, target, *, handle="source", loop=False):
        lookup = {n["id"]: n for n in nodes}
        data = {
            "sourceType": lookup[source]["data"]["type"],
            "targetType": lookup[target]["data"]["type"],
            "isInLoop": loop,
            "isInIteration": False,
        }
        if loop:
            data["loop_id"] = "poll"
        edges.append(
            {
                "id": f"{source}-{handle}-{target}",
                "type": "custom",
                "source": source,
                "sourceHandle": handle,
                "target": target,
                "targetHandle": "target",
                "zIndex": 1002 if loop else 0,
                "data": data,
            }
        )

    node("start", "start", "Start · 开始", 30, 260, variables=inputs)
    tool("submit", submit_name, "Submit ONCE · 仅提交一次", submit_params, 340, 260)
    node(
        "has_task",
        "if-else",
        "Task ID received? · 是否有任务 ID",
        650,
        260,
        cases=[
            {
                "id": "true",
                "case_id": "true",
                "logical_operator": "and",
                "conditions": [
                    {
                        "id": "task-id-present",
                        "varType": "string",
                        "variable_selector": ["submit", "task_id"],
                        "comparison_operator": "not empty",
                        "value": "",
                    }
                ],
            }
        ],
    )
    loop = node(
        "poll",
        "loop",
        "Bounded poll · 最多查询 60 次",
        970,
        260,
        start_node_id="poll_start",
        loop_count=60,
        logical_operator="and",
        break_conditions=[
            {
                "id": "terminal-state",
                "varType": "boolean",
                "variable_selector": ["poll", "terminal"],
                "comparison_operator": "is",
                "value": True,
            }
        ],
        loop_variables=[
            {
                "id": "loop-terminal",
                "label": "terminal",
                "var_type": "boolean",
                "value_type": "constant",
                "value": False,
            },
            {
                "id": "loop-state",
                "label": "last_state",
                "var_type": "string",
                "value_type": "constant",
                "value": "pending",
            },
        ],
        error_handle_mode="terminated",
        width=940,
        height=260,
    )
    loop.update(width=940, height=260, zIndex=1)
    helper = node("poll_start", "loop-start", "", 50, 90, parent="poll")
    helper.update(type="custom-loop-start", width=44, height=48, draggable=False, selectable=False)
    tool(
        "poll_query",
        "query_task",
        "Wait 5s + query · 等待后只读查询",
        {
            "kind": constant(task_kind),
            "task_id": binding(["submit", "task_id"]),
            "download": constant(False),
            "wait_seconds": constant(5),
        },
        150,
        70,
        parent="poll",
    )
    node(
        "update_poll",
        "assigner",
        "Remember terminal · 保存终态",
        460,
        70,
        parent="poll",
        version="2",
        items=[
            {
                "input_type": "variable",
                "operation": "over-write",
                "value": ["poll_query", "terminal"],
                "variable_selector": ["poll", "terminal"],
                "write_mode": "over-write",
            },
            {
                "input_type": "variable",
                "operation": "over-write",
                "value": ["poll_query", "result_state"],
                "variable_selector": ["poll", "last_state"],
                "write_mode": "over-write",
            },
        ],
    )
    tool(
        "final_query",
        "query_task",
        "Retrieve existing task · 下载原任务素材",
        {
            "kind": constant(task_kind),
            "task_id": binding(["submit", "task_id"]),
            "download": constant(True),
            "wait_seconds": constant(0),
        },
        1980,
        260,
    )
    node(
        "result",
        "end",
        "Result + files · 结果和文件",
        2290,
        260,
        outputs=[
            {"variable": field, "value_type": typ, "value_selector": ["final_query", field]}
            for field, typ in [
                ("task_id", "string"),
                ("status", "string"),
                ("terminal", "boolean"),
                ("success", "boolean"),
                ("generation_success", "boolean"),
                ("result_state", "string"),
                ("urls", "array[string]"),
                ("files", "array[file]"),
                ("json", "array[object]"),
            ]
        ],
    )
    node(
        "submit_error",
        "end",
        "STOP: inspect submission · 停止并核查提交",
        970,
        620,
        outputs=[
            {
                "variable": "submission_task_id",
                "value_type": "string",
                "value_selector": ["submit", "task_id"],
            },
            {
                "variable": "submission_result_state",
                "value_type": "string",
                "value_selector": ["submit", "result_state"],
            },
            {
                "variable": "submission_details",
                "value_type": "array[object]",
                "value_selector": ["submit", "json"],
            },
        ],
    )
    edge("start", "submit")
    edge("submit", "has_task")
    edge("has_task", "poll", handle="true")
    edge("has_task", "submit_error", handle="false")
    edge("poll_start", "poll_query", loop=True)
    edge("poll_query", "update_poll", loop=True)
    edge("poll", "final_query")
    edge("final_query", "result")
    return {
        "app": {
            "name": f"Apixly · {title}",
            "description": "Use your own Apixly API key. Free plugin; API usage billed by Apixly. Submit once, query at most 60 times with a delay, then retrieve the original task's files. Website: https://apixly.ai · Console: https://platform.apixly.ai",
            "icon": "🎨" if kind != "video" else "🎬",
            "icon_background": "#2e8fff",
            "icon_type": "emoji",
            "mode": "workflow",
            "use_icon_as_answer_icon": False,
        },
        "kind": "app",
        "version": "0.7.0",
        "dependencies": [
            {
                "current_identifier": None,
                "type": "package",
                "value": {"plugin_unique_identifier": identifier, "version": None},
            }
        ],
        "workflow": {
            "conversation_variables": [],
            "environment_variables": [],
            "features": {
                "file_upload": {"enabled": False},
                "opening_statement": "",
                "retriever_resource": {"enabled": False},
                "sensitive_word_avoidance": {"enabled": False},
                "speech_to_text": {"enabled": False},
                "suggested_questions": [],
                "suggested_questions_after_answer": {"enabled": False},
                "text_to_speech": {"enabled": False},
            },
            "graph": {"nodes": nodes, "edges": edges, "viewport": {"x": 0, "y": 0, "zoom": 0.6}},
        },
    }


def build_image_to_video(plugin_checksum: str, version: str = "0.1.1") -> dict:
    """Connect two existing safe phases without replaying either submission."""
    document = build_workflow("image", plugin_checksum, version)
    video = build_workflow("video", plugin_checksum, version)

    def phase(graph, prefix, offset):
        graph = copy.deepcopy(graph)
        ids = {node["id"]: prefix + node["id"] for node in graph["nodes"]}

        def selectors(value):
            if isinstance(value, list):
                for item in value:
                    selectors(item)
            elif isinstance(value, dict):
                for name in ("value_selector", "variable_selector"):
                    selector = value.get(name)
                    if isinstance(selector, list) and selector and selector[0] in ids:
                        selector[0] = ids[selector[0]]
                if value.get("type") == "variable" or value.get("input_type") == "variable":
                    selector = value.get("value")
                    if isinstance(selector, list) and selector and selector[0] in ids:
                        selector[0] = ids[selector[0]]
                if value.get("type") == "mixed" and isinstance(value.get("value"), str):
                    for old, new in ids.items():
                        value["value"] = value["value"].replace(
                            "{{#" + old + ".", "{{#" + new + "."
                        )
                for item in value.values():
                    selectors(item)

        for node in graph["nodes"]:
            node["id"] = ids[node["id"]]
            if node.get("parentId"):
                node["parentId"] = ids[node["parentId"]]
            else:
                node["position"]["x"] += offset
                node["positionAbsolute"]["x"] += offset
            for name in ("start_node_id", "loop_id"):
                if node["data"].get(name) in ids:
                    node["data"][name] = ids[node["data"][name]]
            selectors(node["data"])
            if node["id"] == prefix + "submit_error":
                for output in node["data"]["outputs"]:
                    output["variable"] = prefix + output["variable"]
        lookup = {node["id"]: node for node in graph["nodes"]}
        for node in graph["nodes"]:
            if node.get("parentId"):
                parent = lookup[node["parentId"]]
                node["positionAbsolute"] = {
                    "x": parent["positionAbsolute"]["x"] + node["position"]["x"],
                    "y": parent["positionAbsolute"]["y"] + node["position"]["y"],
                }
        for edge in graph["edges"]:
            edge["id"] = prefix + edge["id"]
            edge["source"] = ids[edge["source"]]
            edge["target"] = ids[edge["target"]]
            if edge["data"].get("loop_id") in ids:
                edge["data"]["loop_id"] = ids[edge["data"]["loop_id"]]
        return graph

    image_graph = phase(document["workflow"]["graph"], "image_", 0)
    video_graph = phase(video["workflow"]["graph"], "video_", 2660)
    nodes = [node for node in image_graph["nodes"] if node["id"] != "image_result"]
    nodes += [node for node in video_graph["nodes"] if node["id"] != "video_start"]
    edges = [edge for edge in image_graph["edges"] if edge["target"] != "image_result"]
    edges += [edge for edge in video_graph["edges"] if edge["source"] != "video_start"]
    lookup = {node["id"]: node for node in nodes}
    lookup["image_start"]["data"]["variables"] = [
        variable("image_model", "Image model / 图片模型", "grok-imagine-image", True),
        variable(
            "image_prompt",
            "Image prompt / 图片提示词",
            "A single blue glass vase on a clean white studio table, no text.",
            True,
            "paragraph",
        ),
        variable(
            "image_parameters", "Image advanced JSON / 图片高级参数", "{}", False, "paragraph"
        ),
        variable("video_model", "Video model / 视频模型", "grok-imagine-video-1.5-preview", True),
        variable(
            "video_prompt",
            "Video prompt / 视频提示词",
            "Use the reference image as the first frame. Preserve the exact blue vase and composition while the camera moves gently. No text.",
            True,
            "paragraph",
        ),
        variable("video_seconds", "Video seconds / 视频秒数", 3, True, "number"),
    ]
    lookup["image_submit"]["data"]["tool_parameters"] = {
        "model": string_binding(["image_start", "image_model"]),
        "prompt": string_binding(["image_start", "image_prompt"]),
        "parameters_json": string_binding(["image_start", "image_parameters"]),
        "aspect_ratio": constant("1:1"),
        "n": constant(1),
    }
    lookup["video_submit"]["data"]["tool_parameters"] = {
        "model": string_binding(["image_start", "video_model"]),
        "prompt": string_binding(["image_start", "video_prompt"]),
        "parameters_json": {"type": "mixed", "value": "{{#video_reference.output#}}"},
        "seconds": binding(["image_start", "video_seconds"]),
    }

    def ordinary(node_id, typ, label, x, y, **data):
        node = {
            "id": node_id,
            "type": "custom",
            "width": 244,
            "height": 110,
            "position": {"x": x, "y": y},
            "positionAbsolute": {"x": x, "y": y},
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
            "data": {"type": typ, "title": label, "desc": "", "selected": False, **data},
        }
        nodes.append(node)
        lookup[node_id] = node

    ordinary(
        "image_ready",
        "if-else",
        "Image delivered? · 图片交付成功才继续",
        2290,
        260,
        cases=[
            {
                "id": "true",
                "case_id": "true",
                "logical_operator": "and",
                "conditions": [
                    {
                        "id": "image-delivered",
                        "varType": "boolean",
                        "variable_selector": ["image_final_query", "success"],
                        "comparison_operator": "is",
                        "value": True,
                    }
                ],
            }
        ],
    )
    ordinary(
        "video_reference",
        "template-transform",
        "Use generated HTTPS URL · 使用生成图链接",
        2600,
        260,
        variables=[{"variable": "image_urls", "value_selector": ["image_final_query", "urls"]}],
        template='{"images": {{ image_urls[:1] | tojson }}}',
    )
    ordinary(
        "image_not_ready",
        "end",
        "Stop with original image task · 保留原图任务",
        2600,
        620,
        outputs=[
            {
                "variable": "undelivered_image_task_id",
                "value_type": "string",
                "value_selector": ["image_submit", "task_id"],
            },
            {
                "variable": "undelivered_image_result_state",
                "value_type": "string",
                "value_selector": ["image_final_query", "result_state"],
            },
            {
                "variable": "undelivered_image_details",
                "value_type": "array[object]",
                "value_selector": ["image_final_query", "json"],
            },
        ],
    )
    lookup["video_result"]["data"]["outputs"] += [
        {
            "variable": "image_task_id",
            "value_type": "string",
            "value_selector": ["image_submit", "task_id"],
        },
        {
            "variable": "image_files",
            "value_type": "array[file]",
            "value_selector": ["image_final_query", "files"],
        },
    ]

    def connect(source, target, handle="source"):
        edges.append(
            {
                "id": f"{source}-{handle}-{target}",
                "type": "custom",
                "source": source,
                "sourceHandle": handle,
                "target": target,
                "targetHandle": "target",
                "zIndex": 0,
                "data": {
                    "sourceType": lookup[source]["data"]["type"],
                    "targetType": lookup[target]["data"]["type"],
                    "isInLoop": False,
                    "isInIteration": False,
                },
            }
        )

    connect("image_final_query", "image_ready")
    connect("image_ready", "video_reference", "true")
    connect("image_ready", "image_not_ready", "false")
    connect("video_reference", "video_submit")
    document["app"].update(
        name="Apixly · Image to video · 图片到视频",
        description="Use your own Apixly key. Two billable API submissions: generate one image, then use its signed HTTPS URL with the explicitly selected reference-video model. Each stage submits once and polls with a bounded loop. https://apixly.ai · https://platform.apixly.ai",
    )
    document["workflow"]["graph"] = {
        "nodes": nodes,
        "edges": edges,
        "viewport": {"x": 0, "y": 0, "zoom": 0.3},
    }
    return document


def build_creative_workflow(kind: str, plugin_checksum: str, version: str = "0.1.1") -> dict:
    """Add free, default-off composition before one existing media phase."""
    if kind not in {"preview", "image", "edit", "video"}:
        raise ValueError("kind must be preview, image, edit, or video")
    document = build_workflow("image" if kind == "preview" else kind, plugin_checksum, version)
    graph = document["workflow"]["graph"]
    lookup = {n["id"]: n for n in graph["nodes"]}
    start = lookup["start"]
    if kind == "preview":
        start["data"]["variables"] = [
            variable(
                "prompt",
                "Base prompt / 原始提示词",
                "A red toy car with a blue roof on a studio table.",
                False,
                "paragraph",
            )
        ]
    next(v for v in start["data"]["variables"] if v["variable"] == "prompt")["max_length"] = 20000
    definition = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "tools/compose_creative_prompt.yaml").read_text()
    )
    parameters = {}
    for parameter in definition["parameters"]:
        name = parameter["name"]
        if name == "prompt":
            parameters[name] = string_binding(["start", "prompt"])
        elif name == "mode":
            parameters[name] = constant("edit" if kind == "edit" else "generate")
        elif "default" in parameter:
            parameters[name] = {
                "type": "mixed" if parameter["type"] == "string" else "constant",
                "value": parameter["default"],
            }
    composer = copy.deepcopy(lookup["submit"])
    composer.update(
        id="creative_compose", position={"x": 340, "y": 260}, positionAbsolute={"x": 340, "y": 260}
    )
    composer["data"].update(
        title="Free prompt preview · 免费提示词预览",
        provider_id=f"{AUTHOR}/{PLUGIN}/apixly_creative",
        provider_name=f"{AUTHOR}/{PLUGIN}/apixly_creative",
        tool_name="compose_creative_prompt",
        tool_label="Preview creative prompt",
        tool_description="Local composition only; no key or generation. Controls default OFF.",
        tool_parameters=parameters,
    )

    def make_node(node_id, typ, title, x, y, **data):
        node = {
            "id": node_id,
            "type": "custom",
            "width": 244,
            "height": 110,
            "position": {"x": x, "y": y},
            "positionAbsolute": {"x": x, "y": y},
            "sourcePosition": "right",
            "targetPosition": "left",
            "selected": False,
            "data": {"type": typ, "title": title, "desc": "", "selected": False, **data},
        }
        return node

    def output(name, selector, typ="string"):
        return {"variable": name, "value_selector": selector, "value_type": typ}

    def edge(source, target, handle="source"):
        nodes = {n["id"]: n for n in graph["nodes"]}
        return {
            "id": f"{source}-{handle}-{target}",
            "type": "custom",
            "source": source,
            "sourceHandle": handle,
            "target": target,
            "targetHandle": "target",
            "zIndex": 0,
            "data": {
                "sourceType": nodes[source]["data"]["type"],
                "targetType": nodes[target]["data"]["type"],
                "isInLoop": False,
                "isInIteration": False,
            },
        }

    preview_fields = [
        ("final_prompt", "string"),
        ("sections", "array[object]"),
        ("applied_tools", "array[string]"),
        ("changed", "boolean"),
        ("success", "boolean"),
        ("result_state", "string"),
        ("error_path", "string"),
        ("error", "string"),
    ]
    if kind == "preview":
        end = make_node(
            "creative_result",
            "end",
            "Prompt only · 仅预览不生成",
            650,
            260,
            outputs=[output(name, ["creative_compose", name], typ) for name, typ in preview_fields],
        )
        graph["nodes"] = [start, composer, end]
        graph["edges"] = [
            edge("start", "creative_compose"),
            edge("creative_compose", "creative_result"),
        ]
        document["app"].update(
            name="Apixly · FREE creative preview · 免费创作预览",
            description="FREE offline prompt preview: no API key, generation or network call. All three control groups default OFF. Enable a group in the compose node, choose its preset/values, and inspect final_prompt. https://apixly.ai",
        )
    else:
        # Keep the existing safe submit/poll/file phase intact, shifting it right.
        for node in graph["nodes"]:
            if node["id"] != "start" and "parentId" not in node:
                node["position"]["x"] += 680
                node["positionAbsolute"]["x"] += 680
        for node in graph["nodes"]:
            if node.get("parentId"):
                parent = lookup[node["parentId"]]
                node["positionAbsolute"] = {
                    "x": parent["positionAbsolute"]["x"] + node["position"]["x"],
                    "y": parent["positionAbsolute"]["y"] + node["position"]["y"],
                }
        lookup["submit"]["data"]["tool_parameters"]["prompt"] = string_binding(
            ["creative_compose", "final_prompt"]
        )
        ready = make_node(
            "creative_ready",
            "if-else",
            "Valid creative prompt? · 创作指令有效？",
            650,
            260,
            cases=[
                {
                    "id": "true",
                    "case_id": "true",
                    "logical_operator": "and",
                    "conditions": [
                        {
                            "id": "composition-valid",
                            "varType": "boolean",
                            "variable_selector": ["creative_compose", "success"],
                            "comparison_operator": "is",
                            "value": True,
                        }
                    ],
                }
            ],
        )
        stop = make_node(
            "creative_error",
            "end",
            "STOP: fix controls · 修正控制项",
            970,
            80,
            outputs=[
                output("creative_error_state", ["creative_compose", "result_state"]),
                output("creative_error_path", ["creative_compose", "error_path"]),
                output("creative_error_message", ["creative_compose", "error"]),
            ],
        )
        graph["nodes"] += [composer, ready, stop]
        graph["edges"] = [
            e for e in graph["edges"] if not (e["source"] == "start" and e["target"] == "submit")
        ]
        graph["edges"] += [
            edge("start", "creative_compose"),
            edge("creative_compose", "creative_ready"),
            edge("creative_ready", "submit", "true"),
            edge("creative_ready", "creative_error", "false"),
        ]
        lookup["result"]["data"]["outputs"] += [
            output("final_prompt", ["creative_compose", "final_prompt"]),
            output("creative_sections", ["creative_compose", "sections"], "array[object]"),
            output(
                "creative_applied_tools", ["creative_compose", "applied_tools"], "array[string]"
            ),
            output("creative_changed", ["creative_compose", "changed"], "boolean"),
        ]
        lookup["submit_error"]["data"]["outputs"] += [
            output("submission_final_prompt", ["creative_compose", "final_prompt"])
        ]
        label = {"image": "image generation", "edit": "reference edit", "video": "text video"}[kind]
        document["app"].update(
            name=f"Apixly · Creative {label} · controls OFF",
            description=f"Preview typed creative controls locally, then explicitly submit one billed {label} task with your own key. Controls default OFF. Invalid composition stops before submission. Original task polling/files are reused. https://apixly.ai",
        )
    graph["viewport"] = {"x": 0, "y": 0, "zoom": 0.4 if kind == "preview" else 0.3}
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checksum", required=True, help="Exact dify plugin checksum output, not the ZIP SHA256"
    )
    parser.add_argument("--version", default="0.1.1")
    parser.add_argument("--output", type=Path, default=Path("examples"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for kind in ("image", "edit", "video"):
        document = build_workflow(kind, args.checksum, args.version)
        (args.output / f"apixly-{kind}-workflow.yml").write_text(
            yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
        )
    (args.output / "apixly-image-to-video-workflow.yml").write_text(
        yaml.safe_dump(
            build_image_to_video(args.checksum, args.version), sort_keys=False, allow_unicode=True
        )
    )
    for kind in ("preview", "image", "edit", "video"):
        (args.output / f"apixly-creative-{kind}-workflow.yml").write_text(
            yaml.safe_dump(
                build_creative_workflow(kind, args.checksum, args.version),
                sort_keys=False,
                allow_unicode=True,
            )
        )


if __name__ == "__main__":
    main()
