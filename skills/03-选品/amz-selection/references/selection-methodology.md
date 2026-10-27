# 选品方法论与评分体系（amz-selection）

> 融合 seller-agent methodology-cards（blue-ocean-finder / low-review-winner / seasonal-position / new-product-burst / fbm-arbitrage / poor-listing-grab）+ suite/references/selection.md + closed-loop-selection.md。
> 核心原则：**全排序（full ranking）而非硬阈值过滤**——边界产品不消失，卖家自己决策。

## 一、为什么不用硬阈值

传统工具 `minPrice>=$20 AND reviews<100` 会把 $19.99、评论 120 的好产品直接扔掉。Sorftime 的做法是：每个候选在所有维度都打分，按综合指数排序，全部可见。本 Skill 沿用这一原则。

## 二、六大选品指数

### 1. HPI 隐赚指数（蓝海）
```
HPI = η1×需求热度 + η2×供给稀疏度 + η3×利润潜力 + η4×评论壁垒(反向)
    + η5×品牌真空 + η6×增长可持续性 + η7×场景可描述性 + η8×产品复杂度(反向)
```
- 供给稀疏度 ⭐ = 1 /（每 $1000 营收对应的 ASIN 数），供给越少分越高
- 品牌真空 ⭐ = 无品牌流量占比 × 搜索结果中无品牌页面占比（>70% 为强入场信号）
- 典型高 HPI 画像：搜索量 2000-8000、同关键词 ASIN <50、品牌真空 >70%、利润潜力 >50%
- CLI 无直接 HPI 端点；MCP 走 `potential_product`。CLI 通道用 ProductSearch/CategoryRequest 拉全量后自行按上述维度归一化打分。

### 2. 替换机会指数（高销量低评分）
```
替换机会指数 = 月销量 × (5 − 评分) × 评论数修正因子
```
- 高销量 + 评分显著低于类目均值（低 0.5+）= 需求已被验证、产品体验差 → 做改进版截流
- 灰区甜区：月销 800-1200、评分 4.0-4.3，硬阈值工具会漏
- ⚠️ 不做专利检测，入场前必须独立查专利；差评集中在"功能缺失"而非"质量缺陷"时改造成本高

### 3. 季节景气指数
```
景气指数 = 峰谷比得分(40%) × 趋势加速度(40%) × 可行动窗口(20%)
```
- 峰谷比不必卡 3.0x；看"今年趋势加速度"是否领先去年（领先 2-3 个月正是备货信号）
- 可行动窗口 = 距峰值月数；2-3 个月内立即行动，4-6 个月计划不急，已到峰值前夜建议放弃
- 风险：旺季流量集中在峰值前后 60 天，其余时间近乎零流量——按"旺季 ROI"而非"全年 ROI"算账
- CLI 端点 `ProductSearch.PeakSellingSeason` 可按月限定季节品；`CategoryTrend`(index 0) 看 12 个月销量曲线

### 4. 新品爆发指数
```
新品爆发指数 = 月销量 / 上架天数 × 增长加速度（近期日销 / 早期日销）
```
- 7 天爆量苗子应排在 28 天稳步爬升者前面——硬阈值按"月销"排会误判
- CLI：`ProductSearch` 用 `OnlineDateRangeMin/Max` 圈定上架 30/60/90 天内，再按 `ListingSalesVolumeOfMonth` 排
- 区分"自然爆发"（评论稳步增长、长尾词占比高）vs"广告驱动"（品牌词为主、ACoS 高）；Prime Day/黑五窗口的爆量数据失真需剔除

### 5. FBA 转换套利指数
```
转换套利指数 = FBM 销量 × Buy Box 价差溢价率 × FBA 费效系数
```
- CLI：`ProductSearch` 用 `ShippingType=FBM` 过滤，按销量取 Top100 后重排
- 自动剔除大件/重货（FBA 费过高）；无品牌备案的 FBM 卖家是金矿
- ⚠️ 必须先核验品牌备案状态，listing 跟卖有侵权投诉风险；FBA 费以官方 Revenue Calculator 为准

### 6. Listing 优化潜力指数
```
优化潜力指数 = 月销量 × 关键词覆盖缺口 × 主图质量缺口 × 标题质量缺口
```
- 4.3 分但主图是随手拍、标题仅 80 字符、A+ 空白的产品，比 4.6 分满配产品优化空间大得多
- 典型 poor listing 原型：铺货卖家 / 工厂直营 / 无人打理老链接
- ⚠️ 差 listing 仍出单可能是产品本身有致命缺陷（查退货率/差评）

## 三、选品评分总表（全排序用）

| 维度 | 权重(新手/成长/专业可调) | 取数端点 |
|---|---|---|
| 市场需求（月销/搜索量） | 30% | ProductRequest / CategoryRequest |
| 竞争强度（ASIN 数/评论壁垒） | 25%（新手加权） | ProductSearch / category_report |
| 利润潜力（Amazon 费用后贡献，未扣采购/广告/退货） | 20% | ProductRequest.FbaFee/PlatformFee/Profit（仅作初筛，最终以 amz-profit-calc 为准） |
| 品牌真空/集中度 | 10% | CategoryTrend index 32-35 |
| 增长趋势（6 个月斜率） | 10% | product_trend / CategoryTrend index 0 |
| 场景可描述/复杂度 | 5% | SimilarProductFeature |

打分后全量排序，Top 候选进入深挖（product_detail + product_trend 并行）。

## 四、风险等级标注（必须 flag，不隐藏产品）

| 级别 | 类目 | 提示动作 |
|---|---|---|
| 🔴 Hard | 食品/饮料/保健品/医疗器械/婴儿食品/农药/酒精/功能性化妆品 | 必须有资质，独立评审确认 |
| 🟡 Capital | 服装/鞋包/珠宝/假发/家具/床垫/大件家电 | 退货率 5-30%、库存风险高，显著提示 |
| 🟠 Ops | 电子/液体/易燃/IP 授权/汽配/玻璃易碎 | 认证、危险品、侵权、运输破损风险 |
| ⚠️ Trap | 手机壳/钢化膜/节日装饰/书碟 | 极度内卷、利润薄、季节性死库存 |

## 五、闭环工作流参考

完整多阶段闭环（卖家画像门 → 发现 → 深挖 → 供应链 → 财务 → 风险 → 评审团 → 交付 → 监控）见 seller-agent `references/workflows/closed-loop-selection.md`。日常选品不必走完整 100 轮闭环；本 Skill 默认走轻量路径：发现 → Top20 候选 → 评分 → go/no-go。
