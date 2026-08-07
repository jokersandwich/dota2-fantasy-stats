# TI15 Fantasy / OpenDota 字段映射调查

本文件只调查 Fantasy 原始统计量与 OpenDota EWC 2026 缓存 JSON 的映射关系，**不计算 Fantasy 积分、总分或排行榜**。

## 调查范围

- 数据源：`data/raw/matches/*.json`
- OpenDota league ID：`19785`
- 已缓存比赛：157 场
- 玩家比赛记录：1,570 条
- `od_data.has_parsed === true`：157/157 场
- 调查日期：2026-08-07

文中的 JSON 示例均取自缓存文件，只保留与该指标有关的真实字段和值，未展示的无关字段没有用 `0` 补齐。

### 固定随机抽查的 10 场比赛

抽样种子为 `20260807`：

| match_id | Radiant | Dire | parsed replay |
|---:|---|---|---|
| 8885411801 | Aurora Gaming | Level UP esports | yes |
| 8885665054 | Team Nemesis | PVISION | yes |
| 8889468264 | BoomBoys | Xtreme Gaming | yes |
| 8889693867 | Level UP esports | Nigma Galaxy | yes |
| 8889871314 | Team Nemesis | Vici Gaming | yes |
| 8890206902 | Inner Circle x Insanity | Virtus.pro | yes |
| 8892836635 | PVISION | Team Spirit | yes |
| 8893070561 | 1w Team | Team Yandex | yes |
| 8896139222 | Rune Eaters | Virtus.pro | yes |
| 8896140998 | Xtreme Gaming | Team Liquid | yes |

除这 10 场逐项抽查外，字段存在性和关键交叉校验覆盖了全部 157 场。

## 结论摘要

| Fantasy 项目 | 采用字段/结论 | 可直接计算 | parsed replay | 可靠度 |
|---|---|---|---|---|
| 击杀 | `players[].kills` | 是 | 否 | high |
| 死亡 | `players[].deaths` | 是 | 否 | high |
| 正反补 | `last_hits + denies` | 需简单推导 | 否 | high |
| GPM | `players[].gold_per_min` | 是 | 否 | high |
| 疯狂石 | `item_uses.madstone_bundle` 仅是候选代理 | 否，语义待确认 | 是 | low |
| 摧毁防御塔 | `players[].tower_kills` | 是 | 是 | high |
| 放置侦察守卫 | `players[].obs_placed` | 是 | 是 | high |
| 堆叠野怪 | `players[].camps_stacked` | 是 | 是 | high |
| 拾取神符 | `players[].rune_pickups` | 是 | 是 | high |
| 占领观察者 | 无对应数据 | 否 | N/A | unavailable |
| 采集莲花 | 无对应数据；`lotus_orb` 不是莲花池采集 | 否 | N/A | unavailable |
| 击杀 Roshan | `players[].roshans_killed` | 是 | 是 | high |
| 参与团战 | `players[].teamfight_participation` | 是 | 是 | high |
| 眩晕时间 | `players[].stuns` | 有条件 | 是 | medium |
| 击杀 Tormentor | `players[].killed.npc_dota_miniboss` | 需推导且归属有风险 | 是 | medium |
| 击杀信使 | `players[].courier_kills` | 是 | 是 | high |
| 第一滴血 | `players[].firstblood_claimed` | 是 | 是 | high |
| 开雾次数 | `players[].item_uses.smoke_of_deceit` | 需从 map 读取 | 是 | high |

## 逐项字段调查

### 1. 击杀

1. **Fantasy 项目名称**：击杀
2. **OpenDota 字段**：`players[].kills`
3. **实际 JSON 示例**：match `8885411801`、Nightfall（account_id `124801257`）：

   ```json
   {"account_id": 124801257, "kills": 6}
   ```

4. **数据单位**：英雄击杀次数
5. **是否需要 parsed replay**：否
6. **是否能直接计算**：是
7. **推导公式**：无；每场直接取 `kills`
8. **数据可靠程度**：`high`
9. **说明**：字段存在于全部 1,570 条玩家比赛记录。

### 2. 死亡

1. **Fantasy 项目名称**：死亡
2. **OpenDota 字段**：`players[].deaths`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "deaths": 2}
   ```

4. **数据单位**：死亡次数
5. **是否需要 parsed replay**：否
6. **是否能直接计算**：是
7. **推导公式**：无；死亡基础分 `1950` 和扣分规则本轮不计算
8. **数据可靠程度**：`high`
9. **说明**：字段存在于全部 1,570 条玩家比赛记录。

### 3. 正反补

1. **Fantasy 项目名称**：正补与反补
2. **OpenDota 字段**：`players[].last_hits`、`players[].denies`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "last_hits": 398, "denies": 13}
   ```

4. **数据单位**：单位个数
5. **是否需要 parsed replay**：否
6. **是否能直接计算**：需要简单推导
7. **推导公式**：`creep_count = last_hits + denies`；示例为 `398 + 13 = 411`
8. **数据可靠程度**：`high`
9. **说明**：两个字段均存在于全部 1,570 条玩家比赛记录。

### 4. GPM

1. **Fantasy 项目名称**：每分钟金钱
2. **OpenDota 字段**：`players[].gold_per_min`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "gold_per_min": 709}
   ```

4. **数据单位**：gold/minute
5. **是否需要 parsed replay**：否
6. **是否能直接计算**：是
7. **推导公式**：无；直接取该场 `gold_per_min`
8. **数据可靠程度**：`high`
9. **说明**：字段存在于全部 1,570 条玩家比赛记录。

### 5. 疯狂收集数量 / Madstones

1. **Fantasy 项目名称**：收集疯狂石
2. **OpenDota 字段**：没有名为 `madstones_collected` 的专用字段；缓存中实际存在的唯一候选是 `players[].item_uses.madstone_bundle`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {
     "account_id": 124801257,
     "item_uses": {"madstone_bundle": 19}
   }
   ```

4. **数据单位**：OpenDota 记录的 `madstone_bundle` 使用事件次数；JSON 本身没有证明其单位等于“单颗疯狂石”
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：**不能直接作为已确认的疯狂石收集数量**
7. **推导公式**：若后续确认一次 `madstone_bundle` use 就等于一次计分收集，候选公式才是 `item_uses.get("madstone_bundle", 0)`；本轮不采用该假设
8. **数据可靠程度**：`low`
9. **说明**：该 key 出现在 1,412/1,570 条玩家记录中，累计值为 16,183；全部玩家记录都有 `item_uses` map，因此缺 key 可以解释为没有对应 use 事件，但“use”和“collected”的语义等价仍未由 payload 证明。

### 6. 摧毁防御塔

1. **Fantasy 项目名称**：摧毁防御塔
2. **OpenDota 字段**：`players[].tower_kills`；缓存里的 `players[].towers_killed` 与它逐条完全相同
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "tower_kills": 3, "towers_killed": 3}
   ```

4. **数据单位**：由该玩家取得最后一击的防御塔数量
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；使用 `tower_kills`
8. **数据可靠程度**：`high`
9. **说明**：全量数据中玩家字段合计 1,664，与 `objectives[].type == "building_kill"` 且能归属到有效玩家的塔事件逐玩家完全一致。另有 338 座塔没有玩家归属，不能擅自计给某名选手。

### 7. 放置侦察守卫

1. **Fantasy 项目名称**：放置侦察守卫
2. **OpenDota 字段**：`players[].obs_placed`
3. **实际 JSON 示例**：match `8885411801`、Mikoto（account_id `301750126`）：

   ```json
   {"account_id": 301750126, "obs_placed": 2}
   ```

4. **数据单位**：侦察守卫放置次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `obs_placed`。不要加上 `sen_placed`，后者是岗哨守卫
8. **数据可靠程度**：`high`
9. **说明**：示例玩家的 `obs_log` 也有 2 条实际放置日志；`obs_placed` 存在于全部 1,570 条玩家记录。

### 8. 堆叠野怪

1. **Fantasy 项目名称**：堆叠野怪
2. **OpenDota 字段**：`players[].camps_stacked`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "camps_stacked": 3}
   ```

4. **数据单位**：成功堆叠的野区营地次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `camps_stacked`
8. **数据可靠程度**：`high`
9. **说明**：不要使用 `creeps_stacked`；它表示被堆出的单位数量，不等于 Fantasy 所需的堆野次数。

### 9. 拾取/激活神符

1. **Fantasy 项目名称**：拾取/激活神符
2. **OpenDota 字段**：`players[].rune_pickups`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "rune_pickups": 7}
   ```

4. **数据单位**：神符拾取次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `rune_pickups`
8. **数据可靠程度**：`high`
9. **说明**：不要用 `len(runes_log)` 或累加 `players[].runes`。全量 1,570 条记录中，`rune_pickups` 与 `len(runes_log)` 有 971 条不相等，说明日志数组不能替代聚合字段。

### 10. 占领观察者 / Watchers

1. **Fantasy 项目名称**：占领观察者
2. **OpenDota 字段**：无
3. **实际 JSON 示例**：在 157 场完整 JSON 中搜索 `watcher` / `watchers`，匹配场数为 `0`；抽样 match `8885411801` 的 `players`、`objectives` 及其他嵌套结构中也没有对应 key 或事件类型
4. **数据单位**：不可用
5. **是否需要 parsed replay**：N/A（当前 parsed payload 仍无字段）
6. **是否能直接计算**：否
7. **推导公式**：无；不能从位置、守卫或建筑事件猜测
8. **数据可靠程度**：`unavailable`
9. **说明**：后续输出必须使用 `unavailable`/`null`，不能填 `0`。

### 11. 采集莲花

1. **Fantasy 项目名称**：从莲花池采集莲花
2. **OpenDota 字段**：无对应采集字段
3. **实际 JSON 示例**：缓存中出现的 `lotus` 只是装备 Lotus Orb，例如 match `8885183102`：

   ```json
   {"item_uses": {"lotus_orb": 7}}
   ```

4. **数据单位**：不可用
5. **是否需要 parsed replay**：N/A（当前 parsed payload 仍无采集字段）
6. **是否能直接计算**：否
7. **推导公式**：无；`lotus_orb` 是装备使用次数，与莲花池采集无关
8. **数据可靠程度**：`unavailable`
9. **说明**：虽然 77 场 JSON 含字符串 `lotus`，但递归检查后全部属于 `lotus_orb` 的购买、使用、伤害或物品统计，不得当作采集莲花。

### 12. 击杀 Roshan

1. **Fantasy 项目名称**：击杀肉山
2. **OpenDota 字段**：**`players[].roshans_killed`**；也可用 `players[].killed.npc_dota_roshan` 交叉检查
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {
     "account_id": 124801257,
     "roshans_killed": 1,
     "killed": {"npc_dota_roshan": 1}
   }
   ```

4. **数据单位**：玩家对 Roshan 的最后一击次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `roshans_killed`
8. **数据可靠程度**：`high`
9. **说明**：157 场有 351 条 `CHAT_MESSAGE_ROSHAN_KILL`，`roshans_killed` 合计也是 351，并且与 `killed.npc_dota_roshan` 逐玩家零差异。**不要使用 `players[].roshan_kills`**：它在本缓存合计为 451，有 87 条玩家记录与 `roshans_killed` 不同，无法代表本 Fantasy 项目的 Roshan 最后一击。

### 13. 参与团战

1. **Fantasy 项目名称**：团战参与率
2. **OpenDota 字段**：`players[].teamfight_participation`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "teamfight_participation": 0.56666666}
   ```

4. **数据单位**：`0` 到 `1` 的比例值，不是 `0` 到 `100` 的百分数；示例展示为百分比时才是约 `56.67%`
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是，使用 OpenDota 已给出的比例
7. **推导公式**：不自行推导；尤其不能用 `(kills + assists) / 最终团队击杀数` 代替
8. **数据可靠程度**：`high`
9. **说明**：全量实际范围为 `[0, 1]`。简单公式与 OpenDota 字段在 1,570 条记录中有 204 条不一致。`最多 2124 分` 如何映射到该比例属于最终计分算法，本轮不实现。

### 14. 眩晕时间

1. **Fantasy 项目名称**：造成眩晕的持续时间
2. **OpenDota 字段**：`players[].stuns`
3. **实际 JSON 示例**：match `8885411801`、Nightfall：

   ```json
   {"account_id": 124801257, "stuns": 2.1666503}
   ```

4. **数据单位**：秒
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：有条件；正常的非负值可直接读取，但需要先决定异常值处理政策
7. **推导公式**：无；不要自行取整。当前不对异常值做 `max(0, value)`，因为这会未经确认地篡改原始数据
8. **数据可靠程度**：`medium`
9. **说明**：字段存在于全部玩家记录，实际范围 `-0.5835204` 到 `345.60147` 秒。唯一负值出现在 match `8885614030` 的 shiro（account_id `320252024`），因此最终计分前必须明确该异常如何处理，不能直接当作 0。

### 15. 击杀 Tormentor

1. **Fantasy 项目名称**：消灭痛苦魔方 / Tormentor
2. **OpenDota 字段**：没有专用 `tormentor_kills`；实际候选为 `players[].killed.npc_dota_miniboss`
3. **实际 JSON 示例**：match `8885411801`、WoE（account_id `1092267175`）：

   ```json
   {
     "account_id": 1092267175,
     "player_slot": 130,
     "killed": {"npc_dota_miniboss": 1}
   }
   ```

   同场目标事件为：

   ```json
   {
     "time": 1230,
     "type": "CHAT_MESSAGE_MINIBOSS_KILL",
     "team": 3,
     "slot": 6,
     "player_slot": 129
   }
   ```

4. **数据单位**：`npc_dota_miniboss` 击杀事件次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：只能有条件推导，不能视为专用高可靠字段
7. **推导公式**：候选为 `player.get("killed", {}).get("npc_dota_miniboss", 0)`
8. **数据可靠程度**：`medium`
9. **说明**：全量有 272 条 `CHAT_MESSAGE_MINIBOSS_KILL`，`killed.npc_dota_miniboss` 的合计也为 272，说明比赛总数吻合；但目标事件的 `player_slot` 与 `killed` map 的玩家归属大量不一致，且 13 条目标事件没有有效 `player_slot`。因此比赛级总数可信，玩家级计分归属只能标记为 medium，不能提升为 high。

### 16. 击杀信使

1. **Fantasy 项目名称**：杀害信使
2. **OpenDota 字段**：`players[].courier_kills`
3. **实际 JSON 示例**：match `8885411801`、Ws（原始昵称末尾含一个反引号，account_id `126842529`）：

   ```json
   {"account_id": 126842529, "courier_kills": 1}
   ```

4. **数据单位**：信使击杀次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `courier_kills`
8. **数据可靠程度**：`high`
9. **说明**：全量字段合计 490，与 `CHAT_MESSAGE_COURIER_LOST.killer` 能归属到有效玩家的 490 条事件逐玩家完全一致。另有 68 条事件的 `killer == -1`，没有被错误计给任何选手。

### 17. 第一滴血

1. **Fantasy 项目名称**：获得第一滴血
2. **OpenDota 字段**：`players[].firstblood_claimed`
3. **实际 JSON 示例**：match `8885411801`、queezy（account_id `206097366`）：

   ```json
   {"account_id": 206097366, "player_slot": 131, "firstblood_claimed": 1}
   ```

   同场事件：

   ```json
   {
     "time": 88,
     "type": "CHAT_MESSAGE_FIRSTBLOOD",
     "key": "4",
     "slot": 8,
     "player_slot": 131
   }
   ```

4. **数据单位**：二元计数，每场每名玩家为 `0` 或 `1`
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：是
7. **推导公式**：无；直接取 `firstblood_claimed`
8. **数据可靠程度**：`high`
9. **说明**：全量共有 154 个值为 `1`，与 154 条 `CHAT_MESSAGE_FIRSTBLOOD` 的玩家归属逐条完全一致。

### 18. 开雾次数

1. **Fantasy 项目名称**：使用诡计之雾
2. **OpenDota 字段**：`players[].item_uses.smoke_of_deceit`
3. **实际 JSON 示例**：match `8885411801`、Mira（account_id `256156323`）：

   ```json
   {
     "account_id": 256156323,
     "item_uses": {"smoke_of_deceit": 2}
   }
   ```

4. **数据单位**：物品使用次数
5. **是否需要 parsed replay**：是
6. **是否能直接计算**：需要从 `item_uses` map 读取；在 replay 已解析且 `item_uses` 存在时，缺少该 key 表示该场没有 smoke use 事件
7. **推导公式**：`item_uses.get("smoke_of_deceit", 0)`
8. **数据可靠程度**：`high`
9. **说明**：不要使用 `purchase.smoke_of_deceit` 或购买日志；购买次数不等于实际开雾次数。`item_uses` 存在于全部 1,570 条玩家记录，smoke key 出现在其中 671 条。

## 影响后续实现的待确认事项

本轮到此停止，不修改 `process-data.py` 或前端。正式实现计分前需要先确认：

1. 是否接受 `item_uses.madstone_bundle` 作为疯狂石收集的计分代理；当前只能给 `low`。
2. Tormentor 是否接受 `killed.npc_dota_miniboss` 的玩家归属；比赛总数吻合，但事件归属冲突使其只能为 `medium`。
3. `stuns` 唯一负值应该标记该场不可用、保留原值，还是采用其他明确规则；本文件没有擅自归零。
4. 后续 Roshan 处理必须从 `roshan_kills` 改为 `roshans_killed`，但本轮按要求没有修改处理脚本。
5. Watcher 和莲花保持 `unavailable`，不得以 `0` 代替。
