---
name: amz-voc-analysis
description: Amazon VOC（Voice of Customer）客户声音分析 Skill。支持评论批量分析、差评痛点挖掘、好评卖点提取、Q&A/Alexa 问题分析、买家使用场景需求提取、Reddit 社媒舆情监控、负面评论替换机会识别、产品改进建议与卖点提炼。触发词包括：评论分析、差评分析、VOC、客户声音、review analysis、negative reviews、pain point、痛点挖掘、卖点提取、selling point、Q&A分析、Ask Alexa、买家需求、customer voice、Reddit舆情、社媒监控、social listening、review mining、竞品评论、差评关键词、改进建议、product improvement、listing优化素材。默认站点 Amazon US(domain=1)。
---

# amz-voc-analysis — VOC 客户声音分析

> 链路位置：第 9 环「VOC 复盘」，贯穿全程。输出反哺 amz-selection（替换机会）、amz-listing-creator（文案素材）、amz-image-creator（场景图）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

执行前先运行通道检测：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据 `recommended_channel` 选择 MCP 或 CLI 通道。

> 默认 site=US（domain=1）。评论实时采集消耗 Credits（每页5 Credits，每次启动至少扣5），评论查询消耗请求次数。

## 🔴 VOC 数据质量门禁（强制）

在分析前运行：

```bash
python3 scripts/review_quality.py   --customers-say customers_say.json   --reviews reviews_positive.json   --variant "24 oz"   --oz-mode volume   --out-dir ./voc-clean
```

硬规则：

- `Customers Say` 每个话题必须满足 `positive + negative <= mention`。不满足时，该汇总标 `INVALID`，不得用于痛点排序或产品决策。
- 优先使用变体 ASIN / variation ID；没有稳定 ID 时，对属性名、属性值、空白、大小写、分隔符、属性顺序和尺寸单位同义词规范化后分组。
- 同一 `review_id` / `reviewId` 是全局评论身份：跨不同 stable ID、不等价变体、目标/非目标变体、不同有效正文版本或冲突的评分/日期/VP/helpful 元数据时，整组阻断；不得按输入顺序任选一条。
- 同一属性签名对应多个 stable ID，或同一 stable ID 出现互斥规格时，标 `AMBIGUOUS_VARIANT`，不得进入目标可用集。
- 重复属性键若值冲突，整条记录按歧义处理；ml/l、fl oz、lb/g/kg 做确定性换算。普通 `oz` 默认是歧义单位，只有商品维度已确认时才用 `--oz-mode volume|mass` 换算。
- 目标变体做精确规格匹配；组合装或包含多个尺寸的标签不得自动归入单一目标变体。
- 同一变体组的全部非空标签都必须一致命中或一致不命中目标；部分命中、部分不命中时标 `TARGET_OWNERSHIP_CONFLICT` 并阻断整组。
- 在**同一真实变体内部**去重（正文优先，标题兜底）；不同变体之间不得互相删除。
- 同一 review ID 先选唯一代表，再分类内容质量；有效正文优先。其余重复记录计入 `duplicates_removed`，空内容重复另计但不重复算入 `INSUFFICIENT_CONTENT`。
- 标题与正文都为空时保留并标 `INSUFFICIENT_CONTENT`，不参与情感统计；同一 review ID 的空副本只保留一个代表。
- 未标变体的评论只在 review ID 组或唯一 stable ID 能确定归属时桥接；无法唯一归属时单独标记，不混入目标 SKU。
- 报告必须写：原始条数、去重后条数、目标/其他/未标变体条数、歧义/内容冲突/目标归属冲突条数、空内容条数、`accounted_rows` 与 `accounting_consistent`。
- `product_reviews` 单次最多约 100 条且无分页时，明确标“样本限制”。

输出文件：`customers_say_audit.json`、`reviews_clean.json`、`reviews_quality.json`。

### CLI 回退（MCP 评论缺 child ASIN 或 Customers Say 异常时）

先用官方 CLI 拉取原始评论和变体映射：

```bash
python3 scripts/sorftime_cli_fallback.py B08MPRB9YY --out cli-review-data.json
```

从 `cli-review-data.json` 找到目标 child ASIN 的 `Property`，再用 CLI 原始评论执行质量门禁：

```bash
python3 scripts/review_quality.py \
  --reviews cli_reviews.json \
  --variant "24 oz" \
  --oz-mode volume \
  --target-child-asin B08MPRB9YY \
  --trusted-child-identity \
  --trusted-target-property "Size:24OZ-50Pack" \
  --out-dir ./voc-clean-cli
```

CLI 回退只修复评论身份/变体字段，不修复错误的 Customers Say 统计；Customers Say 仍标 `INVALID`，VOC 改用原始评论。

## MCP 通道

### 评论与产品工具（Product 类）

| 工具名 | 状态 | 用途 |
|--------|------|------|
| `product_reviews` | ✅ | 产品评论（最多100条，review_type: Positive/Negative/Both） |
| `product_customers_say` | ⚠️ raw | Amazon AI 汇总的 "Customers Say" 评论摘要（通过 sorftime_raw_call） |
| `product_detail` | ✅ | 产品详情（获取评分分布、Feature 标签等辅助数据） |

### Reddit 社媒舆情工具（均为 ⚠️ raw，通过 sorftime_raw_call 透传）

| 工具名 | 用途 |
|--------|------|
| `reddit_post_search` | 搜索与产品/关键词相关的 Reddit 帖子 |
| `reddit_post_request` | 获取指定 Reddit 帖子完整内容 |
| `reddit_comment_request` | 获取 Reddit 帖子下的评论 |

### MCP 通道典型工作流

```
1. product_detail(asin) → 产品基础数据 + Feature 标签 + 评分分布
2. product_reviews(asin, review_type="Negative") → 差评采样
3. product_reviews(asin, review_type="Positive") → 好评采样
4. product_customers_say(asin) → Amazon AI 评论摘要
5. reddit_post_search(关键词) → Reddit 社媒舆情
6. 按 voc-analysis-framework.md 方法做痛点/卖点/场景分析
```

## CLI 通道

CLI 通道使用 `scripts/cli_call.sh`。

### 评论相关端点（domain=1）

| 端点 | 消耗 | 用途 |
|------|------|------|
| `ProductReviewsCollection` | Credits | 实时采集评论（不返回内容，需配合 Query 拉取） |
| `ProductReviewsCollectionStatusQuery` | 0 | 查询采集任务状态 |
| `ProductReviewsQuery` | 5 | 拉取已采集的评论（分页，每页100条） |
| `ProductCustomersSay` | 1 | Amazon AI "Customers Say" 摘要 |
| `ProductRequest` | 1 | 产品详情（评分分布/Feature标签） |

### Q&A（Alexa Questions）端点

| 端点 | 消耗 | 用途 |
|------|------|------|
| `AlexaQuestionsCollection` | 5 | 实时采集 "Ask Alexa" 预设问题及 AI 回答 |
| `AlexaQuestionsCollectionStatusQuery` | 0 | 查询采集任务状态 |
| `AlexaQuestionsCollectionResultQuery` | 0 | 按任务ID拉取本次采集结果 |
| `AlexaQuestionsQuery` | 5 | 拉取近15天已采集的 Q&A（分页，每页100条） |

> Alexa 端点支持站点 1-9（US/UK/DE/FR/IN/CA/JP/ES/IT），不支持 10-14。

### CLI 调用示例

```bash
# 拉取已有评论（第1页，100条）
scripts/cli_call.sh ProductReviewsQuery '{"asin": "B0CVM8TXHP", "pageIndex": 1}' --domain 1

# 仅拉差评（1-3星）
scripts/cli_call.sh ProductReviewsQuery '{"asin": "B0CVM8TXHP", "star": "10", "pageIndex": 1}' --domain 1

# 实时采集评论（热门模式，1页，仅VP评论）
scripts/cli_call.sh ProductReviewsCollection '{"asin": "B0CVM8TXHP", "mode": 0, "onlyPurchase": 1, "page": 3}' --domain 1

# 查采集任务状态
scripts/cli_call.sh ProductReviewsCollectionStatusQuery '{"asin": "B0CVM8TXHP", "update": 48}' --domain 1

# 获取 Amazon AI 评论摘要
scripts/cli_call.sh ProductCustomersSay '{"asin": "B0CVM8TXHP"}' --domain 1

# 采集 Q&A
scripts/cli_call.sh AlexaQuestionsCollection '{"asin": "B0CVM8TXHP"}' --domain 1

# 拉取 Q&A
scripts/cli_call.sh AlexaQuestionsQuery '{"asin": "B0CVM8TXHP", "pageIndex": 1}' --domain 1
```

## 输出

VOC 报告包含以下章节：
1. **调研概览**：类目/站点/ASIN数量/评论样本量
2. **Top 10 痛点**（按严重度指数排序）：痛点中文描述 + 频次 + 涉及ASIN数 + 原文证据
3. **Top 10 卖点**：用户高频认可的购买理由
4. **Top 10 使用场景**：典型场景 + 用户画像
5. **Q&A 洞察**：买家最关心的问题及 AI 回答
6. **社媒舆情**：Reddit 上的讨论热点
7. **改进建议与卖点提炼**：基于痛点和卖点输出差异化方向

## 详细参考

- [VOC 分析方法论：痛点分类/场景需求提取/差评关键词挖掘](references/voc-analysis-framework.md)
- [评论与 Q&A 端点参数说明](references/review-endpoints.md)

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
