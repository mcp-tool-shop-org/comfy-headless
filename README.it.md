<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**Rendere accessibile la potenza di ComfyUI senza la complessità**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## Perché Comfy Headless?

| Problema | Soluzione |
| --------- | ---------- |
| L'interfaccia a nodi di ComfyUI è eccessivamente complessa. | Preset semplici e API Python pulita. |
| La creazione di prompt è difficile. | Miglioramento dei prompt basato sull'intelligenza artificiale. |
| La generazione di video è complessa. | Generazione di video in una sola riga, con preset di modelli. |
| Non si sa quali impostazioni utilizzare. | Impostazioni ottimali per l'obiettivo desiderato, applicate automaticamente. |

## Guida rapida

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## Filosofia

- **Per gli utenti**: Preset semplici e miglioramento dei prompt basato sull'intelligenza artificiale.
- **Per gli sviluppatori**: API pulita con compilazione del flusso di lavoro basata su modelli.
- **Per tutti**: Impostazioni ottimali per l'obiettivo desiderato, applicate automaticamente.

## Installazione

### Installazione modulare (v2.5.0+)

Installare solo ciò di cui si ha bisogno:

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

### Componenti aggiuntivi disponibili

| Extra | Dipendenze | Funzionalità |
| ------- | -------------- | ---------- |
| `ai` | httpx | Intelligenza dei prompt di Ollama |
| `websocket` | WebSockets | Aggiornamenti in tempo reale dello stato di avanzamento |
| `health` | psutil | Monitoraggio dello stato del sistema |
| `ui` | Gradio | Interfaccia web |
| `validation` | Pydantic | Validazione della configurazione |
| `observability` | OpenTelemetry | Tracciamento distribuito |
| `standard` | AI + WebSocket | Pacchetto consigliato |
| `full` | Tutti quelli sopra elencati | Tutto |

### Requisiti

- Python 3.10+
- ComfyUI in esecuzione localmente (predefinito: `http://localhost:8188`)
- Facoltativo: Ollama per il miglioramento dei prompt basato sull'intelligenza artificiale

## Utilizzo

### Utilizzo come libreria

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### Con miglioramento dell'intelligenza artificiale

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

### Generazione di video

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

### Avviare l'interfaccia web

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

Oppure tramite riga di comando:
```bash
python -m comfy_headless.ui
```

**Funzionalità dell'interfaccia utente (v2.5.1):**
- **Generazione di immagini** - txt2img con preset, miglioramento dei prompt basato sull'intelligenza artificiale
- **Generazione di video** - Supporto per AnimateDiff, LTX, Hunyuan, Wan
- **Coda e cronologia** - Gestione della coda in tempo reale, cronologia dei lavori
- **Flussi di lavoro** - Sfoglia, importa e crea modelli di flusso di lavoro
- **Browser dei modelli** - Visualizza checkpoint, LoRA, modelli di movimento
- **Impostazioni** - Gestione delle connessioni, timeout, informazioni sul sistema

**Tema:** Ocean Mist - accenti in verde acqua su sfondi neutri.

## Modelli per video (v2.5.0)

### Modelli supportati

| Model | VRAM | Qualità | Speed | Ideale per |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | Eccellente | Fast | Uso generale, RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | Alta qualità, RTX 4080+ |
| **Wan 2.1/2.2** | 6-16GB | Great | Medio | GPU di fascia bassa, efficienza |
| **Mochi** | 12GB+ | Eccellente | Slow | Adesione al testo |
| AnimateDiff | 6GB+ | Good | Fast | Anteprime rapide |
| SVD | 8GB+ | Good | Medio | Da immagine a video |
| CogVideoX | 10GB+ | Good | Slow | Supporto legacy |

### Preset per video

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

## Flag delle funzionalità

Verificare quali funzionalità sono disponibili:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## Aggiornamenti dello stato tramite WebSocket

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

## Riferimento API

### Classi principali

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

### Gestione degli errori

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

## Architettura

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

## Requisiti dei nodi ComfyUI

### Per la generazione di video

Installare questi nodi personalizzati:

**Componenti principali:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Codifica video

**Specifici per modello:**
- LTX-Video 2: Supporto integrato per ComfyUI (versioni recenti)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## Progetti correlati

Parte di [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — strumenti open-source per l'apprendimento automatico, progettati per hardware locale.

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - Kit di sviluppo per l'apprendimento automatico
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - Esplora tutti gli strumenti

## Licenza

Licenza MIT - vedi [LICENSE](LICENSE)

## Contributi

I contributi sono benvenuti! Si prega di aprire una segnalazione di bug o una richiesta di modifica.

Aree di interesse:
- Supporto aggiuntivo per modelli video
- Modelli di flusso di lavoro
- Documentazione
- Correzioni di bug

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
