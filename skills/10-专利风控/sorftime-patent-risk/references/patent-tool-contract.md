# Sorftime 专利接口合约（2026-10-27 服务端 schema）

> 通道命名：MCP 用 snake_case；HTTP API/CLI 用 PascalCase。  
> 实测：MCP `patent_search_from_keyword/image`、HTTP API `PatentSearchFromKeyword`、CLI `sorftime api PatentSearchFromKeyword`、`PatentRequest` 均可用。  
> 统一入口：`scripts/patent_call.py --channel auto|mcp|api|cli`。

> 本文件来自 Sorftime MCP 服务端 `tools/list` 的实时 schema 核对。不要用旧版工具名或自定义字段替代。

## patent_search_from_image

用途：按产品图片检索外观设计专利，最多返回 100 件，工具标示成本 450。

### 必填

- `image`：图片 URL、`data:image/...;base64,...` 或裸 Base64；JPG/PNG，<4MB
- `query_mode`：整数
  - `1`：智能关联，推荐；分析图片特征后综合检索，适合真实场景图
  - `2`：按本图检索，适合白底图/线稿，强调图案、形状、颜色一致性

### 可选

- `country`: string[]，如 `["US","CN","WO","EP","JP","KR","EM"]`
- `loc_class_no`: string[]，如 `["07-01","10-01"]`
- `legal_status`: integer[]: `1` Expired, `2` Active, `3` Pending, `4` PCT Expiry, `5` PCT Pending, `6` Unconfirmed
- `product_keyword`: 逗号分隔，如 `corner shelf,bookshelf`
- `applicant`: 申请人/公司名

## patent_search_from_keyword

用途：关键词、公司、发明人、公开号或申请号检索，最多 30/页，工具标示成本 60。

### 必填

- `keyword`

### 可选

- `patent_type`: integer[]:
  - `1` Invention-Pending
  - `2` Invention-Granted
  - `3` Utility Model
  - `4` Design Patent
- `legal_status`: integer[]，同图搜
- `country`: string[]
- `applicant`: string
- `publication_no`: string，如 `USD990417S1`
- `application_no`: string
- `class_type`: `1` LOC, `2` IPC, `3` CPC, `4` GBC
- `class_no`: string[]
- `page_index`: 默认 1，每页最多 30

## patent_request

用途：按公开号取完整详情，工具标示成本 150；同一账户同一公开号首次查询扣费。

### 必填

- `publication_no`

### 返回关注字段

- 专利类型、受理局
- 申请人、发明人
- LOC/IPC/CPC/GBC 分类
- 法律状态
- 申请日、公开日、预计到期日
- 专利图片、PDF 下载链接

## 成本控制

- 一次标准筛查：1 次图搜 450 + 1-3 次词搜 60/次；详情只查 3-8 件高相关命中
- 先列候选，再请求用户确认详情预算
- 同一公开号在本账户内不要重复请求详情
- 批量检索前告知预计次数和成本上限


## 实跑行为（2026-10-27）

- 直接 MCP 工具未在当前 Codex 会话暴露时，使用 `sorftime_raw_call` 可以成功调用三个专利工具。
- 图搜返回 `similarity`；**相似度仅用于排序，不是侵权判定**。
- 关键词搜索可带 `legal_status` / `patent_type` 过滤，但返回条目只稳定给出标题、公开号、申请人、申请日、公开日、缩略图；不要假设列表里一定有状态字段。
- `patent_request` 返回法律状态、分类、日期、专利图和 PDF，但没有权利要求正文。需要做 FTO/侵权判断时，必须继续打开 PDF，并由专业人员比对权利要求。
