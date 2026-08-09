# TI14 OpenDota Payload Audit

- 状态：**PASSED**
- Dataset：`ti14`
- Match source：`ti14-2025-opendota`
- Ruleset：`ti15-base-v1`

## 范围与完整性

| 检查 | 结果 |
|---|---:|
| Frozen manifest matches | 144 |
| Cached payload matches | 144 |
| Player-match rows | 1440 |
| Unique account IDs | 80 |
| Teams | 16 |
| Series | 58 |
| Parsed matches | 144 |
| Duration range (seconds) | 1352–4694 |

## Roster / account_id

- Final ranking roster：80 players / 16 teams。
- Structured roster changes：4。
- Missing account IDs：`[]`。
- Unexpected account IDs：`[]`。
- Per-player game-count mismatches：`[]`。

## Fantasy 字段兼容性

- `kills` / `deaths` / `last_hits + denies` / `gold_per_min`：available。
- `tower_kills` / `obs_placed` / `camps_stacked` / `rune_pickups` / `roshans_killed` / `teamfight_participation` / `stuns` / `courier_kills` / `firstblood_claimed` / smokes：parsed-only。
- Madstones / Watchers / Lotuses：unavailable，继续沿用 `ti15-base-v1` 的 null 语义。
- Tormentor：`killed.npc_dota_miniboss`，继续标记 medium reliability。
- Required source-field missing counts：`{}`。
- Smokes：628 rows / total 2043。
- Madstone candidate（不计分）：1267 rows / total 14318。
- Tormentor candidate：245 rows / total 299。
- Roshan attribution cross-check：players 342 / objectives 342。

## 已隔离异常

- First Blood attribution 缺失：3 matches；policy IDs = `[8446311496, 8457152687, 8457241577]`。
- Teamfight participation 越界：1 rows。
- Negative stun duration：12 rows。
- 上述异常均作为 unavailable 隔离，不归零、不 clamp、不修改 Fantasy constants。

## 错误

无。
