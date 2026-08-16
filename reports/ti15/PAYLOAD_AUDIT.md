# TI14 OpenDota Payload Audit

- 状态：**PASSED**
- Dataset：`ti15`
- Match source：`ti15-2026-opendota`
- Ruleset：`ti15-base-v1`

## 范围与完整性

| 检查 | 结果 |
|---|---:|
| Frozen manifest matches | 109 |
| Cached payload matches | 109 |
| Player-match rows | 1090 |
| Unique account IDs | 80 |
| Teams | 16 |
| Series | 44 |
| Parsed matches | 109 |
| Duration range (seconds) | 1102–5678 |

## Roster / account_id

- Final ranking roster：80 players / 16 teams。
- Structured roster changes：3。
- Missing account IDs：`[]`。
- Unexpected account IDs：`[]`。
- Per-player game-count mismatches：`[]`。

## Fantasy 字段兼容性

- `kills` / `deaths` / `last_hits + denies` / `gold_per_min`：available。
- `tower_kills` / `obs_placed` / `camps_stacked` / `rune_pickups` / `roshans_killed` / `teamfight_participation` / `stuns` / `courier_kills` / `firstblood_claimed` / smokes：parsed-only。
- Madstones / Watchers / Lotuses：unavailable，继续沿用 `ti15-base-v1` 的 null 语义。
- Tormentor：`killed.npc_dota_miniboss`，继续标记 medium reliability。
- Required source-field missing counts：`{}`。
- Smokes：468 rows / total 1584。
- Madstone candidate（不计分）：987 rows / total 11973。
- Tormentor candidate：161 rows / total 191。
- Roshan attribution cross-check：players 266 / objectives 266。

## 已隔离异常

- First Blood attribution 缺失：1 matches；policy IDs = `[8943142948]`。
- Teamfight participation 越界：0 rows。
- Negative stun duration：2 rows。
- 上述异常均作为 unavailable 隔离，不归零、不 clamp、不修改 Fantasy constants。

## 错误

无。
