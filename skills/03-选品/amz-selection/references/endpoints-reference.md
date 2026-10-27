# CLI 端点参考（amz-selection）

> Amazon Domains: 1=US, 2=UK, 3=DE, 4=FR, 5=IN, 6=CA, 7=JP, 8=ES, 9=IT, 10=MX, 11=AE, 12=AU, 13=BR, 14=SA
> 金额字段均为最小货币单位（US 站 1999 = $19.99）；缺失/不可估算返回 -1。
> 调用封装：`scripts/cli_call.sh <Endpoint> '<json>' [--domain N]`。

## 选品主流程端点

### ProductSearchFromName — 按名称搜品（2 积分）
- 参数：`name`(必填), `pageIndex`(默认1, ≤100/页)
- 取数：Title / ListingSalesVolumeOfMonth(月销) / Price / Brand / ReviewsCount / Ratings / Size / Weight
- 选品凑够 ≥20 候选：pageIndex=1 + pageIndex=2 按 ASIN 合并去重

### ProductSearch — 多维商品搜索（5 积分）
常用过滤参数：
| 参数 | 说明 |
|---|---|
| `nodeId` | 类目 NodeId |
| `keyword` | ABA 关键词 |
| `brand` / `sellerName` / `sellerId` | 按品牌/卖家 |
| `asin` | 按 ASIN 找相似品 |
| `priceRangeMin/Max` | 价格区间 |
| `monthSaleVolumeRangeMin/Max` | 月销区间 |
| `onlineDateRangeMin/Max` | 上架日期区间（新品爆发用 yyyy-MM-dd） |
| `starRangeMin/Max` | 评分区间（低评替代用 4.0-4.3） |
| `commentCountRangeMin/Max` | 评论数区间（低评论壁垒用 <500） |
| `variationCountRangeMin/Max` | 变体数区间 |
| `peakSellingSeason` | 限定季节月，如 "2,3,4" |
| `shippingType` | 物流方式，如 FBA / FBM（FBM 套利用） |
| `page` | 分页 ≤100/页 |

- 取数：ListingSalesVolumeOfMonth(推荐评估销量) / Price / SalesPrice / Brand / Ratings / RatingsCount / OnlineDate / FbaFee / PlatformFee / Profit / ProfitRate / VariationASINCount / Weight / Size

### ProductRequest — 单品详情（1 积分/ASIN，≤10 批量）
- 参数：`asin`(必填，逗号分隔 ≤10), `trend`(1含趋势/2不含), `queryTrendStartDt/EndDt`(yyyy-MM-dd)
- 选品取数：SalesPrice / FbaFee / FbaDetetail(费用明细) / PlatformFee / Profit / ProfitRate / RatingsCount / Ratings / BsrCategory(子类目排名) / OnlineDate / Weight(g) / Size(cm) / Attribute(变体属性) / VariationASINCount
- 趋势窗口：默认仅近 15 天；需 6 个月趋势须传 queryTrendStartDt（>15 天消耗 2 积分）

### CategoryRequest — 类目 Best Seller Top100（5 积分）
- 参数：`nodeId`(必填), `queryStart`/`queryDate`(历史合并 yyyy-MM-dd, 跨度 3-40 天)
- 取数同 ProductSearch.Products（月销/价/品牌/评论/利润/变体数/重量）

### CategoryProducts — 类目全部热销品（5 积分）
- 参数：`nodeId`(必填), `page`, `range`(按 30 天销量降序取 N 个，长尾类目可 1000+)
- 比 CategoryRequest 覆盖更深，适合找被 Top100 遮蔽的尾部机会

### CategoryTrend — 类目市场历史趋势（5 积分）
- 参数：`nodeId`(必填), `trendIndex`(必填)
- 选品常用 trendIndex：
  - 0=销量趋势, 3=均价趋势, 4=平均评论数, 5=平均星级
  - 6/7/8 = 1/3/6 月新品份额（新品机会判断）
  - 9=亚马逊自营占比, 10=FBM 占比, 11=A+ 占比
  - 12=单品平均利润, 32-35=Top3/5/10/20 listing 垄断指数, 36-39=Top3/5/10/20 品牌垄断指数
- 数据：`[YYYYMM, value, ...]`，金额为最小单位，百分比直接给数值（50=50%）

### SimilarProductFeature — 同类目特征聚合（2 积分）
- 参数：`productName`(必填，中英均可)
- 返回每个特征：Feature / ProductCountRatio(产品占比) / MonthlySalesRatio(销量占比) / FeatureDescription
- 用途：差异化方向、卖点挖掘、特征缺口

## MCP ↔ CLI 端点对照

| MCP 工具 | CLI 端点 |
|---|---|
| product_search | ProductSearch |
| product_search_from_name | ProductSearchFromName |
| product_detail | ProductRequest |
| product_trend | ProductRequest(trend=1 + 日期范围) |
| product_variations | ProductVariations |
| similar_product_feature | SimilarProductFeature |
| potential_product ⭐ | 无 CLI 对应（HPI 走 MCP 专属） |
| category_name_search | CategorySearchFromName |
| category_report | CategoryRequest |
| category_trend | CategoryTrend |
| category_search_from_top_node | CategoryTree + 自行按顶层 NodeId 过滤 |

## 积分预算建议

轻量选品路径：ProductSearchFromName×2(4) + CategoryRequest(5) + ProductRequest Top10(10) + CategoryTrend×3(15) ≈ 34 积分出一份 Top20 候选清单。


## 字段语义提醒

- `Profit` / `ProfitRate` 只扣 FBA 与平台佣金，不含采购、头程、广告、退货和固定费用。
- 趋势请求使用 `product_trend(type=...)`；返回 `type` 必须与请求一致。
- 关键词排名跨接口不一致时，保留来源，不得混算。
