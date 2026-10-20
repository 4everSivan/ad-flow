# Changelog

本文件按版本记录面向使用者的重要变化，采用 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) 分类与 [Semantic Versioning](https://semver.org/spec/v2.0.0.html) 版本号。

已发布版本的日期与 GitHub Release 保持一致；未发布变化集中在 `Unreleased`。GitHub Release 正文只包含对应版本条目，不混入未发布内容。

## [Unreleased]

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

[Unreleased]: https://github.com/4everSivan/ad-flow/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/4everSivan/ad-flow/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/4everSivan/ad-flow/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/4everSivan/ad-flow/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/4everSivan/ad-flow/releases/tag/v1.1.0
