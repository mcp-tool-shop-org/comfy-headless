<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## Cos'è

comfy-headless crea **grafi in formato ComfyUI API** e li esegue. Si chiama una funzione Python; questa genera il grafo dei nodi JSON, lo invia tramite POST a ComfyUI, verifica il completamento e ti fornisce i percorsi di output.

Questa impostazione è importante, perché ti indica cosa potrebbe andare storto. L'unico compito della libreria è generare i nomi dei nodi e le chiavi di input che il ComfyUI di destinazione effettivamente possiede. Quando ComfyUI rinomina o elimina un nodo, un grafo che fa riferimento al nome precedente viene rifiutato al momento dell'invio con un errore non chiaro, e nulla ti avverte in anticipo.

**v3.0 è la versione che ha preso seriamente in considerazione questo aspetto.** Ogni tipo di nodo che questa libreria genera è stato controllato rispetto al catalogo ComfyUI attivo. Nove non esistevano più. Sono stati eliminati, i grafi che li utilizzavano sono stati ricostruiti su nodi verificati e la libreria ora può dirti cosa manca a un server *prima* di eseguire un processo.

**v3.1 estende questa disciplina a sei profili di flusso di lavoro:** **Immagine, Video, 3D, Inferenza, Metadati, Audio** su un livello condiviso di indirizzamento/tipizzazione che utilizza le regole di convalida di ComfyUI: corrispondenza del tipo unione trascritta dal validatore del server, campi dinamici a punti (`codec.encoding.crf`) e input condizionali che rifiutano i valori di rami inattivi al momento della costruzione. Lo stesso percorso di prima: mesh, musica e didascalie vengono restituiti tramite `/history` + `/view` come tutto il resto.

| Problema | Cosa fa comfy-headless |
|---------|--------------------------|
| L'interfaccia dei nodi è piuttosto complessa | Preset e un'API Python pulita |
| L'ingegneria dei prompt è difficile | Miglioramento opzionale tramite AI locale con Ollama |
| La generazione di video è complessa | 26 preset su 9 famiglie di modelli |
| "Ho bisogno di una mesh da questa immagine" | `generate_3d()` — Hunyuan3D-2, tutti i nodi principali |
| "Ho bisogno di musica/tracce" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "Cosa c'è in questa immagine?" | `run_inference()` — didascalia, tag, rilevamento, segmentazione, OCR |
| "Quale grafo ha generato questo PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
| "Quali impostazioni devo usare?" | Raccomandazioni dimensionate in base alla tua VRAM |
| I grafi falliscono con errori criptici | Il controllo delle dipendenze indica il nome del nodo *e* del pacchetto |

## Avvio rapido

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` restituisce un `dict` con `success`, `prompt_id`, `images`, `error`, `seed` e `preset`. Ogni chiamata di generazione in questa libreria restituisce un dizionario; non esiste un oggetto risultato da estrarre.

## Installazione

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| Extra | Aggiunge |
|-------|------|
| `ai` | Analisi e miglioramento dei prompt tramite Ollama locale |
| `websocket` | Progresso in tempo reale su WebSocket |
| `ui` | Interfaccia web Gradio |
| `health` | Monitoraggio dello stato del sistema |
| `validation` | Convalida della configurazione Pydantic |
| `observability` | Tracciamento OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Tutto quanto sopra |

Richiede **Python 3.10+** e un'istanza ComfyUI in esecuzione.

Verifica cosa è attivo in fase di esecuzione:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## Immagini

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

Otto preset per immagini: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`.

Elabora in batch un elenco di prompt:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Miglioramento del prompt AI

Richiede l'extra `[ai]` e un Ollama locale. Queste sono **funzioni a livello di modulo**, non metodi client:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (nuovo nella versione 3.1)

Qwen-Image-2512, da testo a immagine, viene fornito come modello `qwen_txt2img`, con la ricetta che il modello effettivamente desidera integrata: percorso `UNETLoader`, `EmptySD3LatentImage` a 16 canali (il latente SDXL produce risultati scadenti sui modelli DiT), 20 passaggi, **cfg 2.5**, shift 3.1, bucket nativo 1328×1328:

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

Modifica delle istruzioni con un massimo di tre immagini di riferimento (Qwen-Image-Edit-2511):

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

Le immagini di riferimento vengono fornite a `TextEncodeQwenImageEditPlus` come input discreti `image1..image3` e non passano attraverso VAEEncode, che è la forma del grafo che il nodo effettivamente si aspetta.

### ControlNet (nuovo nella versione 3.1)

Un unico percorso di codice copre l'unione Qwen e SDXL ControlNets:

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

Viene emesso solo il preprocessore principale `Canny` (`preprocess="canny"`); altri tipi di suggerimenti si aspettano un'immagine di controllo pre-elaborata, perché i loro preprocessori si trovano in un pacchetto personalizzato che questa libreria non richiede silenziosamente.

## Video

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

La selezione avviene **tramite preset**, non tramite modello: `generate_video` non ha un argomento `model`. Uno qualsiasi di `frames`, `fps`, `steps`, `cfg`, `width`, `height` può essere passato per sovrascrivere il preset.

### Input immagine

Da immagine a video e qualsiasi altra operazione che utilizza un'immagine di origine, richiede che tale immagine esista all'interno di ComfyUI. Caricala, quindi passa il nome che il server restituisce:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Leggi `name` dalla risposta anziché riutilizzare il nome del file che hai inviato: ComfyUI rinomina in caso di collisione, quindi i due non sono sempre uguali. `ref` è lo stesso valore già unito a qualsiasi sottocartella, che è esattamente ciò di cui il grafo ha bisogno.

> **Modificato nella versione 3.0:** `init_image` è un nome file lato server. Le versioni precedenti accettavano i dati base64 e li passavano attraverso un nodo di terze parti che non esiste in un'installazione ComfyUI standard. Vedi il [CHANGELOG](CHANGELOG.md).

> **Nuovo nella versione 3.1:** Hunyuan 1.5 da immagine a video è un vero i2v: i preset `hunyuan15_i2v` e `hunyuan15_i2v_fast` si basano sul nodo principale `HunyuanVideo15ImageToVideo` e richiedono un `init_image` (v3.0 ha creato silenziosamente un grafo da testo a video). E `output="core"` sostituisce il terminatore `VHS_VideoCombine` con il `CreateVideo → SaveVideo` principale, eliminando completamente la dipendenza dalla Video Helper Suite.

### Famiglie di modelli

| Famiglia | VRAM minima | Qualità | Velocità | Nodi extra | Ideale per |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Ottimo | Medio | — | Bassa VRAM, efficienza |
| AnimateDiff Lightning | 6 GB | Discreto | Veloce | AnimateDiff-Evolved | 4 passaggi di bozza |
| AnimateDiff | 8 GB | Buono | Veloce | AnimateDiff-Evolved, Frame Interp. | Anteprime rapide |
| **LTX-Video** | 12 GB | Eccellente | Veloce | — | L'impostazione predefinita sicura |
| **Mochi** | 12 GB | Eccellente | Lento | — | Coerenza con il testo, clip lunghi |
| **SVD** | 12 GB | Buono | Medio | — | Animare un'immagine statica |
| **Hunyuan 1.5** | 14 GB | Migliore | Lento | — | Massima qualità |
| CogVideoX | 16 GB | Buono | Lento | CogVideoX Wrapper | Legacy |
| **Hunyuan 1.0** | 24 GB | Ottimo | Lento | Interpolazione dei fotogrammi | Sostituito dalla versione 1.5 |

Sei delle nove famiglie funzionano su **nodi core ComfyUI standard**; non è previsto alcun pacchetto wrapper per il modello stesso. Solo AnimateDiff (entrambe le varianti) e CogVideoX ne richiedono uno. L'output video utilizza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); l'interpolazione dei fotogrammi utilizza [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

I valori di VRAM rappresentano il limite inferiore per la risoluzione predefinita di ciascuna famiglia, letti da `VIDEO_MODEL_INFO`; non sono valori massimi. Più memoria consente di ottenere clip più lunghi e risoluzioni più elevate dalla stessa famiglia.

### Verificare prima di eseguire

Invece di scoprire un nodo mancante al momento dell'invio:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

È anche possibile verificare i collegamenti di un grafico rispetto al server attivo, utilizzando la regola di accettazione del server stesso (in modo che un `MESH` che alimenta un input di tipo union `FILE_3D_*` non venga mai rifiutato erroneamente):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (novità nella versione 3.1)

Conversione da immagine a mesh tramite **Hunyuan3D-2**; utilizza esclusivamente nodi core ComfyUI, senza pacchetti wrapper, senza nuove route. Il file GLB viene registrato in `/history` esattamente come farebbe un file PNG e viene scaricato tramite `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` accetta un percorso locale, byte grezzi, un dizionario `upload_image()` o un riferimento lato server e lo carica automaticamente quando necessario. Si tratta di una semplice operazione di condizionamento dell'immagine; non è presente alcun prompt di testo nel grafico. Parametri regolabili: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

I modelli 3D con pacchetto wrapper (TRELLIS, TripoSG, ...) non vengono emessi intenzionalmente; le dipendenze native di ComfyUI-3D-Pack sono le meno stabili nell'ecosistema.

## Audio (novità nella versione 3.1)

Conversione da testo a musica tramite **ACE-Step 1.5**; codice e pesi con licenza MIT, nodi core nativi, zero pacchetti. Il checkpoint turbo viene eseguito con 8 passaggi / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

Il builder applica l'invariante di accoppiamento del modello: l'output `duration` dell'encoder e l'input `seconds` del livello latente sono un singolo parametro logico, controllato da un unico campo; il runtime non li convalida incrociatamente e una mancata corrispondenza viene completata "con successo" con un output silenziosamente errato. L'output passa attraverso `SaveAudioAdvanced` (l'unico nodo di salvataggio audio non deprecato); l'output `flac` non emette alcun campo di qualità, `mp3`/`opus` emettono il sotto-campo `format.quality` puntato.

Separazione delle tracce audio (richiede il pacchetto `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferenza (novità nella versione 3.1)

Chiamate a modelli non generativi: porre domande su un'immagine invece di crearne una. Funziona su Florence-2 (pacchetto `comfyui-florence2`; l'attività di rilevamento aggiunge `comfyui-segment-anything-2`):

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

La regola di carico del profilo: un risultato raggiunge `/history` solo tramite un nodo di output. Ogni grafico di inferenza termina con il nodo core `SaveText` (che riporta il testo in linea; non è necessario un secondo ciclo di comunicazione) o `SaveImage` per le maschere, e il builder rifiuta di emettere un grafico che verrebbe eseguito e non restituirebbe nulla.

## Provenienza (novità nella versione 3.1)

ComfyUI incorpora l'**esatto grafico in formato API** in ogni output PNG. comfy-headless lo legge e può eseguirlo nuovamente:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Scrivere una provenienza personalizzata senza utilizzare alcun nodo personalizzato: qualsiasi elemento in `extra_pnginfo` diventa un blocco di testo PNG negli output:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limiti noti, documentati anziché nascosti: WebP/JPEG contengono gli stessi dati in EXIF (un percorso di lettura diverso, non implementato); gli output video non incorporano il grafico; le implementazioni protette possono eliminare le chiavi sconosciute; e la conversione da GUI ad API non ha una route sul server; utilizzare "Workflow → Export (API)" di ComfyUI.

## Configurazione

Le variabili d'ambiente utilizzano il prefisso `COMFY_HEADLESS_` con i delimitatori di sezione `__`:

| Variabile | Valore predefinito |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | timeout di lettura, secondi |
| `COMFY_HEADLESS_LOGGING__LEVEL` | livello di registrazione |

Oppure, passare l'URL direttamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interfaccia utente web

```bash
comfy-headless                 # launching the UI is the default action
```

| Flag | Significato |
|------|---------|
| `--port` / `-p` | Porta dell'interfaccia utente (predefinita `7861`) |
| `--share` | Link di condivisione pubblico di Gradio |
| `--url` | URL del server ComfyUI |
| `--version` / `-v` | Stampa la versione |
| `--check` | Disponibilità delle funzionalità |
| `--diagnose` | Diagnostica completa |

Sei schede: Immagine, Video, Coda e cronologia, Flussi di lavoro, Modelli, Impostazioni. Il tema è Ocean Mist: accenti color verde acqua su sfondi neutri caldi.

In modo programmatico (richiede `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progresso

Le chiamate bloccanti accettano una funzione di callback `on_progress`:

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

Per aggiornamenti in tempo reale tramite WebSocket (richiede `[websocket]`):

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## Errori

Ogni eccezione contiene un codice, un messaggio e un suggerimento strutturati:

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

## Come funziona

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

La libreria comunica con sette route ComfyUI: `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view`, più `/upload/image` e `/upload/mask` per l'input binario (anche i caricamenti audio utilizzano `/upload/image`; il server non ha una route specifica per l'audio). Tutti e sei i profili si adattano a questa struttura: v3.1 ha aggiunto mesh, musica, didascalie e provenienza senza aggiungere una singola route.

`/object_info` è l'autorità su ciò che un determinato server può eseguire. È un endpoint attivo, non un artefatto con versione: non esiste un registro di nodi core a cui fare riferimento. Pertanto, la libreria convalida i grafici emessi rispetto al catalogo effettivo del server di destinazione anziché presupporre un set di nodi fisso. `check_workflow_dependencies()` è tale controllo ed è un'infrastruttura essenziale, non una semplice comodità.

Utili vie di fuga quando si desidera il grafico stesso:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentazione

Manuale completo: **[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**; introduzione, utilizzo, i sei profili, modelli video, configurazione, riferimento API, architettura.

**Base di conoscenza all'interno del repository** per LLM e collaboratori: [`kb/`](kb/README.md); una [`index.json`](kb/index.json) leggibile dalla macchina su pagine di fatti per profilo, grafici di riferimento eseguibili (`kb/workflows/*.json`, generati dagli stessi builder in modo che non possano divergere) e provenienza dei nodi (`kb/nodes.json`). `python scripts/gen_kb.py` lo rigenera; la suite di test fallisce se il codice e la base di conoscenza non corrispondono.

## Sicurezza e ambito dei dati

- **Dati coinvolti:** si connette a un’istanza ComfyUI locale o remota tramite HTTP/WebSocket.
Invia il JSON del flusso di lavoro e le immagini caricate, riceve i contenuti multimediali generati. Facoltativamente, si connette a un’istanza locale di Ollama per l’elaborazione dei prompt. Scrive l’output in directory temporanee con pulizia automatica.
- **Dati NON coinvolti:** nessun telemetria, nessuna analisi, nessuna API esterna oltre agli endpoint ComfyUI e Ollama che si configurano. I segreti sono mascherati in tutti gli output dei log tramite `SecretValue`.
- **Autorizzazioni richieste:** accesso alla rete al server ComfyUI e, facoltativamente, al server Ollama; autorizzazione di scrittura dei file per l’output e le directory temporanee.
- **Caricamenti:** `upload_image` rifiuta i tentativi di attraversamento delle sottocartelle. I file caricati vengono inseriti nella directory di input di ComfyUI sul server specificato; trattare tale server come attendibile.

Per la segnalazione di vulnerabilità, consultare [SECURITY.md](SECURITY.md).

## Valutazione

| Categoria | Punteggio |
|----------|-------|
| A. Sicurezza | 10/10 |
| B. Gestione degli errori | 10/10 |
| C. Documentazione per l’operatore | 10/10 |
| D. Pratiche di sviluppo | 10/10 |
| E. Identità (soft) | 10/10 |
| **Overall** | **50/50** |

> Valutato con [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Argomenti correlati

Parte di [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — strumenti ML open source per hardware locale.

## Contributi

Sono benvenuti problemi e richieste di pull; consultare [CONTRIBUTING.md](CONTRIBUTING.md). Aree utili: famiglie di modelli aggiuntive, modelli di flusso di lavoro, documentazione, correzioni di bug.

Se si aggiunge un tipo di nodo, verificare innanzitutto che esista nel catalogo ComfyUI attivo e dichiarare il relativo pacchetto se non è un componente principale. Questa regola è il motivo per cui è stata rilasciata questa versione.

## Licenza

MIT — consultare [LICENSE](LICENSE).

---

Realizzato da [MCP Tool Shop](https://mcp-tool-shop.github.io/)
