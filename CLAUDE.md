# taboo-data

Remote game data repository for the Taboo iOS app (`LetsTaboo/taboo-data`).

## Files

| File | Description |
|------|-------------|
| `game_data.json` | All topics, difficulty levels, and word cards |
| `version.json` | Current data version number `{"version": N}` |

## IMPORTANT: game_data.json Must Always Stay in Sync

`game_data.json` exists in **two repos** that must always be identical and committed/pushed together:

| Repo | Path |
|------|------|
| `LetsTaboo/taboo-data` | `game_data.json` |
| `yasinkbas/Taboo-ios` | `Taboo/Resources/Data/game_data.json` |

**Whenever `game_data.json` is modified:**
1. Write the same content to both paths
2. Commit and push `taboo-data` (branch: main)
3. Commit and push `Taboo-ios` (branch: current release branch)

Never push one without the other.

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
