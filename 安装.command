#!/bin/zsh
cd "$(dirname "$0")"
echo "Amazon 全链路 Skill 安装器"
echo "默认安装到 ~/.agents/skills"
echo "如果已有同名 Skill，默认跳过；需要覆盖时运行：python3 install.py --force"
echo
python3 install.py
echo
read -k 1 "?按任意键关闭..."
