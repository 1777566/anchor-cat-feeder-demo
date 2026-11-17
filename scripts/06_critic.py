"""
角色 4：挑刺员 —— 用“另一家”的模型审查 Claude 写的洞察和方案

为什么换模型：同一个模型审自己的稿，容易犯同样的错（视频里提到 Cognition 的经验：审查者要和作者分开）。
这里 Claude 写、DeepSeek 推理模型审。

运行：.venv/bin/python scripts/06_critic.py
需要：环境变量 DEEPSEEK_API_KEY
输出：outputs/critic_deepseek.md
"""
import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
KEY = os.environ["DEEPSEEK_API_KEY"]

SYSTEM = """你是一位严苛的消费硬件产品评审和数据审计员，专门给别人的市场洞察和新品方案挑刺。
规则：
1. 逐条检查方案里的每个卖点和数字：有没有给出数据依据？依据是否真的支持这个结论（相关≠因果、样本量、选择偏差）？
2. 标出所有“没有依据的断言”和“估算被当成事实”的地方。
3. 指出方案最可能失败的 3 个原因（技术、成本、需求、竞争）。
4. 给出最多 5 条具体修改建议，按重要性排序。
5. 用中文，Markdown 表格优先，不要客套话，不要重写整份方案。"""


def main():
    insights = (ROOT / "outputs" / "insights_v2.md").read_text()
    plan = (ROOT / "outputs" / "product_plan.md").read_text()
    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {KEY}"},
        json={"model": "deepseek-reasoner",
              "messages": [{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": f"# 市场洞察\n{insights}\n\n# 新品方案\n{plan}"}]},
        timeout=300,
    )
    r.raise_for_status()
    msg = r.json()["choices"][0]["message"]["content"]
    usage = r.json().get("usage", {})
    (ROOT / "outputs" / "critic_deepseek.md").write_text(
        f"# 挑刺员（DeepSeek 推理模型）审查意见\n\n> 模型：deepseek-reasoner；tokens：{json.dumps(usage)}\n\n{msg}\n")
    print(msg)


if __name__ == "__main__":
    main()
