# TI14 Data Source Plan

> 状态：已确认并完成数据层正式接入。  
> 核验与实施日期：2026-08-09。  
> 本文中的 TI14 指 The International 2025（第十四届 The International）。

## 1. 已确认的数据集定义

TI14 是独立 dataset，不经过 TI15 roster 过滤：

```text
datasetId       = ti14
rosterSourceId  = ti14-2025
matchSourceId   = ti14-2025-opendota
rulesetId       = ti15-base-v1
```

统一 Role aggregation：

- Core = Position 1 + Position 3；
- Mid = Position 2；
- Support = Position 4 + Position 5；
- 两人 Role 只按完全相同的 `matchId` 聚合；
- best / average、同场均值与 null propagation 全部沿用已验证逻辑；
- 不研究或使用 TI14 历史 Fantasy 规则；
- 不修改 TI15 Fantasy scoring constants。

## 2. Roster universe

基础排名 roster 采用最终实际代表 16 支队伍参加 OpenDota league `18324` 的 80 名选手。每队恰好 5 名实际出场选手，Position 1–5 各一人。

赛前被替换且未在 league `18324` 出场的选手不进入 Fantasy player rankings，而是保存在 `rosterChanges` / provenance metadata：

- Gaimin Gladiators 退出，由 Yakutou Brothers 整队替补；
- Tundra Esports：Whitemon → Tobi；
- Xtreme Gaming：poloson → xNova；
- Nigma Galaxy：Miracle- → Ghost（最终 active Position 1）。

正式 roster source：`data/rosters/ti14-2025.json`。

### 2.1 最终队伍、选手、Position 与 account_id

| Team | P1 | P2 | P3 | P4 | P5 | 每人局数 |
|---|---|---|---|---|---|---:|
| Team Liquid | miCKe `152962063` | Nisha `201358612` | SaberLight `126212866` | Boxi `77490514` | Insania `54580962` | 16 |
| PVISION | Satanic `1044002267` | No[o]ne- `106573901` | DM `56351509` | 9Class `164199202` | Dukalis `73401082` | 23 |
| BB Team | Pure `331855530` | gpk~ `480412663` | MieRo `165564598` | Save- `317880638` | Kataomi `196878136` | 23 |
| Team Tidebound | shiro `320252024` | NothingToSay `173978074` | Bach `118134220` | planet `150961567` | y` `111114687` | 16 |
| Team Spirit | Yatoro `321580662` | Larl `106305042` | Collapse `302214028` | rue `847565596` | Miposhka `113331514` | 14 |
| Team Falcons | skiter `100058342` | Malr1ne `898455820` | ATF `183719386` | Cr1t- `25907144` | Sneyking `10366616` | 29 |
| Tundra Esports | Crystallis `127617979` | bzm `93618577` | 33 `86698277` | Saksa `103735745` | Tobi `140288368` | 21 |
| Yakutou Brothers | flyfly `168028715` | Emo `202217968` | Beyond `139031324` | BoBoKa `207829314` | Oli `101259972` | 16 |
| Natus Vincere | gotthejuice `957204049` | Niku `185590374` | pma `835864135` | Zayac `111030315` | Riddys `130991304` | 13 |
| Nigma Galaxy | Ghost `206642367` | SumaiL `111620041` | No!ob `140297552` | OmaR `152168157` | GH `101356886` | 24 |
| Aurora Gaming | Nightfall `124801257` | kiyotaka `858106446` | TORONTOTOKYO `431770905` | Mira `256156323` | panto `108958769` | 13 |
| Xtreme Gaming | Ame `898754153` | Xm `137129583` | Xxs `129958758` | XinQ `157475523` | xNova `94296097` | 26 |
| Team Nemesis | Akashi `330534326` | Mac `104512126` | Raven `132309493` | Jing `219755398` | Erice `100598959` | 10 |
| BOOM Esports | JaCkky `392565237` | Armel `164532005` | Jabz `100471531` | TIMS `155494381` | Jaunuel `148526973` | 12 |
| Wildcard | Yamsun `81475303` | RCY `154974246` | Fayde `160119017` | Bignum `90423751` | Speeed `191362875` | 13 |
| HEROIC | Yuma `177203952` | 4nalog `131303632` | Wisper `292921272` | Scofield `157989498` | KJ `81306398` | 19 |

核验结果：

- numeric account_id：80/80；
- null / anonymous account_id：0；
- roster 缺失 account_id：0；
- payload 非 roster account_id：0；
- 跨队重复 account_id：0；
- 每名选手的实际局数与 roster metadata 完全相等；
- 比赛期间没有第六名实际出场选手或换人。

## 3. OpenDota match source

正式 match source：

```text
provider: OpenDota
leagueIds: [18324]
stages: all
excludedMatchIds: []
cacheNamespace: ti14-2025-opendota
```

数据范围：

| 检查 | 结果 |
|---|---:|
| League ID | `18324` |
| League index rows | 144 |
| Frozen manifest IDs | 144 |
| Cached match payloads | 144 |
| 重复 match IDs | 0 |
| Series | 58 |
| Player-match rows | 1,440 |
| 恰好 10 人的比赛 | 144/144 |
| Parsed matches | 144/144 |
| 最短比赛 | 1,352 秒 |
| 最长比赛 | 4,694 秒 |

冻结 manifest：`data/manifests/ti14-2025-opendota.json`。获取与处理阶段都会要求 league index 与 manifest 完全相等；多出、缺失或重复 ID 均会阻断流水线。

独立 raw cache：`data/raw/match-sources/ti14-2025-opendota/`。该目录不复用也不覆盖 TI15-EWC cache。

## 4. Fantasy 字段兼容性

| 分类 | Metrics | 核验结果 |
|---|---|---|
| available | Kills、Deaths、Creep score、GPM | 1,440/1,440 required values present |
| parsed-only | Tower kills、Observer wards、Camps stacked、Rune pickups、Roshan kills、Teamfight participation、Stun duration、Courier kills、First Blood、Smokes | 144/144 parsed；required source missing = 0 |
| unavailable | Madstones、Watchers、Lotuses | 继续输出 null，不使用候选代理字段 |
| uncertain / medium | Tormentor kills | 继续使用 `killed.npc_dota_miniboss`，不提高 reliability |

重点审计：

- Smokes：`item_uses.smoke_of_deceit` 出现在 628 行，合计 2,043；parent map 存在时缺 leaf 继续解释为真实 0；
- Madstone candidate：`item_uses.madstone_bundle` 出现在 1,267 行，合计 14,318，但不等同于 collected，因此不计分；
- Watcher item-use paths：0；
- Lotus 命中为 `lotus_orb` 物品使用，不是莲花池采集，因此不计分；
- Tormentor candidate：245 行，合计 299，继续 medium reliability；
- Roshan：player attribution 合计 342，与 342 条 objective events 完全一致；
- OpenDota objective 还包含 447 courier lost、141 First Blood、328 Aegis、14 Aegis stolen、2,615 building kills。

## 5. First Blood availability policy

以下 3 场的 root `first_blood_time` 大于 0，但没有 claimant，也没有 First Blood objective attribution：

| matchId | first_blood_time | claimant | objective |
|---:|---:|---:|---:|
| `8446311496` | 236 | 0 | 0 |
| `8457152687` | 237 | 0 | 0 |
| `8457241577` | 79 | 0 | 0 |

处理规则：

- 三场共 30 个 player-match First Blood observations 全部为 `unavailable`；
- `rawValue = null`；
- `baseFantasyScore = null`；
- 不把 10 名选手都解释为 0；
- 不根据 `kills_log` 猜测归属；
- 不修改 Fantasy scoring constants。

该政策由 `data/config/datasets/ti14.json` 的 dataset availability metadata 驱动，不写入 `ti15-base-v1`。

## 6. 其他已隔离异常

- Teamfight participation：1 行越界，match `8446312823`、Oli `101259972`、值 `1.1333333`；现有 maximum=1 规则将其标记为 unavailable，不 clamp；
- Stun duration：12 行负值；现有 minimum=0 规则全部标记为 unavailable，不归零；
- 上述两类共 13 条 source anomalies 均出现在 DATA validation 的 quarantine 记录中；
- Madstones / Watchers / Lotuses 按规则集永久 unavailable，不属于 source anomaly；
- First Blood 30 行属于批准的 dataset availability policy，不伪装成 source 值异常。

## 7. Validation profile

TI14 使用严格精确值：

```json
{
  "matchesDiscovered": 144,
  "matchesProcessed": 144,
  "playerMatchRows": 1440,
  "rosterPlayers": 80,
  "playersWithGames": 80,
  "playersWithoutGames": 0,
  "teams": 16,
  "roleUnits": 48
}
```

Payload audit 还精确验证：

- series = 58；
- parsedMatches = 144；
- uniqueAccountIds = 80；
- teamfightOutOfRangeRows = 1；
- negativeStunRows = 12；
- First Blood audit anomaly IDs 与 dataset policy IDs 完全相等。

## 8. 输出与报告

TI14 namespaced outputs：

- `data/generated/datasets/ti14/fantasy-match-scores.json`；
- `data/generated/datasets/ti14/player-fantasy-rankings.json`；
- `data/generated/datasets/ti14/role-fantasy-rankings.json`。

TI14 reports：

- `reports/ti14/PAYLOAD_AUDIT.json`；
- `reports/ti14/PAYLOAD_AUDIT.md`；
- `reports/ti14/DATA_VALIDATION.md`；
- `reports/ti14/RANKINGS_VALIDATION.md`；
- `reports/ti14/ROLE_RANKINGS_VALIDATION.md`。

本阶段不运行 TI14 publish、不创建前端 dataset entry、不修改 dataset switch。前端继续读取 TI15-EWC 旧兼容路径并默认展示 TI15-EWC。

## 9. 来源

- [Valve / Dota 2 TI14 赛事页](https://www.dota2.com/esports/ti14/watch/18324)
- [Liquipedia: The International 2025](https://liquipedia.net/dota2/The_International/2025)
- [OpenDota league 18324 match index](https://api.opendota.com/api/leagues/18324/matches)
- [OpenDota core](https://github.com/odota/core)
- [DotaData TI2025 league page](https://dotadata.org/leagues/the-international-2025)

## 10. 阶段结论

TI14 已完整接入现有多 dataset Fantasy pipeline。Roster、match source、raw cache、processed outputs、audit 与 validation reports 均与 TI15-EWC 隔离；TI14 与 TI15-EWC 共享 `ti15-base-v1` 和相同 Role aggregation 规则，但不共享 dataset identity 或输出 namespace。

目前没有需要产品口径进一步确认的数据问题。后续前端 TI14/TI15-EWC 切换应作为独立阶段实施。
