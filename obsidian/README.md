# Obsidian UI 与配置真源（Single Source of Truth）

所有 Obsidian UI 改造与可复用配置集中在此目录，彻底与具体笔记库解耦。无论未来新建多少个 Vault（学习库、工作库、专项研究库），都可通过 `scripts/sync_obsidian.py` 一键套用。

## 目录说明

| 目录 | 存放内容 | 分发目标（目标 Vault 内） |
| :--- | :--- | :--- |
| `config/` | 通用配置白名单（`app.json`、`appearance.json`、`hotkeys.json`、`templates.json` 等） | `.obsidian/*.json` |
| `snippets/` | 自定义 CSS 片段（卡片排版、Callout、Canvas 节点样式等） | `.obsidian/snippets/*.css` |
| `themes/` | 自定义或固化的主题目录 | `.obsidian/themes/` |
| `plugins/` | 自研 Obsidian TS 插件源码（仅分发 `manifest.json`、`main.js`、`styles.css` 运行产物） | `.obsidian/plugins/<id>/` |

## 常用同步命令

```bash
# 1) 分发到默认 Vault（读取 .env 中的 VAULT_PATH）
python3 scripts/sync_obsidian.py push

# 2) 分发到任意新知识库（多库复用）
python3 scripts/sync_obsidian.py push --vault /path/to/another-vault

# 3) 在 Obsidian GUI 调好快捷键/外观后，反向拉回真源（自动过滤 workspace 与密钥）
python3 scripts/sync_obsidian.py pull

# 任意命令均可加 --dry-run 先预览变更
python3 scripts/sync_obsidian.py push --dry-run
```

## 安全边界
- `push` 与 `pull` 均使用**安全白名单**，永远不会读取、覆盖或提交 `workspace.json`、`workspace-mobile.json` 或任何插件的 `data.json`（避免泄露 API Key 与本地窗口冲突）。
- 分发采用真实文件拷贝而非跨仓软链接，保证移动端（Git / Remotely Save）100% 可用。
