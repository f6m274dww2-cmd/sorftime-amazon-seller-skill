# 关键词竞争度/搜索量评分方法

## 核心模型：Opportunity Index

```
Opportunity Index = μ₁ × Search Volume Score + μ₂ × Click Concentration (inverse)
                  + μ₃ × Bid Affordability Score + μ₄ × Associated ASIN Quality Score
                  + μ₅ × Seasonal Velocity + μ₆ × Ad Penetration Score
                  + μ₇ × Supply-Demand Ratio ⭐
```

> 来源：sorftime-seller-agent methodology-cards/comprehensive/keyword-strategy.md

---

## 各维度评分说明

### 1. Search Volume Score（搜索量得分）

- 计算方式：min-max 归一化的 log(月搜索量)
- 目的：防止头部词在评分中占绝对主导
- 数据字段：`SearchVolume`（30 天搜索量）

### 2. Click Concentration 反向得分

- 计算方式：Top 3 ASIN 点击占比越低，得分越高
- 低集中（<25%）= 买家浏览比较，新卖家机会大
- 高集中（>60%）= 品牌垄断，新进入者转化极难
- 数据字段：`ShareClickRate`（Top 3 点击占比）

### 3. Bid Affordability Score（出价可负担得分）

- 计算方式：目标利润率 / 建议 CPC 出价
- 比值越高越好
- 数据字段：`Cpc` / `CpcRange`

### 4. Associated ASIN Quality Score

- 查看 SERP 前 3 页竞品的质量水平
- 竞品 review 数少/评分低 = 容易超越
- 数据字段：KeywordSearchResults 返回的产品列表

### 5. Seasonal Velocity（季节性速度）

- 搜索量增长趋势
- 3/6/12 月复合增长率
- 数据字段：`SearchVolumeGrowthRateTrend`

### 6. Ad Penetration Score（广告渗透率）

- SERP 中广告位占比
- >60% 广告位 = 流量纯广告驱动，自然排名积累困难
- 数据字段：KeywordSearchResults 中 positionType=2 的产品占比

### 7. Supply-Demand Ratio ⭐（供需比，Sorftime 独占）

- 计算方式：搜索量 / 供应 ASIN 数
- >10 = 需求远超供给，优先监控
- 数据字段：`SearchVolume` / `ProductCount`

---

## 竞争度等级划分

| 等级 | 搜索量范围 | Top3 点击占比 | CPC | 供需比 | 建议 |
|------|-----------|--------------|-----|--------|------|
| 🔴 高竞争 | >50000 | >60% | >$2.0 | <2 | 谨慎进入，需强供应链 |
| 🟡 中竞争 | 10000-50000 | 30-60% | $0.8-2.0 | 2-10 | 可进入，需差异化 |
| 🟢 低竞争 | <10000 | <30% | <$0.8 | >10 | 蓝海机会，优先抢占 |

---

## "灰区关键词"识别

被硬阈值过滤掉但实际有价值的关键词：

| 特征 | 说明 |
|------|------|
| 搜索量 ~800 但点击集中度极低（Top 3 仅 20%） | 小而美的词，"搜索量>1000"硬阈值会误杀 |
| CPC $1.50 但转化率 15%（品类均值 2 倍） | 纯 CPC 过滤会误杀，实际 ACOS 可能更低 |
| 搜索量 2000-4000，竞品覆盖 <40% | 竞争者尚未投入，先发优势 |

---

## 风险信号

| 信号 | 含义 | 应对 |
|------|------|------|
| 高 Opportunity Index 但 Click Concentration >80 | 点击过度集中，机会可能是虚假的 | 验证是否被品牌词垄断 |
| 季节性 >70 | 淡季广告效果大幅下降 | 仅在旺季前投放 |
| Ad Penetration >60% | SERP 全是广告位 | 自然排名难突破，需高预算 |
| SPR >1.5 | 广告驱动型结果 | 新卖家自然排名几乎无机会 |

---

## 评分输出模板

```markdown
## 关键词竞争度评估

| Keyword | Search Volume | CPC | Click Concentration | Supply-Demand Ratio | Competition Level | Recommendation |
|---------|--------------|-----|---------------------|---------------------|-------------------|----------------|
| power bank | 45,000 | $1.85 | 62% | 1.2 | 🔴 High | 谨慎 |
| slim power bank 10000mah | 8,500 | $1.20 | 28% | 8.5 | 🟢 Low | 优先 |
| ... | ... | ... | ... | ... | ... | ... |
```


## 指标口径补充

- `search_conversion_rate`：平台关键词搜索转化指标，不是广告 CVR。
- `click_conversion_rate_90d`：只有在 `click_90d > 0` 时才有解释意义；点击为 0 时不得写成“转化率为 0”。
- `cpc` / `cpc_range`：Sorftime 参考出价，不是广告账户实际 CPC。
- `share_click_rate`：头部点击集中度，不等于广告曝光份额。
- 不同接口返回的排名必须保留来源与 `Pos X/Y` 分母，不能混算。
