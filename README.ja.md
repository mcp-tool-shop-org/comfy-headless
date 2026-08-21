<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>PythonでComfyUIを自在に操る。ノードグラフは不要。</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## これは何ですか？

comfy-headlessは、**ComfyUI API形式のグラフ**を構築し、実行します。Python関数を呼び出すと、JSONノードグラフが出力され、ComfyUIにPOST送信され、完了がポーリングされ、出力パスが返されます。

この説明が重要なのは、何が問題になる可能性があるかを教えてくれるからです。このライブラリの主な役割は、ターゲットとなるComfyUIに実際に存在するノード名と入力キーを出力することです。ComfyUIがノードの名前を変更または削除した場合、古い名前を参照するグラフは送信時に不明なエラーで拒否され、事前に警告は表示されません。

**v3.0は、この点を重視してリリースされました。** このライブラリが出力するすべてのノードタイプは、実際のComfyUIカタログに対して監査されました。9つのノードタイプは存在しなくなりました。それらは削除され、それらを使用していたグラフは検証済みのノードで再構築され、ライブラリはサーバーに何が不足しているかを、実行を開始する*前*に通知できるようになりました。

| 問題点 | comfy-headlessが行うこと |
|---------|--------------------------|
| ノードインターフェースは非常に複雑です | プリセットとクリーンなPython API |
| プロンプトエンジニアリングは難しい | オプションのローカルOllamaによるAI拡張 |
| ビデオ生成は手間がかかる | 9つのモデルファミリーにわたる24個のプリセット |
| 「どの設定を使用すればよいですか？」 | VRAMに合わせて調整された推奨設定 |
| グラフが曖昧なエラーで失敗する | 依存関係チェックは、ノードとパッケージの名前を特定します |

## クイックスタート

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` は、`success`、`prompt_id`、`images`、`error`、`seed`、および `preset` を含む `dict` を返します。このライブラリのすべての生成呼び出しは辞書を返すため、結果オブジェクトを展開する必要はありません。

## インストール

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| 追加機能 | 追加 |
|-------|------|
| `ai` | ローカルOllamaによるプロンプト分析と拡張 |
| `websocket` | WebSocket経由のリアルタイム進捗状況 |
| `ui` | Gradio Webインターフェース |
| `health` | システム健全性監視 |
| `validation` | Pydanticによる設定検証 |
| `observability` | OpenTelemetryトレーシング |
| `standard` | `ai` + `websocket` |
| `full` | 上記のすべて |

**Python 3.10以上**と、実行中のComfyUIインスタンスが必要です。

実行時にアクティブになっているものを確認してください：

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## 画像

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

8つの画像プリセット：`draft`、`fast`、`quality`、`hd`、`portrait`、`landscape`、`cinematic`、`square`。

プロンプトのリストをバッチ処理します：

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### AIによるプロンプト拡張

この機能を使用するには、`[ai]` の追加機能とローカルOllamaが必要です。これらは**モジュールレベルの関数**であり、クライアントメソッドではありません：

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

## ビデオ

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

選択は**モデルではなくプリセットごと**に行われます—`generate_video` には `model` 引数はありません。`frames`、`fps`、`steps`、`cfg`、`width`、または `height` のいずれかを渡して、プリセットをオーバーライドできます。

### 画像入力

画像からビデオへの変換など、ソース画像を必要とするすべての処理では、まずその画像がComfyUI内に存在する必要があります。アップロードしてから、サーバーから返された名前を渡します：

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

送信したファイル名を再利用するのではなく、レスポンスから `name` を読み取ります—ComfyUIは競合時にファイル名を変更するため、両方が常に同じであるとは限りません。`ref` は、すでにサブフォルダーと結合されているのと同じ値であり、グラフに必要なものです。

> **3.0で変更されました：** `init_image` はサーバー側のファイル名です。以前のバージョンでは、base64データをサポートし、ストック版のComfyUIには存在しないサードパーティノードを介してそれを渡していました。[CHANGELOG](CHANGELOG.md) を参照してください。

### モデルファミリー

| ファミリー | 最小VRAM | 品質 | 速度 | 追加ノード | 最適な用途 |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | 素晴らしい | 中程度 | — | 低VRAM、効率性 |
| AnimateDiff Lightning | 6 GB | まあまあ | 最速 | AnimateDiff-Evolved | 4ステップのドラフト |
| AnimateDiff | 8 GB | 良い | 速い | AnimateDiff-Evolved、フレーム補間 | クイックプレビュー |
| **LTX-Video** | 12 GB | 非常に良い | 速い | — | 安全なデフォルト |
| **Mochi** | 12 GB | 非常に良い | 遅い | — | テキストへの忠実性、長いクリップ |
| **SVD** | 12 GB | 良い | 中程度 | — | 静止画のアニメーション化 |
| **Hunyuan 1.5** | 14 GB | 最高 | 遅い | — | 最高の品質 |
| CogVideoX | 16 GB | 良い | 遅い | CogVideoX Wrapper | レガシー |
| **Hunyuan 1.0** | 24 GB | 素晴らしい | 遅い | フレーム補間 | 1.5に置き換えられました |

9つのファミリーのうち6つは、**ストック版のComfyUIコアノード**で実行されます—モデル自体用のラッパーパックはありません。AnimateDiff（両方のバリアント）とCogVideoXのみがそれらを必要とします。ビデオ出力には[Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)を使用し、フレーム補間には[Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)を使用します。

VRAMの数値は、そのファミリーのデフォルト解像度の下限であり、`VIDEO_MODEL_INFO`から読み取られます—上限ではありません。より多くのメモリがあれば、同じファミリーからより長いクリップと高解像度の画像を作成できます。

### 実行前に確認してください

送信時に不足しているノードを検出するのではなく：

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

## 設定

環境変数は、`__`セクション区切り文字を使用して、`COMFY_HEADLESS_` プレフィックスを使用します。

| 変数 | デフォルト値 |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | 読み取りタイムアウト（秒） |
| `COMFY_HEADLESS_LOGGING__LEVEL` | ログレベル |

または、URLを直接渡します：`ComfyClient("http://192.168.1.50:8188")`。

## Web UI

```bash
comfy-headless                 # launching the UI is the default action
```

| フラグ | 意味 |
|------|---------|
| `--port` / `-p` | UIポート（デフォルトは`7861`） |
| `--share` | パブリックGradio共有リンク |
| `--url` | ComfyUIサーバーURL |
| `--version` / `-v` | バージョンを表示する |
| `--check` | 機能の可用性 |
| `--diagnose` | 完全な診断 |

6つのタブ：画像、ビデオ、キューと履歴、ワークフロー、モデル、設定。テーマは「オーシャンミスト」で、暖かみのあるニュートラルな背景にソフトなティールがアクセントとして使われています。

プログラムによる操作（`[ui]`が必要）：

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## 進捗状況

ブロッキング呼び出しは、`on_progress`コールバックを受け取ります：

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

WebSocket経由でのリアルタイム更新の場合（`[websocket]`が必要）：

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## エラー

すべての例外には、構造化されたコード、メッセージ、およびヒントが含まれます。

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

## 仕組み

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

このライブラリは、7つのComfyUIルート（`/system_stats`、`/object_info`、`/queue`、`/history`、`/prompt`、`/interrupt`、`/view`）と、バイナリ入力用の`/upload/image`および`/upload/mask`に接続します。

`/object_info`は、特定のサーバーで実行できる内容を決定します。これはライブエンドポイントであり、バージョン管理された成果物ではありません。コアノードのレジストリに対して固定することはできません。したがって、このライブラリは、固定されたノードセットを前提とするのではなく、発行されたグラフをターゲットサーバーの実際のカタログに対して検証します。`check_workflow_dependencies()`はそのチェックであり、利便性ではなく、重要なインフラストラクチャです。

グラフ自体が必要な場合の便利な代替手段：

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## ドキュメント

完全なハンドブック：
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — 概要、使用方法、構成、APIリファレンス、ビデオモデル、アーキテクチャ。

## セキュリティとデータ範囲

- **アクセスされるデータ：** HTTP/WebSocket経由でローカルまたはリモートのComfyUIインスタンスに接続します。ワークフローJSONとアップロードされた画像を送信し、生成されたメディアを受信します。オプションで、プロンプトインテリジェンスのためにローカルのOllamaに接続します。出力は自動的にクリーンアップされる一時ディレクトリに書き込みます。
- **アクセスされないデータ：** テレメトリ、分析、ComfyUIとOllamaのエンドポイントで構成する外部APIはありません。秘密情報は、すべてのログ出力で`SecretValue`を使用してマスクされます。
- **必要な権限：** ComfyUIサーバーおよびオプションのOllamaサーバーへのネットワークアクセス。出力用および一時ディレクトリへのファイル書き込み権限。
- **アップロード：** `upload_image`は、サブフォルダをたどる試みを拒否します。アップロードされたファイルは、指定したサーバー上のComfyUIの入力ディレクトリに保存されます。そのサーバーを信頼できるものとして扱ってください。

脆弱性に関する報告については、[SECURITY.md](SECURITY.md)を参照してください。

## スコアカード

| カテゴリ | スコア |
|----------|-------|
| A. セキュリティ | 10/10 |
| B. エラー処理 | 10/10 |
| C. 運用ドキュメント | 10/10 |
| D. リリースの品質 | 10/10 |
| E. アイデンティティ（ソフト） | 10/10 |
| **Overall** | **50/50** |

> [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)を使用して評価

## 関連情報

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/)の一部 — ローカルハードウェア向けのオープンソースMLツール。

## 貢献

問題やプルリクエストは大歓迎です。詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。役立つ分野：追加のモデルファミリー、ワークフローテンプレート、ドキュメント、バグ修正。

ノードタイプを追加する場合は、最初にライブComfyUIカタログに存在することを確認し、コアでない場合はそのパックを宣言してください。このルールが、今回のリリースが存在する理由です。

## ライセンス

MIT — 詳細は[LICENSE](LICENSE)を参照してください。

---

[MCP Tool Shop](https://mcp-tool-shop.github.io/)によって作成されました
