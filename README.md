# my-learning-engine

个人深度学习工作流的**系统本体 + UI 改造真源**（可同时驱动多个知识库）：包含 4 步深度学习核心 Prompt、MCP 接入模板、零依赖 Python 自动化脚本，以及统一的 Obsidian UI 配置/CSS/插件源码。

## 目录结构

```text
my-learning-engine/
├── .env.example                # 环境变量模板（复制为 .env，已被 gitignore）
├── prompts/                    # 4 步深度学习闭环 Prompt
│   ├── 00-system-mentor.md     # 总控角色与反“伪勤奋”铁律
│   ├── 01-icebreaker-map.md    # Step 1: 破冰建骨架（≤150字本质 + 要素 + Canvas/Mermaid）
│   ├── 02-socratic-drill.md    # Step 2: 实战拷问（误区/边界/场景题/逻辑纠偏）
│   ├── 03-atomic-card.md       # Step 3: 沉淀原子卡片 + 检索旧卡强行跨领域入网
│   └── 04-variant-review.md    # Step 4: 跨卡片综合变式考查
├── obsidian/                   # 所有 Obsidian UI/配置改造的唯一真源（支持多库复用）
│   ├── config/                 # app.json、appearance.json、templates.json、hotkeys.json 等
│   ├── snippets/               # 自定义 CSS 片段（如 deep-learning-ui.css）
│   ├── themes/                 # 自定义/固化主题
│   └── plugins/                # 自研 Obsidian TS 插件源码
├── mcp/                        # MCP 接入配置与说明
│   ├── README.md
│   └── mcp-config.example.json
└── scripts/                    # 纯 Python 标准库脚本（零第三方依赖）
    ├── config.py               # Vault 路径解析（环境变量 / .env）
    ├── sync_obsidian.py        # Obsidian UI/配置双向同步（push 到任意库 / pull 回真源）
    ├── canvas_gen.py           # 从骨架 JSON 生成 Obsidian JSON Canvas (.canvas)
    ├── card_index.py           # 扫描 20-Cards/ 生成紧凑索引供 AI 建立双向链接
    └── pick_review.py          # 抽取到期/跨领域旧卡片供变式复盘
```

## 快速开始（MVP）

1. **配置环境变量**（本地已预生成 `.env`，指向同级 `../my-knowledge-vault`）：
   ```bash
   cp .env.example .env
   ```
2. **一键同步 UI 到知识库**（未来新建任何其他知识库，用 `--vault` 同样一键复用）：
   ```bash
   python3 scripts/sync_obsidian.py push
   # 或分发到新库：
   python3 scripts/sync_obsidian.py push --vault /path/to/another-vault
   ```
3. **接入 MCP**：参考 [mcp/README.md](./mcp/README.md) 配置 Filesystem MCP（或 Obsidian Local REST API），让 AI 直接读写 Vault。
4. **日常工作流脚本**：
   ```bash
   # 生成白板到 Vault 的 10-Maps/
   python3 scripts/canvas_gen.py --input skeleton.json --write

   # 生成卡片库紧凑索引（给 AI 做 Step 3 跨领域入网检索）
   python3 scripts/card_index.py

   # 抽取 3 张优先跨领域的旧卡片，准备 Step 4 变式考查
   python3 scripts/pick_review.py -n 3
   ```
