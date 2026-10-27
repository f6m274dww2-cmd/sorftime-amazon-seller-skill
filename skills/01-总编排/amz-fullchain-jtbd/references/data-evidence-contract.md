# 数据证据合约

## 目标

让每一个进入报告的 Sorftime 数值、评论汇总、排名、专利状态和利润字段都能回答四个问题：

1. 来自哪个工具或公开源？
2. 用了什么参数、站点、账号类型和通道？
3. 什么时候观测到的？
4. 原始响应是否被改动过？

## 证据类型

| 类型 | 含义 | 能否直接用于 Go/No-Go |
|---|---|---|
| `observed` | 工具或公开源直接返回 | 可以，但仍需检查业务质量门 |
| `derived` | 基于 observed 计算，写明公式和 `derived_from` | 可以作为决策输入，但必须可复算 |
| `estimate` | 估算值 | 不可以单独支撑精确 Go/No-Go |
| `inference` | 判断、解释、机会假设 | 不可以当作事实 |
| `missing` | 工具返回空数据、空列表或 `No data available` | 不可以；必须写成数据缺口 |

## CLI 自动采集

```bash
python3 ../evidence_ledger.py capture-cli \
  --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest \
  --stage G3 \
  --params '{"asin":"B0XXXXXXXX"}' \
  --domain 1
```

采集成功后会写入：

- `tool`、`params`、`domain`
- `channel=cli`
- `observed_at`、`recorded_at`
- `payload` 和 `payload_sha256`
- 原命令、stdout/stderr 哈希、退出码、API code

需要保留原始输出时加 `--raw-dir data/evidence/raw`。不要写入 API Key、Cookie 或账号密码；脚本检测到疑似密钥字段会拒绝落账。

## MCP 响应落账

把 MCP 工具返回的原始 JSON 保存为文件，然后：

```bash
python3 ../evidence_ledger.py record \
  --ledger data/evidence/ledger.jsonl \
  --tool product_detail \
  --channel mcp \
  --stage G2 \
  --params '{"asin":"B0XXXXXXXX"}' \
  --input response.json
```

不要手工改 JSON 后再落账。需要修改数据时，另写 `derived` 记录，保留 `derived_from` 和公式。

## 校验

```bash
python3 ../evidence_ledger.py verify \
  --ledger data/evidence/ledger.jsonl \
  --decision-grade \
  --require-stage G2 \
  --require-stage G3 \
  --require-stage G4 \
  --require-tool ProductRequest \
  --fresh-hours 168
```

- `--decision-grade` 只把 `observed` 记录计入阶段完整性；`missing` 不计数，不能用“空结果”证明“没有风险/没有数据”。
- 工具返回 `No data available` 时，台账会自动降级为 `missing`。
- `--fresh-hours` 用于价格、销量、排名等时效数据。
- `--max-future-minutes` 默认为 5，防止未来时间被当成证据。
- 任一哈希不匹配、阶段缺失或时间异常都会返回非 0。

## 真实性边界

证据台账不是“上游真实性证明”，也不是区块链。它解决的是：

- 捕获后是否被改动；
- 数字是否能追溯到工具、参数和时间；
- 报告是否把估算误写成事实；
- 同一结论能否由另一个人按命令复核。

上游真实性仍需 Sorftime 凭证、服务端响应和同一参数重放来共同保证。专利结果仍不构成法律意见。
