# CLI 端点参考（amz-market-analysis）

> Amazon Domains: 1=US, 2=UK, 3=DE, 4=FR, 5=IN, 6=CA, 7=JP, 8=ES, 9=IT, 10=MX, 11=AE, 12=AU, 13=BR, 14=SA
> 金额为最小货币单位（US 站 1999 = $19.99）。调用：`scripts/cli_call.sh <Endpoint> '<json>' [--domain N]`。

## CategorySearchFromName — 名称搜类目（1 积分）
- 参数：`name`(必填)
- 返回候选类目数组（含 nodeId/name）。返回 0 个 → 反问用户换词；返回多个 → 取第一个并落盘候选。

## CategoryRequest — 类目 Best Seller Top100（5 积分）
- 参数：`nodeId`(必填), `queryStart`/`queryDate`(历史合并 yyyy-MM-dd, 跨度 3-40 天)
- 分析用取数：ListingSalesVolumeOfMonth / Price / SalesPrice / Brand / Ratings / RatingsCount / OnlineDate / FbaFee / ProfitRate（Amazon 费用后贡献率，不是净利润率）/ VariationASINCount / SellerCount / Weight / Size

## CategoryProducts — 类目全部热销品（5 积分）
- 参数：`nodeId`(必填), `page`, `range`(按 30 天销量降序取 N 个)
- 价格带分桶、品牌集中度、变体分布需要全量 → range 取 500-1000

## CategoryTrend — 类目历史趋势（5 积分）
- 参数：`nodeId`(必填), `trendIndex`(必填)
- 市场分析常用 trendIndex：
| 值 | 含义 |
|---|---|
| 0 | 销量趋势 |
| 1 | 品牌数趋势 |
| 2 | 卖家数趋势 |
| 3 | 均价趋势 |
| 4 | 平均评论数趋势 |
| 5 | 平均星级趋势 |
| 6/7/8 | 1/3/6 月新品份额趋势 |
| 9 | 亚马逊自营占比趋势 |
| 10 | FBM 占比趋势 |
| 11 | A+ 占比趋势 |
| 12 | 单品平均利润趋势 |
| 28-31 | Top3/5/10/20 listing 垄断指数 |
| 32-35 | Top3/5/10/20 品牌垄断指数 |
| 36-39 | Top3/5/10/20 卖家垄断指数 |
- 数据：`[YYYYMM, value, ...]`；金额为最小单位，百分比为数值（50=50%）

## ProductSearch — 类目多维搜索（5 积分）
- 参数：`nodeId` / `priceRangeMin/Max` / `starRangeMin/Max` / `commentCountRangeMin/Max` / `variationCountRangeMin/Max` / `page`
- 用于：价格带×星级交叉、价格带甜区、变体分布

## SimilarProductFeature — 同类目特征聚合（2 积分）
- 参数：`productName`(必填，中英均可)
- 返回 Feature / ProductCountRatio / MonthlySalesRatio / FeatureDescription
- 用于：标题特征频率、差异化方向、特征缺口

## ProductRequest — Top 单品详情（1 积分/ASIN）
- 参数：`asin`(必填，≤10 批量)
- 抽取 Top10 单品：定价策略、品牌、变体结构、FBA 费、上架天数

## MCP ↔ CLI 对照

| MCP 工具 | CLI 端点 |
|---|---|
| category_name_search | CategorySearchFromName |
| category_report | CategoryRequest |
| category_trend | CategoryTrend |
| category_keywords | （类目词库，走 MCP/keyword 通道） |
| category_search_from_top_node | CategoryTree（按顶层 NodeId 过滤） |
| similar_product_feature | SimilarProductFeature |
| product_search | ProductSearch |
| product_detail | ProductRequest |

## 积分预算建议

一份标准市场分析：CategorySearchFromName(1) + CategoryRequest(5) + CategoryProducts(5) + CategoryTrend×6(30) + SimilarProductFeature(2) + ProductRequest Top10(10) ≈ 53 积分。
