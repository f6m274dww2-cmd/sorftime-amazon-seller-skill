---
name: amz-profit-calc
description: Sorftime 亚马逊利润测算 / 隐赚分析。当用户要算利润、算 FBA 费用、算盈亏平衡点、做定价策略、判断隐赚指数/HPI、找轻量小而美高利润品、测算单均毛利净利、评估某 ASIN 能不能赚钱，或说"利润测算/利润计算/FBA费用/佣金/盈亏平衡/保本销量/隐赚/隐赚指数/HPI/轻量利润/小而美/定价/毛利/净利/利润表/profit calculation/FBA fee/break-even/invisible profit/HPI/lightweight profit/pricing strategy/margin"时使用。融合隐赚指数、轻量利润、定价位置方法论，用 ProductRequest 取真实价格/排名/费用数据，输出利润测算表（成本/费用/毛利/净利/盈亏平衡销量/隐赚评分）。默认 Amazon US，支持多站点。
---

# amz-profit-calc — 利润测算 / 隐赚

给一个 ASIN（或一组假设成本/售价）拆解利润账。**必须区分：Amazon 费用后贡献、采购后毛利、经营贡献、月净利。**

> 链路位置：第 4 环「利润测算」。上游 ← amz-supply-chain（采购成本）；下游 → amz-cpc-keywords（go 后建词库）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

开始前先运行：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


按 `recommended_channel` 选 MCP 或 CLI 通道。默认 site=US（domain=1）。

## 典型流程

1. **取真实数据**：售价、`FbaFee`、`PlatformFee`、Weight、月销。
2. **核对 Sorftime `profit`**（旧字段名 `gross_profit`）：它通常等于 `售价 - FBA - 平台佣金`，只能视为 Amazon 费用后贡献。用 `--sorftime-profit` 校验。
3. **补真实到岸成本**：采购 + 头程 + 包装，不能用 1688 搜索价直接替代。
4. **跑测算**：
   ```bash
   python3 scripts/profit_calculator.py      --price 24.99 --landed-cost 6.50 --weight 2.009      --fba-fee 8.90 --platform-fee 3.06      --monthly-sales 8237 --sorftime-profit 13.03
   ```
5. **出利润表**：Amazon 费用后贡献 / 采购后毛利 / 经营贡献 / 月净利 / 决策状态。
6. **来源未核实时必须阻断**：数值存在不等于已验证。
   - 只有 `--price-source verified`、`--fba-source verified`、`--platform-source verified`、`--landed-cost-source verified`、`--monthly-sales-source verified` 才可进入正式 Go/No-Go。
   - 人工输入但未标记来源 → `USER_INPUT_UNVERIFIED` → `BLOCKED`。
   - 公式估算 → `ESTIMATED` → `PROVISIONAL`。

公式见 [references/profit-formula.md](references/profit-formula.md)。

---

## MCP 通道

- `product_detail` — 取 price / fba_fee / platform_fee / profit / profit_rate / review_count / weight_g / package_size_cm
- `product_trend` — 取 6 个月销量/价格趋势（判断盈利可持续性）
- `product_variations` — 变体矩阵（算套装/多件变体利润）

---

## CLI 通道

端点文档见 [references/endpoints-reference.md](references/endpoints-reference.md)。

```bash
# 1. 取单品真实价格/FBA费/佣金/利润（最关键一步）
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'

# 2. 取官方披露的变体销量历史（算月销）
scripts/cli_call.sh AsinSalesVolume '{"asin": "B0CVM8TXHP"}'

# 3. 取全部变体（套装/多件 SKU 利润）
scripts/cli_call.sh ProductVariations '{"asin": "B0CVM8TXHP"}'
```

拿到 SalesPrice / FbaFee / 月销后，喂给本地测算脚本：

```bash
# 用真实拉到的 FBA 费覆盖估算
python3 scripts/profit_calculator.py \
  --price 24.99 --cost 6.5 --weight 0.35 \
  --fba-fee 4.75 --monthly-sales 800 --return-rate 0.05

# 只看公式样例
python3 scripts/profit_calculator.py --json
```

非 US 站点加 `--domain <N>`。

---

## 输出规范

利润测算表必须包含：

| 项目 | 来源 |
|---|---|
| 售价 / 采购成本 | 用户输入 或 ProductRequest.SalesPrice |
| FBA 配送费 | ProductRequest.FbaFee（优先）/ 估算 |
| 平台佣金(Referral) | ProductRequest.PlatformFee |
| 广告成本(估 ~15%) | 假设，标注 |
| Amazon 费用后贡献 | 售价 − 真实 FBA − 平台佣金 |
| 采购后毛利 | Amazon 费用后贡献 − 到岸成本 |
| 广告/退货计提 | 显式假设 |
| 经营贡献 | 采购后毛利 − 广告 − 退货计提 |
| 月净利 | 经营贡献 × 月销 − 固定成本；输入不全时不得精确化 |
| 决策状态 | READY / PROVISIONAL / BLOCKED |
| 隐赚评分 | 本地代理分（官方 HPI 走 MCP potential_product） |
| go / caution / no-go | 综合净利 + 退货敏感性 |

⚠️ 所有利润数字是**估算**；FBA 费必须以官方 Revenue Calculator 复核（尤其大件/异形）；广告占比、退货率按类目假设，须显式标注 `[ASSUMED]`。

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
