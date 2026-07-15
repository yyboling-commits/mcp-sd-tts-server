"""MCP Server: Stable Diffusion txt2img + GPT-SoVITS TTS

Usage:
  pip install mcp requests pyyaml
  python src/server.py          # stdio mode (for Codex)
  python src/server.py --sse    # SSE mode (HTTP)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from sd_client import SDClient
from tts_client import TTSClient


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config() -> dict[str, Any]:
    """Load config.yaml. Falls back to config.example.yaml if not found."""
    search_paths = [
        Path("config.yaml"),
        Path(__file__).parent.parent / "config.yaml",
        Path(__file__).parent.parent / "config.example.yaml",
    ]
    for path in search_paths:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


config = load_config()
sd_cfg = config.get("sd", {})
tts_cfg = config.get("tts", {})

sd_client = SDClient(base_url=sd_cfg.get("url", "http://127.0.0.1:7860"))
tts_client = TTSClient(base_url=tts_cfg.get("url", "http://127.0.0.1:9880"))

server = Server("sd-tts-mcp")


# ---------------------------------------------------------------------------
# Tool: txt2img
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="txt2img",
            description="Generate an image from a text prompt using Stable Diffusion",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Positive prompt"},
                    "negative_prompt": {
                        "type": "string",
                        "description": "Negative prompt",
                        "default": "",
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width",
                        "default": 896,
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height",
                        "default": 1344,
                    },
                    "steps": {
                        "type": "integer",
                        "description": "Sampling steps",
                        "default": 20,
                    },
                    "cfg_scale": {
                        "type": "number",
                        "description": "CFG scale",
                        "default": 5.0,
                    },
                    "sampler_name": {
                        "type": "string",
                        "description": "Sampler",
                        "default": "Euler",
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed (-1 for random)",
                        "default": -1,
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Model checkpoint name (optional)",
                        "default": "",
                    },
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="tts",
            description="Synthesize speech from text using GPT-SoVITS",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to speak",
                    },
                    "speed": {
                        "type": "number",
                        "description": "Speaking speed",
                        "default": 0.85,
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Generation temperature",
                        "default": 1.0,
                    },
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="sd_health",
            description="Check if SD WebUI is running",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="tts_health",
            description="Check if TTS server is running",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="list_sd_models",
            description="List available SD models",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "txt2img":
        model = arguments.get("model_name") or sd_cfg.get("default_model") or None
        img_bytes, seed = sd_client.txt2img(
            prompt=arguments["prompt"],
            negative_prompt=arguments.get("negative_prompt", ""),
            width=arguments.get("width", 896),
            height=arguments.get("height", 1344),
            steps=arguments.get("steps", 20),
            cfg_scale=arguments.get("cfg_scale", 5.0),
            sampler_name=arguments.get("sampler_name", "Euler"),
            seed=arguments.get("seed", -1),
            model_name=model,
        )
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"seed": seed, "size": len(img_bytes)}),
            ),
            types.ImageContent(
                type="image",
                data=img_bytes.hex(),
                mimeType="image/png",
            ),
        ]

    elif name == "tts":
        audio_bytes = tts_client.synthesize(
            text=arguments["text"],
            speed=arguments.get("speed", 0.85),
            temperature=arguments.get("temperature", 1.0),
        )
        return [
            types.ImageContent(
                type="image",
                data=audio_bytes.hex(),
                mimeType="audio/wav",
            ),
        ]

    elif name == "sd_health":
        ok = sd_client.health_check()
        return [types.TextContent(type="text", text=json.dumps({"ok": ok}))]

    elif name == "tts_health":
        ok = tts_client.health_check()
        return [types.TextContent(type="text", text=json.dumps({"ok": ok}))]

    elif name == "list_sd_models":
        models = sd_client.get_models() if sd_client.health_check() else []
        return [types.TextContent(type="text", text=json.dumps({"models": models}))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="SD + TTS MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=config.get("server", {}).get("transport", "stdio"),
    )
    args = parser.parse_args()

    if args.transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        import uvicorn

        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options()
                )

        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages", app=sse.handle_post_message),
            ]
        )
        print("Starting SSE server on http://0.0.0.0:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
