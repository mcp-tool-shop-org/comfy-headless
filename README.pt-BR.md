<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**Tornando o poder do ComfyUI acessível sem a complexidade**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## Por que Comfy Headless?

| Problema | Solução |
| --------- | ---------- |
| A interface de nós do ComfyUI é complexa. | Presets simples e API Python limpa. |
| A criação de prompts é difícil. | Aprimoramento de prompts com inteligência artificial. |
| A geração de vídeos é complexa. | Geração de vídeo em uma única linha, com presets de modelos. |
| Não se sabe quais configurações usar. | As melhores configurações para sua intenção, automaticamente. |

## Início Rápido

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

- **Para Usuários**: Presets simples e aprimoramento de prompts com inteligência artificial.
- **Para Desenvolvedores**: API limpa com compilação de fluxo de trabalho baseada em templates.
- **Para Todos**: As melhores configurações para sua intenção, automaticamente.

## Instalação

### Instalação Modular (v2.5.0+)

Instale apenas o que você precisa:

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

### Recursos Adicionais Disponíveis

| Extra | Dependências | Recursos |
| ------- | -------------- | ---------- |
| `ai` | httpx | Inteligência de prompt Ollama |
| `websocket` | Websockets | Atualizações de progresso em tempo real. |
| `health` | psutil | Monitoramento da saúde do sistema. |
| `ui` | gradio | Interface web. |
| `validation` | pydantic | Validação de configuração. |
| `observability` | opentelemetry | Rastreamento distribuído. |
| `standard` | IA + Websocket | Pacote recomendado |
| `full` | Todos os itens acima. | Tudo. |

### Requisitos

- Python 3.10+
- ComfyUI rodando localmente (padrão: `http://localhost:8188`)
- Opcional: Ollama para aprimoramento de prompts com IA.

## Uso

### Use como uma Biblioteca

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### Com Aprimoramento de IA

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

### Geração de Vídeos

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

### Inicie a Interface Web

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

Ou via linha de comando:
```bash
python -m comfy_headless.ui
```

**Recursos da Interface (v2.5.1):**
- **Geração de Imagens** - txt2img com presets, aprimoramento de prompts com IA.
- **Geração de Vídeos** - Suporte para AnimateDiff, LTX, Hunyuan, Wan.
- **Fila e Histórico** - Gerenciamento de fila em tempo real, histórico de tarefas.
- **Fluxos de Trabalho** - Navegue, importe e crie modelos de fluxo de trabalho.
- **Navegador de Modelos** - Visualize checkpoints, LoRAs, modelos de movimento.
- **Configurações** - Gerenciamento de conexão, timeouts, informações do sistema.

**Tema:** Ocean Mist - toques suaves em tons de verde-água em fundos neutros.

## Modelos de Vídeo (v2.5.0)

### Modelos Suportados

| Model | VRAM | Qualidade | Speed | Ideal para |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | Excelente | Fast | Uso geral, RTX 3080+ |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | Alta qualidade, RTX 4080+ |
| **Wan 2.1/2.2** | 6-16GB | Great | Médio | GPUs de baixo custo, eficiência. |
| **Mochi** | 12GB+ | Excelente | Slow | Adesão ao texto |
| AnimateDiff | 6GB+ | Good | Fast | Pré-visualizações rápidas |
| SVD | 8GB+ | Good | Médio | Imagem para vídeo |
| CogVideoX | 10GB+ | Good | Slow | Suporte legado |

### Presets de Vídeo

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

## Flags de Recursos

Verifique quais recursos estão disponíveis:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## Progresso via Websocket

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

## Referência da API

### Classes Principais

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

### Tratamento de Erros

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

## Arquitetura

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

## Requisitos de Nós do ComfyUI

### Para Geração de Vídeo

Instale estes nós personalizados:

**Núcleo:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - Codificação de vídeo

**Específico para cada modelo:**
- LTX-Video 2: Suporte integrado para ComfyUI (versões recentes)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## Projetos relacionados

Parte de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — conjunto de ferramentas de aprendizado de máquina de código aberto para hardware local.

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - Kit de desenvolvimento para aprendizado de máquina
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - Navegue por todas as ferramentas

## Licença

Licença MIT - veja [LICENSE](LICENSE)

## Contribuições

Contribuições são bem-vindas! Por favor, abra um problema ou solicitação de alteração.

Áreas de interesse:
- Suporte adicional para modelos de vídeo
- Modelos de fluxo de trabalho
- Documentação
- Correção de bugs

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
