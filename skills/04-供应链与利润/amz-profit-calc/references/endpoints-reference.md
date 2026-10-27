# CLI 端点参考（amz-profit-calc）

> Amazon Domains: 1=US, 2=UK, 3=DE, ... 14=SA。金额为最小货币单位（US 站 1999 = $19.99）。
> 调用：`scripts/cli_call.sh <Endpoint> '<json>' [--domain N]`。

## ProductRequest — 单品详情（1 积分/ASIN，≤10 批量）
- 参数：`asin`(必填，逗号分隔 ≤10), `trend`(1含趋势), `queryTrendStartDt/EndDt`(yyyy-MM-dd)
- **利润测算核心取数**：
  | 字段 | 含义 |
  |---|---|
  | SalesPrice | 扣券后实付售价（算收入用） |
  | Price / ListPrice | 标价 / 划线价 |
  | FbaFee | FBA 配送费（FBA 时） |
  | FbaDetetail | FBA 费明细：[配送费, 1-9月仓储, 10-12月仓储] |
  | PlatformFee | 平台佣金 |
  | Profit | Amazon 费用后贡献 = 实付价 − FBA费 − 平台佣金；不含采购/头程/广告/退货 |
  | ProfitRate | Amazon 费用后贡献率 = Profit/实付价×100；不是净利润率 |
  | Weight | 重量 g（磅已换算 1lb≈453.6g） |
  | Size | 外箱尺寸 cm [最长,次长,最短] |
  | RatingsCount / Ratings | 评论数 / 星级 |
  | OnlineDate / OnlineDays | 上架日期 / 上架天数 |
  | IsFBA / BuyboxSellerAddress | 是否 FBA / Buy Box 卖家所在地 |
- 示例：
```bash
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'
```

## AsinSalesVolume — 官方披露变体销量（1 积分）
- 参数：`asin`(必填), `queryDate`(起始 yyyy-MM-dd, 默认近30天), `queryEndDate`, `page`
- 返回 `[[日期, 销量, 类型(1周销/2月销)], ...]`，用于算月销趋势
- 示例：
```bash
scripts/cli_call.sh AsinSalesVolume '{"asin": "B0CVM8TXHP"}'
```

## ProductVariations — 变体数据（1 积分）
- 参数：`asin`(必填), `pageIndex`, `isSalesVolume`(true 则消耗 2，含近15天披露变体销量)
- 用于套装/多件变体利润拆分
- 示例：
```bash
scripts/cli_call.sh ProductVariations '{"asin": "B0CVM8TXHP", "isSalesVolume": true}'
```

## 数据 → profit_calculator.py 映射

| API 字段 | 脚本参数 |
|---|---|
| SalesPrice/100 | `--price` |
| （用户/1688 估算）采购成本 | `--cost` |
| Weight/1000 | `--weight` |
| FbaFee/100 | `--fba-fee`（覆盖估算） |
| PlatformFee/100 | `--platform-fee`（优先）；缺失时才用 `--referral-rate` |
| AsinSalesVolume 月销 | `--monthly-sales` |
| Profit/100 | `--sorftime-profit`（用于口径校验，不作净利润） |

## MCP ↔ CLI 对照

| MCP 工具 | CLI 端点 |
|---|---|
| product_detail | ProductRequest |
| product_trend | ProductRequest(trend=1 + 日期) |
| product_variations | ProductVariations |
| （月销趋势） | AsinSalesVolume |
