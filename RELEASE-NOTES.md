# R4.5 卖家版更新说明

## 本版更新

1. 新增统一的来源与转发声明：本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。
2. 作战地图、开始使用页、README、安装说明及 18 个 Skill 均保留同一来源声明。
3. 新增 `SOURCE-NOTICE.md`、`CHECKSUMS.sha256` 与只读 PDF，用于发布时展示来源、核验完整性。
4. 明确边界：离线文件无法绝对阻止修改；哈希校验用于发现变更，不能替代在线授权或在线验签。

## R4.4 历史更新

## 本版修复

1. 专利三通道统一
   - MCP：`patent_search_from_keyword` / `patent_search_from_image` / `patent_request`，snake_case。
   - HTTP API：`PatentSearchFromKeyword` / `PatentSearchFromImage` / `PatentRequest`，PascalCase。
   - CLI：`sorftime api PatentSearchFromKeyword` 等，PascalCase；图片参数是 `Image`，详情参数是 `PublicationNo`。
   - 新增 `sorftime-patent-risk/scripts/patent_call.py`，自动完成通道和参数映射。

2. 空数据不再冒充 observed
   - `No data available`、空列表、空响应自动标记为 `missing`。
   - `missing` 不进入 `decision-grade`，不能拿空结果证明“没有专利/没有风险”。

3. 生图双通道
   - 本机 `~/.codex/scripts/gen-image.sh` 可用时优先使用。
   - 卖家机器没有本机通道时，自动回退到包内 `product-shots-image-gen`。
   - 两端都没有真实出图能力时，只输出策略/Storyboard/Prompt，不声称已生成图片。

4. 模块化与作战地图 R4.4
   - 技能按模块拆分为市场分析、选品、关键词、Listing、图片、广告、VOC/竞品、专利等目录。
- 更新 `亚马逊卖家全链路工作流地图.html/png` 和 `amz-workflow-map.md`，显示环环相扣的交接与闭环。
   - 包含 G0–G9、闭环飞轮、六道闸门、证据主线、专利三通道、生图双通道、交付物和停止规则。
- 新增数据服务入口：数据到期、额度不足、用量不足或不会查看使用数据时，点击/扫码进入 Sorftime，用于卖家查看账户、使用量、额度和续费。

## 验证结果

- 18/18 Skill 通过 `quick_validate.py`
- 134 个测试收集，130 通过，4 个 live/发布门默认跳过
- 干净目录安装 18/18 成功
- `verify_installed.py` 0 问题
- 本机环境检测：`READY`（本机生图通道 + MCP/CLI）
- B08R6CMC9H 实跑：28 条证据、decision-grade PASS、三张概念图

## 边界

- 专利相似度不是侵权结论，最终仍需律师做权利要求/外观比对。
- 利润中的到岸成本、广告率、退货率、固定成本必须用真实资料替换。
- 示例数据和原始评论台账含个人信息，不要公开分发。

---

**署名：Sorftime Jennifer——17316743165**
