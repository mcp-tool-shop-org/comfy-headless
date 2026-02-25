<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# आरामदायक, बिना सिर वाला

"कोम्फीयूआई की शक्ति को आसान तरीके से उपलब्ध कराना, ताकि इसकी जटिलताओं को कम किया जा सके।"

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## "कॉम्फी हेडलेस" क्यों?

| समस्या। | समाधान। |
| ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। | ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। |
| कॉम्फीयूआई का नोड इंटरफ़ेस बहुत जटिल है। | सरल पूर्व-निर्धारित सेटिंग्स और एक स्पष्ट पायथन एपीआई। |
| "प्रॉम्प्ट इंजीनियरिंग एक जटिल काम है।" | एआई-आधारित संकेत (प्रॉम्प्ट) को बेहतर बनाने की तकनीक। |
| वीडियो बनाना एक जटिल प्रक्रिया है। | एक पंक्ति वाला वीडियो, जिसमें मॉडल के लिए पहले से निर्धारित सेटिंग्स उपलब्ध हैं। |
| मुझे नहीं पता कि कौन से सेटिंग्स (विकल्प) इस्तेमाल करने हैं। | आपके इरादे के लिए सबसे उपयुक्त सेटिंग्स, स्वचालित रूप से। |

## शुरुआत कैसे करें।

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## दर्शनशास्त्र।

- **उपयोगकर्ताओं के लिए:** सरल पूर्व-निर्धारित सेटिंग्स और एआई-संचालित संकेत अनुकूलन।
- **डेवलपर्स के लिए:** स्वच्छ एपीआई (API) और टेम्पलेट-आधारित वर्कफ़्लो संकलन।
- **सभी के लिए:** आपकी आवश्यकताओं के अनुसार सर्वोत्तम सेटिंग्स, जो स्वचालित रूप से लागू हो जाएंगी।

## स्थापना।

### मॉड्यूलर इंस्टॉलेशन (संस्करण 2.5.0 और उसके बाद के संस्करणों में)

केवल वही चीजें स्थापित करें जिनकी आपको आवश्यकता है:

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

### उपलब्ध अतिरिक्त सुविधाएँ।

| Extra | निर्भरताएँ। | विशेषताएं। |
| "The company is committed to providing high-quality products and services."

अनुवाद:

"कंपनी उच्च गुणवत्ता वाले उत्पाद और सेवाएं प्रदान करने के लिए प्रतिबद्ध है।" | ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। | ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। |
| `ai` | httpx | ओलामा: प्रॉम्प्ट इंटेलिजेंस (Ollama: प्रॉम्प्ट इंटेलिजेंस) |
| `websocket` | वेब सॉकेट। | वास्तविक समय में प्रगति की जानकारी। |
| `health` | psutil एक पायथन लाइब्रेरी है जो सिस्टम की जानकारी और संसाधनों को प्रबंधित करने में मदद करती है। | सिस्टम की स्वास्थ्य निगरानी। |
| `ui` | ग्रैडियो | वेब इंटरफेस। |
| `validation` | पायडैंटिक। | कॉन्फ़िगरेशन की वैधता की जांच। |
| `observability` | ओपनटेलमेट्री (OpenTelemetry) | वितरित ट्रेसिंग। |
| `standard` | एआई (कृत्रिम बुद्धिमत्ता) + वेबसॉकेट। | अनुशंसित पैकेज। |
| `full` | उपरोक्त सभी। | सब कुछ। |

### आवश्यकताएं।

- पायथन 3.10 या उससे ऊपर का संस्करण
- कॉमफीयूआई स्थानीय रूप से चल रहा होना चाहिए (डिफ़ॉल्ट: `http://localhost:8188`)
- वैकल्पिक: एआई प्रॉम्प्ट को बेहतर बनाने के लिए ओलामा का उपयोग किया जा सकता है।

## उपयोग

### इसका उपयोग पुस्तकालय के रूप में करें।

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### एआई (कृत्रिम बुद्धिमत्ता) के साथ उन्नत।

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

### वीडियो निर्माण।

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

### वेब यूआई (Web UI) को शुरू करें।

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

या फिर, कमांड लाइन के माध्यम से:
```bash
python -m comfy_headless.ui
```

**यूआई विशेषताएं (संस्करण 2.5.1):**
- **छवि निर्माण:** टेक्स्ट से छवि निर्माण (txt2img) जिसमें पूर्व-निर्धारित सेटिंग्स और एआई प्रॉम्प्ट एन्हांसमेंट शामिल हैं।
- **वीडियो निर्माण:** एनिमेट डिफ, एलटीएक्स, हुनयुआन, वान का समर्थन।
- **कतार और इतिहास:** वास्तविक समय में कतार प्रबंधन, कार्यों का इतिहास।
- **वर्कफ़्लो:** वर्कफ़्लो टेम्पलेट्स को ब्राउज़ करें, आयात करें और बनाएं।
- **मॉडल ब्राउज़र:** चेकपॉइंट, लोरा, मोशन मॉडल देखें।
- **सेटिंग्स:** कनेक्शन प्रबंधन, टाइमआउट, सिस्टम जानकारी।

**विषय:** समुद्री धुंध - हल्के नीले-हरे रंग की बारीकियां, जो गर्म, तटस्थ पृष्ठभूमि पर दिखाई देती हैं।

## वीडियो मॉडल (संस्करण 2.5.0)

### समर्थित मॉडल।

| Model | VRAM | गुणवत्ता। | Speed | सबसे उपयुक्त/बेहतरीन। |
| "The quick brown fox jumps over the lazy dog."

"यह फुर्तीला भूरा लोमड़ी आलसी कुत्ते के ऊपर से कूदता है।" | "Please provide the English text you would like me to translate into Hindi." | ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। | "The quick brown fox jumps over the lazy dog."

"यह फुर्तीला भूरा लोमड़ी आलसी कुत्ते के ऊपर से कूदता है।" | ज़रूर, मैं आपकी मदद कर सकता हूँ। कृपया वह अंग्रेजी पाठ प्रदान करें जिसका आप हिंदी में अनुवाद करवाना चाहते हैं। |
| **LTX-Video 2** | 12GB+ | उत्कृष्ट। | Fast | सामान्य उपयोग, RTX 3080 या उससे बेहतर ग्राफिक्स कार्ड। |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | उच्च गुणवत्ता, RTX 4080 या उससे बेहतर। |
| **Wan 2.1/2.2** | 6-16 जीबी | Great | माध्यम। | कम कीमत वाले ग्राफिक्स कार्ड, दक्षता। |
| **Mochi** | 12GB+ | उत्कृष्ट। | Slow | पाठ का पालन। |
| एनिमेट डिफ (AnimateDiff) | 6GB+ | Good | Fast | त्वरित पूर्वावलोकन। |
| SVD | 8GB+ | Good | माध्यम। | छवि से वीडियो। |
| कॉगवीडियोएक्स। | 10GB+ | Good | Slow | विरासत समर्थन। |

### वीडियो प्रीसेट।

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

## फ़ीचर फ़्लैग्स (फीचर झंडे)

जांच करें कि कौन-कौन सी सुविधाएँ उपलब्ध हैं:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## वेबसोकेट प्रगति।

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

## एपीआई संदर्भ मार्गदर्शिका।

### मुख्य पाठ्यक्रम।

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

### त्रुटि प्रबंधन।

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

## आर्किटेक्चर।

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

## ComfyUI नोड की आवश्यकताएं।

### वीडियो बनाने के लिए।

इन अनुकूलित नोड्स को स्थापित करें:

**मुख्य भाग:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - वीडियो एन्कोडिंग

**मॉडल-विशिष्ट:**
- LTX-Video 2: ComfyUI का अंतर्निहित समर्थन (नवीनतम संस्करण)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## संबंधित परियोजनाएं

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/) का हिस्सा — स्थानीय हार्डवेयर के लिए ओपन-सोर्स मशीन लर्निंग उपकरण।

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - मशीन लर्निंग विकास टूलकिट
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - सभी उपकरणों को देखें

## लाइसेंस

MIT लाइसेंस - [LICENSE](LICENSE) देखें

## योगदान

योगदान का स्वागत है! कृपया एक मुद्दा या पुल अनुरोध खोलें।

रुचि के क्षेत्र:
- अतिरिक्त वीडियो मॉडल समर्थन
- वर्कफ़्लो टेम्पलेट
- दस्तावेज़
- बग फिक्स

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
