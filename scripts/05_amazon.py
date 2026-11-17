"""
角色 3：顾客研究员的数据 —— 亚马逊 “Customers say”（评论汇总 + 各话题提及数与情绪）

亚马逊在商品页上，根据该商品**全部**评论自动生成：
  ① 一段总结；② 一组话题（如 “Wifi connectivity(508)”），每个话题标注 正面/褒贬不一/负面 + 提及次数。
这比我们自己抽样几十条评论更有代表性：一款商品背后是上万条真实购买评论。

方式：通过 opencli 在用户自己的 Chrome 里打开普通商品页（只读、低频、不登录看单条评论）。
运行：.venv/bin/python scripts/05_amazon.py
输出：data/amazon/pages/<ASIN>.json、data/amazon_aspects.csv、data/amazon_products.csv
"""
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "amazon"
OC = str(Path.home() / ".claude/skills/opencli-web-reader/oc.sh")
SESSION = "az"
SEARCHES = {  # 每个品类搜一次，取前 N 个非广告、评论数 ≥ 200 的商品
    "智能喂食器": "smart cat feeder",
    "智能猫砂盆": "self cleaning cat litter box",
    "智能饮水机": "cat water fountain",
}
TOP_N = 6

EXTRACT_JS = r"""(()=>{
  const t=document.body.innerText;
  const i=t.indexOf("Customers say");
  let say=null;
  if(i>=0){ const s=t.slice(i+13,i+1600); say=s.split("AI Generated")[0].trim(); }
  const aspects=[...document.querySelectorAll("button[aria-label$='mentions']")].map(b=>{
    const m=b.getAttribute("aria-label").match(/^(\w+) aspect, (.+), (\d+) mentions$/);
    return m?{sentiment:m[1],aspect:m[2],mentions:+m[3]}:null}).filter(Boolean);
  const g=s=>document.querySelector(s)?.innerText?.trim().replace(/\s+/g," ")||null;
  return JSON.stringify({title:g("#productTitle"),price:g("#corePrice_feature_div .a-offscreen")||g(".a-price .a-offscreen"),
    rating:g("#acrPopover .a-icon-alt"),reviews:g("#acrCustomerReviewText"),say,aspects});
})()"""


def oc(*args, timeout=120):
    p = subprocess.run([OC, *args], capture_output=True, text=True, timeout=timeout)
    return p.stdout


def search(q):
    d = json.loads(oc("amazon", "search", q, "--window", "background"))
    return [x for x in d.get("data", []) if not x["is_sponsored"] and (x["review_count"] or 0) >= 200]


def read_page(asin):
    oc("browser", "open", f"https://www.amazon.com/dp/{asin}", "--session", SESSION, "--window", "background")
    oc("browser", "wait", "time", "5", "--session", SESSION)
    for _ in range(5):  # 评论区是滚动后才加载的
        oc("browser", "scroll", "down", "--session", SESSION)
        oc("browser", "wait", "time", "2", "--session", SESSION)
    raw = json.loads(oc("browser", "eval", "--session", SESSION, EXTRACT_JS))
    page = json.loads(raw["data"])
    page.update(asin=asin, url=f"https://www.amazon.com/dp/{asin}",
                fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return page


if __name__ == "__main__":
    (OUT / "pages").mkdir(parents=True, exist_ok=True)
    products, aspects = [], []
    try:
        for cat, q in SEARCHES.items():
            items = search(q)[:TOP_N]
            print(f"{cat}: 搜索 “{q}” → 取 {len(items)} 款")
            for it in items:
                path = OUT / "pages" / f"{it['asin']}.json"
                page = json.loads(path.read_text()) if path.exists() else read_page(it["asin"])
                path.write_text(json.dumps(page, ensure_ascii=False))
                products.append({"category": cat, "asin": it["asin"], "title": it["title"],
                                 "price_usd": it["price_value"], "rating": it["rating_value"],
                                 "review_count": it["review_count"], "customers_say": page["say"],
                                 "url": page["url"], "fetched_at": page["fetched_at"]})
                for a in page["aspects"]:
                    aspects.append({"category": cat, "asin": it["asin"], "title": it["title"][:60], **a})
                print(f"  {it['asin']} {it['rating_value']}★ {it['review_count']} 评 | 话题 {len(page['aspects'])} 个")
                time.sleep(6)  # 礼貌间隔
    finally:
        oc("browser", "close", "--session", SESSION)
    pd.DataFrame(products).to_csv(ROOT / "data" / "amazon_products.csv", index=False)
    pd.DataFrame(aspects).to_csv(ROOT / "data" / "amazon_aspects.csv", index=False)
    print(f"完成：{len(products)} 款商品，{len(aspects)} 条话题记录")
