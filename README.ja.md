<p align="center">
  <a href="README.md">English</a> | <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

**ComfyUIの強力な機能を、複雑さを感じさせずに利用可能に**

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## Comfy Headlessとは？

| 問題点 | 解決策 |
|---------|----------|
| ComfyUIのノードインターフェースは複雑 | シンプルなプリセットと、使いやすいPython API |
| プロンプトエンジニアリングは難しい | AIを活用したプロンプトの最適化 |
| 動画生成は複雑 | 数行のコードで動画生成が可能（モデルプリセット利用） |
| どの設定を使えば良いか分からない | あなたの意図に最適な設定を自動的に適用 |

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

- **ユーザー向け**: シンプルなプリセットと、AIを活用したプロンプトの最適化
- **開発者向け**: テンプレートベースのワークフローコンパイルが可能な、シンプルなAPI
- **すべての人向け**: あなたの意図に最適な設定を自動的に適用

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

| 追加機能 | 依存関係 | 機能 |
|-------|--------------|----------|
| `ai` | httpx | Ollamaによるプロンプトインテリジェンス |
| `websocket` | websockets | リアルタイムの進捗状況表示 |
| `health` | psutil | システムの状態監視 |
| `ui` | gradio | Webインターフェース |
| `validation` | pydantic | 設定の検証 |
| `observability` | opentelemetry | 分散トレーシング |
| `standard` | AI + WebSocket | 推奨されるバンドル |
| `full` | 上記すべて | すべて |

### 要件

- Python 3.10以上
- ローカルで動作しているComfyUI (デフォルト: `http://localhost:8188`)
- オプション: AIプロンプトの最適化にはOllama

## 使い方

### ライブラリとして利用

```python
from comfy_headless import ComfyClient

# Simple image generation
client = ComfyClient()
result = client.generate_image("a beautiful sunset over mountains")
print(f"Generated: {result['images']}")
```

### AIによる最適化機能付きで利用

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

### Web UIを起動

```python
from comfy_headless import launch
launch()  # Opens http://localhost:7870
```

または、コマンドラインから:
```bash
python -m comfy_headless.ui
```

**UIの機能 (v2.5.1):**
- **画像生成**: プリセット付きのtxt2img、AIによるプロンプトの最適化
- **動画生成**: AnimateDiff、LTX、Hunyuan、Wanのサポート
- **キュー＆履歴**: リアルタイムのキュー管理、ジョブ履歴
- **ワークフロー**: ワークフローテンプレートの閲覧、インポート、作成
- **モデルブラウザ**: チェックポイント、LoRA、モーションモデルの表示
- **設定**: 接続管理、タイムアウト、システム情報

**テーマ**: Ocean Mist - 暖かみのある背景に、ソフトなティール色のアクセント

## 動画モデル (v2.5.0)

### サポートされているモデル

| モデル | VRAM | 画質 | 速度 | 推奨用途 |
|-------|------|---------|-------|----------|
| **LTX-Video 2** | 12GB以上 | 優れている | 速い | 一般的な用途、RTX 3080以上 |
| **Hunyuan 1.5** | 14GB以上 | 最高 | 遅い | 高画質、RTX 4080以上 |
| **Wan 2.1/2.2** | 6-16GB | 良い | 普通 | エントリーモデル、効率重視 |
| **Mochi** | 12GB以上 | 優れている | 遅い | テキストへの適合性 |
| AnimateDiff | 6GB以上 | 良い | 速い | プレビュー用 |
| SVD | 8GB以上 | 良い | 普通 | 画像から動画 |
| CogVideoX | 10GB以上 | 良い | 遅い | レガシーサポート |

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

## WebSocketによる進捗状況表示

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

### 主要クラス

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

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/) の一部 - ローカル環境のハードウェアで使用できるオープンソースの機械学習ツール。

- [brain-dev](https://github.com/mcp-tool-shop-org/brain-dev) - 機械学習開発ツールキット
- [MCP Tool Shop](https://mcp-tool-shop.github.io/) - すべてのツールを閲覧

## セキュリティとデータ範囲

- **アクセスするデータ:** HTTP/WebSocketを介して、ローカルまたはリモートのComfyUIインスタンスに接続します。ワークフローのJSONデータを送信し、生成された画像をデータとして受信します。オプションで、AIプロンプトのインテリジェンスのために、ローカルのOllamaに接続できます。生成された画像を一時ディレクトリに保存し、自動的にクリーンアップします。
- **アクセスしないデータ:** テレメトリー、分析、ユーザーが設定したComfyUIおよびオプションのOllama以外の外部APIはありません。すべてのログ出力において、機密情報は`SecretValue`によってマスクされます。
- **必要な権限:** ComfyUIサーバーへのネットワークアクセス、オプションでOllamaサーバーへのアクセス。画像出力と一時ディレクトリへのファイル書き込み権限。

脆弱性報告とセキュリティに関するベストプラクティスについては、[SECURITY.md](SECURITY.md) を参照してください。

## 評価項目

| カテゴリ | 評価 |
|----------|-------|
| A. セキュリティ | 10/10 |
| B. エラー処理 | 10/10 |
| C. ユーザーマニュアル | 10/10 |
| D. ソフトウェアの品質 | 10/10 |
| E. 識別情報 (ソフト) | 10/10 |
| **Overall** | **50/50** |

> [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck) を使用して評価

## ライセンス

MITライセンス - [LICENSE](LICENSE) を参照

## 貢献

貢献を歓迎します！問題やプルリクエストを送信してください。

関心のある分野:
- 追加のビデオモデルサポート
- ワークフローテンプレート
- ドキュメント
- バグ修正

---

[MCP Tool Shop](https://mcp-tool-shop.github.io/) が作成
