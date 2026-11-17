"""
可复用流水线（Demo 里“换品类重跑”用）：输入任意消费品类 + 几个欧美品牌官网 → 自动跑完
  数据员（抓官网）→ 分析师（AI 打标签、找空白）→ 挑刺员（另一个推理模型审）→ 产品经理（出新品概念）

和猫用智能硬件那一版的区别：那一版的分类规则是我们手写的；这里把“打标签”交给大模型，
所以换任何品类都不用改代码——这就是“方法论可复制”的落地形式。
"""
import json
import os
import re
import html
import time
from collections import Counter

import requests

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
HEADERS = {"User-Agent": "Mozilla/5.0 (research demo; public product catalog)"}


def _key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    if not k:
        try:
            import streamlit as st
            k = st.secrets.get("DEEPSEEK_API_KEY")
        except Exception:
            pass
    if not k:
        raise RuntimeError("未配置 DEEPSEEK_API_KEY")
    return k


def llm(system, user, model="deepseek-chat", as_json=False, timeout=240):
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]}
    if as_json and model == "deepseek-chat":
        body["response_format"] = {"type": "json_object"}
    r = requests.post(DEEPSEEK_URL, headers={"Authorization": f"Bearer {_key()}"}, json=body, timeout=timeout)
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    if as_json:
        return json.JSONDecoder().raw_decode(text[text.index("{"):])[0]
    return text


# ---------- 角色 1：数据员 ----------
def fetch_shopify(domain, max_pages=2):
    domain = domain.strip().replace("https://", "").replace("http://", "").strip("/")
    out = []
    for page in range(1, max_pages + 1):
        r = requests.get(f"https://{domain}/products.json?limit=250&page={page}", headers=HEADERS, timeout=20)
        r.raise_for_status()
        batch = r.json().get("products", [])
        if not batch:
            break
        out += batch
        time.sleep(1)
    rows = []
    for p in out:
        prices = [float(v["price"]) for v in p["variants"] if v.get("price")]
        body = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p.get("body_html") or ""))).strip()
        rows.append({"brand": domain.split(".")[-2] if domain.count(".") >= 1 else domain,
                     "title": p["title"], "price_usd": prices[0] if prices else None,
                     "product_type": p.get("product_type") or "", "description": body[:400],
                     "url": f"https://{domain}/products/{p['handle']}"})
    return rows


# ---------- 角色 2：分析师（AI 打标签）----------
def balanced_sample(rows, total=160):
    """每个品牌均衡取样，避免第一个品牌占满样本。"""
    by = {}
    for r in rows:
        by.setdefault(r["brand"], []).append(r)
    per = max(total // max(len(by), 1), 10)
    return [r for items in by.values() for r in items[:per]][:total]


def tag_products(rows, category):
    sample = balanced_sample(rows)
    listing = "\n".join(f"{i}|{r['brand']}|${r['price_usd']}|{r['title'][:80]}|{r['description'][:160]}"
                        for i, r in enumerate(sample))
    vocab = llm(
        "你是消费品市场分析师。只输出 JSON。",
        f"品类：{category}。下面是欧美品牌官网商品（序号|品牌|价格|标题|描述），其中混有食品、耗材、配件，请忽略它们。\n"
        f"请给出：1) 该品类主产品的 3~6 个子品类 subcategories；2) 10~14 个可以从描述中判断的**产品功能/设计卖点** features"
        f"（如材质、温控、精度、容量、联网等，英文短语；不要用产地、口味这类非产品功能）。\n"
        f'格式：{{"subcategories":[...],"features":[...]}}\n{listing[:12000]}',
        as_json=True)
    tagged = []
    for start in range(0, len(sample), 40):
        chunk = "\n".join(listing.splitlines()[start:start + 40])
        res = llm(
            "你是严谨的数据标注员。只根据给定文字判断，不要猜。只输出 JSON。",
            f"子品类候选：{vocab['subcategories']}\n功能候选：{vocab['features']}\n"
            f"对每个商品判断：is_main_product（属于“{category}”这个品类的主产品=true；食品/耗材/配件/替换件/套装/礼品卡/服务=false），"
            f"subcategory，features（只列描述里明确提到的）。\n"
            f'格式：{{"items":[{{"i":序号,"is_main_product":true,"subcategory":"...","features":["..."]}}]}}\n{chunk}',
            as_json=True)
        for it in res.get("items", []):
            i = it.get("i")
            if isinstance(i, int) and 0 <= i < len(sample):
                tagged.append({**sample[i], **{k: it.get(k) for k in ("is_main_product", "subcategory", "features")}})
    return vocab, tagged


def feature_stats(tagged):
    main = [t for t in tagged if t.get("is_main_product")]
    by_sub = {}
    for t in main:
        by_sub.setdefault(t.get("subcategory") or "其他", []).append(t)
    stats = {}
    for sub, items in by_sub.items():
        prices = sorted(x["price_usd"] for x in items if x["price_usd"])
        cnt = Counter(f for x in items for f in (x.get("features") or []))
        stats[sub] = {"n": len(items), "brands": sorted({x["brand"] for x in items}),
                      "median_price": prices[len(prices) // 2] if prices else None,
                      "feature_share": {f: round(100 * c / len(items)) for f, c in cnt.most_common()}}
    return main, stats


def analyst(category, vocab, stats):
    return llm(
        "你是消费品市场分析师。用中文、Markdown。每条结论后用【】注明依据（来自哪组统计）。没有依据的推测必须标 ⚠️。",
        f"品类：{category}（目标市场：欧美）。功能候选：{vocab['features']}\n"
        f"官网主产品统计（子品类 → 款数、品牌、价格中位数、各功能提及占比%）：\n{json.dumps(stats, ensure_ascii=False)}\n\n"
        "请输出：1) 3 条供给端发现；2) 2~3 个候选机会点（哪些功能扎堆、哪些几乎没人做），每个说明依据和需要用需求端数据验证什么。不超过 350 字。")


# ---------- 角色 3：挑刺员（另一个推理模型）----------
def critic(category, insights):
    return llm(
        "你是严苛的数据审计员。用中文，Markdown 表格，不客套，不重写原文。",
        f"审查下面对“{category}”的洞察：逐条指出 依据不足 / 相关≠因果 / 样本偏差 / 估算当事实 的地方，并给出修改。不超过 250 字。\n\n{insights}",
        model="deepseek-reasoner")


# ---------- 角色 4：产品经理 ----------
def product_manager(category, insights, critique):
    return llm(
        "你是消费硬件产品经理。只输出 JSON。",
        f"品类：{category}，市场：欧美。基于洞察和挑刺意见，提出 1 个新品概念。挑刺员指出的问题必须在方案里回应。\n"
        '格式：{"name":"","one_liner":"","target_user":"","price_usd":0,"selling_points":[{"point":"","evidence":"","evidence_level":"量化/质性/估算"}],'
        '"materials_structure":[""],"risks":[""],"image_prompt":"英文出图提示词"}\n\n'
        f"# 洞察\n{insights}\n\n# 挑刺意见\n{critique}",
        as_json=True)
