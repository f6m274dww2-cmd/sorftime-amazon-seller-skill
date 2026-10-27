---
name: amz-ad-planning
description: Sorftime 纯数据驱动的亚马逊广告规划。仅基于 Sorftime 关键词数据（搜索量/竞争度/相关性/CPC出价区间）做广告决策，设计活动结构、预算分配、出价策略、广告组规划、自动/手动广告组合、关键词否定策略，不依赖亚马逊广告后台数据。当用户要做广告规划、广告投放方案、广告预算分配、广告出价策略、广告组规划、否定关键词策略、SP/SB/SD广告组合、自动手动广告搭配，或说"广告规划/广告投放方案/广告预算分配/广告出价策略/广告组规划/否定关键词/SP广告/SB广告/SD广告/自动广告手动广告/ad planning/advertising strategy/budget allocation/bidding strategy/ad campaign structure/negative keywords/auto manual ads/PPC planning/amazon ads/亚马逊广告/广告结构设计/广告活动规划/广告否定词"时使用。默认 Amazon US，支持多站点。
---

# amz-ad-planning — 广告规划方案

纯基于 Sorftime 关键词数据做广告规划决策：搜索量/竞争度/相关性/出价区间，不依赖亚马逊广告后台数据。

> 链路位置：第 8 环「广告引流」。上游 ← amz-cpc-keywords（词库含 CPC/竞争度）；下游 → amz-competitor-monitor（盯排名/跟卖）。全链路地图见 `../amz-workflow-map.md`。

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

## 核心原则

**纯数据驱动**：所有决策基于关键词数据，不假设已有广告后台数据：
- 搜索量 → 流量潜力
- 竞争度 → 出价难度
- 相关性（关键词与产品匹配度）→ 转化预期
- CPC 出价区间 → 预算估算
- `search_conversion_rate` → 市场搜索转化参考，**不是广告 CVR**
- 广告盈利判断必须等真实广告点击/订单/花费数据；没有时只输出初始方案

## 输入要求

规划前需要：
1. **产品信息**：产品名、品类、目标价格、毛利率
2. **关键词词库**（来自 amz-cpc-keywords 或用户提供）：含搜索量/CPC/竞争度
3. **广告预算**（可选）：日预算上限，不提供则按推荐值输出
4. **产品阶段**（可选）：新品期 / 成长期 / 成熟期

## 工作流

### Step 1：关键词分层到广告组

将词库中的关键词按分类和竞争度映射到不同广告组。详见 `references/keyword-to-ad-mapping.md`。

| 广告组 | 关键词来源 | 匹配方式 | 出价策略 |
|--------|-----------|----------|----------|
| 自动广告组 | （系统自动匹配） | Auto | 低出价起步 |
| 核心词手动组 | 核心词 Top 20 | Exact Match | 高出价抢位 |
| 长尾词手动组 | 长尾词 Top 20 | Phrase Match | 中出价捡漏 |
| 场景词手动组 | 场景词 Top 20 | Exact/Phrase | 中出价 |
| 痛点词手动组 | 痛点词 Top 20 | Exact Match | 中低出价 |

### Step 2：预算分配

按广告类型和关键词优先级分配预算。详见 `references/ad-planning-methodology.md`。

### Step 3：出价策略

基于 CPC 区间数据设定初始出价和调整规则。

### Step 4：否定关键词策略

从词库中筛选不相关词作为否定词。

### Step 5：输出规划方案

## MCP 通道

| 工具 | 用途 |
|------|------|
| `keyword_detail` | 关键词详情（搜索量/CPC） |
| `keyword_extends` | 关键词拓展 |
| `keyword_trend` | 关键词趋势 |
| `product_detail` | 产品详情（价格/评分参考） |
| `product_traffic_terms` | 竞品流量词反查 |

⚠️ raw 工具通过 `sorftime_raw_call` 调用。

## CLI 通道

```bash
# 关键词详情
scripts/cli_call.sh KeywordRequest '{"keyword": "power bank"}'

# 关键词拓展
scripts/cli_call.sh KeywordExtends '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'

# 关键词搜索结果
scripts/cli_call.sh KeywordSearchResults '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'

# ASIN 流量词反查
scripts/cli_call.sh ASINRequestKeyword '{"asin": "B0CVM8TXHP"}'

# 产品详情
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'
```

## 输出格式

```markdown
# 📊 广告规划方案

## 产品信息
- 产品: {product}
- 目标售价: ${price}
- 毛利率: {margin}%
- 阶段: {new/growth/mature}

## 广告活动结构

### Campaign 1: Auto - Discovery
| 项目 | 值 |
|------|-----|
| 类型 | SP Auto |
| 日预算 | $15 |
| 出价 | $0.50 |
| 目标 | 发现转化词 |

### Campaign 2: Core - Exact
| 项目 | 值 |
|------|-----|
| 类型 | SP Manual |
| 日预算 | $25 |
| 关键词 | [核心词 Top 10] |
| 出价 | $1.20-1.80 |
| 匹配方式 | Exact |

... (更多 Campaign)

## 预算总览
- 日总预算: $XX
- 月预估花费: $XXX
- 预估 ACOS: XX%

## 否定词列表
- 精确否定: [词列表]
- 词组否定: [词列表]

## 投放节奏
- 第 1-2 周: 测试期
- 第 3-4 周: 优化期
- 第 5-8 周: 放量期
```

## 详细方法论

- `references/ad-planning-methodology.md`：广告结构设计方法论（SP/SB/SD 组合、预算分配模型、出价公式、否定词策略）
- `references/keyword-to-ad-mapping.md`：关键词分类到广告组的映射规则

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
