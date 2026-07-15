# SD + TTS MCP Server

A Model Context Protocol (MCP) server exposing **Stable Diffusion** (txt2img) and **GPT-SoVITS** (TTS) as standard MCP tools, for use with any MCP-compatible client (Codex, Claude Desktop, etc.).

---

## Quick Start

```bash
# 1. Install
git clone https://github.com/yyboling-commits/mcp-sd-tts-server.git
cd mcp-sd-tts-server
pip install mcp requests pyyaml

# 2. Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your service URLs

# 3. Run
python src/server.py
```

---

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit:

```yaml
sd:
  url: "http://127.0.0.1:7860"    # SD WebUI 地址
  default_model: ""                # 默认模型名（可选）

tts:
  url: "http://127.0.0.1:9880"    # GPT-SoVITS 地址
  default_voice: ""                # 默认音色（可选）

server:
  name: "sd-tts-mcp"
  transport: "stdio"               # stdio | sse
```

### 前置条件

- **Stable Diffusion WebUI** 需启动并开启 `--api` 参数
- **GPT-SoVITS TTS** 需启动 API 服务（默认端口 9880）

---

## Transport 模式

### stdio 模式（默认，推荐）

```bash
python src/server.py
```

标准输入输出模式，适用于 MCP 客户端直接启动子进程调用。

### SSE 模式（HTTP）

```bash
python src/server.py --transport sse
```

HTTP 服务模式，监听 `0.0.0.0:8000`。SSE 端点 `/sse`，消息端点 `/messages`。

---

## 注册到客户端

### Codex / Claude Desktop

在 MCP 配置中添加：

```json
{
  "mcpServers": {
    "sd-tts": {
      "command": "python",
      "args": ["路径/src/server.py"],
      "env": {}
    }
  }
}
```

### 其他 MCP 客户端

任意支持 stdio transport 的 MCP 客户端均可使用，配置方式同上。

---

## 可用工具

### txt2img — 文生图

调用 SD WebUI API 生成图片。

参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | string | - | **必填**。正向提示词 |
| `negative_prompt` | string | "" | 反向提示词 |
| `width` | int | 896 | 图片宽度 |
| `height` | int | 1344 | 图片高度 |
| `steps` | int | 20 | 采样步数 |
| `cfg_scale` | float | 5.0 | CFG 引导尺度 |
| `sampler_name` | string | "Euler" | 采样器 |
| `seed` | int | -1 | 随机种子（-1=随机） |
| `model_name` | string | "" | 模型名（留空用默认） |

返回：PNG 图片 + 种子信息 JSON。

### tts — 文本转语音

调用 GPT-SoVITS API 生成语音。

参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | string | - | **必填**。要合成的文本 |
| `speed` | float | 0.85 | 语速 |
| `temperature` | float | 1.0 | 生成温度 |

返回：WAV 音频。

### sd_health — SD 健康检查

检查 SD WebUI 是否正常运行。无参数。

返回：`{"ok": true/false}`

### tts_health — TTS 健康检查

检查 TTS 服务是否正常运行。无参数。

返回：`{"ok": true/false}`

### list_sd_models — 列出可用模型

查询 SD WebUI 中加载的所有 checkpoint 模型。无参数。

返回：`{"models": ["model1", "model2", ...]}`

---

## 项目结构

```
mcp-sd-tts-server/
├── src/
│   ├── server.py        # MCP 服务入口
│   ├── sd_client.py     # SD WebUI API 封装
│   └── tts_client.py    # GPT-SoVITS API 封装
├── config.example.yaml  # 配置示例
├── pyproject.toml       # 项目元数据
├── README.md
└── .gitignore
```

---

## 依赖

- Python >= 3.11
- `mcp` — Model Context Protocol SDK
- `requests` — HTTP 客户端
- `pyyaml` — YAML 配置解析

---
