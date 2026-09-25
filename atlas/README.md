# comfy-headless: how it works

Mapped at 2026-09-25 from commit bfb7973.

## What this is

9 parts, mostly Python (83 files), TypeScript (2) and JavaScript (1). Work enters through 4 doors; the busiest is CI, which reaches 3 parts. It publishes to PyPI and a container image. People run comfy-headless.

## What changed since the last map

This is the first map.

## What comes in

1. **CI.** On a pull request to main; on a push to main touching 5 paths; or by hand. Runs tests/; checks comfy_headless/ and scripts/.
2. **Publish.** When a release is published; or by hand. Runs comfy_headless/__init__.py and comfy_headless/__main__.py; checks comfy_headless/. On a release event, it also checks LICENSE, README.md and pyproject.toml.
3. **Deploy site to GitHub Pages.** On a push to main touching 2 paths; or by hand. Runs site/astro.config.mjs and site/src/.
4. **comfy-headless** (a command people run). Runs comfy_headless/__main__.py.

## What happens through CI

1. The workflow runs tests/ in tests; it checks comfy_headless/ in comfy_headless and scripts/ in scripts.

## Who reads the results

CI writes nothing this map can see.

## The other doors

**Publish** runs comfy_headless/__init__.py and comfy_headless/__main__.py, checks comfy_headless/, checks LICENSE, README.md and pyproject.toml on a release event, publishes a container image on a release event, and publishes to PyPI (on a run by hand, only with dry_run false).

**Deploy site to GitHub Pages** runs site/astro.config.mjs and site/src/, and deploys the site.

**comfy-headless** (a command people run) runs comfy_headless/__main__.py.

## What breaks what

- **comfy_headless** is imported by 1 part (scripts), and by 1 more only from tests; it sits on the path of 3 doors.
- **scripts** is imported only from tests, by 1 part (tests), and sits on the path of 1 door.

## What tends to change together

No two source files changed together often enough to name.

Window: 180 days; a pair counts from 3 shared commits, since the window holds fewer than 30 qualifying commits.

## What no test touches

Every code part is imported by at least one test.

## Written but never read

Every written place has a reader.

## Helpers that look duplicated

No two parts export a helper that looks alike.

## Generated, never hand-edited

- **kb/** is written by scripts/gen_kb.py.

## Hand-authored

People write .github/, assets/, docs/, the repository root and site/; 2 writes with paths built at run time may land here.

## Where to start

comfy_headless/__main__.py → comfy_headless/feature_flags.py → comfy_headless/__init__.py

Read those in order to follow one run of comfy-headless end to end. This path follows comfy-headless (a command people run) from its entry, since CI runs only tests and checks.

## What this map cannot see

- 2 imports could not be resolved: `comfy_headless/__init__.py` imports a path built at run time; `tests/run_fuzz.py` imports `comfy_headless.tests.test_fuzz`, which is no module on its import path and no declared dependency.
- 2 writes and 4 reads use paths built at run time and are not named here.
- 3 reads go to a temporary directory, not to this repository.
- Statistics confidence is low: fewer than 30 qualifying commits in the window, and fewer than 20 source files reach 10 revisions.

Regenerate with `npx --yes @dogfood-lab/atlas map`.
