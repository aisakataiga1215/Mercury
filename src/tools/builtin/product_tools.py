import csv, os
from collections import Counter
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
    name="get_product_detail",
    description="获取指定SKU的完整商品信息：标题/类目/价格/成本/库存/评分/转化率/30天GMV",
    input_schema={
        "type": "object",
        "properties": {
            "sku": {"type": "string", "description": "商品SKU编码，如 SKU-PH-0001"},
        },
        "required": ["sku"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def get_product_detail(sku: str) -> str:
    products = _load_csv("products.csv")
    for p in products:
        if p["sku"] == sku:
            return (
                f"SKU: {p['sku']}\n"
                f"标题: {p['title']}\n"
                f"类目: {p['category']} / {p['sub_category']}\n"
                f"成本: ¥{p['cost']} | 售价: ¥{p['price']} | 毛利率: {((float(p['price'])-float(p['cost']))/float(p['price'])*100):.1f}%\n"
                f"库存: {p['stock']} | 上架日期: {p['listing_date']}\n"
                f"评分: {p['rating']} | 评价数: {p['review_count']}\n"
                f"30天GMV: ¥{p['gmv_30d']} | 转化率: {p['conversion_rate']}"
            )
    return f"未找到SKU {sku}"


@register_tool(
    name="get_product_reviews",
    description="获取指定SKU的评价列表，可按情感筛选(positive/neutral/negative)，返回评价内容+日期+评分+情感",
    input_schema={
        "type": "object",
        "properties": {
            "sku": {"type": "string", "description": "商品SKU编码"},
            "sentiment": {"type": "string", "description": "情感筛选: positive/neutral/negative/all"},
            "limit": {"type": "integer", "description": "返回数量上限，默认20"},
        },
        "required": ["sku"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def get_product_reviews(sku: str, sentiment: str = "all", limit: int = 20) -> str:
    all_reviews = _load_csv("reviews.csv")
    matched = [r for r in all_reviews if r["sku"] == sku]
    if sentiment != "all":
        matched = [r for r in matched if r["sentiment"] == sentiment]

    if not matched:
        return f"SKU {sku} 无{sentiment}评价记录"

    total = len(matched)
    sentiment_counts = Counter(r["sentiment"] for r in matched)
    avg_rating = sum(int(r["rating"]) for r in matched) / max(len(matched), 1)

    result = f"SKU {sku} 评价概览:\n"
    result += f"总评价数: {total} | 均分: {avg_rating:.1f}\n"
    result += f"好评: {sentiment_counts.get('positive', 0)} | 中评: {sentiment_counts.get('neutral', 0)} | 差评: {sentiment_counts.get('negative', 0)}\n"

    if sentiment == "negative":
        result += f"\n差评率: {total / max(len([r for r in all_reviews if r['sku'] == sku]), 1) * 100:.1f}%\n"

    result += f"\n--- 评价详情 (前{min(len(matched), limit)}条) ---\n"
    for r in matched[:limit]:
        result += f"[{r['sentiment']}] {r['date']} | 评分{r['rating']} | {r['content'][:120]}\n"

    return result


@register_tool(
    name="get_competitor_data",
    description="获取指定品类的竞品数据：竞品名称/价格/月销量/评分/核心卖点，用于对标分析",
    input_schema={
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "品类名称，如 手机壳/充电器/蓝牙耳机"},
            "top_n": {"type": "integer", "description": "返回Top N竞品，默认5"},
        },
        "required": ["category"],
    },
    output_type="structured",
    category=ToolCategory.EXTERNAL_DATA,
)
def get_competitor_data(category: str, top_n: int = 5) -> str:
    all_competitors = _load_csv("competitors.csv")
    matched = [c for c in all_competitors if c["category"] == category]

    if not matched:
        return f"品类 {category} 无竞品数据"

    # Sort by monthly sales desc
    matched.sort(key=lambda x: int(x["monthly_sales"]), reverse=True)
    top = matched[:top_n]

    avg_price = sum(float(c["price"]) for c in top) / len(top)
    avg_rating = sum(float(c["rating"]) for c in top) / len(top)

    result = f"品类 {category} 竞品分析 (Top {len(top)}):\n"
    result += f"竞品均价: ¥{avg_price:.2f} | 均分: {avg_rating:.1f}\n\n"
    for c in top:
        result += (
            f"  {c['competitor_name']} | {c['product_title']}\n"
            f"    价格: ¥{c['price']} | 月销: {c['monthly_sales']} | "
            f"评分: {c['rating']} | 卖点: {c['key_selling_point']}\n"
        )
    return result
