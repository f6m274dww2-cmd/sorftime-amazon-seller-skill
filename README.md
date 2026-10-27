# Amazon 卖家全链路 Skill · 卖家版

> 一个包、一张地图、一个安装入口。  
> 版本：2026-10-27-R4.5  
> 数据服务入口：https://open.sorftime.com/home?tag=NTIw

> **来源与转发声明**  
> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。

## 先做什么

1. 看 `亚马逊卖家全链路工作流地图.png`
2. 双击 `安装.command`（macOS）或 `安装.bat`（Windows）
3. 打开 `开始使用.html`
4. 运行 `python3 Amazon全链路-卖家版/doctor.py` 查看 `READY / PARTIAL / BLOCKED`
5. 用 `$amz-fullchain-jtbd` 跑完整链路

## 包内结构

```text
亚马逊卖家全链路工作流地图.png / html     先看地图
开始使用.html             使用入口与调用示例
安装.command / .bat       一键安装
skills/
  00-Sorftime数据层
  01-总编排
  02-市场分析
  03-选品
  04-供应链与利润
  05-关键词
  06-Listing
  07-图片与A+
  08-广告
  09-VOC与竞品
  10-专利风控
docs/                     数据真实性、验证记录、服务入口二维码
doctor.py                 安装后环境自检
evidence_ledger.py        数据证据台账：采集、哈希、校验
```

## 推荐调用

### 完整链路

```text
使用 $amz-fullchain-jtbd 对 <品类> 做完整选品：
JTBD 任务定义 → 5 行为信号 → 类目/竞品验证 → 候选全排序
→ 专利闸门 → 1688 货源 → 利润 → 关键词 → Listing/图片
→ 广告 → VOC/监控。
```

### 只做专利

```text
使用 $sorftime-patent-risk 检查 <ASIN/产品> 在 <市场> 的专利风险。
```

### 只做主图/A+

```text
使用 $ecommerce-visual-copywriting 做视觉策略和 A+ Storyboard，
再用 $product-shots-main-image / $product-shots-detail-page 出规范。
```

## 数据真实性（卖家版核心）

关键响应不要只把数字抄进报告。先用 `evidence_ledger.py` 落账，再做阶段判断：

```bash
# CLI 直接采集并记录
python3 evidence_ledger.py capture-cli \
  --ledger data/evidence/ledger.jsonl \
  --endpoint ProductRequest --stage G3 \
  --params '{"asin":"YOUR_ASIN"}' --domain 1

# 决策前校验
python3 evidence_ledger.py verify \
  --ledger data/evidence/ledger.jsonl \
  --decision-grade --require-stage G3 --require-tool ProductRequest
```

- `observed` 才能支撑事实判断；`derived` 必须可复算；`estimate` / `inference` 必须显式标注。
- 哈希证明捕获后未被篡改，但不单独证明上游真实性；上游真实性由 Sorftime 凭证、服务端响应和同参数重放共同保证。
- 数据来源、参数、时间和哈希都会留在台账里，买家可复核。

详见 `docs/DATA-VERIFICATION.html`。

## 来源与完整性核验

- 来源与转发声明见 `SOURCE-NOTICE.md`。
- 包内文件校验：`python3 verify_package.py`，应显示 `issues=0`。
- ZIP 校验：将 ZIP 的 SHA-256 与发布页 `LATEST.txt` 的官方值比对。
- 二维码、联系方式和数据服务入口均纳入发布包校验；哈希不一致时停止使用并联系 Jennifer 17316743165。

## 专利三通道

- MCP：`patent_search_from_keyword` / `patent_search_from_image` / `patent_request`，snake_case。
- HTTP API：`/api/PatentSearchFromKeyword` / `PatentSearchFromImage` / `PatentRequest`，PascalCase。
- CLI：`sorftime api PatentSearchFromKeyword` / `PatentSearchFromImage` / `PatentRequest`，PascalCase。
- 统一入口：`sorftime-patent-risk/scripts/patent_call.py`。

## 生图配置

卖家主路径使用包内 `product-shots-image-gen`，不依赖 `~/.codex`：

```bash
bash ../product-shots-image-gen/scripts/setup.sh
```

生图采用双通道：本机 `~/.codex/scripts/gen-image.sh` 可用时优先使用；不可用时回退到包内 `product-shots-image-gen`。包内通道的 Provider Key 推荐设置 `OMNIMAAS_API_KEY` 或 `PRODUCT_SHOTS_IMAGEGEN_API_KEY`；没有 Key 时仍可做视觉策略、Storyboard 和 Prompt，但不得声称已生成图片。

## 注意

- 专利结果不是法律意见。
- 示例数据不能当作目标产品的真实数据；生产使用时用卖家自己的 Sorftime 凭证重新采集。
- 对外分发前确认 Sorftime 数据与第三方许可证的再分发边界，见 `THIRD-PARTY-NOTICES.md`。


## 版本内容

共 18 个 Skill：2 个 Sorftime 数据底座、11 个主链路、1 个专利风控、4 个作图/A+。


## 升级安全

- 检测到已有同名 Skill 时，安装器会停止，避免“旧 Skill + 新 manifest”混装。
- 确认覆盖升级请用：`python3 install.py --force`。
- 旧版本会先移动到 `.backup-AmazonFullchain-时间戳`。

## 安装清单（卖家版）

1. 双击 `安装.command`（macOS）或 `安装.bat`（Windows）。
2. 安装器会复制 18 个 Skill 到 `~/.agents/skills`，并运行 `doctor.py`。
3. 卖家使用自己的 Sorftime 账号配置 MCP/CLI；本包不携带账号密钥。
4. `sorftime-seller-agent` 需要 Python 3.10+，建议 Python 3.12。
5. 生图优先使用本机 `gen-image.sh`；没有时使用包内 `product-shots-image-gen` 并配置 Provider Key。

## 数据服务入口

数据到期、额度不足、用量不足、账号未开通，或不知道在哪里查看使用数据时：

- 点击：https://open.sorftime.com/home?tag=NTIw
- Sorftime 数据入口二维码：`docs/sorftime-service-qr.png`
- 企业微信二维码：`docs/sorftime-jennifer-wecom-qr.png`
- 联系方式：Jennifer 17316743165（微信同号）

该入口用于卖家查看账户、使用量、额度和续费。

---

**署名：Sorftime Jennifer——17316743165**
