# 03 - 任务研发流操作规程 (Task SOP)

本 SOP 规范新阶段立项（Phase）、里程碑（Milestone）拆解、DAG 依赖拓扑管理及能力交付的生命周期。

---

## 阶段一：阶段立项与基线对齐 (Phase Planning)

1. **需求与设计先行**：
   - 在 `docs/devel/design/` 撰写或修订现行设计方案，确立业务领域架构；
   - 确保每个核心业务小节标注了概念主题 `<!-- @topic: TopicName -->`；
2. **待办清空**：
   - 若功能方向曾登记在 `todo/future.md` 或 `now.md`，立项后立即将对应行物理删除。

---

## 阶段二：任务卡拆解与 DAG 依赖 (Task Decomposition & DAG)

1. **里程碑划分**：
   - 确立阶段目标，划分有序里程碑（如 `M1-工程骨架`、`M2-领域内核`、`M3-业务接入`）；
2. **实例化任务卡**：
   - 从 `templates/docs/task/task-card.json.tpl` 复制并建立 `Txx.json`；
   - 填写 `branch: "feat/Txx-[desc]"`（指定多分支研发的特性分支标签）；
   - 填写 `precheck`（能力完成预检命令）与 `callback`（`before / after` 脚本钩子）；
   - **聚焦能力交付**：在 `tasks[]` 中拆解具体的 `capability`（如纯函数、数据结构契约、API 路由），严禁在任务卡中写死具体的代码物理文件路径；
   - **声明拓扑依赖**：显式填写 `depends_on: ["T01", ...]`；
3. **注册任务总账**：
   - 在 `docs/devel/task/index.json` 中注册该卡（包含 `branch` 字段），分配到对应的 `milestones` 与 `topics`。

---

## 阶段三：拓扑驱动自动化开工推导 (DAG Scheduling)

AI Agent 或开发者无需人工猜测下一步该干什么，通过 `task/index.json` 执行标准开工算法：

1. **查找待开发任务**：筛选 `tasks` 中 `status == 'pending'` 的卡片；
2. **检查前置依赖**：检查该任务 `depends_on` 列表中的所有前置卡是否均已是 `'completed'`；
3. **推导可开工清单**：所有依赖已满足的任务即为**当前就绪可开工任务**，推荐开工。

---

## 阶段四：预检、回调执行与完成定义验收 (Execution & DoD)

1. **开工与预检 (Precheck)**：
   - 将卡片及 `task/index.json` 状态改为 `"in_progress"`；
   - 执行 `precheck.command`，检测该任务是否已在代码库中实现（若已完成则置 `is_completed: true`，跳过重复编码直接进入 DoD 验收）；
2. **前置回调 (`callback.before`)**：
   - 按序执行声明的准备命令（如切换分支、拉取最新基线、环境预加载）；
3. **纯函数与分层交付**：
   - 优先实现纯数据结构与业务规则内核，避免过早引入数据库与网络框架耦合；
4. **后置回调 (`callback.after`)**：
   - 按序执行声明的收尾命令（如代码格式化、质量静态检查、构建扫描）；
5. **验收完成定义 (DoD)**：
   - 执行自动化测试套件与纯度检测；
   - 比对 `acceptance.checks` 中的 `true_if / false_if`，收集 `evidence` 并置 `result: true`；
   - 记录无害流水号 `run_id`；
   - 所有检查项全绿后，卡片状态置为 `"completed"`，在 `task/index.json` 同步标记。

---

## 阶段五：阶段封箱归档 (Phase Archiving)

当当前 Phase 所有里程碑任务均已 `"completed"`：
1. 跑通全量集成测试与构建，打出阶段版本 Git Tag；
2. 执行 [references/07-release-archive-sop.md](07-release-archive-sop.md)，将当前阶段任务卡全量封箱移入 `docs/archive/<版本号>/task/`。
