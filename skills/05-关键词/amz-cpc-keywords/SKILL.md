---
name: amz-cpc-keywords
description: Sorftime 亚马逊 CPC 关键词词库构建。基于 Sorftime 数据构建全量关键词词库，4 分类打标（核心词/长尾词/场景词/痛点词，每类≥200词），支持流量词反查、搜索词拓展、关键词竞争度分析，输出含搜索量/CPC出价/竞争度评分的词库（每类 Top20 展示+全量列表）。当用户要构建关键词词库、做CPC关键词、关键词研究、关键词分类打标、关键词拓展、流量词反查、竞品关键词分析、关键词竞争度分析，或说"关键词词库/CPC关键词/关键词研究/关键词分类/关键词拓展/流量词反查/竞品关键词/关键词竞争度/keyword research/keyword library/keyword expansion/CPC keywords/long-tail keywords/reverse ASIN lookup/competitor keywords/keyword competition/keyword taxonomy/亚马逊关键词/amazon keyword research/关键词打标/核心词长尾词场景词痛点词"时使用。默认 Amazon US，支持多站点。
---

# amz-cpc-keywords — CPC 关键词词库构建

基于 Sorftime 数据构建关键词词库：4 分类打标（核心词/长尾词/场景词/痛点词），每类 ≥200 词，含搜索量、CPC 出价、竞争度评分。

> 链路位置：第 5 环「关键词词库」。上游 ← amz-profit-calc（go 决策 + 目标 ASIN）；下游 → amz-listing-creator（埋词）+ amz-ad-planning（投放）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据输出选择 MCP 或 CLI 通道。默认站点：US（domain=1）。

## 🔴 指标口径与排名一致性

- `keyword_detail.search_conversion_rate` 是平台关键词搜索转化指标，不是广告 CVR；`click_conversion_rate_90d` 也只有在 click 样本有效时才可解释。
- `product_traffic_terms`、`product_ranking_trend_by_keyword`、`competitor_product_keywords` 返回的排名不得混算。必须保留来源和时间，并保留 `Pos X/Y` 的分母。
- 需要并排展示时先运行：

```bash
python3 scripts/rank_consistency.py   --source 'traffic=Page 1, Pos 6/50'   --source 'ranking_trend=Page 1, Pos 14/58'   --source 'competitor=Page 1, Pos 4/57'
```

`MATCH` 至少要求两个非空且互异的规范化来源 ID；单来源、未知来源、重复来源（含大小写/别名重复）或空来源分别返回 `INSUFFICIENT_SOURCES` / `INVALID_INPUT`。结果若为 `DIFFERENT_SOURCES_DO_NOT_MERGE`，只能标“跨接口排名待核实”，不能取平均或选一个当唯一真值。若 `position > total`、页码或总数为 0/负数，必须返回 `INVALID_INPUT`，不得参与比较。

## 核心能力

| 能力 | 说明 |
|------|------|
| 关键词词库构建 | 从竞品 ASIN 反查 + 关键词拓展，汇总 ≥800 词 |
| 4 分类打标 | 核心词 / 长尾词 / 场景词 / 痛点词（每类 ≥200） |
| 流量词反查 | 竞品 ASIN 流量词反查 |
| 搜索词拓展 | 从种子关键词拓展相关词 |
| 竞争度分析 | 搜索量/CPC/竞争度/供需比综合评分 |

## 工作流

### Step 1：确定种子

从用户对话获取：
- **产品名或类目名**（如 "power bank" / "portable blender"）
- **竞品 ASIN**（可选，提供则从竞品反查流量词）

### Step 2：关键词采集

**MCP 通道：**
- `keyword_detail`：种子词详情
- `keyword_extends`：拓展关键词
- `keyword_list`：热门关键词列表
- `keyword_search_results`：SERP 产品分布
- `keyword_trend`：趋势
- `product_traffic_terms`：ASIN 流量词反查
- `competitor_product_keywords`：竞品关键词

**CLI 通道：**
```bash
# 关键词查询（ABA 热门词列表）
scripts/cli_call.sh KeywordQuery '{"pattern": {"keyword": "power bank"}, "pageIndex": 1, "pageSize": 50}'

# 关键词详情
scripts/cli_call.sh KeywordRequest '{"keyword": "power bank"}'

# 关键词拓展
scripts/cli_call.sh KeywordExtends '{"keyword": "power bank", "pageIndex": 1, "pageSize": 100}'

# 类目反查关键词
scripts/cli_call.sh CategoryRequestKeyword '{"nodeid": "7073960011", "pageIndex": 1, "pageSize": 100}'

# ASIN 流量词反查
scripts/cli_call.sh ASINRequestKeyword '{"asin": "B0CVM8TXHP", "pageIndex": 1, "pageSize": 100}'

# 关键词搜索结果产品
scripts/cli_call.sh KeywordSearchResults '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'

# 关键词排名追踪
scripts/cli_call.sh KeywordProductRanking '{"keyword": "power bank"}'

# ASIN 关键词排名趋势
scripts/cli_call.sh ASINKeywordRanking '{"keyword": "power bank", "ASIN": "B0CVM8TXHP"}'
```

### Step 3：4 分类打标

按规则将所有关键词分为 4 类，详见 `references/keyword-taxonomy.md`：

| 分类 | 定义 | 识别特征 |
|------|------|----------|
| 核心词 | 高搜索量品类主词 | 短词（1-2词）、月搜索量 >10000 |
| 长尾词 | 多词组合、精准 | 3词以上、含属性词 |
| 场景词 | 适用场景/人群 | 含 "for [scene]" / "for [人群]" |
| 痛点词 | 解决问题/缺陷 | 含 "leak-proof" / "non-slip" / "easy-xxx" |

**目标：每分类 ≥200 词。** 不足时回到 Step 2 扩大采集范围。

### Step 4：竞争度评分

对每个关键词计算综合评分，详见 `references/keyword-scoring.md`。

### Step 5：输出词库报告

每分类输出：
- **Top 20 代表词表**（按月搜索量降序）：关键词 | 月搜索量 | CPC | 竞争度分 | 涉及 ASIN 数
- **选词漏斗 Top 5**：从 Top 20 中精选
- **全量词列表**（≥200 词）

## MCP 通道

| 工具 | 用途 |
|------|------|
| `keyword_detail` | 关键词详情 |
| `keyword_extends` | 关键词拓展 |
| `keyword_list` | 热门关键词列表（raw） |
| `keyword_search_results` | SERP 产品列表 |
| `keyword_trend` | 关键词趋势 |
| `product_traffic_terms` | ASIN 流量词反查 |
| `competitor_product_keywords` | 竞品关键词（raw） |

⚠️ raw 工具通过 `sorftime_raw_call` 调用。

## CLI 通道

8 个关键词端点详见 `references/keyword-endpoints.md`。

## 输出格式

```markdown
# 关键词词库报告

## 调研概览
- 类目: {category}
- 站点: US
- 关键词池总数: {total}
- 4 分类词数: 核心词 N1 / 长尾词 N2 / 场景词 N3 / 痛点词 N4

## 核心词（≥200）
### Top 20 代表词
| Keyword | Search Volume | CPC | Competition Score | ASIN Count |
|---------|--------------|-----|--------------------|------------|

### 选词漏斗 Top 5
1. [kw] — 入选理由
...

### 全量词列表（≥200词）
...
```

## 详细方法论

- `references/keyword-taxonomy.md`：4 分类体系定义和打标规则
- `references/keyword-endpoints.md`：关键词端点说明
- `references/keyword-scoring.md`：竞争度/搜索量评分方法

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
