#!/usr/bin/env python3
"""deck-parity: this repo may only serve decks that are byte-identical to what the apps ship.

iOS (GameUpdateService) reads version.json from raw.githubusercontent.com/LetsTaboo/taboo-data/main and
downloads game_data_<locale>.json for any locale whose advertised version is newer. So:
  1. every *.json in the repo (except version.json) must be listed in app_decks.md5 with the SAME md5;
     an unlisted .json fails (an uploaded ar/es/hu/pt/vi deck must never slip through as "new");
  2. every locale version.json advertises must have a served, verified deck, and the versions must agree
     with that deck's own "version" field;
  3. version.json's top-level "version" (the legacy-manifest fallback) must equal the English deck's.
Exit 0 = all held, 1 = a violation. It prints what it checked, so a zero-file run cannot read as a pass.
"""
import hashlib, json, pathlib, sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
listed = {}
for line in (root / "app_decks.md5").read_text().splitlines():
    if line.strip() and not line.startswith("#"):
        md5, name = line.split(None, 1)
        listed[name.strip()] = md5

errors, checked = [], []
served = sorted(p for p in root.rglob("*.json") if ".git" not in p.parts and ".github" not in p.parts)
for p in served:
    rel = p.relative_to(root).as_posix()
    if rel == "version.json":
        continue
    got = hashlib.md5(p.read_bytes()).hexdigest()
    if rel not in listed:
        errors.append(f"{rel}: NOT an app-bundled deck (not in app_decks.md5) — the apps would download it")
    elif got != listed[rel]:
        errors.append(f"{rel}: md5 {got} != app-bundled {listed[rel]}")
    else:
        checked.append(rel)

def deck_version(name):
    try:
        return json.loads((root / name).read_text()).get("version")
    except Exception as e:
        errors.append(f"{name}: unreadable ({e})"); return None

vpath = root / "version.json"
if not vpath.exists():
    errors.append("version.json missing")
else:
    try:
        manifest = json.loads(vpath.read_text())
    except Exception as e:
        manifest = None; errors.append(f"version.json: invalid JSON ({e})")
    if manifest is not None:
        for loc, meta in sorted((manifest.get("locales") or {}).items()):
            deck = f"game_data_{loc}.json"
            if deck not in checked:
                errors.append(f"version.json advertises '{loc}' but {deck} is not a served, verified deck")
            elif deck_version(deck) != (meta or {}).get("version"):
                errors.append(f"version.json '{loc}' = {(meta or {}).get('version')} but {deck} says {deck_version(deck)}")
        if "game_data_en.json" in checked and manifest.get("version") != deck_version("game_data_en.json"):
            errors.append(f"version.json top-level version {manifest.get('version')} != game_data_en.json {deck_version('game_data_en.json')}")

print(f"deck-parity: {len(served)} json file(s) served, {len(checked)} verified against {len(listed)} app decks")
for c in checked:
    print(f"  ok   {c}")
for e in errors:
    print(f"  FAIL {e}")
if not checked:
    errors.append("nothing verified — refusing to pass an empty check")
    print("  FAIL nothing verified — refusing to pass an empty check")
sys.exit(1 if errors else 0)
