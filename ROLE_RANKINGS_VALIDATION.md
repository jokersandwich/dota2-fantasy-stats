# TI15 Fantasy Role 排名验证

## 结果

- 状态：**PASSED**
- 队伍：16
- Role Units：48
- 成员共同比赛交集计数总和：626
- 已复核 available 的逐场 Role 指标：9389
- 已复核 null 传播的逐场 Role 指标：1879
- 已复核 MID 单成员恒等计算：3180
- 输出文件：`C:/Users/41011/Documents/Project/ti15-ewc-stats/data/processed/role-fantasy-rankings.json`

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
| Aurora Gaming | CORE | 1+3 | Nightfall, Ws | 12 |
| Aurora Gaming | MID | 2 | Mikoto | 12 |
| Aurora Gaming | SUPPORT | 4+5 | Mira, kaori | 12 |
| BoomBoys | CORE | 1+3 | Kiritych~, MieRo | 20 |
| BoomBoys | MID | 2 | gpk~ | 20 |
| BoomBoys | SUPPORT | 4+5 | Save-, Kataomi | 20 |
| 1w Team | CORE | 1+3 | Pure, 33 | 13 |
| 1w Team | MID | 2 | bzm | 13 |
| 1w Team | SUPPORT | 4+5 | Ari, Whitemon | 13 |
| Team Falcons | CORE | 1+3 | skiter, ATF | 12 |
| Team Falcons | MID | 2 | Malr1ne | 12 |
| Team Falcons | SUPPORT | 4+5 | Cr1t-, Sneyking | 12 |
| Team Liquid | CORE | 1+3 | m1CKe, Ace | 16 |
| Team Liquid | MID | 2 | Nisha | 16 |
| Team Liquid | SUPPORT | 4+5 | Boxi, tOfu | 16 |
| Team Yandex | CORE | 1+3 | watson, DM | 17 |
| Team Yandex | MID | 2 | CHIRA_JUNIOR | 17 |
| Team Yandex | SUPPORT | 4+5 | Saksa, Malady | 17 |
| Xtreme Gaming | CORE | 1+3 | Ame, Xxs | 13 |
| Xtreme Gaming | MID | 2 | NothingToSay | 13 |
| Xtreme Gaming | SUPPORT | 4+5 | fy, xNova | 13 |
| Team Spirit | CORE | 1+3 | Yatoro, Collapse | 15 |
| Team Spirit | MID | 2 | Larl | 15 |
| Team Spirit | SUPPORT | 4+5 | not me, rue | 15 |
| TEAM VISION | CORE | 1+3 | Satanic, Noticed | 19 |
| TEAM VISION | MID | 2 | No[o]ne- | 19 |
| TEAM VISION | SUPPORT | 4+5 | 9Class, Dukalis | 19 |
| Nigma Galaxy | CORE | 1+3 | SumaiL, Davai | 12 |
| Nigma Galaxy | MID | 2 | lorenof | 12 |
| Nigma Galaxy | SUPPORT | 4+5 | OmaR, GH | 12 |
| HULIGANI | CORE | 1+3 | ssnovv1, Corrupted | 10 |
| HULIGANI | MID | 2 | Mirage` | 10 |
| HULIGANI | SUPPORT | 4+5 | sayuw, RESPECT | 0 |
| Team Resilience | CORE | 1+3 | YSR-04E, niu | 0 |
| Team Resilience | MID | 2 | Echozz | 0 |
| Team Resilience | SUPPORT | 4+5 | planet, zzq | 0 |
| Vici Gaming | CORE | 1+3 | shiro, Bach | 19 |
| Vici Gaming | MID | 2 | Xm | 19 |
| Vici Gaming | SUPPORT | 4+5 | XinQ, y` | 19 |
| LGD Gaming | CORE | 1+3 | Yuma, Wisper | 14 |
| LGD Gaming | MID | 2 | TaiLung | 14 |
| LGD Gaming | SUPPORT | 4+5 | Thiolicor, KJ | 14 |
| GamerLegion | CORE | 1+3 | Ghost, Fayde | 10 |
| GamerLegion | MID | 2 | RCY | 10 |
| GamerLegion | SUPPORT | 4+5 | Bignum, Speeed | 10 |
| OG | CORE | 1+3 | Natsumi, Raven | 10 |
| OG | MID | 2 | Yopaj- | 10 |
| OG | SUPPORT | 4+5 | TIMS, skem | 10 |

## 指标 validGames 范围

| Metric | Min | Max | validGames=0 的 Role Units |
|---|---:|---:|---:|
| `kills` | 0 | 20 | 4 |
| `deaths` | 0 | 20 | 4 |
| `lastHitsAndDenies` | 0 | 20 | 4 |
| `gpm` | 0 | 20 | 4 |
| `madstones` | 0 | 0 | 48 |
| `towerKills` | 0 | 20 | 4 |
| `observerWards` | 0 | 20 | 4 |
| `campsStacked` | 0 | 20 | 4 |
| `runes` | 0 | 20 | 4 |
| `watchers` | 0 | 0 | 48 |
| `lotuses` | 0 | 0 | 48 |
| `roshanKills` | 0 | 20 | 4 |
| `teamfightParticipation` | 0 | 20 | 4 |
| `stunDuration` | 0 | 20 | 4 |
| `tormentorKills` | 0 | 20 | 4 |
| `courierKills` | 0 | 20 | 4 |
| `firstBlood` | 0 | 20 | 4 |
| `smokes` | 0 | 20 | 4 |

## Unavailable 处理

- CORE/SUPPORT 任一成员在同一 matchId 的指标 unavailable，则该场 Role 指标整体 unavailable，并从 Best/Average 排除。
- MID 完全继承 Position 2 的单局 availability。
- `madstones`、`watchers`、`lotuses` 对全部 48 个 Role Units 均保持 `{"best": null, "average": null}`。
- 没有共同比赛的固定成员组合仍保留为 Role Unit，`gamesPlayedTogether` 为 0。

## 错误

无。
