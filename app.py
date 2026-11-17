"""
ANCHOR · 用 AI 从欧美市场数据到新品 —— 可交互 Demo
运行：.venv/bin/streamlit run app.py
"""
import base64
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
D, O, A = ROOT / "data", ROOT / "outputs", ROOT / "assets"
CORE = ["智能猫砂盆", "智能喂食器", "智能饮水机"]
OAT, INK, ACCENT = "#efe7da", "#2b2723", "#c9772e"

st.set_page_config(page_title="ANCHOR · AI 新品开发", page_icon="🐾", layout="wide")
st.markdown(f"""
<style>
  .block-container {{padding-top: 1.6rem; max-width: 1200px;}}
  h1, h2, h3 {{letter-spacing: -0.01em;}}
  .pill {{display:inline-block;padding:2px 10px;border-radius:999px;background:{OAT};color:{INK};
          font-size:.8rem;margin:0 6px 6px 0;border:1px solid #ddd2c0}}
  .flow {{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:.4rem 0 1rem}}
  .flow div {{background:{OAT};border:1px solid #ddd2c0;border-radius:10px;padding:8px 12px;font-size:.9rem}}
  .flow span {{color:{ACCENT};font-weight:700}}
  .src {{font-size:.78rem;color:#8a8076}}
  .ai {{font-size:.72rem;background:#2b2723;color:#fff;padding:1px 6px;border-radius:4px}}
</style>""", unsafe_allow_html=True)


# ---------------- 数据加载 ----------------
@st.cache_data
def load():
    p = pd.read_csv(D / "products.csv")
    fm = pd.read_csv(O / "feature_matrix.csv")
    asp = pd.read_csv(D / "amazon_aspects.csv")
    ap = pd.read_csv(D / "amazon_products.csv")
    rd = pd.read_csv(D / "reddit_threads.csv")
    x = pd.read_csv(D / "x_posts.csv")
    return p, fm, asp, ap, rd, x


def md(name):
    return (O / name).read_text()


def img_b64(name):
    return base64.b64encode((A / name).read_bytes()).decode()


products, fmatrix, aspects, amz, reddit, xposts = load()
main = products[products.category.isin(CORE) & ~products.is_bundle & ~products.for_dog_only & ~products.is_duplicate]

# ---------------- 头部 ----------------
st.markdown("### 🐾 AI 新品开发挑战 · 猫用智能硬件 × 欧美市场")
st.markdown('<div class="flow"><div>① 市场数据</div><span>→</span><div>② AI 市场洞察</div><span>→</span>'
            '<div>③ 挑刺复核</div><span>→</span><div>④ 新品机会与方案</div><span>→</span><div>⑤ AI 新品设计</div>'
            '<span>→</span><div>⑥ 换个品类再跑一遍</div></div>', unsafe_allow_html=True)

tabs = st.tabs(["首页", "① 数据", "② 洞察", "③ 挑刺", "④ 新品方案", "⑤ 设计", "⑥ 换品类重跑", "方法论"])

# ======================= 首页 =======================
with tabs[0]:
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.image(str(A / "01_hero_gpt.jpg"), use_container_width=True)
        st.markdown('<span class="ai">AI 生成</span> <span class="src">GPT Image · 提示词见“⑤ 设计”</span>', unsafe_allow_html=True)
    with c2:
        st.markdown("## ANCHOR")
        st.markdown("#### 断网不断粮，喂没喂到它自己会称。")
        st.write("一台给欧美上班族的**离线优先、免订阅、称重闭环**的猫喂食器。"
                 "这个方向不是拍脑袋，而是从 8 个品牌官网、18 款亚马逊热销品（约 14 万条评论汇总）、Reddit 和 X 的用户原话里一步步推出来的。")
        k1, k2, k3 = st.columns(3)
        k1.metric("官网商品", f"{len(products)}", f"{len(main)} 款主机")
        k2.metric("亚马逊评论（去重）", "≈14 万", "18 款热销品")
        k3.metric("建议零售价", "$119", "Pro $149")
        st.markdown("**AI 团队分工**")
        st.markdown(
            "| 角色 | 由谁担任 | 产出 |\n|---|---|---|\n"
            "| 数据员 | Python 脚本（不用 AI） | 官网 / 亚马逊 / Reddit / X 原始数据 |\n"
            "| 分析师 · 顾客研究员 | Claude | 功能矩阵、痛点、机会点 |\n"
            "| **挑刺员** | **DeepSeek 推理模型（换一家）** | 推翻了 2 个结论、改了产品承诺 |\n"
            "| 产品经理 | Claude | 新品方案 v2 |\n"
            "| 设计师 | Claude 写提示词 → GPT Image 出图 | 4 张一致的设计图 |")

# ======================= ① 数据 =======================
with tabs[1]:
    st.subheader("① 市场数据：全部真实、可追溯")
    st.caption("每一行都保留原始链接和抓取时间；AI 生成或推测的内容在页面上单独标注。")
    src = pd.DataFrame([
        ["品牌官网（Shopify 公开商品接口）", "8 个品牌", f"{len(products)} 条商品 → {len(main)} 款主机", "供给：在卖什么、怎么定价、宣传什么"],
        ["亚马逊 “Customers say”", "3 个品类 × 前 6 款", f"{len(aspects)} 条话题（情绪+提及次数）", "需求（量化）：亚马逊根据全部评论汇总"],
        ["Reddit", "5 个讨论帖", f"{len(reddit)} 条帖子/评论", "需求（深度）：为什么这么选"],
        ["X", "2 组搜索（之后被限流）", f"{int(xposts.relevant.sum())} 条相关", "补充线索"],
    ], columns=["来源", "范围", "规模", "用途"])
    st.dataframe(src, hide_index=True, use_container_width=True)
    st.markdown("**没用上的来源（如实记录）：** YouTube 视频页要求登录验证、亚马逊单条评论需要登录 → 都没有绕过。")

    t1, t2, t3, t4 = st.tabs(["官网商品", "亚马逊热销品", "Reddit", "X"])
    with t1:
        cat = st.multiselect("品类", sorted(products.category.unique()), default=CORE)
        show = products[products.category.isin(cat)][["brand", "origin", "category", "title", "price_usd", "is_bundle", "url", "fetched_at"]]
        st.dataframe(show, hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("来源链接")})
    with t2:
        st.dataframe(amz[["category", "title", "price_usd", "rating", "review_count", "customers_say", "url"]],
                     hide_index=True, use_container_width=True, column_config={"url": st.column_config.LinkColumn("亚马逊链接")})
        st.caption("⚠️ “Customers say” 本身是亚马逊用 AI 生成的评论汇总；我们只用它的话题和提及次数，不引用评价性措辞。")
    with t3:
        st.dataframe(reddit, hide_index=True, use_container_width=True, column_config={"url": st.column_config.LinkColumn("帖子")})
    with t4:
        st.dataframe(xposts[xposts.relevant][["pain_tag", "likes", "text", "url"]], hide_index=True, use_container_width=True,
                     column_config={"url": st.column_config.LinkColumn("帖子")})

# ======================= ② 洞察 =======================
with tabs[2]:
    st.subheader("② AI 市场洞察")
    a, b = st.columns(2)
    with a:
        st.markdown("**供给：三大件扎堆，猫砂盆是高价战场**")
        fig = px.box(main, x="category", y="price_usd", color="category", points="all", hover_data=["brand", "title"],
                     color_discrete_sequence=["#c9772e", "#8a9a5b", "#6b8fb5"])
        fig.update_layout(showlegend=False, height=360, xaxis_title=None, yaxis_title="官网价格 (USD)", margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.markdown("**功能矩阵：提到该功能的产品比例（%）**")
        pv = fmatrix.pivot(index="功能", columns="品类", values="提到的比例%")
        fig = px.imshow(pv, text_auto=True, color_continuous_scale=["#faf6ef", "#c9772e"], aspect="auto")
        fig.update_layout(height=360, margin=dict(t=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("**需求：亚马逊上的负面和褒贬不一话题（提及次数）**")
    neg = aspects[aspects.sentiment.isin(["Negative", "Mixed"])].copy()
    neg = neg.drop_duplicates(["category", "aspect", "sentiment", "mentions"])  # 同款商品共用评论汇总 → 去重
    g = neg.groupby(["category", "aspect", "sentiment"], as_index=False).mentions.sum()
    sel = st.radio("品类", CORE, index=1, horizontal=True)
    gg = g[g.category == sel].sort_values("mentions").tail(10)
    fig = px.bar(gg, x="mentions", y="aspect", color="sentiment", orientation="h",
                 color_discrete_map={"Negative": "#b5523b", "Mixed": "#d9b68a"})
    fig.update_layout(height=380, yaxis_title=None, xaxis_title="提及次数（已去重）", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("完整洞察报告 v2（含每条结论的依据）", expanded=False):
        st.markdown(md("insights_v2.md"))

# ======================= ③ 挑刺 =======================
with tabs[3]:
    st.subheader("③ 挑刺复核：让另一家模型来审")
    st.write("同一个模型审自己的稿，容易犯同样的错。所以 **Claude 写、DeepSeek 推理模型审**，审出来的问题必须在方案里回应。")
    st.markdown("""
| 被挑出来的问题 | 结果 |
|---|---|
| v1 说“0% 喂食器做了称重” → 回官网原文核查 | **结论被推翻**：Petlibro 2026-08 已推出称重款，但健康提醒要订阅 → 机会点改为“免订阅” |
| “放心出门”和“断网本地报警”矛盾：人不在家，报警没人听见 | **产品承诺改为“断网不断粮”**，并写清断网时的边界 |
| “WiFi 负面 508 次”来自单一商品 | 措辞改为“头部产品上最集中的负面话题” |
| 30 天续航、1 克精度、成本倍率是估算却被当成事实 | 全部标 ⚠️，补单位经济表，删除“符合常见倍率”的结论 |
| “不信任中国云”只有 1 条原话却被当人群依据 | 移出人群依据，只留作风险提示 |
""")
    with st.expander("DeepSeek 推理模型的审查原文"):
        st.markdown(md("critic_deepseek.md"))
    with st.expander("洞察 v1（被修改前）"):
        st.markdown(md("insights_v1.md"))

# ======================= ④ 新品方案 =======================
with tabs[4]:
    st.subheader("④ 新品方案：ANCHOR")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image(str(A / "03_scene_gpt.jpg"), use_container_width=True)
        st.markdown('<span class="ai">AI 生成</span>', unsafe_allow_html=True)
    with c2:
        st.markdown("""
**卖给谁**：欧美白天上班的单猫 / 双猫家庭，被 WiFi 掉线或卡粮坑过。
**定价**：Base **$119**（单猫）/ Pro **$149**（加皮下芯片识别）。对标 Petlibro 称重款 $129.99（健康提醒另收订阅费）。
**刻意不做**：摄像头——拉高成本和功耗，和“安心、离线”的定位冲突。
""")
        ev = pd.DataFrame([
            ["断网不断粮", "WiFi 负面 508 次（单款）+ Reddit 宕机帖", "量化+质性"],
            ["称重确认出粮、卡粮报警", "卡粮负面 270 次（单款）+ X 原话", "量化+质性"],
            ["按克出粮", "份量褒贬不一 514 次", "弱"],
            ["免订阅健康趋势", "Petlibro 页面写明需订阅", "供给端事实"],
            ["认芯片不认项圈（Pro）", "Reddit：猫摘项圈", "质性"],
            ["防撞防偷、内置电池", "Reddit / X 原话；$29.99 款因电池被夸", "质性"],
        ], columns=["卖点", "依据", "证据等级"])
        st.dataframe(ev, hide_index=True, use_container_width=True)
    with st.expander("完整新品方案（目标用户、材料结构工艺、单位经济、风险）", expanded=False):
        st.markdown(md("product_plan.md"))

# ======================= ⑤ 设计 =======================
with tabs[5]:
    st.subheader("⑤ AI 新品设计")
    st.caption("一致性方法：每张图的提示词都以同一段“产品锚定描述”开头，并在同一个对话里要求“保持同一台产品”。")
    g1, g2 = st.columns(2)
    for col, (f, cap) in zip([g1, g2, g1, g2], [("01_hero_gpt.jpg", "主视觉效果图"), ("02_exploded_gpt.jpg", "结构爆炸图：拨轮出粮 + 称重传感器 + 配重底座"),
                                               ("03_scene_gpt.jpg", "生活场景"), ("04_closeup_gpt.jpg", "交互特写：旋钮 + 墨水屏，不用 App 也能设置")]):
        with col:
            st.image(str(A / f), use_container_width=True)
            st.markdown(f'<span class="ai">AI 生成 · GPT Image</span> <span class="src">{cap}</span>', unsafe_allow_html=True)

    st.markdown("#### 3D 模型（可拖动旋转）")
    model = (ROOT / "web" / "model3d.html").read_text().replace("/*THREEJS*/", (ROOT / "web" / "three.min.js").read_text())
    components.html(model, height=430)

    st.markdown("#### 广告海报（网页排版，文字 100% 准确）")
    poster = (ROOT / "web" / "poster.html").read_text().replace("{{HERO}}", img_b64("01_hero_gpt.jpg"))
    components.html(poster, height=560)

    if (A / "01_hero_doubao.jpg").exists():
        st.markdown("#### 生图模型对比：同一段提示词，谁更听话？")
        m1, m2 = st.columns(2)
        m1.image(str(A / "01_hero_gpt.jpg"), caption="GPT Image（ChatGPT，英文提示词）", use_container_width=True)
        m2.image(str(A / "01_hero_doubao.jpg"), caption="Seedream 5.0 Flash（豆包，中文提示词）", use_container_width=True)
        st.markdown("""
| 提示词要求 | GPT Image | Seedream 5.0 Flash |
|---|---|---|
| 鹅卵石外形、低矮宽底 | ✅ 拱顶圆润 | ❌ 圆角方盒 |
| 顶部墨水屏 | ✅ 顶部前倾，有内容 | ⚠️ 放在正面，空白 |
| 正上方铝合金旋钮 | ✅ | ✅ |
| 燕麦色底座 | ✅ | ✅ |
| 横贯正面的 LED 灯带 | ✅ | ⚠️ 只有一小段 |
| 右上侧透明粮仓窗 | ✅ | ✅ |
| 可拆 304 不锈钢碗 + 灰色环 | ✅ | ✅ |
| 可直接商用 | ✅ 无水印 | ⚠️ 带“豆包 AI 生成”水印 |
| **符合度** | **8/8** | **5/8** |

**结论**：两家都能出可用的产品渲染，但 GPT Image 对“外形、屏幕位置”这类关键设计约束更听话，所以主力用它；Seedream 适合做快速草图和中文场景。
*（只比了主视觉 1 张，样本小，结论仅针对本次提示词。）*""")
    with st.expander("出图提示词"):
        st.markdown(md("design_prompts.md"))

# ======================= ⑥ 换品类重跑 =======================
with tabs[6]:
    st.subheader("⑥ 换个品类，整条流水线再跑一遍")
    st.write("输入一个消费品类和几个欧美品牌官网（Shopify 独立站），AI 团队会实时完成：抓数据 → 打标签找空白 → 挑刺 → 出新品概念。")
    presets = {"咖啡器具（磨豆机、手冲壶、电水壶）": "fellowproducts.com, www.timemore.com, www.hario-usa.com",
               "自定义": ""}
    pick = st.radio("示例", list(presets), horizontal=True)
    cat_in = st.text_input("品类", value="" if pick == "自定义" else pick)
    doms = st.text_input("品牌官网（逗号分隔）", value=presets[pick])
    def show_result(res):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**分析师洞察**")
            st.markdown(res["insights"])
        with c2:
            st.markdown("**挑刺员意见（DeepSeek 推理模型）**")
            st.markdown(res["critic"])
        concept = res["concept"]
        st.markdown(f"### 新品概念：{concept.get('name')}")
        st.markdown(f"**{concept.get('one_liner')}** · 目标用户：{concept.get('target_user')} · 定价：${concept.get('price_usd')}")
        st.dataframe(pd.DataFrame(concept.get("selling_points", [])), hide_index=True, use_container_width=True)
        st.markdown("**材料与结构**：" + "；".join(concept.get("materials_structure", [])))
        st.markdown("**风险**：" + "；".join(concept.get("risks", [])))
        st.code(concept.get("image_prompt", ""), language=None)
        st.caption("出图提示词可直接粘贴到 GPT Image / 豆包。")

    cached = O / "rerun_coffee.json"
    if cached.exists() and st.button("📂 查看已缓存的示例结果（咖啡器具，秒开）"):
        res = json.loads(cached.read_text())
        st.info(f"缓存结果 · 品类：{res['category']} · 子品类：{', '.join(res['stats'])}")
        show_result(res)

    if st.button("▶ 运行 AI 团队（实时，约 1 分钟）", type="primary", disabled=not (cat_in and doms)):
        import pipeline as pl
        rows, errs = [], []
        with st.status("数据员：抓取品牌官网…", expanded=True) as s:
            for d in [x.strip() for x in doms.split(",") if x.strip()]:
                try:
                    r = pl.fetch_shopify(d)
                    rows += r
                    st.write(f"✅ {d}：{len(r)} 条")
                except Exception as e:
                    errs.append(d)
                    st.write(f"❌ {d}：{e}")
            if not rows:
                s.update(label="没有抓到数据（这些网站可能不是 Shopify 搭的）", state="error")
                st.stop()
            s.update(label="分析师：AI 打标签、统计功能…")
            vocab, tagged = pl.tag_products(rows, cat_in)
            mainp, stats = pl.feature_stats(tagged)
            st.write(f"主产品 {len(mainp)} 款；子品类：{', '.join(stats)}")
            s.update(label="分析师：写洞察…")
            ins = pl.analyst(cat_in, vocab, stats)
            s.update(label="挑刺员（DeepSeek 推理模型）：审查中…")
            crit = pl.critic(cat_in, ins)
            s.update(label="产品经理：出新品概念…")
            concept = pl.product_manager(cat_in, ins, crit)
            s.update(label="完成", state="complete")
        show_result({"insights": ins, "critic": crit, "concept": concept})
        with st.expander("AI 打过标签的原始数据"):
            st.dataframe(pd.DataFrame(tagged), use_container_width=True)

# ======================= 方法论 =======================
with tabs[7]:
    st.markdown(md("methodology.md"))
