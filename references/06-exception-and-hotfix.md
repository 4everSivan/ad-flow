# 06 - 异常流与紧急通道 (Exception & Hotfix)

本规约补齐 QTVictory 实战中暴露的系统性漏洞：**核验驳回回流机制**、**Hotfix 紧急通道**以及**多 Agent 并行防撞号机制**。

---

## 一、核验驳回回流机制 (Rejection Recovery SOP)

当实测未达预期、测试用例红、或人类在会话中明确判定“驳回/不予合入”时，严格执行以下回流流程，杜绝“驳回后流程失控”：

```
人类判定驳回 ──► 卡片 status 改为 "rejected"
                     └─► rejections[] 追加驳回事实与原因
                          └─► 同卡返工修复 (不占新号，保留历史教训)
                               └─► 重新跑测试并进入第二轮 verification
```

1. **同卡返工原则**：
   - 核验驳回**不新建卡号**，继续在原卡上返工，保证变更历史的连贯性；
   - 绝不重新把事项丢回 `todo/now.md`（避免打破零沉淀纪律）。
2. **记录驳回审计事实**：
   在 `Cxxx.json` 的 `rejections` 数组中追加一条审计记录：
   ```json
   "rejections": [
     {
       "date": "YYYY-MM-DD",
       "reason": "8788 测试实例仍返回空数组，日K未正常加载",
       "action": "检查适配器返回字段并修复 sqlite 绑定，重新测试"
     }
   ]
   ```
3. **修复后重验**：
   - 修复完成后，重新收集 `evidence`，更新 `checks[].result`；
   - 再次呈报人工核验，通过后状态由 `rejected` 转为 `verified`。

---

## 二、Hotfix 紧急通道规则 (Emergency Fast-Track)

针对 S1/P0 级线上严重故障（如交易滑点击穿、资金数据错乱、生产阻塞）：

1. **先修后补原则**：
   - 允许开发者或 Agent 先动代码抢修、先推送 Hotfix 分支以解除生产险情；
2. **显式标记 Hotfix**：
   - 事后补卡时，必须将卡片的 `"is_hotfix": true`；
3. **合规豁免与补票期限**：
   - 门禁校验允许 `is_hotfix: true` 的卡片其 Commit 产生时间早于卡片创建时间；
   - **底线要求**：在故障恢复后 24 小时内，必须全量补齐 C 卡、双向回写设计基线并登记 CHANGELOG，完成闭环。

---

## 三、多 Agent / 多分支并行防撞号机制 (Parallel Collision Avoidance)

当多个 Agent 或开发者同时在不同分支处理不同卡片时：

1. **分支即预占 (Branch Reservation)**：
   - 创建分支时显式以卡号命名（如 `feat/C027-market-cache`）；
   - 创建卡片前，先拉取远程最新 `change/index.json`，按当前最大编号抢占递增；
2. **基线落地队列 (Land Queue)**：
   - 实现可以完全并行，但合入主干并执行设计方案回写时采用串行收口；
   - 后合入的分支若遇到对应设计小节被修改，先 Rebase 主干，解决设计文本冲突后再更新 `change/index.json`。
