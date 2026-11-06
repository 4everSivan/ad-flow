# 07 - 发版与阶段封箱归档 SOP (Release Archiving)

本 SOP 规范项目在打出版本 Git Tag（如 `v0.1.0`）或阶段里程碑收口时，如何安全平移卡片、冻结批次总账，并保证**设计方案基线 0 破坏、0 断链**。

---

## 一、归档触发条件

1. 当前版本内的所有变更卡（`Cxxx.json`）均已处于 `status: "closed"` 状态；
2. 当前阶段内的所有任务卡（`Txx.json`）均已处于 `status: "completed"` 状态；
3. 全量测试通过；Git Tag（如 `git tag -a v0.1.0 -m "Release v0.1.0"`）最后打：归档移动、总账更新与 CHANGELOG 定稿提交且复核校验 Exit 0 之后，在该提交上打 Tag，顺序见 `AGENTS.md` 发版与归档门禁；
4. `todo/future.md` 与 `now.md` 已完成例行评审。
5. **归档前置批次预检**：运行 `scripts/adflow-verify --release <version>` 取得 Exit 0。普通校验的 Exit 0 **不证明**批次终态（非终态活跃卡没有状态前置要求）；批次预检在普通校验之上逐卡核对 `version` 属于本批次的活跃卡：未达终态报 `RELEASE_NOT_TERMINAL`（Exit 4），未填 `version` 的未收口卡报 `RELEASE_SCOPE_UNKNOWN`（Exit 6，先划定批次）；批次早于本次发布、仍滞留活跃区的终态卡以 `RELEASE_STRANDED`（ADVISORY）提示，由人工决定是否随本批次归档。发布范围是否完整仍由人工确认。Exit 4 禁止归档。

---

## 二、归档执行四步法

```
【第 1 步】创建归档目录: docs/archive/<version>/{change,task}
     ↓
【第 2 步】物理迁移卡片: 将 closed 变更卡 / completed 任务卡移入归档目录
     ↓
【第 3 步】冻结批次总账: 新建 <version>/index.json，移出现行总账登记，定稿 CHANGELOG
     ↓
【第 4 步】复核并打 Tag: 设计文档零修改，复核 Exit 0 后提交，在该提交上打 Tag
```

### 第一步：建立版本归档箱
在目标项目中执行创建：
```bash
mkdir -p docs/archive/<version>/change
mkdir -p docs/archive/<version>/task
```

### 第二步：物理移动已闭环卡片
将 `docs/devel/change/` 下已收口至本版本的卡片移动到 `docs/archive/<version>/change/`：
```bash
mv docs/devel/change/C001.json docs/archive/<version>/change/
# ... 对本版本内全部闭环卡片执行移动
```

### 第三步：冻结批次总账并移出现行登记
新建 `docs/archive/<version>/index.json`，把本批次卡片的登记条目原样移入，`file` 改为归档路径，并带上各卡的主题归属（格式见 [04 索引路由](04-index-routing.md)）：
```json
{
  "$schema": "adflow-archive-batch-v1",
  "release": "v0.1.0",
  "archived_at": "2026-09-30",
  "cards": {
    "C001": {
      "title": "修复日K引导缺code",
      "status": "closed",
      "version": "v0.1.0",
      "file": "docs/archive/v0.1.0/change/C001.json"
    }
  },
  "tasks": {},
  "topics": { "MarketService": { "changes": ["C001"] } }
}
```
随后从现行 `change/index.json` 与 `task/index.json` 删除这些登记及 `topics[*].changes` / `.tasks` 中的对应卡号，保留 `topics[*].design_doc`。现行总账因此每次发版都会变小，冻结路由只写这一次。

同一步定稿 CHANGELOG：将 `## [Unreleased]` 改为 `## [<version>] - <发布日期>` 并在其上新建空的 `## [Unreleased]`；本批次卡片链接改指归档路径。项目使用 `sync.tag` 时，为本批次 C 卡填写即将打出的 Tag 名——这是归档卡唯一允许写入的字段，与归档移动在同一提交中完成。

任务卡同样移动至 `docs/archive/<version>/task/`，登记写入同一份批次总账的 `tasks`。后续任务据批次总账只读解析已完成依赖，校验器核对文件存在、卡号及状态一致；卡号不复用，新卡号以 `scripts/adflow-verify --next-id` 覆盖全部批次计算。归档卡不按当前业务规则重验或回写 `gate`。旧项目在现行总账中保留归档登记仍有效，瘦身按归档 README「现行总账瘦身」由人工授权执行。

### 第四步：设计文档零破坏（Zero Diff）并打 Tag
由于设计文档只声明 `<!-- @topic: MarketService -->` 与指向 `change/index.json#MarketService` 的总账入口，**设计文档正文中的任何字符都不需要改动**！
Git Diff 在设计方案上为 0，彻底根除了历史断链的隐患。

复核 `scripts/adflow-verify` 再次 Exit 0 后，提交归档移动、总账与 CHANGELOG 变更，在发布已获授权时于该提交上打 Tag；推送另需授权。不得先打 Tag 再补归档或 CHANGELOG，否则 Tag 指向的提交与发布记录不一致。

---

## 三、发版归档验收清单

- [ ] `docs/devel/change/` 下仅保留尚未发版的活跃卡片（甚至为空）；
- [ ] `docs/archive/<version>/` 下完整包含了本次发版的所有卡片与测试快照；
- [ ] 归档区（本批次及历史批次）无非终态卡：移动与总账更新后再次运行 `scripts/adflow-verify` 且 Exit 0；非 `closed`/`completed` 卡在归档区会被判 `ARCHIVE_NON_TERMINAL` 确定性违规（总账与批次总账路由、归档目录物理扫描双覆盖，未登记的归档卡另报 `ARCHIVE_UNREGISTERED` 提示补登）。历史批次的存量冻结卡不改写状态，按归档 README「历史批次账实修复」流程人工处置；
- [ ] 本批次已写入 `docs/archive/<version>/index.json`，现行总账不再含本批次登记；以 `scripts/adflow-verify --topic <主题>` 从任意设计文档小节跟随 Topic 查卡，路径 100% 正确命中；
- [ ] `CHANGELOG.md` 已有 `[<version>] - <发布日期>` 条目与新的空 `[Unreleased]`，本批次卡片链接指向归档路径；Tag 指向包含上述变更的提交；
- [ ] 自动化测试与 CI 门禁跑通退出码 0；
- [ ] 所有构建与打包分发产物（如 dist / jar / binary）严格输出或归拢至 `local/`（如 `local/dist/`），严禁将打包成果物散落提交至 Git 源码树。
