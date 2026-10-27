# Listing 优化框架：A9 + COSMO + 8维度评分 + FABE

## 一、A9 + COSMO 算法要点

### A9 排名三支柱

| 支柱 | 含义 | 优化方向 |
|------|------|----------|
| **Relevance（相关性）** | Amazon 能否将 listing 匹配到搜索词 | 关键词必须出现在 Title/Bullets/Backend 中 |
| **Conversion（转化率）** | 看到 listing 的买家有多少下单 | 主图、价格、评分、评论、文案说服力 |
| **Sales Velocity（销量速度）** | 特定关键词下的近期销量增速 | 新品用广告和 Deal 制造 velocity |

### 诊断逻辑

- **未被索引** → Relevance 失败，关键词缺失
- **已索引但排名靠后** → Conversion 失败，流量来了不买
- **转化好但爬升慢** → Velocity 问题，需广告+Deal 推动

### COSMO 层（2024+）

COSMO 在 A9 之上增加购物者意图和上下文理解：

1. **意图推断**：买家搜 "gift for new mom who is breastfeeding"，COSMO 会匹配明确描述产后恢复、实用、舒适场景的 listing，即使不含精确词组
2. **场景具体化**：listing 中明确写出使用场景（"for the first six weeks postpartum"）和人群，能被匹配到更多意图搜索
3. **价格带匹配**：描述中体现价格区间有助于 COSMO 匹配预算敏感型买家
4. **核心原则**：使用场景和人群的具体化本身就是排名信号，不只是转化信号

### COSMO 优化实践

- 在 bullets 和 description 中明确写出 **使用场景**（when/where/why）
- 明确写出 **目标人群**（who）
- 覆盖 **多个使用场景**，不要只写一个
- 避免模糊表述（"great for anyone"），改为具体描述

---

## 二、8 维度评分标准

| 维度 | 满分 | 评分要点 |
|------|------|----------|
| **Title** | /15 | 核心关键词前置？包含品牌？含关键属性？≤200字符？移动端不截断（前80字符可读）？ |
| **Bullet Points** | /15 | 5条全部使用？利益前置？关键词自然嵌入？每条≤500字符？ |
| **Images** | /15 | 7+张图？白底主图？信息图？场景图？尺寸参考图？视频？ |
| **A+ Content** | /10 | 是否存在？品牌故事？对比表？场景图？ |
| **Description** | /10 | 未覆盖的关键词是否包含？可读性？问题→解决方案流程？ |
| **Pricing** | /10 | 价格有竞争力？有 Coupon/Deal？ |
| **Reviews** | /15 | 4.0+星？100+评论？近期评论正面？ |
| **SEO Coverage** | /10 | 核心词在 Title+Bullets+Description？长尾词存在？无浪费重复？**关键词覆盖率%** |

### 评分等级

- **90-100**：Excellent，几乎无需修改
- **75-89**：Good，有少量优化空间
- **60-74**：Average，需要针对性优化
- **<60**：Needs work，重大缺失

---

## 三、FABE 文案结构

每个 Bullet 点按 FABE 展开：

```
F — Feature（特征）：产品有什么/做什么
A — Advantage（优势）：为什么比竞品好
B — Benefit（利益）：对买家意味着什么
E — Evidence（证据）：数据/规格/证明支撑
```

### 写作原则

1. **利益前置**：客户买的是结果，不是功能
   - ❌ "Made with BPA-free Tritan plastic"
   - ✅ "SAFE FOR YOUR FAMILY — BPA-free Tritan means no harmful chemicals leaching into your smoothies, even after 1000+ uses"

2. **每条 Bullet 一个核心任务**：
   - Bullet 1：最大卖点（购买理由）
   - Bullet 2-4：重要功能（利益前置写法）
   - Bullet 5：异议消除/售后保障

3. **关键词自然嵌入**：每条 bullet 至少包含 1 个目标关键词，但不能以牺牲可读性为代价

### Tone 风格指南

| Tone | 风格 | 适用品类 |
|------|------|----------|
| Professional | 权威、规格导向、建立信任 | 电子产品、工具、B2B |
| Friendly | 对话式、利益导向、亲切 | 厨房用品、生活方式、礼品 |
| Urgent | 稀缺驱动、行动导向、解决问题 | 健康、安全、季节性 |
| Luxury | 高端、感官语言、排他性 | 美妆、时尚、高端品 |

默认：Professional。

---

## 四、Title 写作规则（2025-07-27 新规：两段式标题）

Amazon 标题调整为 **主标题（Main Title）+ 副标题（Subtitle）** 两段式结构：

**主标题（硬约束 ≤75 字符）**
- 格式：`[Brand] + [Primary Keyword] + [Key Differentiator/Attribute]`
- 只放：品牌 + 核心大词 + 1 个关键差异点/属性，其余一律后移
- 不要全大写（品牌名除外）；不要促销词（"best", "#1", "top rated"）
- 同一个词在主标题中不得重复出现 2 次以上

**副标题（卖点与次关键词承载位）**
- 格式：`[Secondary Keywords] + [Use Scenario] + [Benefit/Proof]`
- 承载放不进主标题的次级关键词、使用场景、核心卖点证据

**通用**
- 关键信息前置，移动端截断后仍可读
- 主标题+副标题合计仍建议 ≤200 字符
- 埋词分配：主标题 → 核心大词；副标题 → 场景/次关键词；Bullets → 长尾；后台词 → 剩余

## 五、Backend Keywords 规则

- 总长度 ≤ 250 字节
- 空格分隔（不需要逗号）
- 不重复 Title/Bullets 中已有的词（浪费字节）
- 不包含竞品品牌名
- 不包含促销词和主观评价词
- 覆盖同义词、拼写变体、单复数
