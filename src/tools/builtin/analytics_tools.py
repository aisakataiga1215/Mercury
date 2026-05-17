import csv, os
from datetime import datetime, timedelta
from collections import defaultdict
from src.tools.base import ToolCategory
from src.tools import register_tool
from utils.path_tool import get_abs_path


def _load_csv(filename: str) -> list[dict]:
    path = get_abs_path(f"data/{filename}")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


@register_tool(
    name="get_order_metrics",
    description="获取指定日期范围的订单核心指标：UV/转化率/客单价/订单量/GMV/退款率/TOP品类，支持 today/yesterday/last_7_days/last_30_days",
    input_schema={
        "type": "object",
        "properties": {
            "date_range": {"type": "string", "description": "日期范围: today/yesterday/last_7_days/last_30_days 或 YYYY-MM-DD~YYYY-MM-DD"},
        },
        "required": ["date_range"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def get_order_metrics(date_range: str) -> str:
    orders = _load_csv("orders.csv")
    if not orders:
        return "无订单数据"

    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if date_range == "today":
        target = [o for o in orders if o["date"] == today_str]
        label = f"今日({today_str})"
    elif date_range == "yesterday":
        target = [o for o in orders if o["date"] == yesterday_str]
        label = f"昨日({yesterday_str})"
    elif date_range == "last_7_days":
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        target = [o for o in orders if o["date"] >= cutoff]
        label = "近7日"
    elif date_range == "last_30_days":
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        target = [o for o in orders if o["date"] >= cutoff]
        label = "近30日"
    elif "~" in date_range:
        start, end = date_range.split("~")
        target = [o for o in orders if start <= o["date"] <= end]
        label = f"{start}~{end}"
    else:
        target = [o for o in orders if o["date"] == date_range]
        label = date_range

    if not target:
        return f"{label} 无订单数据"

    # Also fetch previous period for comparison
    n = len(target)
    all_dates = sorted(set(o["date"] for o in orders))
    target_dates = set(o["date"] for o in target)
    prev_dates = [d for d in all_dates if d not in target_dates][-n:] if len(all_dates) > n else []

    def aggregate(rows):
        uv = sum(int(r["uv"]) for r in rows)
        orders_cnt = sum(int(r["orders"]) for r in rows)
        gmv = sum(float(r["gmv"]) for r in rows)
        cvr = orders_cnt / max(uv, 1) * 100
        aov = gmv / max(orders_cnt, 1)
        refund = sum(float(r["refund_rate"].replace("%", "")) for r in rows) / len(rows)
        top_cat = defaultdict(int)
        for r in rows:
            top_cat[r["top_category"]] += int(r["orders"])
        return uv, orders_cnt, gmv, cvr, aov, refund, top_cat

    cur_uv, cur_orders_cnt, cur_gmv, cur_cvr, cur_aov, cur_refund, cur_top = aggregate(target)

    result = f"## {label} 核心指标\n"
    result += f"UV: {cur_uv:,} | 订单量: {cur_orders_cnt:,} | GMV: ¥{cur_gmv:,.2f}\n"
    result += f"转化率: {cur_cvr:.2f}% | 客单价: ¥{cur_aov:.2f} | 退款率: {cur_refund:.2f}%\n"

    if prev_dates:
        prev_rows = [o for o in orders if o["date"] in prev_dates]
        p_uv, p_ord, p_gmv, p_cvr, p_aov, p_refund, _ = aggregate(prev_rows)
        uv_chg = (cur_uv - p_uv) / max(p_uv, 1) * 100
        gmv_chg = (cur_gmv - p_gmv) / max(p_gmv, 1) * 100
        cvr_chg = cur_cvr - p_cvr
        result += f"\n环比变化: UV {uv_chg:+.1f}% | GMV {gmv_chg:+.1f}% | 转化率 {cvr_chg:+.1f}pp\n"

    result += "\nTOP品类 (按订单量):\n"
    for cat, cnt in sorted(cur_top.items(), key=lambda x: x[1], reverse=True)[:5]:
        result += f"  {cat}: {cnt}单\n"

    return result


@register_tool(
    name="get_promotion_data",
    description="获取指定SKU或品类历史促销活动数据：活动类型/预算/折扣/GMV提升倍数/ROI/转化提升",
    input_schema={
        "type": "object",
        "properties": {
            "sku_or_category": {"type": "string", "description": "SKU编码或品类名称"},
        },
        "required": ["sku_or_category"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def get_promotion_data(sku_or_category: str) -> str:
    promotions = _load_csv("promotions.csv")
    products = _load_csv("products.csv")

    # Determine if it's a SKU or category
    sku_map = {p["sku"]: p for p in products}
    if sku_or_category in sku_map:
        matched = [p for p in promotions if p["sku"] == sku_or_category]
        label = f"SKU {sku_or_category}"
    else:
        # match by category
        category_skus = {p["sku"] for p in products if p["category"] == sku_or_category}
        matched = [p for p in promotions if p["sku"] in category_skus]
        label = f"品类 {sku_or_category}"

    if not matched:
        return f"{label} 无历史促销记录"

    result = f"{label} 历史促销分析 ({len(matched)}次活动):\n"
    # Aggregate by type
    by_type = defaultdict(list)
    for p in matched:
        by_type[p["type"]].append(float(p["roi"]))

    result += "\n按活动类型汇总:\n"
    for ptype, rois in by_type.items():
        avg_roi = sum(rois) / len(rois)
        result += f"  {ptype}: {len(rois)}次 | 平均ROI {avg_roi:.1f} | 最高ROI {max(rois):.1f}\n"

    result += "\n最近5次活动详情:\n"
    for p in matched[-5:]:
        result += (
            f"  {p['date']} | {p['type']} | 预算¥{p['budget']} | "
            f"折扣{p['discount_level']} | GMV提升{p['gmv_uplift']} | "
            f"ROI {p['roi']} | 转化提升{p['conversion_uplift']}\n"
        )
    return result


@register_tool(
    name="calculate_roi",
    description="根据预算/转化率/客单价/毛利率计算预期ROI、回本周期和建议折扣区间",
    input_schema={
        "type": "object",
        "properties": {
            "budget": {"type": "number", "description": "活动预算（元）"},
            "expected_conversion": {"type": "number", "description": "预期活动转化率（%，如3.5）"},
            "expected_aov": {"type": "number", "description": "预期客单价（元）"},
            "gross_margin": {"type": "number", "description": "毛利率（%，如40）"},
        },
        "required": ["budget", "expected_conversion", "expected_aov", "gross_margin"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def calculate_roi(budget: float, expected_conversion: float, expected_aov: float, gross_margin: float) -> str:
    # Scenario analysis: pessimistic / base / optimistic
    scenarios = {
        "悲观": (0.7, 0.7),
        "基准": (1.0, 1.0),
        "乐观": (1.3, 1.3),
    }

    result = f"## ROI 测算\n预算: ¥{budget:,.0f} | 预期转化率: {expected_conversion}% | 客单价: ¥{expected_aov} | 毛利率: {gross_margin}%\n\n"
    result += "| 场景 | 预计UV | 订单量 | GMV | 毛利 | ROI | 回本周期 |\n"
    result += "|------|-------|--------|-----|------|-----|--------|\n"

    best_roi = 0
    for name, (uv_mult, cvr_mult) in scenarios.items():
        uv = budget / (expected_aov * 0.1)  # Assume CPA ~10% of AOV
        uv_adj = uv * uv_mult
        orders = uv_adj * (expected_conversion / 100) * cvr_mult
        gmv = orders * expected_aov
        profit = gmv * (gross_margin / 100)
        roi = profit / max(budget, 1)
        payback_days = budget / max(gmv, 1) * 30

        if roi > best_roi:
            best_roi = roi

        result += f"| {name} | {uv_adj:,.0f} | {orders:,.0f} | ¥{gmv:,.0f} | ¥{profit:,.0f} | {roi:.1f} | {payback_days:.0f}天 |\n"

    # Discount recommendation
    result += f"\n## 折扣建议\n"
    result += f"基于毛利率 {gross_margin}%，建议折扣空间:\n"
    result += f"  - 安全线: {gross_margin * 0.3:.0f}% off（毛利仍为正）\n"
    result += f"  - 激进线: {gross_margin * 0.5:.0f}% off（需走量回本）\n"
    result += f"  - 红线: {gross_margin * 0.7:.0f}% off（亏损获客）\n"

    result += f"\n推荐预算: ¥{budget:,.0f}，预期ROI {best_roi:.1f}，推荐使用安全线折扣"
    return result
