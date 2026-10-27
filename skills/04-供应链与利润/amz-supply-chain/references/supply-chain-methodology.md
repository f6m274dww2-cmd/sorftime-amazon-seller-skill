# 供应链方法论：货源对比评分与价格差分析

## 一、货源候选筛选流程

### Step 1：定位目标产品
- 输入 Amazon ASIN 或产品关键词
- 通过 Amazon 侧工具获取：售价、月销量、FBA 费用、平台佣金、尺寸重量
- 确定产品名称关键词，用于 1688 搜索

### Step 2：1688 找货（三种路径）

| 路径 | 适用场景 | 调用方式 |
|------|---------|---------|
| 按名称搜索 | 知道产品英文名称，直接搜 | `ProductSearchFromName` |
| 以图搜货 | 有 Amazon 主图，找同款 | `ProductSearchFromImage` |
| 多维筛选 | 需要精细筛选供应商质量 | `ProductSearch`（配合 SupplierType / ServiceScoreMin 等） |

### Step 3：供应商初筛
从搜索结果中按以下条件初筛：
- **服务分** ≥ 4.0（`ServiceScore`）
- **30天销量** ≥ 20（`SalesOf30d`，证明有稳定出货）
- **复购率** ≥ 20%（`RepurchaseRate`，证明老客认可）
- **供应商身份**：优先 Super Factory（`SellerIdentities` 含 "Super Factory"）或 Power Seller
- **深度验厂**：`SupplierMemberType=1`（深度认证）优先

---

## 二、供应商评分维度（总分 100）

| 维度 | 权重 | 评分依据 | 数据来源字段 |
|------|------|---------|-------------|
| 价格竞争力 | 30 | 批发价 vs Amazon 售价的比例，越低分越高 | `Price` / `WholesalePriceRange` |
| 供应商资质 | 20 | Super Factory + 深度验厂 = 满分；Power Seller = 中等；普通 = 低 | `SellerIdentities` / `SupplierMemberType` |
| 服务质量 | 15 | `ServiceScore` 4.5+ 满分，4.0-4.5 中等，<4.0 低分 | `ServiceScore` / `ServiceScoreDetail` |
| 出货稳定性 | 15 | 30天销量 + 复购率 + 库存充足度 | `SalesOf30d` / `RepurchaseRate` / `StockCount` |
| 物流时效 | 10 | `ShippingTime`（24小时发货 > 48小时 > 其他） | `ShippingTime` |
| 一件代发支持 | 10 | `IsDropShipping=true` 满分 | `IsDropShipping` / `OfferPrice` |

### 评分公式

```
供应商总分 = 价格得分×0.30 + 资质得分×0.20 + 服务分得分×0.15
           + 稳定性得分×0.15 + 物流得分×0.10 + 代发得分×0.10
```

- **价格得分**：(1 - 批发价/Amazon售价) × 100，上限 100
- **资质得分**：Super Factory+深度验厂=100，Super Factory=80，Power Seller=60，普通=40
- **服务分得分**：ServiceScore / 5.0 × 100
- **稳定性得分**：min(30, SalesOf30d/10) + min(40, RepurchaseRate) + min(30, StockCount/10000)
- **物流得分**：24h发货=100，48h=70，其他=40
- **代发得分**：IsDropShipping=true=100，false=0

---

## 三、跨平台价格差分析方法

### 毛利率测算公式

```
Amazon 售价 (S)
  - 1688 采购成本 (C)        ← 取 WholesalePriceRange 中对应 MOQ 档位
  - 头程物流 (FBA inbound)   ← 按重量/体积估算
  - FBA 配送费               ← ProductRequest 返回的 FbaFee
  - 平台佣金                 ← ProductRequest 返回的 PlatformFee
  - 广告 / 退货 / 其他摊销
= 经营贡献（不是财务净利润）
经营贡献率 = 经营贡献 / Amazon 售价 × 100%
```

### 价格差判断标准

| 毛利率区间 | 判断 | 建议 |
|-----------|------|------|
| ≥ 35% | 优质 | 可直接上架，有足够广告和促销空间 |
| 20% - 35% | 可行 | 需控制广告成本，精细化运营 |
| 10% - 20% | 勉强 | 需走量或优化供应链降本 |
| < 10% | 不建议 | 利润空间不足，风险高 |

### 关键注意事项

1. **阶梯批发价**：`WholesalePriceRange` 通常分多档（如 ≥200件=¥1.5, ≥500件=¥1.2），按实际采购量取对应档位
2. **一件代发 vs 批量采购**：`OfferPrice`（代发价）高于 `Price`（批发价），但无需囤货，按运营模式选择
3. **尺寸重量**：通过 `ProductVariations` 获取尺寸重量，用于估算 FBA 费用和头程物流
4. **产品相似度验证**：1688 搜到的"同款"可能规格/材质不同，需对照 Amazon 产品详情确认
5. **汇率**：1688 价格为人民币（CNY），Amazon 为美元（USD），按当前汇率换算
6. **合格货源门禁**：容量、尺寸、包装数量、盒盖配套、使用场景、食品接触文件任一未确认，不得把该报价带入利润模型
7. **Sorftime profit 字段**：`Profit` / `ProfitRate` 是扣 FBA 与平台佣金后的贡献，不含采购、头程、广告、退货和固定费用

---

## 四、输出模板

### 货源候选清单

| # | 供应商 | 产品链接 | 批发价区间 | MOQ | 服务分 | 30天销量 | 复购率 | 代发 | 评分 |
|---|--------|---------|-----------|-----|--------|---------|--------|------|------|
| 1 | ... | ... | ¥1.2-1.5 | 200 | 4.6 | 320 | 65% | 是 | 82 |

### 价格差分析

```
Amazon ASIN: B0XXXXXXX
Amazon 售价: $XX.XX
1688 采购价: ¥XX.XX（≈$X.XX）
FBA 配送费: $X.XX
平台佣金: $X.XX
头程物流: $X.XX
预估净利润: $X.XX
毛利率: XX.X%
```

### 供应商评估结论
- Top 推荐：供应商名 + 评分 + 推荐理由
- 备选方案：2-3 家备选供应商
- 风险提示：起订量过高 / 服务分偏低 / 库存不足 等
