# 盯盘日报模板

## 日报结构

```markdown
# 竞品盯盘日报 — {日期}

## 一、告警摘要
> 今日触发的所有重要变动，按严重程度排序

### 🔴 高优先级
- [告警类型] ASIN {asin}: {变动描述}

### 🟡 中优先级
- [告警类型] ASIN {asin}: {变动描述}

### 🟢 低优先级
- [告警类型] ASIN {asin}: {变动描述}

---

## 二、ASIN 监控详情

### ASIN: {B0XXXXXXX} — {产品名}
| 指标 | 昨日 | 今日 | 变动 |
|------|------|------|------|
| 售价 | $XX.XX | $XX.XX | ±X.X% |
| 月销量 | XXX | XXX | ±X.X% |
| 评分 | X.X | X.X | ±X.X |
| 评论数 | XXX | XXX | +XX |
| Bsr排名 | #X | #X | ↑/↓ X |
| Buybox卖家 | {name} | {name} | 变动/稳定 |

**变动说明**：
- 价格变动 ≥10% 标红，≥5% 标黄
- 评论增速 ≥100 标红，>5 标黄
- 评分下降 >0.1 标红
- 月销量变动 ≥20% 标注

---

## 三、关键词排名监控

### 关键词: {keyword}
| 指标 | 昨日 | 今日 | 变动 |
|------|------|------|------|
| 月搜索量 | XXX,XXX | XXX,XXX | ±X.X% |
| 建议CPC | $X.XX | $X.XX | ±X.X% |
| 我方排名 | 第X页第X位 | 第X页第X位 | ↑/↓ |
| 竞品排名 | ... | ... | ... |

---

## 四、Best Seller 榜单变动

### 类目: {类目名} ({nodeid})
- 今日新进入 top100: {asin} ({产品名}, 排名 #X)
- 今日跌出 top100: {asin}
- 排名大幅上升(>20位): {asin} ↑XX位
- 排名大幅下降(>20位): {asin} ↓XX位

---

## 五、跟卖监控

### ASIN: {B0XXXXXXX}
- 当前 Buybox 卖家: {name} (变动/稳定)
- 跟卖卖家数: X (昨日 X)
- 新增跟卖: {卖家名} — 价格 $XX.XX
- 库存异常: {卖家名} 库存 0
- Buybox 被抢: 是/否

---

## 六、今日总结与建议
1. {最重要的发现及建议行动}
2. {次重要发现}
3. {需持续观察项}
```

---

## 告警规则参考

| 监控对象 | 指标 | 🔴 高优先级 | 🟡 中优先级 | 🟢 低优先级 |
|---------|------|-----------|-----------|-----------|
| ASIN | 价格变动 | ≥10% | 5-10% | <5% |
| ASIN | 评论增速 | ≥100条 | 6-99条 | 1-5条 |
| ASIN | 评分变动 | 下降>0.1 | 上升>0.1 | 无变化 |
| ASIN | 月销量变动 | ≥20% | — | <20% |
| 关键词 | 搜索量变动 | ≥15% | — | <15% |
| 关键词 | CPC变动 | ≥15% | — | <15% |
| 跟卖 | Buybox变更 | 丢失Buybox | — | — |
| 跟卖 | 新增跟卖者 | 出现新卖家 | — | — |
| 榜单 | 新进入top100 | 直接进入前20 | 21-100名 | — |

---

## 日报生成方式

### MCP 通道（对话式）
调用 `product_detail` 拉取 watchlist 中所有 ASIN 的最新数据，与上一次 snapshot 对比，按上述告警规则输出。

### CLI 通道（脚本化）
```bash
# 1. 拉取 ASIN 详情（支持批量，最多10个）
scripts/cli_call.sh ProductRequest '{"asin": "B0ASIN1,B0ASIN2,B0ASIN3"}' --domain 1

# 2. 拉取监控任务执行结果
scripts/cli_call.sh KeywordTasks '{"pageSize": 50}' --domain 1
scripts/cli_call.sh ProductSellerTasks '{"pageSize": 50}' --domain 1

# 3. 拉取具体批次详情
scripts/cli_call.sh KeywordBatchScheduleDetail '{"ScheduelId": "batch123"}' --domain 1
scripts/cli_call.sh ProductSellerTaskScheduleDetail '{"ScheduelId": "batch456"}' --domain 1

# 4. 拉取榜单数据
scripts/cli_call.sh BestSellerListDataCollect '{"nodeid":"7073960011","BestSellerListType":5,"queryDate":"2026-09-09 00"}' --domain 1
```
