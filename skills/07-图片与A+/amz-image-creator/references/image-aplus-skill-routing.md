# 生图与 A+ Skill 选型路由（2026-10-27）

## 结论

当前没有单一 Skill 同时做到：Sorftime 数据洞察、策略/文案、产品保真、Amazon 主图合规、A+ 模块、文件验收、投放适配。推荐采用组合，而不是强行替代 `amz-image-creator`。

## 推荐组合

| 层级 | 推荐 | 作用 | 状态 |
|---|---|---|---|
| 数据与任务输入 | `amz-image-creator` | 用 VOC/关键词/任务陈述决定“为什么做这张图” | 已安装 |
| 视觉策略与证据账本 | `ecommerce-visual-copywriting` | 主图/A+/Listing 的 Storyboard、图内文案、合规与证据门 | 外部候选，强互补 |
| Amazon 主图与 A+ 规范 | `product-shots` 生态中的 `product-shots-main-image` + `product-shots-detail-page` | 主图合规、7 类副图、8 模块 A+、21:9/3:2、移动安全区 | 外部候选，MIT |
| 七图 + A+ 双端与文件 QA | `create-amazon-listing-images` | Amazon US 7 图 + 6 组 A+/桌面移动共 19 张，带验收脚本 | 外部候选，需部署验证 |
| 快速成品生图 | 当前 `gen-image.sh` / `imagegen`；Beatra 两个本地技能 | 实际渲染、编辑、套图 | 已具备 |
| 本地策略型免费方案 | `ecom-design-master` | 本地 Qwen + 参数卡 + QA | 已安装；商业使用许可需确认 |

## 外部候选对比

### 1. ecommerce-visual-copywriting

- 来源：`feichanggege/ecommerce-visual-copywriting-skill`
- 优点：证据账本、转化驱动力、Campaign Style Lock、Storyboard、图内文案、Prompt、合规门非常完整。
- 局限：偏“策划 + Prompt”，不是最终渲染器。
- 适合：A+ 页面脚本、主图叙事、Listing 图文一致性、合规审查。
- 建议：作为 `amz-image-creator` 的策略前置层优先采用。

### 2. product-shots

- 来源：`motiful/product-shots`（MIT，alpha）
- 优点：按用途拆成主图、A+、广告、社媒、多角度；主图规则和 A+ 尺寸/移动安全区写得很硬。
- 局限：完整的图片生成依赖其 image-gen 引擎和外部 Provider；alpha 阶段需要小样验证。
- 建议：重点采用 `product-shots-main-image` 与 `product-shots-detail-page` 的规范，不必先接管整个生态。

### 3. create-amazon-listing-images

- 来源：`sanshiliu-studio/create-amazon-listing-images`
- 优点：直接面向 Amazon US 七图 + A+ 桌面/移动，包含像素、格式、色彩、透明像素、AI 人物元数据等文件验收。
- 局限：仓库较新、Star 少，许可证与长期维护需核验；默认一次做 19 张，成本与质量控制要先跑小样。
- 建议：作为“交付验收层”候选，不直接替换生成层。

### 4. amazon-image-design

- 来源：`misty1999sd/amazon-image-design-skill`
- 优点：竞品视觉拆解、商业策略、产品保真、7 图叙事和 Amazon 基线较清楚。
- 局限：与 `ecommerce-visual-copywriting` 重叠，二者不必同时安装。
- 建议：如果更偏设计执行选它；如果更偏证据/合规和文案选 visual-copy。

### 5. sellerpilot-product-image-industrial

- 来源：`ninemouth/sellerpilot-product-image-industrial`
- 优点：工业品、多源图片融合、身份几何锁、物理真相、QA 路由、tldraw 审阅非常强。
- 局限：工程体系很重，依赖 Node/Provider/Manager，适合正式工业品项目，不适合轻量日常出图。
- 建议：工业品、复杂结构或高客单项目再启用。

## 本地已有技能如何使用

| Skill | 适用 | 代价/风险 |
|---|---|---|
| `ecommerce-listing-image-set` | 一组统一的 Amazon 上架图 | Beatra 按张收费；规划免费，付费前需确认 |
| `ecommerce-detail-module-studio` | 3-6 张详情页/A+ 模块 | Beatra 按张收费；先规划再制作 |
| `ecom-design-master` | 本地 Qwen、参数卡、QA | 当前许可写明个人学习/非商业，商用前确认授权 |
| `ecom-image2` | GPT-Image-2 模板快速出图 | 走本机统一生图通道，需控制产品保真 |
| `imagegen` | 原生生成/编辑 | 适合单张和参考图编辑，不负责电商业务判断 |

## 建议路由

1. 用户只说“做一张漂亮图” → 先走 `amz-image-creator` 补任务、场景、证据，再调 `imagegen`/`gen-image.sh`。
2. 用户要做 Amazon 七图 → `ecommerce-visual-copywriting` 出策略与镜头表，再走本地 Beatra 或 product-shots 执行。
3. 用户要做 A+ → `product-shots-detail-page` 锁 8 模块规格；用 `ecommerce-visual-copywriting` 补文案与证据；最终用 `create-amazon-listing-images` 的文件验收思路检查。
4. 用户要做工业品/多源图融合 → 评估 SellerPilot。
5. 任何图片含参数、材质、层数、尺寸、功效、认证 → 先过证据账本 → 再过产品保真/合规门。

## 安装原则

- 先安装 1 个策略层 + 1 个执行层，不同时安装 5 套重叠生态。
- 安装前核验 LICENSE、依赖、API Key 和是否按张收费。
- 先用同一张真实产品图做 1 张主图 + 1 个 A+ 模块小样，比较产品保真、文字乱码、风格一致性，再决定长期使用。
