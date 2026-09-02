# -*- coding: utf-8 -*-
"""
阶段2-网申雷达：国聘网岗位采集器
国聘网（iguopin.com）是国企招聘聚合平台，有公开JSON接口。
用法：
  python radar_guopin.py --keyword 测绘 --pages 3 --campus_only --soe_only
  python radar_guopin.py --keyword 测绘,GIS,测量 --pages 2
输出：radar/guopin_关键词_时间.json
"""
import urllib.request, json, io, os, sys, time, argparse, re
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
RADAR_DIR = os.path.join(WS, "radar")
os.makedirs(RADAR_DIR, exist_ok=True)

API_URL = "https://gp-api.iguopin.com/api/jobs/v1/list"
HEADERS = {
    "Content-Type": "application/json",
    "Device": "pc",
    "Subsite": "cujiuye",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://iguopin.com/",
    "Origin": "https://iguopin.com",
    "Accept": "application/json, text/plain, */*",
}

def fetch_page(keyword, page, page_size=20, retries=3):
    """抓取一页，返回岗位列表"""
    payload = {"page": page, "page_size": page_size, "keyword": keyword}
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API_URL, data=data, method="POST")
            for k, v in HEADERS.items():
                req.add_header(k, v)
            resp = urllib.request.urlopen(req, timeout=20)
            result = json.loads(resp.read().decode("utf-8"))
            code = result.get("code")
            if code in (200, 0, "200", "0"):
                d = result.get("data", {})
                return d.get("list", []), d.get("total", 0)
            else:
                msg = result.get("msg", "")
                if "访问人数过多" in msg:
                    wait = 3 * (attempt + 1)
                    print(f"  接口限流，等待{wait}秒后重试 ({attempt+1}/{retries})")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  接口错误 code={code} msg={msg}")
                    return [], 0
        except Exception as e:
            print(f"  请求异常: {type(e).__name__} {str(e)[:80]}")
            time.sleep(2)
    return [], 0

def normalize_job(item):
    """标准化岗位字段，和现有岗位库兼容"""
    job_id = str(item.get("job_id", ""))
    company_info = item.get("company_info", {}) or {}
    district_list = item.get("district_list", []) or []
    location = district_list[0].get("area_cn", "") if district_list else ""

    min_wage = item.get("min_wage", 0) or 0
    max_wage = item.get("max_wage", 0) or 0
    wage_unit = item.get("wage_unit_cn", "元/月")
    months = item.get("months", 12) or 12

    if min_wage and max_wage:
        salary = f"{min_wage}-{max_wage}{wage_unit}"
    elif min_wage:
        salary = f"{min_wage}{wage_unit}起"
    else:
        salary = "面议"

    contents = item.get("contents", "") or ""
    # 分离岗位职责和任职要求
    jd_duty = ""
    jd_req = ""
    if "任职要求" in contents:
        parts = contents.split("任职要求", 1)
        jd_duty = parts[0].strip()
        jd_req = "任职要求" + parts[1].strip()
    elif "岗位要求" in contents:
        parts = contents.split("岗位要求", 1)
        jd_duty = parts[0].strip()
        jd_req = "岗位要求" + parts[1].strip()
    else:
        jd_duty = contents.strip()

    return {
        "id": job_id,
        "title": item.get("job_name", ""),
        "company": item.get("company_name", ""),
        "company_type": company_info.get("nature_cn", ""),
        "company_industry": company_info.get("industry_cn", ""),
        "company_scale": company_info.get("scale_cn", ""),
        "salary": salary,
        "salary_min": min_wage,
        "salary_max": max_wage,
        "salary_months": months,
        "education": item.get("education_cn", ""),
        "experience": item.get("experience_cn", ""),
        "location": location,
        "job_type": item.get("recruitment_type_cn", ""),
        "category": item.get("category_cn", ""),
        "headcount": item.get("amount", 0),
        "publish_time": item.get("start_time", ""),
        "deadline": item.get("end_time", ""),
        "jd_duty": jd_duty,
        "jd_req": jd_req,
        "jd_full": contents,
        "detail_url": f"https://www.iguopin.com/job/detail?id={job_id}",
        "company_url": f"https://www.iguopin.com/company?id={item.get('company_id', '')}",
        "source": "国聘网",
        "is_campus": "校园" in item.get("recruitment_type_cn", ""),
        "is_soe": "国企" in company_info.get("nature_cn", ""),
        "is_apply": item.get("is_apply", False),
    }

def collect(keywords, pages=3, page_size=20, campus_only=False, soe_only=False, delay=1.5):
    """采集多个关键词的岗位"""
    all_jobs = {}
    for kw in keywords:
        print(f"\n=== 搜索关键词: {kw} ===")
        for page in range(1, pages + 1):
            print(f"  第{page}页...", end=" ", flush=True)
            items, total = fetch_page(kw, page, page_size)
            if not items:
                print("无数据")
                break
            print(f"获取{len(items)}条 (总计{total})")
            for item in items:
                job = normalize_job(item)
                if campus_only and not job["is_campus"]:
                    continue
                if soe_only and not job["is_soe"]:
                    continue
                if job["id"] not in all_jobs:
                    all_jobs[job["id"]] = job
            time.sleep(delay)
            if len(items) < page_size:
                print("  已到最后一页")
                break
    return list(all_jobs.values())

def save_jobs(jobs, keywords, prefix="guopin"):
    """保存到JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    kw_str = "_".join(keywords)[:30]
    filename = f"{prefix}_{kw_str}_{len(jobs)}条_{timestamp}.json"
    filepath = os.path.join(RADAR_DIR, filename)
    output = {
        "source": "国聘网",
        "collect_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "keywords": keywords,
        "total": len(jobs),
        "jobs": jobs,
    }
    with io.open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n已保存 {len(jobs)} 条岗位到: {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="国聘网岗位采集器")
    parser.add_argument("--keyword", required=True, help="关键词，多个用逗号分隔（如 测绘,GIS,测量）")
    parser.add_argument("--pages", type=int, default=3, help="每个关键词抓几页（默认3）")
    parser.add_argument("--page_size", type=int, default=20, help="每页条数（默认20）")
    parser.add_argument("--campus_only", action="store_true", help="只保留校园招聘")
    parser.add_argument("--soe_only", action="store_true", help="只保留国企")
    parser.add_argument("--delay", type=float, default=1.5, help="请求间隔秒数（默认1.5）")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keyword.split(",") if k.strip()]
    print(f"关键词: {keywords}")
    print(f"页数: {args.pages}, 每页: {args.page_size}")
    print(f"仅校招: {args.campus_only}, 仅国企: {args.soe_only}")

    jobs = collect(
        keywords,
        pages=args.pages,
        page_size=args.page_size,
        campus_only=args.campus_only,
        soe_only=args.soe_only,
        delay=args.delay,
    )

    # 统计
    soe_count = sum(1 for j in jobs if j["is_soe"])
    campus_count = sum(1 for j in jobs if j["is_campus"])
    print(f"\n=== 采集完成 ===")
    print(f"总计: {len(jobs)} 条")
    print(f"国企: {soe_count} 条 ({soe_count/len(jobs)*100:.0f}%)" if jobs else "国企: 0")
    print(f"校招: {campus_count} 条")

    if jobs:
        save_jobs(jobs, keywords)

if __name__ == "__main__":
    main()
