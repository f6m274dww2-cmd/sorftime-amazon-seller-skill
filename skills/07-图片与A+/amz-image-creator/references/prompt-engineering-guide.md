# 图片提示语工程指南

## 核心原则

1. **简洁聚焦**：GPT-Image-2 / image_gen 对简洁聚焦的提示语效果最好，不要堆砌过多约束
2. **自然语言优先**：描述性句子比关键词列表效果更好
3. **材质明确**：必须明确描述材质纹理（磨砂玻璃、拉丝金属、哑光等）
4. **灯光必写**：始终包含灯光方向和质量描述
5. **参考图加分**：如有产品实拍图，通过 image_reference_url_list 传入可大幅提升一致性

---

## 提示语结构模板

### 电商主图（Hero Image）

```
Professional e-commerce product photography of [产品描述],
centered composition, front view,
clean pure white background,
soft diffused studio lighting from upper left,
crisp details, sharp focus, commercial quality,
[材质描述] texture clearly visible,
no text, no watermark, no props
```

### 场景图（Lifestyle）

```
Professional lifestyle photography of [产品描述] in [使用场景],
[人物描述] using the product naturally,
warm natural lighting, shallow depth of field,
authentic everyday moment,
[环境细节描述],
commercial e-commerce quality, photorealistic
```

### 信息图（Infographic）

```
E-commerce infographic style image of [产品描述],
[背景风格],
product on left side with callout lines pointing to features:
- feature 1 label "文字1"
- feature 2 label "文字2"
- feature 3 label "文字3"
clean modern layout, professional typography,
[配色风格], high contrast, easy to read on mobile
```

### 对比图（Before/After）

```
Split-screen comparison image,
left side showing [竞品/旧方案问题描述],
right side showing [我们的产品优势描述],
clear dividing line in the middle,
arrow pointing from left to right,
professional infographic style, clean background,
text labels "Before" and "After"
```

---

## 图上文字规范

Amazon 主图（Slot 1）**不能有文字**。副图可以有文字，需遵循：

| 规则 | 说明 |
|------|------|
| 文字数量 | 每张图不超过 5-7 个词 |
| 字体风格 | 简洁无衬线体，粗体标题 |
| 位置 | 避开产品主体，放在留白处 |
| 可读性 | 手机端缩小后仍可辨认 |
| 语言 | 与站点一致（US=英文） |

### 文字类型选择（8 选 5+）

1. 使用体验（"No more tangled cables"）
2. 参数数据（"10000mAh / 22.5W Fast Charge"）
3. 材质说明（"BPA-Free Tritan"）
4. 信任徽章（"FDA Certified" / "50,000+ Happy Customers"）
5. 数字统计（"500+ Hours Battery Life"）
6. 时效促销（"Limited Time Offer"）
7. 步骤教程（"Step 1: Charge → Step 2: Connect → Step 3: Enjoy"）
8. 认证徽章（"CE / FCC / RoHS Certified"）

---

## 反 AI 痕迹技巧（UGC/社媒图）

生成 UGC 风格图片时，加入以下要素降低 AI 感：

- 指定具体手机型号："shot on iPhone 15 Pro"
- 加入真实不完美："slight noise, warm color cast, imperfect framing"
- 真实环境感："slightly messy desk, real objects in background"
- 胶片质感："Kodak Portra 400 color feel"
- 明确禁止："NOT professional photography, NOT retouched, NOT AI-generated look"
- 避免 AI 特征词：不用 "perfect", "flawless", "stunning", "hyper-realistic"

---

## 尺寸选择

| 方向 | 宽×高 | 适用 |
|------|-------|------|
| 方形（默认） | 1024×1024 | Amazon 主图、通用 |
| 横版 | 1536×1024 | A+ Banner、社媒横图 |
| 竖版 | 1024×1536 | 小红书、Story、详情页 |

---

## 与生图通道对接

提示语生成后，按双通道执行：

1. 本机 `~/.codex/scripts/gen-image.sh` 可用时优先使用；
2. 不可用时使用包内 `product-shots-image-gen`。

```bash
# 本机通道（有参考图）
~/.codex/scripts/gen-image.sh edit --model gpt-image-2 --quality high --size 1024x1024 --image 原图.jpg --prompt "<生成的英文提示语>" --out outputs/imagegen/xxx.png

# 包内兜底（有参考图）
python3 ../product-shots-image-gen/scripts/generate.py --prompt "<生成的英文提示语>" --model gpt-image-2 --reference-image 原图.png --output outputs/imagegen/xxx.png
```

多张图片时逐张调用，每张图片对应一个独立的 prompt。
（MCP 环境的等价写法：`image_gen(prompt=..., width=..., height=..., image_reference_url_list=[...])`，仅在有 MCP 通道时使用。）

---

## 常见问题排查

| 问题 | 解决 |
|------|------|
| 产品形状不对 | 在 prompt 中更详细描述产品外形/颜色/材质 |
| 文字乱码 | 减少图上文字数量，用更简单的词 |
| 背景太复杂 | 明确写 "clean white background" 或 "solid [color] background" |
| 风格太"AI" | 加入真实感描述，减少完美感 |
| 产品比例失调 | 明确描述 "front view" / "side angle" / "centered composition" |
