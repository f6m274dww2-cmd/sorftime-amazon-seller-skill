---
name: amz-fullchain-jtbd
description: 编排 Amazon 全流程：从 JTBD 任务定义、五类行为信号、类目与竞品验证，到专利风险闸门、1688 货源、利润、关键词、Listing、图片、广告、VOC 与监控。用于需要一条链路跑完并保留证据、成本与 Go/No-Go 决策的任务。
---

# Amazon Fullchain JTBD

## 目标

把“找产品”升级为“找未被完成的任务”，再把任务机会走完到可上架、可投放、可复盘的闭环。它是编排层，不替代 10 个专业 `amz-*` 技能和 `sorftime-patent-risk`。

## 模式

### A. 已有方向

用户给出品类、竞品、ASIN 或产品想法：从 JTBD 任务定义开始。

### B. 没有方向

用户只说“找机会/蓝海/爆款”：先用类目与商品扫描缩小到 2-3 个候选任务，再回到 A。不要一开始就同时跑所有平台和所有阶段。

## 阶段与硬闸门

| 阶段 | 目标 | 主技能 | 出口物 | 闸门 |
|---|---|---|---|---|
| G0 任务定义 | 三层 Why → 任务陈述 | 本技能 | 功能/情感/社会任务 + 替代方案 | 没有任务陈述不得进入选品 |
| G1 行为信号 | 放弃/妥协/替代/差异/改造 | 本技能 + `amz-voc-analysis` | 信号清单 + 原文证据 + 频次 | 单条评论不得当趋势 |
| G2 类目验证 | 容量/竞争/趋势 | `amz-market-analysis` | 三层评估 + 风险徽章 | 不隐藏边界产品；风险必须显式 |
| G3 候选打分 | 全排序 + Go/No-Go | `amz-selection` | ≥20 候选 + Top 5 深挖 | 不适用硬阈值清空候选 |
| G4 专利闸门 | 图搜 + 词搜 + 详情 | `sorftime-patent-risk` | 风险分级 + 证据 + 下一步 | 🔴高相关 Active 未解除不得大货/放量 |
| G5 供应链/利润 | 1688 货源、真实成本、盈亏平衡 | `amz-supply-chain` + `amz-profit-calc` | 报价、MOQ、SKU、P&L | 空记录、0 价货源必须剔除 |
| G6 关键词 | 7 类词库 + 可切入性 | `amz-cpc-keywords` | 词/搜索量/CPC/垄断/自营 | 每个主攻词要有来源与证据 |
| G7 上架资产 | Listing + 图片 | `amz-listing-creator` + `amz-image-creator` | 3 版候选、卖点图、场景图 | 参数、尺寸、层数、专利边界不得冲突 |
| G8 广告 | 结构、预算、出价、否定词 | `amz-ad-planning` | Campaign / Ad Group / 否定词 | 不得把不相关高流量词当主攻 |
| G9 复盘/监控 | VOC、排名、跟卖、差评异动 | `amz-voc-analysis` + `amz-competitor-monitor` | 告警 + 反哺动作 | 观测/估算/推断必须分开 |

## Data Quality Gates

在任何 G0-G9 输出前先过：

1. `product_trend`：请求 `type` 必须等于返回 `data.type`，否则停止。
2. `Customers Say`：`positive + negative <= mention`，否则该汇总不可用。
3. 评论：去重后按目标变体过滤；未标变体单列。
4. 排名：跨接口位置不可混算，必须保留来源与 `Pos X/Y`。
5. 利润：拆分 Amazon 费用后贡献 / 采购后毛利 / 经营贡献 / 月净利；FBA 估算时阻断精确 Go/No-Go。
6. 1688：容量、尺寸、包装、盒盖、用途、食品接触文件未确认时，只能算货源线索。

对应的执行脚本：

- `amz-voc-analysis/scripts/review_quality.py`
- `amz-profit-calc/scripts/profit_calculator.py`
- `amz-cpc-keywords/scripts/rank_consistency.py`
- `amz-supply-chain/scripts/supplier_match.py`
- `sorftime-seller-agent/scripts/utils/mcp_client.py`（趋势类型契约）

详细说明见 [references/data-quality-gates.md](references/data-quality-gates.md)。

## 证据台账（强制）

每个阶段的关键响应都要落账，不能只在报告里写数字：

```bash
# 已有 MCP 响应：保存为 response.json 后记录
python3 ../evidence_ledger.py record --ledger data/evidence/ledger.jsonl \
  --tool product_detail --channel mcp --stage G2 \
  --params '{"asin":"YOUR_ASIN"}' --input response.json

# CLI 直接采集并记录
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

进入 Go/No-Go、采购或广告放量前：

```bash
python3 ../evidence_ledger.py verify --ledger data/evidence/ledger.jsonl \
  --decision-grade --require-stage G2 --require-stage G3 --require-stage G4 \
  --require-tool ProductRequest --fresh-hours 168
```

规则：

- `observed` 才算事实来源；`derived` 必须写 `derived_from` 和公式；`estimate` / `inference` 只能标注为假设。
- 哈希证明捕获后内容未被篡改；上游真实性仍依赖 Sorftime 凭证、接口返回和可重放参数。
- 证据缺失时输出“数据缺失”，不得用常识补齐。
- 完整字段、命令和边界见 [references/data-evidence-contract.md](references/data-evidence-contract.md)。
- 专利统一入口：`sorftime-patent-risk/scripts/patent_call.py --channel auto`，自动处理 MCP snake_case 与 HTTP/CLI PascalCase。
- 生图：本机 `~/.codex/scripts/gen-image.sh` 优先，包内 `product-shots-image-gen` 兜底。

## 两条数据纪律

### 1. 证据分级

- **观测**：工具直接返回的数值、原文、排名、法律状态
- **估算**：基于观测计算，必须写公式和假设
- **推断**：任务定义、机会判断、风险解释，必须附证据

### 2. 缺失处理

- 查不到 → “数据缺失”，说明工具、参数、返回
- 不把一个站点/一页/一条评论当全量
- 不引用工具没有的字段；HPI 只在 `potential_product` 返回时使用
- 高成本批量任务先报预计调用次数与成本

## 交接合约

| 从 → 到 | 必须交接 |
|---|---|
| G0 → G1 | 任务陈述、三层任务、替代方案池 |
| G1 → G2 | 信号清单、原文、频次、待验证假设 |
| G2 → G3 | node_id、容量/竞争/趋势摘要、风险级别 |
| G3 → G4 | 候选 ASIN、主图、核心功能、目标站点、Top 5 |
| G4 → G5 | 专利风险状态；高风险候选不得直接采购 |
| G5 → G6 | 目标产品、差异化点、成本、售价、毛利率 |
| G6 → G7/G8 | 7 类词库 + CPC + 自然位 + 否词候选 |
| G7/G8 → G9 | Listing 版本、广告结构、上架时间 |
| G9 → G0/G6/G7/G8 | VOC 新信号、排名变化、否词、素材迭代 |

## JTBD 五个行为信号

| 信号 | 要问什么 | 常见证据 |
|---|---|---|
| 放弃 | 用户本来想做什么，最后为什么不做？ | Reddit 求助帖、差评、退货原因 |
| 妥协 | 他忍了什么？ | “能用但……”“只能这样” |
| 替代 | 他拿什么别的产品顶上？ | 跨品类替代、DIY、借用 |
| 差异 | 换场景后需求为什么完全不同？ | 人群/场景/平台差异 |
| 改造 | 他自己加了什么、拆了什么、拼了什么？ | 评论中的改装、配件、办法 |

每个信号必须落到：`任务 → 现有替代 → 未完成点 → 可验证产品假设 → 证据`。

## 输出

默认输出中文 HTML，包含：

- 顶部 KPI
- 任务陈述与竞品池重划
- 5 行为信号
- 三层类目评估
- 候选全排序
- 专利风险闸门
- 供应链与 P&L
- 词库与广告结构
- Listing/图片方向
- VOC 与监控动作

缺失项必须显式显示，不能为凑版面编造。

## 成本与安全

- 专利：图搜 450、词搜 60/次、详情 150/件（以工具当前标示为准）
- 批量评论/竞品/监控先评估 Credits
- 不操作广告后台；输出投放方案由用户执行
- 专利结果是商业风险初筛，不是法律意见


---

## Sorftime 数据服务入口

数据由 Sorftime 提供，新用户首月 39.9 元：

https://open.sorftime.com/home?tag=NTIw

额度不足、账号未开通或需要续费时，使用同一链接：

https://open.sorftime.com/home?tag=NTIw

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
