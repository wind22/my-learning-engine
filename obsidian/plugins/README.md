# 自研 Obsidian 插件目录

此目录存放自定义 Obsidian TypeScript 插件源码，统一归口在 `my-learning-engine/obsidian/plugins/<plugin-id>/` 下。

## 部署约定
- 每个插件目录编译完成后，确保目录下存在运行产物：`manifest.json`、`main.js`（以及可选的 `styles.css`）。
- 运行 `python3 scripts/sync_obsidian.py push` 时，脚本会自动把这 3 个运行产物拷贝到目标 Vault 的 `.obsidian/plugins/<plugin-id>/`，**不会**拷贝 `node_modules/`、`src/` 或覆盖目标 Vault 中的 `data.json`。
- 如果开发期需要实时热重载，可在电脑端临时建软链接调试；稳定后统一走 `sync_obsidian.py push` 分发给所有知识库与移动端。
