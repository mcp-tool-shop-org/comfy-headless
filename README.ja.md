<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="logo.png" alt="comfy-headless" width="400">
</p>

# Comfy Headless

**ComfyUIの強力な機能を、複雑さを感じさせずに利用可能に**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue?style=flat-square" alt="Landing Page"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/dm/comfy-headless?color=green&logo=pypi&logoColor=white" alt="Downloads"></a>
</p>

---

## Comfy Headlessの利点

| 問題点 | 解決策 |
| --------- | ---------- |
| ComfyUIのノードインターフェースが複雑 | シンプルなプリセットと、使いやすいPython API |
| プロンプトの作成が難しい | AIを活用したプロンプトの改善 |
| 動画生成が複雑 | 数行のコードでモデルプリセットを利用した動画生成 |
| どの設定を使えば良いかわからない | 意図に最適な設定を自動的に適用 |

## クイックスタート

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

## 哲学

- **ユーザー向け**: シンプルなプリセットと、AIを活用したプロンプトの改善
- **開発者向け**: テンプレートベースのワークフローコンパイルに対応した、シンプルなAPI
- **すべての人向け**: 意図に最適な設定を自動的に適用

## インストール

### モジュール式インストール (v2.5.0以降)

必要なものだけをインストール:

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

### 利用可能な追加機能

| Extra | 依存関係 | 機能 |
| ------- | -------------- | ---------- |
| `ai` | httpx | Ollamaによるプロンプトのインテリジェンス |
| `websocket` | WebSockets | リアルタイムの進捗状況の表示 |
| `health` | psutil | システムの状態監視 |
| `ui` | Gradio | Webインターフェース |
| `validation` | pydantic | 設定の検証 |
| `observability` | opentelemetry | 分散トレーシング |
| `standard` | AI + WebSocket | 推奨されるバンドル |
| `full` | 上記すべて | すべて |

### 要件

- Python 3.10以上
- ローカルで動作しているComfyUI (デフォルト: `http://localhost:8188`)
- オプション: AIプロンプトの改善のためのOllama

## 使い方

### ライブラリとして使用

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### AIによる改善機能付き

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

### 動画生成

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

### Web UIの起動

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

または、コマンドラインから:
```bash
python -m comfy_headless.ui
```

**UIの機能 (v2.5.1):**
- **画像生成**: プリセット付きのtxt2img、AIによるプロンプトの改善
- **動画生成**: AnimateDiff、LTX、Hunyuan、Wanのサポート
- **キューと履歴**: リアルタイムのキュー管理、ジョブ履歴
- **ワークフロー**: ワークフローテンプレートの閲覧、インポート、作成
- **モデルブラウザ**: チェックポイント、LoRA、モーションモデルの表示
- **設定**: 接続管理、タイムアウト、システム情報

**テーマ**: Ocean Mist - 暖かみのある背景に、ソフトなティール色のアクセント

## 動画モデル (v2.5.0)

### サポートされているモデル

| Model | VRAM | 品質 | Speed | 最適な用途 |
| ------- | ------ | --------- | ------- | ---------- |
| **LTX-Video 2** | 12GB+ | 優れている | Fast | 一般的な用途、RTX 3080以上 |
| **Hunyuan 1.5** | 14GB+ | Best | Slow | 高品質、RTX 4080以上 |
| **Wan 2.1/2.2** | 6-16GB | Great | 普通 | エントリーレベルのGPU、効率重視 |
| **Mochi** | 12GB+ | 優れている | Slow | テキストへの忠実性 |
| AnimateDiff | 6GB+ | Good | Fast | プレビューの高速化 |
| SVD | 8GB+ | Good | 普通 | 画像から動画への変換 |
| CogVideoX | 10GB+ | Good | Slow | レガシーサポート |

### 動画プリセット

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

## 機能フラグ

利用可能な機能を確認:

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)
# {'ai': True, 'websocket': True, 'health': False, ...}

print(list_missing_features())
# {'health': 'pip install comfy-headless[health]', ...}
```

## WebSocketによる進捗状況

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

## APIリファレンス

### 主要なクラス

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

### エラー処理

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

## アーキテクチャ

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

## ComfyUIノードの要件

### 動画生成に必要なもの

以下のカスタムノードをインストールしてください:

**主要機能:**
- [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) - ビデオエンコード

**モデル固有:**
- LTX-Video 2: ComfyUIへの組み込みサポート (最新バージョン)
- Hunyuan 1.5: [ComfyUI-HunyuanVideo](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper)
- Wan: [ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- AnimateDiff: [ComfyUI-AnimateDiff-Evolved](https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved)

## 関連プロジェクト

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/) の一部 — ローカル環境のハードウェアで使用できるオープンソースの機械学習ツール。

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - 機械学習開発ツールキット
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - すべてのツールを閲覧

## ライセンス

MITライセンス - [LICENSE](LICENSE) を参照

## 貢献

貢献を歓迎します！ 問題やプルリクエストを送信してください。

関心のある分野:
- 追加のビデオモデルサポート
- ワークフローテンプレート
- ドキュメント
- バグ修正

---

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/issues">Issues</a> • <a href="https://github.com/mcp-tool-shop-org/comfy-headless/discussions">Discussions</a>
</p>
