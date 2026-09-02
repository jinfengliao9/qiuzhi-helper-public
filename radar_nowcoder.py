# -*- coding: utf-8 -*-
"""
阶段2-网申雷达：牛客校招日程采集器
牛客（nowcoder.com）校招日程API，返回公司级校招信息（网申起止时间、城市、岗位类别、官方链接）。
用法：
  python radar_nowcoder.py --pages 3 --keyword 测绘
  python radar_nowcoder.py --pages 5 --soe_only
输出：radar/nowcoder_数量条_时间.json
"""
import urllib.request, json, io, os, sys, time, argparse, re
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
RADAR_DIR = os.path.join(WS, "radar")
os.makedirs(RADAR_DIR, exist_ok=True)

API_URL = "https://www.nowcoder.com/school/schedule/data"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.nowcoder.com/school/schedule",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

SOE_KEYWORDS = ["国企", "央企", "国有", "中国", "中建", "中铁", "中交", "中能建", "中电建", "中石油", "中石化", "国家电网", "南方电网", "中国移动", "中国联通", "中国电信", "中国邮政", "中国烟草", "中国建筑", "中国铁建", "中国交建", "中国能建", "中国电建", "中国五矿", "中国中冶", "中国化学", "中国有色", "中国黄金", "中国广核", "中国核工业", "中国航天", "中国航空", "中国船舶", "中国兵器", "中国电子", "中国一汽", "中国东风", "中国重汽", "中国中车", "中国通号", "中国中铁", "中国铁建"]

def fetch_page(page=1, retries=3):
    """抓取一页公司列表"""
    url = f"{API_URL}?page={page}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            resp = urllib.request.urlopen(req, timeout=20)
            result = json.loads(resp.read().decode("utf-8"))
            code = result.get("code")
            if code == 0:
                d = result.get("data", {})
                return d.get("companyList", []), d.get("pageInfo", {})
            else:
                print(f"  接口错误 code={code} msg={result.get('msg','')}")
                return [], {}
        except Exception as e:
            print(f"  请求异常: {type(e).__name__} {str(e)[:80]}")
            time.sleep(2)
    return [], {}

def timestamp_to_date(ts):
    """时间戳转日期字符串"""
    if not ts or ts == 0:
        return ""
    try:
        return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
    except:
        return ""

def is_soe_company(name, tags):
    """判断是否国企"""
    text = name + " " + " ".join(tags) if tags else name
    for kw in SOE_KEYWORDS:
        if kw in text:
            return True
    return False

def is_wangshen_active(wangshen_date):
    """判断网申是否在进行中"""
    if not wangshen_date or len(wangshen_date) < 2:
        return False
    now = time.time() * 1000
    start = wangshen_date[0]
    end = wangshen_date[1]
    return start <= now <= end

def _normalize_tags(raw):
    """牛客 tags 可能是列表、字符串、或'["通信电子"]'这种JSON数组字符串，统一为字符串列表。"""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(t).strip().strip('"\'') for t in raw if str(t).strip().strip('"\'')]
    if isinstance(raw, str):
        s = raw.strip()
        # 先尝试按 JSON 数组解析
        if s.startswith('['):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(t).strip().strip('"\'') for t in parsed if str(t).strip().strip('"\'')]
            except Exception:
                pass
        s = s.strip('"\'')
        parts = re.split(r'[,，、|/\s]+', s)
        return [p.strip().strip('"\'') for p in parts if p.strip().strip('"\'')]
    return [str(raw)]


def normalize_company(item):
    """标准化公司信息"""
    name = item.get("name", "")
    tags = _normalize_tags(item.get("tags"))
    wangshen_date = item.get("wangshenDate", []) or []
    cities = item.get("cities", []) or []
    careers = item.get("companyCareersStr", []) or []

    return {
        "id": str(item.get("companyId", item.get("id", ""))),
        "company": name,
        "company_type": "国企" if is_soe_company(name, tags) else (tags[0] if tags else ""),
        "cities": cities if isinstance(cities, list) else [str(cities)],
        "job_categories": careers if isinstance(careers, list) else [str(careers)],
        "wangshen_start": timestamp_to_date(wangshen_date[0]) if len(wangshen_date) > 0 else "",
        "wangshen_end": timestamp_to_date(wangshen_date[1]) if len(wangshen_date) > 1 else "",
        "wangshen_active": is_wangshen_active(wangshen_date),
        "hire_state": item.get("hireState", ""),
        "status": item.get("status", ""),
        "tags": tags,
        "interview_time": item.get("interviewTime", ""),
        "test_time": item.get("testTime", ""),
        "offer_time": item.get("offerTime", ""),
        "official_url": item.get("officalUrl", "") or item.get("officalEncodeUrl", ""),
        "logo": item.get("logo", ""),
        "important": item.get("importantCompany", False),
        "hot": item.get("hotSearchTop", False),
        "source": "牛客校招日程",
        "is_soe": is_soe_company(name, tags),
    }

def collect(pages=3, keyword="", soe_only=False, active_only=False, delay=1.0):
    """采集多页公司列表"""
    all_companies = {}
    for page in range(1, pages + 1):
        print(f"第{page}页...", end=" ", flush=True)
        items, page_info = fetch_page(page)
        if not items:
            print("无数据")
            break
        print(f"获取{len(items)}家公司")

        for item in items:
            comp = normalize_company(item)

            # 关键词筛选（公司名、城市、岗位类别）
            if keyword:
                text = comp["company"] + " " + " ".join(comp["cities"]) + " " + " ".join(comp["job_categories"])
                if keyword.lower() not in text.lower():
                    continue

            # 国企筛选
            if soe_only and not comp["is_soe"]:
                continue

            # 网申进行中筛选
            if active_only and not comp["wangshen_active"]:
                continue

            if comp["id"] not in all_companies:
                all_companies[comp["id"]] = comp

        time.sleep(delay)

        # 判断是否到最后一页
        if page_info:
            total_pages = page_info.get("pageCount", 1)
            if page >= total_pages:
                print("已到最后一页")
                break

    return list(all_companies.values())

def save_companies(companies, prefix="nowcoder"):
    """保存到JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{len(companies)}家_{timestamp}.json"
    filepath = os.path.join(RADAR_DIR, filename)
    output = {
        "source": "牛客校招日程",
        "collect_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(companies),
        "companies": companies,
    }
    with io.open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n已保存 {len(companies)} 家公司到: {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="牛客校招日程采集器")
    parser.add_argument("--pages", type=int, default=3, help="采集页数（默认3，每页50家）")
    parser.add_argument("--keyword", default="", help="关键词筛选（公司名/城市/岗位类别）")
    parser.add_argument("--soe_only", action="store_true", help="只保留国企")
    parser.add_argument("--active_only", action="store_true", help="只保留网申进行中")
    parser.add_argument("--delay", type=float, default=1.0, help="请求间隔秒数")
    args = parser.parse_args()

    print(f"牛客校招日程采集器")
    print(f"页数: {args.pages}, 关键词: {args.keyword or '无'}")
    print(f"仅国企: {args.soe_only}, 仅进行中: {args.active_only}")

    companies = collect(
        pages=args.pages,
        keyword=args.keyword,
        soe_only=args.soe_only,
        active_only=args.active_only,
        delay=args.delay,
    )

    # 统计
    soe_count = sum(1 for c in companies if c["is_soe"])
    active_count = sum(1 for c in companies if c["wangshen_active"])
    print(f"\n=== 采集完成 ===")
    print(f"总计: {len(companies)} 家公司")
    print(f"国企: {soe_count} 家 ({soe_count/len(companies)*100:.0f}%)" if companies else "国企: 0")
    print(f"网申进行中: {active_count} 家")

    if companies:
        save_companies(companies)

if __name__ == "__main__":
    main()
