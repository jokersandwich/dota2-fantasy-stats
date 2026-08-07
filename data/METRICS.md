# EWC 2026 指标字段审计

审计对象为 OpenDota `GET /api/matches/{match_id}` 的实际 EWC 2026 JSON。
“需要 parsed replay”表示只有当 `od_data.has_parsed === true` 时才使用该指标；
缺少解析数据或必需字段时，处理器输出 `unavailable` 和 `null`，不会补 0。

| 指标 | 数据来源字段 | 计算公式 | 可靠 | 需要 parsed replay |
|---|---|---|---|---|
| games played | `players[].account_id`、顶层 `match_id` | 指定 `account_id` 出现的不同比赛数 | 是 | 否 |
| kills | `players[].kills` | 直接取值；跨比赛求和/分位数 | 是 | 否 |
| deaths | `players[].deaths` | 直接取值；跨比赛求和/分位数 | 是 | 否 |
| assists | `players[].assists` | 直接取值；跨比赛求和/分位数 | 是 | 否 |
| creep score | `players[].last_hits`、`players[].denies` | 本项目定义为 `last_hits + denies` | 是 | 否 |
| GPM | `players[].gold_per_min` | 直接取值 | 是 | 否 |
| runes | `players[].rune_pickups` | 直接取值 | 是 | 是 |
| teamfight participation | `players[].teamfight_participation` | 直接取 OpenDota 值 | 是 | 是 |
| wards | `players[].obs_placed`、`players[].sen_placed` | `obs_placed + sen_placed` | 是 | 是 |
| camps stacked | `players[].camps_stacked` | 直接取值 | 是 | 是 |
| smokes | `players[].item_uses.smoke_of_deceit` | key 存在时取次数；`item_uses` 存在但 key 不存在时为真实 0 | 是 | 是 |
| Roshan kills | `players[].roshan_kills` | 直接取值，含义是玩家对 Roshan 的最后一击数 | 是 | 是 |
| Tormentor kills | 仅观察到 `players[].killed.npc_dota_miniboss` 内部实体计数 | 不计算；输出 `unavailable` | 否 | 是 |
| courier kills | `players[].courier_kills` | 直接取值 | 是 | 是 |
| stuns | `players[].stuns` | 直接取值，单位为秒 | 是 | 是 |
| first blood | `players[].firstblood_claimed` | 直接取 0/1；可用 `objectives[]` 的 `CHAT_MESSAGE_FIRSTBLOOD.player_slot` 交叉核对 | 是 | 是 |
| buybacks | `players[].buyback_count` | 直接取值；可用 `len(players[].buyback_log)` 交叉核对 | 是 | 是 |

## 不能采用的替代算法

- Runes 不能改为汇总 `players[].runes`。实际样本中它与 `rune_pickups` 并不总是相等。
- Teamfight participation 不能改为 `(kills + assists) / radiant_score|dire_score`。
  抽查的 60 个 player-match 中有 5 个与该简式不一致。
- Smokes 明确定义为“使用次数”。`purchase.smoke_of_deceit` 是购买次数，实际样本中购买与使用并不总是相等。
- Roshan kills 不能用 `killed.npc_dota_roshan` 重建。抽查中该内部映射与官方
  `roshan_kills` 字段有差异。
- Tormentor 没有 `tormentor_kills` 顶层字段。虽然当前 payload 的 `killed` 中可看到
  `npc_dota_miniboss`，但 Roshan 的对照已经证明 `killed` 内部映射不适合作为官方
  last-hit 聚合字段的通用替代，因此按不可靠处理。

## 跨比赛统计

对每名 roster 选手，每个可用指标先形成“每场比赛一个观测值”的序列：

- `total = sum(values)`
- `average_per_game = total / games_played`
- `P50`、`P75`、`P90` 使用排序后相邻值线性插值

只有该指标在该选手的所有已处理比赛中都可用时才输出统计值。GPM 和
teamfight participation 的 `total` 仅为了保持统一 JSON 结构；实际展示应优先使用
average 和分位数。
