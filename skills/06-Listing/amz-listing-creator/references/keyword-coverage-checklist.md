# 关键词覆盖检查清单

## 一、覆盖检查方法

### Step 1：建立目标关键词列表

从以下来源汇总目标关键词：
- Sorftime 关键词拓展（keyword_extends / KeywordExtends）
- 竞品 ASIN 流量词反查（product_traffic_terms / ASINRequestKeyword）
- 用户提供的词表
- 关键词搜索结果 Top 产品标题提取

### Step 2：分级

| 层级 | 标准 | 目标位置 |
|------|------|----------|
| 🔴 Primary | 最高搜索量（>10000/月），核心品类词 | 主标题必须出现（≤75 字符，放不下则进副标题） |
| 🟡 Secondary | 中搜索量（1000-10000），高相关 | Bullets 必须出现 |
| 🟢 Tertiary | 低搜索量/长尾（<1000） | Description 尽量覆盖 |
| ⚪ Backend | 未在正文中覆盖的词 | Backend Search Terms |

### Step 3：逐项检查

对每个目标关键词，检查是否出现在：
- Title
- Bullet Points（5条合并检查）
- Description
- Backend Keywords

### Step 4：生成覆盖报告

```markdown
## 关键词覆盖报告

| Keyword | Volume | In Title? | In Bullets? | In Description? | In Backend? | Status |
|---------|--------|-----------|-------------|-----------------|-------------|--------|
| power bank | 45,000 | ✅ | ✅ | ✅ | — | 🟢 Covered |
| portable charger | 22,000 | ❌ | ✅ | ✅ | ✅ | 🟡 Add to title |
| fast charging | 18,000 | ✅ | ✅ | ❌ | ✅ | 🟢 Covered |
| slim power bank | 8,000 | ❌ | ❌ | ✅ | ✅ | 🟡 Add to bullets |
| mini charger | 3,500 | ❌ | ❌ | ❌ | ✅ | 🔴 Missing |

**覆盖率：18/22 keywords (82%)**
```

### 覆盖等级

- 🟢 **90%+**：Excellent，关键词覆盖充分
- 🟡 **70-89%**：Good，有少量缺口
- 🔴 **<70%**：Needs work，重要关键词缺失

---

## 二、常见缺口诊断

| 现象 | 可能原因 | 修复方向 |
|------|----------|----------|
| 高搜索量词完全未覆盖 | Listing 语义场缺失 | 在 Title/Bullets 中自然嵌入 |
| 竞品都在用但你没有 | 竞品关键词布局更全 | 竞品反查后补齐 |
| 长尾词覆盖率低 | 正文空间不足 | 放入 Backend Keywords |
| Title 关键词密度过高 | 关键词堆砌风险 | 减少重复，移至 Backend |
| COSMO 意图词未覆盖 | 场景/人群描述模糊 | 增加使用场景和人群描述 |

---

## 三、竞品对比检查

当提供竞品 ASIN 时，执行以下对比：

1. 拉取竞品 listing 标题和五点（ProductRequest）
2. 提取竞品使用的关键词集合
3. 对比你的 listing 与竞品的关键词差异
4. 输出 Gap 分析：

```markdown
### 竞品关键词 Gap 分析

| Keyword | Your Listing | Competitor 1 | Competitor 2 | Priority |
|---------|-------------|-------------|-------------|----------|
| [kw] | ❌ | ✅ Title | ✅ Bullet | 🔴 High |
```

**Gap Score 计算参考：**
```
Gap Score = (竞品覆盖数 - 自身覆盖数) × 搜索量权重 × 排名差距系数
```

- Gap Score > 80：竞品全覆盖，你完全没有 → 最高优先级
- Gap Score 30-80：部分竞品覆盖 → 次优先级
- Gap Score < 30：零散覆盖 → 增量补充

---

## 四、检查清单

生成 listing 后逐项确认：

- [ ] Title 包含至少 1 个 Primary 关键词
- [ ] 5 条 Bullets 每条至少包含 1 个目标关键词
- [ ] Description 包含 Title/Bullets 未覆盖的 Tertiary 关键词
- [ ] Backend Keywords ≤ 250 字节
- [ ] Backend 不重复正文已有词
- [ ] 无竞品品牌名出现在任何位置
- [ ] 无促销/主观评价词（best, #1, top rated）
- [ ] 主标题 ≤ 75 字符（7.27 新规两段式），含 品牌+核心大词+1 个关键差异点；副标题承载次关键词
- [ ] 移动端可读性检查通过
- [ ] COSMO 场景/人群描述已明确
