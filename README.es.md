<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## De qué se trata

comfy-headless crea **gráficos en formato ComfyUI API** y los ejecuta. Se llama a una función de Python; esta genera el gráfico de nodos JSON, lo envía a ComfyUI, espera a que se complete y te proporciona las rutas de salida.

Este enfoque es importante, ya que te indica qué puede salir mal. La función principal de la biblioteca es generar nombres de nodos y claves de entrada que el ComfyUI de destino realmente tenga. Cuando ComfyUI renombra o elimina un nodo, un gráfico que haga referencia al nombre antiguo se rechazará al enviarse, con un error opaco, y nada te advertirá de antemano.

**v3.0 es la versión que abordó este problema de manera seria.** Cada tipo de nodo que esta biblioteca genera fue auditado en relación con el catálogo activo de ComfyUI. Nueve ya no existían. Han desaparecido, los gráficos que los utilizaban se reconstruyen con nodos verificados y ahora la biblioteca puede indicarte qué falta en un servidor *antes* de que ejecutes un proceso en él.

**v3.1 extiende esta disciplina a seis perfiles de flujo de trabajo:** **Imagen, Video, 3D, Inferencia, Metadatos, Audio**, en una capa compartida de direccionamiento/tipado que utiliza las propias reglas de validación de ComfyUI: coincidencia de tipos de unión transcrita del validador del servidor, campos dinámicos combinados (`codec.encoding.crf`) y entradas condicionales que rechazan los valores de ramas inactivas en el momento de la construcción. La misma estructura que antes: los mallas, la música y los subtítulos se devuelven a través de `/history` + `/view` como todo lo demás.

| Problema | Qué hace comfy-headless |
|---------|--------------------------|
| La interfaz de nodo es bastante extensa | Preajustes y una API de Python limpia |
| La ingeniería de prompts es difícil | Mejora opcional con IA a través de Ollama local |
| La generación de video es complicada | 26 preajustes en 9 familias de modelos |
| "Necesito una malla de esta imagen" | `generate_3d()` — Hunyuan3D-2, todos los nodos principales |
| "Necesito música/pistas" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "¿Qué hay en esta imagen?" | `run_inference()` — subtítulo, etiqueta, detección, segmentación, OCR |
| "¿Qué gráfico generó este PNG?" | `extract_prompt_graph()` / `rerun_from_png()` |
| "¿Qué configuración debo usar?" | Recomendaciones adaptadas a tu VRAM |
| Los gráficos fallan con errores crípticos | La verificación de dependencias indica el nombre del nodo *y* del paquete |

## Inicio rápido

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` devuelve un `dict` con `success`, `prompt_id`, `images`, `error`, `seed` y `preset`. Cada llamada de generación en esta biblioteca devuelve un diccionario; no hay ningún objeto de resultado que se deba extraer.

## Instalación

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| Extras | Añade |
|-------|------|
| `ai` | Análisis y mejora de prompts a través de Ollama local |
| `websocket` | Progreso en tiempo real a través de WebSocket |
| `ui` | Interfaz web de Gradio |
| `health` | Monitoreo del estado del sistema |
| `validation` | Validación de configuración de Pydantic |
| `observability` | Trazado de OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Todo lo anterior |

Requiere **Python 3.10+** y una instancia de ComfyUI en ejecución.

Comprueba qué está activo en tiempo de ejecución:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## Imágenes

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

Ocho preajustes de imagen: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`.

Procesa por lotes una lista de prompts:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Mejora de prompts con IA

Requiere el extra `[ai]` y un Ollama local. Estas son **funciones a nivel de módulo**, no métodos de cliente:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (nuevo en la versión 3.1)

Qwen-Image-2512, de texto a imagen, se incluye como la plantilla `qwen_txt2img`, con la receta que realmente desea el modelo: ruta `UNETLoader`, 16 canales `EmptySD3LatentImage` (la latencia de SDXL produce resultados incorrectos en los modelos DiT), 20 pasos, **cfg 2.5**, desplazamiento 3.1, tamaño nativo 1328×1328:

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

Edición de instrucciones con hasta tres imágenes de referencia (Qwen-Image-Edit-2511):

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

Las referencias se introducen en `TextEncodeQwenImageEditPlus` como entradas `image1..image3` discretas y no pasan por VAEEncode, que es la forma del gráfico que realmente espera el nodo.

### ControlNet (nuevo en la versión 3.1)

Un único camino de código cubre la unión de Qwen y SDXL ControlNets:

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

Solo se emite el preprocesador principal `Canny` (`preprocess="canny"`); otros tipos de sugerencias esperan una imagen de control prefabricada, porque sus preprocesadores se encuentran en un paquete personalizado que esta biblioteca no requiere silenciosamente.

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

La selección se realiza **mediante un preajuste**, no por modelo; `generate_video` no tiene un argumento `model`. Cualquiera de `frames`, `fps`, `steps`, `cfg`, `width`, `height` se puede pasar para anular el preajuste.

### Entrada de imagen

El video de imagen a video, y cualquier otra cosa que utilice una imagen de origen, necesita que esa imagen exista primero dentro de ComfyUI. Cárgala y, a continuación, pasa el nombre que te proporcione el servidor:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Lee `name` de la respuesta en lugar de reutilizar el nombre de archivo que enviaste; ComfyUI cambia el nombre en caso de conflicto, por lo que los dos no siempre son iguales. `ref` es el mismo valor que ya se ha unido a cualquier subcarpeta, que es exactamente lo que necesita el gráfico.

> **Cambiado en la versión 3.0:** `init_image` es un nombre de archivo del lado del servidor. Las versiones anteriores aceptaban base64 y lo introducían a través de un nodo de terceros que no existe en una instalación estándar de ComfyUI. Consulta el [CAMBIOS](CHANGELOG.md).

> **Nuevo en la versión 3.1:** El video de imagen a video de Hunyuan 1.5 es real i2v: los preajustes `hunyuan15_i2v` y `hunyuan15_i2v_fast` se basan en el nodo principal `HunyuanVideo15ImageToVideo` y requieren un `init_image` (v3.0 creó silenciosamente un gráfico de video a partir de texto en su lugar). Y `output="core"` intercambia el terminador `VHS_VideoCombine` por el principal `CreateVideo → SaveVideo`, eliminando por completo la dependencia de Video Helper Suite.

### Familias de modelos

| Familia | VRAM mínima | Calidad | Velocidad | Nodos adicionales | Ideal para |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Excelente | Mediana | — | Bajo consumo de VRAM, eficiencia |
| AnimateDiff Lightning | 6 GB | Justo | Más rápido | AnimateDiff-Evolved | 4 pasos de borrador |
| AnimateDiff | 8 GB | Bueno | Rápido | AnimateDiff-Evolved, Interpolación de fotogramas | Previsualizaciones rápidas |
| **LTX-Video** | 12 GB | Excelente | Rápido | — | La opción segura por defecto |
| **Mochi** | 12 GB | Excelente | Lento | — | Cumplimiento del texto, clips largos |
| **SVD** | 12 GB | Bueno | Mediana | — | Animar una imagen estática |
| **Hunyuan 1.5** | 14 GB | El mejor | Lento | — | Calidad más alta |
| CogVideoX | 16 GB | Bueno | Lento | CogVideoX Wrapper | Legado |
| **Hunyuan 1.0** | 24 GB | Excelente | Lento | Interpolación de fotogramas | Reemplazado por 1.5 |

Seis de las nueve familias se ejecutan en **nodos centrales ComfyUI estándar**; no hay un paquete de "wrapper" para el modelo en sí. Solo AnimateDiff (ambas variantes) y CogVideoX lo necesitan. La salida de video utiliza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); la interpolación de fotogramas utiliza [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Las cifras de VRAM son el mínimo para la resolución predeterminada de esa familia, leídas desde `VIDEO_MODEL_INFO`; no son el máximo. Más memoria permite clips más largos y resoluciones más altas de la misma familia.

### Verifique antes de ejecutar

En lugar de descubrir un nodo faltante en el momento de la ejecución:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

También puede verificar los bordes de un gráfico con el servidor activo, utilizando la propia regla de aceptación del servidor (de modo que un `MESH` que alimenta una entrada de unión `FILE_3D_*` nunca sea un rechazo falso):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (nuevo en la versión 3.1)

Imagen a malla a través de **Hunyuan3D-2**; nodos centrales completamente ComfyUI, sin paquetes de "wrapper", sin nuevas rutas. Los archivos GLB se registran en `/history` exactamente como lo hace un archivo PNG y se descargan a través de `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` acepta una ruta local, bytes sin procesar, un diccionario `upload_image()` o una referencia del lado del servidor, y se carga automáticamente cuando sea necesario. Es una condición de imagen pura; no hay indicaciones de texto en el gráfico. Ajustes: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

Los modelos 3D con paquete de "wrapper" (TRELLIS, TripoSG, ...) no se generan deliberadamente; las dependencias nativas de ComfyUI-3D-Pack son las menos estables en el ecosistema.

## Audio (nuevo en la versión 3.1)

Texto a música a través de **ACE-Step 1.5**; código y pesos con licencia MIT, nodos centrales nativos, cero paquetes. El punto de control "turbo" se ejecuta en 8 pasos / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

El generador aplica la invariante de acoplamiento del modelo por usted: el `duration` del codificador y el `seconds` del latente son un parámetro lógico, que se controla desde un solo campo; el entorno de ejecución no los valida de forma cruzada, y una discrepancia se completa "correctamente" con una salida silenciosamente incorrecta. La salida pasa por `SaveAudioAdvanced` (el único nodo de guardado de audio no obsoleto); la salida `flac` no emite ningún campo de calidad, `mp3`/`opus` emiten el subcampo punteado `format.quality`.

Separación de pistas (requiere el paquete `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferencia (nuevo en la versión 3.1)

Llamadas de modelos no generativos; haga preguntas sobre una imagen en lugar de crear una. Se ejecuta en Florence-2 (paquete `comfyui-florence2`; la tarea de detección agrega `comfyui-segment-anything-2`):

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

La regla de carga del perfil: un resultado llega a `/history` solo a través de un nodo de salida. Cada gráfico de inferencia termina en el nodo central `SaveText` (que informa el texto en línea; no hay una segunda comunicación) o `SaveImage` para máscaras, y el generador se niega a generar un gráfico que se ejecute y no devuelva nada.

## Procedencia (nuevo en la versión 3.1)

ComfyUI incrusta el **gráfico exacto en formato API** en cada archivo PNG de salida. comfy-headless lo lee y puede volver a ejecutarlo textualmente:

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Escriba procedencia personalizada sin ningún nodo personalizado; cualquier cosa en `extra_pnginfo` se convierte en un fragmento de texto PNG en las salidas:

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Límites conocidos, documentados en lugar de ocultos: WebP/JPEG llevan los mismos datos en EXIF (una ruta de lector diferente, no implementada); las salidas de video no incrustan el gráfico; las implementaciones reforzadas pueden eliminar claves desconocidas; y la conversión de GUI a API no tiene una ruta de servidor; use "Workflow → Export (API)" de ComfyUI.

## Configuración

Las variables de entorno utilizan el prefijo `COMFY_HEADLESS_` con delimitadores de sección `__`:

| Variable | Valor predeterminado |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | tiempo de espera de lectura, segundos |
| `COMFY_HEADLESS_LOGGING__LEVEL` | nivel de registro |

O pase la URL directamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interfaz de usuario web

```bash
comfy-headless                 # launching the UI is the default action
```

| Indicador | Significado |
|------|---------|
| `--port` / `-p` | Puerto de la interfaz de usuario (predeterminado `7861`) |
| `--share` | Enlace público de Gradio |
| `--url` | URL del servidor ComfyUI |
| `--version` / `-v` | Imprimir versión |
| `--check` | Disponibilidad de funciones |
| `--diagnose` | Diagnósticos completos |

Seis pestañas: Imagen, Video, Cola e historial, Flujos de trabajo, Modelos, Configuración. El tema es Ocean Mist: suaves detalles en color aguamarina sobre fondos neutros cálidos.

De forma programática (requiere `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progreso

Las llamadas bloqueantes toman una función de devolución de llamada `on_progress`:

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

Para actualizaciones en tiempo real a través de WebSocket (requiere `[websocket]`):

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## Errores

Cada excepción contiene un código, mensaje y sugerencia estructurados:

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

## Cómo funciona

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

La biblioteca se comunica con siete rutas ComfyUI: `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view`, más `/upload/image` y `/upload/mask` para entrada binaria (las cargas de audio también se realizan a través de `/upload/image`; el servidor no tiene una ruta específica para audio). Los seis perfiles caben en esa superficie: v3.1 agregó mallas, música, subtítulos y procedencia sin agregar una sola ruta.

`/object_info` es la autoridad sobre lo que un servidor determinado puede ejecutar. Es un punto final activo, no un artefacto con versiones: no hay un registro de nodos centrales para fijar. Por lo tanto, la biblioteca valida los gráficos generados con el catálogo real del servidor de destino en lugar de asumir un conjunto fijo de nodos. `check_workflow_dependencies()` es esa verificación, y es una infraestructura fundamental en lugar de una comodidad.

Útiles vías de escape cuando desea el gráfico en sí:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentación

Manual completo: **[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**: introducción, uso, los seis perfiles, modelos de video, configuración, referencia de la API, arquitectura.

**Base de conocimientos en el repositorio** para LLM y colaboradores: [`kb/`](kb/README.md); una [`index.json`](kb/index.json) legible por máquina sobre páginas de hechos por perfil, gráficos de referencia ejecutables (`kb/workflows/*.json`, generados a partir de los propios generadores para que no puedan desviarse) y procedencia de nodos (`kb/nodes.json`). `python scripts/gen_kb.py` lo regenera; la suite de pruebas falla si el código y la base de conocimientos no coinciden.

## Seguridad y alcance de los datos

- **Datos accedidos:** se conecta a una instancia ComfyUI local o remota a través de HTTP/WebSocket.
Envía el JSON del flujo de trabajo y las imágenes cargadas, y recibe los archivos multimedia generados. Opcionalmente, se conecta a un Ollama local para obtener inteligencia en las indicaciones. Escribe la salida en directorios temporales con limpieza automática.
- **Datos NO accedidos:** no hay telemetría, ni análisis, ni API externas más allá de los puntos finales ComfyUI y Ollama que configure. Los secretos se enmascaran en toda la salida del registro mediante `SecretValue`.
- **Permisos requeridos:** acceso a la red a su servidor ComfyUI y, opcionalmente, al servidor Ollama; permiso de escritura de archivos para la salida y los directorios temporales.
- **Cargas:** `upload_image` rechaza los intentos de acceder a subcarpetas. Los archivos cargados se guardan en el directorio de entrada de ComfyUI en el servidor que se especifique; trate ese servidor como de confianza.

Consulte [SECURITY.md](SECURITY.md) para informar sobre vulnerabilidades.

## Evaluación

| Categoría | Puntuación |
|----------|-------|
| A. Seguridad | 10/10 |
| B. Manejo de errores | 10/10 |
| C. Documentación para operadores | 10/10 |
| D. Buenas prácticas de desarrollo | 10/10 |
| E. Identidad (suave) | 10/10 |
| **Overall** | **50/50** |

> Evaluado con [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Relacionado

Parte de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/): herramientas de código abierto para el aprendizaje automático (ML) para hardware local.

## Contribuciones

Se aceptan problemas y solicitudes de incorporación de código; consulte [CONTRIBUTING.md](CONTRIBUTING.md). Áreas útiles: familias de modelos adicionales, plantillas de flujo de trabajo, documentación, corrección de errores.

Si agrega un tipo de nodo, primero verifique que exista en el catálogo ComfyUI activo y declare su paquete si no es un componente principal. Esa regla es la razón por la que existe esta versión.

## Licencia

MIT: consulte [LICENSE](LICENSE).

---

Creado por [MCP Tool Shop](https://mcp-tool-shop.github.io/)
