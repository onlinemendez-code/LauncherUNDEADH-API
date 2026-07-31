# AGENTS.md

## Cursor Cloud specific instructions

This repo is an **asset-generation toolkit** for the UNDEAD Heaven (DayZ) project: Python + [Pillow](https://python-pillow.org/) scripts in `scripts/` that procedurally render PNG assets (Discord forum covers, minimap/compass frames, dialog-UI mockups, a beauty guide). It also holds static data (`api.json` news feed, `launcherupdate.json`) and one GitHub workflow (`.github/workflows/map-live-sync.yml`) that only runs on `repository_dispatch`.

### Dependencies / environment
- Only external dependency is **Pillow**; everything else is Python stdlib. Python 3.12 is preinstalled. The startup update script installs Pillow (into the user site via `pip --break-system-packages`), so you normally don't need to install anything.
- There is **no lint or automated-test framework** configured. "Testing" a change means running the relevant generator and inspecting the emitted PNG(s).

### Running the generators
- Run scripts from the repo root, e.g. `python3 scripts/generate_compass_rim.py`. Each script has **hardcoded absolute output paths under `/workspace/...`**, so it must run from a checkout located at `/workspace`.
- `generate_minimap_frames_diverse.py`, `generate_minimap_frames_radical.py`, and `generate_minimap_frames_games.py` `import generate_minimap_frames`, so run them with `scripts/` on the path — e.g. `cd scripts && python3 generate_minimap_frames_diverse.py` (or set `PYTHONPATH=scripts`). The minimap batch is slow (renders many 4K PNGs; the full set takes a couple of minutes).

### Gotchas
- Scripts write directly into the tracked asset directories (`compass-rim/`, `dialog-styles/`, `minimap-frames/`, `beauty-guide/`), overwriting files in place. Most individual PNGs regenerate byte-identical, but the `.zip` bundles and contact sheets differ every run (archive timestamps / unseeded `random`). If you only meant to change setup or a script, run `git checkout -- .` afterward to drop unintended asset churn.
- `generate_beauty_guide.py` is the **only** script that needs external inputs: source PNGs in `/opt/cursor/artifacts/assets/` (not committed). Without them it fails with `FileNotFoundError`. All other scripts are fully self-contained.
- Fonts come from `/usr/share/fonts/truetype/dejavu/` (present in the base image); scripts fall back to Pillow's default font if a face is missing.
