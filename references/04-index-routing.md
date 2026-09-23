# 04 - 索引总账与路由规约 (Index Routing)

本规约定义中枢索引（`change/index.json` 与 `task/index.json`）的数据契约、Topic 命名规则与路由行为。

---

## 一、中枢解耦模型核心价值

传统的网状链接中，设计方案直接链接 C/T 卡。一旦卡片归档，所有链接瞬间变成死链。
`ad-flow` 采用中枢路由：

$$\text{执行卡片 (C/T)} \longleftrightarrow \text{索引总账 (index.json)} \longleftrightarrow \text{设计方案基线 (Design)}$$

- **设计方案**：仅声明概念主题 `<!-- @topic: TopicName -->` 与统一总账入口；
- **执行卡片**：仅声明所属主题 `target.topic: "TopicName"`；
- **索引总账**：唯一掌握每张卡当前的物理路径（是在 `devel/` 还是在 `archive/`）。

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

---

## 三、变更索引结构 (`change/index.json`) 规约

```json
{
  "$schema": "https://ad-flow.org/schemas/change-index.v1.json",
  "updated_at": "YYYY-MM-DD",
  "topics": {
    "MarketService": {
      "design_doc": "docs/devel/design/02-后端设计方案.md",
      "changes": ["C001", "C008", "C027"]
    }
  },
  "cards": {
    "C001": {
      "title": "修复日K引导缺code",
      "type": "BugFix",
      "status": "closed",
      "topic": "MarketService",
      "version": "v0.1.0",
      "file": "docs/archive/v0.1.0/change/C001.json"
    },
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

### 路由字段语义：
- `topics[TopicName].design_doc`: 对应设计方案的仓库根基准路径；
- `topics[TopicName].changes`: 关联的所有卡号有序数组；
- `cards[CardID].file`: 卡片的精确物理文件路径。归档前为 `docs/devel/change/Cxxx.json`，归档后更新为 `docs/archive/<version>/change/Cxxx.json`。

---

## 四、Agent 路由算法

1. **从设计小节查找变更**：
   - 提取小节中的 `@topic: TopicName`；
   - 读取 `change/index.json` 的 `topics[TopicName].changes`；
   - 依据 `cards[CardID].file` 直接定位到卡片文件打开。
2. **从变更卡回写设计方案**：
   - 读取卡片中的 `target.design_doc` 与 `target.design_topic`；
   - 打开该设计文档，查找包含 `<!-- @topic: TopicName -->` 的对应小节执行回写。
