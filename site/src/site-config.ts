import type { SiteConfig } from '@mcptoolshop/site-theme';

export const config: SiteConfig = {
  title: 'comfy-headless',
  description: 'Production-ready headless client for ComfyUI with AI-powered prompt intelligence, video generation, and modern Gradio UI.',
  logoBadge: 'CH',
  brandName: 'comfy-headless',
  repoUrl: 'https://github.com/mcp-tool-shop-org/comfy-headless',
  footerText: 'MIT Licensed — built by <a href="https://github.com/mcp-tool-shop-org" style="color:var(--color-muted);text-decoration:underline">mcp-tool-shop-org</a>',

  hero: {
    badge: 'Python · PyPI',
    headline: 'ComfyUI power,',
    headlineAccent: 'minus the complexity.',
    description: 'Production-ready headless client for ComfyUI. AI-powered prompt enhancement, 5+ video models, modular installs, and a Gradio UI — all from a clean Python API.',
    primaryCta: { href: '#quickstart', label: 'Quick start' },
    secondaryCta: { href: 'handbook/', label: 'Read the Handbook' },
    previews: [
      {
        label: 'Install',
        code: '# Recommended for most users\npip install comfy-headless[standard]\n\n# Core only (~2MB, no extras)\npip install comfy-headless',
      },
      {
        label: 'Generate',
        code: 'from comfy_headless import ComfyClient\n\nclient = ComfyClient()\nresult = client.generate_image("a beautiful sunset over mountains")\nprint(f"Generated: {result[\'images\']}")',
      },
      {
        label: 'Video',
        code: 'from comfy_headless import ComfyClient, VideoModel\n\nclient = ComfyClient()\nresult = client.generate_video(\n    "a timelapse of clouds over mountains",\n    model=VideoModel.LTXV,\n)\nprint(f"Video: {result[\'video\']}")',
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
          title: 'AI prompt intelligence',
          desc: 'Analyze and enhance prompts with Ollama before generation. The intelligence layer detects style, intent, and subject — then rewrites for better results automatically.',
        },
        {
          title: '5+ video model presets',
          desc: 'LTX-Video 2, Hunyuan 1.5, Wan, AnimateDiff, and more — each with curated default settings. One line to generate video; VRAM-aware preset recommendations included.',
        },
        {
          title: 'Modular by design',
          desc: 'Install only what you need. The core is ~2MB with zero heavy deps. Add [ai], [websocket], [ui], or [health] extras individually as your use case grows.',
        },
      ],
    },
    {
      kind: 'data-table',
      id: 'extras',
      title: 'Installation extras',
      subtitle: 'Mix and match — install only the capabilities you need.',
      columns: ['Extra', 'What it adds'],
      rows: [
        ['comfy-headless', 'Core HTTP client, workflow compiler, presets — no heavy deps'],
        ['comfy-headless[ai]', 'AI prompt analysis and enhancement via Ollama'],
        ['comfy-headless[websocket]', 'Real-time generation progress over WebSocket'],
        ['comfy-headless[ui]', 'Gradio 6.0 web interface with Ocean Mist theme'],
        ['comfy-headless[health]', 'Health checks and circuit-breaker retry logic'],
        ['comfy-headless[standard]', 'Recommended bundle: core + ai + websocket + health'],
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
          code: 'from comfy_headless import ComfyClient\n\nclient = ComfyClient()  # connects to localhost:8188\nresult = client.generate_image(\n    "a photorealistic forest at golden hour",\n)\nprint(result[\'images\'])',
        },
        {
          title: 'Generate video',
          code: 'from comfy_headless import ComfyClient, VideoModel, get_recommended_preset\n\nclient = ComfyClient()\npreset = get_recommended_preset(vram_gb=16)  # auto-select by VRAM\nresult = client.generate_video(\n    "a slow pan across a mountain range",\n    model=VideoModel.WAN,\n    settings=preset,\n)\nprint(result[\'video\'])',
        },
        {
          title: 'Launch the Gradio UI',
          code: '# Requires comfy-headless[ui]\npython -m comfy_headless.ui\n# → http://localhost:7860',
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
          desc: 'Simple presets and AI-powered prompt enhancement mean great results without prompt engineering expertise. Launch the Gradio UI and start generating immediately.',
        },
        {
          title: 'For developers',
          desc: 'Clean Python API with template-based workflow compilation. Full error taxonomy, circuit-breaker retry logic, and WebSocket progress hooks for production integration.',
        },
        {
          title: 'For pipelines',
          desc: 'Headless operation, modular installs, and configurable settings make comfy-headless easy to embed in automation workflows, CI image testing, or batch generation jobs.',
        },
      ],
    },
  ],
};
