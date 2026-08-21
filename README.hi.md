<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.md">English</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>ComfyUI को पायथन से चलाएं, बिना किसी जटिल नोड ग्राफ के।</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## यह क्या है

comfy-headless, **ComfyUI API-प्रारूप ग्राफ़** बनाता है और उन्हें चलाता है। आप एक पायथन फ़ंक्शन को कॉल करते हैं; यह JSON नोड ग्राफ़ उत्सर्जित करता है, इसे ComfyUI पर POST करता है, पूर्ण होने के लिए जांच करता है, और आपको आउटपुट पथ प्रदान करता है।

यह ढांचा महत्वपूर्ण है, क्योंकि यह बताता है कि क्या गलत हो सकता है। लाइब्रेरी का पूरा काम नोड नाम और इनपुट कुंजियाँ उत्सर्जित करना है जो लक्षित ComfyUI में वास्तव में मौजूद हैं। जब ComfyUI किसी नोड का नाम बदलता है या उसे हटा देता है, तो पुराने नाम को संदर्भित करने वाला ग्राफ़ सबमिट करते समय एक अस्पष्ट त्रुटि के साथ अस्वीकार कर दिया जाता है - और कुछ भी आपको पहले चेतावनी नहीं देता है।

**v3.0 वह रिलीज़ है जिसने इसे गंभीरता से लिया।** इस लाइब्रेरी द्वारा उत्सर्जित प्रत्येक नोड प्रकार की लाइव ComfyUI कैटलॉग के विरुद्ध ऑडिट किया गया था। अब नौ मौजूद नहीं हैं। वे चले गए हैं, उनका उपयोग करने वाले ग्राफ़ सत्यापित नोड्स पर फिर से बनाए जाते हैं, और लाइब्रेरी अब आपको यह बता सकती है कि किसी सर्वर में क्या गायब है *इससे पहले* कि आप उस पर कोई रन खर्च करें।

| समस्या | comfy-headless क्या करता है |
|---------|--------------------------|
| नोड इंटरफ़ेस बहुत अधिक है | प्रीसेट और एक स्वच्छ पायथन API |
| प्रॉम्प्ट इंजीनियरिंग कठिन है | स्थानीय Ollama के माध्यम से वैकल्पिक AI संवर्धन |
| वीडियो निर्माण जटिल है | 9 मॉडल परिवारों में 24 प्रीसेट |
| "मुझे कौन सी सेटिंग्स का उपयोग करना चाहिए?" | आपके VRAM के अनुसार अनुशंसाएँ |
| ग्राफ़ अस्पष्ट त्रुटियों के साथ विफल हो जाते हैं | निर्भरता जांच नोड *और* पैक दोनों को नाम देती है |

## त्वरित शुरुआत

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` एक `dict` लौटाता है जिसमें `success`, `prompt_id`, `images`, `error`, `seed` और `preset` शामिल हैं। इस लाइब्रेरी में प्रत्येक पीढ़ी कॉल एक डिक्ट लौटाती है - अनरैप करने के लिए कोई परिणाम ऑब्जेक्ट नहीं है।

## स्थापित करें

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| अतिरिक्त | जोड़ता है |
|-------|------|
| `ai` | स्थानीय Ollama के माध्यम से प्रॉम्प्ट विश्लेषण और संवर्धन |
| `websocket` | WebSocket पर वास्तविक समय की प्रगति |
| `ui` | Gradio वेब इंटरफ़ेस |
| `health` | सिस्टम स्वास्थ्य निगरानी |
| `validation` | Pydantic कॉन्फ़िगरेशन सत्यापन |
| `observability` | OpenTelemetry ट्रेसिंग |
| `standard` | `ai` + `websocket` |
| `full` | उपरोक्त सभी |

इसके लिए **Python 3.10+** और एक चल रहे ComfyUI इंस्टेंस की आवश्यकता होती है।

रनटाइम पर जांच करें कि क्या सक्रिय है:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## चित्र

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

आठ छवि प्रीसेट: `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`।

प्रॉम्प्ट की एक सूची को बैच करें:

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### AI प्रॉम्प्ट संवर्धन

इसके लिए `[ai]` अतिरिक्त और एक स्थानीय Ollama की आवश्यकता होती है। ये **मॉड्यूल-स्तरीय फ़ंक्शन** हैं, न कि क्लाइंट विधियाँ:

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## वीडियो

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

चयन **मॉडल द्वारा नहीं, बल्कि प्रीसेट द्वारा** किया जाता है - `generate_video` में कोई `model` तर्क नहीं है। किसी भी `frames`, `fps`, `steps`, `cfg`, `width`, `height` को प्रीसेट को ओवरराइड करने के लिए पास किया जा सकता है।

### छवि इनपुट

इमेज-टू-वीडियो, और कोई भी अन्य चीज़ जो एक स्रोत छवि लेती है, उसे पहले ComfyUI के अंदर उस छवि को मौजूद होने की आवश्यकता होती है। इसे अपलोड करें, फिर सर्वर द्वारा वापस दिए गए नाम को पास करें:

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

प्रतिक्रिया से `name` पढ़ें, न कि आपके द्वारा भेजी गई फ़ाइल का नाम दोबारा उपयोग करें - ComfyUI टकराव पर नाम बदलता है, इसलिए दोनों हमेशा समान नहीं होते हैं। `ref` वही मान है जो पहले से किसी भी सबफ़ोल्डर के साथ जोड़ा गया है, जो ठीक वही है जिसकी ग्राफ़ को आवश्यकता होती है।

> **3.0 में बदला गया:** `init_image` सर्वर-साइड फ़ाइल नाम है। पुराने संस्करणों ने base64 डेटा स्वीकार किया और इसे एक तीसरे पक्ष के नोड के माध्यम से पारित किया जो स्टॉक ComfyUI इंस्टॉलेशन पर मौजूद नहीं है। [CHANGELOG](CHANGELOG.md) देखें।

### मॉडल परिवार

| परिवार | न्यूनतम VRAM | गुणवत्ता | गति | अतिरिक्त नोड | सर्वोत्तम किसके लिए |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 जीबी | महान | मध्यम | — | कम VRAM, दक्षता |
| AnimateDiff लाइटनिंग | 6 जीबी | उचित | सबसे तेज़ | AnimateDiff-Evolved | 4-चरण ड्राफ्ट |
| AnimateDiff | 8 जीबी | अच्छा | तेज़ | AnimateDiff-Evolved, फ्रेम इंटरप। | त्वरित पूर्वावलोकन |
| **LTX-Video** | 12 जीबी | उत्कृष्ट | तेज़ | — | सुरक्षित डिफ़ॉल्ट |
| **Mochi** | 12 जीबी | उत्कृष्ट | धीमा | — | टेक्स्ट पालन, लंबे क्लिप |
| **SVD** | 12 जीबी | अच्छा | मध्यम | — | एक स्थिर छवि को एनिमेट करना |
| **Hunyuan 1.5** | 14 जीबी | सर्वश्रेष्ठ | धीमा | — | उच्चतम गुणवत्ता |
| CogVideoX | 16 जीबी | अच्छा | धीमा | CogVideoX रैपर | विरासत |
| **Hunyuan 1.0** | 24 जीबी | महान | धीमा | फ्रेम इंटरपोलेशन | 1.5 द्वारा प्रतिस्थापित |

नौ परिवारों में से छह **स्टॉक ComfyUI कोर नोड्स** पर चलते हैं - मॉडल के लिए कोई रैपर पैक नहीं। केवल AnimateDiff (दोनों वेरिएंट) और CogVideoX को एक की आवश्यकता होती है। वीडियो आउटपुट [वीडियो हेल्पर सूट](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) का उपयोग करता है; फ्रेम इंटरपोलेशन [फ्रेम इंटरपोलेशन](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation) का उपयोग करता है।

VRAM आंकड़े उस परिवार के डिफ़ॉल्ट रिज़ॉल्यूशन के लिए न्यूनतम हैं, जो `VIDEO_MODEL_INFO` से पढ़ा जाता है - अधिकतम नहीं। अधिक मेमोरी एक ही परिवार से लंबे क्लिप और उच्च रिज़ॉल्यूशन प्राप्त करती है।

### चलाने से पहले जांच करें

सबमिट समय पर लापता नोड की खोज करने के बजाय:

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## कॉन्फ़िगरेशन

पर्यावरण चर `COMFY_HEADLESS_` उपसर्ग का उपयोग करते हैं जिसमें `__` अनुभाग विभाजक होते हैं:

| चर | डिफ़ॉल्ट |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | पढ़ने का समय समाप्त, सेकंड |
| `COMFY_HEADLESS_LOGGING__LEVEL` | लॉग स्तर |

या सीधे URL पास करें: `ComfyClient("http://192.168.1.50:8188")`।

## वेब UI

```bash
comfy-headless                 # launching the UI is the default action
```

| ध्वज | अर्थ |
|------|---------|
| `--port` / `-p` | UI पोर्ट (डिफ़ॉल्ट `7861`) |
| `--share` | सार्वजनिक Gradio साझा लिंक |
| `--url` | ComfyUI सर्वर URL |
| `--version` / `-v` | संस्करण प्रिंट करें |
| `--check` | सुविधा उपलब्धता |
| `--diagnose` | पूर्ण निदान |

छह टैब: छवि, वीडियो, क्यू और इतिहास, वर्कफ़्लो, मॉडल, सेटिंग्स। थीम है ओशन मिस्ट — गर्म तटस्थ पृष्ठभूमि पर हल्के नीले रंग के लहजे।

प्रोग्रामेटिक रूप से (`[ui]` की आवश्यकता है):

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## प्रगति

ब्लॉकिंग कॉल एक `on_progress` कॉलबैक लेते हैं:

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

वेब सॉकेट पर वास्तविक समय के अपडेट के लिए (`[websocket]` की आवश्यकता है):

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## त्रुटियाँ

प्रत्येक अपवाद में एक संरचित कोड, संदेश और संकेत होता है:

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

## यह कैसे काम करता है

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

लाइब्रेरी सात ComfyUI मार्गों से बात करती है — `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view` — साथ ही बाइनरी इनपुट के लिए `/upload/image` और `/upload/mask`।

`/object_info` यह निर्धारित करता है कि कोई दिया गया सर्वर क्या चला सकता है। यह एक लाइव एंडपॉइंट है, संस्करणित कलाकृति नहीं: इसे पिन करने के लिए कोई कोर-नोड रजिस्ट्री नहीं है। इसलिए लाइब्रेरी मान्य किए गए ग्राफ़ को अनुमान लगाने के बजाय लक्ष्य सर्वर की वास्तविक सूची के विरुद्ध सत्यापित करती है
एक निश्चित नोड सेट का। `check_workflow_dependencies()` वह जाँच है, और यह एक सुविधा होने के बजाय भार-असर ढांचा है।

जब आप स्वयं ग्राफ चाहते हैं तो उपयोगी एस्केप हैच:

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## दस्तावेज़

पूर्ण हैंडबुक:
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — आरंभ करना, उपयोग, कॉन्फ़िगरेशन, एपीआई संदर्भ, वीडियो मॉडल, आर्किटेक्चर।

## सुरक्षा और डेटा दायरा

- **उपयोग किया गया डेटा:** HTTP/WebSocket पर स्थानीय या दूरस्थ ComfyUI इंस्टेंस से जुड़ता है। वर्कफ़्लो JSON और अपलोड की गई छवियों को भेजता है, उत्पन्न मीडिया प्राप्त करता है। वैकल्पिक रूप से प्रॉम्प्ट इंटेलिजेंस के लिए एक स्थानीय ओलामा से जुड़ता है। आउटपुट को स्वचालित सफाई के साथ अस्थायी निर्देशिकाओं में लिखता है।
- **उपयोग नहीं किया गया डेटा:** कोई टेलीमेट्री नहीं, कोई एनालिटिक्स नहीं, ComfyUI और ओलामा एंडपॉइंट्स से परे कोई बाहरी एपीआई नहीं जिसे आप कॉन्फ़िगर करते हैं। सभी लॉग आउटपुट में गुप्त जानकारी `SecretValue` के माध्यम से मास्क की जाती है।
- **आवश्यक अनुमतियाँ:** आपके ComfyUI सर्वर और वैकल्पिक ओलामा सर्वर तक नेटवर्क एक्सेस; आउटपुट और अस्थायी निर्देशिकाओं के लिए फ़ाइल लेखन।
- **अपलोड:** `upload_image` सबफ़ोल्डर ट्रैवर्सल प्रयासों को अस्वीकार करता है। अपलोड की गई फाइलें उस सर्वर पर ComfyUI की इनपुट निर्देशिका में जाती हैं जिस पर आप इंगित करते हैं — उस सर्वर को विश्वसनीय मानें।

भेद्यता रिपोर्टिंग के लिए [SECURITY.md](SECURITY.md) देखें।

## स्कोरकार्ड

| श्रेणी | अंक |
|----------|-------|
| ए. सुरक्षा | 10/10 |
| बी. त्रुटि प्रबंधन | 10/10 |
| सी. ऑपरेटर दस्तावेज़ | 10/10 |
| डी. शिपिंग स्वच्छता | 10/10 |
| ई. पहचान (सॉफ्ट) | 10/10 |
| **Overall** | **50/50** |

> [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck) के साथ मूल्यांकन किया गया

## संबंधित

[**MCP टूल शॉप**](https://mcp-tool-shop.github.io/) का हिस्सा — स्थानीय हार्डवेयर के लिए ओपन-सोर्स एमएल टूलिंग।

## योगदान

मुद्दे और पुल अनुरोधों का स्वागत है — [CONTRIBUTING.md](CONTRIBUTING.md) देखें। उपयोगी क्षेत्र: अतिरिक्त मॉडल परिवार, वर्कफ़्लो टेम्पलेट, दस्तावेज़, बग फिक्स।

यदि आप एक नोड प्रकार जोड़ते हैं, तो पहले यह सत्यापित करें कि यह लाइव ComfyUI सूची में मौजूद है, और यदि यह कोर नहीं है तो इसके पैक की घोषणा करें। यही नियम इस रिलीज़ के अस्तित्व का कारण है।

## लाइसेंस

एमआईटी — [LICENSE](LICENSE) देखें।

---

[MCP टूल शॉप](https://mcp-tool-shop.github.io/) द्वारा निर्मित
