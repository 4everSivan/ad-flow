# 05 - 对抗式合规审计清单 (Audit Checklist)

本清单用于在 PR 合入主干、执行发版归档或例行质量自检时，由 AI Agent 或 Reviewer 执行确定性核对。

> **可执行化**：本清单的部分结构条件已由 `scripts/adflow-verify` 落地为状态感知门禁（设计挂接非 README + `@topic`、证据锚、commit 祖先、零沉淀、索引对齐、二值契约对称、依赖存在及完成前提、版本一致等），退出码 0/4/6 与本表一致。收口/合入/归档前按 SOP 运行可发现已覆盖项；本清单保留供对抗式证伪与 Exit 6 存疑项的人工研判。

---

## 一、结构检查与人工核对项

### 1. 零沉淀违规检查 (Zero Sediment)
- [ ] 检查 `docs/devel/todo/now.md` 与 `future.md`；
- [ ] 比对当前活跃的 C 卡与 T 卡所描述的现象/需求；
- [ ] **断言**：todo 表格中不得残留任何已建卡或已立项的事项行（命中即判定违规阻断）。

### 2. 脱钩物理文件检查 (Decoupled Scope)
- [ ] 检查所有活跃 `Cxxx.json` 与 `Txx.json`；
- [ ] **断言**：卡片内部不得硬编码具体的源码文件物理路径（如 `files: ["backend/app/..."]`），必须且仅能声明 `module`、`component`、`capability`；
- [ ] 物理变动必须通过关联的 `commit` 追溯。

### 3. Git 提交祖先真实性检查 (Commit Ancestor)
- [ ] 检查已标记为 `closed` 的变更卡中的 `sync.commit`；
- [ ] 执行 `git merge-base --is-ancestor <commit> HEAD`；
- [ ] **断言**：关联的提交必须真实存在于 Git 历史中，且必须是当前 HEAD 的祖先提交（是否已进入主干需另行核对）（防止伪造假 Commit Hash）。

### 4. 证据锚有效性检查 (Evidence Anchors)
- [ ] 检查卡片 `verification.run_id` 与 `user_quote`；
- [ ] **断言**：
  - `run_id` 必须为非空安全流水号（如纯数字或 `local-` 前缀），严禁包含内网 URL；
  - `user_quote` 必须为非空人类会话原话引用，严禁由 AI 仅写“已确认”。

### 5. 中枢总账双向对齐检查 (Index Alignment)
- [ ] 检查 `docs/devel/change/index.json` 中的 `cards` 状态与物理文件一致性；
- [ ] 检查卡片声明的 `target.design_topic` 是否在对应设计文档中真实存在 `<!-- @topic -->`；
- [ ] 检查 `CHANGELOG.md` 顶部是否存在对应卡片的双向超链接。

### 6. 设计文档有效性与严禁关联 README (INV_NO_README_AS_DESIGN_DOC)
- [ ] 检查所有活跃与历史卡片（`Cxxx.json` / `Txx.json`）中的 `target.design_doc` 与 `design.doc`，以及 `index.json` 中 `topics[].design_doc`；
- [ ] **断言**：
  - `design_doc` **绝对严禁指向任何 `README.md`**（包括 `docs/devel/design/README.md`，违规直接判定为 Exit Code 4 阻断）；
  - 必须指向现行基线具体设计文档（`00-系统总体设计.md` 或 `01~99-[模块名].md`）；
  - 目标设计文档内部必须真实存在与 `target.design_topic` 完全吻合的 `<!-- @topic: TopicName -->` 锚标。

---

## 二、对抗性证伪与反向核验 (Adversarial Verification)

Reviewer Agent 必须站在“尝试证伪（Falsify）”的立场审视改动：

1. **Bug 是否真修好？**
   - 检查 `verification.checks` 中是否包含了针对核心根因的实测证据，还是仅仅跑了无关单测；
2. **反向影响面是否漏评？**
   - 检查本次代码改动是否隐含波及了未在 `impact` 声明的模块（如行情修改波及撮合滑点）；
3. **条件契约是否对称严密？**
   - 检查 `true_if` 与 `false_if` 是否互斥且完整，是否存在既非 True 也非 False 的死角。

---

## 三、退出状态判定 (Audit Exit Codes)

| 状态码 | 判定语义 | 处理指令 |
|---|---|---|
| **0** | **未发现已覆盖的基线门禁问题** | 仍需满足业务验收和操作授权；单独报告 ADVISORY |
| **4** | **存在确定性治理违规** | **强制阻断**：如存在残留 todo、伪造 Commit、证据锚缺失，必须先修复再重跑 |
| **6** | **证据不充分或结论存疑** | 降级为参考意见，在回复中完整列出事实，由人工核对后决策 |


## 四、版本兼容与校验边界

- v1.2.0 新增缺失主题、依赖环路、终态验收项未全为 true 的 `ADVISORY` 旁路诊断；不改变退出码，不追溯迁移旧卡。既有 ERROR/WARN 的 4/6 判定保留。
- `--card <卡号> --to <目标状态>` 在内存检查目标状态，`--record` 仅回写指定卡的 gate，不修改卡片或索引状态。全局违规也会计入记录结果；Exit 0 后同步状态，再运行普通检查。
- 不带 `--card` 的旧 `--record` 仍回写全部活跃卡；规范升级不执行它。`--warn-only` 仅用于观察，不能与 `--record` 合用，也不能作为正式通过证据。
- 校验器检查非空、格式和部分关系，不能证明人类原话真实性、验收条件语义互斥完整、应用实测正确，或所有历史归档卡都已审计。审查者另行核对来源和覆盖范围。
- 修复限定在授权范围内，最多 3 轮；相同阻断连续两次或依赖缺失授权/事实时停止相关操作并报告。性能收益需要实测，不作固定比例承诺。
