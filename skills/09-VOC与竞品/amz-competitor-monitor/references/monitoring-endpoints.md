# 监控端点参考（14 个端点）

> 所有 Amazon 监控端点 domain 默认 1（US）。监控类端点消耗 **Credits**（非请求次数），每月 10 号 0 点清零。监控数据保留 30 天。

## 一、关键词排名监控（5 端点）

### 1. KeywordBatchSubscription — 注册关键词监控

**Credit 成本**：按关键词数消耗，非请求次数。监控 1 关键词 7×24h 每小时 1 次前 3 页 = 504 Credits/周。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String[] | 是 | 关键词列表，如 `["kw1","kw2"]` |
| mode | Integer | 是 | 0=PC浏览器, 1=移动端 |
| area | String | 条件 | 邮编（PC模式必传） |
| page | Integer | 是 | 监控前 N 页：1/3/5/7（移动端固定1） |
| period | String | 是 | 频率表达式：`<星期>|<时段>|<频率>` |

**period 语法**：
- 星期：1-7 逗号分隔（1=周一）
- 时段：1-6（每段4小时，北京时间）：1=1-4点, 2=5-8点, 3=9-12点, 4=13-16点, 5=17-20点, 6=21-0点
- 频率：1=时段内1次, 2=每小时1次, 3=每2小时1次

**PC 模式邮编**：US=10041(纽约)/60601(芝加哥)/94102(旧金山)

**示例**：
```bash
# 工作日 5-8点和9-12点，每时段1次，PC模式(纽约)，前3页
sorftime api KeywordBatchSubscription '{"keyword":["power bank"],"mode":0,"area":"10041","page":3,"period":"1,2,3,4,5|2,3|1"}' --domain 1
```

**返回**：`["keyword:taskId", ...]`；taskId=-999 表示注册失败（时段任务过多）

---

### 2. KeywordTasks — 查询关键词监控任务

| 参数 | 类型 | 说明 |
|------|------|------|
| pageIndex | Integer | 默认1 |
| pageSize | Integer | 20-200，默认20 |
| taskid | String | 按任务ID查，逗号分隔 |
| keyword | String | 关键词模糊匹配 |

---

### 3. KeywordBatchTaskUpdate — 修改关键词监控任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | Integer | 是 | 任务ID |
| update | Integer | 是 | 0=改设置, 1=暂停, 2=启动, 9=删除 |
| mode/area/page/period | — | 条件 | update=0 时传 |

---

### 4. KeywordBatchScheduleList — 查询执行批次

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| TaskId | Integer | 是 | 任务ID |
| queryDate | String | 否 | yyyy-MM-dd，从该日期起查 |

---

### 5. KeywordBatchScheduleDetail — 提取批次详情

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ScheduelId | String | 是 | 批次ID，逗号分隔最多20个 |

**返回**：CSV 格式字符串数组，每行含 asin、主图、标题、曝光类型、排名等 20 个字段。

---

## 二、Best Seller 榜单监控（4 端点）

### 1. BestSellerListSubscription — 注册榜单监控

**前提**：目标类目必须已关注。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nodeid | String | 是 | 类目 NodeId |
| Range | Integer | 是 | 1=top100 |
| Period | Integer | 是 | 频率（见下） |
| BestSellerListType | Integer | 是 | 1=New Releases, 3=Most Wished For, 4=Gift Ideas, 5=Best Sellers |

**Period**：100=每日0点, 106=每日6点, 112=每日12点, 118=每日18点, 200=每2小时(偶数), 201=每2小时(奇数)

**Credit 成本**：top100=10/天, top200=20/天, top300=30/天, top400=40/天

---

### 2. BestSellerListTask — 查询榜单监控任务

| 参数 | 类型 | 说明 |
|------|------|------|
| pageIndex / pageSize | Integer | 分页 |

---

### 3. BestSellerListDelete — 删除榜单监控

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nodeid | String | 是 | 类目 NodeId |
| BestSellerListType | Integer | 是 | 1/3/4/5 |

---

### 4. BestSellerListDataCollect — 拉取榜单数据

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nodeid | String | 是 | 类目 NodeId |
| BestSellerListType | Integer | 是 | 1/3/4/5 |
| queryDate | String | 是 | `yyyy-MM-dd HH`，如 "2026-09-09 00" |

---

## 三、跟卖 & 库存监控（5 端点）

### 1. ProductSellerSubscription — 注册跟卖监控

**Credit 成本**：每次监控 2 Credits/ASIN（JP站4），开启库存检查 +1 Credits。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| asin | String | 是 | 目标 ASIN |
| checkstock | Integer | 否 | 0=不查库存(默认), 1=查库存 |
| period | String | 是 | 频率表达式（同关键词监控） |

**限制**：最多监控 top 30 卖家。

---

### 2. ProductSellerTasks — 查询跟卖监控任务

分页查询所有有效任务。

---

### 3. ProductSellerTaskUpdate — 修改跟卖监控任务

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | Integer | 是 | 任务ID |
| update | Integer | 是 | 0=改设置, 1=暂停, 2=启动, 9=删除 |
| period | String | 条件 | update=0 时传 |

---

### 4. ProductSellerTaskScheduleList — 查询执行批次

| 参数 | 类型 | 必填 |
|------|------|------|
| TaskId | Integer | 是 |

---

### 5. ProductSellerTaskScheduleDetail — 提取跟卖结果

| 参数 | 类型 | 必填 |
|------|------|------|
| ScheduelId | String | 是 |

**返回 CSV 行格式**：`<采集时间>,<asin>,<卖家名>,<卖家ID>,<是否Buybox>,<配送方式>,<类型>,<价格>,<库存>,<是否限购>`

---

## 四、站点支持矩阵

| domain | 站点 | 关键词监控 | 榜单监控 | 跟卖监控 |
|--------|------|-----------|---------|---------|
| 1 | US | ✓ | ✓ | ✓ |
| 2 | UK | ✓ | ✓ | ✓ |
| 3 | DE | ✓ | ✓ | ✓ |
| 4 | FR | ✓ | ✓ | ✓ |
| 6 | CA | ✓ | ✓ | ✓ |
| 7 | JP | ✓ | ✓ | ✓ |
| 8 | ES | ✓ | ✗ | ✓ |
| 9 | IT | ✓ | ✗ | ✓ |
| 10 | MX | ✗ | ✗ | ✓ |
| 12 | AU | ✗ | ✓ | ✓ |

## 五、常见错误码

| Code | 说明 | 处理 |
|------|------|------|
| 4 | Credits 不足 | 充值或等待下月清零 |
| -999 | 注册/修改失败 | 时段任务过多，换时段或频率 |
| 401 | 认证失败 | 检查 Account-SK |
| 403 | 权限不足 | 检查套餐 |
