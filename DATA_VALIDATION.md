# TI15 Fantasy 数据验证

本报告由 `python -m scripts.fantasy.scoring` 对完整 EWC 2026 OpenDota 缓存生成。

## 处理范围

- 发现比赛：157
- 成功处理比赛：157
- 玩家比赛记录：1570
- 每场不是 10 名玩家的比赛：0
- 仅计算基础积分；未加入战旗品质、战旗特性或指导员称号加成

## 自动检查结果

| 检查 | 结果 |
|---|---:|
| NaN / Infinity / 非数值的 available 字段 | 0 |
| `undefined` | 0（JSON/Python 输出模型不存在 undefined） |
| 负 Fantasy 分数 | 0 |
| unavailable 项目却含非 null 值 | 0 |
| 隔离的原始负数异常 | 1 |

JSON 写出使用 `allow_nan=False`，因此任何 NaN 或 Infinity 都会令处理失败，而不是进入前端文件。

## 各指标范围

| 指标 | available | unavailable | raw min | raw max | score min | score max |
|---|---:|---:|---:|---:|---:|---:|
| `kills` | 1570 | 0 | 0 | 33 | 0 | 3531 |
| `deaths` | 1570 | 0 | 0 | 17 | 0 | 1950 |
| `creep_score` | 1570 | 0 | 6 | 1357 | 18 | 4071 |
| `gpm` | 1570 | 0 | 139 | 1155 | 278 | 2310 |
| `madstones` | 0 | 1570 | — | — | — | — |
| `tower_kills` | 1570 | 0 | 0 | 10 | 0 | 3520 |
| `observer_wards` | 1570 | 0 | 0 | 30 | 0 | 3510 |
| `camps_stacked` | 1570 | 0 | 0 | 15 | 0 | 3510 |
| `rune_pickups` | 1570 | 0 | 0 | 25 | 0 | 3525 |
| `watchers` | 0 | 1570 | — | — | — | — |
| `lotuses` | 0 | 1570 | — | — | — | — |
| `roshan_kills` | 1570 | 0 | 0 | 3 | 0 | 3516 |
| `teamfight_participation` | 1570 | 0 | 0 | 1 | 0 | 2124 |
| `stun_duration` | 1569 | 1 | 0 | 345.60147 | 0 | 3456.0147 |
| `tormentor_kills` | 1570 | 0 | 0 | 3 | 0 | 2637 |
| `courier_kills` | 1570 | 0 | 0 | 5 | 0 | 3515 |
| `first_blood` | 1570 | 0 | 0 | 1 | 0 | 1934 |
| `smokes` | 1570 | 0 | 0 | 12 | 0 | 3516 |

## 发现的问题与处理

### 1. 眩晕时间负值

OpenDota 原始数据中有 1 条被隔离的非法原始值：match `8885614030`、shiro（account_id `320252024`）、`stun_duration` 原值 `-0.5835204`。计分引擎没有将其归零，也没有产生负分；该指标的 `rawValue` 和 `baseFantasyScore` 均输出为 `null`，`dataAvailability` 为 `unavailable`。

### 2. 永久 unavailable 项目

`madstones`、`watchers`、`lotuses` 在全部玩家比赛记录中均保持 `null`。Madstones 的 `item_uses.madstone_bundle` 仍只是低可靠候选，没有被当作已确认收集数。

### 3. Tormentor 玩家归属

`tormentor_kills` 按已确认的候选公式读取 `killed.npc_dota_miniboss`，可靠度为 medium。比赛级总量可以与目标事件核对，但玩家归属仍有已知冲突；输出规则目录保留了该可靠度说明。

### 4. Roshan 字段

计分引擎使用 `roshans_killed`，没有使用会多计的 `roshan_kills`。

### 5. 总分完整性

由于至少三个项目永久 unavailable，完整 `baseFantasyScore` 为 `null`，避免把缺失项目当作 0。`availableBaseFantasyScore` 仅表示可用指标的小计，不能解释为完整 Fantasy 总分。

## 结论

数据集可稳定生成，没有 NaN、Infinity、undefined 或负 Fantasy 分数。发现的唯一原始负数已被隔离为 unavailable。各指标最大值已列在上表供人工复核，未发现违反明确字段边界（例如团战参与率 0–1、第一滴血 0/1）的数量。

生成的数据文件：`public/data/fantasy-match-scores.json`
