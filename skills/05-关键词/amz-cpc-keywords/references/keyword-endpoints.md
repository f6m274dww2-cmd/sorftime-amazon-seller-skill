# Sorftime 关键词端点说明（12 个）

> 完整文档见 sorftime-data-cli/resources/amazon-keyword-api.md。
> 本文档为 amz-cpc-keywords 常用端点速查。

**Amazon Domains**: 1=US, 2=UK, 3=DE, 4=FR, 6=CA, 7=JP, 8=ES, 9=IT, 10=MX, 11=AE, 12=AU, 13=BR, 14=SA

---

## 常用端点速查

### 1. KeywordQuery — ABA 热门词查询

- **用途**：按关键词搜索 ABA 热门词列表，支持搜索量/排名过滤
- **消耗**：5 积分
- **参数**：`pattern`（含 keyword/NodeIdRange/RankCondition/SearchVolumeCondition）、`pageIndex`、`pageSize`
- **关键返回字段**：Keyword, Rank, SearchVolume, Cpc, CpcRange, ProductCount, RankChangeOfWeekly, SearchConversionRate, ShareClickRate, ShareConversionRate

```bash
scripts/cli_call.sh KeywordQuery '{"pattern": {"keyword": "power bank"}, "pageIndex": 1, "pageSize": 50}'
```

### 2. KeywordRequest — 关键词详情

- **用途**：单个关键词的完整详情（搜索量趋势、CPC 趋势、SERP 概况）
- **消耗**：1 积分
- **参数**：`keyword`
- **关键返回字段**：SearchVolume, Cpc, CpcRange, CpcTrend, ProductCount, SearchConversionRate, SearchResultOfFP, ShareClickRate, ShareConversionRate, Top3asin, AssociatedWithCategoryDetail

```bash
scripts/cli_call.sh KeywordRequest '{"keyword": "power bank"}'
```

### 3. KeywordExtends — 关键词拓展

- **用途**：从种子关键词拓展相关关键词
- **消耗**：5 积分
- **参数**：`keyword`、`pageIndex`、`pageSize`
- **返回**：关键词摘要对象数组。⚠️ 实测（2026-09-10）：KeywordExtends 返回的需求字段是 `ClickOf90D`/`SalesVolumeOf90D`（90天点击/销量），**无 `SearchVolume` 字段**；评分时用 ClickOf90D 作需求代理，CPC 字段单位为分（÷100=美元）

```bash
scripts/cli_call.sh KeywordExtends '{"keyword": "power bank", "pageIndex": 1, "pageSize": 100}'
```

### 4. KeywordSearchResults — 关键词 SERP 产品

- **用途**：查看关键词搜索结果页的产品列表（最近 15 天）
- **消耗**：5 积分
- **参数**：`keyword`、`positionType`（0=全部/1=自然/2=广告）、`pageIndex`、`pageSize`
- **关键返回字段**：Products（Title, ASIN, Price, Brand, RatingsCount, Rank, MonthlySales 等）

```bash
scripts/cli_call.sh KeywordSearchResults '{"keyword": "power bank", "pageIndex": 1, "pageSize": 50}'
```

### 5. CategoryRequestKeyword — 类目反查关键词

- **用途**：按类目 NodeId 反查相关 ABA 关键词
- **消耗**：1 积分
- **参数**：`nodeid`（叶子类目 NodeId）、`pageIndex`、`pageSize`

```bash
scripts/cli_call.sh CategoryRequestKeyword '{"nodeid": "7073960011", "pageIndex": 1, "pageSize": 100}'
```

### 6. ASINRequestKeyword — ASIN 流量词反查

- **用途**：查询 ASIN 在前 3 页获得曝光的关键词（最近 30 天）
- **消耗**：1 积分
- **参数**：`asin`、`pageIndex`、`pageSize`
- **关键返回字段**：ShowShare（流量占比）、PositionType、AdPosition、SearchPosition、Keyword（完整关键词对象）

```bash
scripts/cli_call.sh ASINRequestKeyword '{"asin": "B0CVM8TXHP", "pageIndex": 1, "pageSize": 100}'
```

### 7. KeywordProductRanking — 关键词历史排名

- **用途**：关键词历史月度搜索结果产品（最多 2 年）
- **消耗**：5 积分
- **参数**：`keyword`、`month`（US 站可选）、`page`

```bash
scripts/cli_call.sh KeywordProductRanking '{"keyword": "power bank"}'
```

### 8. ASINKeywordRanking — ASIN 关键词排名趋势

- **用途**：ASIN 在指定关键词下的历史排名变化（最多 2 年，仅 US 站）
- **消耗**：2 积分
- **参数**：`keyword`、`ASIN`、`queryStart`、`queryEnd`

```bash
scripts/cli_call.sh ASINKeywordRanking '{"keyword": "power bank", "ASIN": "B0CVM8TXHP"}'
```

---

## 关键词库管理端点

| 端点 | 用途 | 消耗 |
|------|------|------|
| `FavoriteKeyword` | 添加关键词到词库文件夹 | 1 |
| `ChangeFavoriteKeyword` | 移动/删除词库关键词 | 0 |
| `GetFavoriteKeyword` | 查询词库关键词 | 1 |

---

## MCP 工具对应关系

| CLI 端点 | MCP 工具 | 状态 |
|----------|----------|------|
| KeywordQuery | keyword_list | raw |
| KeywordRequest | keyword_detail | ✅ Registered |
| KeywordExtends | keyword_extends | ✅ Registered |
| KeywordSearchResults | keyword_search_results | ✅ Registered |
| CategoryRequestKeyword | category_keywords | raw |
| ASINRequestKeyword | product_traffic_terms | ✅ Registered |
| KeywordProductRanking | product_ranking_trend_by_keyword | raw |
| ASINKeywordRanking | product_ranking_trend_by_keyword | raw |
| FavoriteKeyword | favorite_keyword | raw |
| ChangeFavoriteKeyword | change_favorite_keyword | raw |
| GetFavoriteKeyword | get_favorite_keyword | raw |
