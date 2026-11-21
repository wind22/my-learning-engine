# MCP 接入指南

优先使用 **Filesystem MCP** 让支持 MCP 的 AI 客户端（Claude Desktop / Cursor / T3 Code / Antigravity 等）直接读写本地 `my-knowledge-vault`。

## 方案 A：Filesystem MCP（MVP 首选，零插件依赖）

1. 将 [mcp-config.example.json](./mcp-config.example.json) 中的路径替换为你本机的 `my-knowledge-vault` 绝对路径。
2. 合并到你的 AI 客户端 MCP 配置文件中（例如 Claude Desktop 的 `~/Library/Application Support/Claude/claude_desktop_config.json`）。
3. 重启客户端后，AI 即可直接：
   - 读取 `20-Cards/` 检索旧卡片并建立 `[[双向链接]]`
   - 在 `10-Maps/` 写入主题骨架 `.md` 与 `.canvas` 白板
   - 在 `30-Reviews/` 记录变式复盘日志

## 方案 B：Obsidian Local REST API（进阶可选）

当需要利用 Obsidian 内部搜索索引、活动标签页上下文或触发 Obsidian 命令时，可在 Obsidian 中安装社区插件 **Local REST API**，并在 `.env` 中填入：

- `OBSIDIAN_REST_API_URL`
- `OBSIDIAN_REST_API_KEY`（**绝不提交到仓库**；Vault 的 `.gitignore` 也已屏蔽该插件的 `data.json`）
