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
- [ ] 检查 C 卡 `verification` 与 T 卡 `acceptance` 中的 `run_id`、`user_quote` 与 `signoff`；
- [ ] **断言**：
  - `run_id` 必须为非空安全流水号（如纯数字或 `local-` 前缀），严禁包含内网 URL；
  - `user_quote` 必须为非空人类会话原话引用，严禁由 AI 仅写“已确认”；
  - `rejected` 卡不得保留驳回前的确认原话，返工后的确认须为驳回之后的新原话（`SIGNOFF_STALE`）；
  - T 卡 `completed` 缺少确认原话或代签人报 `TASK_SIGNOFF_MISSING`（ADVISORY，旧卡不追溯阻断）。

### 5. 中枢总账双向对齐检查 (Index Alignment)
- [ ] 检查 C/T 两轨 `index.json` 登记的路径、卡号、状态与物理文件双向一致；归档路由仍须存在且身份/状态一致，依赖可引用归档卡；
- [ ] 检查卡片声明的 `target.design_topic` 是否在对应设计文档中真实存在 `<!-- @topic -->`；
- [ ] 检查 `CHANGELOG.md` 顶部是否存在对应卡片的双向超链接。

### 6. 设计文档有效性与严禁关联 README (INV_NO_README_AS_DESIGN_DOC)
- [ ] 检查活跃卡片（`Cxxx.json` / `Txx.json`）中的 `target.design_doc` 与 `design.doc`，以及 `index.json` 中 `topics[].design_doc`；历史卡按归档时适用规范另行抽查，不因升级追溯改写；
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


## 四、诊断目录、版本兼容与校验边界

- 诊断码目录以 `scripts/adflow-verify --list-checks [--json]` 为唯一权威来源：列出每个码的默认严重级别、一句话释义与修复提示，当前共 66 个（42 `ERROR` / 6 `WARN` / 18 `ADVISORY`），不依赖目标项目是否已初始化。本清单不再逐码复述，避免两处漂移。
- 每条 finding 带 `hint`：文本模式显示为「↳ 修复」，`--json` 中为同名字段；调用点可给出比注册表更具体的一条。`--json` 的 `summary.codes` 按码汇总本次最终 findings 的各严重级别条数（先应用 `--warn-only`），无发现时为 `{}`。提示指向根因处理或现有 SOP，不构成写入授权，也不替代人工取证与验收。
- `ADVISORY` 默认政策不变：新增诊断不改变退出码，不追溯迁移旧卡；`ARCHIVE_NON_TERMINAL` 仍是唯一记录在案的硬门禁例外（1.4.0 起，覆盖总账路由与归档目录中直接存放的卡片）。历史冻结非终态卡按归档 README「历史批次账实修复」由人工定口径处置，升级只报告不改写。`TOOL_VERSION_DRIFT` 仅在 `--mode init` 核对校验器副本与 `docs/index.json.adflow_version` 一致；旧布局的指南与模板路径继续只读兼容，升级不追溯迁移业务记录。
- 分层总账：归档批次总账 `docs/archive/<version>/index.json`（`adflow-archive-batch-v1`）的条目与现行总账适用同一组路由硬检查，参与撞号与依赖判定。现行总账仍登记归档卡时只报聚合的 `LEDGER_ARCHIVED_ENTRIES`（ADVISORY），旧布局不追溯阻断；`--release` 另以 `RELEASE_STRANDED`（ADVISORY）提示批次早于本次发布、仍滞留活跃区的终态卡。
- `LEDGER_DUPLICATE_KEY`（同一总账或批次总账内卡号重名，JSON 只保留最后一条）与 `ARCHIVE_ID_COLLISION`（未登记的归档卡与其他卡撞号）暂为 `ADVISORY`，计划在后续版本升级为阻断；未登记的归档卡只参与撞号判定，不作为依赖解析来源。合入主干前在 `git merge --no-commit --no-ff` 的合并结果上复核。
- `--next-id change|task`、`--topic <主题>`、`--list-checks` 与 `--scaffold new-card --plan` 为独占只读查询，不能与 `--card`、`--to`、`--record`、`--receipt`、`--release`、`--warn-only` 或 `--mode init` 合用。前两者分别输出覆盖全部批次及本机其他工作树、本地/远端跟踪分支的下一卡号（看不到他人未推送的分支）、主题在现行总账与各批次中的全部卡片（查不到主题时报 `TOPIC_EMPTY`，ADVISORY），并执行完整普通复核、退出码语义不变；`--scaffold` 只输出建卡计划，不写文件，缺失输入时计划标记为不可执行。
- `--release <version>` 为发版/归档前的只读批次预检：本批次活跃卡未达终态报 `RELEASE_NOT_TERMINAL`（Exit 4），无 `version` 的未收口卡报 `RELEASE_SCOPE_UNKNOWN`（Exit 6）。它不能与 `--card`、`--to`、`--record` 合用，也不证明发布范围完整。
- `--card <卡号> --receipt` 在状态同步后执行完整普通复核（退出码语义不变），并按固定格式输出节点回执：事实行取自卡片与本次复核，执行者只填写「未覆盖」「需要你」。审查时可对照回执与卡片原文，事实行被改写即视为汇报失真。它不能与 `--to`、`--record`、`--warn-only` 合用。
- `--card <卡号> --to <目标状态>` 在内存检查目标状态，`--record` 仅回写指定卡的 gate，不修改卡片或索引状态。全局违规也会计入记录结果；Exit 0 后同步状态，再运行普通检查。
- 不带 `--card` 的旧 `--record` 仍回写全部活跃卡；规范升级不执行它。记录时重新评估目标卡的当前约束，不把其旧 gate 失败当成本轮失败原因；真实结构或全局违规仍阻断。`--warn-only` 仅用于观察，不能与 `--record` 合用，也不能作为正式通过证据。
- 校验器检查非空、格式和部分关系，不能证明人类原话真实性、验收条件语义互斥完整、应用实测正确，或所有历史归档卡都已审计。审查者另行核对来源和覆盖范围。
- 修复限定在授权范围内，最多 3 轮；相同阻断连续两次或依赖缺失授权/事实时停止相关操作并报告。性能收益需要实测，不作固定比例承诺。
