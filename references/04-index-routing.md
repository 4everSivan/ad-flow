# 04 - 索引总账与路由规约 (Index Routing)

本规约定义中枢索引（`change/index.json` 与 `task/index.json`）的数据契约、Topic 命名规则与路由行为。

---

## 一、中枢解耦模型核心价值

传统的网状链接中，设计方案直接链接 C/T 卡。一旦卡片归档，所有链接瞬间变成死链。
`ad-flow` 采用中枢路由：

$$\text{执行卡片 (C/T)} \longleftrightarrow \text{索引总账 (index.json)} \longleftrightarrow \text{设计方案基线 (Design)}$$

- **设计方案**：仅声明概念主题 `<!-- @topic: TopicName -->` 与统一总账入口；
- **执行卡片**：以 `target.design_doc` 挂接具体设计正文，以 `target.design_topic: "TopicName"` 声明所属主题；源码影响范围使用领域能力描述；
- **现行总账**（`change/index.json`、`task/index.json`）：登记活跃卡的物理路径与状态，并保留主题与设计正文的对应关系；
- **归档批次总账**（`docs/archive/<version>/index.json`）：发版时随本批次冻结卡片路由与主题归属，此后不再改动。

**分层原则：可变的进现行总账，冻结的随批次冻结。** 归档卡不会再移动或改状态，其路由与批次一起冻结；现行总账只承载仍会变化的登记，规模取决于在研事项而非历史总量。归档时新建批次总账并删除现行登记，设计正文仍然零改动、零断链。

---

## 二、Topic 命名与声明契约

1. **命名规范**：
   - 必须采用**驼峰命名（PascalCase）**，且具有明确的业务领域语义；
   - 推荐模式：`[Domain][Service/Engine/Manager/Store]`，例如 `MarketService`、`MatchingEngine`、`AuthGuard`、`OrderLedger`；
   - 严禁使用文件物理后缀或临时序号作为 Topic。
2. **在设计方案中的声明方式**：
   在设计小节标题正下方必须紧随一行 HTML 隐式注释声明：
   ```markdown
   ### 2.2 行情服务 (MarketService)
   <!-- @topic: MarketService -->
   ```
   并提供统一指向总账的锚点：
   ```markdown
   > 📌 **变更总账**: 参见 [变更总账 (MarketService)](../change/index.json#MarketService)
   ```
3. **【绝对红线】设计文档指向约束 (INV_NO_README_AS_DESIGN_DOC)**：
   - 无论是卡片中的 `target.design_doc` / `design.doc`，还是中枢 `index.json` 中的 `topics[].design_doc`，**绝对严禁指向任何 `README.md`**（包括 `docs/devel/design/README.md`）；
   - `design_doc` 必须且仅能指向具体的现行设计基线文档（`00-系统总体设计.md` 或 `01~99-[模块名].md`）；
   - 若改动涉及系统拓扑或工程结构，应挂接在 `00-系统总体设计.md` 中对应的架构章节；若尚未编写对应设计，必须遵循“文档先行”，先补充设计正文并打上 `@topic` 锚标，再行挂接。

---

## 三、变更索引结构 (`change/index.json`) 规约

```json
{
  "$schema": "https://ad-flow.org/schemas/change-index.v1.json",
  "updated_at": "YYYY-MM-DD",
  "topics": {
    "MarketService": {
      "design_doc": "docs/devel/design/02-后端设计方案.md",
      "changes": ["C027"]
    }
  },
  "cards": {
    "C027": {
      "title": "修复夜盘时段数据污染",
      "type": "BugFix",
      "status": "pending",
      "topic": "MarketService",
      "version": "v0.2.0",
      "file": "docs/devel/change/C027.json"
    }
  }
}
```

任务总账同理：`tasks` 只登记活跃任务，`topics[TopicName].tasks` 只列活跃卡号；`milestones` 随阶段数增长、规模很小，保留在现行任务总账，成员清单可以包含已归档任务。

### 归档批次总账 (`docs/archive/<version>/index.json`)

发版归档时为本批次新建，两轨共用一份，归档后只读：

```json
{
  "$schema": "adflow-archive-batch-v1",
  "release": "v0.1.0",
  "archived_at": "2026-09-30",
  "cards": {
    "C001": {
      "title": "修复日K引导缺code",
      "type": "BugFix",
      "status": "closed",
      "topic": "MarketService",
      "version": "v0.1.0",
      "file": "docs/archive/v0.1.0/change/C001.json"
    }
  },
  "tasks": {},
  "topics": {
    "MarketService": { "changes": ["C001"] }
  }
}
```

### 路由字段语义：
- `topics[TopicName].design_doc`: 对应设计方案的仓库根基准路径；主题没有活跃卡时也保留，设计正文的总账链接因此始终可达；
- `topics[TopicName].changes` / `.tasks`: 本总账中仍活跃的关联卡号；归档时移入批次总账同名主题；
- `cards[CardID].file`: 活跃卡的精确物理路径 `docs/devel/change/Cxxx.json`；
- 批次总账 `cards` / `tasks`: 条目沿用现行总账字段，`file` 必须指向本批次对应轨道目录（如 `docs/archive/v0.1.0/change/C001.json`）；`topics` 记录本批次卡的主题归属，可一卡多主题；
- 校验器以 `$schema: adflow-archive-batch-v1` 识别批次总账，对其条目执行与现行总账相同的路由硬检查（路径、存在、身份、状态一致、归档终态），并据此判定撞号与跨版本依赖。未声明该 schema 的批次根文件（如项目自建快照）不按清单解析；
- **兼容旧布局**：现行总账中保留归档登记的旧项目继续有效，校验器只以聚合的 `LEDGER_ARCHIVED_ENTRIES` 旁路提示。规范同步不自动迁移，需要瘦身时按归档 README「现行总账瘦身」经人工授权执行。

---

## 四、Agent 路由算法

1. **从设计小节查找变更**：
   - 提取小节中的 `@topic: TopicName`；
   - 运行 `scripts/adflow-verify --topic TopicName`，一次列出现行总账与全部批次总账中该主题的卡号、状态、批次与路径（只读）；
   - 手工查询时读取现行总账 `topics[TopicName]` 与各 `docs/archive/<version>/index.json` 的 `topics[TopicName]`，依据条目 `file` 打开卡片。
2. **从变更卡回写设计方案**：
   - 读取卡片中的 `target.design_doc` 与 `target.design_topic`；
   - 打开该设计文档，查找包含 `<!-- @topic: TopicName -->` 的对应小节执行回写。
3. **分配新卡号**：
   - 运行 `scripts/adflow-verify --next-id change`（或 `task`），取现行总账、批次总账、活跃卡池与归档目录，以及本机其他工作树和本地/远端跟踪分支中已出现的最大卡号 +1，无需通读历史登记；最大号不在当前工作区时，`--json` 的 `next_id_basis` 与文本模式的 stderr 会说明出处；
   - 该结果不是原子预占，他人尚未推送的分支仍可能撞号；合入主干前在合并结果上运行校验（见 [06 异常流](06-exception-and-hotfix.md) 三），结合 `ID_DUPLICATE`、`LEDGER_DUPLICATE_KEY` 与 Git 冲突检查处理。

## 五、设计文档机器路由 (`docs/devel/index.json`)

设计文档的人类可读清单位于 `docs/devel/design/README.md` 的模块矩阵；机器路由位于 `docs/devel/index.json` 的 `design` 子系统：

```json
{
  "subsystems": [
    {
      "name": "design",
      "path": "docs/devel/design",
      "readme": "docs/devel/design/README.md",
      "designs": [
        {"file": "docs/devel/design/01-订单模块.md", "topic": "OrderService",
         "status": "baseline", "title": "订单模块"}
      ]
    }
  ]
}
```

- `file` 为项目根相对路径，`topic` 必须与正文中的 `<!-- @topic: TopicName -->` 一致；`status` 与正文元数据一致（`draft` / `baseline`）。
- 声明 `designs` 后，校验器以 `DESIGN_ROUTE_DRIFT`（ADVISORY）报告：设计文档未登记、条目指向不存在文件、条目缺少 `file`、`designs` 不是数组、或 `topic` 锚标未命中。它不改变退出码，也不阻断收口。
- **兼容旧布局**：没有 `designs` 键的项目保持只读兼容，初始化/升级不追溯补登记；新建或明确同步规范的项目按上述结构登记。

## 规范与模板入口

`docs/index.json.standards` 登记 `docs/standards/coding.json`、`task-template.json` 和 `change-template.json`。规范目录无需另建 README 或索引；真实 C/T 卡片及其当前总账仍在 `docs/devel/`。旧路径只用于兼容已有项目，明确同步后以顶层登记的入口为准。已有设计文件名及其关联保留，不因模板语言调整改写历史资料。
