<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## Cos'è questo

comfy-headless crea **grafi in formato API ComfyUI** e li esegue. Si chiama una funzione Python; questa genera il grafo dei nodi JSON, lo invia a ComfyUI tramite POST, verifica il completamento e fornisce i percorsi di output.

Questa impostazione è importante perché indica cosa potrebbe andare storto. L'obiettivo principale della libreria è generare nomi di nodi e chiavi di input che siano effettivamente presenti in ComfyUI. Quando ComfyUI rinomina o elimina un nodo, un grafo che fa riferimento al nome precedente viene rifiutato durante l'invio con un errore non chiaro, senza alcun avviso preventivo.

**La versione 3.0 affronta seriamente questo problema.** Ogni tipo di nodo generato da questa libreria è stato verificato rispetto al catalogo ComfyUI attivo. Nove nodi non esistevano più. Sono stati rimossi, i grafi che li utilizzavano sono stati ricostruiti con nodi verificati e la libreria ora può indicare quali elementi mancano in un server *prima* di avviare l'esecuzione.

**La versione 3.1 estende questo approccio a sei profili di flusso di lavoro:** **Immagine, Video, 3D, Inferenza, Metadati, Audio**, su un livello condiviso di indirizzamento/tipizzazione che utilizza le regole di convalida proprie di ComfyUI: corrispondenza dei tipi union trascritta dal validatore del server, campi dinamici a punti (`codec.encoding.crf`) e input condizionali che rifiutano i valori delle diramazioni inattive al momento della creazione. Lo stesso percorso utilizzato in precedenza: mesh, musica e didascalie vengono restituiti tramite `/history` + `/view` come tutti gli altri elementi.

| Problema | Cosa fa comfy-headless |
|---------|--------------------------|
| L'interfaccia dei nodi è piuttosto complessa | Preset e un'API Python pulita |
| L'ingegneria del prompt è difficile | Miglioramento opzionale tramite AI locale con Ollama |
| La generazione di video è complessa | 26 preset su 9 famiglie di modelli |
| "Ho bisogno di una mesh da questa immagine" | `generate_3d()` — Hunyuan3D-2, tutti i nodi principali |
| "Ho bisogno di musica/tracce audio" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "Cosa c'è in questa immagine?" | `run_inference()` — didascalia, tag, rilevamento, segmentazione, OCR |
| "Quale grafo ha generato questo PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
| "Quali impostazioni devo usare?" | Raccomandazioni adattate alla VRAM disponibile |
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

| Extra | Aggiunte |
|-------|------|
| `ai` | Analisi e miglioramento del prompt tramite Ollama locale |
| `websocket` | Progresso in tempo reale tramite WebSocket |
| `ui` | Interfaccia web Gradio |
| `health` | Monitoraggio dello stato del sistema |
| `validation` | Convalida della configurazione Pydantic |
| `observability` | Tracciamento OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Tutto quanto sopra |

Richiede **Python 3.10+** e un'istanza di ComfyUI in esecuzione.

Verifica cosa è attivo durante l'esecuzione:

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

Elabora un elenco di prompt:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Miglioramento del prompt tramite AI

Richiede l'extra `[ai]` e un Ollama locale. Queste sono **funzioni a livello di modulo**, non metodi client:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (nuovo nella versione 3.1)

Qwen-Image-2512, conversione da testo a immagine, viene fornito come modello `qwen_txt2img`, con la ricetta che il modello effettivamente desidera integrata: percorso `UNETLoader`, 16 canali `EmptySD3LatentImage` (il latente SDXL produce risultati scadenti sui modelli DiT), 20 passaggi, **cfg 2.5**, shift 3.1, bucket nativo 1328×1328:

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

Le immagini di riferimento vengono fornite come input discreti `image1..image3` in `TextEncodeQwenImageEditPlus` e non passano attraverso VAEEncode: questa è la forma del grafo che il nodo effettivamente si aspetta.

### ControlNet (nuovo nella versione 3.1)

Un unico percorso di codice copre i ControlNet union Qwen e SDXL:

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

Viene emesso solo il preprocessore principale `Canny` (`preprocess="canny"`); altri tipi di suggerimenti si aspettano un'immagine di controllo pre-elaborata, perché i loro preprocessori sono presenti in un pacchetto personalizzato che questa libreria non richiede silenziosamente.

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

L'input immagine-video e qualsiasi altro elemento che utilizza un'immagine di origine devono prima avere tale immagine presente in ComfyUI. Caricala, quindi passa il nome restituito dal server:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Leggi `name` dalla risposta anziché riutilizzare il nome del file inviato: ComfyUI rinomina in caso di collisione, quindi i due non sono sempre uguali. `ref` è lo stesso valore già unito a qualsiasi sottocartella, che è esattamente ciò di cui ha bisogno il grafo.

> **Modificato nella versione 3.0:** `init_image` è un nome file lato server. Le versioni precedenti accettavano dati base64 e li trasmettevano tramite un nodo di terze parti che non esiste in un'installazione standard di ComfyUI. Consulta il [CHANGELOG](CHANGELOG.md).

> **Nuovo nella versione 3.1:** Hunyuan 1.5, conversione da immagine a video, è una vera i2v: i preset `hunyuan15_i2v` e `hunyuan15_i2v_fast` si basano sul nodo principale `HunyuanVideo15ImageToVideo` e richiedono un `init_image` (la versione 3.0 creava silenziosamente un grafo di conversione da testo a video). Inoltre, `output="core"` sostituisce il terminatore `VHS_VideoCombine` con il core `CreateVideo → SaveVideo`, eliminando completamente la dipendenza dalla Video Helper Suite.

### Famiglie di modelli

| Famiglia | VRAM minima | Qualità | Velocità | Nodi extra | Ideale per |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Ottimo | Medio | — | Bassa VRAM, efficienza |
| AnimateDiff Lightning | 6 GB | Discreto | Più veloce | AnimateDiff-Evolved | Bozze in 4 passaggi |
| AnimateDiff | 8 GB | Buono | Veloce | AnimateDiff-Evolved, interpolazione dei fotogrammi. | Anteprime rapide |
| **LTX-Video** | 12 GB | Eccellente | Veloce | — | L'impostazione predefinita più sicura |
| **Mochi** | 12 GB | Eccellente | Lento | — | Rispetto del testo, clip lunghe |
| **SVD** | 12 GB | Buono | Medio | — | Animazione di un'immagine statica |
| **Hunyuan 1.5** | 14 GB | Migliore | Lento | — | Massima qualità |
| CogVideoX | 16 GB | Buono | Lento | Wrapper CogVideoX | Legacy (obsoleto) |
| **Hunyuan 1.0** | 24 GB | Ottimo | Lento | Interpolazione dei fotogrammi | Sostituito dalla versione 1.5 |

Sei delle nove famiglie funzionano con i **nodi principali standard di ComfyUI**; non è necessario alcun pacchetto aggiuntivo per il modello stesso. Solo AnimateDiff (entrambe le varianti) e CogVideoX ne richiedono uno. L'output video utilizza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); l'interpolazione dei fotogrammi utilizza [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

I valori di VRAM rappresentano il limite inferiore per la risoluzione predefinita di ciascuna famiglia, letti da `VIDEO_MODEL_INFO`; non sono valori massimi. Più memoria consente clip più lunghe e risoluzioni più elevate all'interno della stessa famiglia.

### Verifica prima di eseguire

Invece di scoprire un nodo mancante al momento dell'invio:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

È anche possibile verificare la presenza di nodi in un grafico rispetto al server attivo, utilizzando la regola di accettazione del server stesso (in modo che l'alimentazione di `MESH` a un input union `FILE_3D_*` non comporti mai un rifiuto errato):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (novità nella versione 3.1)

Conversione da immagine a mesh tramite **Hunyuan3D-2**: utilizza esclusivamente i nodi principali di ComfyUI, senza pacchetti aggiuntivi o nuove route. Il file GLB viene registrato in `/history` esattamente come farebbe un file PNG e scaricato tramite `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` accetta un percorso locale, byte grezzi, un dizionario `upload_image()` o un riferimento lato server e lo carica automaticamente quando necessario. Si tratta di una pura condizione basata sull'immagine; non è presente alcun prompt testuale nel grafico. Parametri regolabili: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

I modelli 3D con pacchetti aggiuntivi (TRELLIS, TripoSG, ...) non vengono generati intenzionalmente; le dipendenze native di ComfyUI-3D-Pack sono le meno stabili nell'ecosistema.

## Audio (novità nella versione 3.1)

Conversione da testo a musica tramite **ACE-Step 1.5**: codice e pesi con licenza MIT, nodi principali nativi, nessun pacchetto aggiuntivo. Il checkpoint turbo viene eseguito in 8 passaggi / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

Il builder applica l'invariante di accoppiamento del modello per te: l'output `duration` dell'encoder e l'input `seconds` della latenza sono un unico parametro logico, derivato da un singolo campo; il runtime non li convalida incrociatamente e una mancata corrispondenza viene completata "con successo" con un output silenziosamente errato. L'output passa attraverso `SaveAudioAdvanced` (l'unico nodo di salvataggio audio non obsoleto); l'output `flac` non emette alcun campo di qualità, `mp3`/`opus` emettono il sotto-campo punteggiato `format.quality`.

Separazione delle tracce (richiede il pacchetto `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferenza (novità nella versione 3.1)

Chiamate a modelli non generativi: poni domande su un'immagine invece di crearne una. Funziona con Florence-2 (pacchetto `comfyui-florence2`; l'attività di rilevamento aggiunge `comfyui-segment-anything-2`):

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

La regola fondamentale del profilo: un risultato raggiunge `/history` solo tramite un nodo di output. Ogni grafico di inferenza termina nei nodi principali `SaveText` (che visualizza il testo in linea; non è necessario un secondo ciclo) o `SaveImage` per le maschere, e il builder rifiuta di generare un grafico che verrebbe eseguito senza restituire alcun risultato.

## Provenienza (novità nella versione 3.1)

ComfyUI incorpora l'**esatto formato API del grafico** in ogni output PNG. comfy-headless lo legge e può riprodurlo esattamente:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Scrivi una provenienza personalizzata senza utilizzare alcun nodo personalizzato: qualsiasi elemento in `extra_pnginfo` diventa un blocco di testo PNG negli output:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limiti noti, documentati anziché nascosti: WebP/JPEG contengono gli stessi dati in EXIF (un percorso di lettura diverso, non implementato); gli output video non incorporano il grafico; le distribuzioni protette possono eliminare chiavi sconosciute e la conversione da GUI ad API non ha una route sul server; utilizza "Workflow → Export (API)" di ComfyUI.

## Configurazione

Le variabili d'ambiente utilizzano il prefisso `COMFY_HEADLESS_` con i delimitatori della sezione `__`:

| Variabile | Predefinito |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | Timeout di lettura, secondi |
| `COMFY_HEADLESS_LOGGING__LEVEL` | Livello di registrazione |

Oppure passa l'URL direttamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interfaccia utente web

```bash
comfy-headless                 # launching the UI is the default action
```

| Flag | Significato |
|------|---------|
| `--port` / `-p` | Porta dell'interfaccia utente (predefinito `7861`) |
| `--share` | Link di condivisione pubblico Gradio |
| `--url` | URL del server ComfyUI |
| `--version` / `-v` | Stampa la versione |
| `--check` | Disponibilità delle funzionalità |
| `--diagnose` | Diagnostica completa |

Sei schede: Immagine, Video, Coda e cronologia, Flussi di lavoro, Modelli, Impostazioni. Il tema è Ocean Mist: accenti color verde acqua su sfondi neutri caldi.

A livello programmatico (richiede `[ui]`):

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

La libreria comunica con sette route di ComfyUI: `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view`, più `/upload/image` e `/upload/mask` per l'input binario (anche gli upload audio utilizzano `/upload/image`; il server non ha una route specifica per l'audio). Tutti e sei i profili si adattano a questa struttura: la versione 3.1 ha aggiunto mesh, musica, didascalie e provenienza senza aggiungere una singola route.

`/object_info` è l'autorità su ciò che un determinato server può eseguire. È un endpoint attivo, non un artefatto con versioni: non esiste un registro di nodi principali a cui fare riferimento. Pertanto, la libreria convalida i grafici generati rispetto al catalogo effettivo del server di destinazione anziché presupporre un set fisso di nodi. `check_workflow_dependencies()` è tale controllo ed è un'infrastruttura fondamentale piuttosto che una semplice funzionalità.

Utili strumenti di emergenza quando si desidera utilizzare il grafico stesso:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentazione

Manuale completo:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— guida introduttiva, istruzioni d'uso, i sei profili, modelli video, configurazione, riferimento API,
architettura.

**Base di conoscenza all'interno del repository** per LLM e collaboratori: [`kb/`](kb/README.md) — una
base di dati leggibile da macchina [`index.json`](kb/index.json) contenente informazioni sui singoli profili, grafici di riferimento eseguibili (`kb/workflows/*.json`, generati dagli stessi builder in modo che
non possano divergere) e provenienza dei nodi (`kb/nodes.json`). `python scripts/gen_kb.py`
la rigenera; la suite di test fallisce se il codice e la base di conoscenza non corrispondono.

## Sicurezza e ambito dei dati

- **Dati elaborati:** si connette a un'istanza ComfyUI locale o remota tramite HTTP/WebSocket.
Invia il JSON del flusso di lavoro e le immagini caricate, riceve i contenuti generati. Facoltativamente, si connette
a un'istanza Ollama locale per l'elaborazione dei prompt. Scrive i risultati in directory temporanee con
pulizia automatica.
- **Dati NON elaborati:** nessun telemetria, nessuna analisi, nessuna API esterna oltre gli endpoint ComfyUI e Ollama
che si configurano. I segreti sono mascherati in tutti gli output dei log tramite
`SecretValue`.
- **Autorizzazioni richieste:** accesso alla rete al server ComfyUI e, facoltativamente, al server Ollama; autorizzazione di scrittura per i file di output e le directory temporanee.
- **Caricamenti:** `upload_image` rifiuta i tentativi di attraversamento delle sottocartelle. I file caricati vengono salvati nella
directory di input di ComfyUI sul server specificato: trattare tale server come affidabile.

Per segnalare vulnerabilità, consultare [SECURITY.md](SECURITY.md).

## Valutazione

| Categoria | Punteggio |
|----------|-------|
| A. Sicurezza | 10/10 |
| B. Gestione degli errori | 10/10 |
| C. Documentazione per l'utente | 10/10 |
| D. Qualità del codice | 10/10 |
| E. Identità (soft) | 10/10 |
| **Overall** | **50/50** |

> Valutato con [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Argomenti correlati

Parte di [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — strumenti ML open source per
hardware locale.

## Contributi

Sono benvenuti problemi e richieste di pull: vedere [CONTRIBUTING.md](CONTRIBUTING.md). Aree utili:
famiglie di modelli aggiuntive, modelli di flusso di lavoro, documentazione, correzioni di bug.

Se si aggiunge un tipo di nodo, verificare innanzitutto che esista nel catalogo ComfyUI e dichiarare il suo
pacchetto se non è un elemento principale. Questa regola è la ragione per cui questa versione esiste.

## Licenza

MIT — vedere [LICENSE](LICENSE).

---

Creato da [MCP Tool Shop](https://mcp-tool-shop.github.io/)
