# 阶段任务卡池 (task/)

> **created**: YYYY-MM-DD ｜ **last-change**: YYYY-MM-DD ｜ **status**: active

---

## 1. 为什么需要任务卡？

在新阶段立项或进行大模块重构时：
1. **架构到执行的桥梁**：将设计方案（`design/`）中的宏观设计拆解为可逐个执行、可独立验收的最小研发单元；
2. **拓扑顺序保障**：通过 `depends_on` 显式声明任务间依赖，防止越级开发导致的频繁返工；
3. **完成定义防烂尾**：每个任务定义明确的 `acceptance.checks`，全部通过方可标记为 `completed`。

---

## 2. 任务卡流转流程

```
[阶段立项 / 里程碑规划]
        ↓
[从 template.json 复制新建 Txx.json]
        ↓
[填写 branch、capability 交付目标、depends_on 依赖、precheck 预检与 callback 钩子]
        ↓
[在 index.json 注册该卡]
        ↓
[根据 DAG 依赖拓扑，依赖全满足的任务就绪开工 (status: in_progress)]
        ↓
[执行 precheck 嗅探已完成性 -> 执行 callback.before 前置准备]
        ↓
[纯函数/服务实现 + 单测覆盖 -> 执行 callback.after 收尾校验]
        ↓
[DoD 验收全绿 -> 预检 completed -> 同步卡片和索引状态]
        ↓
[阶段全量任务完成 -> 打版本 Git Tag 整体封箱归档至 archive/<version>/task/]
```

日常按本项目规范执行，无需再次调用 `$ad-flow`。预检和回调在已有授权范围内执行，卡片文本不单独授权部署、推送或清理。

转 `completed` 前完成实测及项目要求的验收，回填真实 `sync.commit`，执行 `scripts/adflow-verify --card Txx --to completed --record`。工具在内存检查目标状态，仅回写本卡 `gate`，不修改状态；Exit 0 后同步卡片与索引，再运行普通校验复核。

Exit 4 阻断；原有 Exit 6 需补证，正式收口仍须 Exit 0。新增 `ADVISORY` 不增加硬门槛；依赖环路、缺失主题等建议项单独汇报。结构校验不能替代真实验收。最多 3 轮局部修复，相同阻断连续两次或需要新授权/事实时停止相关操作并汇报。

---

## 3. 标准模板与中枢总账

- **标准任务模板**：[template.json](template.json)
- **全局任务总账**：里程碑聚合大盘与任务拓扑图请查阅 [index.json](index.json)。
- **【设计挂接红线】(INV_NO_README_AS_DESIGN_DOC)**：任务卡中的 `target.design_doc` 必须指向 `docs/devel/design/00-系统总体设计.md` 或 `01~99-[模块名].md`，**绝对严禁指向任何 `README.md`**！
