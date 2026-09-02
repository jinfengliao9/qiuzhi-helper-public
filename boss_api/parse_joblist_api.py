# -*- coding: utf-8 -*-
"""
BOSS直聘 joblist.json API 响应解析器（方案A：被动捕获，零注入请求）

输入：被动捕获到的 /wapi/zpgeek/search/joblist.json 原始响应（JSON）
输出：与岗位库 jobs.json 对齐的标准化岗位列表（可直接喂给 job_pipeline import）

关键说明：
- 列表接口直接返回明文薪资 salaryDesc，绕过搜索结果页的自定义字体反爬。
- 本脚本只做"数据映射"，不发起任何网络请求、不操作浏览器。
- 列表阶段 responsibilities/requirements 为空，完整 JD 由后续详情接口/详情页补充。

用法：
  python parse_joblist_api.py raw_joblist_page1.json
  python parse_joblist_api.py raw1.json raw2.json -o scraped_boss_api.json
"""
import argparse
import html as html_lib
import json
import os
import re
import sys
from datetime import datetime


def html_to_text(s):
    """把 postDescription 的 HTML/富文本清洗为纯文本。"""
    if not s:
        return ""
    s = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div|li|ul|ol|h\d|section|tr)\s*>", "\n", s)
    s = re.sub(r"(?i)<li[^>]*>", "· ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_lib.unescape(s)
    lines = [re.sub(r"[ \t\u3000]+", " ", x).strip() for x in s.split("\n")]
    out = []
    for x in lines:
        if x and (not out or out[-1] != x):
            out.append(x)
    return "\n".join(out).strip()


def split_jd(text):
    """把整段JD按"任职要求/岗位要求/职位要求/我们希望"等切分为职责与要求。"""
    if not text:
        return "", ""
    m = re.search(r"(?:任职|岗位|职位)?(?:要求|资格|条件|我们希望|你需要|任职资格)", text)
    if m and m.start() > 0:
        resp = text[:m.start()].strip(" ：:\n")
        req = text[m.start():].strip()
        return resp, req
    return text, ""


def extract_detail(raw):
    """从扩展补全的 __detail（=detail.json 的 zpData）提取JD文本与补充信息。"""
    info = {}
    if not isinstance(raw, dict):
        return info
    detail = raw.get("__detail")
    if not isinstance(detail, dict):
        return info
    job_info = detail.get("jobInfo") or {}
    post = html_to_text(job_info.get("postDescription") or "")
    resp, req = split_jd(post)
    if resp:
        info["responsibilities"] = resp
    if req:
        info["requirements"] = req
    info["detail_text"] = post
    # showSkills 可能比列表 skills 更全
    show_skills = job_info.get("showSkills")
    if isinstance(show_skills, list) and show_skills:
        info["detail_skills"] = [str(x).strip() for x in show_skills if str(x).strip()]
    # 公司补充信息
    brand = detail.get("brandComInfo") or {}
    if isinstance(brand, dict):
        parts = [brand.get("industryName"), brand.get("stageName"), brand.get("scaleName")]
        info["detail_company"] = " / ".join([str(x) for x in parts if x])
        if brand.get("introduce"):
            info["company_intro"] = html_to_text(str(brand.get("introduce")))[:400]
    return info


def map_one(raw):
    """把 joblist.json 的单条原始记录映射为标准岗位字典。"""
    if not isinstance(raw, dict):
        return None

    encrypt_job_id = str(raw.get("encryptJobId") or "").strip()
    encrypt_brand_id = str(raw.get("encryptBrandId") or "").strip()

    city_parts = [
        raw.get("cityName") or "",
        raw.get("areaDistrict") or "",
        raw.get("businessDistrict") or "",
    ]
    city = raw.get("cityName") or ""
    work_location = "·".join(p for p in city_parts if p)

    skills = [s for s in (raw.get("skills") or []) if s]
    job_labels = [s for s in (raw.get("jobLabels") or []) if s]
    welfare = [s for s in (raw.get("welfareList") or []) if s]

    # 公司规模/行业/融资阶段
    company_size = raw.get("brandScaleName") or ""
    company_industry = raw.get("brandStageName") or ""
    brand_industry = raw.get("brandIndustry") or ""
    company_info = " / ".join(
        x for x in [brand_industry, raw.get("brandStageName") or ""] if x
    )

    job_url = (
        f"https://www.zhipin.com/job_detail/{encrypt_job_id}.html"
        if encrypt_job_id else ""
    )
    company_link = (
        f"https://www.zhipin.com/gongsi/{encrypt_brand_id}.html"
        if encrypt_brand_id else ""
    )

    detail = extract_detail(raw)
    # 合并详情里更全的技能
    if detail.get("detail_skills"):
        merged_skills = list(dict.fromkeys(skills + detail["detail_skills"]))
    else:
        merged_skills = skills
    if detail.get("detail_company") and not company_info:
        company_info = detail["detail_company"]

    return {
        "company": raw.get("brandName") or "",
        "position": raw.get("jobName") or "",
        "city": city,
        "work_location": work_location,
        "salary": raw.get("salaryDesc") or "",
        "education": raw.get("jobDegree") or "",
        "experience": raw.get("jobExperience") or "",
        "skills": merged_skills,
        "job_labels": job_labels,
        "benefits": welfare,
        "company_size": company_size,
        "company_industry": company_info,
        "responsibilities": detail.get("responsibilities", ""),
        "requirements": detail.get("requirements", ""),
        "detail_text": detail.get("detail_text", ""),
        "company_intro": detail.get("company_intro", ""),
        "has_detail": 1 if detail.get("detail_text") else 0,
        "company_link": company_link,
        "source": "BOSS直聘",
        "job_url": job_url,
        # 详情接口需要的上下文参数，先保留
        "security_id": raw.get("securityId") or "",
        "lid": raw.get("lid") or "",
        "encrypt_job_id": encrypt_job_id,
        "encrypt_brand_id": encrypt_brand_id,
        "boss_name": raw.get("bossName") or "",
        "boss_title": raw.get("bossTitle") or "",
        "collected_at": datetime.now().isoformat(timespec="seconds"),
    }


def extract_jobs(raw_obj):
    """从一份原始响应里抽出岗位列表，兼容多种外层结构。"""
    if not isinstance(raw_obj, dict):
        return []
    zp_data = raw_obj.get("zpData")
    if isinstance(zp_data, dict):
        job_list = zp_data.get("jobList")
    else:
        job_list = None
    if not isinstance(job_list, list):
        # 容错：直接就是列表
        job_list = raw_obj.get("jobList") if isinstance(raw_obj.get("jobList"), list) else []
    out = []
    for item in job_list:
        mapped = map_one(item)
        if mapped and mapped["company"] and mapped["position"]:
            out.append(mapped)
    return out


def dedupe(jobs):
    """按 encrypt_job_id / 岗位链接 / 公司+岗位 去重，保留先出现的。"""
    seen = set()
    out = []
    for j in jobs:
        key = j.get("encrypt_job_id") or j.get("job_url") or f"{j['company']}|{j['position']}"
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def main():
    parser = argparse.ArgumentParser(description="解析BOSS joblist.json API响应")
    parser.add_argument("inputs", nargs="+", help="一个或多个原始响应JSON文件")
    parser.add_argument("-o", "--output", default="scraped_boss_api.json", help="输出文件")
    args = parser.parse_args()

    all_jobs = []
    for path in args.inputs:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        jobs = extract_jobs(raw)
        print(f"  {os.path.basename(path)}: 解析出 {len(jobs)} 条")
        all_jobs.extend(jobs)

    all_jobs = dedupe(all_jobs)

    # 薪资明文率统计
    salary_ok = sum(1 for j in all_jobs if j["salary"])
    skills_ok = sum(1 for j in all_jobs if j["skills"])
    url_ok = sum(1 for j in all_jobs if j["job_url"])

    payload = {
        "platform": "BOSS直聘",
        "capture_method": "passive_network",
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "total": len(all_jobs),
        "jobs": all_jobs,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n=== 解析完成（去重后 {len(all_jobs)} 条）===")
    if all_jobs:
        print(f"明文薪资率: {salary_ok}/{len(all_jobs)} = {salary_ok/len(all_jobs)*100:.0f}%")
        print(f"技能标签率: {skills_ok}/{len(all_jobs)} = {skills_ok/len(all_jobs)*100:.0f}%")
        print(f"岗位链接率: {url_ok}/{len(all_jobs)} = {url_ok/len(all_jobs)*100:.0f}%")
        print("\n前5条预览：")
        for j in all_jobs[:5]:
            print(f"  {j['position']} | {j['salary']} | {j['work_location']} | {j['company']}")
    print(f"\n已保存: {os.path.abspath(args.output)}")


if __name__ == "__main__":
    sys.exit(main())
