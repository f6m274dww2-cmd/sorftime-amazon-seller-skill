---
name: amz-listing-creator
description: Sorftime 亚马逊 Listing 创作与优化。基于 Sorftime 数据生成标题/五点/描述/后台关键词，融合 A9+COSMO 算法优化、FABE 文案框架、8 维度质量评分，支持关键词覆盖检查、竞品对比优化、COSMO 意图信号优化。当用户要创建listing、写listing、优化listing、写标题五点描述、生成后台关键词、做listing评分诊断、改写listing，或说"创建listing/写listing/listing优化/listing创作/标题五点描述/后台关键词/listing评分/listing audit/create listing/optimize listing/listing copy/bullet points/product description/backend keywords/keyword coverage/A9 optimization/COSMO algorithm/listing scoring/写标题/写五点/写描述/listing改写/listing诊断/竞品对比优化/关键词覆盖检查/亚马逊listing/amazon listing copy"时使用。默认 Amazon US，支持多站点。
---

# amz-listing-creator — Listing 创作与优化

基于 Sorftime 数据的 Amazon Listing 全流程创作：标题/五点/描述/后台关键词生成、关键词覆盖检查、A9+COSMO 优化、竞品对比优化、8 维度评分。

> 链路位置：第 6 环「Listing 上架」。上游 ← amz-cpc-keywords（4 分类词库）+ amz-voc-analysis（痛点/卖点素材）；下游 → amz-image-creator（配图）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

执行任何数据操作前，先运行通道检测：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据输出选择通道：
- `mcp_available=true` → 优先使用 MCP 通道
- `cli_available=true` → 使用 CLI 通道
- 两者均不可用 → 提示用户注册配置

默认站点：US（domain=1）。

## 能力总览

| 输出物 | 说明 |
|--------|------|
| 完整 Listing | 标题 + 五点 + 描述 + 后台关键词 |
| 优化评分 | 8 维度打分（Title/Bullets/Images/A+/Description/Pricing/Reviews/SEO） |
| 关键词覆盖报告 | 每个目标关键词在 Title/Bullets/Description 的覆盖状态 |

## 工作流

### Step 1：收集输入

从用户对话中提取：
- **产品信息**：产品名、品牌、核心属性（材质/尺寸/颜色/容量等）、差异化卖点
- **关键词来源**：用户提供的词表 / 竞品 ASIN 反查 / 关键词拓展
- **竞品 ASIN**（可选）：1-3 个竞品 ASIN 用于对比优化
- **风格偏好**：Professional / Friendly / Urgent / Luxury（默认 Professional）

### Step 2：获取关键词数据

**MCP 通道：**
- `keyword_detail`：查关键词搜索量、CPC、竞争度
- `keyword_extends`：拓展相关关键词
- `keyword_search_results`：查看关键词 SERP 产品分布
- `keyword_trend`：关键词趋势
- `product_traffic_terms`：ASIN 流量词反查
- `product_detail`：获取竞品 listing 详情

**CLI 通道：**
```bash
# 关键词详情
scripts/cli_call.sh KeywordRequest '{"keyword": "power bank"}'

# 关键词拓展
scripts/cli_call.sh KeywordExtends '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'

# 关键词搜索结果
scripts/cli_call.sh KeywordSearchResults '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'

# ASIN 流量词反查
scripts/cli_call.sh ASINRequestKeyword '{"asin": "B0CVM8TXHP", "pageIndex": 1, "pageSize": 50}'

# 产品详情
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'
```

### Step 3：关键词分级

将收集到的关键词按优先级分层：

| 层级 | 规则 | 投放位置 |
|------|------|----------|
| 🔴 Primary | 最高搜索量核心词 | Title（前置） |
| 🟡 Secondary | 中搜索量 + 高相关性 | Bullets（每条至少1个） |
| 🟢 Tertiary | 低搜索量/长尾词 | Description |
| ⚪ Backend | 未覆盖词 | Backend Search Terms |

### Step 4：生成 Listing 文案

按 FABE 结构（Feature → Advantage → Benefit → Evidence）撰写，详见 `references/listing-optimization-framework.md`。

**主标题 Main Title（硬约束 ≤75 字符，7.27 新规两段式）：**
`[Brand] + [Primary Keyword] + [Key Differentiator]`（其余信息全部后移）

**副标题 Subtitle：**
`[Secondary Keywords] + [Use Scenario] + [Benefit/Proof]`（承载场景词/次关键词/卖点证据）

**Bullets（5条，每条≤500字符）：**
- Bullet 1：最大卖点 + 核心关键词
- Bullet 2：核心使用场景 + 次级关键词
- Bullet 3：品质/材质 + 信任信号
- Bullet 4：包装清单/兼容性
- Bullet 5：售后保障/差异化

**Description（≤2000字符）：**
问题引入 → 功能展开（不重复 bullets）→ 行动号召

**Backend Keywords（≤250字节）：**
空格分隔，不重复，不包含品牌名

### Step 5：8 维度评分与关键词覆盖检查

评分标准详见 `references/listing-optimization-framework.md`。
覆盖检查清单详见 `references/keyword-coverage-checklist.md`。

输出覆盖报告：

```
| Keyword | Volume | In Title? | In Bullets? | In Description? | Status |
|---------|--------|-----------|-------------|-----------------|--------|
```

## MCP 通道

使用 Sorftime MCP 工具直接调用，适合交互式单条查询：

| 工具 | 用途 |
|------|------|
| `keyword_detail` | 关键词详情（搜索量/CPC/趋势） |
| `keyword_extends` | 关键词拓展 |
| `keyword_search_results` | 关键词 SERP 产品列表 |
| `keyword_trend` | 关键词历史趋势 |
| `product_detail` | 产品 listing 详情 |
| `product_traffic_terms` | ASIN 流量词反查 |

⚠️ 标注为 raw 的工具需通过 `sorftime_raw_call` 调用。

## CLI 通道

使用 `scripts/cli_call.sh` 调用，适合批量拉取数据：

| CLI 端点 | 用途 |
|----------|------|
| `KeywordRequest` | 关键词详情 |
| `KeywordExtends` | 关键词拓展 |
| `KeywordSearchResults` | 关键词 SERP |
| `ASINRequestKeyword` | ASIN 流量词反查 |
| `ProductRequest` | 产品详情 |

调用示例：
```bash
scripts/cli_call.sh KeywordRequest '{"keyword": "portable blender"}'
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'
```

## 输出格式

```markdown
# ✅ Listing 已生成

## 主标题（≤75字符）
[主标题文本]

## 副标题
[副标题文本]

## Bullet Points
1. [BENEFIT HEADER] — [文本]
2. ...

## Description
[描述文本]

## Backend Search Terms
[空格分隔关键词]

---

# 📊 优化评分

| 维度 | 得分 | 说明 |
|------|------|------|
| Title | /15 | ... |
| ... | ... | ... |
| **总分** | **/100** | ... |

## 关键词覆盖率：X%
[覆盖表]
```

## 详细方法论

- `references/listing-optimization-framework.md`：A9+COSMO 算法要点、8 维度评分标准、FABE 文案结构
- `references/keyword-coverage-checklist.md`：关键词覆盖检查清单

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
