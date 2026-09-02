# -*- coding: utf-8 -*-
"""
猎聘(liepin)岗位解析器
将 Edge 扩展导出的 liepin_raw（猎聘搜索API原始响应）解析为标准岗位格式。

猎聘特点：
- 搜索API: https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job
- 岗位列表在 data.data.data.jobCardList
- 每个卡片有 comp(公司) / job(岗位) / recruiter(HR)
- 列表API不返回完整JD，只有基本信息（标题/薪资/标签/公司/地区）
- 岗位详情页: https://www.liepin.com/lptjob/{jobId}

用法：
    from parse_liepin_api import parse_liepin, dedupe_liepin
    jobs = parse_liepin(raw['liepin_raw'])   # 从原始响应列表解析
    jobs = dedupe_liepin(jobs)
"""
import html
import re
from datetime import datetime


def clean_text(s):
    """清理HTML实体和多余空白。"""
    if not s:
        return ""
    s = html.unescape(str(s))
    s = s.replace("&nbsp;", " ").replace("\xa0", " ")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def extract_city(dq):
    """从'上海-杨浦区'提取城市名。"""
    if not dq:
        return ""
    if "-" in dq:
        return dq.split("-")[0].strip()
    return dq.strip()


def parse_refresh_time(t):
    """解析猎聘刷新时间 '20260826153345' → '2026-08-26 15:33:45'"""
    if not t or len(str(t)) < 14:
        return ""
    t = str(t)
    try:
        return f"{t[0:4]}-{t[4:6]}-{t[6:8]} {t[8:10]}:{t[10:12]}:{t[12:14]}"
    except Exception:
        return ""



def split_liepin_jd(description):
    """
    从猎聘schema.org description中拆分职责和要求。
    猎聘JD常见格式：
      工作内容：
      1、xxx
      2、xxx
      任职要求：
      1、xxx
    """
    if not description:
        return "", "", description
    desc = clean_text(description)

    # 常见分隔符
    duty_keywords = ["工作内容", "岗位职责", "职责描述", "岗位描述", "职位描述", "工作职责", "工作职能"]
    req_keywords = ["任职要求", "岗位要求", "职位要求", "任职资格", "岗位资格", "资格要求", "应聘要求", "能力要求"]

    responsibilities = ""
    requirements = ""

    # 找职责部分
    duty_start = -1
    duty_kw = ""
    for kw in duty_keywords:
        idx = desc.find(kw)
        if idx != -1 and (duty_start == -1 or idx < duty_start):
            duty_start = idx
            duty_kw = kw

    # 找要求部分
    req_start = -1
    req_kw = ""
    for kw in req_keywords:
        idx = desc.find(kw)
        if idx != -1 and (req_start == -1 or idx < req_start):
            req_start = idx
            req_kw = kw

    if duty_start != -1 and req_start != -1:
        # 职责和要求都有
        if duty_start < req_start:
            responsibilities = desc[duty_start + len(duty_kw):req_start].strip()
            requirements = desc[req_start + len(req_kw):].strip()
        else:
            requirements = desc[req_start + len(req_kw):duty_start].strip()
            responsibilities = desc[duty_start + len(duty_kw):].strip()
    elif duty_start != -1:
        # 只有职责
        responsibilities = desc[duty_start + len(duty_kw):].strip()
    elif req_start != -1:
        # 只有要求
        requirements = desc[req_start + len(req_kw):].strip()
    else:
        # 没有明确分隔符，全部作为职责
        responsibilities = desc

    # 清理开头的冒号和换行
    responsibilities = responsibilities.lstrip("：:").strip()
    requirements = requirements.lstrip("：:").strip()

    return responsibilities, requirements, desc

def parse_one(card):
    """
    解析单个猎聘岗位卡片为标准岗位格式。
    card 结构: {comp: {...}, job: {...}, recruiter: {...}, dataParams: '...'}
    """
    if not isinstance(card, dict):
        return None

    comp = card.get("comp", {}) or {}
    job = card.get("job", {}) or {}
    recruiter = card.get("recruiter", {}) or {}

    # 基本信息
    job_id = str(job.get("jobId") or "")
    title = clean_text(job.get("title") or "")
    salary = clean_text(job.get("salary") or "")
    dq = clean_text(job.get("dq") or "")
    city = extract_city(dq)
    link = job.get("link") or ""
    if link and not link.startswith("http"):
        link = f"https://www.liepin.com{link}"

    # 标签
    labels = job.get("labels") or []
    if isinstance(labels, list):
        labels = [clean_text(l) for l in labels if clean_text(l)]
    else:
        labels = [clean_text(str(labels))] if labels else []

    # 校园招聘类型（应届/实习生等）
    campus_kind = clean_text(job.get("campusJobKind") or "")
    if campus_kind and campus_kind not in labels:
        labels.append(campus_kind)

    # 公司信息
    company = clean_text(comp.get("compName") or "")
    company_size = clean_text(comp.get("compScale") or "")
    company_industry = clean_text(comp.get("compIndustry") or "")
    company_link = comp.get("link") or ""
    if company_link and not company_link.startswith("http"):
        company_link = f"https://www.liepin.com{company_link}"

    # HR信息
    hr_name = clean_text(recruiter.get("recruiterName") or "")
    hr_title = clean_text(recruiter.get("recruiterTitle") or "")
    hr_online = clean_text(recruiter.get("imShowText") or "")

    # 刷新时间
    publish_date = parse_refresh_time(job.get("refreshTime") or "")

    # JD处理：优先使用补全的__detail，否则用简要描述
    responsibilities = ""
    requirements = ""
    has_detail = False
    detail_text = ""

    # 检查是否有补全的JD（来自扩展的fillLiepinDetails）
    detail_obj = card.get("__detail") or {}
    if isinstance(detail_obj, dict) and detail_obj.get("description"):
        responsibilities, requirements, detail_text = split_liepin_jd(detail_obj["description"])
        has_detail = True
    elif isinstance(card.get("__detail"), str) and card["__detail"]:
        responsibilities, requirements, detail_text = split_liepin_jd(card["__detail"])
        has_detail = True

    if not has_detail:
        # 猎聘列表无完整JD，用标题+标签+公司行业构造简要描述
        detail_parts = []
        if title:
            detail_parts.append(f"岗位名称：{title}")
        if labels:
            detail_parts.append(f"岗位标签：{'、'.join(labels)}")
        if company_industry:
            detail_parts.append(f"公司行业：{company_industry}")
        detail_text = "\n".join(detail_parts)

    # 技能标签：从labels中提取技术相关
    skill_keywords = ["测绘", "测量", "GIS", "ArcGIS", "CAD", "CASS", "ENVI", "遥感",
                      "地籍", "地形", "国土", "规划", "数据", "制图", "GPS", "RTK",
                      "全站仪", "水准仪", "Python", "SQL", "数据库", "矢量化", "空间分析",
                      "硕士", "本科", "大专", "应届", "实习生"]
    skills = [l for l in labels if any(kw.lower() in l.lower() for kw in skill_keywords)]

    if not title or not company:
        return None

    return {
        # 基本信息
        "company": company,
        "position": title,
        "city": city,
        "work_location": dq,
        "salary": salary,
        "salary_min": None,
        "salary_max": None,
        "education": "",
        "experience": "",
        # 标签
        "skills": skills,
        "job_labels": labels,
        "benefits": [],
        # 公司信息
        "company_size": company_size,
        "company_industry": company_industry,
        "company_type": "",
        "company_intro": "",
        # JD（优先使用补全的__detail）
        "responsibilities": responsibilities,
        "requirements": requirements,
        "detail_text": detail_text,
        "has_detail": has_detail,
        # 链接
        "company_link": company_link,
        "source": "猎聘",
        "job_url": link,
        "encrypt_job_id": job_id,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # 猎聘扩展字段
        "hr_name": hr_name,
        "hr_title": hr_title,
        "hr_online": hr_online,
        "publish_date": publish_date,
        "job_kind": str(job.get("jobKind") or ""),
    }


def parse_liepin(liepin_raw):
    """
    从猎聘原始响应列表（liepin_raw）中解析岗位。
    自动定位 pc-search-job API 响应，提取 jobCardList。

    Args:
        liepin_raw: 扩展导出的 liepin_raw 列表，每个元素 {url, data, time}

    Returns:
        标准岗位列表
    """
    if not liepin_raw:
        return []

    all_jobs = []
    for item in liepin_raw:
        if not isinstance(item, dict):
            continue
        url = item.get("url", "")
        # 只处理岗位搜索API
        if "pc-search-job" not in url or "cond-init" in url:
            continue
        data = item.get("data", {})
        if not isinstance(data, dict):
            continue
        # 定位 jobCardList: data.data.data.jobCardList
        inner = data.get("data", {})
        if not isinstance(inner, dict):
            continue
        inner_data = inner.get("data", {})
        if not isinstance(inner_data, dict):
            continue
        job_list = inner_data.get("jobCardList", [])
        if not isinstance(job_list, list):
            continue
        for card in job_list:
            try:
                job = parse_one(card)
                if job:
                    all_jobs.append(job)
            except Exception as e:
                print(f"  [警告] 解析猎聘岗位失败: {e}")
                continue

    return all_jobs




def parse_liepin_jobs(liepin_jobs):
    """
    从扩展导出的 liepin_jobs（已补全JD的岗位列表）解析标准岗位。
    与 parse_liepin（从raw解析）互补：liepin_jobs包含补全的JD。

    Args:
        liepin_jobs: 扩展导出的 liepin_jobs 列表

    Returns:
        标准岗位列表
    """
    if not liepin_jobs:
        return []
    result = []
    for card in liepin_jobs:
        try:
            job = parse_one(card)
            if job:
                result.append(job)
        except Exception as e:
            print(f"  [警告] 解析猎聘岗位失败: {e}")
            continue
    return result

def dedupe_liepin(jobs):
    """猎聘岗位去重。按 (公司名, 岗位名) 去重，保留第一个。"""
    if not jobs:
        return []
    seen = set()
    result = []
    for j in jobs:
        key = (j.get("company", "").strip(), j.get("position", "").strip())
        if key in seen:
            continue
        seen.add(key)
        result.append(j)
    return result


# ============================================================================
# 命令行测试
# ============================================================================

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("用法: python parse_liepin_api.py <导出JSON文件>")
        sys.exit(1)

    path = sys.argv[1]
    raw = json.load(open(path, encoding="utf-8"))
    liepin_raw = raw.get("liepin_raw", [])
    print(f"原始liepin_raw数: {len(liepin_raw)}")

    # 统计有多少条是岗位搜索API
    search_apis = [r for r in liepin_raw if "pc-search-job" in r.get("url", "") and "cond-init" not in r.get("url", "")]
    print(f"岗位搜索API响应数: {len(search_apis)}")

    jobs = parse_liepin(liepin_raw)
    print(f"解析成功: {len(jobs)}")

    jobs = dedupe_liepin(jobs)
    print(f"去重后: {len(jobs)}")

    # 统计
    cities = {}
    for j in jobs:
        c = j["city"]
        cities[c] = cities.get(c, 0) + 1
    print(f"\n城市分布: {dict(sorted(cities.items(), key=lambda x: -x[1])[:5])}")
    print(f"有完整JD: {sum(1 for j in jobs if j['has_detail'])}/{len(jobs)}（猎聘列表无JD，需详情页补全）")

    # 显示前5条
    print("\n=== 前5条解析结果 ===")
    for i, j in enumerate(jobs[:5]):
        print(f"\n[{i+1}] {j['position']} @ {j['company']}")
        print(f"    薪资: {j['salary']} | 地点: {j['work_location']} | 标签: {j['job_labels'][:5]}")
        print(f"    公司: {j['company_industry']} | {j['company_size']}")
        print(f"    HR: {j['hr_name']}({j['hr_title']}) {j['hr_online']}")
        print(f"    链接: {j['job_url'][:80]}")
