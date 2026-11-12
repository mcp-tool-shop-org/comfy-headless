<p align="center">
  <a href="README.md">English</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## これは何ですか

comfy-headlessは、**ComfyUI API形式のグラフ**をビルドし、実行します。Python関数を呼び出すと、JSONノードグラフが出力され、ComfyUIにPOSTされ、完了をポーリングし、出力パスが返されます。

この構成が重要なのは、何が問題になる可能性があるかを示しているからです。このライブラリの主な役割は、ターゲットのComfyUIに実際に存在するノード名と入力キーを出力することです。ComfyUIがノードの名前を変更または削除した場合、古い名前を参照するグラフは、不透明なエラーとともに送信時に拒否されます。そして、事前に警告は表示されません。

**v3.0は、この点を真剣に受け止めたリリースです。**このライブラリが出力するすべてのノードタイプは、ライブのComfyUIカタログに対して監査されました。9つはもはや存在しません。それらは削除され、それらを使用していたグラフは、検証済みのノードで再構築され、ライブラリは、実行を開始する前に、サーバーに何が不足しているかを通知できるようになりました。

**v3.1は、この規律を6つのワークフロープロファイル（画像、ビデオ、3D、推論、メタデータ、オーディオ）に拡張します。**これらは、ComfyUI独自の検証ルールを適用する共有のアドレス指定/型指定レイヤー上に構築されています。具体的には、サーバーのバリデーターから転写されたユニオン型マッチング、ドット区切りの動的コンボフィールド（`codec.encoding.crf`）、および構築時に非アクティブなブランチの値を受け付けない条件付き入力です。以前と同様のルーティング構造で、メッシュ、音楽、キャプションは、他のすべての要素と同様に、`/history`と`/view`を通じて返されます。

| 問題点 | comfy-headlessが行うこと |
|---------|--------------------------|
| ノードインターフェースは非常に多岐にわたる | プリセットとクリーンなPython API |
| プロンプトエンジニアリングは難しい | オプションのローカルOllamaによるAI機能強化 |
| ビデオ生成は複雑 | 9つのモデルファミリーにわたる26のプリセット |
| 「この画像からメッシュが必要です」 | `generate_3d()` — Hunyuan3D-2、すべてのコアノード |
| 「音楽/ステムが必要です」 | `generate_audio()`（ACE-Step 1.5）、`separate_audio()` |
| 「この画像には何が含まれていますか？」 | `run_inference()` — キャプション、タグ、検出、セグメント、OCR |
| 「このPNGを作成したのはどのグラフですか？」 | `extract_prompt_graph()` / `rerun_from_png()` |
| 「どの設定を使用すればよいですか？」 | VRAMに合わせて調整された推奨設定 |
| グラフが曖昧なエラーで失敗する | 依存関係チェックは、ノードとパックの名前を特定する |

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

`generate_image`は、`dict`、`success`、`prompt_id`、`images`、`error`、`seed`、および`preset`を含む辞書を返します。このライブラリのすべての生成呼び出しは辞書を返します。結果オブジェクトをアンラップする必要はありません。

## インストール

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| 追加機能 | 追加 |
|-------|------|
| `ai` | ローカルOllamaによるプロンプト分析と機能強化 |
| `websocket` | WebSocketでのリアルタイムの進捗状況 |
| `ui` | Gradio Webインターフェース |
| `health` | システムヘルス監視 |
| `validation` | Pydanticによる設定の検証 |
| `observability` | OpenTelemetryトレーシング |
| `standard` | `ai` + `websocket` |
| `full` | 上記のすべて |

**Python 3.10以上**と、実行中のComfyUIインスタンスが必要です。

実行時にアクティブになっているものを確認します。

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

プロンプトのリストをバッチ処理します。

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### AIプロンプトの機能強化

これには、`[ai]`の追加機能とローカルのOllamaが必要です。これらは**モジュールレベルの関数**であり、クライアントメソッドではありません。

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image（3.1で新規）

Qwen-Image-2512のテキストから画像への変換は、`qwen_txt2img`テンプレートとして提供され、モデルが実際に必要とするレシピが組み込まれています。具体的には、`UNETLoader`パス、16チャンネルの`EmptySD3LatentImage`（SDXLラテントはDiTモデルで役に立たない）、ステップ20、**cfg 2.5**、シフト3.1、ネイティブ1328×1328バケットです。

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

参照画像は、個別の`image1..image3`入力として`TextEncodeQwenImageEditPlus`に供給され、ノードが実際に期待するグラフ形状であるVAEEncodeを通過しません。

### ControlNet（3.1で新規）

1つのコードパスで、QwenとSDXLのユニオンControlNetsを処理します。

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

コアの`Canny`プリプロセッサーのみが出力されます（`preprocess="canny"`）。他のヒントタイプは、事前に作成されたコントロール画像を期待します。なぜなら、それらのプリプロセッサーは、このライブラリがサイレントに必要としないカスタムパックに存在するためです。

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

選択は**モデルではなく、プリセットごと**に行われます。`generate_video`には`model`引数はありません。`frames`、`fps`、`steps`、`cfg`、`width`、または`height`のいずれかを渡して、プリセットをオーバーライドできます。

### 画像入力

画像からビデオへの変換、およびソース画像を使用するその他のすべての処理では、まずその画像がComfyUI内に存在する必要があります。アップロードしてから、サーバーから返された名前を渡します。

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

レスポンスから`name`を読み取り、送信したファイル名を再利用するのではなく、ComfyUIは衝突時に名前を変更するため、両方は常に同じであるとは限りません。`ref`は、すでにサブフォルダーと結合された同じ値であり、グラフに必要な値です。

> **3.0で変更:** `init_image`はサーバー側のファイル名です。以前のバージョンでは、base64データを受け入れ、存在しないサードパーティのノードを通じてそれを渡していました。標準のComfyUIインストールでは、[CHANGELOG](CHANGELOG.md)を参照してください。

> **3.1で新規:** Hunyuan 1.5の画像からビデオへの変換は、実際のi2vです。プリセット`hunyuan15_i2v`と`hunyuan15_i2v_fast`は、コアの`HunyuanVideo15ImageToVideo`ノードを基に構築されており、`init_image`が必要です（v3.0は、テキストからビデオへのグラフをサイレントに構築していました）。また、`output="core"`は、コアの`CreateVideo → SaveVideo`に代わる`VHS_VideoCombine`ターミネーターを置き換え、Video Helper Suiteへの依存関係を完全に削除します。

### モデルファミリー

| ファミリー | 最小VRAM | 品質 | 速度 | 追加ノード | 最適な用途 |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 GB | 素晴らしい | 中 | — | 低VRAM、効率性 |
| AnimateDiff Lightning | 6 GB | まあまあ | 最速 | AnimateDiff-Evolved | 4ステップのドラフト |
| AnimateDiff | 8 GB | 良い | 速い | AnimateDiff-Evolved、フレーム補間 | クイックプレビュー |
| **LTX-Video** | 12 GB | 非常に優れている | 速い | — | 安全なデフォルト |
| **Mochi** | 12 GB | 非常に優れている | 遅い | — | テキストの一貫性、長いクリップ |
| **SVD** | 12 GB | 良い | 中 | — | 静止画をアニメーション化 |
| **Hunyuan 1.5** | 14GB | 最高 | 遅い | — | 最高の品質 |
| CogVideoX | 16GB | 良い | 遅い | CogVideoXラッパー | レガシー |
| **Hunyuan 1.0** | 24GB | 素晴らしい | 遅い | フレーム補間 | 1.5に置き換え |

9つのファミリーのうち6つは、**標準のComfyUIコアノード**で動作する。モデル自体にはラッパーパックは不要。AnimateDiff（両方のバリアント）とCogVideoXのみが必要。ビデオ出力には[Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite)を使用。フレーム補間には[Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation)を使用。

VRAMの数値は、そのファミリーのデフォルト解像度の下限であり、`VIDEO_MODEL_INFO`から読み取られるものであり、上限ではない。より多くのメモリを使用すると、同じファミリーからより長いクリップとより高い解像度が得られる。

### 実行前に確認してください

送信時にノードが見つからないという事態を避けるために：

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

グラフのエッジをライブサーバーに対して型チェックすることもできます。サーバー自身の受け入れルールを使用します（したがって、`MESH`が`FILE_3D_*`のユニオン入力に接続されている場合、誤った拒否は発生しません）。

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D（3.1で新規）

**Hunyuan3D-2**を介した画像からメッシュへの変換 — 完全にComfyUIコアノードのみで、ラッパーパックや新しいルートは不要。GLBは`/history`にPNGと同様に登録され、`/view`を通じてダウンロードされる。

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d`は、ローカルパス、生のバイト、`upload_image()`辞書、またはサーバー側の参照を受け入れ、必要に応じて自動的にアップロードする。これは純粋な画像処理であり、グラフ内にテキストプロンプトは含まれていない。調整可能なパラメータ：`steps`（30）、`cfg`（5.5）、`octree_resolution`（256）、`threshold`（0.6）、`seed`。

ラッパーパックの3Dモデル（TRELLIS、TripoSGなど）は、意図的に出力されない。ComfyUI-3D-Packのネイティブ依存関係は、エコシステムの中で最も不安定である。

## オーディオ（3.1で新規）

**ACE-Step 1.5**を介したテキストから音楽への変換 — MITライセンスのコードとウェイト、ネイティブコアノード、ゼロパック。ターボチェックポイントは、8ステップ/cfg 1で実行される。

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

ビルダーは、モデルの結合不変性を強制する。エンコーダーの`duration`と潜在空間の`seconds`は、1つの論理パラメータであり、単一のフィールドから駆動される。ランタイムはそれらをクロス検証せず、不一致が発生した場合、「正常に」完了し、静かに誤った出力となる。出力は`SaveAudioAdvanced`（唯一の非推奨のオーディオ保存ノード）を通過する。`flac`の出力は品質フィールドを一切出力せず、`mp3`/`opus`はドット区切りの`format.quality`サブフィールドを出力する。

ステム分離（`audio-separation-nodes-comfyui`パックが必要）

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## 推論（3.1で新規）

非生成モデルの呼び出し — 画像を作成する代わりに、画像に関する質問をする。Florence-2（パック`comfyui-florence2`で実行。検出タスクは`comfyui-segment-anything-2`を追加する）。

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

プロファイルの荷重を支えるルール：結果は、出力ノードを介してのみ`/history`に到達する。すべての推論グラフは、コア`SaveText`（テキストをインラインでレポートする。2回目のラウンドトリップは不要）またはマスク用の`SaveImage`で終了し、ビルダーは緑色で実行されて何も返さないグラフの出力を拒否する。

## プロベナンス（3.1で新規）

ComfyUIは、すべての出力PNGに**正確なAPI形式のグラフ**を埋め込む。comfy-headlessはそれを読み込み、純粋なstdlib（Pillowは不要）で、それをそのまま再実行できる。

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

カスタムノードを使用せずに、カスタムプロベナンスを記述できる。`extra_pnginfo`内のものはすべて、出力のPNGテキストチャンクになる。

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

既知の制限事項（隠さずに文書化）：WebP/JPEGは、EXIFに同じデータを格納する（異なるリーダーパスであり、実装されていない）。ビデオ出力はグラフを埋め込まない。強化されたデプロイメントは、不明なキーを削除する可能性がある。GUI→API変換にはサーバー側のルートがない。ComfyUIの「ワークフロー→エクスポート（API）」を使用する。

## 設定

環境変数は、`__`セクション区切り文字付きの`COMFY_HEADLESS_`プレフィックスを使用する。

| 変数 | デフォルト |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | 読み取りタイムアウト（秒） |
| `COMFY_HEADLESS_LOGGING__LEVEL` | ログレベル |

または、URLを直接渡す：`ComfyClient("http://192.168.1.50:8188")`。

## Web UI

```bash
comfy-headless                 # launching the UI is the default action
```

| フラグ | 意味 |
|------|---------|
| `--port` / `-p` | UIポート（デフォルトは`7861`） |
| `--share` | パブリックGradio共有リンク |
| `--url` | ComfyUIサーバーURL |
| `--version` / `-v` | バージョンを表示 |
| `--check` | 機能の可用性 |
| `--diagnose` | 完全な診断 |

6つのタブ：画像、ビデオ、キューと履歴、ワークフロー、モデル、設定。テーマはオーシャンミスト — 暖かくニュートラルな背景に、ソフトなティールアクセント。

プログラムによる操作（`[ui]`が必要）

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## 進捗状況

ブロッキング呼び出しは、`on_progress`コールバックを受け取る。

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

リアルタイムの更新（`[websocket]`が必要）をWebSocket経由で行う場合。

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

すべての例外には、構造化されたコード、メッセージ、およびヒントが含まれる。

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

ライブラリは、7つのComfyUIルート（`/system_stats`、`/object_info`、`/queue`、`/history`、`/prompt`、`/interrupt`、`/view`）と、バイナリ入力（オーディオアップロードも`/upload/image`を使用する。サーバーにはオーディオ専用のルートはない）用の`/upload/image`と`/upload/mask`にアクセスする。6つのプロファイルはすべて、その表面内に収まる。v3.1は、メッシュ、音楽、キャプション、およびプロベナンスを追加したが、単一のルートを追加しなかった。

`/object_info`は、特定のサーバーで実行できるものを決定する。これはライブエンドポイントであり、バージョン管理された成果物ではない。コアノードのレジストリに固定する必要はない。したがって、ライブラリは、固定されたノードセットを想定するのではなく、出力されたグラフをターゲットサーバーの実際のカタログに対して検証する。`check_workflow_dependencies()`はそのチェックであり、利便性ではなく、重要なインフラストラクチャである。

グラフ自体が必要な場合の便利なエスケープハッチ。

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## ドキュメント

完全なハンドブック：**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — 概要、使用方法、6つのプロファイル、ビデオモデル、設定、APIリファレンス、アーキテクチャ。

LLMおよびコントリビューター向けの**リポジトリ内のナレッジベース**：[`kb/`](kb/README.md) — プロファイルごとの事実ページ、実行可能な参照グラフ（`kb/workflows/*.json`、ビルダー自体から生成されるため、ドリフトすることはない）、およびノードプロベナンス（`kb/nodes.json`）の機械可読形式の[`index.json`](kb/index.json)。`python scripts/gen_kb.py`はそれを再生成する。テストスイートは、コードとナレッジベースが一致しない場合に失敗する。

## セキュリティとデータ範囲

- **アクセスされるデータ:** HTTP/WebSocket経由でローカルまたはリモートのComfyUIインスタンスに接続します。ワークフローJSONとアップロードされた画像を送信し、生成されたメディアを受信します。オプションで、プロンプトのインテリジェンスのためにローカルのOllamaに接続します。出力は、自動的にクリーンアップされる一時ディレクトリに書き込まれます。
- **アクセスされないデータ:** テレメトリ、分析、構成したComfyUIおよびOllamaエンドポイント以外の外部APIは使用しません。すべてのログ出力において、機密情報は`SecretValue`によってマスクされます。
- **必要な権限:** ComfyUIサーバーおよびオプションのOllamaサーバーへのネットワークアクセス。出力および一時ディレクトリへのファイル書き込み権限。
- **アップロード:** `upload_image`は、サブフォルダーへのアクセス試行を拒否します。アップロードされたファイルは、指定したサーバーのComfyUIの入力ディレクトリに保存されます。そのサーバーを信頼できるものとして扱ってください。

脆弱性に関する報告については、[SECURITY.md](SECURITY.md)を参照してください。

## スコアカード

| カテゴリ | スコア |
|----------|-------|
| A. セキュリティ | 10/10 |
| B. エラー処理 | 10/10 |
| C. 運用ドキュメント | 10/10 |
| D. リリース時の品質 | 10/10 |
| E. 識別（ソフト） | 10/10 |
| **Overall** | **50/50** |

> [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)を使用して評価

## 関連

[**MCP Tool Shop**](https://mcp-tool-shop.github.io/)の一部 — ローカルハードウェア向けのオープンソースの機械学習ツール。

## 貢献

問題やプルリクエストは大歓迎です。詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。貢献できる分野：追加のモデルファミリー、ワークフローテンプレート、ドキュメント、バグ修正。

ノードタイプを追加する場合は、まずライブのComfyUIカタログに存在することを確認し、コアでない場合はそのパッケージを宣言してください。このルールが、今回のリリースが存在する理由です。

## ライセンス

MIT — 詳細は[LICENSE](LICENSE)を参照してください。

---

[MCP Tool Shop](https://mcp-tool-shop.github.io/)によって作成
