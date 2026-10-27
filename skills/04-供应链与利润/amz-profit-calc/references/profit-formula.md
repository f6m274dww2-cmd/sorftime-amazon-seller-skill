# Amazon 利润口径与计算规则

## 一、必须分开的四层利润

```text
1. Amazon 费用后贡献
   = 售价 − FBA 配送费 − 平台佣金

2. 采购后毛利
   = Amazon 费用后贡献 − 到岸成本
   = 售价 − FBA − 平台佣金 − 采购 − 头程/包装

3. 经营贡献
   = 采购后毛利 − 广告成本 − 退货计提
   （可再扣促销、仓储、长期仓储）

4. 月净利
   = 经营贡献 × 月销量 − 固定费用
```

**Sorftime `profit`（旧字段 `gross_profit`）通常只等于第 1 层。**  
示例：`$24.99 − $8.90 − $3.06 = $13.03`。  
这不是净利润，也不是已经扣过采购成本的毛利。

## 二、FBA 费用优先级

1. `ProductRequest.FbaFee` / `product_detail.fba_fee`
2. Amazon Revenue Calculator / 官方费率
3. 本地公式估算，必须标记 `ESTIMATED_FORMULA`

估算公式（仅用于早期粗筛）：

```text
max(3.5, kg × 2.5 + 1.5)
```

**硬规则：**FBA 使用估算值时，输出 `BLOCKED`，不得给精确 Go/No-Go，也不得把估算月净利包装成经营结论。

## 三、平台佣金

优先使用 `PlatformFee`。如果只有费率，则：

```text
平台佣金 = 售价 × referral_rate
```

费率必须标 `ESTIMATED_RATE`；不同类目和站点费率不同。

## 四、广告与退货

- 广告：`售价 × ad_rate`，必须标 `[ASSUMED]`。
- 退货计提：`return_rate × (landed_cost + fba_fee + return_processing_fee)`。
- 广告/退货假设不能冒充店铺后台实绩。

## 五、盈亏平衡

```text
盈亏平衡月销量 = 固定月费用 / 单位经营贡献
盈亏平衡日销量 = 盈亏平衡月销量 / 30
```

单位经营贡献 ≤ 0 时：无法盈亏平衡。

## 六、输出要求

必须同时展示：

| 指标 | 说明 |
|---|---|
| 售价 | ProductRequest |
| FBA + 来源 | VERIFIED / ESTIMATED |
| 平台佣金 + 来源 | VERIFIED / ESTIMATED |
| Amazon 费用后贡献 | Sorftime 字段口径 |
| 到岸成本 | 必须来自真实采购/头程 |
| 采购后毛利 | 扣采购后 |
| 广告 | 显式假设 |
| 退货计提 | 显式假设 |
| 经营贡献 | 扣广告/退货后 |
| 月净利 | 仅在输入完整时可输出 |
| 决策状态 | READY / BLOCKED |


## 七、来源验证状态

- 来源按字段白名单校验，不能跨字段复用：
  - 售价 / FBA / 平台费 / 月销：`verified` / `product_detail` / `user_verified`
  - 到岸成本：`verified` / `supplier_confirmed` / `user_verified`
- `supplier_confirmed` 不能证明 FBA 或月销；`product_detail` 不能证明到岸成本。
- `estimated` / `estimated_rate` / `user_estimate`：只能输出 `PROVISIONAL`。
- 未提供来源、`USER_INPUT_UNVERIFIED`、`UNKNOWN`、缺失：必须 `BLOCKED`。
- 只有所有实际参与计算的字段均 verified，且经营贡献为正，才能输出 `READY_FOR_GO_NO_GO_REVIEW`。
- 重量（用于 FBA 估算）、referral rate（用于佣金估算）、广告率、退货率、退货处理费、固定月费和 Sorftime profit 校验值也必须有来源状态。
