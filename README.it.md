<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.md">English</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Comanda ComfyUI con Python. Niente più grafici complessi.</strong>
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

Questa impostazione è importante perché indica cosa potrebbe andare storto. L'obiettivo principale della libreria è generare nomi di nodi e chiavi di input che siano effettivamente presenti in ComfyUI. Quando ComfyUI rinomina o elimina un nodo, un grafo che fa riferimento al nome precedente viene rifiutato all'invio con un errore non chiaro, senza alcun avviso preventivo.

**La versione 3.0 ha affrontato seriamente questo problema.** Ogni tipo di nodo generato da questa libreria è stato verificato rispetto al catalogo ComfyUI attivo. Nove nodi non esistevano più. Sono stati rimossi, i grafi che li utilizzavano sono stati ricostruiti utilizzando nodi verificati e la libreria ora può indicare quali elementi mancano in un server *prima* di avviare l'esecuzione.

| Problema | Cosa fa comfy-headless |
|---------|--------------------------|
| L'interfaccia dei nodi è piuttosto complessa | Preset e API Python pulita |
| L'ingegneria del prompt è difficile | Miglioramento opzionale tramite AI locale con Ollama |
| La generazione di video richiede attenzione | 24 preset su 9 famiglie di modelli |
| "Quali impostazioni devo usare?" | Raccomandazioni adattate alla VRAM disponibile |
| I grafi falliscono con errori criptici | Il controllo delle dipendenze indica il nome del nodo *e* del pacchetto |

## Guida rapida

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
| `ai` | Analisi e miglioramento del prompt tramite Ollama locale |
| `websocket` | Progresso in tempo reale tramite WebSocket |
| `ui` | Interfaccia web Gradio |
| `health` | Monitoraggio dello stato del sistema |
| `validation` | Validazione della configurazione Pydantic |
| `observability` | Tracciamento OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Tutto quanto sopra |

Richiede **Python 3.10+** e un'istanza ComfyUI in esecuzione.

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

Richiede l'extra `[ai]` e Ollama locale. Queste sono **funzioni a livello di modulo**, non metodi client:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## Video

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

La selezione avviene **tramite preset**, non tramite modello; `generate_video` non ha un argomento `model`. Uno qualsiasi tra `frames`, `fps`, `steps`, `cfg`, `width`, `height` può essere passato per sovrascrivere il preset.

### Input immagine

Per la conversione da immagine a video e per qualsiasi altra operazione che utilizzi un'immagine di origine, è necessario che tale immagine sia presente in ComfyUI. Caricala, quindi passa il nome restituito dal server:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Leggi `name` dalla risposta anziché riutilizzare il nome del file inviato; ComfyUI rinomina i file in caso di conflitto, quindi i due non sono sempre uguali. `ref` è lo stesso valore già unito a qualsiasi sottocartella, che è esattamente ciò di cui ha bisogno il grafo.

> **Modificato nella versione 3.0:** `init_image` è un nome file lato server. Le versioni precedenti accettavano dati base64 e li passavano tramite un nodo di terze parti che non esiste in un'installazione standard di ComfyUI. Consulta il [CHANGELOG](CHANGELOG.md).

### Famiglie di modelli

| Famiglia | VRAM minima | Qualità | Velocità | Nodi extra | Ideale per |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Ottimo | Medio | — | Bassa VRAM, efficienza |
| AnimateDiff Lightning | 6 GB | Discreto | Più veloce | AnimateDiff-Evolved | Bozze a 4 passaggi |
| AnimateDiff | 8 GB | Buono | Veloce | AnimateDiff-Evolved, Frame Interp. | Anteprime rapide |
| **LTX-Video** | 12 GB | Eccellente | Veloce | — | L'impostazione predefinita più sicura |
| **Mochi** | 12 GB | Eccellente | Lento | — | Aderenza al testo, clip lunghe |
| **SVD** | 12 GB | Buono | Medio | — | Animazione di un'immagine statica |
| **Hunyuan 1.5** | 14 GB | Il migliore | Lento | — | Massima qualità |
| CogVideoX | 16 GB | Buono | Lento | Wrapper CogVideoX | Legacy |
| **Hunyuan 1.0** | 24 GB | Ottimo | Lento | Interpolazione dei fotogrammi | Sostituito dalla versione 1.5 |

Sei delle nove famiglie funzionano con i **nodi principali standard di ComfyUI**, senza pacchetti aggiuntivi per il modello stesso. Solo AnimateDiff (entrambe le varianti) e CogVideoX ne richiedono uno. L'output video utilizza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); l'interpolazione dei fotogrammi utilizza [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

I valori di VRAM sono il minimo per la risoluzione predefinita di ciascuna famiglia, letti da `VIDEO_MODEL_INFO`; non rappresentano il massimo. Più memoria consente clip più lunghe e risoluzioni più elevate dalla stessa famiglia.

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

## Configurazione

Le variabili d'ambiente utilizzano il prefisso `COMFY_HEADLESS_` con delimitatori di sezione `__`:

| Variabile | Predefinito |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | timeout di lettura, secondi |
| `COMFY_HEADLESS_LOGGING__LEVEL` | livello di log |

Oppure passa l'URL direttamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interfaccia web

```bash
comfy-headless                 # launching the UI is the default action
```

| Flag | Significato |
|------|---------|
| `--port` / `-p` | Porta dell'interfaccia utente (predefinita `7861`) |
| `--share` | Link di condivisione pubblico Gradio |
| `--url` | URL del server ComfyUI |
| `--version` / `-v` | Stampa la versione |
| `--check` | Disponibilità delle funzionalità |
| `--diagnose` | Diagnostica completa |

Sei schede: Immagine, Video, Coda e Cronologia, Flussi di lavoro, Modelli, Impostazioni. Il tema è Ocean Mist —
toni tenui color acquamarina su sfondi neutri caldi.

A livello programmatico (richiede `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progresso

Le chiamate bloccanti richiedono una funzione di callback `on_progress`:

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

La libreria comunica con sette endpoint ComfyUI — `/system_stats`, `/object_info`, `/queue`,
`/history`, `/prompt`, `/interrupt`, `/view` — più `/upload/image` e `/upload/mask` per
input binari.

`/object_info` è l'autorità su ciò che un determinato server può eseguire. È un endpoint attivo, non
un artefatto con versioni: non esiste un registro di nodi principali a cui fare riferimento. Pertanto, la libreria
valida i grafici generati rispetto al catalogo effettivo del server di destinazione anziché presupporre un
set di nodi fisso. `check_workflow_dependencies()` è tale controllo ed è un'infrastruttura essenziale piuttosto che una comodità.

Utili "uscite di emergenza" quando si desidera il grafico stesso:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentazione

Manuale completo:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— introduzione, utilizzo, configurazione, riferimento API, modelli video, architettura.

## Sicurezza e ambito dei dati

- **Dati interessati:** si connette a un'istanza ComfyUI locale o remota tramite HTTP/WebSocket.
Invia il JSON del flusso di lavoro e le immagini caricate, riceve i media generati. Facoltativamente, si connette
a un'istanza Ollama locale per l'intelligenza dei prompt. Scrive l'output in directory temporanee con
pulizia automatica.
- **Dati NON interessati:** nessun telemetria, nessuna analisi, nessuna API esterna oltre agli endpoint ComfyUI e Ollama
che si configurano. I segreti sono mascherati in tutti gli output dei log tramite `SecretValue`.
- **Autorizzazioni richieste:** accesso alla rete al server ComfyUI e al server Ollama opzionale; autorizzazione di scrittura per l'output e le directory temporanee.
- **Caricamenti:** `upload_image` rifiuta i tentativi di attraversamento delle sottocartelle. I file caricati vengono inseriti
nella directory di input di ComfyUI sul server a cui si fa riferimento: trattare tale server come affidabile.

Consultare [SECURITY.md](SECURITY.md) per la segnalazione di vulnerabilità.

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

Se si aggiunge un tipo di nodo, verificare innanzitutto che esista nel catalogo ComfyUI attivo e dichiarare il suo
pacchetto se non è un nodo principale. Questa regola è la ragione per cui esiste questa versione.

## Licenza

MIT — vedere [LICENSE](LICENSE).

---

Creato da [MCP Tool Shop](https://mcp-tool-shop.github.io/)
