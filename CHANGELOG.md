# Changelog

本文件按版本记录面向使用者的重要变化，采用 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 分类与 [Semantic Versioning](https://semver.org/spec/v2.0.0.html) 版本号。

已发布版本的日期与 GitHub Release 保持一致；未发布变化集中在 `Unreleased`。GitHub Release 正文只包含对应版本条目，不混入未发布内容。

## [Unreleased]

## [1.8.0] - 2026-11-17

### Added

- 校验器内建诊断码注册表，并新增只读查询 `scripts/adflow-verify --list-checks [--json]`：列出全部 66 个诊断码（42 `ERROR` / 6 `WARN` / 18 `ADVISORY`）的默认严重级别、一句话释义与修复提示。目录为静态输出，不依赖目标项目状态，与 `--next-id`/`--topic` 同类的独占查询；JSON 顶层为 `tool`、`version`、`checks`，条目按 `code` 排序。回归测试以 AST 扫描全部发出点，双向比对注册表、默认级别与字段完整性，并拒绝绕过 `Ctx.add` 直接追加 finding 的新增调用。
- 补齐 Step 7 设计登记契约：`docs/devel/index.json` 的 `design` 子系统新增 `designs` 数组，条目为 `{file, topic, status, title}`（项目根相对路径与 `@topic` 锚标）；SKILL、workflow、设计 README 与索引路由规约同步说明。新增 ADVISORY `DESIGN_ROUTE_DRIFT`：声明 `designs` 后报告设计文档未登记、条目指向不存在文件、缺少 `file`、`designs` 非数组或主题锚标未命中；旧布局没有该键时保持只读兼容，初始化与升级不追溯补登记。
- 每条 finding 新增修复提示 `hint`：文本输出在问题行下显示「↳ 修复」，`--json` 的 `findings[].hint` 承载同一内容。注册表提供默认提示，调用点可传更具体的一条覆盖；42 个 `ERROR` 码全部覆盖。涉及人工原话、历史归档、真实提交或既有资产处置时，提示指向根因复查或现有 SOP，不诱导改写证据，也不改变回执与路由查询的固定输出。`JSON_PARSE` 改走统一发出路径。
- `--json` 的 `summary` 新增 `codes`：按诊断码汇总本次最终 findings 的各严重级别条数（先应用 `--warn-only`，无发现时为 `{}`）。新增字段均为增量，旧消费者可继续解析；启用严格字段校验的消费者应在升级前核对。
- 维护者统一检查入口 `tools/check.sh`：依次运行回归测试、`bump_version.py --check`、`check_package.py` 与 `sh -n scripts/adflow-verify`，本地与 CI 使用同一命令。
- 源仓库 CI `.github/workflows/ci.yml`：Linux、macOS 的 Python 3.9 与 3.12 上执行 `tools/check.sh`。它只验证技能包自身，不代表目标项目验收；安装到目标项目的校验器仍不依赖钩子或 CI。
- 维护者检查器 `tools/check_package.py`：解析 `workflow.yaml` 中以成对 `# @adflow:manifest-begin/end <名称>` 注释界定的 JSON 流式机器块，校验每块唯一且可解析，安装映射恰为 24 个治理文件加 2 个校验器文件，目的地唯一且为项目内相对路径，模板存在且无孤儿，`docs/standards` 与 `scripts` 归属正确，wrapper 保留执行位，升级映射只触碰受管资产并与安装模板一致，且与校验器 `BASE_FILES`/`STANDARD_FILES`/`TOOL_FILES`/`LEGACY_FILES` 常量及版本双锚一致。未知字段、重复字段、重复目的地与解析失败均报出具体块和条目。
- 新增回归 `tools/test_checks_catalog.py`（诊断目录、提示场景与统计）与 `tools/test_check_package.py`（映射负例、互换模板的内容独立断言，以及按映射安装到空工程后由安装版 Shell 入口执行 `--mode init` 与普通复核）。
- 新增只读建卡计划（A6 试点）`scripts/adflow-verify --scaffold new-card --plan`：输出建议卡号与取号依据、模板路径、设计文档与 `@topic` 锚标解析、拟创建的卡片内容、总账/主题/待办变更与缺失输入；缺失项使 `executable=false`。计划不写任何文件，卡号不构成原子预占，退出码沿用普通复核语义。写入与归档流程未实现，需另行设计冲突检测、中断恢复与人工验收后再决定是否发布。
- 把 v1.8.0 新增命令面纳入 Agent 执行约定：`SKILL.md`、`workflow.yaml`、`AGENTS.md` 模板、变更/任务 SOP 与 C/T 卡池 README 明确 `--list-checks`、`--scaffold new-card --plan` 及其 `--track`/`--design-topic`/`--title`/`--card-version`/`--branch`/`--design-doc`/`--todo`/`--milestone`，以及 `--json` 的 `hint` 与 `summary.codes` 由 Agent 在流程中使用。建卡必须先取得 `executable=true` 的只读计划，再按 `writes`/`topics`/`todo` 落盘；人类只用自然语言，Agent 不把命令清单转交人类。新增回归 `tools/test_agent_surface.py` 校验这些参数与输出字段出现在指令层。

### Changed

- `workflow.yaml` 的 Step 4/5/6/8 与升级 U2–U4 的机器消费映射改为 JSON 流式取值（同时是合法 YAML 值），保留原有字段层级与条目说明；新增 `execution_contract.machine_manifests` 说明块约定与检查边界。普通段落与逐步操作规则保持原 YAML 写法。
- `SKILL.md`、`workflow.yaml` 与审计清单不再逐码复述诊断清单，改为“以 `--list-checks` 为准 + 策略说明”；`ADVISORY` 默认政策、`ARCHIVE_NON_TERMINAL` 硬门禁例外、历史批次处置与旧布局兼容保持不变。
- README 维护章节与发版步骤改用 `./tools/check.sh`，并补充 `--list-checks`、`hint` 与 `summary.codes` 的说明。

## [1.7.0] - 2026-11-05

### Added

- AGENTS 项目宪法「四、测试规范」新增首条规则「本地既有测试规则优先」：先扫描项目既有测试规则与约定（原 agent 文件测试规范、构建/测试配置与命令、CI 测试入口、既有测试目录布局与命名习惯），存在则按已有规则组织与执行测试，不强行迁移测试位置或改写既有约定；原「测试文件归拢」等规则成为无既有约定时的默认规范。已有项目经 `$ad-flow --upgrade` 刷新宪法时同步获得该规则，项目自定义规则区不受影响。
- 分层总账：发版归档改为把本批次卡片的登记与主题归属写入冻结的批次总账 `docs/archive/<version>/index.json`（`$schema: adflow-archive-batch-v1`，两轨共用一份），并从现行总账移出；现行总账只登记活跃卡，`topics[*].design_doc` 照常保留，设计正文的总账链接不变。此前现行总账保留全部历史登记，每次发版只改写 `file`，规模随卡片总数线性膨胀，日常建卡与转状态都要改写这份不断增长的文件。校验器对批次总账条目执行与现行总账相同的路由硬检查（`INDEX_FILE_INVALID` / `INDEX_FILE_DEAD` / `INDEX_ID_DRIFT` / `INDEX_STATUS_DRIFT` / `ARCHIVE_NON_TERMINAL`），并据此判定 `ID_DUPLICATE` 与跨版本依赖；未声明该 schema 的批次根文件（如项目自建快照）不按清单解析。
- 校验器新增只读路由查询：`--next-id change|task` 输出覆盖现行总账、全部批次总账与归档目录的下一卡号（文本模式只打印卡号），取代通读历史登记求最大号；它同时读取本机其他工作树中的卡片文件与本地/远端跟踪分支末端的卡片文件名，最大号来自别处时以 `next_id_basis` 与 stderr 说明出处，减少多分支并行撞号，但看不到他人未推送的分支，仍不是原子预占；`--topic <主题>` 列出该主题在现行总账与各批次中的全部卡片、状态、批次与路径。两者执行完整普通复核、退出码语义不变，不能与其他模式参数或 `--warn-only` 合用。
- 新增 ADVISORY 诊断（不改变退出码，不追溯阻断）：`LEDGER_ARCHIVED_ENTRIES`（现行总账仍登记或引用归档卡，每轨聚合为一条）、`RELEASE_STRANDED`（`--release` 时批次早于本次发布、仍滞留活跃区的终态卡；按版本精确匹配的归档不会带走它们）、`TOPIC_EMPTY`（`--topic` 查无该主题）、`LEDGER_DUPLICATE_KEY`（同一总账或批次总账内卡号重名：JSON 只保留最后一条，合并冲突保留两侧登记时会静默吞掉一张卡）、`ARCHIVE_ID_COLLISION`（未登记的归档卡与其他卡撞号；未登记卡仍不作为依赖解析来源）。后两项此前完全不可见，先以 ADVISORY 观察，计划在后续版本另行记录决策后升级为阻断。
- 归档 README 新增「6. 现行总账瘦身」：旧项目经人工授权一次性把现行总账中的归档登记迁入批次总账，不改写、不移动卡片文件，以普通复核发现、`--next-id` 与各主题 `--topic` 前后一致作为等价证据。新增样例 `examples/sample-archive-index.json`。

### Changed

- CLI 回归测试从 `tests/test_adflow_verify.py` 迁至 `tools/test_adflow_verify.py`，维护命令改为 `python3 -m unittest discover -s tools -v`。回归测试与 `bump_version.py` 同属维护者资产，统一归入不安装到目标项目的 `tools/` 资产区，仓库根目录不再保留 `tests/` 目录。
- 发版归档第 3 步由“改写现行总账 `file`”改为“写入批次总账并移出现行登记”，复核改用 `--topic` 从设计主题定位归档卡并确认无新增 `ARCHIVE_UNREGISTERED`（AGENTS、归档 README、发版归档 SOP、索引路由规约、文档中心、研发 README、心智模型）。建卡取号改为 `scripts/adflow-verify --next-id`（AGENTS、C/T 卡池 README、变更 SOP、异常流手册）；任务依赖经批次总账定位归档前置卡（任务 README、任务 SOP）。旧布局继续有效：初始化与升级不迁移、不瘦身现行总账，治理文件仍为 24 个，既有硬检查对旧数据不变。
- 多分支合入规则（AGENTS 五.1、异常流手册、变更 SOP、C/T 卡池 README）：合入主干前以 `git merge --no-commit --no-ff <分支>` 在合并结果上运行校验，Exit 0 且没有 `LEDGER_DUPLICATE_KEY` / `ARCHIVE_ID_COLLISION` 时再提交，否则 `git merge --abort`。分层总账下，主干已归档进批次总账的卡与另一分支新建的同号活跃卡路径不同，可能无任何 Git 冲突地合入，此时只有校验器的 `ID_DUPLICATE` 能发现撞号。
- 总账样例改为分层布局：变更与任务总账样例只登记活跃卡，归档卡移入批次总账样例；同时移除样例主题中指向不存在卡片的 `C015` / `C020` / `T06`。回归测试核对样例遵守分层规则，并以校验器实际解析批次总账样例。

## [1.6.0] - 2026-10-26

### Added

- T 卡补齐人工核验代签：任务卡模板 `acceptance` 新增 `user_quote` 与 `signoff`，AGENTS 二.1、任务 README 与任务 SOP 在 `completed` 预检前增加“节点回执请求确认 → 记录人类原话”一步，与 AGENTS 声明的“人工核验代签”闭环及 C 卡流程一致。此前 T 卡无处记录确认，回执固定显示“按项目要求另行验收”。
- 新增 ADVISORY 诊断（不改变退出码，旧卡不追溯阻断）：`TASK_SIGNOFF_MISSING`（`completed` 任务卡缺少确认原话或代签人）、`TASKS_NOT_ALL_DONE`（`completed` 任务卡仍有 `tasks[].done` 不为 `true`）、`SIGNOFF_STALE`（`rejected` 变更卡仍保留驳回前的 `user_quote`，或返工后的终态卡沿用驳回前已记录的原话）。
- 维护者工具 `tools/bump_version.py`：`--check` 核对 23 处治理版本号与 CHANGELOG 发布标题、链接是否一致；`<X.Y.Z>` 一次性更新全部版本号并把 `[Unreleased]` 切为新版本条目、更新比较链接。不安装到目标项目，提交与打 Tag 仍由人工执行。回归测试运行 `--check`，漏改任一处即失败。

### Changed

- 节点回执「人工」行 C/T 卡统一：已确认显示原话与代签人，未确认显示“待人工确认”，驳回后显示“已驳回，返工后重新请求确认”。「同步」行在收口前把未到期的项显示为“待回填 / 待登记 / 待回写”，收口后仍缺失才显示“缺失 / 未登记 / 未回写”，避免 `verified` 等中间节点误读为缺口。
- 驳回流程明确清空驳回前的 `user_quote` / `signoff`，返工后须取得新的人工确认（AGENTS、变更 README、异常流手册、审计清单）。
- 目标项目发版顺序改为“收口 → `--release` 批次预检 Exit 0 → 归档移动 + 总账更新 + CHANGELOG 定稿 → 复核 Exit 0 → 提交后在该提交上打 Tag”，保证 Tag 指向的提交已包含归档结果与定稿的 CHANGELOG（AGENTS、归档 README、任务 README、任务 SOP、发版归档 SOP）。`sync.tag` 改为在归档步骤随归档提交填写，消除“收口时不得虚填”与“归档卡冻结”导致该字段永远无法如实填写的矛盾。
- 测试从校验器读取 `VERSION`，发版时不再需要手改测试中的版本号；README 新增技能维护与发版步骤。

### Fixed

- 修复驳回后沿用过期代签：已 `verified` 的卡被驳回后，`--to verified` 预检会接受驳回前的确认原话。C 卡 `--record` 现在于 `gate.signed_quote` / `gate.signed_rejection_count` 记下所依据的原话与驳回次数；驳回卡残留原话，或返工后仍沿用该原话时报 `SIGNOFF_STALE`，并保留旧记录直至写入新原话；回执不再把驳回前的原话显示为有效确认。仅对本版 `--record` 记录过的卡生效，不追溯旧卡。
- 补齐 v1.5.0 遗漏的 CHANGELOG 比较链接：新增 `[1.5.0]`，`[Unreleased]` 改为从 `v1.5.0` 比较。

## [1.5.0] - 2026-10-20

### Added

- 校验器新增只读发版批次预检 `--release <version>`：本批次（按卡片 `version`，缺失时回退总账登记）活跃卡未达本轨终态报 `RELEASE_NOT_TERMINAL`（Exit 4），无 `version` 的未收口卡报 `RELEASE_SCOPE_UNKNOWN`（Exit 6），找不到批次卡片报 `RELEASE_BATCH_EMPTY`（ADVISORY）。发版与归档门禁由“逐卡人工核定”改为可执行预检，发布范围仍由人工确认；该参数为可选项，不改变默认门禁，也不在初始化或升级中运行。
- `--mode init` 新增 `TOOL_VERSION_DRIFT`：已安装 `scripts/adflow_verify.py` 的版本须与 `docs/index.json.adflow_version` 一致，避免升级后项目仍运行缺少新门禁的旧校验器。
- 新增 ADVISORY 诊断：`DEP_NOT_READY`（任务已 `in_progress` 但前置未 `completed`）、`ARCHIVE_UNREGISTERED`（归档卡未经现行总账路由）、`TAG_DUPLICATE`（`AGENTS.md` 含多个版本不同的初始化标签）、`PLACEHOLDER_UNRENDERED`（初始化后元数据仍为 `MyProject` / `YYYY-MM-DD`）。均不改变退出码。
- 卡片节点回执：`scripts/adflow-verify --card <卡号> --receipt` 在状态同步后执行完整复核（退出码语义不变），按固定格式输出 Markdown 回执——标题（`from → to`）、批次/分支/设计行、验收表，以及「门禁」「同步」「人工」「驳回」「改动」事实行全部取自卡片与本次复核，执行者只填写「未覆盖」「需要你」。AGENTS 模板新增二.3 规定请求人工确认、`verified`、`closed`、`completed`、`rejected` 各节点统一转交该回执，C/T 卡池 README、文档中心与 SOP 的“同步后复核”一步改用此命令。`--record` 预检时额外记录 `gate.from_status`，回执据此显示真实发生的状态转换。
- 技能与 workflow 明确模板占位符渲染契约：项目名与元数据日期在初始化时填写真实值，正文格式示例保留占位符，升级保留既有项目名与创建日期。

### Changed

- AGENTS 模板、归档 README、文档中心、任务 README 与发版归档 SOP 的发版顺序统一为“收口 → `--release` 批次预检 Exit 0 → 归档移动 + 总账更新 → 复核 Exit 0 → 打 Tag / CHANGELOG 定稿”；修正任务 SOP 与发版归档 SOP 中“先打 Tag 再归档”的旧顺序。
- 升级刷新归档 README 时保留项目的归档批次清单及勘误登记。
- 样例对齐现行模板：变更卡与任务卡补齐 `version`、`sync`、`gate` 并在收尾回调中运行校验器，移除清空 `local/` 测试数据的破坏性回调；设计样例改为四章结构与英文元数据，改经变更总账查询历史卡，不再直接链接会随归档移动的卡片文件。新增测试保证样例字段集合与模板同步。

### Fixed

- 里程碑成员判定兼容 `milestones[].tasks` 清单、任务卡中的里程碑 ID、标题及带归档后缀的标题，修复 `MILESTONE_STATUS_DRIFT` 漏报；区分 `M1` 与 `M10`，诊断按任务号稳定排序。此修复在 v1.4.0 标签之后合入，本版首次随正式发布交付。
- 归档扫描通过卡号文件名或 `id` 识别缺少 `status` 的卡片，以 `JSON_TYPE`（Exit 4）报告，不再静默跳过；总账快照和非卡片报告仍不受检。
- 初始化占位符检查仅匹配字符串元数据，避免对象或数组字段触发 `TypeError`，保持占位符诊断的 `ADVISORY` 口径。
- `changes` / `tasks` 与既有 `rejections` 一同校验为对象数组或 null；非法类型返回 `JSON_TYPE`（Exit 4），不再使节点回执崩溃或静默丢弃内容。
- 修复 `ARCHIVE_NON_TERMINAL` 漏检：此前只检查经总账路由的归档卡，绕过总账直接放入 `docs/archive/<version>/{change,task}/` 的非终态卡仍保持 Exit 0。现增加归档目录物理扫描（跳过总账快照 `index.json` 与非卡片资料），与总账路由同口径判定。
- 修复 `CHANGELOG_LINK_MISSING` 漏报：此前以子串匹配卡号，CHANGELOG 模板注释中的语法示例 `C001` 会让首张 C 卡永远“已互链”，`C0011` 也会误命中 `C001`。现忽略 HTML 注释并按整词匹配。
- 修复零沉淀检查漏报：卡号紧邻中文（如“修复C001问题”）时 `\b` 无法识别，残留待办不被阻断。现改用 ASCII 边界匹配。
- 修复 `workflow.yaml` 状态路由：第 1 步输出状态名与第 2、3 步条件不一致（`ALREADY_INITIALIZED` 与 `ALREADY_INITIALIZED_UP_TO_DATE`；`NEEDS_UPGRADE` 及版本冲突状态会落入迁移确认与快照步骤）。迁移确认与隔离快照现仅作用于 `ONGOING_*` 状态，并补齐 `VERSION_NEWER` / `VERSION_CONFLICT` 状态。

## [1.4.0] - 2026-10-14

### Added

- 新增发版与归档门禁（INV_RELEASE_ARCHIVE_GATE）：打 Tag、发布或移卡入归档前，本发布批次 C 卡须全部 `closed`、T 卡须全部 `completed` 且普通校验 Exit 0；严禁非终态卡进入归档区，明确「收口 → 校验 Exit 0 → 归档移动 + 总账更新 → 复核校验 Exit 0 → 打 Tag / CHANGELOG 定稿」顺序；Exit 4 期间禁止发布、归档与主干合入。规则写入 AGENTS.md 模板、归档 README 与发版归档 SOP。
- 校验器新增 `ARCHIVE_NON_TERMINAL` 确定性违规（Exit 4）：归档区卡片状态非 `closed`/`completed` 即阻断，补齐归档前置自 v1.1.0 起仅存在于文本的门禁覆盖。该提升为记录在案的适用性/迁移决策：存量项目升级后，历史冻结非终态卡会暴露为 Exit 4，属预期暴露而非升级引入的故障；按归档 README「历史批次账实修复」流程人工处置，升级只报告不改写。
- 校验器新增 `MILESTONE_STATUS_DRIFT` 旁路诊断（ADVISORY）：里程碑标记 `completed` 而成员任务未完成时报告，不影响退出码；list 型里程碑结构（无状态字段）自动跳过。
- 新增归档批次账实不符修复 SOP（异常流手册第四节 + 归档 README「历史批次账实修复」，随升级分发到已初始化项目）：盘点暴露 → 人工三口径处置（补收加豁免标注 / 回迁活跃区 / 废弃注明理由，严禁伪造证据字段）→ 派生矛盾修正 → 勘误登记 → 治理修复建卡 → 复核恢复 Exit 0。

### Changed

- 修正发版归档 SOP 与归档 README 中「归档前普通校验 Exit 0」的过度承诺：非终态活跃卡没有状态前置要求，Exit 0 不证明批次全部终态；归档前须逐卡核定，归档后复核须再次 Exit 0。
- AGENTS.md 模板补充发布、归档与主干合入的阻断条件与操作顺序；推送、部署仍需独立授权，发版紧迫性不扩大权限。

### Fixed

- 修复发布未受门禁约束即移动卡片、导致非终态卡冻结进归档区的账实不符漏洞：此类"卡片与总账一致但状态非终态、gate 与 sync.commit 全部缺失"的历史事故，此后在归档复核中即被 `ARCHIVE_NON_TERMINAL` 阻断，不再静默保持 Exit 0。
- 修正 `MILESTONE_STATUS_DRIFT` 的成员判定：此前只把任务卡 `milestone` 字段与里程碑 ID 精确比对，凡该项目把里程碑标题（或带“(已发版归档)”一类后缀的标题）写入该字段，诊断即静默漏报。现改为解析 `milestones[].tasks` 成员清单，并接受里程碑 ID、标题与去后缀标题三种别名；前缀匹配限定在整词边界（`M1` 不误匹配 `M10`），输出按任务号排序稳定。新增 4 项回归用例覆盖真实登记形态、跨里程碑误配与成员全完成时的静默。

## [1.3.0] - 2026-10-13

### Added

- 新增 JSON 代码编写规范及 Python、Go、JavaScript、TypeScript、Java、Shell、C++、Rust 语言模板，保留 Google 与 Rust 官方来源。初始化可多选或只用通用规则，生成 `docs/standards/coding.json` 并关联 README、AGENTS 与顶层索引。
- 编码规范沿用项目已有工具配置，升级保留既有规范内容；初始化校验核对已登记文件及 JSON 可读性，兼容未安装该文件的旧项目，不新增格式门禁、审批或日常命令。

### Changed

- 将代码规范与 C/T 卡片模板集中到 `docs/standards/`，代码规范及 workflow 执行说明使用英文，其他模板保留中文正文与原有英文字段；扩充命名、注释、API 文档、错误处理和测试要求，补充各语言的文档格式。旧项目路径保持只读兼容，明确同步时保留自定义规则与历史记录。
- 统一全部 10 个 README 模板的用途、入口、规范和执行指引；公共约定集中说明，C/T 收口、待办移出与按批次归档保持可独立执行。
- 设计正文大纲统一为四章，明确批准规则、实现事实与验收证据的关系；校正路径、元数据和资源边界，环境入口改为分级处理说明，不新增治理状态、审批或日常命令。

### Fixed

- 修正英文化范围：恢复 README、AGENTS、设计大纲、指南、索引及卡片说明的原有语言；保留 `docs/standards/` 路径与详细编码要求，注释语言遵循项目约定。
- 修复归档任务依赖解析、索引登记卡丢失漏检和按轨状态校验，保持原有卡片状态与命令。
- 修复批量 `--record` 失败后的门禁自锁：重评本次记录卡的真实前提，保留全局违规阻断及只读门禁追责。
- 补齐 C/T 模板发布批次与 T 卡提交字段，将驳回、Hotfix 和编号冲突说明放入已有日常规则。
- 同版本退出前核对安装完整性，未完成时续做缺失步骤；保护根目录构建输入，保留无标准标题的原 Agent 规则并统一旧入口。
- 用现有 T 卡说明批准设计的实现进度，不新增基线体系、卡片状态、审批或日常步骤。
- 规范升级流程明确物理删除旧路径模板（`docs/devel/change/template.json` 与 `docs/devel/task/template.json`）；启用 `standards` 规范后禁止旧模板残留（`LEGACY_TEMPLATE_EXISTS` 门禁），消除双份模板歧义。

## [1.2.0] - 2026-10-10

### Added

- 标准库校验器 `scripts/adflow-verify`：按活跃卡片状态检查设计挂接、证据字段、提交祖先、索引、零沉淀和依赖等已覆盖前提；提供初始化骨架检查 `--mode init`、结构化输出 `--json`、观察模式 `--warn-only` 与真实结果回写 `--record`，不安装 Git hook 或外部 CI。
- 目标状态预检 `--card ID --to STATE`：在内存检查 `verified`、`closed` 或 `completed` 的前提，可仅回写指定卡的 `gate`；不修改卡片或索引状态，全局问题仍参与结果判定。
- `ADVISORY` 旁路诊断：报告缺失设计主题、依赖环路和终态验收项未全为 `true`，不改变退出码，不追溯提高旧项目硬门槛。
- 隔离工程夹具下的 CLI 回归测试，覆盖旧版兼容、只读预检、指定卡回写、违规记录及项目内工具独立运行。

### Changed

- 保留一次初始化、按需升级和日常独立治理；日常使用目标项目内的规则、模板、索引与工具，无需技能源目录。不新增技能子命令、卡片状态或审批阶段。
- 初始化、升级和收口步骤接入校验器；C/T 模板增加 `gate` 与收尾检查，升级刷新工具副本但不改写已有业务卡片、待办、索引登记和 `gate`。
- 区分授权、当前阶段步骤与来源资料；明确已捕获快照只读、升级使用独立快照，初始化保护既有 `local/`，后续授权构建、测试和部署可写入对应产物及报告。
- 涉及已有实例的操作优先参考部署报告并核对运行态，报告缺失或漂移时结合指南排查；纯单元测试不依赖部署报告。
- 在既有节点内执行生成、机械与语义评估、局部修复和重验，最多 3 轮，相同阻断连续两次则汇报；不承诺固定 Token 或延迟收益。
- README 补齐 1.2.0 改进、首次初始化、日常使用、版本路由、校验命令、退出码和能力边界；发布记录统一版本链接与分类。

### Fixed

- 初始化与升级在创建备份前，确保目标项目根 `.gitignore` 排除 `_adflow_backup/`，保留已有规则并避免重复追加；校验忽略效果，单独报告已被 Git 跟踪的备份。
- 修复重复卡号被字典覆盖而漏检的问题，并将全局或其他卡的违规计入完整检查的回写结果，避免局部 `gate` 错记通过。
- 修复 `--warn-only` 将硬违规误报为 Exit 0 的情况；降级观察存在违规时返回 6，禁止与正式 `--record` 合用。
- 校验器兼容任务索引的 `tasks` 与既有 `cards` 字段，不迁移旧数据；初始化索引、设计矩阵和待办表不再预登记示例事项。
- 修复 `workflow.yaml` Step 7 的 `execution_rules` YAML 序列格式。
- 统一初始化清单为 23 个治理文件（含 10 个目录 README）加 2 个工具文件，修正旧字段、步数和目录说明。

## [1.1.0] - 2026-09-24

### Added

- 23 个标准化治理文件，覆盖文档中心、静态资源、操作指南、设计基线、C/T 卡片、待办、环境治理与历史归档。
- 环境与缓存治理目录 `docs/devel/env/`，提供环境清单、分级清理指引和依赖恢复步骤。
- C/T 卡片模板中的 `branch`、`precheck` 与 `callback.before/after` 字段，用于声明执行分支、已完成性预检与准备、收尾命令。
- `$ad-flow`、`/ad-flow`、`ad-flow`、`adflow` 及明确初始化意图等技能入口。
- 存量文档隔离备份与设计基线重构流程：保留旧资产，依据旧文档和源码生成系统总体设计及模块设计。

### Changed

- 移除根目录 `adflow.config.json`，治理元数据统一存于 `AGENTS.md` 初始化标签与 `docs/index.json`。
- 规范要求 `design_doc` 指向真实设计正文及匹配的 `@topic`，禁止使用目录 `README.md` 代替设计文档。此版本尚未包含后续加入的可执行校验器。
- 规范要求将构建产物、运行数据及实测报告收拢至 `local/`，避免生成物进入源码和 Git。
- 再次调用技能时按目标版本同步项目规则、目录 README 与卡片模板，并保留已有业务设计、卡片及自定义规则。

[Unreleased]: https://github.com/4everSivan/ad-flow/compare/v1.8.0...HEAD
[1.8.0]: https://github.com/4everSivan/ad-flow/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/4everSivan/ad-flow/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/4everSivan/ad-flow/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/4everSivan/ad-flow/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/4everSivan/ad-flow/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/4everSivan/ad-flow/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/4everSivan/ad-flow/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/4everSivan/ad-flow/releases/tag/v1.1.0
