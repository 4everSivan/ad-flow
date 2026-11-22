#!/bin/sh
# ad-flow 源仓库统一检查入口（维护者资产，不安装到目标项目）。
# 用法：tools/check.sh
# 覆盖：回归测试（含 T 卡讨论入口、建卡设计挂接、模板分发与 Python 3.7 兼容守卫）、版本一致性、workflow.yaml 机器块与包资产、wrapper 语法。
set -eu
cd "$(dirname "$0")/.."
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tools -v
python3 tools/bump_version.py --check
python3 tools/check_package.py
sh -n scripts/adflow-verify
