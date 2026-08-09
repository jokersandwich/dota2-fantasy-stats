# Frontend Multi-Dataset Switch Plan

> 状态：实施方案草稿，尚未修改前端代码。
> 目标：在保持 `ti15-ewc-2026` 为默认 dataset 的前提下，让用户在 EWC 2026 与 TI14 之间切换，并为未来 `ti15` 预留扩展能力。

## 1. 当前前端数据加载方式

当前前端在 `src/App.tsx` 顶层静态导入：

```ts
import roleRankingsData from '../data/processed/role-fantasy-rankings.json'
```

该文件是 TI15-EWC 的旧兼容产物。导入后，数据被转换为模块级常量：

```ts
const payload = roleRankingsData as unknown as RoleRankingsPayload
```

因此当前实现具有以下特点：

- 只能展示单一 dataset；
- 没有 dataset selection state；
- 没有异步 dataset loader；
- 没有 payload cache；
- 没有 dataset 加载失败处理；
- Role filter、Best/Average 和排序都直接读取固定的 `payload` 常量。

当前前端相关 state 都位于 `App` 内：

- `roleFilter`；
- `performanceMode`；
- `sortKey`；
- `sortDirection`；
- `tableScrollEdges`；
- 语言状态由 `useLanguage` 管理。

## 2. Dataset registry 与公开输出现状

现有 canonical dataset registry：

```text
data/config/datasets/index.json
```

当前内容：

```json
{
  "schemaVersion": 1,
  "defaultDatasetId": "ti15-ewc-2026",
  "datasets": [
    "ti15-ewc-2026",
    "ti14"
  ]
}
```

默认 dataset 已正确保持为：

```text
ti15-ewc-2026
```

### 2.1 EWC 公开输出

```text
public/data/datasets/ti15-ewc-2026/role-fantasy-rankings.json
```

### 2.2 TI14 输出

已验证的 namespaced generated output：

```text
data/generated/datasets/ti14/role-fantasy-rankings.json
```

TI14 当前尚未建立 public 副本：

```text
public/data/datasets/ti14/role-fantasy-rankings.json
```

前端实施开始前，应使用现有 dataset publisher 发布 TI14。该操作只新增 TI14 public Role JSON，不更新 TI15-EWC legacy outputs，也不修改任何 generated artifact。

### 2.3 Payload schema 兼容性

TI15-EWC 与 TI14 的 Role ranking payload 已核验为相同 schema：

- 顶层字段一致；
- `source` 字段一致；
- 均有 48 个 Role Units；
- 均有相同的 18 个 Fantasy metrics；
- 均使用 `ti15-base-v1`；
- Core / Mid / Support aggregation 语义一致。

因此前端不需要为 TI14 创建独立表格或独立计算逻辑。

## 3. Registry 驱动的切换设计

继续使用现有 `data/config/datasets/index.json` 作为以下信息的唯一来源：

- 可用 dataset IDs；
- dataset 排列顺序；
- 默认 dataset ID。

新增前端 dataset registry/loader 模块，例如：

```text
src/data/datasets.ts
```

该模块负责：

1. 导入 canonical dataset registry；
2. 暴露 `defaultDatasetId`；
3. 按 registry 顺序生成可用 dataset 列表；
4. 按统一约定生成 Role ranking URL；
5. 对运行时加载的 JSON 做最低限度 contract validation。

公开路径统一约定为：

```text
data/datasets/<datasetId>/role-fantasy-rankings.json
```

实际请求 URL 使用 `import.meta.env.BASE_URL` 拼接，避免未来部署在非根路径时失效。

Dataset 显示名称放在现有中英文翻译系统中：

```text
ti15-ewc-2026 → EWC 2026
ti14           → TI14
```

如果未来 registry 增加 `ti15`：

1. 发布对应 public Role JSON；
2. 在翻译表补充显示名称；
3. UI 会自动根据 registry 生成新选项，不需要新增第三个硬编码按钮。

如果 dataset 暂时没有显示名称，则回退显示其 dataset ID，避免 registry 新增项直接破坏页面。

## 4. Dataset loader 与失败隔离

建议把 dataset 加载逻辑从 `App` 主体中分离，例如：

```text
src/hooks/useDataset.ts
```

Loader 管理：

- `activeDatasetId`；
- `payload`；
- `pendingDatasetId`；
- `loadError`；
- 已加载 payload cache；
- 快速切换时的 request race protection。

### 4.1 默认 EWC fallback

当前 TI15-EWC 兼容 payload 继续作为构建时内置 fallback。

这保证：

- 首次打开仍立即展示 EWC；
- EWC 不依赖运行时网络请求才能显示；
- TI14 JSON 加载失败时不会清空或破坏 EWC 表格；
- 默认用户可见行为保持不变。

### 4.2 切换流程

用户选择另一个 dataset 时：

1. 设置 `pendingDatasetId`；
2. 保留当前 active payload 和表格；
3. 如果目标已在 cache，直接使用缓存；
4. 否则请求目标 public Role JSON；
5. 对 payload 做最低限度结构检查；
6. 只有加载与检查全部成功后，才更新 `activeDatasetId` 和 `payload`；
7. 加载失败时保持原 dataset 为 active，并显示本地化错误；
8. 用户可以重新点击目标 dataset 重试。

最低限度 payload validation 包括：

- `schemaVersion` 合法；
- `datasetId` 等于请求的 dataset ID；
- `source` 是对象；
- `source.matchesProcessed` 是有效数字；
- `roleUnits` 是数组；
- Role Unit 数量和字段结构可以被现有表格消费；
- JSON 中不存在无效数值。

前端只验证预计算 payload 的形状和身份，不重新计算 Fantasy score 或 Role aggregation。

### 4.3 请求竞态

快速连续点击多个 dataset 时，需要使用以下任一种方式防止旧请求覆盖新状态：

- `AbortController`；或
- 单调递增的 request token。

只有最后一次仍有效的请求可以更新 active dataset。

## 5. UI 位置与视觉方案

Dataset 是整个页面的数据上下文，不只是表格筛选条件。因此建议在现有 site header 下方、hero 上方增加一条全局 dataset bar：

```text
┌ Brand                                      Language ┐
├ DATASET   [ EWC 2026 ] [ TI14 ]                       ┤
├ Hero / selected dataset description                  ┤
├ Role filter                         Best / Average    ┤
└ Rankings table                                       ┘
```

不建议把 dataset selector 与 Role filter 混在同一个语义分组，因为：

- Dataset 会改变整个页面；
- Role filter 只影响当前 dataset 的表格行；
- Dataset 还会改变 hero、比赛数、联赛 ID、说明文字和 footer。

### 5.1 视觉约束

新控件沿用现有界面：

- 深色背景；
- 细边框；
- 现有红色 accent 表示 active dataset；
- 复用当前 display/data 字体；
- 不新增大面积视觉装饰；
- 不改变现有 hero、表格或高密度数据布局；
- 保持清晰的 hover、active 和 keyboard focus 状态。

Dataset 按钮由 registry 循环生成，不针对 EWC/TI14 编写两个固定按钮。

移动端使用单行横向滚动或可滚动 segmented control，不让 dataset 按钮挤压语言切换或页面标题。未来计划中的第三个 `ti15` 可以直接容纳。

### 5.2 Loading 与错误状态

加载过程中：

- 当前表格继续显示；
- 目标 dataset 按钮显示 loading 状态；
- selector 使用 `aria-busy`；
- 不把表格替换成空白 loading 页面。

加载失败时：

- active dataset 不变化；
- 当前数据不变化；
- 在 dataset bar 下方显示简短本地化错误；
- 错误明确指出哪个 dataset 加载失败；
- 提供重试方式；
- 不使用全页弹窗。

## 6. Dataset 切换时的 state 策略

### 6.1 保留的 state

成功切换 dataset 后保留：

- 中文 / 英文；
- Best / Average；
- Role filter；
- 当前排序字段；
- 当前排序方向。

理由：

- 这些都是 dataset-independent UI preference；
- TI14 与 TI15-EWC schema 相同；
- 保留条件可以让用户直接比较两个赛事中的相同 Role 和 metric。

### 6.2 重置的 state

建议在成功切换后重置：

- 表格横向滚动位置回到最左侧；
- `pendingDatasetId`；
- 之前的 dataset load error；
- table scroll edge detection。

如果未来某个 dataset 不包含当前排序 metric，则回退为：

```text
sortKey = gpm
sortDirection = desc
```

当前 EWC/TI14 metric schema 一致，因此本阶段不会触发该回退。

## 7. Dataset-aware 页面文案

当前以下文案写死为 TI15/EWC：

- document title；
- meta description；
- brand 下方的 OpenDota league；
- hero subtitle；
- hero description；
- average summary；
- footer title；
- footer league ID。

这些文案需要改为根据 active dataset 和当前语言组合生成。

建议保留统一产品主题：

```text
TI15 Fantasy rules
```

同时明确当前被评价的赛事：

```text
EWC 2026
TI14
```

中文说明示例：

```text
统一使用 TI15 梦幻挑战规则评估 TI14 参赛选手的比赛表现。
```

英文说明示例：

```text
TI14 player performance evaluated with the shared TI15 Fantasy ruleset.
```

Document title 和 meta description 同样需要随语言与 dataset 更新。

## 8. URL 与 localStorage 建议

推荐采用 URL query：

```text
?dataset=ti14
```

暂不建议使用 localStorage 保存 dataset selection。

### 8.1 URL query 的优点

- 页面链接可分享；
- 浏览器前进/后退可以恢复 dataset；
- 无 query 时明确回到默认 EWC；
- 无效 dataset ID 可以安全回退到 EWC；
- 不会因为上一次访问记录而静默改变默认展示；
- 以后做跨赛事对比或深链接更容易扩展。

### 8.2 localStorage 的风险

- 用户再次访问时可能直接进入 TI14；
- 容易让“默认 dataset 是 EWC”变得不直观；
- 分享链接不能表达当前 dataset；
- 需要额外定义 URL 与 localStorage 冲突时的优先级。

建议第一版使用：

```text
URL query only
no dataset localStorage
```

在用户明确确认前，不实施 URL 或 localStorage 持久化。

## 9. 预计修改文件

### 9.1 前端代码

- `src/App.tsx`
  - 将固定模块级 `payload` 改为 active dataset payload；
  - 渲染 registry-driven selector；
  - 让 hero、stats、table 和 footer 使用 active payload；
  - 保留现有筛选、排序和 Role 表格逻辑。

- `src/data/datasets.ts`（新增）
  - 加载 canonical registry；
  - 生成公开 URL；
  - 定义 dataset descriptor；
  - 执行 payload contract validation。

- `src/hooks/useDataset.ts`（可新增）
  - 管理异步加载、cache、fallback、错误和竞态。

- `src/i18n/translations.ts`
  - dataset 显示名称；
  - selector label；
  - dataset-aware hero/footer 文案；
  - loading、失败与 retry 文案。

- `src/i18n/useLanguage.ts`
  - 让 document title 和 meta description 能结合 active dataset；或把 metadata 更新职责移到独立 hook。

- `src/styles.css`
  - dataset bar；
  - active/loading/error/focus 状态；
  - 移动端布局。

### 9.2 Public artifact

- `public/data/datasets/ti14/role-fantasy-rankings.json`（新增）

### 9.3 自动化测试

如果引入 Vitest / React Testing Library：

- `package.json`；
- `pnpm-lock.yaml`；
- test setup；
- dataset registry/loader tests；
- dataset switch component tests。

### 9.4 明确不修改

- `scripts/fantasy/rules.py`；
- Fantasy scoring constants；
- Python scoring/rankings/role aggregation；
- TI14 roster；
- TI15 roster；
- TI14 generated outputs；
- TI15-EWC generated outputs；
- Core / Mid / Support aggregation；
- TI15-EWC legacy compatibility outputs。

## 10. 测试方案

### 10.1 Registry 与数据契约

- default dataset 必须仍为 `ti15-ewc-2026`；
- selector 顺序必须来自 registry；
- registry ID 必须唯一；
- 每个 registry entry 必须能生成合法 public URL；
- payload `datasetId` 必须匹配请求的 ID；
- 无效 payload 必须被拒绝且不能覆盖 active data。

### 10.2 默认 EWC

- 首次进入显示 EWC 2026；
- 157 matches；
- 48 Role Units；
- 默认 Average；
- 默认排序保持现状；
- 当前 Role filter、语言和表格行为保持不变。

### 10.3 TI14 切换

- TI14 加载成功后 active selector 更新；
- 144 matches；
- 48 Role Units；
- 表格数据来自 TI14 payload；
- hero、league ID、footer 和说明文字同步变化。

### 10.4 State 保持

切换前设置：

- Best；
- Support；
- First Blood 排序；
- English。

切换 TI14 后以上状态应保持，且排序使用 TI14 的预计算 First Blood Fantasy score。

### 10.5 失败隔离

- 模拟 TI14 404；
- 模拟 JSON parse error；
- 模拟 payload datasetId 不匹配；
- 模拟快速点击 EWC → TI14 → EWC；
- 所有失败场景均必须保留 EWC 默认数据；
- 失败后可重试 TI14。

### 10.6 构建与回归

```powershell
pnpm run typecheck
pnpm run build
python -B -m unittest discover -s scripts/fantasy -p "test_*.py"
```

还需要浏览器验收：

- 桌面宽屏；
- 1100px 左右中等宽度；
- 680px 以下移动端；
- 中文 / 英文；
- 键盘操作和 focus 样式；
- reduced motion；
- 数据表 sticky columns 与横向滚动；
- dataset loading/error 状态。

## 11. 推荐实施顺序

1. 发布 TI14 public Role JSON，并确认不会更新任何 legacy output；
2. 新增 dataset registry/loader 与 payload validation；
3. 用内置 EWC payload 建立 default fallback；
4. 将 `App` 的模块级固定 payload 改为 state payload；
5. 接入 registry-driven selector；
6. 更新 dataset-aware 中英文文案与 metadata；
7. 加入 loading/error/race protection；
8. 添加样式和移动端行为；
9. 添加自动化测试；
10. 运行 typecheck、build、Python regression tests 和浏览器验收；
11. 确认 EWC 默认用户可见行为没有回归后停止。

## 12. 待确认事项

实施前只需要确认 dataset selection 的持久化方式：

> 是否采用推荐的“URL query（例如 `?dataset=ti14`），不使用 localStorage”方案？

在得到确认前，不实现 URL 或 localStorage 持久化。
