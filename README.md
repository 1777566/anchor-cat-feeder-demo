# ANCHOR · 用 AI 从欧美市场数据到新品（智贸星途 AI 新品开发挑战）

**品类**：猫用智能硬件 · **市场**：欧美 · **新品**：ANCHOR 离线优先、免订阅、称重闭环的猫喂食器

## 核心流程
市场数据 → AI 市场洞察 → 挑刺复核（换一家模型）→ 新品机会与方案 → AI 新品设计（图片 + 3D + 海报）→ 换品类实时重跑

## 本地运行
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
mkdir -p .streamlit && echo 'DEEPSEEK_API_KEY = "你的key"' > .streamlit/secrets.toml   # 仅“换品类重跑”需要
.venv/bin/streamlit run app.py
```

## 目录
| 路径 | 内容 |
|---|---|
| `scripts/01_fetch.py` `02_clean.py` | 数据员：品牌官网抓取与清洗 |
| `scripts/03_features.py` | 分析师：功能矩阵 |
| `scripts/04_youtube.py` `05_amazon.py` | 需求端数据（YouTube 因登录验证未使用） |
| `scripts/06_critic.py` | 挑刺员：DeepSeek 推理模型审稿 |
| `pipeline.py` | 可复用流水线（换品类重跑） |
| `app.py` | Demo 网页 |
| `data/` | 原始与清洗后的数据（每行带来源链接与抓取时间） |
| `outputs/` | 洞察 v1/v2、挑刺意见、新品方案、出图提示词、**方法论说明** |
| `assets/` | AI 生成的设计图（均已标注） |

所有市场数据来自公开页面；AI 生成或推测的内容在页面和文档中均已标注。
