<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## De qué se trata esto

comfy-headless crea **gráficos en formato de API de ComfyUI** y los ejecuta. Se llama a una función de Python; esta emite el gráfico de nodos JSON, lo envía a ComfyUI mediante POST, verifica si se completó y te proporciona las rutas de salida.

Esta forma de plantearlo es importante, ya que indica qué puede salir mal. La tarea principal de la biblioteca consiste en emitir los nombres de los nodos y las claves de entrada que realmente tiene el ComfyUI objetivo. Cuando ComfyUI cambia el nombre o elimina un nodo, se rechaza un gráfico que hace referencia al nombre antiguo al enviarse, generando un error opaco, y nada te advierte con anticipación.

**La versión 3.0 es la que abordó este problema de manera seria.** Se revisó cada tipo de nodo que emite esta biblioteca en relación con el catálogo activo de ComfyUI. Nueve ya no existían. Han desaparecido, los gráficos que los utilizaban se reconstruyen sobre nodos verificados y ahora la biblioteca puede indicarte qué le falta a un servidor *antes* de que ejecutes una tarea en él.

**La versión 3.1 extiende esta disciplina a seis perfiles de flujo de trabajo:** **Imagen, Video, 3D, Inferencia, Metadatos, Audio**, en una capa compartida de direccionamiento/tipado que utiliza las propias reglas de validación de ComfyUI: coincidencia de tipos de unión transcrita del validador del servidor, campos dinámicos con puntos (`codec.encoding.crf`) y entradas condicionales que rechazan los valores de ramas inactivas en el momento de la construcción. La misma estructura que antes: las mallas, la música y los subtítulos se devuelven a través de `/history` + `/view` como todo lo demás.

| Problema | Qué hace comfy-headless |
|---------|--------------------------|
| La interfaz del nodo es bastante extensa | Preajustes y una API de Python limpia |
| La ingeniería de prompts es difícil | Mejora opcional con IA mediante Ollama local |
| La generación de video es complicada | 26 preajustes en 9 familias de modelos |
| "Necesito una malla a partir de esta imagen" | `generate_3d()`: Hunyuan3D-2, todos los nodos principales |
| "Necesito música/pistas" | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| "¿Qué hay en esta imagen?" | `run_inference()`: subtítulo, etiqueta, detección, segmentación, OCR |
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
| `ai` | Análisis y mejora de prompts mediante Ollama local |
| `websocket` | Progreso en tiempo real a través de WebSocket |
| `ui` | Interfaz web Gradio |
| `health` | Monitoreo del estado del sistema |
| `validation` | Validación de configuración con Pydantic |
| `observability` | Trazado con OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Todo lo anterior |

Requiere **Python 3.10+** y una instancia de ComfyUI en ejecución.

Verifica qué está activo en tiempo de ejecución:

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

Requiere el extra `[ai]` y un Ollama local. Estas son **funciones a nivel de módulo**, no métodos del cliente:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (nuevo en la versión 3.1)

Qwen-Image-2512, conversión de texto a imagen, se incluye como plantilla `qwen_txt2img`, con la receta que realmente desea el modelo integrada: ruta `UNETLoader`, 16 canales `EmptySD3LatentImage` (la salida latente de SDXL produce resultados incorrectos en los modelos DiT), pasos 20, **cfg 2.5**, desplazamiento 3.1, tamaño nativo 1328×1328:

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

Las referencias se alimentan a `TextEncodeQwenImageEditPlus` como entradas discretas `image1..image3` y no pasan por VAEEncode; esta es la forma del gráfico que realmente espera el nodo.

### ControlNet (nuevo en la versión 3.1)

Un único camino de código cubre los ControlNets de Qwen y SDXL:

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

Solo se emite el preprocesador principal `Canny` (`preprocess="canny"`); otros tipos de indicaciones esperan una imagen de control ya creada, porque sus preprocesadores están en un paquete personalizado que esta biblioteca no requiere silenciosamente.

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

La selección se realiza **mediante un preajuste**, no por modelo; `generate_video` no tiene ningún argumento `model`. Cualquiera de los siguientes: `frames`, `fps`, `steps`, `cfg`, `width`, `height` puede pasarse para anular el preajuste.

### Entrada de imagen

La conversión de imagen a video y cualquier otra cosa que utilice una imagen de origen necesita que esa imagen exista primero dentro de ComfyUI. Cárgala y, luego, pasa el nombre que te devuelve el servidor:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Lee `name` desde la respuesta en lugar de reutilizar el nombre del archivo que enviaste; ComfyUI cambia los nombres si hay una colisión, por lo que ambos no siempre son iguales. `ref` es el mismo valor que ya se unió con cualquier subcarpeta, que es exactamente lo que necesita el gráfico.

> **Cambio en la versión 3.0:** `init_image` es un nombre de archivo del lado del servidor. Las versiones anteriores aceptaban datos base64 y los introducían a través de un nodo de terceros que no existe en una instalación estándar de ComfyUI. Consulta el [ARCHIVO DE CAMBIOS](CHANGELOG.md).

> **Nuevo en la versión 3.1:** La conversión de imagen a video de Hunyuan 1.5 es una verdadera i2v; los preajustes `hunyuan15_i2v` y `hunyuan15_i2v_fast` se basan en el nodo principal `HunyuanVideo15ImageToVideo` y requieren un `init_image` (la versión 3.0 creó silenciosamente un gráfico de texto a video). Y `output="core"` intercambia el terminador `VHS_VideoCombine` por el núcleo `CreateVideo → SaveVideo`, eliminando por completo la dependencia del Video Helper Suite.

### Familias de modelos

| Familia | VRAM mínima | Calidad | Velocidad | Nodos adicionales | Ideal para |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Excelente | Mediana | — | Bajo consumo de VRAM, eficiencia |
| AnimateDiff Lightning | 6 GB | Justo | Más rápido | AnimateDiff-Evolved | Borradores de 4 pasos |
| AnimateDiff | 8 GB | Bueno | Rápido | AnimateDiff-Evolved, Interpolación de fotogramas. | Previsualizaciones rápidas |
| **LTX-Video** | 12 GB | Excelente | Rápido | — | La opción predeterminada segura |
| **Mochi** | 12 GB | Excelente | Lento | — | Adherencia al texto, clips largos |
| **SVD** | 12 GB | Bueno | Mediana | — | Animando una imagen estática |
| **Hunyuan 1.5** | 14 GB | El mejor | Lento | — | La máxima calidad |
| CogVideoX | 16 GB | Bueno | Lento | Wrapper de CogVideoX | Legado |
| **Hunyuan 1.0** | 24 GB | Excelente | Lento | Interpolación de fotogramas | Reemplazado por la versión 1.5 |

Seis de las nueve familias se ejecutan con los **nodos centrales estándar de ComfyUI**, sin paquetes adicionales para el modelo en sí. Solo AnimateDiff (ambas variantes) y CogVideoX necesitan uno. La salida de video utiliza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); la interpolación de fotogramas utiliza [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Las cifras de VRAM son el mínimo para la resolución predeterminada de cada familia, obtenidas de `VIDEO_MODEL_INFO`; no son valores máximos. Más memoria permite clips más largos y resoluciones más altas dentro de la misma familia.

### Compruebe antes de ejecutar

En lugar de descubrir un nodo faltante al momento de enviar:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

También puede verificar los bordes de un gráfico con el servidor en tiempo real, utilizando la propia regla de aceptación del servidor (de modo que una entrada `MESH` alimentando una unión `FILE_3D_*` nunca sea un rechazo falso):

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (nuevo en la versión 3.1)

Imagen a malla mediante **Hunyuan3D-2**: totalmente con nodos centrales de ComfyUI, sin paquetes adicionales ni nuevas rutas. El archivo GLB se registra en `/history` exactamente como lo haría un PNG y se descarga a través de `/view`:

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` acepta una ruta local, bytes brutos, un diccionario `upload_image()` o una referencia del lado del servidor, y se carga automáticamente cuando sea necesario. Es pura condicionamiento de imagen; no hay indicaciones de texto en el gráfico. Ajustes: `steps` (30), `cfg` (5.5), `octree_resolution` (256), `threshold` (0.6), `seed`.

Los modelos 3D con paquetes adicionales (TRELLIS, TripoSG, ...) no se incluyen deliberadamente; las dependencias nativas de ComfyUI-3D-Pack son las menos estables del ecosistema.

## Audio (nuevo en la versión 3.1)

Texto a música mediante **ACE-Step 1.5**: código y pesos con licencia MIT, nodos centrales nativos, cero paquetes adicionales. El punto de control turbo se ejecuta en 8 pasos / cfg 1:

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

El constructor aplica la invariante de acoplamiento del modelo por usted: el `duration` del codificador y el `seconds` del latente son un parámetro lógico, que se deriva de un solo campo; el entorno de ejecución no los valida cruzadamente, y una discrepancia se completa "correctamente" con una salida silenciosamente incorrecta. La salida pasa a través de `SaveAudioAdvanced` (el único nodo de guardado de audio que no está en desuso); la salida `flac` no emite ningún campo de calidad, `mp3`/`opus` emiten el subcampo punteado `format.quality`.

Separación de pistas (requiere el paquete `audio-separation-nodes-comfyui`):

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inferencia (nuevo en la versión 3.1)

Llamadas a modelos no generativos: haga preguntas sobre una imagen en lugar de crear una. Se ejecuta con Florence-2 (paquete `comfyui-florence2`; la tarea de detección agrega `comfyui-segment-anything-2`):

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

La regla fundamental del perfil: un resultado llega a `/history` solo a través de un nodo de salida. Cada gráfico de inferencia termina en los nodos centrales `SaveText` (que informa el texto en línea, sin una segunda comunicación) o `SaveImage` para máscaras, y el constructor se niega a emitir un gráfico que se ejecute correctamente y no devuelva nada.

## Procedencia (nuevo en la versión 3.1)

ComfyUI incrusta el **formato de gráfico API exacto** en cada PNG de salida. comfy-headless lo lee nuevamente, utilizando solo stdlib, sin Pillow, y puede volver a ejecutarlo textualmente:

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

Límites conocidos, documentados en lugar de ocultos: WebP/JPEG contienen los mismos datos en EXIF (una ruta de lector diferente, no implementada); las salidas de video no incrustan el gráfico; las implementaciones reforzadas pueden eliminar claves desconocidas; y la conversión de GUI a API no tiene una ruta del servidor; utilice "Flujo de trabajo → Exportar (API)" de ComfyUI.

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

| Bandera | Significado |
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

La biblioteca se comunica con siete rutas de ComfyUI: `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view`, además de `/upload/image` y `/upload/mask` para entrada binaria (las cargas de audio también utilizan `/upload/image`; el servidor no tiene una ruta específica para audio). Las seis perfiles se ajustan a esa superficie: la versión 3.1 agregó mallas, música, subtítulos y procedencia sin agregar una sola ruta.

`/object_info` es la autoridad sobre lo que un servidor determinado puede ejecutar. Es un punto final activo, no un artefacto con versiones: no hay un registro de nodos centrales para fijar. Por lo tanto, la biblioteca valida los gráficos emitidos en función del catálogo real del servidor de destino en lugar de asumir un conjunto fijo de nodos. `check_workflow_dependencies()` es esa verificación y es una infraestructura fundamental en lugar de una comodidad.

Formas útiles de acceder al gráfico en sí:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentación

Manual completo:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— introducción, uso, los seis perfiles, modelos de video, configuración, referencia de la API,
arquitectura.

**Base de conocimientos dentro del repositorio** para LLM y colaboradores: [`kb/`](kb/README.md) — una
base de datos legible por máquina [`index.json`](kb/index.json) con páginas de hechos por perfil, gráficos de referencia ejecutables (`kb/workflows/*.json`, generados a partir de los propios constructores para que
no cambien), y procedencia de nodos (`kb/nodes.json`). `python scripts/gen_kb.py`
lo regenera; la suite de pruebas falla si el código y la base de conocimientos no coinciden.

## Seguridad y alcance de los datos

- **Datos accedidos:** se conecta a una instancia local o remota de ComfyUI a través de HTTP/WebSocket.
Envía el JSON del flujo de trabajo y las imágenes cargadas, recibe los medios generados. Opcionalmente, se conecta
a un Ollama local para la inteligencia de los mensajes. Escribe la salida en directorios temporales con
limpieza automática.
- **Datos NO accedidos:** no hay telemetría, ni análisis, ni API externas más allá de los puntos finales de ComfyUI
y Ollama que configure. Los secretos están ocultos en toda la salida del registro a través de
`SecretValue`.
- **Permisos requeridos:** acceso a la red al servidor de ComfyUI y, opcionalmente, al servidor de Ollama; permiso de escritura de archivos para la salida y los directorios temporales.
- **Cargas:** `upload_image` rechaza los intentos de recorrer subcarpetas. Los archivos cargados se guardan en
el directorio de entrada de ComfyUI en el servidor que especifique; trate ese servidor como
de confianza.

Consulte [SECURITY.md](SECURITY.md) para informar sobre vulnerabilidades.

## Evaluación

| Categoría | Puntuación |
|----------|-------|
| A. Seguridad | 10/10 |
| B. Manejo de errores | 10/10 |
| C. Documentación del operador | 10/10 |
| D. Buenas prácticas de desarrollo | 10/10 |
| E. Identidad (suave) | 10/10 |
| **Overall** | **50/50** |

> Evaluado con [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Relacionado

Parte de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — herramientas de código abierto para el aprendizaje automático
para hardware local.

## Contribuciones

Se aceptan problemas y solicitudes de incorporación de cambios; consulte [CONTRIBUTING.md](CONTRIBUTING.md). Áreas útiles:
familias de modelos adicionales, plantillas de flujo de trabajo, documentación, corrección de errores.

Si agrega un tipo de nodo, primero verifique que exista en el catálogo activo de ComfyUI y declare su
paquete si no es un componente básico. Esa regla es la razón por la que existe esta versión.

## Licencia

MIT — consulte [LICENSE](LICENSE).

---

Creado por [MCP Tool Shop](https://mcp-tool-shop.github.io/)
