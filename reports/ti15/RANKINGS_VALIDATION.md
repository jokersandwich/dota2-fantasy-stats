# TI15 Fantasy 排名汇总验证

## 结果

- 状态：**PASSED**
- TI15 选手：80
- 有 TI15 比赛的选手：80
- 没有 TI15 比赛的选手：0
- 数据文件：`data/generated/datasets/ti15/player-fantasy-rankings.json`

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
| BoomBoys | Kiritych~ | 172099728 | 1 | 12 |
| BoomBoys | gpk~ | 480412663 | 2 | 12 |
| BoomBoys | MieRo | 165564598 | 3 | 12 |
| BoomBoys | Save- | 317880638 | 4 | 12 |
| BoomBoys | Kataomi | 196878136 | 5 | 12 |
| Iron Wing | Pure | 331855530 | 1 | 14 |
| Iron Wing | bzm | 93618577 | 2 | 14 |
| Iron Wing | 33 | 86698277 | 3 | 14 |
| Iron Wing | Ari | 346412363 | 4 | 14 |
| Iron Wing | Whitemon | 136829091 | 5 | 14 |
| Team Falcons | skiter | 100058342 | 1 | 15 |
| Team Falcons | Malr1ne | 898455820 | 2 | 15 |
| Team Falcons | ATF | 183719386 | 3 | 15 |
| Team Falcons | Cr1t- | 25907144 | 4 | 15 |
| Team Falcons | Sneyking | 10366616 | 5 | 15 |
| Team Liquid | m1CKe | 152962063 | 1 | 14 |
| Team Liquid | Nisha | 201358612 | 2 | 14 |
| Team Liquid | Ace | 97590558 | 3 | 14 |
| Team Liquid | Boxi | 77490514 | 4 | 14 |
| Team Liquid | tOfu | 16497807 | 5 | 14 |
| Team Yandex | watson | 171262902 | 1 | 14 |
| Team Yandex | CHIRA_JUNIOR | 312436974 | 2 | 14 |
| Team Yandex | DM | 56351509 | 3 | 14 |
| Team Yandex | Saksa | 103735745 | 4 | 14 |
| Team Yandex | Malady | 93817671 | 5 | 14 |
| Xtreme Gaming | Ame | 898754153 | 1 | 11 |
| Xtreme Gaming | NothingToSay | 173978074 | 2 | 11 |
| Xtreme Gaming | Xxs | 129958758 | 3 | 11 |
| Xtreme Gaming | fy | 101695162 | 4 | 11 |
| Xtreme Gaming | xNova | 94296097 | 5 | 11 |
| Team Spirit | Yatoro | 321580662 | 1 | 11 |
| Team Spirit | Larl | 106305042 | 2 | 11 |
| Team Spirit | Collapse | 302214028 | 3 | 11 |
| Team Spirit | not me | 218231587 | 4 | 11 |
| Team Spirit | rue | 847565596 | 5 | 11 |
| TEAM VISION | Satanic | 1044002267 | 1 | 10 |
| TEAM VISION | No[o]ne- | 106573901 | 2 | 10 |
| TEAM VISION | Noticed | 195108598 | 3 | 10 |
| TEAM VISION | 9Class | 164199202 | 4 | 10 |
| TEAM VISION | Dukalis | 73401082 | 5 | 10 |
| Nigma Galaxy | SumaiL | 111620041 | 1 | 10 |
| Nigma Galaxy | lorenof | 210053851 | 2 | 10 |
| Nigma Galaxy | Davai | 138880576 | 3 | 10 |
| Nigma Galaxy | OmaR | 152168157 | 4 | 10 |
| Nigma Galaxy | GH | 101356886 | 5 | 10 |
| HULIGANI | ssnovv1 | 320017600 | 1 | 10 |
| HULIGANI | Mirage` | 140251702 | 2 | 10 |
| HULIGANI | Corrupted | 92487440 | 3 | 10 |
| HULIGANI | sayuw | 145065875 | 4 | 10 |
| HULIGANI | RESPECT | 123787715 | 5 | 10 |
| Team Resilience | YSR-04E | 170896543 | 1 | 13 |
| Team Resilience | Echozz | 315272623 | 2 | 13 |
| Team Resilience | niu | 145957968 | 3 | 13 |
| Team Resilience | planet | 150961567 | 4 | 13 |
| Team Resilience | zzq | 249835593 | 5 | 13 |
| Vici Gaming | shiro | 320252024 | 1 | 12 |
| Vici Gaming | Xm | 137129583 | 2 | 12 |
| Vici Gaming | Bach | 118134220 | 3 | 12 |
| Vici Gaming | XinQ | 157475523 | 4 | 12 |
| Vici Gaming | y` | 111114687 | 5 | 12 |
| LGD Gaming | Yuma | 177203952 | 1 | 13 |
| LGD Gaming | Topson | 94054712 | 2 | 13 |
| LGD Gaming | Wisper | 292921272 | 3 | 13 |
| LGD Gaming | Thiolicor | 105045291 | 4 | 13 |
| LGD Gaming | KJ | 81306398 | 5 | 13 |
| GamerLegion | Ghost | 206642367 | 1 | 12 |
| GamerLegion | RCY | 154974246 | 2 | 12 |
| GamerLegion | Fayde | 160119017 | 3 | 12 |
| GamerLegion | Bignum | 90423751 | 4 | 12 |
| GamerLegion | Speeed | 191362875 | 5 | 12 |
| OG | Natsumi | 355168766 | 1 | 11 |
| OG | Yopaj- | 324277900 | 2 | 11 |
| OG | Raven | 132309493 | 3 | 11 |
| OG | TIMS | 155494381 | 4 | 11 |
| OG | skem | 100594231 | 5 | 11 |

## 指标 validGames 范围

| 指标 | 最小 validGames | 最大 validGames | 全部 unavailable 的选手数 |
|---|---:|---:|---:|
| `kills` | 10 | 15 | 0 |
| `deaths` | 10 | 15 | 0 |
| `lastHitsAndDenies` | 10 | 15 | 0 |
| `gpm` | 10 | 15 | 0 |
| `madstones` | 0 | 0 | 80 |
| `towerKills` | 10 | 15 | 0 |
| `observerWards` | 10 | 15 | 0 |
| `campsStacked` | 10 | 15 | 0 |
| `runes` | 10 | 15 | 0 |
| `watchers` | 0 | 0 | 80 |
| `lotuses` | 0 | 0 | 80 |
| `roshanKills` | 10 | 15 | 0 |
| `teamfightParticipation` | 10 | 15 | 0 |
| `stunDuration` | 10 | 15 | 0 |
| `tormentorKills` | 10 | 15 | 0 |
| `courierKills` | 10 | 15 | 0 |
| `firstBlood` | 9 | 15 | 0 |
| `smokes` | 10 | 15 | 0 |

## 随机抽查

使用固定种子 `20260807` 随机抽查 10 名有 TI15 比赛的 TI15 选手。每人检查 `deaths`、`gpm`、`firstBlood`、`teamfightParticipation`、`runes` 五项。

| Team | Player | Account ID | 检查结果 |
|---|---|---:|---|
| Aurora Gaming | kaori | 320219866 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |
| TEAM VISION | Noticed | 195108598 | deaths=passed(10), gpm=passed(10), firstBlood=passed(10), teamfightParticipation=passed(10), runes=passed(10) |
| Nigma Galaxy | lorenof | 210053851 | deaths=passed(10), gpm=passed(10), firstBlood=passed(10), teamfightParticipation=passed(10), runes=passed(10) |
| Team Resilience | niu | 145957968 | deaths=passed(13), gpm=passed(13), firstBlood=passed(13), teamfightParticipation=passed(13), runes=passed(13) |
| BoomBoys | MieRo | 165564598 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |
| TEAM VISION | Satanic | 1044002267 | deaths=passed(10), gpm=passed(10), firstBlood=passed(10), teamfightParticipation=passed(10), runes=passed(10) |
| Team Resilience | YSR-04E | 170896543 | deaths=passed(13), gpm=passed(13), firstBlood=passed(13), teamfightParticipation=passed(13), runes=passed(13) |
| Vici Gaming | shiro | 320252024 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |
| Team Spirit | Collapse | 302214028 | deaths=passed(11), gpm=passed(11), firstBlood=passed(11), teamfightParticipation=passed(11), runes=passed(11) |
| GamerLegion | Fayde | 160119017 | deaths=passed(12), gpm=passed(12), firstBlood=passed(12), teamfightParticipation=passed(12), runes=passed(12) |

## 数据不可用说明

- `madstones`、`watchers`、`lotuses` 对所有选手均为 `{"best": null, "average": null}`。
- 没有参加 TI15 的 TI15 选手仍保留在数据集中，`gamesPlayed` 为 0，所有指标 Best/Average 均为 null。
- 个别场次不可用不会参与平均值，`validGames` 会小于 `gamesPlayed`；不会补 0。
- `firstBlood.average.rawValue` 保持 0–1 比例；`teamfightParticipation` 同样保持 0–1，不提前乘以 100。

## 错误

无。
