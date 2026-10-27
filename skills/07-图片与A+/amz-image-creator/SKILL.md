---
name: amz-image-creator
description: Sorftime 数据驱动的亚马逊电商图片创作。用 VOC/评论/关键词/用户场景/Q&A 等数据洞察指导图片内容和卖点呈现，生成主图/A+图片/社媒图，融合 GPT-Image-2 25 套场景模板与 Sorftime 市场数据，提高点击率和转化率。当用户要做图、设计主图、做A+图片、社媒图、产品图片、电商图片、listing图片、白底图、场景图，或说"做图/主图设计/A+图片/社媒图/产品图片/图片设计/电商图片/listing图片/白底图/场景图/image generation/e-commerce image/product photography/hero image/A+ content image/social media image/lifestyle image/infographic/flat lay/亚马逊主图/amazon product image/图片提示词/image prompt/data-driven image/VOC图片"时使用。默认 Amazon US，支持多站点。
---

# amz-image-creator — 数据驱动的电商图片创作

用 Sorftime 数据辅助生图：通过 VOC/评论/关键词/用户场景等数据洞察，指导图片内容和卖点呈现，提高点击率和转化率。渲染采用双通道：如果本机 `~/.codex/scripts/gen-image.sh` 存在且可用，优先使用已验证的本机通道；否则自动回退到包内 `product-shots-image-gen`，保证卖家版可移植。

> 链路位置：第 7 环「做图」。上游 ← amz-listing-creator（卖点/关键词）+ amz-voc-analysis（场景/痛点）；下游 → 上架发布 → amz-ad-planning。全链路地图见 `../amz-workflow-map.md`。

## 证据落账（强制）

关键 Sorftime 响应不能只把数字抄进报告，必须先写入证据台账：

```bash
python3 ../evidence_ledger.py capture-cli --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 --params '{"asin":"YOUR_ASIN"}' --domain 1
```

MCP 响应使用 `record --channel mcp --input response.json`。阶段决策前执行 `verify --decision-grade --require-stage ...`。详见 `../amz-fullchain-jtbd/references/data-evidence-contract.md`。

## 前置检查

执行任何数据操作前，先运行通道检测：

```bash
python3 scripts/channel_check.py
```
> 💡 无 Sorftime 凭证、或调用报"额度不足"时：通过数据服务入口登录 / 查看账户（含 7 天试用）→ https://open.sorftime.com/home?tag=NTIw


根据输出选择 MCP 或 CLI 通道。默认站点：US（domain=1）。

## 生图与 A+ Skill 路由

按层级调用，不要让一个 Skill 同时承担策略、生成、合规和验收：

- 策略/证据/A+ Storyboard：`ecommerce-visual-copywriting`
- Amazon 主图与副图：`product-shots-main-image`
- Amazon A+ 模块：`product-shots-detail-page`
- 实际渲染：优先本机 `gen-image.sh`；不可用时使用包内 `product-shots-image-gen/scripts/generate.py`
- 付费快速套图：`ecommerce-listing-image-set` / `ecommerce-detail-module-studio`
- 工业品复杂项目：再评估 `sellerpilot-product-image-industrial`

Sorftime 数据服务入口：https://open.sorftime.com/home?tag=NTIw  
登录 / 查看账户 / 续费：https://open.sorftime.com/home?tag=NTIw

完整路由与许可证注意项见 [references/image-aplus-skill-routing.md](references/image-aplus-skill-routing.md)。

## 核心流程（三阶段）

```
阶段一：Sorftime 数据辅助分析
  ↓
阶段二：生成图片提示语（Prompt Engineering）
  ↓
阶段三：调用 image_gen 渲染实际 PNG
```

### 阶段一：数据辅助分析

用 Sorftime 数据回答"图片应该展示什么"：

| 数据维度 | 数据来源 | 指导图片内容 |
|----------|----------|-------------|
| 用户场景/使用场景 | product_customers_say / product_reviews | 场景图展示真实使用环境 |
| 用户画像 | product_customers_say / reviews 分析 | 模特图选择匹配人群 |
| 卖得好的产品特征 | keyword_search_results / product_search / product_detail | 主图构图/角度参考竞品 |
| Q&A 常见问题 | product_reviews（问题类评论） | 信息图解答常见疑问 |
| VOC 核心卖点 | product_customers_say | 突出用户最关心的卖点 |
| 关键词趋势 | keyword_detail / keyword_trend | 图片文字包含高频搜索词 |
| Reddit 特征 | reddit_post_search | 社媒图风格参考 |

### 阶段二：提示语生成

基于数据分析结果，从 25 套场景模板中匹配最适合的模板，生成结构化英文提示语。详见 `references/image-templates.md` 和 `references/prompt-engineering-guide.md`。

### 阶段三：图片渲染（本机优先 + 包内兜底）

先检查：

```bash
python3 ../doctor.py --dest ..
```

#### 通道 A：本机已配置的生图通道（优先）

如果 `~/.codex/scripts/gen-image.sh` 存在且可执行，直接使用。该通道已在 2026-10-27 的 B08R6CMC9H 实跑中成功生成白底、场景和细节三张概念图。

```bash
~/.codex/scripts/gen-image.sh edit \
  --model gpt-image-2 --quality high --size 1024x1024 \
  --image 原图.jpg \
  --prompt "保持产品外观一致，改为真实厨房场景" \
  --out outputs/imagegen/xxx.png
```

#### 通道 B：包内可移植渲染器（卖家机器兜底）

```bash
bash ../product-shots-image-gen/scripts/setup.sh
python3 ../product-shots-image-gen/scripts/generate.py \
  --prompt "阶段二生成的英文提示语" \
  --model gpt-image-2 \
  --size 1024x1024 \
  --output outputs/imagegen/<产品名>-<图位>.png
```

已有产品实拍图时：

```bash
python3 ../product-shots-image-gen/scripts/generate.py \
  --prompt "保持产品外观一致，改为真实厨房场景" \
  --model gpt-image-2 \
  --reference-image 原图.png \
  --output outputs/imagegen/xxx.png
```

包内通道的 Provider Key 推荐使用环境变量 `OMNIMAAS_API_KEY` 或 `PRODUCT_SHOTS_IMAGEGEN_API_KEY`；也可使用 `~/.product_shots_imagegen_api_key`（权限 600）。没有 Key 时仍可完成策略、Storyboard 和 Prompt，但不要声称已生成图片。

双通道都不可用时，明确输出“生图通道不可用 + 原因”，不得用提示词冒充已生成图片。

输出：实际 PNG 图片 + 数据辅助分析报告 + 提示语文档。

## MCP 通道

| 工具 | 用途 |
|------|------|
| `product_detail` | 获取产品 listing 详情（标题/卖点/价格/评分） |
| `product_reviews` | 获取用户评论（差评痛点/好评亮点） |
| `product_customers_say` | 获取 Amazon 总结的客户声音（VOC） |
| `keyword_detail` | 关键词详情（搜索量/CPC，用于图片文字选择） |

⚠️ raw 工具通过 `sorftime_raw_call` 调用。

## CLI 通道

```bash
# 产品详情
scripts/cli_call.sh ProductRequest '{"asin": "B0CVM8TXHP"}'

# 客户声音
scripts/cli_call.sh ProductCustomersSay '{"asin": "B0CVM8TXHP"}'

# 产品评论
scripts/cli_call.sh ProductReviewsQuery '{"asin": "B0CVM8TXHP", "pageIndex": 1}'

# 关键词详情
scripts/cli_call.sh KeywordRequest '{"keyword": "power bank"}'
```

## 输出格式

```markdown
# 📸 图片创作结果

## 数据辅助分析
- 核心卖点：[从 VOC/评论提取]
- 用户场景：[从客户声音提取]
- 高频关键词：[从关键词数据提取]
- 竞品图片参考：[从 product_search_results 提取]

## 生成图片清单
| 序号 | 图位 | 场景类型 | Prompt 摘要 | 文件 |
|------|------|----------|-------------|------|
| 1 | 主图 | Hero Image | ... | xxx-01.png |
| 2 | 场景图 | Lifestyle | ... | xxx-02.png |
| ... | ... | ... | ... | ... |
```

## 详细方法论

- `references/image-data-assistance.md`：数据辅助生图方法论（VOC/关键词/用户场景如何指导图片内容）
- `references/image-templates.md`：25 套场景模板摘要
- `references/prompt-engineering-guide.md`：图片提示语工程指南

---

## 来源与转发

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
>
> 来源署名：Sorftime Jennifer——17316743165  
> 联系方式：Jennifer 17316743165（微信同号）  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw
