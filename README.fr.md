<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.md">English</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/mcp-tool-shop-org/brand/main/logos/comfy-headless/readme.png" alt="comfy-headless" width="400">
</p>

<p align="center">
  <strong>Pilotez ComfyUI avec Python. Plus besoin de schéma nodulaire.</strong>
</p>

<p align="center">
  <a href="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml"><img src="https://github.com/mcp-tool-shop-org/comfy-headless/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless"><img src="https://codecov.io/gh/mcp-tool-shop-org/comfy-headless/branch/main/graph/badge.svg" alt="Codecov"></a>
  <a href="https://pypi.org/project/comfy-headless/"><img src="https://img.shields.io/pypi/v/comfy-headless?color=blue&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License"></a>
  <a href="https://mcp-tool-shop-org.github.io/comfy-headless/"><img src="https://img.shields.io/badge/Landing_Page-live-blue" alt="Landing Page"></a>
</p>

---

## De quoi il s’agit

comfy-headless crée des **graphiques au format API ComfyUI** et les exécute. Vous appelez une fonction Python ; elle génère le graphique de nœuds JSON, l’envoie à ComfyUI via POST, vérifie son achèvement et vous fournit les chemins de sortie.

Cette approche est importante car elle vous indique ce qui peut mal se passer. La tâche principale de la bibliothèque consiste à générer des noms de nœuds et des clés d’entrée que ComfyUI cible possède réellement. Lorsque ComfyUI renomme ou supprime un nœud, un graphique référençant l’ancien nom est rejeté lors de sa soumission avec une erreur opaque, et rien ne vous avertit au préalable.

**La version 3.0 prend cette question très au sérieux.** Chaque type de nœud que cette bibliothèque génère a été vérifié par rapport au catalogue ComfyUI en direct. Neuf n’existent plus. Ils ont disparu, les graphiques qui les utilisaient sont reconstruits sur des nœuds vérifiés, et la bibliothèque peut maintenant vous indiquer ce qui manque à un serveur *avant* que vous ne lanciez une exécution.

| Problème | Ce que fait comfy-headless |
|---------|--------------------------|
| L’interface des nœuds est assez complexe. | Préréglages et API Python propre |
| L’ingénierie des invites est difficile. | Amélioration optionnelle par l’IA via Ollama local |
| La génération de vidéos est délicate. | 24 préréglages répartis dans 9 familles de modèles |
| « Quels paramètres dois-je utiliser ? » | Recommandations adaptées à votre VRAM |
| Les graphiques échouent avec des erreurs cryptiques. | La vérification des dépendances indique le nom du nœud *et* du pack. |

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
| `observability` | Traçage OpenTelemetry |
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

Huit préréglages d’images : `draft`, `fast`, `quality`, `hd`, `portrait`, `landscape`, `cinematic`, `square`.

Traitez une liste d’invites :

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

## Vidéo

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

La sélection se fait **par préréglage**, et non par modèle ; `generate_video` n’a pas d’argument `model`. N’importe lequel des éléments `frames`, `fps`, `steps`, `cfg`, `width`, `height` peut être transmis pour remplacer le préréglage.

### Image en entrée

La conversion d’image en vidéo, et tout autre processus utilisant une image source, nécessite que cette image existe au préalable dans ComfyUI. Téléchargez-la, puis transmettez le nom renvoyé par le serveur :

```python
ref = client.upload_image("reference.png")
# {"name": "reference.png", "subfolder": "", "type": "input", "ref": "reference.png"}

result = client.generate_video(
    "a cat walking through a garden",
    preset="wan_14b",
    init_image=ref["name"],
)
```

Récupérez `name` à partir de la réponse plutôt que de réutiliser le nom de fichier que vous avez envoyé ; ComfyUI renomme les fichiers en cas de conflit, de sorte que les deux ne sont pas toujours identiques. `ref` est la même valeur déjà combinée avec tout sous-dossier, ce qui correspond exactement à ce dont le graphique a besoin.

> **Modifié dans la version 3.0 :** `init_image` est un nom de fichier côté serveur. Les versions antérieures acceptaient des données base64 et les transmettaient via un nœud tiers qui n’existe pas dans une installation ComfyUI standard. Consultez le [JOURNAL DES MODIFICATIONS](CHANGELOG.md).

### Familles de modèles

| Famille | VRAM minimale | Qualité | Vitesse | Nœuds supplémentaires | Idéal pour |
|--------|----------|---------|-------|-------------|----------|
| **Wan 2.1/2.2** | 6 Go | Excellent | Moyen | — | Faible VRAM, efficacité |
| AnimateDiff Lightning | 6 Go | Correct | Le plus rapide | AnimateDiff-Evolved | Brouillons en 4 étapes |
| AnimateDiff | 8 Go | Bon | Rapide | AnimateDiff-Evolved, interpolation d’images. | Aperçus rapides |
| **LTX-Video** | 12 Go | Excellent | Rapide | — | La valeur par défaut la plus sûre |
| **Mochi** | 12 Go | Excellent | Lent | — | Adhérence au texte, clips longs |
| **SVD** | 12 Go | Bon | Moyen | — | Animation d’une image fixe |
| **Hunyuan 1.5** | 14 Go | Le meilleur | Lent | — | Qualité la plus élevée |
| CogVideoX | 16 Go | Bon | Lent | Enveloppe CogVideoX | Ancien |
| **Hunyuan 1.0** | 24 Go | Excellent | Lent | Interpolation d’images | Remplacé par la version 1.5 |

Six des neuf familles fonctionnent sur les **nœuds principaux ComfyUI standard** ; aucun pack d’enveloppe pour le modèle lui-même. Seuls AnimateDiff (les deux variantes) et CogVideoX en ont besoin. La sortie vidéo utilise [Video Helper Suite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) ; l’interpolation d’images utilise [Frame Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation).

Les chiffres de VRAM représentent le minimum pour la résolution par défaut de cette famille, lu dans `VIDEO_MODEL_INFO` ; ce ne sont pas des valeurs maximales. Plus de mémoire permet d’obtenir des clips plus longs et une résolution plus élevée à partir de la même famille.

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

## Configuration

Les variables d’environnement utilisent le préfixe `COMFY_HEADLESS_` avec des délimiteurs de section `__` :

| Variable | Valeur par défaut |
|----------|---------|
| `COMFY_HEADLESS_COMFYUI__URL` | `http://localhost:8188` |
| `COMFY_HEADLESS_OLLAMA__URL` | `http://localhost:11434` |
| `COMFY_HEADLESS_OLLAMA__MODEL` | `qwen2.5:7b` |
| `COMFY_HEADLESS_COMFYUI__TIMEOUT_READ` | délai d’attente de lecture, en secondes |
| `COMFY_HEADLESS_LOGGING__LEVEL` | niveau de journalisation |

Ou passez l’URL directement : `ComfyClient("http://192.168.1.50:8188")`.

## Interface utilisateur web

```bash
comfy-headless                 # launching the UI is the default action
```

| Indicateur | Signification |
|------|---------|
| `--port` / `-p` | Port de l’interface utilisateur (par défaut : `7861`) |
| `--share` | Lien de partage public Gradio |
| `--url` | URL du serveur ComfyUI |
| `--version` / `-v` | Afficher la version |
| `--check` | Disponibilité des fonctionnalités |
| `--diagnose` | Diagnostics complets |

Six onglets : Image, Vidéo, File d’attente et historique, Flux de travail, Modèles, Paramètres. Le thème est Ocean Mist —
des touches de bleu turquoise sur un fond neutre chaud.

De manière programmatique (nécessite `[ui]`) :

```python
from comfy_headless import launch
launch(port=7861, share=False)
```

## Progression

Les appels bloquants nécessitent une fonction de rappel `on_progress` :

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

Chaque exception contient un code, un message et une indication structurés :

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

## Comment cela fonctionne

```
your call ─→ build API-format graph ─→ POST /prompt ─→ poll /history ─→ GET /view
                     │
                     └─ validated against GET /object_info
```

La bibliothèque communique avec sept routes ComfyUI — `/system_stats`, `/object_info`, `/queue`,
`/history`, `/prompt`, `/interrupt`, `/view` — ainsi que `/upload/image` et `/upload/mask` pour
les entrées binaires.

`/object_info` est la référence en matière de ce qu’un serveur donné peut exécuter. Il s’agit d’une interface active, et non
d’un artefact versionné : il n’existe pas de registre central pour les nœuds auxquels se référer. La bibliothèque valide donc les graphiques générés par rapport au catalogue réel du serveur cible plutôt que de supposer un
ensemble fixe de nœuds. `check_workflow_dependencies()` est cette vérification, et il s’agit d’une infrastructure essentielle plutôt qu’un simple outil.

Des solutions pratiques lorsque vous souhaitez accéder au graphique lui-même :

```python
workflow = client.build_txt2img_workflow("a fox")   # the raw API-format dict
prompt_id = client.queue_prompt(workflow)           # submit it yourself
client.wait_for_completion(prompt_id)
```

## Documentation

Manuel complet :
**[mcp-tool-shop-org.github.io/comfy-headless](https://mcp-tool-shop-org.github.io/comfy-headless/handbook/)** — prise en main, utilisation, configuration, référence de l’API, modèles vidéo, architecture.

## Sécurité et portée des données

- **Données concernées :** se connecte à une instance ComfyUI locale ou distante via HTTP/WebSocket.
Envoie le JSON du flux de travail et les images téléchargées, reçoit les médias générés. Se connecte éventuellement
à un Ollama local pour l’intelligence des invites. Écrit les résultats dans des répertoires temporaires avec
une suppression automatique.
- **Données NON concernées :** pas de télémétrie, pas d’analyses, pas d’API externes autres que les points de terminaison ComfyUI
et Ollama que vous configurez. Les informations sensibles sont masquées dans tous les journaux via
`SecretValue`.
- **Autorisations requises :** accès réseau à votre serveur ComfyUI et éventuellement à un serveur Ollama ; autorisation d’écriture de fichiers pour les sorties et les répertoires temporaires.
- **Téléchargements :** `upload_image` rejette les tentatives de traversée des sous-dossiers. Les fichiers téléchargés sont placés dans
le répertoire d’entrée de ComfyUI sur le serveur que vous spécifiez — considérez ce serveur comme étant de confiance.

Consultez [SECURITY.md](SECURITY.md) pour signaler les vulnérabilités.

## Tableau de bord

| Catégorie | Score |
|----------|-------|
| A. Sécurité | 10/10 |
| B. Gestion des erreurs | 10/10 |
| C. Documentation pour les utilisateurs | 10/10 |
| D. Qualité de la publication | 10/10 |
| E. Identité (souple) | 10/10 |
| **Overall** | **50/50** |

> Évalué avec [`@mcptoolshop/shipcheck`](https://github.com/mcp-tool-shop-org/shipcheck)

## Éléments connexes

Fait partie de [**MCP Tool Shop**](https://mcp-tool-shop.github.io/) — outils d’apprentissage automatique open source pour
le matériel local.

## Contribution

Les problèmes et les demandes de fusion sont les bienvenus — consultez [CONTRIBUTING.md](CONTRIBUTING.md). Domaines utiles :
familles de modèles supplémentaires, modèles de flux de travail, documentation, corrections de bugs.

Si vous ajoutez un type de nœud, vérifiez d’abord qu’il existe dans le catalogue ComfyUI actif, puis déclarez son
ensemble s’il n’est pas un élément central. Cette règle explique pourquoi cette version a été publiée.

## Licence

MIT — consultez [LICENSE](LICENSE).

---

Créé par [MCP Tool Shop](https://mcp-tool-shop.github.io/)
