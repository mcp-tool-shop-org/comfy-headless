<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.md">English</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Controla ComfyUI desde Python. Olvídate de los diagramas de nodos.</strong>
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

comfy-headless crea **gráficos en formato de API de ComfyUI** y los ejecuta. Se llama a una función de Python; esta genera el gráfico de nodos JSON, lo envía a ComfyUI mediante POST, verifica si la operación se completó y te proporciona las rutas de salida.

Esta formulación es importante porque indica qué puede salir mal. La tarea principal de la biblioteca consiste en generar los nombres de los nodos y las claves de entrada que realmente tiene el ComfyUI de destino. Cuando ComfyUI cambia el nombre o elimina un nodo, se rechaza un gráfico que hace referencia al nombre antiguo al enviarlo, generando un error opaco; además, no se te advierte previamente.

**La versión 3.0 es la que abordó este problema de manera seria.** Se revisó cada tipo de nodo que genera esta biblioteca en relación con el catálogo activo de ComfyUI. Nueve ya no existían. Han desaparecido, los gráficos que los utilizaban se reconstruyen sobre nodos verificados y ahora la biblioteca puede indicarte qué falta en un servidor *antes* de que ejecutes una tarea.

| Problema | Qué hace comfy-headless |
|---------|--------------------------|
| La interfaz del nodo es bastante extensa | Preajustes y una API de Python limpia |
| El diseño de prompts es complicado | Mejora opcional con IA mediante Ollama local |
| La generación de video requiere ajustes finos | 24 preajustes en 9 familias de modelos |
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

Ocho preajustes de imagen: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic` y `square`.

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

La selección se realiza **por preajuste**, no por modelo; `generate_video` no tiene ningún argumento `model`. Cualquiera de los siguientes: `frames`, `fps`, `steps`, `cfg`, `width` o `height` puede pasarse para anular el preajuste.

### Entrada de imagen

La conversión de imagen a video y cualquier otra operación que utilice una imagen de origen requiere que esa imagen exista primero dentro de ComfyUI. Cárgala y luego pasa el nombre que te devuelve el servidor:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Lee `name` desde la respuesta en lugar de reutilizar el nombre del archivo que enviaste; ComfyUI cambia el nombre si hay una colisión, por lo que los dos no siempre son iguales. `ref` es el mismo valor que ya se ha unido a cualquier subcarpeta, que es exactamente lo que necesita el gráfico.

> **Cambiado en la versión 3.0:** `init_image` es un nombre de archivo del lado del servidor. Las versiones anteriores aceptaban datos base64 y los transmitían a través de un nodo de terceros que no existe en una instalación estándar de ComfyUI. Consulta el [ARCHIVO DE CAMBIOS](CHANGELOG.md).

### Familias de modelos

| Familia | VRAM mínima | Calidad | Velocidad | Nodos adicionales | Ideal para |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | Excelente | Mediana | — | Bajo consumo de VRAM, eficiencia |
| AnimateDiff Lightning | 6 GB | Justa | Más rápida | AnimateDiff-Evolved | Borradores de 4 pasos |
| AnimateDiff | 8 GB | Buena | Rápida | AnimateDiff-Evolved, interpolación de fotogramas. | Previsualizaciones rápidas |
| **LTX-Video** | 12 GB | Excelente | Rápida | — | La opción predeterminada segura |
| **Mochi** | 12 GB | Excelente | Lenta | — | Adherencia al texto, clips largos |
| **SVD** | 12 GB | Buena | Mediana | — | Animación de una imagen fija |
| **Hunyuan 1.5** | 14 GB | La mejor | Lenta | — | Mayor calidad |
| CogVideoX | 16 GB | Buena | Lenta | Wrapper de CogVideoX | Legado |
| **Hunyuan 1.0** | 24 GB | Excelente | Lenta | Interpolación de fotogramas | Reemplazada por la versión 1.5 |

Seis de las nueve familias se ejecutan en **los nodos principales estándar de ComfyUI**, sin ningún paquete wrapper para el modelo en sí. Solo AnimateDiff (ambas variantes) y CogVideoX necesitan uno. La salida de video utiliza [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite); la interpolación de fotogramas utiliza
[Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Las cifras de VRAM son el mínimo para la resolución predeterminada de esa familia, obtenidas de `VIDEO_MODEL_INFO`; no son valores máximos. Más memoria permite obtener clips más largos y resoluciones más altas de la misma familia.

### Verifica antes de ejecutar

En lugar de descubrir un nodo faltante en el momento del envío:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## Configuración

Las variables de entorno utilizan el prefijo `COMFY_HEADLESS_` con delimitadores de sección `__`:

| Variable | Valor predeterminado |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | tiempo de espera para la lectura, en segundos |
| `COMFY_HEADLESS_LOGGING__LEVEL` | nivel de registro |

O pasa la URL directamente: `ComfyClient("http://192.168.1.50:8188")`.

## Interfaz web

```bash
comfy-headless                 # launching the UI is the default action
```

| Indicador | Significado |
|------|---------|
| `--port` / `-p` | Puerto de la interfaz de usuario (predeterminado: `7861`) |
| `--share` | Enlace público para compartir Gradio |
| `--url` | URL del servidor ComfyUI |
| `--version` / `-v` | Imprimir versión |
| `--check` | Disponibilidad de funciones |
| `--diagnose` | Diagnósticos completos |

Seis pestañas: Imagen, Video, Cola e Historial, Flujos de trabajo, Modelos, Configuración. El tema es Ocean Mist —
tonos suaves color aguamarina sobre fondos neutros cálidos.

De forma programática (requiere `[ui]`):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progreso

Las llamadas bloqueantes requieren una función de devolución de llamada `on_progress`:

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

La biblioteca se comunica con siete rutas de ComfyUI — `/system_stats`, `/object_info`, `/queue`,
`/history`, `/prompt`, `/interrupt`, `/view` — más `/upload/image` y `/upload/mask` para
entrada binaria.

`/object_info` es la autoridad sobre lo que puede ejecutar un servidor determinado. Es un punto final activo, no
un artefacto con versiones: no hay un registro de nodos centrales al que hacer referencia. Por lo tanto, la biblioteca
valida los gráficos emitidos en función del catálogo real del servidor de destino en lugar de asumir un
conjunto fijo de nodos. `check_workflow_dependencies()` es esa comprobación y constituye una infraestructura esencial en lugar de una simple herramienta.

Opciones útiles cuando se necesita el gráfico en sí:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentación

Manual completo:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)**
— introducción, uso, configuración, referencia de la API, modelos de video, arquitectura.

## Seguridad y alcance de los datos

- **Datos afectados:** se conecta a una instancia local o remota de ComfyUI a través de HTTP/WebSocket.
Envía el JSON del flujo de trabajo y las imágenes cargadas, recibe los medios generados. Opcionalmente, se conecta
a un Ollama local para la inteligencia del mensaje. Escribe la salida en directorios temporales con
limpieza automática.
- **Datos NO afectados:** no hay telemetría, ni análisis, ni API externas más allá de los puntos finales de ComfyUI
y Ollama que configure. Los secretos se ocultan en toda la salida del registro mediante
`SecretValue`.
- **Permisos requeridos:** acceso a la red al servidor de ComfyUI y al servidor de Ollama opcional; escritura de archivos para la salida y los directorios temporales.
- **Cargas:** `upload_image` rechaza los intentos de atravesar subcarpetas. Los archivos cargados se guardan en
el directorio de entrada de ComfyUI en el servidor que especifique; trate ese servidor como
de confianza.

Consulte [SECURITY.md](SECURITY.md) para informar sobre vulnerabilidades.

## Evaluación

| Categoría | Puntuación |
|----------|-------|
| A. Seguridad | 10/10 |
| B. Manejo de errores | 10/10 |
| C. Documentación para el usuario | 10/10 |
| D. Buenas prácticas de desarrollo | 10/10 |
| E. Identidad (suave) | 10/10 |
| **Overall** | **50/50** |

> Evaluado con [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Relacionado

Parte de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — herramientas de código abierto para el aprendizaje automático en
hardware local.

## Contribución

Se aceptan problemas y solicitudes de incorporación de cambios; consulte [CONTRIBUTING.md](CONTRIBUTING.md). Áreas útiles:
familias de modelos adicionales, plantillas de flujo de trabajo, documentación, corrección de errores.

Si agrega un tipo de nodo, primero verifique que exista en el catálogo activo de ComfyUI y declare su
paquete si no es un nodo central. Esa regla es la razón por la que existe esta versión.

## Licencia

MIT — consulte [LICENSE](LICENSE).

---

Creado por [MCP Tool Shop](https://mcp-tool-shop.github.io/)
