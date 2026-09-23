# 07 - 发版与阶段封箱归档 SOP (Release Archiving)

本 SOP 规范项目在打出版本 Git Tag（如 `v0.1.0`）或阶段里程碑收口时，如何安全平移卡片、固化总账快照，并保证**设计方案基线 0 破坏、0 断链**。

---

## 一、归档触发条件

1. 当前版本内的所有变更卡（`Cxxx.json`）均已处于 `status: "closed"` 状态；
2. 当前阶段内的所有任务卡（`Txx.json`）均已处于 `status: "completed"` 状态；
3. 全量测试通过，代码已打出对应 Git Tag（如 `git tag v0.1.0`）；
4. `todo/future.md` 与 `now.md` 已完成例行评审。

---

## 二、归档执行四步法

```
【第 1 步】创建归档目录: docs/archive/<version>/{change,task}
     ↓
【第 2 步】物理迁移卡片: 将 closed 状态卡片移入归档目录
     ↓
【第 3 步】更新中枢总账: 更新 index.json 中的 file 映射路径
     ↓
【第 4 步】设计文档零修改: 现行基线保持纯净，0 断链
```

### 第一步：建立版本归档箱
在目标项目中执行创建：
```bash
mkdir -p docs/archive/<version>/change
mkdir -p docs/archive/<version>/task
```

### 第二步：物理移动已闭环卡片
将 `docs/devel/change/` 下已收口至本版本的卡片移动到 `docs/archive/<version>/change/`：
```bash
mv docs/devel/change/C001.json docs/archive/<version>/change/
# ... 对本版本内全部闭环卡片执行移动
```

### 第三步：更新中枢总账路由 (`index.json`)
在 `docs/devel/change/index.json` 中，更新被移动卡片的物理路径指向：
```json
"cards": {
  "C001": {
    "title": "修复日K引导缺code",
    "status": "closed",
    "version": "v0.1.0",
    "file": "docs/archive/v0.1.0/change/C001.json"  // 仅此处由 index 吸收变化！
  }
}
```
同时可在 `docs/archive/<version>/change/` 备份一份当时总账的静态快照 `index.json`。

### 第四步：设计文档零破坏（Zero Diff）
由于设计文档只声明 `<!-- @topic: MarketService -->` 与指向 `change/index.json#MarketService` 的总账入口，**设计文档正文中的任何字符都不需要改动**！
Git Diff 在设计方案上为 0，彻底根除了历史断链的隐患。

---

## 三、发版归档验收清单

- [ ] `docs/devel/change/` 下仅保留尚未发版的活跃卡片（甚至为空）；
- [ ] `docs/archive/<version>/` 下完整包含了本次发版的所有卡片与测试快照；
- [ ] 尝试从任意设计文档小节跟随 Topic 并在 `index.json` 查卡，路径 100% 正确命中；
- [ ] 自动化测试与 CI 门禁跑通退出码 0。
