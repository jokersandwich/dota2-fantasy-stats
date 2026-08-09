# Dota 2 Fantasy 多数据集架构方案

## 1. 目标与约束

本方案用于将当前单一的 TI15-EWC 数据管线演进为可长期支持多赛事、多年份的数据集架构。

长期至少需要支持三个相互独立的 dataset：

| Dataset | Roster Source | Match Source | Ruleset |
|---|---|---|---|
| `ti14` | TI14 完整参赛名单 | TI14 正赛 | 当前已验证的 TI15 规则集 |
| `ti15-ewc-2026` | TI15 名单 | EWC 2026 / OpenDota league 19785 | 当前 TI15 规则集 |
| `ti15` | 与 TI15-EWC 复用同一份 TI15 名单 | TI15 正赛 | TI15 规则集 |

必须遵守以下原则：

- Roster source 与 match/statistics source 是两个独立概念。
- Dataset 可以复用 roster source，但不能因此共享比赛缓存、处理产物、验证报告或前端入口。
- Scoring ruleset 可以被多个 dataset 共享；三个规划中的 dataset 全部引用当前已验证的 `ti15-base-v1`。
- TI14 基础数据集必须覆盖 TI14 当届全部参赛队伍和参赛选手，不能按 TI15 roster 裁剪。
- “同时参加 TI14 和 TI15 的选手”属于未来前端筛选或跨数据集比较功能，不进入基础数据处理管线。
- 三个 dataset 统一使用当前 TI15 梦幻挑战的 Role 组合与聚合规则。
- 当前 TI15-EWC 始终是默认 dataset，直至前端多数据集切换单独实施并验证完成。
- 本轮架构改造不改变任何 Fantasy scoring constants、公式、Role 计算规则、缺失值规则或当前前端行为。

## 2. 总体模型

系统拆分成四个独立概念：

```text
Roster Source ----+
                  |
Match Source -----+--> Dataset --> 独立产物、验证和前端入口
                  |
Ruleset ---------+
```

- **Roster Source**：定义参赛队伍、选手身份、`account_id`、位置和 Role 阵容。
- **Match Source**：定义统计比赛来自哪个赛事、数据提供方和 league/match 范围。
- **Ruleset**：定义版本化 Fantasy 计分规则；同一个规则集可以安全地被多个 dataset 引用。
- **Dataset**：引用以上三者，形成一个不可混用的发布单元。

本项目使用 ruleset 的目的不是还原各届 TI 当年的历史 Fantasy 规则，而是采用统一评价口径比较不同赛事中的选手表现。当前统一口径为已经完成字段审计和验证的 TI15 Fantasy rules，即 `ti15-base-v1`。

三个规划中的 dataset 均固定引用：

```text
ti14           -> ti15-base-v1
ti15-ewc-2026  -> ti15-base-v1
ti15           -> ti15-base-v1
```

共享 ruleset 只表示共享不可变的计分定义。各 dataset 的单场计分结果、排名和验证文件仍然独立生成和存储。

所有生成产物必须携带以下 provenance：

```json
{
  "datasetId": "ti15-ewc-2026",
  "rosterSourceId": "ti15-2026",
  "matchSourceId": "ewc-2026-opendota",
  "rulesetId": "ti15-base-v1"
}
```

下游模块读取上游产物时必须核对这些标识。不匹配时立即失败，避免把某个赛事的单场数据与另一个赛事的 roster 或排名混用。

## 3. Dataset Config

建议 dataset config 采用以下结构：

```json
{
  "schemaVersion": 1,
  "datasetId": "ti15-ewc-2026",
  "status": "published",
  "rosterSourceId": "ti15-2026",
  "matchSourceId": "ewc-2026-opendota",
  "rulesetId": "ti15-base-v1",
  "populationPolicy": {
    "playerRankings": "all-roster-participants",
    "roleRankings": "configured-role-lineups",
    "crossDatasetIntersection": false
  },
  "validationProfile": "ti15-ewc-2026"
}
```

字段含义：

- `schemaVersion`：配置结构版本。
- `datasetId`：不可变的 dataset 身份，同时作为输出命名空间。
- `status`：`draft`、`verified` 或 `published`。
- `rosterSourceId`：引用独立 roster source。
- `matchSourceId`：引用独立 match source。
- `rulesetId`：锁定统一评价规则版本。多个 dataset 可以引用同一个 ID，但不能复制或修改其中的计分常量。
- `populationPolicy.playerRankings`：个人排名覆盖 roster 中全部参赛选手。
- `populationPolicy.roleRankings`：Role 排名使用 roster 中配置的固定位置阵容。
- `populationPolicy.crossDatasetIntersection`：基础处理阶段禁止跨 dataset 取交集。
- `validationProfile`：引用该 dataset 的规模和质量验证要求。

正式输出路径不在 dataset config 中自由填写，而是统一由 `datasetId` 推导，防止多个 dataset 写入同一个目录。

默认 dataset 由独立注册表管理：

```json
{
  "schemaVersion": 1,
  "defaultDatasetId": "ti15-ewc-2026",
  "datasets": [
    "ti15-ewc-2026"
  ]
}
```

当前阶段注册表只包含 TI15-EWC。

## 4. Roster Source

Roster source 采用独立、可复用的版本化文件：

```json
{
  "schemaVersion": 1,
  "rosterSourceId": "ti15-2026",
  "competition": {
    "code": "TI15",
    "edition": 15,
    "season": 2026
  },
  "status": "verified",
  "lastVerified": "2026-08-07",
  "expectations": {
    "teamCount": 16,
    "requiredPositions": [1, 2, 3, 4, 5],
    "accountIdsUnique": true
  },
  "teams": []
}
```

Roster source 负责：

- 完整参赛队伍和选手身份；
- 数字 OpenDota `account_id`；
- 队伍归属和位置；
- 首发、替补、临时替补等参赛资格；
- 用于固定 Core/Mid/Support Role Unit 的五人位置阵容。

玩家排名覆盖所有被标记为参赛的 roster 成员。Role 排名只使用配置好的位置阵容。因此，即使未来 TI14 某队存在超过五名参赛选手，也不需要为了生成 Role Unit 而从个人基础数据中删除替补。

TI15-EWC 与未来 TI15 都引用 `ti15-2026`，从而复用同一份名单事实。

## 5. Match Source

Match source 独立描述赛事和 OpenDota 数据范围：

```json
{
  "schemaVersion": 1,
  "matchSourceId": "ewc-2026-opendota",
  "competition": {
    "code": "EWC",
    "season": 2026
  },
  "provider": {
    "id": "OpenDota",
    "leagueIds": [19785]
  },
  "cacheNamespace": "ewc-2026-opendota",
  "matchSelection": {
    "stages": "all",
    "excludedMatchIds": []
  },
  "expectations": {
    "playersPerMatch": 10
  }
}
```

使用 `leagueIds` 数组而不是单个 league ID，以支持一个赛事由多个 OpenDota league 组成的情况。

不同 match source 必须拥有不同 `cacheNamespace`：

```text
ewc-2026-opendota  -> TI15-EWC 的比赛缓存
ti14-...-opendota -> TI14 的比赛缓存
ti15-...-opendota -> 未来 TI15 正赛的比赛缓存
```

## 6. Roster 与 Match Source 的处理边界

数据处理顺序如下：

1. Match source 决定加载哪些比赛。
2. Scoring 对比赛中的全部玩家行进行单场计分，不读取 roster，不做 roster 过滤。
3. Player rankings 根据当前 dataset 引用的 roster source 建立完整参赛选手集合。
4. 只把当前 roster 成员在当前 match source 中的比赛记录归入该 dataset。
5. Role rankings 使用同一 roster source 中配置的固定位置阵容。

由此保证：

- TI14 dataset 只读取 TI14 roster 和 TI14 match source。
- TI14 不会因为 TI15 roster 而遗漏任何参赛选手。
- 没有有效比赛的 roster 选手仍保留在输出中，`gamesPlayed` 为 0，各指标保持 `null`。
- 跨 dataset 的选手交集只通过 `account_id` 在查询或前端比较层计算。

### 统一的 Role Aggregation Rules

TI14、TI15-EWC 和未来 TI15 全部沿用当前已经验证的 TI15 Role 规则：

- Core = Position 1 + Position 3；
- Mid = Position 2；
- Support = Position 4 + Position 5。

三个 dataset 也统一沿用以下聚合语义：

- Core 和 Support 只按完全相同的 `matchId` 连接两名成员，不能使用时间、系列、顺序或局数推断共同比赛。
- 两人 Role Unit 的单场 `roleRawValue` 是两名成员 raw value 的算术平均。
- 两人 Role Unit 的单场 `roleFantasyScore` 是两名成员已经计算完成的 Fantasy score 的算术平均。
- Mid 完全继承 Position 2 的单场值，不额外除以二。
- 任一成员的某项指标 unavailable 时，该场 Role 指标整体 unavailable，null 必须继续传播，不能转换为零。
- Best 首先选择最高 Fantasy score，再按指标配置的 raw value 优秀方向打破平局，仍相同时选择较小的 `matchId`。
- Average 必须从有效的逐场 Role 值计算，不能先计算成员的赛事平均再组合。
- unavailable 观察不参加平均值，`validGames` 记录实际有效场次。

这些规则属于所有 dataset 共享的统一评价逻辑，不为 TI14 创建历史版本，也不在前端重复实现。

## 7. TI15 Roster 复用与输出隔离

TI15-EWC 与未来 TI15 的关系如下：

```text
ti15-ewc-2026
  rosterSourceId = ti15-2026
  matchSourceId  = ewc-2026-opendota

ti15
  rosterSourceId = ti15-2026
  matchSourceId  = ti15-2026-opendota
```

两者只共享 roster source。以下内容全部独立：

- `datasetId`；
- match source；
- raw/cache namespace；
- 单场 Fantasy 计分产物；
- 玩家排名产物；
- Role 排名产物；
- 验证报告；
- 前端 dataset entry。

三个 dataset 使用同一 ruleset，但必须在各自产物中记录相同的 `rulesetId`，不能共享可写的 processed 文件。

## 8. 目录规划

```text
data/
  config/
    datasets/
      index.json
      ti15-ewc-2026.json
    match-sources/
      ewc-2026-opendota.json

  rosters/
    ti15-2026.json

  raw/
    match-sources/
      ewc-2026-opendota/
        leagues/
          19785.json
        matches/
          <matchId>.json

  generated/
    datasets/
      ti15-ewc-2026/
        fantasy-match-scores.json
        player-fantasy-rankings.json
        role-fantasy-rankings.json

  baselines/
    ti15-ewc-2026.semantic-sha256.json

public/
  data/
    datasets/
      ti15-ewc-2026/
        role-fantasy-rankings.json

reports/
  ti15-ewc-2026/
    DATA_VALIDATION.md
    RANKINGS_VALIDATION.md
    ROLE_RANKINGS_VALIDATION.md
```

未来 TI14 和 TI15 正赛分别增加自己的 dataset config、match source、raw namespace、generated 目录和 reports 目录。

## 9. 当前安全实施步骤

### 第 1 步：建立 TI15-EWC 不可变语义基线

计划新增：

- `scripts/fantasy/semantic_compare.py`
- `scripts/fantasy/test_semantic_compare.py`
- `data/baselines/ti15-ewc-2026.semantic-sha256.json`

这一阶段不修改业务处理逻辑和现有输出。

语义比较器只忽略以下非业务字段：

- `generatedAt`；
- 输出文件路径；
- 重构后新增的 dataset provenance。

所有统计值、顺序、成员、availability 和 `matchId` 必须精确相同，不使用浮点容差。

### 第 2 步：引入配置层，继续使用旧输出路径

计划新增：

- `data/config/datasets/index.json`
- `data/config/datasets/ti15-ewc-2026.json`
- `data/config/match-sources/ewc-2026-opendota.json`
- `data/rosters/ti15-2026.json`
- `scripts/fantasy/dataset_config.py`
- `scripts/fantasy/rulesets.py`
- 对应配置加载和校验测试

计划修改：

- `scripts/fetch-ewc.py`
- `scripts/fantasy/scoring.py`
- `scripts/fantasy/rankings.py`
- `scripts/fantasy/role_rankings.py`
- 相关 `scripts/fantasy/test_*.py`

约束：

- 默认 dataset 仍是 TI15-EWC；
- 仍读取当前 EWC 缓存；
- 仍使用当前 `RULES`，仅通过 `ti15-base-v1` 进行版本选择；
- Ruleset 选择层只负责让多个 dataset 引用同一套当前 TI15 规则，不修改、复制或重新解释任何 scoring constants；
- 仍写入当前旧文件路径；
- 不修改 `src/App.tsx`、翻译或前端数据加载；
- 不修改 `scripts/process-data.py`。

### 第 3 步：增加命名空间输出和兼容发布

正式产物写入：

- `data/generated/datasets/ti15-ewc-2026/`
- `public/data/datasets/ti15-ewc-2026/`
- `reports/ti15-ewc-2026/`

当前旧产物继续作为 TI15-EWC 兼容副本保留：

- `public/data/fantasy-match-scores.json`
- `data/processed/player-fantasy-rankings.json`
- `data/processed/role-fantasy-rankings.json`
- 根目录的三个验证报告

只有在新旧语义比较完全通过后，才以原子方式更新旧兼容文件。比较失败时不得覆盖旧产物。

通用命名空间中的个人排名只使用 `source.rosterPlayers`。TI15-EWC 的旧个人排名兼容副本在发布边界显式转换为 `source.ti15Players`，不会让通用 schema 长期同时保留两个字段。语义比较先执行这项白名单 schema 转换，再比较所有业务字段，因此字段兼容迁移不会被误报，数值、选手集合或结构中的其他变化仍会阻止发布。

各 dataset 的 validation profile 继续使用严格的精确期望值。`playersWithoutGames` 是 dataset-specific 计数并允许配置为 `0`；TI15-EWC 仍精确要求为 `6`，其他规模字段仍要求为正整数。

前端在这一阶段仍从原路径加载数据，因此默认展示和现有功能不变。

## 10. TI15-EWC 重构等价性证明

重构必须通过以下六层验证：

1. 记录现有三个 Fantasy 输出的规范化 SHA-256。
2. 对重构前后规范化 JSON 做完整结构比较，并报告第一个差异路径。
3. 单场数据逐项精确比较：
   - 157 个 match；
   - 1,570 个玩家比赛行；
   - 每个 raw value、availability、Fantasy score 和异常记录。
4. 玩家排名逐项精确比较：
   - 80 名 TI15 选手；
   - 74 人有比赛、6 人无比赛；
   - 每项 Best、Average、`validGames` 和 `matchId`。
5. Role 结果逐项精确比较：
   - 16 支队伍；
   - 48 个 Role Units；
   - 成员、共同比赛数、指标结果和 null 传播。
6. 运行现有 Python 单元测试、三个完整验证模块和前端 production build。

任何数值、选手集合、比赛集合、顺序、Role 成员或 availability 差异都视为失败。

## 11. 当前阶段明确不做的事项

- 不获取 TI14 数据。
- 不创建 TI14 roster。
- 不获取未来 TI15 正赛数据。
- 不修改前端数据集切换。
- 不改变 TI15-EWC 默认展示。
- 不改变 Fantasy scoring rules。
- 不改变当前已经验证的 TI15 Fantasy scoring constants。
- 不研究或引入 TI14 历史 Fantasy 官方规则。
- 不实现 TI14/TI15 参赛选手交集筛选。
- 不泛化当前未被 Fantasy 排行榜使用的旧 `scripts/process-data.py` 管线。

## 12. 后续需要确认的事项

以下事项不阻塞当前第 1～3 步，但新增 TI14 前需要确认：

1. “TI14 全部参赛选手”是否包含官方替补、临时 stand-in 和比赛期间换人。
2. 某队存在超过五名参赛选手时，哪五名用于固定 Role Unit；其余参赛选手仍进入个人排名。
3. TI14 match source 是否覆盖全部阶段，以及重赛、弃权、无效局的排除规则。
4. 长期 dataset ID 是否确定为 `ti14`、`ti15-ewc-2026` 和 `ti15`。发布后的内部 ID 应保持稳定。
5. 旧兼容输出建议至少保留到前端多数据集切换稳定一个发布周期后再考虑移除。
