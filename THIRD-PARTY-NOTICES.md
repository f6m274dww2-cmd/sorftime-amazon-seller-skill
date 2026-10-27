# 第三方组件与数据说明

## 第三方 Skill 许可证

本包包含以下 MIT License 组件，原始许可证文件均保留在对应 Skill 目录：

| Skill | 版权方 |
|---|---|
| sorftime-data-cli | DannylydST · Sorftime Data Technology |
| sorftime-seller-agent | DannylydST · Sorftime Data Technology |
| ecommerce-visual-copywriting | OpenClaw Community |
| product-shots-main-image | motiful |
| product-shots-detail-page | motiful |
| product-shots-image-gen | motiful |

MIT License 允许使用、修改、复制、分发、再许可和销售，但必须保留版权声明和许可证文本。发布时不得删除对应 `LICENSE` 文件。

## Sorftime 数据与示例证据

- 卖家精简版不包含 `evidence/` 和 `tests/live/artifacts/` 样例证据；生产使用时请用卖家自己的 Sorftime 凭证重新采集。
- 对外销售或分发前，请确认你有权再分发相应的 Sorftime 返回数据；若不确定，卖家版应只保留脱敏后的汇总结果，不附带原始响应。
- 生产使用时，卖家应使用自己的 Sorftime 凭证重新采集数据，不应把示例数据当作目标产品的真实数据。
- `evidence_ledger.py` 记录工具、参数、通道、时间与响应哈希，能证明捕获后的内容未被篡改；它不能单独证明上游服务一定真实，也不替代 Sorftime 凭证、官方文件或律师意见。

## 专利与法律边界

专利检索结果仅作商业风险初筛，不构成侵权结论、FTO 意见或法律意见。高相关 Active 专利应由专业律师进一步核对权利要求和地域范围。
