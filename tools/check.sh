#!/bin/sh
# ad-flow 源仓库统一检查入口（维护者资产，不安装到目标项目）。
# 用法：tools/check.sh
# 覆盖：回归测试、治理版本号一致性、workflow.yaml 机器块与包资产、wrapper 语法。
set -eu
cd "$(dirname "$0")/.."
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools -v
python3 tools/bump_version.py --check
python3 tools/check_package.py
sh -n scripts/adflow-verify
