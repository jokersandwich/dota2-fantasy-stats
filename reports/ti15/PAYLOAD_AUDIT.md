# TI14 OpenDota Payload Audit

- 状态：**PASSED**
- Dataset：`ti15`
- Match source：`ti15-2026-opendota`
- Ruleset：`ti15-base-v1`

## 范围与完整性

| 检查 | 结果 |
|---|---:|
| Frozen manifest matches | 59 |
| Cached payload matches | 59 |
| Player-match rows | 590 |
| Unique account IDs | 80 |
| Teams | 16 |
| Series | 24 |
| Parsed matches | 59 |
| Duration range (seconds) | 1293–5678 |

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
- Smokes：253 rows / total 904。
- Madstone candidate（不计分）：534 rows / total 6773。
- Tormentor candidate：90 rows / total 108。
- Roshan attribution cross-check：players 158 / objectives 158。

## 已隔离异常

- First Blood attribution 缺失：1 matches；policy IDs = `[8943142948]`。
- Teamfight participation 越界：0 rows。
- Negative stun duration：1 rows。
- 上述异常均作为 unavailable 隔离，不归零、不 clamp、不修改 Fantasy constants。

## 错误

无。
