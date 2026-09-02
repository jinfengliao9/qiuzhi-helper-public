# -*- coding: utf-8 -*-
"""
前程无忧(51job)岗位解析器
将 Edge 扩展导出的 job51_jobs（51job搜索API原始岗位对象）解析为标准岗位格式。

51job特点：
- 列表API直接返回完整JD（jobDescribe字段，格式"工作职责:...任职资格:..."）
- 薪资同时有明文（provideSalaryString）和数值（jobSalaryMin/Max，月薪元）
- jobName可能带职位编号后缀（如"(J10008)"），需清理
- jobTags是字符串形式的列表，也有jobTagsList真正列表

用法：
    from parse_51job_api import parse_51job, dedupe_51job
    jobs = parse_51job(raw['job51_jobs'])
    jobs = dedupe_51job(jobs)
"""
import html
import re
from datetime import datetime


# ============================================================================
# 工具函数
# ============================================================================

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


def parse_job_tags(tags_str, tags_list=None):
    """解析岗位标签。tags_str可能是字符串或列表，tags_list是字典列表（含jobTagName）。"""
    # 优先处理 tags_list（字典列表，提取 jobTagName）
    if tags_list and isinstance(tags_list, list):
        result = []
        for t in tags_list:
            if isinstance(t, dict):
                name = t.get("jobTagName") or t.get("name") or t.get("label") or ""
                if name and str(name).strip():
                    result.append(str(name).strip())
            elif str(t).strip():
                result.append(str(t).strip())
        return result
    # tags_str 可能本身就是列表
    if isinstance(tags_str, list):
        return [str(t).strip() for t in tags_str if str(t).strip()]
    if not tags_str:
        return []
    # 尝试解析字符串形式的列表: "['a', 'b', 'c']"
    try:
        import ast
        parsed = ast.literal_eval(tags_str)
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if str(t).strip()]
    except Exception:
        pass
    #  fallback: 按逗号/顿号分割
    parts = re.split(r"[,，、]", str(tags_str).strip("[]'\" "))
    return [p.strip().strip("'\"") for p in parts if p.strip().strip("'\"")]


def extract_city(area_string):
    """从'广州·越秀区'提取城市名。"""
    if not area_string:
        return ""
    # 取第一个·之前的部分
    if "·" in area_string:
        return area_string.split("·")[0].strip()
    if "-" in area_string:
        return area_string.split("-")[0].strip()
    return area_string.strip()


def clean_job_name(name):
    """清理岗位名称中的职位编号后缀，如'实习生（测绘类）(J10008)' → '实习生（测绘类）'"""
    if not name:
        return ""
    # 移除 (J数字) 或 （J数字） 后缀
    name = re.sub(r"[（(]J\d+[）)]\s*$", "", name).strip()
    return name


def split_jd(describe):
    """
    拆分51job的jobDescribe为 responsibilities（工作职责）和 requirements（任职资格）。
    51job格式通常是：
        工作职责:
        1. ...
        2. ...
        任职资格:
        1. ...
        2. ...
    也可能用"岗位职责"、"岗位要求"等变体。
    """
    if not describe:
        return "", "", ""
    text = clean_text(describe)

    # 定义职责和要求的关键词模式
    resp_patterns = [
        r"工作职责[:：]?", r"岗位职责[:：]?", r"工作内容[:：]?",
        r"岗位描述[:：]?", r"职位描述[:：]?", r"职责描述[:：]?",
        r"你将做什么[:：]?", r"工作任务[:：]?",
    ]
    req_patterns = [
        r"任职资格[:：]?", r"任职要求[:：]?", r"岗位要求[:：]?",
        r"职位要求[:：]?", r"任职条件[:：]?", r"招聘要求[:：]?",
        r"资格要求[:：]?", r"你需要具备[:：]?", r"要求[:：]?",
    ]

    # 找所有匹配位置
    splits = []
    for pat in resp_patterns:
        for m in re.finditer(pat, text):
            splits.append((m.start(), "resp", m.group()))
    for pat in req_patterns:
        for m in re.finditer(pat, text):
            splits.append((m.start(), "req", m.group()))

    if not splits:
        # 没有明确分隔，全部作为detail_text
        return "", text, text

    splits.sort(key=lambda x: x[0])

    responsibilities = ""
    requirements = ""

    for i, (pos, kind, label) in enumerate(splits):
        end = splits[i + 1][0] if i + 1 < len(splits) else len(text)
        segment = text[pos + len(label):end].strip()
        # 清理开头的换行、序号和闭合括号（如 】 】 ）——51job用【工作内容】格式
        segment = re.sub(r"^[\n\r\s]+", "", segment)
        segment = re.sub(r"^[】\]\)）\s]+", "", segment)
        if kind == "resp" and not responsibilities:
            responsibilities = segment
        elif kind == "req" and not requirements:
            requirements = segment

    detail_text = text
    return responsibilities, requirements, detail_text


def parse_welfare(welfare_list):
    """解析福利标签列表。"""
    if not welfare_list or not isinstance(welfare_list, list):
        return []
    result = []
    for item in welfare_list:
        if isinstance(item, dict):
            name = (item.get("chineseTitle") or item.get("typeTitle") or
                    item.get("name") or item.get("label") or item.get("title") or "")
            if name:
                result.append(str(name).strip())
        elif isinstance(item, str):
            if item.strip():
                result.append(item.strip())
    return result


# ============================================================================
# 核心解析
# ============================================================================

def parse_one(j):
    """
    解析单个51job岗位对象为标准岗位格式。
    """
    job_id = str(j.get("jobId") or j.get("encCoId") or "")
    raw_name = j.get("jobName") or ""
    position = clean_job_name(raw_name)
    salary = j.get("provideSalaryString") or ""
    salary_min = j.get("jobSalaryMin") or None
    salary_max = j.get("jobSalaryMax") or None
    area = j.get("jobAreaString") or ""
    city = extract_city(area)
    experience = j.get("workYearString") or ""
    education = j.get("degreeString") or ""

    # 公司：优先用全称
    company = j.get("fullCompanyName") or j.get("companyName") or ""
    company_size = j.get("companySizeString") or ""
    company_industry = j.get("companyIndustryType1Str") or ""
    company_type = j.get("companyTypeString") or ""

    # 链接
    job_url = j.get("jobHref") or ""
    company_link = j.get("companyHref") or ""

    # HR信息
    hr_name = j.get("hrName") or ""
    publish_date = j.get("issueDateString") or ""

    # JD拆分
    jd_raw = j.get("jobDescribe") or ""
    responsibilities, requirements, detail_text = split_jd(jd_raw)
    has_detail = bool(detail_text and len(detail_text) > 20)

    # 标签/技能
    tags = parse_job_tags(j.get("jobTags"), j.get("jobTagsList"))
    # 技能标签：过滤掉学历、经验等非技能标签
    skill_keywords = ["测绘", "测量", "GIS", "ArcGIS", "CAD", "CASS", "ENVI", "遥感",
                      "地籍", "地形", "国土", "规划", "数据", "制图", "GPS", "RTK",
                      "全站仪", "水准仪", "Python", "SQL", "数据库", "矢量化", "空间分析"]
    skills = [t for t in tags if any(kw.lower() in t.lower() for kw in skill_keywords)]
    job_labels = tags  # 全部标签保留
    benefits = parse_welfare(j.get("jobWelfareCodeDataList"))

    # 经纬度
    lon = j.get("lon")
    lat = j.get("lat")
    is_intern = bool(j.get("isIntern"))

    return {
        # 基本信息
        "company": company,
        "position": position,
        "city": city,
        "work_location": area,
        "salary": salary,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "education": education,
        "experience": experience,
        # 标签
        "skills": skills,
        "job_labels": job_labels,
        "benefits": benefits,
        # 公司信息
        "company_size": company_size,
        "company_industry": company_industry,
        "company_type": company_type,
        "company_intro": "",
        # JD
        "responsibilities": responsibilities,
        "requirements": requirements,
        "detail_text": detail_text,
        "has_detail": has_detail,
        # 链接
        "company_link": company_link,
        "source": "前程无忧",
        "job_url": job_url,
        "encrypt_job_id": job_id,
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # 51job特有扩展字段
        "hr_name": hr_name,
        "publish_date": publish_date,
        "is_intern": is_intern,
        "longitude": lon,
        "latitude": lat,
    }


def parse_51job(job_list):
    """
    解析51job岗位列表，返回标准岗位列表。
    自动跳过无效岗位（无职位名或无公司名）。
    """
    if not job_list:
        return []
    results = []
    skipped = 0
    for j in job_list:
        if not isinstance(j, dict):
            skipped += 1
            continue
        name = j.get("jobName") or ""
        company = j.get("fullCompanyName") or j.get("companyName") or ""
        if not name or not company:
            skipped += 1
            continue
        try:
            results.append(parse_one(j))
        except Exception as e:
            skipped += 1
            print(f"  [警告] 解析岗位失败: {name[:30]}... 错误: {e}")
    return results


def dedupe_51job(jobs):
    """
    51job岗位去重。按 (公司名, 职位名) 去重，保留第一个。
    """
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
        print("用法: python parse_51job_api.py <导出JSON文件>")
        sys.exit(1)

    path = sys.argv[1]
    raw = json.load(open(path, encoding="utf-8"))
    job51_list = raw.get("job51_jobs", [])
    print(f"原始51job岗位数: {len(job51_list)}")

    jobs = parse_51job(job51_list)
    print(f"解析成功: {len(jobs)}")

    jobs = dedupe_51job(jobs)
    print(f"去重后: {len(jobs)}")

    # 统计
    has_jd = sum(1 for j in jobs if j["has_detail"])
    cities = {}
    for j in jobs:
        c = j["city"]
        cities[c] = cities.get(c, 0) + 1
    print(f"\n有完整JD: {has_jd}/{len(jobs)} ({has_jd*100//max(len(jobs),1)}%)")
    print(f"城市分布: {dict(sorted(cities.items(), key=lambda x: -x[1])[:5])}")

    # 显示前3条
    print("\n=== 前3条解析结果 ===")
    for i, j in enumerate(jobs[:3]):
        print(f"\n[{i+1}] {j['position']} @ {j['company']}")
        print(f"    薪资: {j['salary']} | 地点: {j['work_location']} | 学历: {j['education']} | 经验: {j['experience']}")
        print(f"    公司: {j['company_industry']} | {j['company_type']} | {j['company_size']}")
        print(f"    标签: {j['job_labels'][:5]}")
        print(f"    福利: {j['benefits'][:5]}")
        print(f"    JD长度: 职责{len(j['responsibilities'])}字 / 要求{len(j['requirements'])}字 / 全文{len(j['detail_text'])}字")
        if j['responsibilities']:
            print(f"    职责预览: {j['responsibilities'][:80]}...")
        if j['requirements']:
            print(f"    要求预览: {j['requirements'][:80]}...")
        print(f"    链接: {j['job_url'][:80]}")
