<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="600">
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

comfy-headless cria **gráficos no formato ComfyUI API** e os executa. Você chama uma função Python; ela gera o gráfico de nós JSON, envia-o para ComfyUI, verifica se a operação foi concluída e fornece os caminhos de saída.

Essa estrutura é importante, pois indica o que pode dar errado. A função principal da biblioteca é gerar nomes de nós e chaves de entrada que o ComfyUI de destino realmente possui. Quando ComfyUI renomeia ou remove um nó, um gráfico que referencia o nome antigo é rejeitado no envio, com um erro obscuro — e nada o avisa com antecedência.

**v3.0 é a versão que levou isso a sério.** Cada tipo de nó que esta biblioteca gera foi auditado em relação ao catálogo ativo de ComfyUI. Nove não existiam mais. Eles foram removidos, os gráficos que os utilizavam são reconstruídos com nós verificados e a biblioteca agora pode informar o que falta em um servidor *antes* que você execute um processo nele.

**v3.1 estende essa abordagem para seis perfis de fluxo de trabalho** — **Imagem, Vídeo, 3D, Inferência, Metadados, Áudio** — em uma camada compartilhada de endereçamento/tipagem que utiliza as próprias regras de validação de ComfyUI: correspondência de tipos de união transcrita do validador do servidor, campos dinâmicos pontilhados (`codec.encoding.crf`) e entradas condicionais que rejeitam valores de ramos inativos no momento da construção. A mesma estrutura de roteamento de antes — malhas, músicas e legendas retornam através de `/history` + `/view`, como tudo o mais.

| Problema | O que o comfy-headless faz |
|---------|--------------------------|
| A interface do nó é extensa | Predefinições e uma API Python limpa |
| A engenharia de prompts é difícil | Aprimoramento opcional por meio de IA local com Ollama |
| A geração de vídeo é complexa | 26 predefinições em 9 famílias de modelos |
| "Preciso de uma malha a partir desta imagem" | `generate_3d()` — Hunyuan3D-2, todos os nós principais |
| "Preciso de música/faixas" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "O que tem nesta imagem?" | `run_inference()` — legenda, tag, detectar, segmentar, OCR |
| "Qual gráfico gerou este PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
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
| `ai` | Análise e aprimoramento de prompts por meio de IA local com Ollama |
| `websocket` | Progresso em tempo real em WebSocket |
| `ui` | Interface web Gradio |
| `health` | Monitoramento da saúde do sistema |
| `validation` | Validação de configuração Pydantic |
| `observability` | Rastreamento OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Tudo o que foi mencionado |

Requer **Python 3.10+** e uma instância ComfyUI em execução.

Verifique o que está ativo em tempo de execução:

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

Oito predefinições de imagem: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`.

Processe uma lista de prompts:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Aprimoramento de prompt por IA

Requer o extra `[ai]` e um Ollama local. Estas são **funções de nível de módulo**, não métodos de cliente:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (novo na versão 3.1)

Qwen-Image-2512, de texto para imagem, é fornecido como o modelo `qwen_txt2img`, com a receita que o modelo realmente deseja incorporada: caminho `UNETLoader`, 16 canais `EmptySD3LatentImage` (a latência SDXL produz resultados ruins em modelos DiT), 20 etapas, **cfg 2.5**, deslocamento 3.1, bucket nativo 1328×1328:

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

As referências são fornecidas para `TextEncodeQwenImageEditPlus` como entradas `image1..image3` discretas e não passam por VAEEncode — a forma do gráfico que o nó realmente espera.

### ControlNet (novo na versão 3.1)

Um único caminho de código abrange a união Qwen e SDXL ControlNets:

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

Apenas o pré-processador principal `Canny` é gerado (`preprocess="canny"`); outros tipos de dicas esperam uma imagem de controle pré-criada, porque seus pré-processadores estão em um pacote personalizado que esta biblioteca não exige silenciosamente.

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

A seleção é feita **por predefinição**, não por modelo — `generate_video` não tem um argumento `model`. Qualquer um de `frames`, `fps`, `steps`, `cfg`, `width`, `height` pode ser passado para substituir a predefinição.

### Entrada de imagem

Vídeo a partir de imagem e qualquer outra coisa que utilize uma imagem de origem, precisa que essa imagem exista primeiro em ComfyUI. Carregue-a e, em seguida, passe o nome que o servidor retorna:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Leia `name` da resposta, em vez de reutilizar o nome do arquivo que você enviou — ComfyUI renomeia em caso de colisão, portanto, os dois nem sempre são iguais. `ref` é o mesmo valor já combinado com qualquer subpasta, que é exatamente o que o gráfico precisa.

> **Alterado na versão 3.0:** `init_image` é um nome de arquivo do lado do servidor. Versões anteriores aceitavam dados base64 e os transmitiam por meio de um nó de terceiros que não existe em uma instalação padrão de ComfyUI. Consulte o [CHANGELOG](CHANGELOG.md).

> **Novo na versão 3.1:** O vídeo de imagem Hunyuan 1.5 é um i2v real — as predefinições `hunyuan15_i2v` e `hunyuan15_i2v_fast` são baseadas no nó principal `HunyuanVideo15ImageToVideo` e exigem um `init_image` (v3.0 criou silenciosamente um gráfico de vídeo a partir de texto em vez disso). E `output="core"` troca o terminador `VHS_VideoCombine` pelo `CreateVideo → SaveVideo` principal, eliminando completamente a dependência do Video Helper Suite.

### Famílias de modelos

| Família | VRAM mínima | Qualidade | Velocidade | Nós extras | Melhor para |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Ótimo | Médio | — | Baixa VRAM, eficiência |
| AnimateDiff Lightning | 6 GB | Razoável | Mais rápido | AnimateDiff-Evolved | 4 etapas de rascunho |
| AnimateDiff | 8 GB | Bom | Rápido | AnimateDiff-Evolved, Interpolação de quadros | Visualizações rápidas |
| **LTX-Video** | 12 GB | Excelente | Rápido | — | O padrão seguro |
| **Mochi** | 12 GB | Excelente | Lento | — | Adesão ao texto, clipes longos |
| **SVD** | 12 GB | Bom | Médio | — | Animar uma imagem estática |
| **Hunyuan 1.5** | 14 GB | Melhor | Lento | — | Qualidade mais alta |
| CogVideoX | 16 GB | Bom | Lento | CogVideoX Wrapper | Legado |
| **Hunyuan 1.0** | 24 GB | Ótimo | Lento | Interpolação de quadros | Substituído pela versão 1.5 |

Seis das nove famílias funcionam em **nós principais ComfyUI padrão** — sem pacote wrapper para o próprio modelo. Apenas AnimateDiff (ambas as variantes) e CogVideoX precisam de um. A saída de vídeo usa [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); a interpolação de quadros usa [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Os valores de VRAM são o mínimo para a resolução padrão da família, lidos de `VIDEO_MODEL_INFO` — não são valores máximos. Mais memória permite clipes mais longos e resoluções mais altas da mesma família.

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

Você também pode verificar os tipos de dados das arestas de um grafo em relação ao servidor ativo, usando a própria regra de aceitação do servidor (de modo que uma entrada `MESH` alimentando uma união `FILE_3D_*` nunca seja uma rejeição falsa):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (novo na versão 3.1)

Imagem para malha via **Hunyuan3D-2** — totalmente nós principais ComfyUI, sem pacotes wrapper, sem novas rotas. Os arquivos GLB são registrados em `/history` exatamente como um arquivo PNG e são baixados através de `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` aceita um caminho local, bytes brutos, um dicionário `upload_image()` ou uma referência do lado do servidor e faz o upload automaticamente quando necessário. É apenas condicionamento de imagem — não há prompt de texto no grafo. Ajustáveis: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

Os modelos 3D com pacote wrapper (TRELLIS, TripoSG, ...) não são gerados intencionalmente — as dependências nativas de ComfyUI-3D-Pack são as menos estáveis no ecossistema.

## Áudio (novo na versão 3.1)

Texto para música via **ACE-Step 1.5** — código e pesos com licença MIT, nós principais nativos, zero pacotes. O checkpoint turbo é executado em 8 etapas / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

O criador aplica a invariante de acoplamento do modelo para você: o `duration` do codificador e o `seconds` do latente são um único parâmetro lógico, derivados de um único campo — o tempo de execução não os valida cruzadamente e uma incompatibilidade é concluída "com sucesso" com uma saída silenciosamente incorreta. A saída passa por `SaveAudioAdvanced` (o único nó de salvamento de áudio não obsoleto); a saída `flac` não emite nenhum campo de qualidade, `mp3`/`opus` emitem o subcampo pontilhado `format.quality`.

Separação de faixas (requer o pacote `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferência (novo na versão 3.1)

Chamadas de modelo não generativas — faça perguntas sobre uma imagem em vez de criar uma. Executa no Florence-2 (pacote `comfyui-florence2`; a tarefa de detecção adiciona `comfyui-segment-anything-2`):

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

A regra de carga do perfil: um resultado atinge `/history` apenas através de um nó de saída. Cada grafo de inferência termina no nó principal `SaveText` (que relata o texto embutido — sem uma segunda troca) ou `SaveImage` para máscaras, e o criador se recusa a gerar um grafo que seja executado e não retorne nada.

## Provável (novo na versão 3.1)

ComfyUI incorpora o **grafo exato no formato da API** em cada saída PNG. O comfy-headless o lê novamente — apenas stdlib, sem Pillow — e pode executá-lo novamente literalmente:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Escreva informações de rastreamento personalizadas sem nenhum nó personalizado — qualquer coisa em `extra_pnginfo` se torna um fragmento de texto PNG nas saídas:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limites conhecidos, documentados em vez de ocultos: WebP/JPEG carregam os mesmos dados em EXIF (um caminho de leitura diferente, não implementado); as saídas de vídeo não incorporam o grafo; as implantações reforçadas podem remover chaves desconhecidas; e a conversão GUI→API não tem rota de servidor — use a opção "Fluxo de Trabalho → Exportar (API)" de ComfyUI.

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

## Interface de usuário da web

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

Seis guias: Imagem, Vídeo, Fila e Histórico, Fluxos de Trabalho, Modelos, Configurações. O tema é Ocean Mist — tons suaves de azul-esverdeado em fundos neutros quentes.

Programaticamente (requer `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progresso

Chamadas de bloqueio recebem um callback `on_progress`:

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

A biblioteca se comunica com sete rotas ComfyUI — `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view` — mais `/upload/image` e `/upload/mask` para entrada binária (os uploads de áudio também usam `/upload/image`; o servidor não tem uma rota específica para áudio). Todos os seis perfis se encaixam nessa superfície: v3.1 adicionou malhas, música, legendas e informações de rastreamento sem adicionar uma única rota.

`/object_info` é a autoridade sobre o que um determinado servidor pode executar. É um endpoint ativo, não um artefato com versão: não há um registro de nós principais para fixar. Portanto, a biblioteca valida os grafos gerados em relação ao catálogo real do servidor de destino, em vez de presumir um conjunto fixo de nós. `check_workflow_dependencies()` é essa verificação e é uma infraestrutura essencial, em vez de uma conveniência.

Úteis saídas de emergência quando você deseja o próprio grafo:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentação

Manual completo: **[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — introdução, uso, os seis perfis, modelos de vídeo, configuração, referência da API, arquitetura.

**Base de conhecimento no repositório** para LLMs e colaboradores: [`kb/`](kb/README.md) — uma [`index.json`](kb/index.json) legível por máquina sobre páginas de fatos por perfil, grafos de referência executáveis (`kb/workflows/*.json`, gerados pelos próprios criadores, para que não possam divergir) e informações de rastreamento de nós (`kb/nodes.json`). `python scripts/gen_kb.py` o regenera; a suíte de testes falha se o código e a base de conhecimento discordarem.

## Segurança e âmbito dos dados

- **Dados acessados:** conecta-se a uma instância ComfyUI local ou remota através de HTTP/WebSocket.
Envia o JSON do fluxo de trabalho e as imagens enviadas, recebendo os conteúdos multimédia gerados. Opcionalmente, conecta-se a um Ollama local para obter inteligência de prompts. Escreve os resultados em diretórios temporários com limpeza automática.
- **Dados NÃO acessados:** sem telemetria, sem análise de dados, sem APIs externas além dos pontos de extremidade ComfyUI e Ollama que você configurar. Os segredos são mascarados em todas as saídas de registro através de `SecretValue`.
- **Permissões necessárias:** acesso à rede para o seu servidor ComfyUI e servidor Ollama (opcional); permissão de escrita de arquivos para os diretórios de saída e temporários.
- **Envios:** `upload_image` rejeita tentativas de atravessar subpastas. Os arquivos enviados são armazenados no diretório de entrada de ComfyUI no servidor que você especificar — trate esse servidor como confiável.

Consulte [SECURITY.md](SECURITY.md) para relatar vulnerabilidades.

## Avaliação

| Categoria | Pontuação |
|----------|-------|
| A. Segurança | 10/10 |
| B. Tratamento de erros | 10/10 |
| C. Documentação para operadores | 10/10 |
| D. Boas práticas de desenvolvimento | 10/10 |
| E. Identidade (suave) | 10/10 |
| **Overall** | **50/50** |

> Avaliado com [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Relacionado

Parte do [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — ferramentas de código aberto para aprendizado de máquina (ML) para hardware local.

## Contribuições

Problemas e solicitações de pull são bem-vindos — consulte [CONTRIBUTING.md](CONTRIBUTING.md). Áreas úteis: famílias de modelos adicionais, modelos de fluxo de trabalho, documentação, correções de bugs.

Se você adicionar um tipo de nó, verifique se ele existe no catálogo ComfyUI ativo e declare seu pacote, caso não seja um componente principal. Essa regra é o motivo pelo qual esta versão existe.

## Licença

MIT — consulte [LICENSE](LICENSE).

---

Criado por [MCP Tool Shop](https://mcp-tool-shop.github.io/)
