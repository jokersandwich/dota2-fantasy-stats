# TI14 Fantasy Role 排名验证

## 结果

- 状态：**PASSED**
- 队伍：16
- Role Units：48
- 成员共同比赛交集计数总和：864
- 已复核 available 的逐场 Role 指标：12929
- 已复核 null 传播的逐场 Role 指标：2623
- 已复核 MID 单成员恒等计算：4305
- 输出文件：`data/generated/datasets/ti14/role-fantasy-rankings.json`

## 必检项目

| # | 检查 | 结果 |
|---:|---|---|
| 1 | 正好有 48 个 Role Units | PASS |
| 2 | 每支队伍正好包含 Core、Mid、Support | PASS |
| 3 | Core 严格由 Position 1 + 3 构成 | PASS |
| 4 | Mid 严格由 Position 2 构成 | PASS |
| 5 | Support 严格由 Position 4 + 5 构成 | PASS |
| 6 | Core/Support 仅使用完全相同 matchId | PASS |
| 7 | roleRawValue 为同场成员 rawValue 平均 | PASS |
| 8 | roleFantasyScore 为同场成员 FantasyScore 平均 | PASS |
| 9 | Mid 未额外除以 2 | PASS |
| 10 | Best 为最高单场 roleFantasyScore | PASS |
| 11 | Average 基于逐场 Role 数据 | PASS |
| 12 | null 正确传播且未转换为 0 | PASS |
| 13 | gamesPlayedTogether 为成员 matchId 交集大小 | PASS |
| 14 | validGames 只统计完整 available Role 场次 | PASS |
| 15 | NaN | 0 |
| 16 | Infinity | 0 |
| 17 | undefined | 0 |

所有 CORE/SUPPORT 共同比赛均通过成员 `matchId` 集合交集生成，没有使用 start_time、series_id、比赛顺序或 game number。

## 48 个 Role Units

| Team | Role | Positions | Members | gamesPlayedTogether |
|---|---|---|---|---:|
| Team Liquid | CORE | 1+3 | miCKe, SaberLight | 16 |
| Team Liquid | MID | 2 | Nisha | 16 |
| Team Liquid | SUPPORT | 4+5 | Boxi, Insania | 16 |
| PVISION | CORE | 1+3 | Satanic, DM | 23 |
| PVISION | MID | 2 | No[o]ne- | 23 |
| PVISION | SUPPORT | 4+5 | 9Class, Dukalis | 23 |
| BB Team | CORE | 1+3 | Pure, MieRo | 23 |
| BB Team | MID | 2 | gpk~ | 23 |
| BB Team | SUPPORT | 4+5 | Save-, Kataomi | 23 |
| Team Tidebound | CORE | 1+3 | shiro, Bach | 16 |
| Team Tidebound | MID | 2 | NothingToSay | 16 |
| Team Tidebound | SUPPORT | 4+5 | planet, y` | 16 |
| Team Spirit | CORE | 1+3 | Yatoro, Collapse | 14 |
| Team Spirit | MID | 2 | Larl | 14 |
| Team Spirit | SUPPORT | 4+5 | rue, Miposhka | 14 |
| Team Falcons | CORE | 1+3 | skiter, ATF | 29 |
| Team Falcons | MID | 2 | Malr1ne | 29 |
| Team Falcons | SUPPORT | 4+5 | Cr1t-, Sneyking | 29 |
| Tundra Esports | CORE | 1+3 | Crystallis, 33 | 21 |
| Tundra Esports | MID | 2 | bzm | 21 |
| Tundra Esports | SUPPORT | 4+5 | Saksa, Tobi | 21 |
| Yakutou Brothers | CORE | 1+3 | flyfly, Beyond | 16 |
| Yakutou Brothers | MID | 2 | Emo | 16 |
| Yakutou Brothers | SUPPORT | 4+5 | BoBoKa, Oli | 16 |
| Natus Vincere | CORE | 1+3 | gotthejuice, pma | 13 |
| Natus Vincere | MID | 2 | Niku | 13 |
| Natus Vincere | SUPPORT | 4+5 | Zayac, Riddys | 13 |
| Nigma Galaxy | CORE | 1+3 | Ghost, No!ob | 24 |
| Nigma Galaxy | MID | 2 | SumaiL | 24 |
| Nigma Galaxy | SUPPORT | 4+5 | OmaR, GH | 24 |
| Aurora Gaming | CORE | 1+3 | Nightfall, TORONTOTOKYO | 13 |
| Aurora Gaming | MID | 2 | kiyotaka | 13 |
| Aurora Gaming | SUPPORT | 4+5 | Mira, panto | 13 |
| Xtreme Gaming | CORE | 1+3 | Ame, Xxs | 26 |
| Xtreme Gaming | MID | 2 | Xm | 26 |
| Xtreme Gaming | SUPPORT | 4+5 | XinQ, xNova | 26 |
| Team Nemesis | CORE | 1+3 | Akashi, Raven | 10 |
| Team Nemesis | MID | 2 | Mac | 10 |
| Team Nemesis | SUPPORT | 4+5 | Jing, Erice | 10 |
| BOOM Esports | CORE | 1+3 | JaCkky, Jabz | 12 |
| BOOM Esports | MID | 2 | Armel | 12 |
| BOOM Esports | SUPPORT | 4+5 | TIMS, Jaunuel | 12 |
| Wildcard | CORE | 1+3 | Yamsun, Fayde | 13 |
| Wildcard | MID | 2 | RCY | 13 |
| Wildcard | SUPPORT | 4+5 | Bignum, Speeed | 13 |
| HEROIC | CORE | 1+3 | Yuma, Wisper | 19 |
| HEROIC | MID | 2 | 4nalog | 19 |
| HEROIC | SUPPORT | 4+5 | Scofield, KJ | 19 |

## 指标 validGames 范围

| Metric | Min | Max | validGames=0 的 Role Units |
|---|---:|---:|---:|
| `kills` | 10 | 29 | 0 |
| `deaths` | 10 | 29 | 0 |
| `lastHitsAndDenies` | 10 | 29 | 0 |
| `gpm` | 10 | 29 | 0 |
| `madstones` | 0 | 0 | 48 |
| `towerKills` | 10 | 29 | 0 |
| `observerWards` | 10 | 29 | 0 |
| `campsStacked` | 10 | 29 | 0 |
| `runes` | 10 | 29 | 0 |
| `watchers` | 0 | 0 | 48 |
| `lotuses` | 0 | 0 | 48 |
| `roshanKills` | 10 | 29 | 0 |
| `teamfightParticipation` | 10 | 29 | 0 |
| `stunDuration` | 10 | 29 | 0 |
| `tormentorKills` | 10 | 29 | 0 |
| `courierKills` | 10 | 29 | 0 |
| `firstBlood` | 10 | 29 | 0 |
| `smokes` | 10 | 29 | 0 |

## Unavailable 处理

- CORE/SUPPORT 任一成员在同一 matchId 的指标 unavailable，则该场 Role 指标整体 unavailable，并从 Best/Average 排除。
- MID 完全继承 Position 2 的单局 availability。
- `madstones`、`watchers`、`lotuses` 对全部 48 个 Role Units 均保持 `{"best": null, "average": null}`。
- 没有共同比赛的固定成员组合仍保留为 Role Unit，`gamesPlayedTogether` 为 0。

## 错误

无。
