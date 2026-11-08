#!/usr/bin/env python3
"""deck-parity: this repo may only serve decks that are byte-identical to what the apps ship.

iOS (GameUpdateService) reads version.json from raw.githubusercontent.com/LetsTaboo/taboo-data/main and
downloads game_data_<locale>.json for any locale whose advertised version is newer. So:
  1. every *.json in the repo (except version.json) must be listed in app_decks.md5 with the SAME md5;
     an unlisted .json fails (an uploaded ar/es/hu/pt/vi deck must never slip through as "new");
  2. every locale version.json advertises must have a served, verified deck, and the versions must agree
     with that deck's own "version" field;
  3. version.json's top-level "version" (the legacy-manifest fallback) must equal the English deck's.
  4. the ROOT path is what apps up to 2.13.0 read (and Android before Geography): a root deck may only carry the
     six older topics. Apps that ship Geography read `topics7/` (contract topic_rotation.md section 8); rules 1-3
     hold there with its own version.json, and its decks may carry the seventh topic.
Exit 0 = all held, 1 = a violation. It prints what it checked, so a zero-file run cannot read as a pass.
"""
import hashlib, json, pathlib, sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
listed = {}
for line in (root / "app_decks.md5").read_text().splitlines():
    if line.strip() and not line.startswith("#"):
        md5, name = line.split(None, 1)
        listed[name.strip()] = md5

# The six topics every app knows; the root path serves only these (contract topic_rotation.md section 8).
OLD_TOPICS = {"cultural", "sports", "movies_tv", "food_drink", "science", "history"}
# Each served path: its folder prefix. "" = the root (older apps), "topics7/" = the apps that ship Geography.
PATHS = ["", "topics7/"]

errors, checked = [], []
served = sorted(p for p in root.rglob("*.json") if ".git" not in p.parts and ".github" not in p.parts)
for p in served:
    rel = p.relative_to(root).as_posix()
    if rel in {f"{pre}version.json" for pre in PATHS}:
        continue
    if "/" in rel and not any(pre and rel.startswith(pre) and "/" not in rel[len(pre):] for pre in PATHS):
        errors.append(f"{rel}: in no served path ({', '.join(pre or 'root' for pre in PATHS)})")
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

# Rule 4: a root deck with a topic outside the six would reach older apps.
root_topics_checked = 0
for rel in checked:
    if "/" in rel:
        continue
    try:
        topics = {t.get("topic") for t in json.loads((root / rel).read_text()).get("data", [])}
    except Exception as e:
        errors.append(f"{rel}: unreadable ({e})"); continue
    root_topics_checked += 1
    extra = sorted(t for t in topics if t not in OLD_TOPICS)
    if extra:
        errors.append(f"{rel}: root deck carries {extra}: apps up to 2.13.0 read the root; such a deck goes in topics7/")

for pre in PATHS:
    vpath = root / f"{pre}version.json"
    if not vpath.exists():
        if not pre:
            errors.append("version.json missing")
        elif any(c.startswith(pre) for c in checked):
            errors.append(f"{pre}version.json missing beside its decks")
        continue
    try:
        manifest = json.loads(vpath.read_text())
    except Exception as e:
        errors.append(f"{pre}version.json: invalid JSON ({e})"); continue
    for loc, meta in sorted((manifest.get("locales") or {}).items()):
        deck = f"{pre}game_data_{loc}.json"
        if deck not in checked:
            errors.append(f"{pre}version.json advertises '{loc}' but {deck} is not a served, verified deck")
        elif deck_version(deck) != (meta or {}).get("version"):
            errors.append(f"{pre}version.json '{loc}' = {(meta or {}).get('version')} but {deck} says {deck_version(deck)}")
    en = f"{pre}game_data_en.json"
    if en in checked and manifest.get("version") != deck_version(en):
        errors.append(f"{pre}version.json top-level version {manifest.get('version')} != {en} {deck_version(en)}")

print(f"deck-parity: {len(served)} json file(s) served, {len(checked)} verified against {len(listed)} app decks; "
      f"{root_topics_checked} root deck(s) checked for the six topics")
for c in checked:
    print(f"  ok   {c}")
for e in errors:
    print(f"  FAIL {e}")
if not checked:
    errors.append("nothing verified — refusing to pass an empty check")
    print("  FAIL nothing verified — refusing to pass an empty check")
sys.exit(1 if errors else 0)
