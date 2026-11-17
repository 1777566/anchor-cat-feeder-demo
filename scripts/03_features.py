"""
角色 2（前半）：数据分析师 —— 功能点矩阵

问题：各家都在宣传哪些功能？哪些功能已经“人人都有”（拼不出差异），哪些“几乎没人做”（可能是机会）？
方法：在每款主机的官网描述里查功能关键词（透明、可复查），统计每个品类里有多少比例的产品提到该功能，
      再对比“有这个功能”和“没有”的产品价格中位数 → 看哪些功能能撑起溢价。

运行：.venv/bin/python scripts/03_features.py
输出：outputs/feature_matrix.csv、outputs/feature_by_product.csv
"""
import html
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CORE = ["智能猫砂盆", "智能喂食器", "智能饮水机"]

FEATURES = {
    "App远程控制": r"\bapp\b|remote(ly)? control|wi-?fi|smartphone",
    "摄像头": r"camera|video|\bvision\b",
    "AI识别": r"\bai\b|a\.i\.|recogni[sz]|facial|identif",
    "多猫区分": r"multi-?cat recogni|recogni[sz]e[sd]? (each|every|individual|multiple)|rfid|facial|individual cat|each cat",
    "体重/如厕记录": r"\bweigh|weight (track|monitor|record|change)|track(s|ing)? (weight|visits|usage)|visit(s)? (record|track)",
    "尿液/健康预警": r"urine|\bph\b|health (alert|report|monitor|insight|track)|early (warning|detection)|vet",
    "除味/杀菌": r"odou?r|deodori|uv-?c?\b|uvc|steril|ion",
    "开放式设计": r"open-?top|open-?view|open design",
    "无线/电池": r"cordless|wireless|battery|batteries",
    "不锈钢": r"stainless",
    "湿粮/鲜食": r"wet food|fresh-?made|fresh food|wet meal",
    "安全防夹": r"anti-?pinch|safety|infrared|safe(ly)? (sensor|stop)",
    "静音": r"quiet|silent|noise|\bdb\b",
    "免订阅": r"no subscription|subscription-?free|without subscription|no (monthly|hidden) fee",
    "智能家居生态": r"alexa|google home|homekit|matter",
}


def load_full_text():
    """从原始 JSON 取完整描述（products.csv 里只截了前 600 字）。"""
    full = {}
    for f in (ROOT / "data" / "raw").glob("*.json"):
        rec = json.loads(f.read_text())
        for p in rec["products"]:
            body = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
            text = " ".join([p["title"], html.unescape(body), " ".join(p.get("tags") or [])])
            full[(rec["brand"], p["title"])] = re.sub(r"\s+", " ", text).lower()
    return full


df = pd.read_csv(ROOT / "data" / "products.csv")
d = df[df.category.isin(CORE) & ~df.is_bundle & ~df.for_dog_only & ~df.is_duplicate].copy()
full = load_full_text()
d["text"] = [full.get((b, t), "") for b, t in zip(d.brand, d.title)]
for name, pat in FEATURES.items():
    d[name] = d.text.str.contains(pat, regex=True)

(ROOT / "outputs").mkdir(exist_ok=True)
d.drop(columns=["text", "description"]).to_csv(ROOT / "outputs" / "feature_by_product.csv", index=False)

rows = []
for cat, g in d.groupby("category"):
    for name in FEATURES:
        has = g[g[name]]
        rows.append({
            "品类": cat, "功能": name, "样本数": len(g),
            "提到的比例%": round(100 * len(has) / len(g)),
            "有该功能·价格中位数": has.price_usd.median() if len(has) else None,
            "无该功能·价格中位数": g[~g[name]].price_usd.median() if len(has) < len(g) else None,
            "提到的品牌": ", ".join(sorted(has.brand.unique())),
        })
m = pd.DataFrame(rows)
m.to_csv(ROOT / "outputs" / "feature_matrix.csv", index=False)

pd.set_option("display.width", 220)
print(f"样本：{len(d)} 款主机单品（{', '.join(f'{c} {n}' for c, n in d.category.value_counts().items())}）\n")
pivot = m.pivot(index="功能", columns="品类", values="提到的比例%")
print("各品类中提到该功能的产品比例（%）")
print(pivot.sort_values("智能猫砂盆", ascending=False))
