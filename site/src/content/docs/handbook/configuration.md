---
title: Configuration
description: Feature flags, WebSocket progress tracking, and runtime configuration options for Comfy Headless.
sidebar:
  order: 4
---

This page covers how to check which features are available, configure WebSocket progress tracking, and customize runtime behavior.

## Feature flags

Comfy Headless detects which optional extras are installed and exposes this through the `FEATURES` dictionary. This lets you write code that adapts gracefully to whatever is available.

```python
from comfy_headless import FEATURES, list_missing_features

# Check what's available
print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, 'ui': False, ...}

# See what's missing and how to install it
print(list_missing_features())
# {'health': 'pip install comfy-headless[health]',
#  'ui': 'pip install comfy-headless[ui]', ...}
```

### Using feature flags in your code

```python
from comfy_headless import FEATURES

if FEATURES['ai']:
    from comfy_headless import enhance_prompt
    enhanced = enhance_prompt("a forest scene")
    prompt = enhanced.enhanced
else:
    prompt = "a forest scene, high quality, detailed"
```

This pattern ensures your application works with any combination of installed extras and degrades gracefully when optional features are absent.

## WebSocket progress

When the `[websocket]` extra is installed, you can monitor generation progress in real time using the `ComfyWSClient`. This is especially useful for video generation, which can take minutes to complete.

```python
import asyncio
from comfy_headless import ComfyWSClient

async def generate_with_progress():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        result = await ws.wait_for_completion(
            prompt_id,
            on_progress=lambda p: print(f"Progress: {p.progress}%")
        )
        return result

asyncio.run(generate_with_progress())
```

### How WebSocket progress works

1. `ComfyWSClient` opens a persistent WebSocket connection to ComfyUI.
2. When you queue a prompt, it returns a `prompt_id` for tracking.
3. `wait_for_completion` listens for progress messages on the WebSocket and invokes your callback with each update.
4. The `on_progress` callback receives a progress object with a `progress` field (0-100 percentage).
5. When generation finishes, the method returns the result.

### When to use WebSocket vs HTTP

| Scenario | Recommended client |
|----------|-------------------|
| Single image, no progress needed | `ComfyClient` (HTTP) |
| Image with progress bar | `ComfyWSClient` |
| Video generation (long-running) | `ComfyWSClient` |
| Batch processing | `ComfyClient` (HTTP) with polling |
| Production pipeline with monitoring | `ComfyWSClient` + `[observability]` |

The HTTP client (`ComfyClient`) polls for results. The WebSocket client (`ComfyWSClient`) receives push notifications. For anything that takes more than a few seconds, WebSocket gives a much better user experience.

## Connection settings

By default, Comfy Headless connects to `http://localhost:8188`. You can customize this when creating a client:

```python
from comfy_headless import ComfyClient

# Connect to a remote ComfyUI instance
client = ComfyClient(host="192.168.1.100", port=8188)

# Connect with a custom timeout
client = ComfyClient(timeout=300)  # 5-minute timeout
```

## Health monitoring

When the `[health]` extra is installed, Comfy Headless includes system health monitoring and circuit-breaker retry logic. If ComfyUI becomes unresponsive, the circuit breaker prevents your application from hammering it with requests. Once ComfyUI recovers, the circuit breaker automatically resets.

## Observability

The `[observability]` extra adds OpenTelemetry distributed tracing. This is primarily useful in production deployments where you need to trace generation requests through multiple services.

## Next steps

- See the full class and function reference in [API Reference](../api-reference/).
- Understand the project structure and module responsibilities in [Architecture](../architecture/).
