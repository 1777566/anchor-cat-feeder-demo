"""
角色 1（续）：数据员 —— 把原始 JSON 整理成一张干净的表

做三件事：
  1. 去掉“不是商品”的条目（运费险、保修、付款链接、赠品）
  2. 按关键词给每个商品分类（猫砂盆 / 喂食器 / 饮水机 / ... / 耗材配件）
  3. 每一行都保留商品链接 + 抓取时间 → 任何结论都能点回原始页面核对

运行：.venv/bin/python scripts/02_clean.py
输出：data/products.csv
"""
import html
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# —— 分类规则 ——
# 为什么用关键词而不用 AI？规则透明、可复查、零成本；AI 留给需要“理解”的环节。
# 教训：最早用“子串匹配”，结果 "mat"（垫子）匹配到了 "Automatic"，自动猫砂盆全被当成了配件。
#       所以现在用 \b 整词匹配，并且分三层判断。
def has(text, words):
    return any(re.search(rf"\b{w}\b", text) for w in words)

NOT_PRODUCT = ["protection", "worry-free", "payment", "warranty", "gift card", "shipping",
               "insurance", "100% off", "e-gift", "plan", "video cloud", "petlibro care",
               "exchange and price"]
# 第 1 层：一看就是配件/耗材的词（优先于设备词判断）
STRONG_ACC = ["replacement", "replaced", "accessories", "refills?", "filters?", "waste bags?",
              "trash bags?", "liners?", "pump", "cleaning set", "sifter", "front-entry hood",
              "raised stand", "geniedoor", "geniedome", "tags?", "attachment", "odor eliminator",
              "cube", "desiccant", "remover", "fence( 2\\.0)?", "mats?", "step",
              "crystal litter", "saver rings", "cylinder", "base replacement",
              # “for 某品牌/某型号” = 给那台设备用的配件
              "(only )?for (all )?(catlink|petkit|purobot|puramax|scooper|scoop|luma|catgenie|"
              "neakasa|m1|meowant|dockstream|granary|eversweet)"]
# 第 2 层：设备词（产品线名也算，比如 Petlibro 的 Luma 是猫砂盆）
DEVICE = [
    ("智能猫砂盆", ["litter box", "litter robot", "scooper", "scoop robot", "self-cleaning",
                  "catgenie", "purobot", "luma", "puramax", "genie units"]),
    ("智能喂食器", ["feeders?", "feeding", "granary"]),
    ("智能饮水机", ["fountains?", "eversweet", "dockstream"]),
    ("除味/净化", ["air purifier", "fresh air", "deodorizer"]),
    ("宠物摄像头", ["camera", "cam"]),
    ("烘干/美容", ["dryer", "grooming", "vacuum"]),
    ("定位/健康", ["gps", "tracker", "scale"]),
    ("智能玩具", ["toy", "laser", "launcher"]),
]
# 第 3 层：普通耗材
WEAK_ACC = ["cat litter", "granules", "brush", "pads?", "mats?", "liners?", "cartridges?",
            "curtain", "ramp", "sidewalls", "adapter", "hose", "soak", "spray", "cable",
            "charger", "battery", "bowls?", "tray", "cover", "sticker", "sensor", "shield",
            "base", "pedal", "fence", "disposal", "gel", "clipper", "trimmer", "comb"]
BUNDLE = ["bundle", "ecosystem", "combo", "set", "kit", "essentials", "\\d-pack", "double"]


def device_of(t):
    for cat, keys in DEVICE:
        if has(t, keys):
            return cat
    return None


def classify(title, ptype, price):
    t = f"{title} {ptype}".lower()
    if any(k in t for k in NOT_PRODUCT):
        return "非商品"
    dev = device_of(t)
    if has(t, STRONG_ACC):
        # 价格护栏：标题里既有设备词又有配件词（如“猫砂盆 + 踏板套装”），
        # 且价格 ≥ $120、又不是“replacement”，那它其实是设备本体
        if dev and price and price >= 120 and "replacement" not in t:
            return dev
        return "耗材配件"
    if dev:
        return dev
    if has(t, WEAK_ACC):
        return "耗材配件"
    if has(t, BUNDLE):
        return "多品类套装"
    return "其他（非智能用品）"


def strip_html(s, n=600):
    text = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()[:n]


rows = []
for f in sorted((ROOT / "data" / "raw").glob("*.json")):
    rec = json.loads(f.read_text())
    domain = rec["source"].split("/")[2]
    for p in rec["products"]:
        prices = [float(v["price"]) for v in p["variants"] if v.get("price")]
        compares = [float(v["compare_at_price"]) for v in p["variants"] if v.get("compare_at_price")]
        price = prices[0] if prices else None  # 取第一个规格的价格 = 商品页默认显示的价格
        compare = max(compares) if compares else None
        title_l = p["title"].lower()
        rows.append({
            "brand": rec["brand"],
            "origin": rec["origin"],
            "title": p["title"],
            "category": classify(p["title"], p.get("product_type") or "", price),
            "for_dog_only": ("dog" in title_l and "cat" not in title_l),
            "is_bundle": has(title_l, BUNDLE),
            "price_usd": price,
            "price_min_usd": min(prices) if prices else None,
            "price_max_usd": max(prices) if prices else None,
            "compare_at_usd": compare,  # 划线原价
            "discount_pct": round((1 - price / compare) * 100, 1) if price and compare and compare > price else 0.0,
            "variants": len(p["variants"]),
            "product_type": p.get("product_type") or "",
            "tags": ", ".join(p.get("tags") or [])[:200],
            "published_at": (p.get("published_at") or "")[:10],
            "description": strip_html(p.get("body_html")),
            "url": f"https://{domain}/products/{p['handle']}",
            "fetched_at": rec["fetched_at"],
        })

df = pd.DataFrame(rows)
# 同一款商品在官网重复上架（如 Petlibro 的 “Granary Smart Feeder” 和 “... for pet”）→ 标记重复，分析时只算一次
df["title_key"] = df.title.str.lower().str.replace(r"\s+for pets?$", "", regex=True).str.strip()
df["is_duplicate"] = df.duplicated(["brand", "title_key", "price_usd"])
df = df.drop(columns="title_key")
df.to_csv(ROOT / "data" / "products.csv", index=False)

# —— 打印一个小结，方便人工检查分类对不对 ——
pd.set_option("display.width", 200)
print(f"共 {len(df)} 行，来自 {df.brand.nunique()} 个品牌\n")
print(pd.crosstab(df.category, df.brand, margins=True, margins_name="合计"))
