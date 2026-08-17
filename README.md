# Dota2 Fantasy Stats

A React + TypeScript + Vite frontend backed by build-time Python data
pipelines for Dota 2 Fantasy analysis. The current published dataset is TI15
Fantasy player performance based on EWC 2026 and TI14 matches from OpenDota.

https://dota2-fantasy-stats.netlify.app/

pc:

<img width="831" height="550" alt="屏幕截图 2026-08-16 213224" src="https://github.com/user-attachments/assets/12ddb79d-2ec5-431c-92a1-bd3ae1c0045c" />

mobile:

<img width="252" height="550" alt="屏幕截图 2026-08-17 092455" src="https://github.com/user-attachments/assets/7c3a19d3-8a59-4040-a0bb-c2913dc856b2" />

<img width="252" height="550" alt="屏幕截图 2026-08-17 092534" src="https://github.com/user-attachments/assets/cdc82bd8-69b7-4589-89de-9ad93de176fb" />


	
从小组赛来看：

【正反补】是兼具上限和稳定性的最优词条。

【拾取神符】是中单除了正反补以外，另一个上限和稳定性都很高的词条。

【死亡数】是最稳定的词条，优秀选手基本都能打出死亡1次以内的成绩。

【gpm】【团战参与】是和死亡数接近的稳定词条。

【击杀数】【摧毁防御塔】【击杀肉山】波动性稍微强一点，上限更高，下限更低。

【眩晕时间】【消灭魔方】【杀害信使】【第一滴血】都属于上限高，但波动很大，且选手随机的抽奖词条。

【放置守卫】【堆叠野怪】【开雾次数】是辅助的常规词条。

【收集狂石】【采集莲花】【占领观察者】因为数据缺失没有统计到。
	
淘汰赛队伍之间的实力更接近，或许碾压局会变少，gpm更难刷出超高分。而回家局的队伍可能会采取保守的打法，导致比赛时间拖长，所以正反补、放置守卫、堆叠野怪、拾取神符、开雾次数、狂石收集等词条可能会更容易刷出高分。


	
综合推荐

核心：正反补>>死亡=gpm=团战=防御塔（=狂石）>击杀=肉山

中单：正反补=神符>> 击杀=死亡=gpm=团战>防御塔=堆野=肉山

辅助：插眼=堆野=开雾=团战>眩晕=信使>一血



另外，可以根据选择的选手和队伍风格，以及自己的风险偏好进行调整，比如小孩哥考虑gpm、崩溃哥考虑眩晕时间，可以在网站查看具体数据。



## Local setup

```powershell
pnpm install
pnpm run dev
```

Build for Netlify with `pnpm run build`. Netlify configuration is included in
`netlify.toml`.

See `data/README.md` for the data workflow and `data/METRICS.md` for the audited
OpenDota field mappings. The roster file intentionally starts
in `draft` status and empty so unverified team/player identities are never
silently shipped.
