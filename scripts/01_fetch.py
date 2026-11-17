"""
角色 1：数据员 —— 从品牌官网抓取公开商品数据（不用 AI）

原理：很多欧美电商独立站用 Shopify 搭建，Shopify 会在
  https://品牌域名/products.json
公开所有在售商品（名称、价格、规格、上架时间、描述）。这是品牌官方数据，真实、可追溯。

运行：.venv/bin/python scripts/01_fetch.py
输出：data/raw/<品牌>.json   （原始数据，原封不动保存，方便以后核对）
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests

# 品牌清单：品牌名, 官网域名, 出身（用来对比“中国出海品牌 vs 欧美本土品牌”）
BRANDS = [
    ("Petlibro", "petlibro.com", "中国团队出海"),
    ("PETKIT", "petkit.com", "中国品牌出海"),
    ("CATLINK", "www.catlinkus.com", "中国品牌出海"),
    ("Neakasa", "neakasa.com", "中国品牌出海"),
    ("Meowant", "www.meowant.com", "中国品牌出海"),
    ("UAHPET", "www.uahpet.com", "中国品牌出海"),
    ("PAWBBY", "www.pawbby.com", "中国品牌出海"),
    ("CATGENIE", "www.catgenie.com", "美国本土"),
]

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
HEADERS = {"User-Agent": "Mozilla/5.0 (research script; public product catalog)"}


def fetch_brand(brand):
    name, domain, origin = brand
    products, page = [], 1
    while True:
        url = f"https://{domain}/products.json?limit=250&page={page}"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()  # 网站报错就直接失败，不偷偷用旧数据
        batch = r.json().get("products", [])
        if not batch:
            break
        products += batch
        page += 1
        time.sleep(1)  # 礼貌抓取：每页间隔 1 秒
    record = {
        "brand": name,
        "origin": origin,
        "source": f"https://{domain}/products.json",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "products": products,
    }
    (RAW_DIR / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False))
    return name, len(products)


if __name__ == "__main__":
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    # 各品牌互不相干 → 同时抓（这是整条流水线里唯一值得“并行”的一步）
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch_brand, b): b[0] for b in BRANDS}
        for f, name in futures.items():
            try:
                brand, n = f.result()
                print(f"✅ {brand}: {n} 个商品")
            except Exception as e:
                print(f"❌ {name}: 抓取失败 —— {e}")
