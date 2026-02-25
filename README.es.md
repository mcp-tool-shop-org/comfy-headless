<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**Haciendo que el poder de ComfyUI sea accesible sin la complejidad.**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## ¿Por qué Comfy Headless?

| Problema | Solución |
| --------- | ---------- |
| La interfaz de nodos de ComfyUI es abrumadora. | Preajustes sencillos y una API de Python limpia. |
| La ingeniería de prompts es difícil. | Mejora de prompts impulsada por IA. |
| La generación de video es compleja. | Generación de video en una sola línea con preajustes de modelos. |
| No se sabe qué configuraciones usar. | Las mejores configuraciones para su intención, automáticamente. |

## Comienzo rápido

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## Filosofía

- **Para usuarios:** Preajustes sencillos y mejora de prompts impulsada por IA.
- **Para desarrolladores:** API limpia con compilación de flujo de trabajo basada en plantillas.
- **Para todos:** Las mejores configuraciones para su intención, automáticamente.

## Instalación

### Instalación modular (v2.5.0+)

Instale solo lo que necesita:

```bash
# Core only (minimal - ~2MB)
pip install comfy-headless

# With AI prompt enhancement (Ollama)
pip install comfy-headless[ai]

# With WebSocket real-time progress
pip install comfy-headless[websocket]

# Recommended for most users
pip install comfy-headless[standard]

# Everything (UI, health monitoring, observability)
pip install comfy-headless[full]
```

### Complementos disponibles

| Extra | Dependencias | Características |
| ------- | -------------- | ---------- |
| `ai` | httpx | Inteligencia de prompts de Ollama. |
| `websocket` | Websockets. | Actualizaciones de progreso en tiempo real. |
| `health` | psutil. | Monitoreo de la salud del sistema. |
| `ui` | gradio. | Interfaz web. |
| `validation` | pydantic. | Validación de configuración. |
| `observability` | opentelemetry. | Trazabilidad distribuida. |
| `standard` | IA + websocket. | Paquete recomendado. |
| `full` | Todo lo anterior. | Todo. |

### Requisitos

- Python 3.10+.
- ComfyUI ejecutándose localmente (por defecto: `http://localhost:8188`).
- Opcional: Ollama para la mejora de prompts de IA.

## Uso

### Usar como una biblioteca

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### Con mejora de IA

```python
from comfy_headless import analyze_prompt, enhance_prompt

# Analyze a prompt
analysis = analyze_prompt("a cyberpunk city at night with neon lights")
print(f"Intent: {analysis.intent}")        # "scene"
print(f"Styles: {analysis.styles}")        # ["scifi", "cinematic"]
print(f"Preset: {analysis.suggested_preset}")  # "cinematic"

# Enhance a prompt
enhanced = enhance_prompt("a cat", style="detailed")
print(enhanced.enhanced)   # "a cat, masterpiece, best quality, highly detailed..."
print(enhanced.negative)   # Style-aware negative prompt
```

### Generación de video

```python
from comfy_headless import ComfyClient, list_video_presets

# See available presets
print(list_video_presets())

# Generate video with preset
client = ComfyClient()
result = client.generate_video(
    prompt="a cat walking through a garden",
    preset="ltx_quality"  # LTX-Video 2, 1280x720, 49 frames
)
```

### Iniciar la interfaz web

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

O a través de la línea de comandos:
```bash
python -m comfy_headless.ui
```

**Características de la interfaz (v2.5.1):**
- **Generación de imágenes:** txt2img con preajustes, mejora de prompts de IA.
- **Generación de video:** Soporte para AnimateDiff, LTX, Hunyuan, Wan.
- **Cola y historial:** Gestión de cola en tiempo real, historial de trabajos.
- **Flujos de trabajo:** Explorar, importar y crear plantillas de flujo de trabajo.
- **Explorador de modelos:** Ver puntos de control, LoRAs, modelos de movimiento.
- **Configuración:** Gestión de conexiones, tiempos de espera, información del sistema.

**Tema:** Ocean Mist: detalles suaves en tonos turquesa sobre fondos neutros cálidos.

## Modelos de video (v2.5.0)

### Modelos soportados

| Model | VRAM | Calidad | Speed | Ideal para |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | Excelente | Fast | Uso general, RTX 3080+. |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | Alta calidad, RTX 4080+. |
| **Wan 2.1/2.2** | 6-16 GB. | Great | Medio | GPUs de bajo presupuesto, eficiencia. |
| **Mochi** | 12GB+ | Excelente | Slow | Adherencia al texto. |
| AnimateDiff. | 6GB+ | Good | Fast | Previsualizaciones rápidas. |
| SVD | 8GB+ | Good | Medio | Imagen a video. |
| CogVideoX. | 10GB+ | Good | Slow | Soporte heredado. |

### Preajustes de video

```python
from comfy_headless import VIDEO_PRESETS, get_recommended_preset

# Get preset recommendation based on your VRAM
preset = get_recommended_preset(vram_gb=16)  # Returns "hunyuan15_720p"

# LTX-Video 2 (Fast, great quality)
# "ltx_quick": 768x512, 25 frames, 20 steps
# "ltx_standard": 1280x720, 49 frames, 25 steps
# "ltx_quality": 1280x720, 97 frames, 30 steps

# Hunyuan 1.5 (Best quality)
# "hunyuan15_720p": 1280x720, 121 frames
# "hunyuan15_1080p": 1920x1080 with super-resolution

# Wan (Efficient)
# "wan_1.3b": 720x480, 49 frames (6GB VRAM)
# "wan_14b": 1280x720, 81 frames (12GB VRAM)
```

## Marcadores de características

Verifique qué características están disponibles:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## Progreso de WebSocket

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

## Referencia de la API

### Clases principales

```python
from comfy_headless import (
    # Client
    ComfyClient,           # Main HTTP client
    ComfyWSClient,         # WebSocket client (requires [websocket])

    # Video
    VideoSettings,         # Video generation settings
    VideoModel,            # Model enum (LTXV, HUNYUAN_15, WAN, etc.)
    VIDEO_PRESETS,         # Preset configurations
    get_recommended_preset, # VRAM-based recommendation

    # Workflows
    compile_workflow,      # Compile workflow from preset
    WorkflowCompiler,      # Low-level compiler

    # Intelligence (requires [ai])
    analyze_prompt,        # Analyze prompt intent/style
    enhance_prompt,        # AI-powered enhancement
    PromptAnalysis,        # Analysis result type
)
```

### Manejo de errores

```python
from comfy_headless import (
    ComfyHeadlessError,      # Base exception
    ComfyUIConnectionError,  # Can't reach ComfyUI
    ComfyUIOfflineError,     # ComfyUI not responding
    GenerationTimeoutError,  # Generation took too long
    GenerationFailedError,   # Generation failed
    ValidationError,         # Invalid parameters
)

try:
    result = client.generate_image("test")
except ComfyUIOfflineError:
    print("Start ComfyUI first!")
except GenerationTimeoutError:
    print("Generation timed out")
```

## Arquitectura

```
comfy_headless/
├── __init__.py          # Package exports, lazy loading
├── feature_flags.py     # Optional dependency detection
├── client.py            # ComfyUI HTTP client
├── websocket_client.py  # WebSocket client
├── intelligence.py      # AI prompt analysis (requires [ai])
├── workflows.py         # Template compiler & presets
├── video.py             # Video models & presets
├── ui.py                # Gradio 6.0 interface (requires [ui])
├── theme.py             # Ocean Mist theme
├── config.py            # Settings management
├── exceptions.py        # Error types
├── retry.py             # Circuit breaker, rate limiting
├── health.py            # Health checks (requires [health])
└── tests/               # Test suite
```

## Requisitos de nodos de ComfyUI

### Para la generación de video

Instale estos nodos personalizados:

**Núcleo:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Codificación de video

**Específico del modelo:**
- LTX-Video 2: Soporte integrado para ComfyUI (versiones recientes)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## Proyectos relacionados

Parte de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — herramientas de aprendizaje automático de código abierto para hardware local.

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - Kit de herramientas de desarrollo de aprendizaje automático
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - Explore todas las herramientas

## Licencia

Licencia MIT - ver [LICENSE](LICENSE)

## Contribuciones

¡Las contribuciones son bienvenidas! Por favor, abra un problema o una solicitud de extracción.

Áreas de interés:
- Soporte adicional para modelos de video
- Plantillas de flujo de trabajo
- Documentación
- Corrección de errores

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
