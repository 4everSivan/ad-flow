# 02 - 变更流标准操作规程 (Change SOP)

本 SOP 规范日常缺陷修复（BugFix）、功能回调（Rollback）、参数调整（Param）与代码重构（Refactor）的端到端执行流程。

---

## 阶段一：发现与建卡 (Card Creation)

1. **登记与零沉淀移出**：
   - 发现问题时，若已在 `docs/devel/todo/now.md` 登记，读取该行信息，并在建卡后**立即将该行物理删除**；
2. **分配全局卡号**：
   - 读取 `docs/devel/change/index.json`，获取已存在的最大卡号并 +1（如 `C027`）；
   - 卡号全局递增，跨版本不重置。
3. **实例化变更卡**：
   - 复制 `templates/docs/change/change-card.json.tpl` 至 `docs/devel/change/Cxxx.json`；
   - 填写 `branch: "fix/Cxxx-[desc]"`（指定多分支开发的执行分支标签）；
   - 填写 `target.module`、`target.component`、`target.design_doc` 与 `target.design_topic`（★ **绝对红线**：`design_doc` 必须指向 `00-系统总体设计.md` 或 `01~99-[模块].md`，严禁指向任何 `README.md`！若缺少对应设计，必须遵循“文档先行”先补齐设计正文）；
   - 填写 `why`（现象、根因、危害）与 `changes`（`before / after / impact`）；
   - 填写 `precheck`（缺陷复现嗅探命令）与 `callback`（`before / after` 脚本）；
   - **事前定义验收契约**：在 `verification.checks` 预先写好各核验项的 `true_if` 和 `false_if`。此时 `evidence` 置空，`result: null`；
4. **总账预占登记**：
   - 在 `docs/devel/change/index.json` 的 `cards` 增加本卡条目（包含 `branch` 映射），状态记为 `"draft"` 或 `"pending"`。

---

## 阶段二：预检、回调与实现 (Precheck, Callback & Implementation)

1. **执行预检 (Precheck)**：
   - 执行 `precheck.command`，嗅探当前缺陷是否已被前序提交意外修复；若已修复，回填 `is_completed: true` 并直接进入阶段三核验收口；
2. **执行前置回调 (`callback.before`)**：
   - 自动按序运行声明的准备命令（如分支检出、数据清理、环境快照）；
3. **实现代码修复与补测**：
   - 遵循最小修改原则，修复问题并补充针对性的自动化回归用例；
4. **执行后置回调 (`callback.after`)**：
   - 自动按序运行声明的收尾命令（如代码格式化、质量静态扫描、构建检查）；
5. **执行测试套件**：
   - 运行全量测试，检查退出码与通过用例数。

---

## 阶段三：证据采集与人机代签 (Verification & Signoff)

1. **填充事实证据**：
   - 采集真实测试输出与统计，填入 `verification.checks[].evidence`；
   - 比对预先定义的条件：
     - 若事实吻合 `true_if` $\rightarrow$ 设置 `result: true`；
     - 若命中 `false_if` $\rightarrow$ 设置 `result: false`，并在会话中向人类警示，转入异常流；
2. **记录脱敏流水号**：
   - 获取测试流水号（如 `$GITHUB_RUN_ID` 纯数字或本地运行时间戳 `local-YYYYMMDD-HH`），填入 `verification.run_id`；
3. **人机对齐汇报**：
   - AI 在会话中向人类呈报测试事实、修改前后逻辑与关键验证现象；
4. **人类口头确认与 AI 代签**：
   - 人类在会话中明确回复同意后，AI 摘录人类发言原话填入 `verification.user_quote`；
   - 填写 `signoff`（格式：`用户名 (AI代签)`）；
   - 卡片状态由 `pending` 转为 `verified`。

---

## 阶段四：合入主干与双向闭环 (Merge & Closure)

1. **合入主干**：
   - 提交代码并推送主干，获取 Git Commit Hash（如 `14d108e`）；
2. **设计方案回写**：
   - 若 `design.modified == true`，将 `design.rule_diff.after` 的新规则同步更新至设计文档正文对应小节；
3. **更新 CHANGELOG**：
   - 在 `CHANGELOG.md` 顶部按 semver 追加条目，并附带与本卡互链的 Markdown 链接；
4. **更新索引总账与关闭卡片**：
   - 在 `change/index.json` 中：
     - 将 `cards[Cxxx].status` 更新为 `"closed"`；
     - 记录 `commit` 与当前目标版本 `version`；
     - 将卡号追加到对应 `topics[topic].changes` 列表中；
   - 在 `Cxxx.json` 中将 `sync` 各标志置为 `true`。
