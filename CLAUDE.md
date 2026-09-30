# taboo-data

Remote game data repository for the Taboo iOS app (`LetsTaboo/taboo-data`).

## Files

| File | Description |
|------|-------------|
| `game_data.json` | All topics, difficulty levels, and word cards |
| `version.json` | Current data version number `{"version": N}` |

## 🔴 This repo may only serve decks the apps already ship (deck-parity, required check)

iOS reads `version.json` from this repo's `main` and downloads `game_data_<locale>.json` for any locale
whose version is newer. So anything served here reaches iPhones. The `deck-parity` GitHub Action
(`.github/scripts/check_decks.py`) runs on every push and PR to `main`, and `main` is protected: the check
is required, direct pushes are refused, and that includes admins. It fails when:
- any `*.json` other than `version.json` is not in `app_decks.md5` or differs from it by md5;
- `version.json` advertises a locale with no verified deck, or a version different from that deck's own
  `version` field, or a top-level `version` different from the English deck's.

**`app_decks.md5` is the source of truth**, and it has ONE update path: Server regenerates it from the iOS
release branch that ships the decks, and commits it in the same PR as the deck change here:

```bash
tools/regen_app_decks_md5.sh <path-to-forbidden-ios> origin/release/<version>
```

Do not edit it by hand. Android's bundled decks are kept byte-identical to iOS by the apps' own md5 parity
test. `game_data.json` is the legacy (v2.0.0) alias of the English deck.

**To publish a deck update:** ship it in the app bundle first (iOS `Taboo/Resources/Data/`, plus Android),
regenerate `app_decks.md5` from that release branch, then open a PR here with the deck(s), the new
`app_decks.md5` and the bumped `version.json`. The check must be green before the merge.

## Data Structure

```json
{
  "version": 4,
  "data": [
    {
      "topic": "general",
      "displayName": "General",
      "icon": "books.vertical",
      "levels": [
        {
          "type": "basic",
          "words": [
            { "word": "Example", "forbiddens": ["w1", "w2", "w3", "w4", "w5"] }
          ]
        }
      ]
    }
  ]
}
```

- `topic`: unique snake_case id
- `icon`: SF Symbol name
- `type`: `basic` | `medium` | `hard`
- `forbiddens`: always exactly 5 words

## Current Topics (7)

`general`, `technology`, `sports`, `movies_tv`, `food_drink`, `science`, `history`

A synthetic **Random** topic is created at runtime by the iOS app — do not add it here.

## Versioning

- Increment `version` in both `game_data.json` (root field) and `version.json` when publishing a data update
- The iOS app compares remote `version.json` against the bundled version on launch and prompts users to download if newer
