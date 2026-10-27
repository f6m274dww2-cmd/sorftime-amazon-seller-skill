# 来源与转发声明

> 本 Skill 及配套作战地图由 Sorftime Jennifer 提供。允许内部使用与转发，但不得删除来源署名、联系方式或数据服务入口。

来源署名：Sorftime Jennifer——17316743165  
联系方式：Jennifer 17316743165（微信同号）  
数据服务入口：https://open.sorftime.com/home?tag=NTIw

本声明随 Skill 与作战地图一同交付。允许内部使用与转发；转发时请完整保留本文件、来源署名、联系方式和数据服务入口。

## 完整性说明

- 发布包内提供 `manifest.json` 与 `CHECKSUMS.sha256`，用于核验文件是否发生变化。
- 离线 HTML、PNG、PDF、Markdown 和 ZIP 均无法在技术上阻止被复制或修改。
- 只读权限和哈希校验可以降低误改并提供变更检测，但不能替代在线授权或在线验签。

## 如何判断是否被改

1. 将 ZIP 的 SHA-256 与发布页 `LATEST.txt` 中的官方值比对。
2. 解压后进入包根目录，运行 `python3 verify_package.py`。
3. 若出现 `issues=0`，说明包内文件与发布清单一致；若哈希不一致，请停止使用并联系 Sorftime Jennifer——17316743165。
