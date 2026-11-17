# 设计师角色：ANCHOR 出图提示词

> 设计师角色（Claude）根据 `product_plan.md` 写成。
> **一致性规则（对应加分项 6“产品设计一致性”）：** 每张图的提示词都以同一段“产品锚定描述”开头，只改变场景和视角。这样概念图、结构图、场景图、包装图里出现的是同一台产品。
> 所有生成的图片在 Demo 里都标注“AI 生成”。

## 产品锚定描述（每张图都原样粘贴）
**中文：**
一台名为 ANCHOR 的智能猫粮喂食器：外形像一块被水冲圆的鹅卵石，低矮宽底，高约 28 厘米。外壳是暖白色哑光细砂纹塑料，底部一圈燕麦色。顶部嵌一块小尺寸黑白电子墨水屏，旁边是一个拉丝铝合金旋钮。正面下方是一个可拆卸的 304 不锈钢圆碗，碗口有一圈细细的浅灰色环。正面中间有一条柔和的暖白色 LED 状态灯带。上半部是带透明窗的粮仓，能看到里面的猫粮。整体是北欧极简家居风，没有任何品牌 logo 以外的装饰。

**English（备用，部分工具英文效果更好）：**
A smart cat food feeder named ANCHOR, shaped like a smooth river pebble, low and wide-based, about 28 cm tall. Warm-white matte fine-textured plastic shell with an oat-beige band at the base. A small black-and-white e-ink display and a brushed aluminum knob on top. A removable round 304 stainless steel bowl at the front bottom, with a thin light-gray ring around the bowl rim. A soft warm-white LED status strip across the front. A food hopper with a clear window showing kibble. Scandinavian minimalist home-appliance design, no decorations besides a small "ANCHOR" wordmark.

## 5 张图
| # | 用途 | 对应加分项 | 场景提示词（接在锚定描述后面） |
|---|---|---|---|
| 1 | **主视觉效果图** | ①视觉审美 | 产品摄影棚拍摄，三分之二侧前方视角，浅燕麦色无缝背景，柔和窗光从左侧照入，地面有柔和阴影，超写实产品渲染，8K，细节清晰 |
| 2 | **结构爆炸图** | ③空间表现、⑥一致性 | 等距视角的产品爆炸分解图，部件沿竖直方向分开排列：顶盖与墨水屏和旋钮、透明粮仓与密封圈、硅胶软叶片拨轮出粮机构、主控电路板与可充电电池、称重传感器、不锈钢碗、带配重块的底座。白色背景，工业设计说明图风格，部件之间有细引线，干净精确 |
| 3 | **生活场景图** | ②艺术表现、⑦商业化 | 傍晚的北欧风客厅，木地板，窗外是黄昏的城市灯光；一只英国短毛猫正在从喂食器的碗里吃东西；墨水屏显示 “18:00 ✓ 23g”；暖色调，电影感，浅景深 |
| 4 | **交互特写** | ①视觉审美、⑦商业化 | 俯拍顶部特写：电子墨水屏清楚显示 “Last meal 07:00 ✓ 23 g eaten · Wi-Fi off · Next 18:00”，一只手正在转动拉丝铝合金旋钮，背景虚化，微距产品摄影 |
| 5 | **包装与广告海报** | ⑦商业化呈现 | 一张广告海报：左边是牛皮纸色包装盒，正面印着 “ANCHOR — Feeds without Wi-Fi. Knows if your cat ate.”；右边是喂食器实物；底部一行大字标语 “Your Wi-Fi can go down. Dinner can't.”；杂志广告排版，留白充足，暖色 |

## 使用说明
- 每张图都生成 2~4 张候选，**挑和第 1 张主视觉最一致的那张**：看外形比例、颜色、旋钮位置是否一致。
- 图里出现的文字（屏幕内容、标语），AI 常常会写错。可以在 Demo 里用网页文字叠加在图上，不要依赖 AI 写字。
- 保存时按 `01_hero.png`、`02_exploded.png` …… 命名，放进 `assets/`。
