<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Drive ComfyUI from Python. No node graph.</strong>
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

**A versão 3.1 estende essa funcionalidade para seis perfis de fluxo de trabalho:** — **Imagem, Vídeo, 3D, Inferência, Metadados, Áudio** — em uma camada compartilhada de endereçamento/tipagem que utiliza as próprias regras de validação do ComfyUI: correspondência de tipos de união transcrita do validador do servidor, campos dinâmicos pontuados (`codec.encoding.crf`) e entradas condicionais que rejeitam valores de ramos inativos no momento da construção. A mesma estrutura de roteamento anterior — malhas, música e legendas retornam através de `/history` + `/view` como tudo o mais.

| Problema | O que comfy-headless faz |
|---------|--------------------------|
| A interface do nó é extensa | Predefinições e uma API Python limpa |
| A engenharia de prompts é difícil | Aprimoramento opcional por meio da IA local Ollama |
| A geração de vídeo é complexa | 24 predefinições em 9 famílias de modelos |
| "Preciso de uma malha a partir desta imagem." | `generate_3d()` — Hunyuan3D-2, todos os nós principais |
| "Preciso de música/faixas separadas." | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "O que há nesta imagem?" | `run_inference()` — legenda, tag, detecção, segmentação, OCR |
| "Qual gráfico gerou esta imagem PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
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

### Qwen-Image (novo na versão 3.1)

O modelo Qwen-Image-2512 de texto para imagem é fornecido como o modelo `qwen_txt2img`, com a receita que o modelo realmente deseja incorporada: caminho `UNETLoader`, `EmptySD3LatentImage` de 16 canais (a representação latente do SDXL produz resultados ruins em modelos DiT), 20 passos, **cfg 2.5**, desvio 3.1, tamanho nativo 1328×1328:

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

Edição de instruções com até três imagens de referência (Qwen-Image-Edit-2511):

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

As referências são fornecidas como entradas discretas `image1..image3` em `TextEncodeQwenImageEditPlus` e não passam pelo VAEEncode — a forma do gráfico é exatamente o que o nó espera.

### ControlNet (novo na versão 3.1)

Um único caminho de código abrange os ControlNets de união Qwen e SDXL:

```python
from comfy_headless import build_controlnet_workflow

workflow = build_controlnet_workflow(
    "a stone fortress at dawn",
    control_image_ref=client.upload_image("depth.png")["ref"],
    control_type="depth",      # verbatim enum; "auto" makes the model infer
    base="qwen",               # or "sdxl"
)
client.queue_prompt(workflow)
```

Apenas o pré-processador principal `Canny` é emitido (`preprocess="canny"`); outros tipos de dicas esperam uma imagem de controle pré-criada, porque seus pré-processadores estão em um pacote personalizado que esta biblioteca não exige silenciosamente.

## Vídeo

```python
from comfy_headless import list_video_presets, get_recommended_preset

print(list_video_presets())                  # 26 presets
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

> **Novo na versão 3.1:** Hunyuan 1.5 de imagem para vídeo é um verdadeiro i2v — os predefinidos `hunyuan15_i2v` e `hunyuan15_i2v_fast` são construídos sobre o nó principal `HunyuanVideo15ImageToVideo` e exigem uma entrada `init_image` (a versão 3.0 criou silenciosamente um gráfico de texto para vídeo). E `output="core"` substitui o terminador `VHS_VideoCombine` pelo principal `CreateVideo → SaveVideo`, eliminando completamente a dependência do Video Helper Suite.

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

Você também pode verificar os tipos das arestas de um gráfico em relação ao servidor ativo, usando a própria regra de aceitação do servidor (de modo que uma entrada `MESH` alimentando uma entrada de união `FILE_3D_*` nunca seja uma rejeição falsa):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (novo na versão 3.1)

Imagem para malha via **Hunyuan3D-2** — totalmente nós principais do ComfyUI, sem pacotes de wrapper, sem novos caminhos. O GLB é registrado em `/history` exatamente como um PNG e baixado através de `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` aceita um caminho local, bytes brutos, um dicionário `upload_image()` ou uma referência do lado do servidor e faz o upload automaticamente quando necessário. É apenas condicionamento de imagem — não há prompt de texto no gráfico. Ajustáveis: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

Os modelos 3D do pacote wrapper (TRELLIS, TripoSG, ...) não são emitidos deliberadamente — as dependências nativas do ComfyUI-3D-Pack são as menos estáveis no ecossistema.

## Áudio (novo na versão 3.1)

Texto para música via **ACE-Step 1.5** — código e pesos com licença MIT, nós principais nativos, zero pacotes. O checkpoint turbo é executado em 8 passos / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

O construtor aplica a invariante de acoplamento do modelo para você: o `duration` do codificador e o `seconds` da representação latente são um único parâmetro lógico, derivados de um único campo — o tempo de execução não os valida cruzadamente e uma incompatibilidade é concluída "com sucesso" com saída silenciosamente incorreta. A saída passa por `SaveAudioAdvanced` (o único nó de salvamento de áudio não depreciado); a saída `flac` não emite nenhum campo de qualidade, `mp3`/`opus` emitem o subcampo pontuado `format.quality`.

Separação de faixas (requer o pacote `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferência (novo na versão 3.1)

Chamadas de modelo não generativas — faça perguntas sobre uma imagem em vez de criá-la. Executa no Florence-2 (pacote `comfyui-florence2`; a tarefa de detecção adiciona `comfyui-segment-anything-2`):

```python
r = client.run_inference("photo.png", task="caption")
print(r["text"])                     # the caption, read straight from /history

r = client.run_inference("photo.png", task="tag")               # booru-style tags
r = client.run_inference("photo.png", task="ocr")
r = client.run_inference("photo.png", task="detect", text_input="the red car")
print(r["text"])                     # bounding-box coordinates as JSON

r = client.run_inference("photo.png", task="segment", text_input="the person")
mask_png = client.get_file(**r["images"][0])
```

A regra fundamental do perfil: um resultado atinge `/history` apenas através de um nó de saída. Cada gráfico de inferência termina em `SaveText` principal (que relata o texto diretamente — sem uma segunda viagem) ou `SaveImage` para máscaras, e o construtor se recusa a emitir um gráfico que seria executado e não retornaria nada.

## Proveniência (novo na versão 3.1)

O ComfyUI incorpora o **exato formato de gráfico da API** em cada imagem PNG de saída. O comfy-headless lê isso — código stdlib puro, sem Pillow — e pode executá-lo novamente literalmente:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Crie uma proveniência personalizada sem nenhum nó personalizado — qualquer coisa em `extra_pnginfo` se torna um fragmento de texto PNG nas saídas:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limites conhecidos, documentados em vez de ocultos: WebP/JPEG carregam os mesmos dados no EXIF (um caminho de leitor diferente, não implementado); as saídas de vídeo não incorporam o gráfico; implantações reforçadas podem remover chaves desconhecidas; e a conversão GUI→API não tem rota do servidor — use "Fluxo de Trabalho → Exportar (API)" do ComfyUI.

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
    GraphAddressError,        # new in 3.1 — bad dotted field / inactive combo branch
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

A biblioteca se comunica com sete rotas do ComfyUI — `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view` — mais `/upload/image` e `/upload/mask` para entrada binária (os uploads de áudio também usam `/upload/image`; o servidor não tem rota específica de áudio). Todos os seis perfis se encaixam nessa estrutura: a versão 3.1 adicionou malhas, música, legendas e proveniência sem adicionar uma única rota.

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
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — introdução, uso, os seis perfis, modelos de vídeo, configuração, referência da API, arquitetura.

**Base de conhecimento no repositório** para LLMs e colaboradores: [`kb/`](kb/README.md) — uma base [`index.json`](kb/index.json) legível por máquina sobre páginas de fatos por perfil, gráficos de referência executáveis (`kb/workflows/*.json`, gerados a partir dos próprios construtores para que não possam divergir) e proveniência do nó (`kb/nodes.json`). `python scripts/gen_kb.py` regenera isso; o conjunto de testes falha se o código e a base de conhecimento discordarem.

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
