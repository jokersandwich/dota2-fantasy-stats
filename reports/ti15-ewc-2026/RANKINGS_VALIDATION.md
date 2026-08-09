# TI15 Fantasy 排名汇总验证

## 结果

- 状态：**PASSED**
- TI15 选手：80
- 有 EWC 比赛的选手：74
- 没有 EWC 比赛的选手：6
- 数据文件：`data/generated/datasets/ti15-ewc-2026/player-fantasy-rankings.json`

## 验证项目

| 检查 | 结果 |
|---|---|
| roster 总人数为 80 | PASS |
| 每名选手 gamesPlayed 与单局数据行数一致 | PASS |
| 每项 validGames 只统计 available 场次 | PASS |
| NaN | 0 |
| Infinity | 0 |
| undefined | 0（合法 JSON 不存在 undefined） |
| 全部 unavailable 被错误转换为 0 | 0 |
| Best 不是该指标最大 FantasyScore | 0 |
| Best matchId/rawValue/FantasyScore 对不上源比赛 | 0 |
| Average rawValue 不等于有效场次算术平均 | 0 |
| Average FantasyScore 未由共享 scoring engine 生成 | 0 |

Best 的并列规则已验证：先取最高 FantasyScore，再按指标的优秀 rawValue 方向，仍相同则取较小 matchId。

## 每名选手 gamesPlayed

| Team | Player | Account ID | Position | Games |
|---|---|---:|---:|---:|
| Aurora Gaming | Nightfall | 124801257 | 1 | 12 |
| Aurora Gaming | Mikoto | 301750126 | 2 | 12 |
| Aurora Gaming | Ws | 126842529 | 3 | 12 |
| Aurora Gaming | Mira | 256156323 | 4 | 12 |
| Aurora Gaming | kaori | 320219866 | 5 | 12 |
| BoomBoys | Kiritych~ | 172099728 | 1 | 20 |
| BoomBoys | gpk~ | 480412663 | 2 | 20 |
| BoomBoys | MieRo | 165564598 | 3 | 20 |
| BoomBoys | Save- | 317880638 | 4 | 20 |
| BoomBoys | Kataomi | 196878136 | 5 | 20 |
| 1w Team | Pure | 331855530 | 1 | 13 |
| 1w Team | bzm | 93618577 | 2 | 13 |
| 1w Team | 33 | 86698277 | 3 | 13 |
| 1w Team | Ari | 346412363 | 4 | 13 |
| 1w Team | Whitemon | 136829091 | 5 | 13 |
| Team Falcons | skiter | 100058342 | 1 | 12 |
| Team Falcons | Malr1ne | 898455820 | 2 | 12 |
| Team Falcons | ATF | 183719386 | 3 | 12 |
| Team Falcons | Cr1t- | 25907144 | 4 | 12 |
| Team Falcons | Sneyking | 10366616 | 5 | 12 |
| Team Liquid | m1CKe | 152962063 | 1 | 16 |
| Team Liquid | Nisha | 201358612 | 2 | 16 |
| Team Liquid | Ace | 97590558 | 3 | 16 |
| Team Liquid | Boxi | 77490514 | 4 | 16 |
| Team Liquid | tOfu | 16497807 | 5 | 16 |
| Team Yandex | watson | 171262902 | 1 | 17 |
| Team Yandex | CHIRA_JUNIOR | 312436974 | 2 | 17 |
| Team Yandex | DM | 56351509 | 3 | 17 |
| Team Yandex | Saksa | 103735745 | 4 | 17 |
| Team Yandex | Malady | 93817671 | 5 | 17 |
| Xtreme Gaming | Ame | 898754153 | 1 | 13 |
| Xtreme Gaming | NothingToSay | 173978074 | 2 | 13 |
| Xtreme Gaming | Xxs | 129958758 | 3 | 13 |
| Xtreme Gaming | fy | 101695162 | 4 | 13 |
| Xtreme Gaming | xNova | 94296097 | 5 | 13 |
| Team Spirit | Yatoro | 321580662 | 1 | 15 |
| Team Spirit | Larl | 106305042 | 2 | 15 |
| Team Spirit | Collapse | 302214028 | 3 | 15 |
| Team Spirit | not me | 218231587 | 4 | 15 |
| Team Spirit | rue | 847565596 | 5 | 15 |
| TEAM VISION | Satanic | 1044002267 | 1 | 19 |
| TEAM VISION | No[o]ne- | 106573901 | 2 | 19 |
| TEAM VISION | Noticed | 195108598 | 3 | 19 |
| TEAM VISION | 9Class | 164199202 | 4 | 19 |
| TEAM VISION | Dukalis | 73401082 | 5 | 19 |
| Nigma Galaxy | SumaiL | 111620041 | 1 | 12 |
| Nigma Galaxy | lorenof | 210053851 | 2 | 12 |
| Nigma Galaxy | Davai | 138880576 | 3 | 12 |
| Nigma Galaxy | OmaR | 152168157 | 4 | 12 |
| Nigma Galaxy | GH | 101356886 | 5 | 12 |
| HULIGANI | ssnovv1 | 320017600 | 1 | 10 |
| HULIGANI | Mirage` | 140251702 | 2 | 10 |
| HULIGANI | Corrupted | 92487440 | 3 | 10 |
| HULIGANI | sayuw | 145065875 | 4 | 0 |
| HULIGANI | RESPECT | 123787715 | 5 | 10 |
| Team Resilience | YSR-04E | 170896543 | 1 | 0 |
| Team Resilience | Echozz | 315272623 | 2 | 0 |
| Team Resilience | niu | 145957968 | 3 | 0 |
| Team Resilience | planet | 150961567 | 4 | 0 |
| Team Resilience | zzq | 249835593 | 5 | 0 |
| Vici Gaming | shiro | 320252024 | 1 | 19 |
| Vici Gaming | Xm | 137129583 | 2 | 19 |
| Vici Gaming | Bach | 118134220 | 3 | 19 |
| Vici Gaming | XinQ | 157475523 | 4 | 19 |
| Vici Gaming | y` | 111114687 | 5 | 19 |
| LGD Gaming | Yuma | 177203952 | 1 | 14 |
| LGD Gaming | TaiLung | 1026694469 | 2 | 14 |
| LGD Gaming | Wisper | 292921272 | 3 | 14 |
| LGD Gaming | Thiolicor | 105045291 | 4 | 14 |
| LGD Gaming | KJ | 81306398 | 5 | 14 |
| GamerLegion | Ghost | 206642367 | 1 | 10 |
| GamerLegion | RCY | 154974246 | 2 | 10 |
| GamerLegion | Fayde | 160119017 | 3 | 10 |
| GamerLegion | Bignum | 90423751 | 4 | 10 |
| GamerLegion | Speeed | 191362875 | 5 | 10 |
| OG | Natsumi | 355168766 | 1 | 10 |
| OG | Yopaj- | 324277900 | 2 | 10 |
| OG | Raven | 132309493 | 3 | 10 |
| OG | TIMS | 155494381 | 4 | 10 |
| OG | skem | 100594231 | 5 | 10 |

## 指标 validGames 范围

| 指标 | 最小 validGames | 最大 validGames | 全部 unavailable 的选手数 |
|---|---:|---:|---:|
| `kills` | 0 | 20 | 6 |
| `deaths` | 0 | 20 | 6 |
| `lastHitsAndDenies` | 0 | 20 | 6 |
| `gpm` | 0 | 20 | 6 |
| `madstones` | 0 | 0 | 80 |
| `towerKills` | 0 | 20 | 6 |
| `observerWards` | 0 | 20 | 6 |
| `campsStacked` | 0 | 20 | 6 |
| `runes` | 0 | 20 | 6 |
| `watchers` | 0 | 0 | 80 |
| `lotuses` | 0 | 0 | 80 |
| `roshanKills` | 0 | 20 | 6 |
| `teamfightParticipation` | 0 | 20 | 6 |
| `stunDuration` | 0 | 20 | 6 |
| `tormentorKills` | 0 | 20 | 6 |
| `courierKills` | 0 | 20 | 6 |
| `firstBlood` | 0 | 20 | 6 |
| `smokes` | 0 | 20 | 6 |

## 随机抽查

使用固定种子 `20260807` 随机抽查 10 名有 EWC 比赛的 TI15 选手。每人检查 `deaths`、`gpm`、`firstBlood`、`teamfightParticipation`、`runes` 五项。

| Team | Player | Account ID | 检查结果 |
|---|---|---:|---|
| Aurora Gaming | kaori | 320219866 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |
| TEAM VISION | Noticed | 195108598 | deaths=passed(19), gpm=passed(19), firstBlood=passed(19), teamfightParticipation=passed(19), runes=passed(19) |
| Nigma Galaxy | lorenof | 210053851 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |
| Vici Gaming | XinQ | 157475523 | deaths=passed(19), gpm=passed(19), firstBlood=passed(19), teamfightParticipation=passed(19), runes=passed(19) |
| BoomBoys | MieRo | 165564598 | deaths=passed(20), gpm=passed(20), firstBlood=passed(20), teamfightParticipation=passed(20), runes=passed(20) |
| TEAM VISION | Satanic | 1044002267 | deaths=passed(19), gpm=passed(19), firstBlood=passed(19), teamfightParticipation=passed(19), runes=passed(19) |
| Vici Gaming | Xm | 137129583 | deaths=passed(19), gpm=passed(19), firstBlood=passed(19), teamfightParticipation=passed(19), runes=passed(19) |
| LGD Gaming | TaiLung | 1026694469 | deaths=passed(14), gpm=passed(14), firstBlood=passed(14), teamfightParticipation=passed(14), runes=passed(14) |
| Team Spirit | Collapse | 302214028 | deaths=passed(15), gpm=passed(15), firstBlood=passed(15), teamfightParticipation=passed(15), runes=passed(15) |
| GamerLegion | Fayde | 160119017 | deaths=passed(10), gpm=passed(10), firstBlood=passed(10), teamfightParticipation=passed(10), runes=passed(10) |

## 数据不可用说明

- `madstones`、`watchers`、`lotuses` 对所有选手均为 `{"best": null, "average": null}`。
- 没有参加 EWC 的 TI15 选手仍保留在数据集中，`gamesPlayed` 为 0，所有指标 Best/Average 均为 null。
- 个别场次不可用不会参与平均值，`validGames` 会小于 `gamesPlayed`；不会补 0。
- `firstBlood.average.rawValue` 保持 0–1 比例；`teamfightParticipation` 同样保持 0–1，不提前乘以 100。

## 错误

无。
