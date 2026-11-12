<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
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

## De quoi il s'agit

comfy-headless crée des **graphiques au format ComfyUI** et les exécute. Vous appelez une fonction Python ; elle génère le graphique de nœuds JSON, l’envoie à ComfyUI, attend la fin de l’exécution et vous fournit les chemins de sortie.

Cette approche est importante, car elle vous indique ce qui peut mal se passer. La tâche principale de la bibliothèque consiste à générer des noms de nœuds et des clés d’entrée que le ComfyUI cible possède réellement. Lorsque ComfyUI renomme ou supprime un nœud, un graphique qui fait référence à l’ancien nom est rejeté lors de la soumission, avec une erreur opaque, et rien ne vous avertit au préalable.

**v3.0 est la version qui a pris cela au sérieux.** Chaque type de nœud que cette bibliothèque génère a été vérifié par rapport au catalogue ComfyUI en direct. Neuf n’existent plus. Ils ont disparu, les graphiques qui les utilisaient sont reconstruits sur des nœuds vérifiés, et la bibliothèque peut maintenant vous indiquer ce qui manque à un serveur *avant* que vous ne lanciez une exécution.

**v3.1 étend cette approche à six profils de flux de travail** — **Image, Vidéo, 3D, Inférence, Métadonnées, Audio** — sur une couche d’adressage/de typage partagée qui utilise les propres règles de validation de ComfyUI : correspondance de types d’union transcrite à partir du validateur du serveur, champs dynamiques à points (`codec.encoding.crf`) et entrées conditionnelles qui refusent les valeurs de branche inactive au moment de la construction. Même structure que précédemment : les maillages, la musique et les légendes sont renvoyés via `/history` + `/view` comme tous les autres éléments.

| Problème | Ce que fait comfy-headless |
|---------|--------------------------|
| L’interface de nœud est assez complexe | Préréglages et API Python claire |
| L’ingénierie des invites est difficile | Amélioration optionnelle par l’IA via Ollama local |
| La génération de vidéos est délicate | 26 préréglages dans 9 familles de modèles |
| « J’ai besoin d’un maillage à partir de cette image » | `generate_3d()` — Hunyuan3D-2, tous les nœuds principaux |
| « J’ai besoin de musique/de pistes » | `generate_audio()` (ACE-Step 1.5), `separate_audio()` |
| « Qu’y a-t-il dans cette image ? » | `run_inference()` — légende, balise, détection, segmentation, OCR |
| « Quel graphique a créé ce PNG ? » | `extract_prompt_graph()` / `rerun_from_png()` |
| « Quels paramètres dois-je utiliser ? » | Recommandations adaptées à votre VRAM |
| Les graphiques échouent avec des erreurs cryptiques | La vérification des dépendances indique le nom du nœud *et* du pack |

## Démarrage rapide

```bash
pip install comfy-headless[standard]
```

```python
from comfy_headless import ComfyClient

client = ComfyClient()                       # defaults to http://localhost:8188
result = client.generate_image("a beautiful sunset over mountains")
print(result["images"])
```

`generate_image` renvoie un `dict` avec `success`, `prompt_id`, `images`, `error`, `seed` et `preset`. Chaque appel de génération dans cette bibliothèque renvoie un dictionnaire ; il n’y a pas d’objet de résultat à extraire.

## Installation

```bash
pip install comfy-headless              # core only, ~2MB
pip install comfy-headless[standard]    # + AI enhancement + WebSocket (recommended)
pip install comfy-headless[full]        # everything
```

| Compléments | Ajoute |
|-------|------|
| `ai` | Analyse et amélioration des invites via Ollama local |
| `websocket` | Suivi en temps réel via WebSocket |
| `ui` | Interface web Gradio |
| `health` | Surveillance de l’état du système |
| `validation` | Validation de la configuration Pydantic |
| `observability` | Tracé OpenTelemetry |
| `standard` | `ai` + `websocket` |
| `full` | Tout ce qui précède |

Nécessite **Python 3.10+** et une instance ComfyUI en cours d’exécution.

Vérifiez ce qui est actif au moment de l’exécution :

```python
from comfy_headless import FEATURES, list_missing_features

print(FEATURES)                 # {'ai': True, 'websocket': True, 'health': False, ...}
print(list_missing_features())  # {'health': 'pip install comfy-headless[health]', ...}
```

## Images

```python
result = client.generate_image(
    "a cyberpunk street at night",
    negative_prompt="blurry, low quality",
    preset="hd",          # overrides width/height/steps/cfg when set
    seed=42,
)
```

Huit préréglages d’image : `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`.

Traitez par lots une liste d’invites :

```python
result = client.generate_batch(
    ["a red fox", "a snowy owl", "a grey wolf"],
    preset="fast",
)
```

### Amélioration de l’IA des invites

Nécessite le complément `[ai]` et un Ollama local. Il s’agit de **fonctions au niveau du module**, et non de méthodes client :

```python
from comfy_headless import enhance_prompt, analyze_prompt

result = enhance_prompt("a cat", style="balanced")
print(result.enhanced)   # .original .enhanced .negative .additions .reasoning

analysis = analyze_prompt("a cyberpunk city at night")
print(analysis.intent, analysis.styles, analysis.suggested_preset)
```

### Qwen-Image (nouveau dans la version 3.1)

Qwen-Image-2512, la génération d’images à partir de texte, est fourni en tant que modèle `qwen_txt2img`, avec la recette que le modèle souhaite réellement, intégrée : chemin `UNETLoader`, 16 canaux `EmptySD3LatentImage` (le latent SDXL produit des résultats médiocres sur les modèles DiT), 20 étapes, **cfg 2.5**, décalage 3.1, plage native 1328 x 1328 :

```python
from comfy_headless import compile_workflow

compiled = compile_workflow("a castle above the clouds", template_id="qwen_txt2img")
prompt_id = client.queue_prompt(compiled.workflow)
```

Édition d’instructions avec jusqu’à trois images de référence (Qwen-Image-Edit-2511) :

```python
result = client.edit_image(
    "make it night, keep the composition",
    images=["photo.png"],          # local paths, bytes, or uploaded refs — 1 to 3
)
```

Les références alimentent `TextEncodeQwenImageEditPlus` en tant qu’entrées `image1..image3` discrètes et ne passent pas par VAEEncode, qui est la forme du graphique que le nœud attend réellement.

### ControlNet (nouveau dans la version 3.1)

Un seul chemin de code couvre l’union Qwen et SDXL ControlNets :

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

Seul le préprocesseur principal `Canny` est généré (`preprocess="canny"`) ; les autres types d’indices attendent une image de contrôle pré-créée, car leurs préprocesseurs se trouvent dans un pack personnalisé que cette bibliothèque ne requiert pas silencieusement.

## Vidéo

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

La sélection se fait **par préréglage**, et non par modèle : `generate_video` n’a pas d’argument `model`. N’importe lequel de `frames`, `fps`, `steps`, `cfg`, `width`, `height` peut être transmis pour remplacer le préréglage.

### Entrée d’image

La conversion d’image en vidéo, et tout autre élément qui utilise une image source, nécessite que cette image existe d’abord dans ComfyUI. Téléchargez-la, puis transmettez le nom que le serveur renvoie :

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Lisez `name` à partir de la réponse plutôt que de réutiliser le nom de fichier que vous avez envoyé : ComfyUI renomme en cas de conflit, de sorte que les deux ne sont pas toujours égaux. `ref` est la même valeur déjà jointe à tout sous-dossier, ce qui est exactement ce dont le graphique a besoin.

> **Modifié dans la version 3.0 :** `init_image` est un nom de fichier côté serveur. Les versions antérieures acceptaient les données base64 et les transmettaient via un nœud tiers qui n’existe pas dans une installation ComfyUI standard. Voir le [JOURNAL DES MODIFICATIONS](CHANGELOG.md).

> **Nouveau dans la version 3.1 :** La conversion d’image en vidéo Hunyuan 1.5 est une vraie i2v : les préréglages `hunyuan15_i2v` et `hunyuan15_i2v_fast` sont basés sur le nœud principal `HunyuanVideo15ImageToVideo` et nécessitent un `init_image` (v3.0 a silencieusement créé un graphique de conversion de texte en vidéo à la place). Et `output="core"` remplace le terminateur `VHS_VideoCombine` par le terminateur principal `CreateVideo → SaveVideo`, supprimant complètement la dépendance de la suite d’aide vidéo.

### Familles de modèles

| Famille | VRAM minimale | Qualité | Vitesse | Nœuds supplémentaires | Idéal pour |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 Go | Excellent | Moyenne | — | Faible VRAM, efficacité |
| AnimateDiff Lightning | 6 Go | Correct | La plus rapide | AnimateDiff-Evolved | 4 étapes d’ébauche |
| AnimateDiff | 8 Go | Bon | Rapide | AnimateDiff-Evolved, interpolation d’images | Aperçus rapides |
| **LTX-Video** | 12 Go | Excellent | Rapide | — | La valeur par défaut sûre |
| **Mochi** | 12 Go | Excellent | Lent | — | Respect des contraintes de texte, clips longs |
| **SVD** | 12 Go | Bon | Moyenne | — | Animer une image fixe |
| **Hunyuan 1.5** | 14 Go | Meilleur | Lent | — | Qualité la plus élevée |
| CogVideoX | 16 Go | Bon | Lent | CogVideoX Enveloppe | Ancien |
| **Hunyuan 1.0** | 24 Go | Excellent | Lent | Interpolation d'images | Remplacé par la version 1.5 |

Six des neuf familles fonctionnent sur des **nœuds de base ComfyUI** — aucun pack d'enveloppe pour le modèle lui-même. Seuls AnimateDiff (les deux variantes) et CogVideoX en ont besoin. La sortie vidéo utilise [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) ; l'interpolation d'images utilise [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Les chiffres de la VRAM représentent la valeur minimale pour la résolution par défaut de chaque famille, lus à partir de `VIDEO_MODEL_INFO` — et non la valeur maximale. Plus de mémoire permet d'obtenir des clips plus longs et des résolutions plus élevées pour la même famille.

### Vérifiez avant de lancer

Plutôt que de découvrir un nœud manquant au moment de la soumission :

```python
workflow = client.build_video_workflow("a cat walking")

report = client.check_workflow_dependencies(workflow)
print(report["missing_packs"])     # what this server is missing
print(report["required_packs"])    # what this graph needs

# or raise MissingNodePackError, naming the class and the pack that provides it
client.require_workflow_dependencies(workflow)
```

Vous pouvez également vérifier les arêtes d'un graphe par rapport au serveur en direct, en utilisant la règle d'acceptation du serveur (de sorte qu'un nœud `MESH` alimentant une entrée d'union `FILE_3D_*` ne soit jamais rejeté à tort) :

```python
report = client.check_workflow_types(workflow)
print(report["errors"])     # edges the server would reject
print(report["warnings"])   # accepted edges with partial type overlap
```

## 3D (nouveau dans la version 3.1)

Image vers maillage via **Hunyuan3D-2** — entièrement des nœuds de base ComfyUI, aucun pack d'enveloppe, aucune nouvelle route. Les GLB sont enregistrés dans `/history` exactement comme un PNG et téléchargés via `/view` :

```python
result = client.generate_3d("character.png", preset="detail")
# presets: standard / draft / detail
glb = client.get_file(**result["meshes"][0])
open("character.glb", "wb").write(glb)
```

`generate_3d` accepte un chemin local, des octets bruts, un dictionnaire `upload_image()` ou une référence côté serveur, et télécharge automatiquement lorsque cela est nécessaire. Il s'agit d'un simple conditionnement d'image — il n'y a pas d'invite de texte dans le graphe. Paramètres ajustables : `steps` (30), `cfg` (5,5), `octree_resolution` (256), `threshold` (0,6), `seed`.

Les modèles 3D avec pack d'enveloppe (TRELLIS, TripoSG, ...) ne sont pas générés intentionnellement — les dépendances natives de ComfyUI-3D-Pack sont les moins stables de l'écosystème.

## Audio (nouveau dans la version 3.1)

Texte vers musique via **ACE-Step 1.5** — code et poids sous licence MIT, nœuds de base natifs, zéro pack. Le point de contrôle turbo fonctionne à 8 étapes / cfg 1 :

```python
result = client.generate_audio(
    tags="lo-fi, jazz, mellow, rainy night",
    lyrics="",                       # empty = instrumental
    preset="music",                  # music / music_long / jingle / music_mp3 / draft
    seconds=30,
)
flac = client.get_file(**result["audios"][0])
```

Le générateur applique la contrainte de couplage du modèle pour vous : l'encodeur `duration` et la latence `seconds` sont un seul paramètre logique, contrôlé à partir d'un seul champ — l'exécution ne valide pas les paramètres croisés, et une incompatibilité se termine « avec succès » avec une sortie silencieusement incorrecte. La sortie passe par `SaveAudioAdvanced` (le seul nœud d'enregistrement audio non obsolète) ; la sortie `flac` n'émet aucun champ de qualité, `mp3`/`opus` émettent le sous-champ `format.quality`.

Séparation des pistes (nécessite le pack `audio-separation-nodes-comfyui`) :

```python
result = client.separate_audio("song.flac")            # bass, drums, other, vocals
result = client.separate_audio("song.flac", stems=["vocals"])
```

## Inférence (nouveau dans la version 3.1)

Appels de modèles non génératifs — posez des questions sur une image au lieu d'en créer une. Fonctionne sur Florence-2 (pack `comfyui-florence2` ; la tâche de détection ajoute `comfyui-segment-anything-2`) :

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

La règle de charge du profil : un résultat atteint `/history` uniquement via un nœud de sortie. Chaque graphe d'inférence se termine dans le nœud de base `SaveText` (qui affiche le texte en ligne — pas de deuxième échange) ou `SaveImage` pour les masques, et le générateur refuse de générer un graphe qui fonctionnerait et ne renverrait rien.

## Provenance (nouveau dans la version 3.1)

ComfyUI intègre le **graphe exact au format API** dans chaque PNG de sortie. comfy-headless le relit — pure stdlib, pas de Pillow — et peut le réexécuter tel quel :

```python
from comfy_headless import read_workflow_metadata, extract_prompt_graph

record = read_workflow_metadata("output.png")
print(record.prompt is not None)     # the machine-runnable graph
print(record.extra)                  # your custom keys land here

graph = extract_prompt_graph("output.png")   # raises with a hint if scrubbed
result = client.rerun_from_png("output.png") # re-POSTs it verbatim
```

Écrivez une provenance personnalisée sans aucun nœud personnalisé — tout ce qui se trouve dans `extra_pnginfo` devient un bloc de texte PNG dans les sorties :

```python
client.queue_prompt(workflow, extra_pnginfo={"myapp:run_id": "r-2026-077"})
```

Limites connues, documentées plutôt que cachées : WebP/JPEG contiennent les mêmes données dans EXIF (un chemin de lecteur différent, non implémenté) ; les sorties vidéo n'intègrent pas le graphe ; les déploiements renforcés peuvent supprimer les clés inconnues ; et la conversion GUI→API n'a pas de route côté serveur — utilisez « Workflow → Export (API) » de ComfyUI.

## Configuration

Les variables d'environnement utilisent le préfixe `COMFY_HEADLESS_` avec les délimiteurs de section `__` :

| Variable | Valeur par défaut |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | délai d'attente de lecture, en secondes |
| `COMFY_HEADLESS_LOGGING__LEVEL` | niveau de journalisation |

Ou passez l'URL directement : `ComfyClient("http://192.168.1.50:8188")`.

## Interface utilisateur Web

```bash
comfy-headless                 # launching the UI is the default action
```

| Indicateur | Signification |
|------|---------|
| `--port` / `-p` | Port de l'interface utilisateur (par défaut : `7861`) |
| `--share` | Lien de partage Gradio public |
| `--url` | URL du serveur ComfyUI |
| `--version` / `-v` | Afficher la version |
| `--check` | Disponibilité des fonctionnalités |
| `--diagnose` | Diagnostics complets |

Six onglets : Image, Vidéo, File d'attente et historique, Flux de travail, Modèles, Paramètres. Le thème est Ocean Mist — des accents bleu turquoise doux sur des arrière-plans neutres chauds.

Par programmation (nécessite `[ui]`) :

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progression

Les appels bloquants prennent un rappel `on_progress` :

```python
client.generate_image("a fox", on_progress=lambda pct, msg: print(f"{pct:.0%} {msg}"))
```

Pour les mises à jour en temps réel via WebSocket (nécessite `[websocket]`) :

```python
import asyncio
from comfy_headless import ComfyWSClient

async def main():
    async with ComfyWSClient() as ws:
        prompt_id = await ws.queue_prompt(workflow)
        return await ws.wait_for_completion(prompt_id)

asyncio.run(main())
```

## Erreurs

Chaque exception contient un code, un message et un indice structurés :

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

## Comment cela fonctionne

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

La bibliothèque communique avec sept routes ComfyUI — `/system_stats`, `/object_info`, `/queue`, `/history`, `/prompt`, `/interrupt`, `/view` — ainsi que `/upload/image` et `/upload/mask` pour les entrées binaires (les téléchargements audio passent également par `/upload/image` ; le serveur n'a pas de route audio spécifique). Les six profils s'intègrent dans cette surface : v3.1 a ajouté des maillages, de la musique, des légendes et une provenance sans ajouter une seule route.

`/object_info` est l'autorité sur ce qu'un serveur donné peut exécuter. Il s'agit d'un point de terminaison en direct, et non d'un artefact versionné : il n'y a pas de registre de nœuds de base auquel se référer. Par conséquent, la bibliothèque valide les graphes générés par rapport au catalogue réel du serveur cible plutôt que de supposer un ensemble de nœuds fixe. `check_workflow_dependencies()` est cette vérification, et il s'agit d'une infrastructure essentielle plutôt que d'un simple outil.

Des moyens pratiques de sortir lorsque vous voulez le graphe lui-même :

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentation

Manuel complet : **[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — prise en main, utilisation, les six profils, modèles vidéo, configuration, référence de l'API, architecture.

**Base de connaissances dans le dépôt** pour les LLM et les contributeurs : [`kb/`](kb/README.md) — une [`index.json`](kb/index.json) lisible par machine sur des pages de faits par profil, des graphes de référence exécutables (`kb/workflows/*.json`, générés à partir des générateurs eux-mêmes afin qu'ils ne puissent pas dériver) et la provenance des nœuds (`kb/nodes.json`). `python scripts/gen_kb.py` le régénère ; la suite de tests échoue si le code et la base de connaissances sont en désaccord.

## Sécurité et portée des données

- **Données concernées :** se connecte à une instance ComfyUI locale ou distante via HTTP/WebSocket.
Envoie le JSON du flux de travail et les images téléchargées, reçoit les médias générés. Se connecte éventuellement à une instance locale d’Ollama pour l’intelligence des invites. Écrit les résultats dans des répertoires temporaires avec une suppression automatique.
- **Données non concernées :** aucune télémétrie, aucune analyse, aucune API externe autre que les points de terminaison ComfyUI et Ollama que vous configurez. Les informations sensibles sont masquées dans tous les journaux via `SecretValue`.
- **Autorisations requises :** accès réseau à votre serveur ComfyUI et, éventuellement, à un serveur Ollama ; autorisation d’écriture de fichiers pour les résultats et les répertoires temporaires.
- **Téléchargements :** `upload_image` rejette les tentatives de navigation dans les sous-dossiers. Les fichiers téléchargés sont placés dans le répertoire d’entrée de ComfyUI sur le serveur que vous spécifiez ; considérez ce serveur comme étant de confiance.

Pour signaler les vulnérabilités, consultez le fichier [SECURITY.md](SECURITY.md).

## Évaluation

| Catégorie | Score |
|----------|-------|
| A. Sécurité | 10/10 |
| B. Gestion des erreurs | 10/10 |
| C. Documentation pour les opérateurs | 10/10 |
| D. Qualité de la distribution | 10/10 |
| E. Identité (souple) | 10/10 |
| **Overall** | **50/50** |

> Évalué avec [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Éléments connexes

Fait partie de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) : ensemble d’outils d’apprentissage automatique open source pour le matériel local.

## Contribution

Les problèmes et les demandes de modification sont les bienvenus ; consultez le fichier [CONTRIBUTING.md](CONTRIBUTING.md). Domaines utiles : familles de modèles supplémentaires, modèles de flux de travail, documentation, corrections de bogues.

Si vous ajoutez un type de nœud, vérifiez d’abord qu’il existe dans le catalogue ComfyUI en cours, puis déclarez son paquet s’il n’est pas un élément de base. Cette règle explique pourquoi cette version existe.

## Licence

MIT ; consultez le fichier [LICENSE](LICENSE).

---

Créé par [MCP Tool Shop](https://mcp-tool-shop.github.io/)
