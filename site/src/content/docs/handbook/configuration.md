---
title: Configuration
description: Environment variables, optional feature extras, timeouts, retry and circuit-breaker behaviour, logging, and how to inspect resolved settings.
sidebar:
  order: 5
---

Configuration comes from three places, in increasing order of precedence:

1. Built-in defaults
2. Environment variables
3. Arguments you pass directly (`ComfyClient("http://…")`, `preset=…`, and so on)

## Environment variables

Every setting is reachable as an environment variable using the `COMFY_HEADLESS_` prefix
and a **double underscore** between the section and the key:

```
COMFY_HEADLESS_<SECTION>__<KEY>
```

```bash
export COMFY_HEADLESS_COMFYUI__URL=http://192.168.1.50:8188
export COMFY_HEADLESS_LOGGING__LEVEL=DEBUG
export COMFY_HEADLESS_UI__PORT=8080
```

The `__` is not decorative — a single underscore will not work, because section names
themselves contain underscores.

### `comfyui`

| Key | Default | Meaning |
|-----|---------|---------|
| `url` | `http://localhost:8188` | ComfyUI server |
| `timeout_connect` | `5.0` | Connection timeout, seconds |
| `timeout_read` | `30.0` | Read timeout |
| `timeout_queue` | `10.0` | Queue submission timeout |
| `timeout_image` | `60.0` | Image fetch / upload timeout |
| `timeout_video` | `120.0` | Video fetch timeout |

### `generation`

| Key | Default |
|-----|---------|
| `default_width` / `default_height` | `1024` |
| `default_steps` | `25` |
| `default_cfg` | `7.0` |
| `max_width` / `max_height` | `2048` |
| `max_steps` | `100` |
| `generation_timeout` | `300.0` |
| `video_timeout` | `600.0` |

The `max_*` values are guard rails — requests beyond them are rejected before they reach
ComfyUI, which is cheaper than a server-side failure.

### `ollama`

Only used when the `[ai]` extra is installed.

| Key | Default |
|-----|---------|
| `url` | `http://localhost:11434` |
| `model` | `qwen2.5:7b` |
| `timeout_analysis` | `15.0` |
| `timeout_enhancement` | `30.0` |
| `timeout_connect` | `2.0` |
| `few_shot_examples_path` | `None` |

### `retry`

| Key | Default | Meaning |
|-----|---------|---------|
| `max_retries` | `3` | Attempts before giving up |
| `backoff_base` | `1.5` | Exponential base |
| `backoff_max` | `30.0` | Backoff ceiling, seconds |
| `backoff_jitter` | `True` | Randomise to avoid thundering herds |
| `circuit_breaker_threshold` | `5` | Failures before the circuit opens |
| `circuit_breaker_reset` | `60.0` | Seconds before a half-open retry |

When the circuit opens, calls fail fast with `CircuitOpenError` instead of piling onto a
server that is already struggling.

### `http`

Connection pooling: `max_connections` (100), `max_keepalive_connections` (20),
`keepalive_expiry` (5.0), `http2` (True), plus `connect_timeout`, `read_timeout`,
`write_timeout` and `pool_timeout`.

### `logging`

| Key | Default |
|-----|---------|
| `level` | `INFO` |
| `format` | `%(asctime)s \| %(levelname)-8s \| %(name)s \| %(message)s` |
| `file` | `None` (stderr) |
| `json_output` | `False` |
| `otel_enabled` | `False` |
| `otel_service_name` | `comfy-headless` |
| `otel_endpoint` | `None` |

Set `json_output=True` for structured logs when shipping to a collector. OpenTelemetry
export requires the `[observability]` extra.

### `ui`

| Key | Default |
|-----|---------|
| `port` | `7861` |
| `host` | `127.0.0.1` |
| `share` | `False` |
| `auto_open` | `True` |
| `temp_cleanup_interval` | `3600` |

## Inspecting resolved settings

```python
from comfy_headless import get_settings

s = get_settings()
print(s.comfyui.url)
print(s.retry.max_retries)
print(s.version)
```

From the shell, `--diagnose` prints the resolved configuration alongside feature
availability — the fastest way to confirm an environment variable actually took effect:

```bash
comfy-headless --diagnose
```

If you change environment variables inside a running process:

```python
from comfy_headless import reload_settings
reload_settings()
```

## Optional features

The core install is deliberately small. Everything else is an extra:

| Extra | Enables |
|-------|---------|
| `ai` | `enhance_prompt`, `analyze_prompt`, `quick_enhance` (needs Ollama) |
| `websocket` | `ComfyWSClient` real-time progress |
| `ui` | `launch()` and the `comfy-headless` web interface |
| `health` | `check_health`, `HealthMonitor`, system metrics |
| `validation` | Pydantic-backed config validation |
| `observability` | OpenTelemetry tracing |
| `standard` | `ai` + `websocket` |
| `full` | Everything above |

Check at runtime rather than guessing:

```python
from comfy_headless import FEATURES, check_feature, list_missing_features

print(FEATURES)                  # {'ai': True, 'websocket': True, 'health': False, ...}
print(check_feature("ai"))       # True / False
print(list_missing_features())   # {'health': 'pip install comfy-headless[health]', ...}
```

```bash
comfy-headless --check
```

Importing a feature you have not installed raises `FeatureNotAvailable`, whose hint is the
exact `pip install` line you need.

## Timeouts in practice

Two levels exist and they answer different questions.

**Transport timeouts** (`comfyui.timeout_*`) bound a single HTTP call. Raise
`timeout_read` if your server is slow to respond, not if generation is slow.

**Generation timeouts** (`generation.generation_timeout`, `video_timeout`) bound the whole
job while polling. This is the one to raise for a long video:

```python
client.generate_video("a long clip", preset="mochi", timeout=1800)
```

A cold model load can take minutes on the first call. If the first generation times out
and the second succeeds, the timeout was too tight for a load, not for the render.

## Logging

```python
from comfy_headless import set_log_level, get_logger

set_log_level("DEBUG")
log = get_logger(__name__)
```

Secrets are masked automatically via `SecretValue`, and URLs are redacted with
`mask_url_credentials` before they reach a log line — credentials embedded in a ComfyUI
URL will not appear in output.
