import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'comfy-headless',
  description:
    'Drive ComfyUI from Python. Builds and runs ComfyUI API-format graphs — image and video generation, verified node types, and a clean API with no node canvas.',
  logoBadge: 'CH',
  brandName: 'comfy-headless',
  repoUrl: 'https://github.com/mcp-tool-shop-org/comfy-headless',
  footerText:
    'MIT Licensed — built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'Python · PyPI',
    headline: 'Drive ComfyUI from Python.',
    headlineAccent: 'No node graph.',
    description:
      'comfy-headless builds ComfyUI API-format graphs and runs them. 8 image presets, 24 video presets across 9 model families, optional AI prompt enhancement — and every node type it emits is verified against the live ComfyUI catalog.',
    primaryCta: { href: '#quickstart', label: 'Quick start' },
    secondaryCta: { href: 'handbook/', label: 'Read the Handbook' },
    previews: [
      {
        label: 'Install',
        code: '# Recommended for most users\npip install comfy-headless[standard]\n\n# Core only (~2MB, no extras)\npip install comfy-headless',
      },
      {
        label: 'Generate',
        code: 'from comfy_headless import ComfyClient\n\nclient = ComfyClient()\nresult = client.generate_image("a beautiful sunset over mountains")\nprint(result["images"])',
      },
      {
        label: 'Video',
        code: 'from comfy_headless import ComfyClient\n\nclient = ComfyClient()\nresult = client.generate_video(\n    "a slow pan across a mountain range",\n    preset="ltx_quality",\n)\nprint(result["videos"])',
      },
    ],
  },

  sections: [
    {
      kind: 'features',
      id: 'features',
      title: 'Everything ComfyUI, none of the node graph',
      subtitle: 'A clean API over the full ComfyUI feature set.',
      features: [
        {
          title: 'Verified node graphs',
          desc: 'Every node type this library emits is checked against the live ComfyUI catalog. Ask a server what it is missing before you spend a run — dependency errors name the node and the pack that provides it, not a bare validation failure.',
        },
        {
          title: '24 video presets, 9 families',
          desc: 'LTX-Video, Hunyuan 1.5, Wan, Mochi, SVD, AnimateDiff and CogVideoX, each with curated resolution, frame count and step settings. Six of the nine run on stock ComfyUI core nodes — no wrapper packs.',
        },
        {
          title: 'AI prompt intelligence',
          desc: 'Analyse and enhance prompts with a local Ollama before generating. Detects intent, style and subject, then rewrites the prompt and builds a matching negative. Entirely optional and entirely local.',
        },
        {
          title: 'Modular by design',
          desc: 'The core is around 2MB with no heavy dependencies. AI, WebSocket, the web UI, health checks, validation and tracing are opt-in extras that load lazily on first use.',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'extras',
      title: 'Installation extras',
      subtitle: 'Install only the capabilities you need.',
      columns: ['Extra', 'What it adds'],
      rows: [
        ['comfy-headless', 'Core client, graph builders, presets — no heavy deps'],
        ['comfy-headless[ai]', 'Prompt analysis and enhancement via local Ollama'],
        ['comfy-headless[websocket]', 'Real-time generation progress over WebSocket'],
        ['comfy-headless[ui]', 'Gradio web interface, Ocean Mist theme'],
        ['comfy-headless[health]', 'System health checks and monitoring'],
        ['comfy-headless[validation]', 'Pydantic-backed configuration validation'],
        ['comfy-headless[observability]', 'OpenTelemetry tracing'],
        ['comfy-headless[standard]', 'Recommended: core + ai + websocket'],
        ['comfy-headless[full]', 'Everything above'],
      ],
    },
    {
      kind: 'code-cards',
      id: 'quickstart',
      title: 'Quick start',
      cards: [
        {
          title: 'Install',
          code: 'pip install comfy-headless[standard]',
        },
        {
          title: 'Generate an image',
          code: 'from comfy_headless import ComfyClient\n\nclient = ComfyClient()  # connects to localhost:8188\nresult = client.generate_image(\n    "a photorealistic forest at golden hour",\n    preset="hd",\n)\nprint(result["images"])',
        },
        {
          title: 'Generate video',
          code: 'from comfy_headless import ComfyClient, get_recommended_preset\n\nclient = ComfyClient()\npreset = get_recommended_preset(vram_gb=16)  # sized to your card\nresult = client.generate_video(\n    "a slow pan across a mountain range",\n    preset=preset,\n)\nprint(result["videos"])',
        },
        {
          title: 'Check before you run',
          code: 'workflow = client.build_video_workflow("a cat walking")\n\nreport = client.check_workflow_dependencies(workflow)\nprint(report["missing_packs"])  # empty means ready\n\n# or raise MissingNodePackError\nclient.require_workflow_dependencies(workflow)',
        },
        {
          title: 'Launch the web UI',
          code: '# Requires comfy-headless[ui]\ncomfy-headless\n# -> http://localhost:7861',
        },
      ],
    },
    {
      kind: 'features',
      id: 'design',
      title: 'Built for every level',
      subtitle: 'From quick experiments to production pipelines.',
      features: [
        {
          title: 'For users',
          desc: 'Presets and optional AI prompt enhancement mean good results without prompt-engineering expertise. Launch the web UI and start generating immediately.',
        },
        {
          title: 'For developers',
          desc: 'A clean Python API with escape hatches to the raw graph. Structured errors carrying a code, message and hint; circuit-breaker retry; WebSocket progress hooks.',
        },
        {
          title: 'For pipelines',
          desc: 'Headless operation, modular installs and environment-driven configuration make it easy to embed in automation, CI image testing, or batch generation.',
        },
      ],
    },
  ],
};
