# 1688 端点参考（9 个端点）

> 1688 平台仅支持 `domain=601`。所有调用必须传 `--domain 601`。

## 端点总览

| # | 端点名 | 消耗请求 | 说明 |
|---|--------|---------|------|
| 1 | ProductSearchFromName | 2 | 按产品名称搜索 |
| 2 | ProductSearchFromImage | 2 | 以图搜货（ImageUrl ≤ 1MB） |
| 3 | ProductSearch | 5 | 多维筛选搜索（20+ 过滤条件） |
| 4 | ProductRequest | 1 | 产品详情 |
| 5 | ProductVariations | 1 | SKU 变体数据 |
| 6 | CoinQuery | 0 | 查本月剩余 Credits |
| 7 | CoinStream | 0 | 查 Credits 消耗明细 |
| 8 | RequestStreamMonth | 0 | 查请求额度 |
| 9 | CategoryTree | 5 | 类目树（返回约 10MB+） |

---

## 1. ProductSearchFromName（按名称搜索）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| Name | String | 是 | 产品名称 |
| Page | Integer | 否 | 分页，每页最多 100 条，默认 1 |

**CLI 示例**：
```bash
sorftime api ProductSearchFromName '{"Name": "transparent acrylic double-sided tape"}' --domain 601
```

**主要返回字段**：
- `Title` / `Photo` / `Url` / `Price` / `ProductId`
- `StoreName` / `ServiceScore`（综合服务分）/ `ServiceScoreDetail`（JSON 字符串，需 parse）
- `OnlineDate` / `SalesOf30d` / `WholesalePriceRange`（JSON 字符串，阶梯批发价）
- `RepurchaseRate`（复购率 %）/ `ShippingOrigin` / `ShippingTime`
- `SellerIdentities`（如 Super Factory / Power Seller）/ `OfferIdentities`
- `ReviewCount` / `Score` / `SkuCount`
- `MinOrderQuantity`（取自 WholesalePriceRange 第一档）
- `IsDropShipping` / `StockCount`

---

## 2. ProductSearchFromImage（以图搜货）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ImageUrl | String | 是 | 网络图片 URL（≤ 1MB） |
| Page | Integer | 否 | 分页，每页最多 50 条，默认 1 |

**CLI 示例**：
```bash
sorftime api ProductSearchFromImage '{"ImageUrl": "https://example.com/product.jpg", "Page": 1}' --domain 601
```

**用途**：用 Amazon 产品主图 URL 直接反查 1688 同款货源。

---

## 3. ProductSearch（多维筛选搜索）

**参数**（部分关键参数）：

| 参数 | 类型 | 说明 |
|------|------|------|
| Page | Integer | 分页，默认 1 |
| ProductId | String | 按 ProductId 查同类产品 |
| NodeId | String | 按类目筛选 |
| SupplierName | String | 供应商名模糊匹配 |
| SupplierType | Integer | 1=Power Seller, 2=Super Factory |
| SupplierMemberType | Integer | 1=深度验厂, 2=非深度验厂 |
| ServiceScoreMin / Max | Number | 服务分范围 |
| OnlineDateRangeMin / Max | String (yyyy-MM-dd) | 上架时间范围 |
| DropshippingPriceRangeMin / Max | Number | 一件代发价格范围 |
| CumulativeSaleCountMin / Max | Integer | 累计销量范围 |
| Recent30DaySaleMin / Max | Integer | 近 30 天销量范围 |
| RepurchaseRateMin / Max | Number | 复购率范围 |
| Rights | String | 逗号分隔：1=7天无理由退货, 2=运费险, 3=48小时发货 |
| SkuCountMin / Max | Integer | SKU 数量范围 |
| StockCountMin / Max | Integer | 库存数量范围 |

**CLI 示例**：
```bash
sorftime api ProductSearch '{"Page":1, "SupplierType":2, "ServiceScoreMin":4.5, "Recent30DaySaleMin":50}' --domain 601
```

---

## 4. ProductRequest（产品详情）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ProductId | String | 是 | 1688 产品 ID |

**CLI 示例**：
```bash
sorftime api ProductRequest '{"ProductId": "789542752062"}' --domain 601
```

返回字段同 ProductSearchFromName。

---

## 5. ProductVariations（SKU 变体）

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ProductId | String | 是 | 1688 产品 ID |

**返回 Data 数组中每项**：
- `SkuId` / `SkuName`
- `Price`（批发价）/ `OfferPrice`（一件代发价）
- `Stock`（库存）
- `Width` / `Length` / `Height`（尺寸）
- `Weight`（重量）
- `PkgSizeSource`（包装尺寸来源）

**CLI 示例**：
```bash
sorftime api ProductVariations '{"ProductId": "789542752062"}' --domain 601
```

---

## 6-8. Credits / 额度查询

| 端点 | 参数 | 说明 |
|------|------|------|
| CoinQuery | 无 | 返回 `Coin`（本月剩余 Credits） |
| CoinStream | Querydate(数组), PageIndex, PageSize | Credits 消耗明细 |
| RequestStreamMonth | 无 | 返回 Purchase + Consume（请求额度） |

> Credits 和请求额度是全局的，不区分站点。

---

## 9. CategoryTree（类目树）

- **参数**：无
- **返回**：`Id`, `ParentId`, `NodeId`, `Name`
- **注意**：返回约 10MB+，建议长超时

---

## 注意事项

- `ServiceScoreDetail` 和 `WholesalePriceRange` 是 JSON **字符串**（非已解析对象），使用前需 `JSON.parse`
- 1688 仅支持 domain=601，无其他站点变体
- 请求消耗：0（额度查询）/ 1（单品详情/变体）/ 2（名称/图片搜索）/ 5（类目树/多维搜索）
