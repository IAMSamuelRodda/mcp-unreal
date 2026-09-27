"""Structured MCP tools that wrap common UE workflows via execute-script."""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Optional

import mcp.types as types

from mcp_unreal.ue_remote import ExecMode, ExecResult, make_client

# Work root as the *editor* host sees it (scripts/, export/, screenshots/).
# Paths are sent to UE, so on a remote Windows editor set e.g.
# UE_WORK_ROOT=H:/UnrealWork; the default suits an editor on this machine.
UE_WORK_ROOT = PurePosixPath(os.environ.get("UE_WORK_ROOT") or (Path.home() / "UnrealEngine").as_posix())
DEFAULT_SCRIPTS = UE_WORK_ROOT / "scripts"
DEFAULT_EXPORT = UE_WORK_ROOT / "export" / "web"
DEFAULT_SCREENSHOTS = UE_WORK_ROOT / "screenshots"


def structured_tool_definitions() -> list[types.Tool]:
    return [
        types.Tool(
            name="ue_ping",
            description="Check MCP HTTP bridge and Unreal Engine version.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_run_script_file",
            description="Run a Python file inside the UE editor (path on workstation).",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to .py file on the UE host.",
                    }
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="ue_export_glb",
            description="Export a Content Browser asset or path to .glb using web_export presets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_path": {
                        "type": "string",
                        "description": "UE asset path e.g. /Game/Meshes/Hero.Hero",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output .glb path (defaults to export/web/).",
                    },
                    "preset": {
                        "type": "string",
                        "default": "web-default",
                        "description": "Preset from web-export-config.json",
                    },
                },
                "required": ["asset_path"],
            },
        ),
        types.Tool(
            name="ue_list_selected_assets",
            description="List assets currently selected in the Content Browser.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_greybox_m1",
            description="Build M1 greybox in current level: floor, walls, player start, pickup placeholder.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_scripts_dir": {
                        "type": "string",
                        "default": str(DEFAULT_SCRIPTS),
                    }
                },
            },
        ),
        types.Tool(
            name="ue_smoke_test",
            description="Run Foo/WebPipeline MCP smoke test inside UE.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_gameplay_m2",
            description="Wire M2 collector loop: pickup + on-screen score HUD (Python PIE tick).",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_gameplay_m3",
            description="Wire M3 loop: collect N pickups before timer expires.",
            inputSchema={
                "type": "object",
                "properties": {
                    "win_score": {"type": "integer", "default": 3},
                    "timer_seconds": {"type": "number", "default": 120},
                },
            },
        ),
        types.Tool(
            name="ue_foo_showcase",
            description=(
                "Build the Foo showcase arena: styled collector level, visible HUD, "
                "lights, camera, animated pickups, and PIE gameplay tick."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_foo_asset_foundation",
            description=(
                "Create Foo's first UE asset scaffold: /Game/Foo folders, "
                "LV_FooArena, BP_FooPickup, BP_FooCharacter, BP_FooGameMode, and WBP_FooHUD."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="ue_list_actors",
            description="List actors in the current editor level, optionally filtered by label prefix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prefix": {
                        "type": "string",
                        "default": "",
                        "description": "Optional actor-label prefix such as SHW_ or GBX_.",
                    }
                },
            },
        ),
        types.Tool(
            name="ue_screenshot",
            description="Request a high-resolution editor/game viewport screenshot.",
            inputSchema={
                "type": "object",
                "properties": {
                    "output_path": {
                        "type": "string",
                        "description": "Optional screenshot path on the UE host; defaults to <UE_WORK_ROOT>/screenshots/.",
                    },
                    "width": {"type": "integer", "default": 1280},
                    "height": {"type": "integer", "default": 720},
                },
            },
        ),
    ]


def execute_structured_tool(
    name: str,
    arguments: dict[str, Any],
    client: Any,
    bridge_url: Optional[str] = None,
) -> ExecResult | dict[str, Any]:
    if name == "ue_ping":
        return _ue_ping(client, bridge_url)
    if name == "ue_run_script_file":
        path = arguments.get("path", "")
        return client.run(path, exec_mode=ExecMode.EXECUTE_FILE, unattended=True)
    if name == "ue_export_glb":
        asset_path = arguments.get("asset_path", "")
        output_path = arguments.get("output_path") or None
        preset = arguments.get("preset", "web-default")
        code = f"""
import web_export
path = web_export.export_to_glb({asset_path!r}, {output_path!r}, preset={preset!r})
print(path)
path
"""
        return client.run(code, exec_mode=ExecMode.EVALUATE_STATEMENT, unattended=True)
    if name == "ue_list_selected_assets":
        code = """
import unreal
util = unreal.GlobalEditorUtilityBase.get_default_object()
assets = util.get_selected_assets()
paths = [a.get_path_name() for a in assets]
print('\\n'.join(paths) if paths else '(none selected)')
paths
"""
        return client.run(code, exec_mode=ExecMode.EVALUATE_STATEMENT, unattended=True)
    if name == "ue_greybox_m1":
        scripts = arguments.get("project_scripts_dir", str(DEFAULT_SCRIPTS))
        script = PurePosixPath(scripts) / "greybox_m1.py"
        return client.run(str(script), exec_mode=ExecMode.EXECUTE_FILE, unattended=True)
    if name == "ue_smoke_test":
        script = DEFAULT_SCRIPTS / "foo_smoke_test.py"
        return client.run(str(script), exec_mode=ExecMode.EXECUTE_FILE, unattended=True)
    if name == "ue_gameplay_m2":
        script = DEFAULT_SCRIPTS / "gameplay_m2.py"
        return client.run(str(script), exec_mode=ExecMode.EXECUTE_FILE, unattended=True)
    if name == "ue_gameplay_m3":
        win_score = int(arguments.get("win_score", 3))
        timer_seconds = float(arguments.get("timer_seconds", 120))
        code = f"""
import foo_gameplay
foo_gameplay.setup_m3(win_score={win_score}, timer_seconds={timer_seconds})
"""
        return client.run(code, exec_mode=ExecMode.EXECUTE_STATEMENT, unattended=True)
    if name == "ue_foo_showcase":
        code = """
import importlib
import foo_showcase
importlib.reload(foo_showcase)
result = foo_showcase.setup_showcase()
print(result)
"""
        return client.run(code, exec_mode=ExecMode.EXECUTE_STATEMENT, unattended=True)
    if name == "ue_foo_asset_foundation":
        code = """
import importlib
import foo_asset_foundation
importlib.reload(foo_asset_foundation)
result = foo_asset_foundation.setup_asset_foundation()
print(result)
"""
        return client.run(code, exec_mode=ExecMode.EXECUTE_STATEMENT, unattended=True)
    if name == "ue_list_actors":
        prefix = str(arguments.get("prefix", ""))
        code = f"""
import unreal
prefix = {prefix!r}
actors = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if not prefix or label.startswith(prefix):
        loc = actor.get_actor_location()
        actors.append({{
            "label": label,
            "class": actor.get_class().get_name(),
            "location": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
        }})
actors = sorted(actors, key=lambda item: item["label"])
for a in actors:
    print(f"{{a['label']}}\\t{{a['class']}}\\t{{a['location']}}")
print(f"COUNT {{len(actors)}}")
"""
        return client.run(code, exec_mode=ExecMode.EXECUTE_STATEMENT, unattended=True)
    if name == "ue_screenshot":
        width = int(arguments.get("width", 1280))
        height = int(arguments.get("height", 720))
        output_path = arguments.get("output_path")
        path = output_path or str(DEFAULT_SCREENSHOTS / "foo-showcase.png")
        code = f"""
import os
import unreal
path = {path!r}
os.makedirs(os.path.dirname(path), exist_ok=True)
ok = unreal.AutomationLibrary.take_high_res_screenshot({width}, {height}, path)
print(path)
print(ok)
"""
        return client.run(code, exec_mode=ExecMode.EXECUTE_STATEMENT, unattended=True)
    raise ValueError(f"Unknown structured tool: {name}")


def _ue_ping(client: Any, bridge_url: Optional[str]) -> dict[str, Any]:
    bridge_ok = False
    ping_body: dict[str, Any] = {}
    url = bridge_url or getattr(client, "bridge_url", "http://127.0.0.1:6800")
    try:
        import httpx

        resp = httpx.get(f"{url.rstrip('/')}/ping", timeout=3.0)
        bridge_ok = resp.status_code == 200
        ping_body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    except Exception as exc:  # noqa: BLE001
        ping_body = {"error": str(exc)}

    engine_version = None
    if bridge_ok:
        result = client.run(
            "import unreal; print(unreal.SystemLibrary.get_engine_version())",
            exec_mode=ExecMode.EXECUTE_STATEMENT,
            unattended=True,
        )
        if result.success:
            for entry in result.output:
                line = (entry.get("output") or "").strip()
                if line and not line.startswith("["):
                    engine_version = line
                    break
            if engine_version is None and result.return_value:
                engine_version = str(result.return_value)

    return {
        "bridge_url": url,
        "bridge_ok": bridge_ok,
        "ping": ping_body,
        "engine_version": engine_version,
    }
