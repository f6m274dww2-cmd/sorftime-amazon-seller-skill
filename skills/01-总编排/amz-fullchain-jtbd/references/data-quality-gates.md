# 全链路数据质量门禁

## P0

### 1. Trend type

- 新参数：`type`
- 兼容旧参数：`product_trend_type`
- 必须断言：请求 `SalesVolume/SalesAmount/Price/Rank/BsrRank/...` 后，返回的 `data.type` 完全一致。
- 不一致 → 停止，不画图、不算同比、不进入报告。

### 2. Customers Say

- `positive + negative <= mention`
- 不满足 → 汇总不可用于决策，改看原始评论。

### 3. Reviews

- 去重：stable ID 优先；同 stable ID 出现互斥规格或重复属性冲突时整条/整组标 AMBIGUOUS_VARIANT；无 ID 时按规范化属性签名分组
- 空文本保留为 INSUFFICIENT_CONTENT；AMBIGUOUS_VARIANT 与 INSUFFICIENT_CONTENT 采用互斥主分类
- 变体过滤：目标变体、其他变体、未标变体三段分开统计
- 报告必须写样本前后数量

### 4. Profit

- Amazon 费用后贡献 = 售价 − FBA − 平台佣金
- 采购后毛利 = Amazon 费用后贡献 − 到岸成本
- 经营贡献 = 采购后毛利 − 广告 − 退货计提
- 月净利 = 经营贡献 × 月销 − 固定费用
- FBA 估算 → 只能粗筛，不能精确 Go/No-Go
- 数值存在 ≠ 已核实：所有实际参与计算的字段（售价、FBA、平台费、到岸成本、月销量、重量、费率、广告/退货假设、固定成本、Sorftime profit）都必须分别标注来源
- 来源必须匹配字段白名单；未核实/错配必须 BLOCKED，默认假设只能 PROVISIONAL
- 拒绝 bool、NaN、Infinity、负费用、越界比例；Sorftime profit 算术匹配不等于来源已验证

### 5. Rank

- 不同接口的位置不是同一指标
- source 标签必须归一化为受控 source_id；单来源、重复别名、未知来源都不可比较
- 排名必须是完整格式，position <= total；至少两个互异有效来源才能比较
- 保留：source / page / position / total / time

### 6. Supply

- 1688 搜索价 ≠ 可采购成本
- 必须核对：容量、尺寸、包装数量、盒盖配套、场景适用性、食品接触文件
