<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## これは何ですか？

comfy-headlessは、**ComfyUI API形式のグラフ**を構築し、実行します。Python関数を呼び出すと、JSONノードグラフが出力され、ComfyUIにPOST送信され、完了がポーリングされ、出力パスが返されます。

この説明が重要なのは、何が問題になる可能性があるかを教えてくれるからです。このライブラリの主な役割は、ターゲットとなるComfyUIが実際に持っているノード名と入力キーを出力することです。ComfyUIがノードの名前を変更したり削除したりすると、古い名前を参照するグラフは送信時に不明なエラーで拒否され、事前に警告は表示されません。

**v3.0は、この点を重視してリリースされました。** このライブラリが出力するすべてのノードタイプは、実際のComfyUIカタログに対して監査されました。9つのノードはもはや存在しません。それらは削除され、それらを使用していたグラフは検証済みのノードで再構築され、ライブラリはサーバーに何が不足しているかを、実行を開始する*前*に通知できるようになりました。

**v3.1では、この原則を6つのワークフロープロファイル（画像、ビデオ、3D、推論、メタデータ、オーディオ）に拡張しました。** これらは、ComfyUI独自の検証ルールに対応する共有のアドレス指定/型付けレイヤー上に構築されています。具体的には、サーバーのバリデーターから転写されたユニオン型の照合、ドット区切りの動的コンボフィールド（`codec.encoding.crf`）、および構築時に非アクティブなブランチの値を受け入れない条件付き入力です。以前と同様に、メッシュ、音楽、キャプションはすべて `/history` + `/view` を通じて返されます。

| 問題点 | comfy-headlessが行うこと |
|---------|--------------------------|
| ノードインターフェースが複雑すぎる | プリセットとクリーンなPython API |
| プロンプトエンジニアリングは難しい | オプションのローカルOllamaによるAI機能強化 |
| ビデオ生成は手間がかかる | 9つのモデルファミリーにわたる26個のプリセット |
| 「この画像からメッシュを作成したい」 | `generate_3d()` — Hunyuan3D-2、すべてのコアノード |
| 「音楽/ステムが必要だ」 | `generate_audio()`（ACE-Step 1.5）、`separate_audio()` |
| 「この画像には何が写っているのか？」 | `run_inference()` — キャプション、タグ、検出、セグメント化、OCR |
| 「このPNGを作成したのはどのグラフか？」 | `extract_prompt_graph()` / `rerun_from_png()` |
| 「どの設定を使用すればよいのか？」 | VRAMに合わせて調整された推奨設定 |
| グラフが曖昧なエラーで失敗する | 依存関係チェックは、ノードとパッケージの両方を特定する |

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

`generate_image` returns a `dict` with `success`, `prompt_id`, `images`, `error`, `seed`
and `preset`. Every generation call in this library returns a dict — there is no result
object to unwrap.

## インストール

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| 追加機能 | 追加 |
|-------|------|
| `ai` | ローカルOllamaによるプロンプト分析と強化 |
| `websocket` | WebSocket経由のリアルタイム進捗状況 |
| `ui` | Gradio Webインターフェース |
| `health` | システムヘルス監視 |
| `validation` | Pydanticによる設定検証 |
| `observability` | OpenTelemetryトレーシング |
| `standard` | `ai` + `websocket` |
| `full` | 上記のすべて |

**Python 3.10以上**と、実行中のComfyUIインスタンスが必要です。

実行時にアクティブなものを確認します：

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

### AIによるプロンプトの強化

ローカルOllamaと追加機能 `[ai]` が必要です。これらは**モジュールレベルの関数**であり、クライアントメソッドではありません。

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image（v3.1で新規）

Qwen-Image-2512テキストから画像への変換は、テンプレート `qwen_txt2img` として提供され、モデルが実際に必要とするレシピが組み込まれています：`UNETLoader` パス、16チャンネルの `EmptySD3LatentImage`（SDXLラテントはDiTモデルで役に立たない）、ステップ20、**cfg 2.5**、シフト3.1、ネイティブ1328×1328バケット。

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

最大3つの参照画像を使用したインストラクション編集（Qwen-Image-Edit-2511）：

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

参照は、個別の `image1..image3` 入力として `TextEncodeQwenImageEditPlus` に入力され、VAEEncodeを通過しません。これは、ノードが実際に期待するグラフの形状です。

### ControlNet（v3.1で新規）

QwenとSDXLのユニオンControlNetをカバーする単一のコードパス：

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

コア `Canny` プリプロセッサのみが出力されます（`preprocess="canny"`）。他のヒントタイプは、事前に作成されたコントロール画像が必要であり、そのプリプロセッサはカスタムパックに存在するため、このライブラリはそれを自動的に必要としません。

## ビデオ

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

選択は**モデルではなくプリセットごと**に行われます。`generate_video` には `model` 引数はありません。任意の `frames`、`fps`、`steps`、`cfg`、`width`、または `height` を渡して、プリセットをオーバーライドできます。

### 画像入力

画像からビデオへの変換、およびソース画像を使用するその他のすべての処理では、まずその画像をComfyUI内に存在させる必要があります。アップロードしてから、サーバーが返す名前を渡します：

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

レスポンスから `name` を読み取り、送信したファイル名を再利用しないでください。ComfyUIは競合時に名前を変更するため、両方が常に同じであるとは限りません。`ref` は、すでにサブフォルダーと結合されているのと同じ値であり、グラフに必要なものです。

> **v3.0で変更：** `init_image` はサーバー側のファイル名です。以前のバージョンでは、base64データをサポートしておらず、ストックComfyUIインストールに存在しないサードパーティノードを介して送信していました。 [CHANGELOG](CHANGELOG.md) を参照してください。

> **v3.1で新規：** Hunyuan 1.5画像からビデオへの変換は、実際のi2vです。プリセット `hunyuan15_i2v` と `hunyuan15_i2v_fast` は、コアノード `HunyuanVideo15ImageToVideo` に基づいて構築され、 `init_image` が必要です（v3.0ではテキストからビデオへのグラフがサイレントに構築されていました）。また、 `output="core"` はターミネーター `VHS_VideoCombine` をコア `CreateVideo → SaveVideo` に置き換え、Video Helper Suiteの依存関係を完全に削除します。

### モデルファミリー

| ファミリー | 最小VRAM | 品質 | 速度 | 追加ノード | 最適な用途 |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | 非常に良い | 中程度 | — | 低VRAM、効率性 |
| AnimateDiff Lightning | 6 GB | まあまあ | 最速 | AnimateDiff-Evolved | 4段階のドラフト |
| AnimateDiff | 8 GB | 良好 | 高速 | AnimateDiff-Evolved、フレーム補間 | クイックプレビュー |
| **LTX-Video** | 12 GB | 非常に良い | 高速 | — | 安全なデフォルト設定 |
| **Mochi** | 12 GB | 非常に良い | 低速 | — | テキストへの適合性、長いクリップ |
| **SVD** | 12 GB | 良好 | 中程度 | — | 静止画のアニメーション化 |
| **Hunyuan 1.5** | 14 GB | 最高 | 低速 | — | 最高の品質 |
| CogVideoX | 16 GB | 良好 | 低速 | CogVideoXラッパー | レガシー |
| **Hunyuan 1.0** | 24 GB | 非常に良い | 低速 | フレーム補間 | バージョン1.5に置き換えられました |

9つのファミリーのうち6つは、**標準のComfyUIコアノード**で動作します。モデル自体用のラッパーパックはありません。AnimateDiff（両方のバリアント）とCogVideoXのみがそれが必要です。ビデオ出力には[Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)を使用し、フレーム補間には[Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)を使用します。

VRAMの数値は、そのファミリーのデフォルト解像度の下限であり、`VIDEO_MODEL_INFO`から読み取られます。上限ではありません。より多くのメモリを使用すると、同じファミリーからより長いクリップと高解像度の画像を作成できます。

### 実行前に確認してください

送信時にノードが見つからないという問題を回避するためには：

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

グラフのエッジをライブサーバーに対してタイプチェックすることもできます。サーバー自身の受け入れルールを使用します（したがって、`MESH`が`FILE_3D_*`のユニオン入力に接続されている場合、誤った拒否は発生しません）。

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D（バージョン3.1で追加）

**Hunyuan3D-2**による画像からメッシュへの変換 — 完全にComfyUIコアノードを使用し、ラッパーパックや新しいルートはありません。GLBは`/history`にPNGと同様に登録され、`/view`を通じてダウンロードされます。

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d`はローカルパス、生のバイト、`upload_image()`辞書、またはサーバー側の参照を受け入れ、必要に応じて自動的にアップロードします。これは純粋な画像コンディショニングであり、グラフにはテキストプロンプトはありません。調整可能なパラメータ：`steps`（30）、`cfg`（5.5）、`octree_resolution`（256）、`threshold`（0.6）、`seed`。

ラッパーパックの3Dモデル（TRELLIS、TripoSGなど）は意図的に出力されません。ComfyUI-3D-Packのネイティブ依存関係は、エコシステムの中で最も不安定です。

## オーディオ（バージョン3.1で追加）

**ACE-Step 1.5**によるテキストから音楽への変換 — MITライセンスのコードとウェイトを使用し、ネイティブコアノードのみで、パックはゼロです。ターボチェックポイントは8ステップ/cfg 1で実行されます。

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

ビルダーはモデルの結合不変性を強制します。エンコーダーの`duration`と潜在的なものの`seconds`は1つの論理パラメータであり、単一のフィールドから駆動されます。ランタイムではそれらをクロス検証せず、ミスマッチが発生すると「正常に」完了し、静かに誤った出力になります。出力は`SaveAudioAdvanced`（唯一の非推奨ではないオーディオ保存ノード）を通過します。`flac`の出力には品質フィールドが一切含まれず、`mp3`/`opus`はドット区切りの`format.quality`サブフィールドを出力します。

ステム分離（`audio-separation-nodes-comfyui`パックが必要です）。

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## 推論（バージョン3.1で追加）

非生成モデルの呼び出し — 画像を作成する代わりに、画像に関する質問をします。Florence-2上で実行されます（パック`comfyui-florence2`。検出タスクは`comfyui-segment-anything-2`を追加します）。

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

プロファイルの荷重を支えるルール：結果は出力ノードを通じてのみ`/history`に到達します。すべての推論グラフは、コアの`SaveText`（テキストをインラインでレポートするものであり、2回目のラウンドトリップはありません）またはマスク用の`SaveImage`で終了し、ビルダーはそのようなグラフを出力することを拒否します。

## プロベナンス（バージョン3.1で追加）

ComfyUIは、**正確なAPI形式のグラフ**をすべての出力PNGに埋め込みます。comfy-headlessはそれを読み戻し、純粋なstdlibを使用し、Pillowは使用しません。そして、それをそのまま再実行できます。

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

カスタムノードなしでカスタムプロベナンスを作成します。`extra_pnginfo`にあるものはすべて、出力のPNGテキストチャンクになります。

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

既知の制限事項（隠すのではなくドキュメント化されています）。WebP/JPEGはEXIFに同じデータを持ちます（異なるリーダーパスであり、実装されていません）。ビデオ出力にはグラフが埋め込まれません。強化されたデプロイでは、不明なキーが削除される場合があります。GUI→API変換にはサーバー側のルートはありません。ComfyUIの「ワークフロー→エクスポート（API）」を使用してください。

## 設定

環境変数は、`COMFY_HEADLESS_`プレフィックスと`__`セクション区切り文字を使用します。

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

6つのタブ：画像、ビデオ、キューと履歴、ワークフロー、モデル、設定。テーマはオーシャンミストで、暖かくニュートラルな背景にソフトなティールアクセントが施されています。

プログラムによる操作（`[ui]`が必要です）。

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## 進捗状況

ブロッキング呼び出しは、`on_progress`コールバックを受け取ります。

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

WebSocket経由でのリアルタイム更新の場合（`[websocket]`が必要です）。

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
    GraphAddressError,        # new in 3.1 — bad dotted field / inactive combo branch
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

ライブラリは、7つのComfyUIルート（`/system_stats`、`/object_info`、`/queue`、`/history`、`/prompt`、`/interrupt`、`/view`）と、バイナリ入力用の`/upload/image`および`/upload/mask`に通信します（オーディオのアップロードも`/upload/image`で行われます。サーバーにはオーディオ専用ルートはありません）。すべての6つのプロファイルは、その表面内に収まります。バージョン3.1では、メッシュ、音楽、キャプション、およびプロベナンスが追加されましたが、単一のルートは追加されませんでした。

`/object_info`は、特定のサーバーで実行できるかどうかを決定します。これはライブエンドポイントであり、バージョン管理された成果物ではありません。コアノードレジストリに固定するものではありません。したがって、ライブラリは出力されるグラフをターゲットサーバーの実際のカタログに対して検証し、固定されたノードセットを想定しません。`check_workflow_dependencies()`はそのチェックであり、利便性ではなく、重要なインフラストラクチャです。

グラフ自体が必要な場合の便利な代替手段：

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## ドキュメント

完全なハンドブック：
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — 概要、使用方法、6つのプロファイル、ビデオモデル、構成、APIリファレンス、
アーキテクチャ。

LLMおよびコントリビューター向けの**リポジトリ内ナレッジベース**: [`kb/`](kb/README.md) — プロファイルごとの事実ページに関する機械可読形式の[`index.json`](kb/index.json)、実行可能な参照グラフ（`kb/workflows/*.json`、ビルド自体から生成されるため、変更されることはない）、およびノードの出所（`kb/nodes.json`）。 `python scripts/gen_kb.py`によって再生成されます。コードとナレッジベースが一致しない場合、テストスイートは失敗します。

## セキュリティとデータ範囲

- **アクセスされるデータ:** HTTP/WebSocket経由でローカルまたはリモートのComfyUIインスタンスに接続します。ワークフローJSONとアップロードされた画像を送信し、生成されたメディアを受信します。オプションで、プロンプトインテリジェンスのためにローカルのOllamaに接続します。出力は自動的にクリーンアップされる一時ディレクトリに書き込まれます。
- **アクセスされないデータ:** テレメトリ、分析、ComfyUIと構成したOllamaのエンドポイント以外の外部APIはありません。秘密情報は、すべてのログ出力で`SecretValue`によってマスクされます。
- **必要な権限:** ComfyUIサーバーおよびオプションのOllamaサーバーへのネットワークアクセス。出力および一時ディレクトリへのファイル書き込み。
- **アップロード:** `upload_image`はサブフォルダをたどる試みを拒否します。アップロードされたファイルは、指定したサーバー上のComfyUIの入力ディレクトリに保存されます。そのサーバーを信頼できるものとして扱ってください。

脆弱性に関する報告については、[SECURITY.md](SECURITY.md)を参照してください。

## スコアカード

| カテゴリ | スコア |
|----------|-------|
| A. セキュリティ | 10/10 |
| B. エラー処理 | 10/10 |
| C. オペレーター向けドキュメント | 10/10 |
| D. リリースの品質 | 10/10 |
| E. 識別（ソフト） | 10/10 |
| **Overall** | **50/50** |

> [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)を使用して評価されました。

## 関連情報

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/)の一部 — ローカルハードウェア向けのオープンソースMLツール。

## 貢献

課題とプルリクエストは大歓迎です。[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。役立つ分野：追加のモデルファミリー、ワークフローテンプレート、ドキュメント、バグ修正。

ノードタイプを追加する場合は、まずライブComfyUIカタログに存在することを確認し、コアでない場合はそのパックを宣言してください。このルールが、今回のリリースの理由です。

## ライセンス

MIT — [LICENSE](LICENSE)を参照してください。

---

[MCP Tool Shop](https://mcp-tool-shop.github.io/)によって作成されました。
