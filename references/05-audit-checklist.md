# 05 - 对抗式合规审计清单 (Audit Checklist)

本清单用于在 PR 合入主干、执行发版归档或例行质量自检时，由 AI Agent 或 Reviewer 执行确定性核对。

---

## 一、机械硬判检查项 (100% 确定性)

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
- [ ] **断言**：关联的提交必须真实存在于 Git 历史中，且必须是主干的祖先提交（防止伪造假 Commit Hash）。

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
| **0** | **未发现合规缺陷** | 允许合入主干或继续执行发版封箱 |
| **4** | **存在确定性治理违规** | **强制阻断**：如存在残留 todo、伪造 Commit、证据锚缺失，必须先修复再重跑 |
| **6** | **证据不充分或结论存疑** | 降级为参考意见，在回复中完整列出事实，由人工核对后决策 |
