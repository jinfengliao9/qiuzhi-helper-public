# -*- coding: utf-8 -*-
"""
智联招聘 搜索接口响应解析器（按真实样本精修 v1.1）
输入：扩展捕获的智联原始岗位条目列表（envelope.zhaopin_jobs）
输出：与岗位库对齐的标准岗位字典（source=智联招聘）

真实字段（www.zhaopin.com 搜索列表响应，2026-08 样本）：
- 岗位名: name          薪资: salary60（明文，如"3000-4000元"）
- 学历: education       经验: workingExp
- 城市: workCity        区县: cityDistrict    街道: streetName
- 公司: companyName     规模: companySize     行业: industryName    性质: propertyName
- 岗位链接: positionURL（部分缺失，用 number 拼 http://jobs.zhaopin.com/{number}.htm）
- 公司链接: companyUrl
- 技能: jobSkillTags[].name + skillLabel[].value
- 福利: jobDetailData.position.desc.welfareLabel / welfareTags
- 完整JD: jobDetailData.position.desc.description（100%覆盖，列表已内嵌，无需补详情）
"""
import html as html_lib
import re


def _txt(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, dict):
        if v.get("name"):
            return str(v["name"]).strip()
        if v.get("displayName"):
            return str(v["displayName"]).strip()
        items = v.get("items")
        if isinstance(items, list) and items:
            return "·".join(_txt(x) for x in items if _txt(x))
    if isinstance(v, list):
        return "·".join(_txt(x) for x in v if _txt(x))
    return str(v).strip()


def _clean_html(s):
    if not s:
        return ""
    s = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div|li|h\d|section)\s*>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_lib.unescape(s)
    lines = [re.sub(r"[ \t\u3000]+", " ", x).strip() for x in s.split("\n")]
    out = []
    for x in lines:
        if x and (not out or out[-1] != x):
            out.append(x)
    return "\n".join(out).strip()


def _split_jd(text):
    """智联JD常为职责+工作时间，无明确要求段时全部归入职责。"""
    if not text:
        return "", ""
    m = re.search(r"(?:任职|岗位|职位)?(?:要求|资格|条件|我们希望|你需要|任职资格)", text)
    if m and m.start() > 0:
        return text[:m.start()].strip(" ：:\n"), text[m.start():].strip()
    return text, ""


def _tag_names(arr):
    """从 [{'name':..}] / [{'value':..}] / ['str'] 中提取字符串标签。"""
    out = []
    if not isinstance(arr, list):
        return out
    for x in arr:
        if isinstance(x, dict):
            t = x.get("name") or x.get("value") or x.get("labelName") or x.get("tagName")
        else:
            t = x
        if t and str(t).strip() and str(t).strip() not in out:
            out.append(str(t).strip())
    return out


def map_one_zh(raw):
    if not isinstance(raw, dict):
        return None

    position = _txt(raw.get("name"))
    company = _txt(raw.get("companyName"))
    if not (position and company):
        return None

    salary = _txt(raw.get("salary60")) or _txt(raw.get("salaryReal")) or _txt(raw.get("salary"))
    education = _txt(raw.get("education"))
    experience = _txt(raw.get("workingExp"))
    city = _txt(raw.get("workCity"))
    district = _txt(raw.get("cityDistrict"))
    street = _txt(raw.get("streetName"))
    work_location = "·".join(x for x in [city, district, street] if x)

    comp_size = _txt(raw.get("companySize"))
    comp_ind = _txt(raw.get("industryName"))
    comp_prop = _txt(raw.get("propertyName"))
    company_info = " / ".join(x for x in [comp_ind, comp_prop, comp_size] if x)

    # 完整JD（列表已内嵌）
    jd = (raw.get("jobDetailData") or {}).get("position") or {}
    desc = jd.get("desc") if isinstance(jd, dict) else {}
    desc = desc if isinstance(desc, dict) else {}
    summary = _clean_html(_txt(desc.get("description")))
    resp, req = _split_jd(summary)

    # 技能：jobSkillTags + skillLabel
    skills = _tag_names(raw.get("jobSkillTags")) + _tag_names(raw.get("skillLabel"))
    skills = list(dict.fromkeys(skills))

    # 福利：desc.welfareLabel / welfareTags（顶层 welfareLabel 常为空）
    welfare = _tag_names(desc.get("welfareLabel")) + _tag_names(desc.get("welfareTags"))
    if not welfare:
        welfare = _tag_names(raw.get("welfareLabel"))
    welfare = list(dict.fromkeys(welfare))

    # 链接：positionURL 优先，缺失用 number 拼
    number = str(raw.get("number") or "").strip()
    job_url = _txt(raw.get("positionURL")) or _txt(raw.get("positionUrl"))
    if not job_url and number:
        job_url = f"http://jobs.zhaopin.com/{number}.htm"
    company_link = _txt(raw.get("companyUrl")) or (f"https://sou.zhaopin.com/?kw={company}" if company else "")

    return {
        "company": company,
        "position": position,
        "city": city,
        "work_location": work_location,
        "salary": salary,
        "education": education,
        "experience": experience,
        "skills": skills,
        "job_labels": [],
        "benefits": welfare,
        "company_size": comp_size,
        "company_industry": company_info,
        "responsibilities": resp,
        "requirements": req,
        "detail_text": summary,
        "company_intro": "",
        "has_detail": 1 if summary else 0,
        "company_link": company_link,
        "source": "智联招聘",
        "job_url": job_url,
        "encrypt_job_id": number,
        "collected_at": "",
    }


def parse_zhaopin(raw_items):
    out, seen = [], set()
    for it in raw_items or []:
        m = map_one_zh(it)
        if not m:
            continue
        key = m["encrypt_job_id"] or f"{m['company']}|{m['position']}"
        if key in seen:
            continue
        seen.add(key)
        out.append(m)
    return out
