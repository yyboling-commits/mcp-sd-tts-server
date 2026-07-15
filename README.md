# SD + TTS MCP Server

A Model Context Protocol (MCP) server that exposes **Stable Diffusion** (txt2img) and **GPT-SoVITS** (TTS) as MCP tools — making them accessible from any MCP-compatible client (Codex, Claude Desktop, etc.).

## Features

### Tools

| Tool | Description |
|------|-------------|
| `txt2img` | Generate images from text prompts via SD WebUI API |
| `tts` | Synthesize speech from text via GPT-SoVITS API |
| `sd_health` | Check if SD WebUI is running |
| `tts_health` | Check if TTS server is running |
| `list_sd_models` | List available SD checkpoint models |

### Transport

- **stdio** (default) — for MCP client integration (Codex, Claude Desktop)
- **sse** — HTTP server mode (useful for remote access)

## Prerequisites

- Python 3.11+
- [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) running with `--api` flag
- [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) TTS server running

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/mcp-sd-tts-server.git
cd mcp-sd-tts-server

# Install dependencies
pip install -e .
```

## Configuration

Copy the example config and fill in your local service URLs:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
sd:
  url: "http://127.0.0.1:7860"    # Your SD WebUI URL
  default_model: "your_model"      # Optional default model

tts:
  url: "http://127.0.0.1:9880"    # Your GPT-SoVITS URL
  default_voice: "your_voice"      # Optional default voice
```

## Usage

### stdio mode (for Codex / Claude Desktop)

```bash
python src/server.py
```

### SSE mode (HTTP)

```bash
python src/server.py --transport sse
```

### Register with Codex

In your Codex config, register the server:

```json
{
  "mcpServers": {
    "sd-tts": {
      "command": "python",
      "args": ["path/to/src/server.py"],
      "env": {}
    }
  }
}
```

## API Reference

### txt2img

```json
{
  "prompt": "your positive prompt",
  "negative_prompt": "negative prompt (optional)",
  "width": 896,
  "height": 1344,
  "steps": 20,
  "cfg_scale": 5.0,
  "sampler_name": "Euler",
  "seed": -1,
  "model_name": "optional model override"
}
```

### tts

```json
{
  "text": "text to speak",
  "speed": 0.85,
  "temperature": 1.0
}
```

## Project Structure

```
mcp-sd-tts-server/
├── src/
│   ├── server.py        # MCP server entry point
│   ├── sd_client.py     # SD WebUI API wrapper
│   └── tts_client.py    # GPT-SoVITS API wrapper
├── config.example.yaml  # Sample configuration
├── pyproject.toml       # Python project metadata
└── .gitignore
```

## License

MIT
