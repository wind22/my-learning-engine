# Obsidian UI 与配置真源（Single Source of Truth）

所有 Obsidian UI 改造、插件清单与可复用配置集中在此目录，彻底与具体笔记库解耦。无论未来新建多少个 Vault（学习库、工作库、专项研究库），都可通过 `scripts/sync_obsidian.py` 一键套用。

## 目录说明

| 目录 | 存放内容 | 分发目标（目标 Vault 内） |
| :--- | :--- | :--- |
| `config/` | 通用配置白名单（`app.json`、`appearance.json`、`core-plugins.json`、`community-plugins.json`、`templates.json`、`hotkeys.json`） | `.obsidian/*.json` |
| `config/plugin-defaults/` | 无密钥插件的默认 `data.json`（`dataview`、`templater-obsidian`、`omnisearch`） | `.obsidian/plugins/<id>/data.json`（仅目标缺失时写入，加 `--force-defaults` 可强制刷新） |
| `snippets/` | 自定义 CSS 片段（卡片排版、Callout、Canvas 节点样式等） | `.obsidian/snippets/*.css` |
| `themes/` | 自定义或固化的主题目录 | `.obsidian/themes/` |
| `plugins/` | 自研 Obsidian TS 插件源码（仅分发 `manifest.json`、`main.js`、`styles.css` 运行产物） | `.obsidian/plugins/<id>/` |

## 预置社区插件（精简 7 件套）
1. **`dataview`**：驱动 `Home.md` 动态控制台看板（到期待检验决策、思维模型武器库、今日待复盘卡片、知识地图）。
2. **`templater-obsidian`**：4 个核心目录新建笔记自动套模板（`10-Maps/`、`20-Cards/`、`30-Models/`、`40-Decisions/`），自动生成日期与验尸时间。
3. **`omnisearch`**：中文友好的毫秒级模糊搜索。
4. **`obsidian-mindmap-nextgen`**：纯 Markdown 标题/列表一键转交互式思维导图，与原生 `.canvas` 白板互补。
5. **`obsidian-git`**：桌面端 Git 自动同步（`data.json` 由 Vault `.gitignore` 隔离）。
6. **`remotely-save`**：手机端跨端同步方案（S3/R2/WebDAV/网盘等，`data.json` 由 Vault `.gitignore` 隔离）。
7. **`obsidian-local-rest-api`**：AI / MCP 直连 Obsidian 接口（含 API Key，`data.json` 由 Vault `.gitignore` 隔离）。

## 常用同步命令

```bash
# 1) 分发配置、CSS 与默认插件参数（加 --force-defaults 更新已有插件默认映射）
python3 scripts/sync_obsidian.py push

# 2) 一键下载并安装 community-plugins.json 中列出的所有社区插件（支持 --vault 复用到新库）
python3 scripts/sync_obsidian.py install-plugins

# 3) 在 Obsidian GUI 调好快捷键/外观后，反向拉回真源（自动过滤 workspace 与密钥）
python3 scripts/sync_obsidian.py pull
```
