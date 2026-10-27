---
name: amz-supply-chain
description: 1688供应链找货与货源对比 Skill。支持1688找工厂/找货源、按名称/图片搜品、货源候选筛选与对比、跨平台价格差分析（Amazon vs 1688）、供应商评估与利润测算。触发词包括：找货源、找工厂、1688、供应链、sourcing、supplier、wholesale、批发价、货源对比、价格差、cross-platform gap、product sourcing、find supplier、price arbitrage、货源评估、供应商筛选、一件代发、dropshipping、MOQ、起订量。默认站点 Amazon US(domain=1)，1688 端点固定 domain=601。
---

# amz-supply-chain — 1688 供应链找货

> 链路位置：第 3 环「找货源」。上游 ← amz-market-analysis（目标 ASIN/产品名）；下游 → amz-profit-calc（1688 采购成本 + Amazon 售价/FBA 费）。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

在执行任何数据调用之前，先运行通道检测脚本：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据输出 JSON 的 `recommended_channel` 字段选择执行通道：
- `mcp` → 走 MCP 通道（见下方 MCP 通道章节）
- `cli` → 走 CLI 通道（见下方 CLI 通道章节）
- 无凭证 → 按脚本输出引导用户注册配置

> **重要**：1688 端点的 domain 固定为 **601**，不是默认的 1（Amazon US）。所有 1688 相关调用必须传 `--domain 601`。Amazon 侧价格参考仍用 domain=1。

## 🔴 供应商合格门禁

1688 搜索成功只代表找到线索，不代表找到合格货源。候选进入利润测算前，必须逐项核对：

- 容量（oz/ml）
- 长宽高尺寸
- 包装数量（如 50 盒 + 50 盖）
- 盒盖是否配套、颜色是否一致
- 微波炉 / 冷冻 / 洗碗机适用性
- 食品接触材料与合规文件
- 布尔字段严格解析：`false/no/0/否/不支持/无` 只能判为否；未知字符串判为 `UNKNOWN`，必须阻断，不能因非空字符串直接放行
- 容量/尺寸拒绝 bool、NaN、Infinity、非正数和畸形字符串；包装数量只接受正整数，`50.9` 或 `"50.0"` 不得截断为 50
- 容差必须是非 bool、有限且 >= 0；非法容差直接判 `NOT_QUALIFIED`

可用脚本做硬比较：

```bash
python3 scripts/supplier_match.py --target target_sku.json --candidate candidate.json
```

只有 `qualified_for_profit_calc=true` 的候选才能把价格带入利润模型。否则只能列为“线索”，不能进入 Go/No-Go 成本。

## MCP 通道

Sorftime MCP 中 1688 相关工具如下（✅ 为已注册工具，⚠️ 需通过 `sorftime_raw_call` 透传）：

| 工具名 | 状态 | 用途 |
|--------|------|------|
| `ali1688_similar_product` | ✅ Registered | 按 Amazon 产品在 1688 找同类货源/批发供应商 |
| `ali1688_product_search` | ⚠️ raw | 1688 多维产品搜索（按类目/供应商类型/销量等筛选） |
| `ali1688_product_search_from_name` | ⚠️ raw | 1688 按产品名称搜索 |
| `ali1688_product_search_from_image` | ⚠️ raw | 1688 以图搜货 |
| `ali1688_product_request` | ⚠️ raw | 1688 产品详情 |
| `ali1688_product_variations` | ⚠️ raw | 1688 产品 SKU 变体数据 |
| `ali1688_category_tree` | ⚠️ raw | 1688 类目树 |

**⚠️ raw 工具调用方式**：通过 `sorftime_raw_call` 透传，示例：
```json
{
  "tool_name": "ali1688_product_search_from_name",
  "arguments": {"Name": "transparent acrylic double-sided tape"}
}
```

**Amazon 侧价格参考工具**（domain=1）：
- `product_detail`（✅）— 获取 Amazon ASIN 售价、FBA 费用、利润率
- `product_search`（✅）— 按关键词/类目搜索 Amazon 竞品价格

### MCP 通道典型工作流

1. 输入 Amazon ASIN 或产品名称
2. MCP `product_detail`（或 `product_search`）获取 Amazon 售价、月销量、FBA 费用
3. MCP `ali1688_similar_product` 或 `ali1688_product_search_from_name` 在 1688 找同类货源
4. MCP `ali1688_product_request` 查看候选供应商详情
5. MCP `ali1688_product_variations` 获取 SKU 批发价/库存/尺寸重量
6. 计算 Amazon vs 1688 价格差，输出货源候选清单 + 利润测算

## CLI 通道

CLI 通道使用 `scripts/cli_call.sh` 调用 Sorftime CLI。1688 端点固定 `--domain 601`，Amazon 端点用 `--domain 1`。

### 1688 端点（domain=601）

| 端点 | 消耗请求 | 用途 |
|------|---------|------|
| `ProductSearchFromName` | 2 | 按名称搜品 |
| `ProductSearchFromImage` | 2 | 以图搜货 |
| `ProductSearch` | 5 | 多维筛选搜品（20+ 过滤条件） |
| `ProductRequest` | 1 | 产品详情 |
| `ProductVariations` | 1 | SKU 变体（批发价/库存/尺寸/重量） |
| `CategoryTree` | 5 | 类目树（返回约 10MB，建议长超时） |
| `CoinQuery` | 0 | 查本月剩余 Credits |
| `CoinStream` | 0 | 查 Credits 消耗明细 |
| `RequestStreamMonth` | 0 | 查请求额度 |

### CLI 调用示例

```bash
# 按名称搜 1688 货源
scripts/cli_call.sh ProductSearchFromName '{"Name": "transparent acrylic double-sided tape"}' --domain 601

# 多维筛选：Super Factory + 服务分≥4.5 + 近30天销量≥50
scripts/cli_call.sh ProductSearch '{"Page":1, "SupplierType":2, "ServiceScoreMin":4.5, "Recent30DaySaleMin":50}' --domain 601

# 查 1688 产品详情
scripts/cli_call.sh ProductRequest '{"ProductId": "789542752062"}' --domain 601

# 查 SKU 变体价格/库存/尺寸重量
scripts/cli_call.sh ProductVariations '{"ProductId": "789542752062"}' --domain 601

# 以图搜货（用 Amazon 主图 URL）
scripts/cli_call.sh ProductSearchFromImage '{"ImageUrl": "https://example.com/product.jpg", "Page": 1}' --domain 601

# Amazon 侧参考：查 ASIN 售价/FBA/利润
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}' --domain 1
```

## 输出

- **货源候选清单**：供应商名、1688 链接、批发价区间、起订量、服务分、30天销量、复购率、是否一件代发
- **价格差分析**：Amazon 售价 vs 1688 批发价，计算毛利率 = (Amazon 售价 - 1688 成本 - FBA 费 - 平台佣金) / Amazon 售价
- **供应商评估**：按 [supply-chain-methodology.md](references/supply-chain-methodology.md) 的评分维度输出排名

## 详细参考

- [1688 端点完整参数与返回字段](references/1688-endpoints.md)
- [供应链方法论：货源对比评分维度与价格差分析方法](references/supply-chain-methodology.md)

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
