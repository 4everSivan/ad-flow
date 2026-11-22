# v1.8.1 发布前验证

本机使用 macOS 和 Python 3.9.13，验证日期为 2026-11-22。

| 检查 | 结果 |
|---|---|
| `tools/check.sh` | 155 项通过，版本锚点、24+2 安装包和 Shell 语法检查通过。 |
| `scripts/adflow-verify --card T04 --to completed --record --json` | Exit 0，卡片取得 `completed` 前置回执。 |
| `scripts/adflow-verify --release v1.8.1 --json` | 归档前和归档后均为 Exit 0，错误、警告和建议均为 0。 |
| `scripts/adflow-verify --topic TaskCardCreation --scope history --json` | 命中本批次归档的 T04，状态为 `completed`。 |

[归档 T04](../task/T04.json)
