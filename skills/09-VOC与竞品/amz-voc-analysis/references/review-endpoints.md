# 评论与 Q&A 端点参考

> 所有端点 domain 默认 1（US）。评论实时采集消耗 Credits，评论查询消耗请求次数。

## 一、评论端点

### 1. ProductReviewsCollection — 实时采集评论

**Credit 成本**：每页 5 Credits（10条/页），每次启动至少扣 5 Credits。同一产品 2 小时内不可重复采集。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ASIN | String | 是 | 目标 ASIN |
| Mode | Integer | 是 | 0=热门评论模式, 1=最新评论模式 |
| Star | String | 否 | 星级筛选，逗号分隔：1-5=单星, 10=差评(1-3星), 11=好评(4-5星) |
| OnlyPurchase | Integer | 是 | 0=不限, 1=仅VP评论 |
| Page | Integer | 是 | 采集页数，1-10 |

**注意**：此端点不返回评论内容，仅启动采集任务。实际完成时间 2 小时到 7 天不等。完成后通过 `ProductReviewsQuery` 拉取。

**示例**：
```bash
# 采集差评（1-3星），3页，仅VP评论
sorftime api ProductReviewsCollection '{"asin":"B0CVM8TXHP","mode":0,"star":"10","onlyPurchase":1,"page":3}' --domain 1
```

---

### 2. ProductReviewsCollectionStatusQuery — 采集任务状态查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ASIN | String | 是 | 目标 ASIN |
| Update | Integer | 否 | 检查最近 N 小时内的任务，1-240 |

---

### 3. ProductReviewsQuery — 拉取评论

**请求消耗**：5

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ASIN | String | 是 | 目标 ASIN |
| Querystartdt | String | 否 | 起始日期 yyyy-MM-dd |
| PageIndex | Integer | 否 | 分页，每页100条，默认1 |
| Star | String | 否 | 星级筛选：1-5/10(差评)/11(好评)，逗号分隔 |
| OnlyPurchase | Integer | 否 | 0=不限, 1=仅VP评论 |

**返回字段**：
- `ConsumerName` / `ConsumerURL` / `ConsumerBadge`（评论者昵称/主页/徽章）
- `Star`（星级）/ `Title`（评论标题）
- `ReviewedCountry` / `ReviewsDate`
- `IsVP`（是否验证购买）
- `Asin` / `AsinProperty`（变体信息）
- `Helpful`（有用票数）
- `Content`（评论正文）
- `Resource`（评论图片，||分隔）
- `Videos`（视频缩略图）
- `ItemIndex`（数据索引：当前/总数）
- `UpdateTime`（首次采集时间）

**示例**：
```bash
# 拉取差评第1页
sorftime api ProductReviewsQuery '{"asin":"B0CVM8TXHP","star":"10","pageIndex":1}' --domain 1
```

---

### 4. ProductCustomersSay — Amazon AI 评论摘要

**请求消耗**：1

| 参数 | 类型 | 必填 |
|------|------|------|
| Asin | String | 是 |

**返回**：`Data.CustomerSay`（String）— Amazon AI 自动汇总的评论内容。

---

### 5. ProductRequest — 产品详情（辅助数据）

**请求消耗**：1/ASIN（最多10个批量）

关键字段：
- `RatingsCount` / `Ratings`（评论数/评分）
- `OneStartRatings` ~ `FiveStartRatings`（1-5星占比）
- `Feature`（Amazon 统计的产品特征及各特征评分）

---

## 二、Q&A（Alexa Questions）端点

> 支持站点：1(US)/2(UK)/3(DE)/4(FR)/5(IN)/6(CA)/7(JP)/8(ES)/9(IT)。不支持 10-14。

### 1. AlexaQuestionsCollection — 实时采集 Q&A

**请求消耗**：5

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Asin | String | 是 | 目标 ASIN（仅采集当前 ASIN，不含其他变体） |

**返回**：`Data` = taskId（Integer），>0 表示成功。

---

### 2. AlexaQuestionsCollectionStatusQuery — 任务状态查询

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Asin | String | 是 | 目标 ASIN |
| Update | Integer | 否 | 检查最近 N 小时，1-240 |

---

### 3. AlexaQuestionsCollectionResultQuery — 按任务ID拉取结果

| 参数 | 类型 | 必填 |
|------|------|------|
| TaskId | Integer | 是 |

**返回**：
- `Asin` / `VariationAsin`
- `AlexaQuestions`（问题原文）
- `Answer`（AI 回答）
- `ItemIndex` / `ItemTotal`

---

### 4. AlexaQuestionsQuery — 拉取近15天 Q&A

**请求消耗**：5

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Asin | String | 是 | 目标 ASIN |
| PageIndex | Integer | 否 | 分页，每页100条，默认1 |

**返回字段**同 ResultQuery。

---

## 三、完整 VOC 工作流

```
# 1. 拉取产品详情（评分分布/特征标签）
sorftime api ProductRequest '{"asin":"B0XXXX"}' --domain 1

# 2. 获取 Amazon AI 摘要
sorftime api ProductCustomersSay '{"asin":"B0XXXX"}' --domain 1

# 3. 实时采集评论（如已有数据可跳过）
sorftime api ProductReviewsCollection '{"asin":"B0XXXX","mode":0,"onlyPurchase":1,"page":5}' --domain 1

# 4. 拉取差评
sorftime api ProductReviewsQuery '{"asin":"B0XXXX","star":"10","pageIndex":1}' --domain 1

# 5. 拉取好评
sorftime api ProductReviewsQuery '{"asin":"B0XXXX","star":"11","pageIndex":1}' --domain 1

# 6. 采集 Q&A
sorftime api AlexaQuestionsCollection '{"asin":"B0XXXX"}' --domain 1

# 7. 拉取 Q&A
sorftime api AlexaQuestionsQuery '{"asin":"B0XXXX","pageIndex":1}' --domain 1
```
