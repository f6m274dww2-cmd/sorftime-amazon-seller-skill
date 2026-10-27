# Amazon 卖家全链路作战地图 R4.5

> 版本：2026-10-27-R4.5  
> 数据：Sorftime MCP / HTTP API / CLI  
> 原则：市场归市场，选品归选品，关键词归关键词，广告归广告；上一环的输出就是下一环的输入。

> **来源与转发声明**  
> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。

## 模块目录

| 目录 | 职责 | 接收 | 交付 |
|---|---|---|---|
| `00-Sorftime数据层` | MCP/CLI/API、评论、类目、关键词、专利原始能力 | 账号与请求参数 | 可落账的原始数据 |
| `01-总编排` | 全链路编排、证据门禁、交接合约 | 用户任务与预算 | G0–G9 决策包 |
| `02-市场分析` | 市场容量、竞争、价格带、品牌集中度 | 类目、ASIN、关键词 | 市场机会与风险 |
| `03-选品` | 候选池、评分、排序、Go/Caution/No-Go | 市场结论、候选 ASIN | 候选清单与 Top 5 |
| `04-供应链与利润` | 1688 货源、规格门禁、P&L、盈亏平衡 | 目标 SKU、售价、FBA | 可采购性与利润敏感性 |
| `05-关键词` | 核心/长尾/场景/痛点词库、CPC、自然位 | 目标 ASIN、类目、竞品 | 词库与广告否词候选 |
| `06-Listing` | 标题、五点、描述、后台词 | 词库、VOC、差异点 | Listing 版本 |
| `07-图片与A+` | 主图、场景、细节、A+ Storyboard、渲染 | 产品实拍、卖点、词库 | 图片与 A+ 素材 |
| `08-广告` | Campaign、预算、出价、否词、放量规则 | 词库、Listing、价格、库存 | 投放方案 |
| `09-VOC与竞品` | 差评、VOC、排名、跟卖、竞品异动 | 评论、搜索、监控数据 | 反哺任务与告警 |
| `10-专利风控` | 图搜、词搜、详情、FTO 下一步 | 产品图、结构、公开号 | 风险分级与证据 |

## 环环相扣

```
02 市场分析
   │  输出：容量 / 竞争 / 价格带 / 品牌缺口 / nodeId
   ▼
03 选品
   │  输出：候选 ASIN / 评分 / Top 5 / 目标 SKU
   ▼
10 专利风控 ── 04 供应链与利润
   │                 │ 输出：风险等级 / 成本 / 毛利 / 盈亏平衡
   └────────┬────────┘
            ▼
05 关键词
   │  输出：主攻词 / 长尾词 / 场景词 / 痛点词 / CPC / 否定词
   ├──────────────┐
   ▼              ▼
06 Listing      08 广告
   │              │
   ▼              ▼
07 图片与A+     投放与放量
   └──────┬───────┘
          ▼
09 VOC与竞品
   │  输出：差评主题 / 排名变化 / 跟卖 / 竞品动作
   ▼
回到 02/03/05/06/07/08
```

## 关键交接

| 从 → 到 | 必须交接 |
|---|---|
| 市场分析 → 选品 | nodeId、市场容量、价格带、竞争/品牌风险、候选类目 |
| 选品 → 专利/供应链/利润 | 目标 ASIN、产品图、核心结构、目标售价、首批数量 |
| 专利/供应链/利润 → 关键词 | 可售结论、差异化点、成本底线、目标毛利 |
| 关键词 → Listing/图片/广告 | 主攻词、场景词、痛点词、CPC、否定词、关键词优先级 |
| Listing/图片 → 广告 | 标题/五点、主图/场景图、价格、库存、转化卖点 |
| 广告/VOC/竞品 → 下一轮 | 搜索词、ACOS、差评、退货、排名、跟卖、竞品动作 |

## 闭环飞轮

`市场 → 选品 → 专利/供应/利润 → 关键词 → Listing/图片 → 广告 → VOC/竞品 → 市场/选品/关键词/Listing/图片/广告`

复盘不是报告终点；VOC、搜索词、排名、差评和竞品动作必须回到下一轮模块，形成闭环。

## 六道硬闸门

1. 任务闸门：没有任务陈述，不堆产品参数。
2. 专利闸门：高相关 Active 未解除，不做大货/广告放量。
3. 供应闸门：规格、盖体、材质、MOQ、食品接触文件未核实，只能算线索。
4. 利润闸门：到岸成本、广告、退货、固定成本未验证，不给精确净利。
5. 证据闸门：空响应记 `missing`；估算/推断不得写成事实。
6. 图片闸门：主图白底/无文字/Logo；场景和细节不得改变真实产品结构。

## 证据台账

所有模块的关键响应先落账：

```bash
python3 evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
python3 evidence_ledger.py verify --ledger data/evidence/ledger.jsonl \
  --decision-grade --require-stage G2 --require-stage G3 --require-stage G4
```

- `observed`：工具直接返回，可支撑事实。
- `derived`：写明公式与 `derived_from`。
- `estimate` / `inference`：只能作为假设。
- `missing`：空数据，不能写成“没有风险”。

## 专利与数据服务支持

- 专利统一入口：`10-专利风控/sorftime-patent-risk/scripts/patent_call.py --channel auto`。
- MCP 工具使用 snake_case；HTTP API/CLI 使用 PascalCase。
- 使用中遇到数据到期、额度不足、用量不足、MCP 配置或查看用量问题，可以直接进入 Sorftime 数据服务：
  https://open.sorftime.com/home?tag=NTIw
- 企业微信二维码：`docs/sorftime-jennifer-wecom-qr.png`
- 联系方式：Jennifer 17316743165（微信同号）

## 生图双通道

1. 本机 `~/.codex/scripts/gen-image.sh` 可用时优先。
2. 否则使用 `07-图片与A+/product-shots-image-gen`。
3. 两端都不可用时，只输出策略、Storyboard、Prompt，不声称已出图。

---

**署名：Sorftime Jennifer——17316743165**
