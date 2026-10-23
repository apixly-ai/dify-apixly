"""Build importable Dify workflows from the exact package content checksum.

Node and loop shapes follow Dify's official workflow fixtures. Native host
validation/import is required in addition to the safety regression tests.
"""

from __future__ import annotations

import argparse
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


def constant(value):
    return {"type": "constant", "value": value}


def build_workflow(kind: str, plugin_checksum: str, version: str = "0.1.0") -> dict:
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
            variable("reference_image", "Reference HTTPS URL / 参考图 URL", "", True, "paragraph"),
            variable(
                "additional_images",
                "Additional reference JSON / 更多参考图数组",
                "[]",
                False,
                "paragraph",
            ),
        ]
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
                "variable": "task_id",
                "value_type": "string",
                "value_selector": ["submit", "task_id"],
            },
            {
                "variable": "result_state",
                "value_type": "string",
                "value_selector": ["submit", "result_state"],
            },
            {
                "variable": "details",
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checksum", required=True, help="Exact dify plugin checksum output, not the ZIP SHA256"
    )
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--output", type=Path, default=Path("examples"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for kind in ("image", "edit", "video"):
        document = build_workflow(kind, args.checksum, args.version)
        (args.output / f"apixly-{kind}-workflow.yml").write_text(
            yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
        )


if __name__ == "__main__":
    main()
