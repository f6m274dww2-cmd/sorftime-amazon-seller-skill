---
name: sorftime-patent-risk
description: 在 Amazon/跨境选品、上架、改款或投诉前，用 Sorftime 专利接口做外观设计专利与关键词专利初筛，输出风险分级、证据和下一步。仅作商业风险筛查，不替代律师检索、权利要求分析或 FTO 法律意见。
---

# Sorftime Patent Risk

## 用途

在选品进入采购、Listing 制作、广告放量之前，先回答三个问题：

1. 目标站点是否存在可能阻挡销售的**有效专利**？
2. 风险更偏**外观设计**、**发明/实用新型**，还是普通商标问题？
3. 当前证据是否足以继续投入，还是必须先做律师级 FTO？

专利检索只能降低风险，不能证明“不侵权”。所有结论必须带检索范围、时间、样本和证据等级。

## 触发

用户提到专利、侵权预警、外观专利、设计专利、发明专利、实用新型、FTO、专利检索、上架前查专利、竞品专利组合、`patent_search_from_image`、`patent_search_from_keyword`、`patent_request` 时使用。

不用于：商标注册、版权、平台投诉文书、法律意见出具。

## 必须收集的最小输入

- 产品标题、类目、核心功能/结构、目标销售站点
- 至少 1 张清晰产品图；优先白底、产品占画面 >80%、JPG/PNG、<4MB
- 已知品牌/申请人/竞品 ASIN（可选，但强烈建议）
- 目标国家/地区；Amazon US 至少查 `US`，再按供应链与销售市场补 `CN/WO/EP/JP/KR`
- 当前阶段：选品、采购、上架、改款、投诉应对
- 预算确认：批量或高成本调用前，先说明预计调用次数与成本

## 接口与成本

以 Sorftime 当前服务端 schema 为准：

| 工具 | 必填参数 | 主要用途 | 返回上限 | 工具标示成本 |
|---|---|---|---:|---:|
| `patent_search_from_image` | `image`, `query_mode` | 外观/设计专利图搜 | 100 | 450 |
| `patent_search_from_keyword` | `keyword` | 关键词、公司/申请人、公开号检索 | 30/页 | 60 |
| `patent_request` | `publication_no` | 公开号详情、分类、法律状态、图片/PDF | 单件 | 150；同账户同一公开号首次查询扣费 |

`patent_request` 只在初筛出高相关专利后调用，不要对全部搜索结果逐条查询。调用前向用户提示成本，除非用户已明确授权本次批量预算。

## 三通道调用（必须区分命名）

MCP、HTTP API、CLI 的参数命名不同，不能混用：

| 通道 | 工具/端点 | 参数风格 | 示例 |
|---|---|---|---|
| MCP | `patent_search_from_keyword` | snake_case | `keyword`, `country`, `legal_status`, `patent_type`, `page_index` |
| HTTP API | `POST /api/PatentSearchFromKeyword` | PascalCase | `Keyword`, `Country`, `LegalStatus`, `PatentType`, `PageIndex` |
| CLI | `sorftime api PatentSearchFromKeyword` | PascalCase | `{"Keyword":"bento lunch box","Country":["US"]}` |

图搜和详情同理：

- HTTP/CLI：`PatentSearchFromImage`，图片参数必须用 `Image`，不是 `ImageUrl`；还需 `QueryMode`。
- HTTP/CLI：`PatentRequest`，公开号参数必须用 `PublicationNo`。
- MCP：仍使用 `patent_search_from_image`、`patent_request` 和 `image`、`publication_no`。

本 Skill 自带统一调用器，自动完成端点/参数映射：

```bash
python3 scripts/patent_call.py --channel auto --tool patent_search_from_keyword \
  --params '{"keyword":"bento lunch box","country":["US"],"legal_status":[2,3],"patent_type":[2,3,4],"page_index":1}'
```

`--channel` 可选 `auto|mcp|api|cli`。2026-10-27 实测：MCP、HTTP API、CLI 三条路径均能返回 `USD955179S` 等真实结果。不要把 snake_case 端点直接传给 `sorftime api`，会 404。

## 工作流

### 1. 定义检索边界

先确定：

- 目标国家/地区：至少包含计划销售的站点
- 专利类型：设计专利优先图搜；功能/结构优先关键词；两类都查
- 产品边界：外观轮廓、关键部件、连接结构、特殊功能
- 时间边界：优先 Active / Pending；Expired 仅用于理解技术演进

### 2. 外观设计检索

调用 `patent_search_from_image`：

```json
{
  "image": "https://example.com/product.jpg",
  "query_mode": 1,
  "country": ["US", "CN", "WO", "EP"],
  "legal_status": [2, 3],
  "product_keyword": "corner shelf"
}
```

- `query_mode=1`：智能关联，适合真实场景图/复杂背景，默认首选
- `query_mode=2`：整图匹配，适合线稿、白底图或图案/颜色本身是关键差异
- 必须填写 `query_mode`；`image` 支持 URL、`data:image/...;base64,...` 或裸 Base64
- 结果不要只按相似度排序；同时核对产品轮廓、关键部件、比例和装饰特征

### 3. 关键词/申请人检索

至少做 1-3 组检索：

- 品类核心词：`corner shelf`
- 功能组合词：`corner shelf metal frame`, `corner shelf anti tip`
- 已知品牌/申请人：`MAHANCRIS`
- 已知公开号/申请号：直接填 `publication_no` 或 `application_no`

示例：

```json
{
  "keyword": "corner shelf",
  "patent_type": [2, 3, 4],
  "legal_status": [2, 3],
  "country": ["US"],
  "page_index": 1
}
```

类型：`1` 发明申请中、`2` 发明已授权、`3` 实用新型、`4` 外观设计。

### 4. 初筛与详情

先按以下顺序筛：

1. 目标站点 + Active/Pending
2. 产品形态/功能高度相关
3. 申请人、发明人、分类号与竞品关系
4. 公开时间是否覆盖你的上架/采购计划

只对 3-8 件高相关专利调用 `patent_request`，提取：

- 公开号、专利类型、受理局
- 申请人/发明人
- LOC/IPC/CPC/GBC 分类
- 法律状态、申请日、公开日、预计到期日
- 专利图片、PDF 链接

### 5. 风险分级

| 级别 | 判定条件 | 建议动作 |
|---|---|---|
| 🔴 高风险 | 目标站点 Active 且产品外观/核心结构高度重合，或已授权权利要求覆盖关键功能 | 暂停批量采购/放量；做权利要求对照，取得律师意见 |
| 🟠 中风险 | 目标站点 Pending、境外 Active、局部结构相似、分类相关但证据不足 | 小批量验证前补查；改款规避；保留采购暂停条款 |
| 🟡 数据不足 | 图片不合格、无相关结果、法律状态不完整、检索辖区不全 | 不得写成“安全”；补图/补词/补辖区或转专业检索 |
| 🟢 未发现明显高风险 | 在已声明范围内完成图搜+词搜，未发现高相关 Active 专利 | 可继续商业评估，但仍需声明“非法律 clearance” |

### 6. 结果呈现

先给结论，再给证据。至少包含：

- 检索范围：站点、关键词、图片、法律状态、时间
- 命中数量与去重后数量
- 风险表：公开号/标题/类型/申请人/状态/相关点/证据
- 高风险专利的图与 PDF 链接
- 仍需人工判断的权利要求/外观对比
- 下一步：继续、改款、换市场、律师 FTO、暂缓
- 免责声明：不是法律意见

## 调用失败时

如果当前 Agent 没有直接暴露专利工具：

1. 确认 Sorftime schema 已有 `patent_search_from_image`、`patent_search_from_keyword`、`patent_request`
2. 使用 `sorftime_raw_call` 透传：

```json
{
  "tool_name": "patent_search_from_keyword",
  "arguments": {
    "keyword": "corner shelf",
    "country": ["US"],
    "legal_status": [2, 3],
    "page_index": 1
  }
}
```

3. 不要凭名称猜参数；先核对 `references/patent-tool-contract.md`
4. 额度不足、401/402/配额错误 → 停止重试，让用户检查 Sorftime 账户

## 硬规则

- 不编造专利号、标题、申请人、法律状态、权利要求或到期日。
- 不用“无搜索结果”等同于“无侵权风险”。
- 不把图像相似度当作侵权结论。
- 不做权利要求逐字比对的法律定论；可整理证据，最终由专业律师判断。
- 只引用接口返回的字段；日期、币种、辖区保持原文。
- 每个关键结论标注 `观测 / 估算 / 推断`。


## 实跑验证记录（2026-10-27）

- 当前 Codex 会话未直接暴露专利工具时，`sorftime_raw_call` 透传路径可用。
- `patent_search_from_image` 会返回 `similarity`，但相似度不是侵权结论。
- `patent_search_from_keyword` 的法律状态/专利类型主要在服务端过滤，返回列表不一定包含这两个字段；需要精确状态时再调 `patent_request`。
- `patent_request` 返回元数据、专利图片和 PDF 链接，但不返回权利要求正文；必须打开 PDF 人工比对。
- 因此完整风险结论至少需要：图搜命中 + 关键词命中 + 重点专利详情/PDF + 人工外观与权利要求比对。


---

## Sorftime 数据服务入口

数据由 Sorftime 提供，新用户首月 39.9 元：

https://open.sorftime.com/home?tag=NTIw

额度不足、账号未开通或需要续费时，使用同一链接：

https://open.sorftime.com/home?tag=NTIw

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
