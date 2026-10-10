# 变更与核验卡池 (change/)

> **created**: YYYY-MM-DD ｜ **last-change**: YYYY-MM-DD ｜ **status**: active

---

## 1. 为什么需要变更核验卡？

在系统进入维护与演进期后，**严禁只改代码而使文档失真，也不要无序涂抹历史基线**：
1. **Bug 修复 (BugFix)**：发现并修复了业务规则、接口或算法中的缺陷；
2. **功能回调 (Rollback)**：实测后发现某项设计不合理，需要回调至上一版参数或逻辑；
3. **接口/契约微调 (Param/Refactor)**：联调时对请求参数、错误码、数据类型或枚举值进行调整。

此时，在 `docs/devel/change/` 下以 `C001`、`C002` 递增编号新建变更卡，记录变更原因、前后规则对照及证据锚。

---

## 2. 变更卡使用流程

```
[发现 Bug / 提出回调]
        ↓
[从 template.json 复制新建 Cxxx.json]  ★ 立即从 todo/now.md 物理删除对应行 (零沉淀)
        ↓
[填写 branch 分支标签、precheck 预检命令与 callback 前后回调钩子]
        ↓
[执行 precheck 嗅探已修复性 -> 执行 callback.before 前置环境准备]
        ↓
[修改代码 + 补充针对性回归测试 -> 执行 callback.after 收尾质量门禁]
        ↓
[运行测试采集 evidence 与脱敏 run_id]
        ↓
[AI 汇报实测并在会话中对齐]
        ↓
[人工确认无误 -> 摘录 user_quote/signoff -> 预检 verified -> 同步卡片和索引状态]
        ↓
[代码合入主干 -> 双向回写闭环 (更新 design、CHANGELOG、并在 index.json 标记 closed)]
```

日常按本项目规范执行，无需再次调用 `$ad-flow`。在已有授权范围内运行预检和回调；卡片中的命令文本不单独授权清理、部署或推送。

转 `verified` 前，取得真实人工确认后运行 `scripts/adflow-verify --card Cxxx --to verified --record`。转 `closed` 前先回填真实 `sync.commit` 并完成基线/CHANGELOG 回写，再以 `--to closed` 预检。工具只在内存评估目标状态并回写本卡 `gate`，不修改卡片或索引状态。Exit 0 后才同步状态，再运行普通校验确认落盘一致。

Exit 4 阻断；原有 Exit 6 需列明事实并补证，正式收口仍须 Exit 0。新增 `ADVISORY` 不增加硬门槛。结构校验不能证明业务行为或人工验收；按证据核对语义。按具体发现局部修复最多 3 轮，相同阻断连续两次或需要新授权/事实时停止相关操作并汇报。

---

## 3. 标准模板与中枢总账

- **标准卡片模板**：[template.json](template.json)
- **全局变更总账**：全量卡片索引与所属 Topic 映射请查阅 [index.json](index.json)。
- **【设计挂接红线】(INV_NO_README_AS_DESIGN_DOC)**：卡片中的 `target.design_doc` 与 `design.doc` 必须指向 `docs/devel/design/00-系统总体设计.md` 或 `01~99-[模块名].md`，**绝对严禁指向任何 `README.md`**！
