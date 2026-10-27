# 25 套电商场景模板摘要

> 提取自 ecom-image2（GPT-Image-2，buluslan/新西楼.AI）的 25 套模板。
> 使用时根据产品类型和营销目标匹配模板，再用 Sorftime 数据填充内容。

## 模板速查表

| # | 模板名 | 触发关键词 | 适用场景 | 核心元素 |
|---|--------|-----------|----------|----------|
| 01 | Hero Image / 白底主图 | 白底图, 主图, hero, packshot | Amazon 主图 | 纯白背景、产品居中、正面视角、专业棚拍光 |
| 02 | Lifestyle Scene / 生活场景图 | 场景图, 生活图, lifestyle | 副图/A+内容 | 真实家居/办公/户外环境、自然使用状态 |
| 03 | Flat Lay / 平铺图 | 平铺图, flat lay, 俯拍 | 多产品展示/礼品 | 俯视角度、道具搭配、构图整洁 |
| 04 | Detail / Macro / 微距细节图 | 细节图, 微距, macro, 特写 | 材质/工艺展示 | 极近距离、材质纹理、工艺细节 |
| 05 | Poster / Banner / 海报横幅 | 海报, poster, banner, 促销 | 促销活动/品牌页 | 大标题、促销信息、视觉冲击 |
| 06 | Social Media / 社交媒体图 | 社交媒体, 小红书, Instagram, TikTok | 社媒推广 | 竖版构图、生活化、文字叠加 |
| 07 | UGC Style / 买家秀风格 | UGC, 买家秀, GRWM | 社媒/评价区 | 手机拍摄感、不完美构图、真实感 |
| 08 | Model Showcase / 模特展示 | 模特, model, 人物展示 | 服装/美妆/配饰 | 专业模特、产品佩戴/使用效果 |
| 09 | Before/After / 前后对比 | 对比, before after, 前后 | 效果类产品 | 左右分屏、箭头指示、效果对比 |
| 10 | Packaging / 包装展示 | 包装, packaging, 礼盒 | 礼品/高端品 | 礼盒设计、开箱体验、包装细节 |
| 11 | Infographic / 信息图 | 信息图, A+, 详情页 | A+内容/副图 | 图标+文字标注、卖点拆解、步骤说明 |
| 12 | Creative Concept / 创意概念 | 创意, 概念, creative | 品牌调性/广告 | 艺术化表达、超现实元素、情绪共鸣 |
| 13 | Size/Spec / 尺寸规格图 | 尺寸, 规格, 使用步骤 | 家具/工具/食品 | 尺寸标注、参照物对比、步骤图示 |
| 14 | Multi-Product / 套装组合 | 套装, 组合, bundle | 多件套产品 | 全套产品排列、组件标注、价值展示 |
| 15 | Livestream / 直播场景 | 直播, livestream | 直播带货图 | 直播界面感、主播讲解、实时氛围 |
| 16 | Try-On Virtual / 虚拟试穿 | 试穿, 融入, try on | 服装/眼镜/美妆 | 人物佩戴效果、多角度展示 |
| 17 | Exploded View / 爆炸拆解图 | 拆解图, 爆炸图, exploded view | 电子产品/机械 | 零件分离、结构展示、内部构造 |
| 18 | Ghost Mannequin / 隐形模特 | 隐形模特, ghost mannequin | 服装类 | 无头人台效果、服装版型展示 |
| 19 | Multi-Angle Grid / 多角度网格 | 多角度, 网格, grid, 多色展示 | 多色/多款式 | 2x2/3x3 网格、多角度/多色排列 |
| 20 | Magazine Editorial / 杂志风 | 杂志, 封面, editorial, magazine | 时尚/高端品 | 杂志排版、大片质感、艺术氛围 |
| 21 | Seasonal Campaign / 季节活动 | 季节, 四季, campaign | 节日营销 | 节日元素、季节氛围、送礼场景 |
| 22 | Luxury Atmospherics / 奢华氛围 | 奢华, 氛围, 烟雾, luxury | 高端品/美妆 | 暗调光影、烟雾/花瓣等氛围道具 |
| 23 | Device Mockup / 设备模型 | 设备模型, 界面, mockup, APP | 软件/数码配件 | 设备屏幕展示、界面预览、使用场景 |
| 24 | Storefront / 店铺门面 | 店铺, 门面, 空间, storefront | 品牌店/实体 | 店面外观、店内陈列、购物体验 |
| 25 | Sports Campaign / 运动场景 | 运动, 健身, sports, fitness | 运动户外类 | 运动姿态、动态感、户外场景 |

## 模板选择决策树

```
用户请求 → 是 Amazon 主图吗？
  ├─ 是 → 01 Hero Image
  └─ 否 → 是 A+ 内容吗？
       ├─ 是 → 11 Infographic / 02 Lifestyle / 14 Multi-Product
       └─ 否 → 是社媒推广吗？
            ├─ 是 → 06 Social Media / 07 UGC Style
            └─ 否 → 根据产品类型匹配最佳模板
```

## 与 Sorftime 数据结合

每个模板的具体内容（产品描述、场景元素、文字标注）都应由 Sorftime 数据驱动：
- 卖点文字 → 来自 VOC/Customer Say
- 场景选择 → 来自评论中的使用场景
- 关键词标注 → 来自 keyword_detail
- 竞品差异化 → 来自 keyword_search_results 的图片观察
