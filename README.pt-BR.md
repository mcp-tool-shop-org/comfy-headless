<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Controle o ComfyUI com Python. Sem necessidade de diagramas complexos.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## O que é isso

comfy-headless cria **gráficos no formato da API ComfyUI** e os executa. Você chama uma função Python; ela emite o gráfico de nós JSON, envia para o ComfyUI, verifica se a operação foi concluída e fornece os caminhos de saída.

Essa estrutura é importante porque indica o que pode dar errado. A tarefa principal da biblioteca é emitir nomes de nós e chaves de entrada que o ComfyUI de destino realmente possui. Quando o ComfyUI renomeia ou remove um nó, um gráfico que referencia o nome antigo é rejeitado no envio com um erro obscuro — e nada avisa você antes.

**A versão 3.0 foi a primeira a levar isso a sério.** Cada tipo de nó que esta biblioteca emite foi auditado em relação ao catálogo ativo do ComfyUI. Nove não existiam mais. Eles foram removidos, os gráficos que os usavam são reconstruídos com nós verificados e a biblioteca agora pode informar o que falta em um servidor *antes* que você execute uma tarefa nele.

| Problema | O que comfy-headless faz |
|---------|--------------------------|
| A interface do nó é extensa | Predefinições e uma API Python limpa |
| A engenharia de prompts é difícil | Aprimoramento opcional por meio da IA local Ollama |
| A geração de vídeo é complexa | 24 predefinições em 9 famílias de modelos |
| "Quais configurações devo usar?" | Recomendações dimensionadas para sua VRAM |
| Os gráficos falham com erros enigmáticos | A verificação de dependências identifica o nó *e* o pacote |

## Guia rápido

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` retorna um `dict` com `success`, `prompt_id`, `images`, `error`, `seed` e `preset`. Cada chamada de geração nesta biblioteca retorna um dicionário — não há objeto de resultado para extrair.

## Instalação

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| Extras | Adiciona |
|-------|------|
| `ai` | Análise e aprimoramento de prompts por meio da IA local Ollama |
| `websocket` | Progresso em tempo real via WebSocket |
| `ui` | Interface web Gradio |
| `health` | Monitoramento do estado do sistema |
| `validation` | Validação de configuração Pydantic |
| `observability` | Rastreamento OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Todos os itens acima |

Requer **Python 3.10+** e uma instância do ComfyUI em execução.

Verifique o que está ativo durante a execução:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## Imagens

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

Oito predefinições de imagem: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic` e `square`.

Execute em lote uma lista de prompts:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Aprimoramento de prompt por IA

Requer o extra `[ai]` e um Ollama local. Estas são **funções no nível do módulo**, não métodos de cliente:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## Vídeo

```python
from comfy_headless import list_video_presets, get_recommended_preset

print(list_video_presets())                  # 24 presets
print(get_recommended_preset(vram_gb=16))    # picks one that fits

result = client.generate_video(
    "a slow pan across a mountain range",
    preset="ltx_quality",
)
print(result["videos"])
```

A seleção é feita **por predefinição**, não por modelo — `generate_video` não tem o argumento `model`. Qualquer um dos itens `frames`, `fps`, `steps`, `cfg`, `width` ou `height` pode ser passado para substituir a predefinição.

### Entrada de imagem

A conversão de imagem em vídeo e qualquer outra operação que utilize uma imagem de origem exige que essa imagem exista primeiro no ComfyUI. Carregue-a e, em seguida, passe o nome que o servidor retorna:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Leia `name` da resposta, em vez de reutilizar o nome do arquivo que você enviou — o ComfyUI renomeia os arquivos em caso de conflito, portanto, os dois nem sempre são iguais. `ref` é o mesmo valor já combinado com qualquer subpasta, que é exatamente o que o gráfico precisa.

> **Alterado na versão 3.0:** `init_image` é um nome de arquivo do lado do servidor. Versões anteriores aceitavam dados base64 e os transmitiam por meio de um nó de terceiros que não existe em uma instalação padrão do ComfyUI. Consulte o [CHANGELOG](CHANGELOG.md).

### Famílias de modelos

| Família | VRAM mínima | Qualidade | Velocidade | Nós extras | Melhor para |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Ótimo | Médio | — | Baixa VRAM, eficiência |
| AnimateDiff Lightning | 6 GB | Razoável | Mais rápido | AnimateDiff-Evolved | Rascunhos de 4 etapas |
| AnimateDiff | 8 GB | Bom | Rápido | AnimateDiff-Evolved, Interpolação de quadros. | Visualizações rápidas |
| **LTX-Video** | 12 GB | Excelente | Rápido | — | O padrão seguro |
| **Mochi** | 12 GB | Excelente | Lento | — | Adesão ao texto, clipes longos |
| **SVD** | 12 GB | Bom | Médio | — | Animando uma imagem estática |
| **Hunyuan 1.5** | 14 GB | Melhor | Lento | — | Maior qualidade |
| CogVideoX | 16 GB | Bom | Lento | Wrapper CogVideoX | Legado |
| **Hunyuan 1.0** | 24 GB | Ótimo | Lento | Interpolação de quadros | Substituído pela versão 1.5 |

Seis das nove famílias funcionam com **nós principais padrão do ComfyUI** — sem pacote wrapper para o próprio modelo. Apenas AnimateDiff (ambas as variantes) e CogVideoX precisam de um. A saída de vídeo usa [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); a interpolação de quadros usa [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Os valores de VRAM são o mínimo para a resolução padrão da família, lidos de `VIDEO_MODEL_INFO` — não os máximos. Mais memória permite clipes mais longos e resoluções mais altas da mesma família.

### Verifique antes de executar

Em vez de descobrir um nó ausente no momento do envio:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## Configuração

As variáveis de ambiente usam o prefixo `COMFY_HEADLESS_` com delimitadores de seção `__`:

| Variável | Padrão |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | tempo limite de leitura, segundos |
| `COMFY_HEADLESS_LOGGING__LEVEL` | nível de registro |

Ou passe a URL diretamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interface web

```bash
comfy-headless                 # launching the UI is the default action
```

| Sinalizador | Significado |
|------|---------|
| `--port` / `-p` | Porta da interface do usuário (padrão `7861`) |
| `--share` | Link de compartilhamento público do Gradio |
| `--url` | URL do servidor ComfyUI |
| `--version` / `-v` | Imprimir versão |
| `--check` | Disponibilidade de recursos |
| `--diagnose` | Diagnósticos completos |

Seis abas: Imagem, Vídeo, Fila e Histórico, Fluxos de Trabalho, Modelos, Configurações. O tema é Ocean Mist —
tons suaves de azul-esverdeado em fundos neutros quentes.

Programaticamente (requer `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progresso

Chamadas bloqueantes usam uma função de retorno `on_progress`:

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

Para atualizações em tempo real via WebSocket (requer `[websocket]`):

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## Erros

Cada exceção contém um código, mensagem e dica estruturados:

```python
from comfy_headless import (
    ComfyHeadlessError,       # base
    ComfyUIConnectionError,   # cannot reach ComfyUI
    ComfyUIOfflineError,      # ComfyUI not responding
    GenerationTimeoutError,
    GenerationFailedError,
    ValidationError,
    UploadError,              # new in 3.0
    MissingNodePackError,     # new in 3.0
)

try:
    client.generate_image("test")
except ComfyUIOfflineError:
    print("Start ComfyUI first")
```

## Como funciona

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

A biblioteca se comunica com sete rotas do ComfyUI — `/system_stats`, `/object_info`, `/queue`,
`/history`, `/prompt`, `/interrupt`, `/view` — mais `/upload/image` e `/upload/mask` para
entrada binária.

`/object_info` é a autoridade sobre o que um determinado servidor pode executar. É um ponto de extremidade ativo, não
um artefato com versão: não há um registro central de nós para referenciar. Portanto, a biblioteca
valida os gráficos gerados em relação ao catálogo real do servidor de destino, em vez de assumir um
conjunto fixo de nós. `check_workflow_dependencies()` é essa verificação e representa uma infraestrutura essencial, e não apenas uma conveniência.

Recursos úteis quando você precisa do próprio gráfico:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentação

Manual completo:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— introdução, uso, configuração, referência da API, modelos de vídeo, arquitetura.

## Segurança e escopo dos dados

- **Dados acessados:** conecta-se a uma instância local ou remota do ComfyUI via HTTP/WebSocket.
Envia o JSON do fluxo de trabalho e as imagens carregadas, recebe os arquivos de mídia gerados. Opcionalmente, conecta-se
a um Ollama local para inteligência de prompts. Grava a saída em diretórios temporários com
limpeza automática.
- **Dados NÃO acessados:** sem telemetria, sem análise, sem APIs externas além dos pontos de extremidade do ComfyUI
e do Ollama que você configurar. Os segredos são mascarados em toda a saída do log por meio de
`SecretValue`.
- **Permissões necessárias:** acesso à rede para o seu servidor ComfyUI e servidor Ollama opcional; permissão de gravação de arquivos para saída e diretórios temporários.
- **Uploads:** `upload_image` rejeita tentativas de atravessar subpastas. Os arquivos carregados são armazenados
no diretório de entrada do ComfyUI no servidor especificado — trate esse servidor como confiável.

Consulte [SECURITY.md](SECURITY.md) para relatar vulnerabilidades.

## Avaliação

| Categoria | Pontuação |
|----------|-------|
| A. Segurança | 10/10 |
| B. Tratamento de erros | 10/10 |
| C. Documentação para o usuário | 10/10 |
| D. Boas práticas de desenvolvimento | 10/10 |
| E. Identidade (suave) | 10/10 |
| **Overall** | **50/50** |

> Avaliado com [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Relacionado

Parte do [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — ferramentas de ML de código aberto para
hardware local.

## Contribuições

Problemas e solicitações de pull são bem-vindos — consulte [CONTRIBUTING.md](CONTRIBUTING.md). Áreas úteis:
famílias adicionais de modelos, modelos de fluxo de trabalho, documentação, correções de bugs.

Se você adicionar um tipo de nó, verifique primeiro se ele existe no catálogo ativo do ComfyUI e declare seu
pacote, caso não seja um nó central. Essa regra é o motivo pelo qual esta versão existe.

## Licença

MIT — consulte [LICENSE](LICENSE).

---

Criado por [MCP Tool Shop](https://mcp-tool-shop.github.io/)
