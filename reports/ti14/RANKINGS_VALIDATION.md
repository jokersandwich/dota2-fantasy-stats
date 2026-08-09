# TI14 Fantasy 排名汇总验证

## 结果

- 状态：**PASSED**
- TI14 选手：80
- 有 TI14 比赛的选手：80
- 没有 TI14 比赛的选手：0
- 数据文件：`data/generated/datasets/ti14/player-fantasy-rankings.json`

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
| Team Liquid | miCKe | 152962063 | 1 | 16 |
| Team Liquid | Nisha | 201358612 | 2 | 16 |
| Team Liquid | SaberLight | 126212866 | 3 | 16 |
| Team Liquid | Boxi | 77490514 | 4 | 16 |
| Team Liquid | Insania | 54580962 | 5 | 16 |
| PVISION | Satanic | 1044002267 | 1 | 23 |
| PVISION | No[o]ne- | 106573901 | 2 | 23 |
| PVISION | DM | 56351509 | 3 | 23 |
| PVISION | 9Class | 164199202 | 4 | 23 |
| PVISION | Dukalis | 73401082 | 5 | 23 |
| BB Team | Pure | 331855530 | 1 | 23 |
| BB Team | gpk~ | 480412663 | 2 | 23 |
| BB Team | MieRo | 165564598 | 3 | 23 |
| BB Team | Save- | 317880638 | 4 | 23 |
| BB Team | Kataomi | 196878136 | 5 | 23 |
| Team Tidebound | shiro | 320252024 | 1 | 16 |
| Team Tidebound | NothingToSay | 173978074 | 2 | 16 |
| Team Tidebound | Bach | 118134220 | 3 | 16 |
| Team Tidebound | planet | 150961567 | 4 | 16 |
| Team Tidebound | y` | 111114687 | 5 | 16 |
| Team Spirit | Yatoro | 321580662 | 1 | 14 |
| Team Spirit | Larl | 106305042 | 2 | 14 |
| Team Spirit | Collapse | 302214028 | 3 | 14 |
| Team Spirit | rue | 847565596 | 4 | 14 |
| Team Spirit | Miposhka | 113331514 | 5 | 14 |
| Team Falcons | skiter | 100058342 | 1 | 29 |
| Team Falcons | Malr1ne | 898455820 | 2 | 29 |
| Team Falcons | ATF | 183719386 | 3 | 29 |
| Team Falcons | Cr1t- | 25907144 | 4 | 29 |
| Team Falcons | Sneyking | 10366616 | 5 | 29 |
| Tundra Esports | Crystallis | 127617979 | 1 | 21 |
| Tundra Esports | bzm | 93618577 | 2 | 21 |
| Tundra Esports | 33 | 86698277 | 3 | 21 |
| Tundra Esports | Saksa | 103735745 | 4 | 21 |
| Tundra Esports | Tobi | 140288368 | 5 | 21 |
| Yakutou Brothers | flyfly | 168028715 | 1 | 16 |
| Yakutou Brothers | Emo | 202217968 | 2 | 16 |
| Yakutou Brothers | Beyond | 139031324 | 3 | 16 |
| Yakutou Brothers | BoBoKa | 207829314 | 4 | 16 |
| Yakutou Brothers | Oli | 101259972 | 5 | 16 |
| Natus Vincere | gotthejuice | 957204049 | 1 | 13 |
| Natus Vincere | Niku | 185590374 | 2 | 13 |
| Natus Vincere | pma | 835864135 | 3 | 13 |
| Natus Vincere | Zayac | 111030315 | 4 | 13 |
| Natus Vincere | Riddys | 130991304 | 5 | 13 |
| Nigma Galaxy | Ghost | 206642367 | 1 | 24 |
| Nigma Galaxy | SumaiL | 111620041 | 2 | 24 |
| Nigma Galaxy | No!ob | 140297552 | 3 | 24 |
| Nigma Galaxy | OmaR | 152168157 | 4 | 24 |
| Nigma Galaxy | GH | 101356886 | 5 | 24 |
| Aurora Gaming | Nightfall | 124801257 | 1 | 13 |
| Aurora Gaming | kiyotaka | 858106446 | 2 | 13 |
| Aurora Gaming | TORONTOTOKYO | 431770905 | 3 | 13 |
| Aurora Gaming | Mira | 256156323 | 4 | 13 |
| Aurora Gaming | panto | 108958769 | 5 | 13 |
| Xtreme Gaming | Ame | 898754153 | 1 | 26 |
| Xtreme Gaming | Xm | 137129583 | 2 | 26 |
| Xtreme Gaming | Xxs | 129958758 | 3 | 26 |
| Xtreme Gaming | XinQ | 157475523 | 4 | 26 |
| Xtreme Gaming | xNova | 94296097 | 5 | 26 |
| Team Nemesis | Akashi | 330534326 | 1 | 10 |
| Team Nemesis | Mac | 104512126 | 2 | 10 |
| Team Nemesis | Raven | 132309493 | 3 | 10 |
| Team Nemesis | Jing | 219755398 | 4 | 10 |
| Team Nemesis | Erice | 100598959 | 5 | 10 |
| BOOM Esports | JaCkky | 392565237 | 1 | 12 |
| BOOM Esports | Armel | 164532005 | 2 | 12 |
| BOOM Esports | Jabz | 100471531 | 3 | 12 |
| BOOM Esports | TIMS | 155494381 | 4 | 12 |
| BOOM Esports | Jaunuel | 148526973 | 5 | 12 |
| Wildcard | Yamsun | 81475303 | 1 | 13 |
| Wildcard | RCY | 154974246 | 2 | 13 |
| Wildcard | Fayde | 160119017 | 3 | 13 |
| Wildcard | Bignum | 90423751 | 4 | 13 |
| Wildcard | Speeed | 191362875 | 5 | 13 |
| HEROIC | Yuma | 177203952 | 1 | 19 |
| HEROIC | 4nalog | 131303632 | 2 | 19 |
| HEROIC | Wisper | 292921272 | 3 | 19 |
| HEROIC | Scofield | 157989498 | 4 | 19 |
| HEROIC | KJ | 81306398 | 5 | 19 |

## 指标 validGames 范围

| 指标 | 最小 validGames | 最大 validGames | 全部 unavailable 的选手数 |
|---|---:|---:|---:|
| `kills` | 10 | 29 | 0 |
| `deaths` | 10 | 29 | 0 |
| `lastHitsAndDenies` | 10 | 29 | 0 |
| `gpm` | 10 | 29 | 0 |
| `madstones` | 0 | 0 | 80 |
| `towerKills` | 10 | 29 | 0 |
| `observerWards` | 10 | 29 | 0 |
| `campsStacked` | 10 | 29 | 0 |
| `runes` | 10 | 29 | 0 |
| `watchers` | 0 | 0 | 80 |
| `lotuses` | 0 | 0 | 80 |
| `roshanKills` | 10 | 29 | 0 |
| `teamfightParticipation` | 10 | 29 | 0 |
| `stunDuration` | 10 | 29 | 0 |
| `tormentorKills` | 10 | 29 | 0 |
| `courierKills` | 10 | 29 | 0 |
| `firstBlood` | 10 | 29 | 0 |
| `smokes` | 10 | 29 | 0 |

## 随机抽查

使用固定种子 `20260807` 随机抽查 10 名有 TI14 比赛的 TI14 选手。每人检查 `deaths`、`gpm`、`firstBlood`、`teamfightParticipation`、`runes` 五项。

| Team | Player | Account ID | 检查结果 |
|---|---|---:|---|
| Team Liquid | Insania | 54580962 | deaths=passed(16), gpm=passed(16), firstBlood=passed(16), teamfightParticipation=passed(16), runes=passed(16) |
| Natus Vincere | pma | 835864135 | deaths=passed(13), gpm=passed(13), firstBlood=passed(13), teamfightParticipation=passed(13), runes=passed(13) |
| Nigma Galaxy | SumaiL | 111620041 | deaths=passed(24), gpm=passed(24), firstBlood=passed(22), teamfightParticipation=passed(24), runes=passed(24) |
| Xtreme Gaming | Xxs | 129958758 | deaths=passed(26), gpm=passed(26), firstBlood=passed(25), teamfightParticipation=passed(26), runes=passed(26) |
| PVISION | DM | 56351509 | deaths=passed(23), gpm=passed(23), firstBlood=passed(23), teamfightParticipation=passed(23), runes=passed(23) |
| Natus Vincere | gotthejuice | 957204049 | deaths=passed(13), gpm=passed(13), firstBlood=passed(13), teamfightParticipation=passed(13), runes=passed(13) |
| Xtreme Gaming | Ame | 898754153 | deaths=passed(26), gpm=passed(26), firstBlood=passed(25), teamfightParticipation=passed(26), runes=passed(26) |
| Team Nemesis | Akashi | 330534326 | deaths=passed(10), gpm=passed(10), firstBlood=passed(10), teamfightParticipation=passed(10), runes=passed(10) |
| Yakutou Brothers | Beyond | 139031324 | deaths=passed(16), gpm=passed(16), firstBlood=passed(16), teamfightParticipation=passed(16), runes=passed(16) |
| Wildcard | Fayde | 160119017 | deaths=passed(13), gpm=passed(13), firstBlood=passed(13), teamfightParticipation=passed(13), runes=passed(13) |

## 数据不可用说明

- `madstones`、`watchers`、`lotuses` 对所有选手均为 `{"best": null, "average": null}`。
- 没有参加 TI14 的 TI14 选手仍保留在数据集中，`gamesPlayed` 为 0，所有指标 Best/Average 均为 null。
- 个别场次不可用不会参与平均值，`validGames` 会小于 `gamesPlayed`；不会补 0。
- `firstBlood.average.rawValue` 保持 0–1 比例；`teamfightParticipation` 同样保持 0–1，不提前乘以 100。

## 错误

无。
