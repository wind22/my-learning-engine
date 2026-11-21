# my-learning-engine

个人决策与深度学习工作流的**系统本体 + UI 改造真源**（1 套引擎可同时驱动 N 个知识库）：沉淀“知识地图 → 原子卡片 → 思维模型 → 决策辅导与检验”的完整 Prompt、MCP 配置、零依赖 Python 脚本与 Obsidian UI 真源。

## 目录结构

```text
my-learning-engine/
├── .env.example                # 环境变量模板（复制为 .env，已被 gitignore）
├── prompts/                    # 5 步深度学习与决策检验闭环 Prompt
│   ├── 00-system-mentor.md     # 总控角色（深度学习导师 + 决策红队）
│   ├── 01-icebreaker-map.md    # Step 1: 破冰建地图（白板 .canvas + 导图 .md）
│   ├── 02-socratic-drill.md    # Step 2: 实战拷问（暴露盲区与失效边界）
│   ├── 03-atomic-card.md       # Step 3: 沉淀原子卡片 + 跨领域入网
│   ├── 04-extract-model.md     # Step 4: 从多张卡片提纯思维模型（触发信号 + Checklist）
│   └── 05-decision-coach.md    # Step 5: 事前决策辅导 + 事后验尸反哺模型 + 变式演练
├── obsidian/                   # 所有 Obsidian UI/插件/配置改造的唯一真源
│   ├── config/                 # 核心配置、7 插件清单与无密钥默认参数
│   ├── snippets/               # 自定义 CSS 片段（deep-learning-ui.css）
│   ├── themes/                 # 自定义/固化主题
│   └── plugins/                # 自研 Obsidian TS 插件源码
├── mcp/                        # MCP 接入配置与说明
│   ├── README.md
│   └── mcp-config.example.json
└── scripts/                    # 纯 Python 标准库脚本（零第三方依赖）
    ├── config.py               # Vault 路径解析（环境变量 / .env）
    ├── sync_obsidian.py        # Obsidian UI 同步与社区插件一键安装（push / pull / install-plugins）
    ├── canvas_gen.py           # 从骨架 JSON 生成 Obsidian JSON Canvas (.canvas)
    ├── card_index.py           # 扫描 30-Models/ 与 20-Cards/ 生成紧凑索引供 AI 检索
    └── pick_review.py          # 抽取到期待检验决策、思维模型或原子卡片
```

## 快速开始

```bash
# 1) 分发 UI 配置并一键安装 7 个社区插件（新知识库加 --vault <路径> 即可复用）
python3 scripts/sync_obsidian.py push --force-defaults
python3 scripts/sync_obsidian.py install-plugins

# 2) 生成白板到 Vault 的 10-Maps/
python3 scripts/canvas_gen.py --input skeleton.json --write

# 3) 生成思维模型 + 原子卡片紧凑索引（供 AI 检索入网或决策辅导）
python3 scripts/card_index.py --scope all

# 4) 查看到期待验尸的决策 / 抽取模型或卡片演练
python3 scripts/pick_review.py --mode decisions
python3 scripts/pick_review.py --mode models -n 2
python3 scripts/pick_review.py --mode cards -n 3
```
