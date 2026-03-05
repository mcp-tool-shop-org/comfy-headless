<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**Rendre la puissance de ComfyUI accessible sans la complexité**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## Pourquoi Comfy Headless ?

| Problème | Solution |
| --------- | ---------- |
| L'interface de nœuds de ComfyUI est intimidante. | Préconfigurations simples et API Python claire. |
| La création de prompts est difficile. | Amélioration des prompts grâce à l'IA. |
| La génération de vidéos est complexe. | Génération de vidéos en une seule ligne avec des préconfigurations de modèles. |
| Vous ne savez pas quels paramètres utiliser. | Meilleurs paramètres pour votre objectif, automatiquement. |

## Démarrage rapide

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## Philosophie

- **Pour les utilisateurs :** Préconfigurations simples et amélioration des prompts grâce à l'IA.
- **Pour les développeurs :** API claire avec compilation de flux de travail basée sur des modèles.
- **Pour tout le monde :** Meilleurs paramètres pour votre objectif, automatiquement.

## Installation

### Installation modulaire (v2.5.0+)

Installez uniquement ce dont vous avez besoin :

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

### Fonctionnalités supplémentaires disponibles

| Extra | Dépendances | Fonctionnalités |
| ------- | -------------- | ---------- |
| `ai` | httpx | Intelligence des prompts Ollama |
| `websocket` | Websockets | Mises à jour de progression en temps réel |
| `health` | psutil | Surveillance de l'état du système |
| `ui` | gradio | Interface web |
| `validation` | pydantic | Validation de la configuration |
| `observability` | opentelemetry | Traçage distribué |
| `standard` | IA + Websocket | Bundle recommandé |
| `full` | Tout ce qui précède | Tout |

### Prérequis

- Python 3.10+
- ComfyUI en cours d'exécution localement (par défaut : `http://localhost:8188`)
- Facultatif : Ollama pour l'amélioration des prompts par l'IA

## Utilisation

### Utilisation en tant que bibliothèque

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### Avec amélioration par l'IA

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

### Génération de vidéos

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

### Lancer l'interface web

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

Ou via la ligne de commande :
```bash
python -m comfy_headless.ui
```

**Fonctionnalités de l'interface utilisateur (v2.5.1) :**
- **Génération d'images** - txt2img avec des préconfigurations, amélioration des prompts par l'IA
- **Génération de vidéos** - Prise en charge de AnimateDiff, LTX, Hunyuan, Wan
- **File d'attente et historique** - Gestion de la file d'attente en temps réel, historique des tâches
- **Flux de travail** - Parcourir, importer et créer des modèles de flux de travail
- **Explorateur de modèles** - Afficher les checkpoints, les LoRAs, les modèles de mouvement
- **Paramètres** - Gestion des connexions, délais d'attente, informations système

**Thème :** Brume océanique - accents bleu sarcé sur des fonds neutres chauds

## Modèles vidéo (v2.5.0)

### Modèles pris en charge

| Model | VRAM | Qualité | Speed | Idéal pour |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | Excellent | Fast | Utilisation générale, RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | Haute qualité, RTX 4080+ |
| **Wan 2.1/2.2** | 6-16 Go | Great | Moyen | GPU économiques, efficacité |
| **Mochi** | 12GB+ | Excellent | Slow | Adhérence au texte |
| AnimateDiff | 6GB+ | Good | Fast | Aperçus rapides |
| SVD | 8GB+ | Good | Moyen | Image vers vidéo |
| CogVideoX | 10GB+ | Good | Slow | Prise en charge héritée |

### Préconfigurations vidéo

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

## Fonctionnalités

Vérifiez les fonctionnalités disponibles :

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## Mise à jour de progression via WebSocket

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

## Référence de l'API

### Classes principales

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

### Gestion des erreurs

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

## Architecture

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

## Exigences des nœuds ComfyUI

### Pour la génération de vidéos

Installez ces nœuds personnalisés :

**Fonctionnalités de base :**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Encodage vidéo

**Spécifique à certains modèles :**
- LTX-Video 2 : Prise en charge intégrée de ComfyUI (versions récentes)
- Hunyuan 1.5 : [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan : [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff : [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## Projets connexes

Fait partie de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — outils d'apprentissage automatique open source pour matériel local.

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - Kit de développement pour l'apprentissage automatique
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - Parcourir tous les outils

## Licence

Licence MIT - voir [LICENSE](LICENSE)

## Contributions

Les contributions sont les bienvenues ! Veuillez ouvrir un problème ou une demande de tirage.

Domaines d'intérêt :
- Prise en charge de modèles vidéo supplémentaires
- Modèles de flux de travail
- Documentation
- Corrections de bugs

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
