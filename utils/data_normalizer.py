"""
数据标准化工具 - 将现有岗位数据转换为统一Schema格式

使用方法：
    from utils.data_normalizer import normalize_job, normalize_jobs_list

    # 标准化单个岗位
    normalized_job = normalize_job(old_job_data)

    # 批量标准化岗位列表
    normalized_jobs = normalize_jobs_list(old_jobs_list)
"""

import os
import json
import re
import hashlib
from datetime import datetime


def clean_text(text):
    """清理文本：去除多余符号、空白字符"""
    if not text or not isinstance(text, str):
        return ""

    # 去除首尾空白
    text = text.strip()

    # 去除常见的多余符号（如【】、】、【等）
    text = re.sub(r'^[【】\[\]\(\)\s]+', '', text)
    text = re.sub(r'[【】\[\]\(\)\s]+$', '', text)

    # 去除多余的空白字符
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def parse_city_field(city_text):
    """
    解析city字段，分离城市、经验、学历
    旧格式可能包含："广州        经验不限\n本科"
    """
    if not city_text or not isinstance(city_text, str):
        return "", "", ""

    city = ""
    experience = ""
    education = ""

    # 按空白字符分割
    parts = re.split(r'[\s\n]+', city_text.strip())
    parts = [p for p in parts if p]

    if parts:
        city = parts[0]  # 第一个通常是城市

    # 查找经验和学历
    for part in parts[1:]:
        if "经验" in part or "年" in part or "应届" in part:
            experience = part
        elif "本科" in part or "硕士" in part or "博士" in part or "大专" in part or "学历" in part:
            education = part

    return city, experience, education


def parse_salary(salary_text):
    """
    解析薪资范围，返回最低和最高月薪（元）
    支持格式：6-9K、6-9K·14薪、6000-10000元、面议等
    """
    if not salary_text or not isinstance(salary_text, str):
        return None, None

    salary_min = None
    salary_max = None

    # 去除"·14薪"等后缀
    salary_text = re.sub(r'·\d+薪', '', salary_text)
    salary_text = salary_text.strip()

    if "面议" in salary_text or salary_text == "":
        return None, None

    # 匹配 K 格式（如 6-9K）
    k_match = re.match(r'(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*[Kk]', salary_text)
    if k_match:
        salary_min = float(k_match.group(1)) * 1000
        salary_max = float(k_match.group(2)) * 1000
        return salary_min, salary_max

    # 匹配 元 格式（如 6000-10000元）
    yuan_match = re.match(r'(\d+)\s*[-~]\s*(\d+)\s*元', salary_text)
    if yuan_match:
        salary_min = float(yuan_match.group(1))
        salary_max = float(yuan_match.group(2))
        return salary_min, salary_max

    # 匹配 万/月 格式（如 0.6-0.9万/月）
    wan_match = re.match(r'(\d+(?:\.\d+)?)\s*[-~]\s*(\d+(?:\.\d+)?)\s*万', salary_text)
    if wan_match:
        salary_min = float(wan_match.group(1)) * 10000
        salary_max = float(wan_match.group(2)) * 10000
        return salary_min, salary_max

    return salary_min, salary_max


def separate_skills_and_benefits(skills_list):
    """
    分离专业技能和福利待遇
    旧格式中skills字段可能混合了福利标签
    """
    if not skills_list or not isinstance(skills_list, list):
        return [], []

    # 常见福利关键词
    benefit_keywords = [
        "五险一金", "意外险", "定期体检", "年终奖", "底薪加提成",
        "带薪年假", "餐补", "免费工装", "通讯补贴", "节日福利",
        "生日福利", "交通补助", "加班补助", "补充医疗", "员工旅游",
        "带薪病假", "弹性工作", "远程办公", "股票期权", "绩效奖金",
        "全勤奖", "工龄奖", "高温补贴", "取暖补贴", "住房补贴",
        "子女福利", "培训机会", "晋升空间", "扁平管理", "领导好"
    ]

    skills = []
    benefits = []

    for item in skills_list:
        if not item or not isinstance(item, str):
            continue
        item = item.strip()
        if not item:
            continue

        # 判断是否是福利
        is_benefit = False
        for keyword in benefit_keywords:
            if keyword in item:
                is_benefit = True
                break

        if is_benefit:
            if item not in benefits:
                benefits.append(item)
        else:
            if item not in skills:
                skills.append(item)

    return skills, benefits


def generate_job_id(company, position, source):
    """生成岗位唯一ID"""
    raw = f"{source}_{company}_{position}"
    hash_obj = hashlib.md5(raw.encode("utf-8"))
    hash_short = hash_obj.hexdigest()[:8]
    return f"{source}_{company}_{position}_{hash_short}"


def normalize_job(old_job):
    """
    将旧格式岗位数据转换为新Schema格式

    Args:
        old_job: 旧格式岗位数据

    Returns:
        dict: 标准化后的岗位数据
    """
    if not old_job or not isinstance(old_job, dict):
        return None

    # 解析city字段
    raw_city = old_job.get("city", "")
    city, experience_from_city, education_from_city = parse_city_field(raw_city)

    # 解析薪资
    salary_text = old_job.get("salary", "")
    salary_min, salary_max = parse_salary(salary_text)

    # 分离技能和福利
    raw_skills = old_job.get("skills", [])
    skills, benefits = separate_skills_and_benefits(raw_skills)

    # 清理岗位职责和任职要求
    responsibilities = clean_text(old_job.get("responsibilities", ""))
    requirements = clean_text(old_job.get("requirements", ""))

    # 如果responsibilities或requirements为空，尝试从detail_text或jd_text提取
    if not responsibilities and not requirements:
        detail_text = old_job.get("detail_text", "") or old_job.get("jd_text", "")
        if detail_text:
            # 尝试按"岗位职责"和"任职要求"分割
            if "岗位职责" in detail_text and "任职要求" in detail_text:
                parts = detail_text.split("任职要求")
                responsibilities = clean_text(parts[0].replace("岗位职责", ""))
                requirements = clean_text(parts[1])
            elif "岗位职责" in detail_text:
                responsibilities = clean_text(detail_text.replace("岗位职责", ""))
            elif "任职要求" in detail_text:
                requirements = clean_text(detail_text.replace("任职要求", ""))

    # 获取公司链接（优先使用company_link，否则生成搜索链接）
    company_link = old_job.get("company_link", "")
    if not company_link and old_job.get("company"):
        source = old_job.get("source", "其他")
        if source == "智联招聘":
            company_link = f"https://sou.zhaopin.com/?jl=763&kw={old_job['company']}"
        elif source == "BOSS直聘":
            company_link = f"https://www.zhipin.com/web/geek/jobs?query={old_job['company']}"

    # 获取岗位URL（优先使用job_url，其次url）
    job_url = old_job.get("job_url", "") or old_job.get("url", "")

    # 获取采集时间
    collected_at = old_job.get("collected_at", "")
    if not collected_at:
        collected_at = datetime.now().isoformat()

    # 生成岗位ID
    company = old_job.get("company", "未知公司")
    position = old_job.get("position", "未知岗位")
    source = old_job.get("source", "其他")
    job_id = old_job.get("id", "") or generate_job_id(company, position, source)

    # 构建标准化数据
    normalized = {
        "id": job_id,
        "company": company,
        "position": position,
        "city": city or old_job.get("city", ""),
        "salary": salary_text,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "education": old_job.get("education", "") or education_from_city,
        "experience": old_job.get("experience", "") or experience_from_city,
        "skills": skills,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "benefits": benefits,
        "jd_text": old_job.get("jd_text", "") or old_job.get("detail_text", ""),
        "company_size": old_job.get("company_size", ""),
        "company_industry": old_job.get("company_industry", ""),
        "company_link": company_link,
        "work_location": old_job.get("work_location", ""),
        "source": source,
        "job_url": job_url,
        "collected_at": collected_at,
        "status": old_job.get("status", "待评估"),
        "match_score": old_job.get("match_score"),
        "match_detail": old_job.get("match_detail"),
        "notes": old_job.get("notes", "")
    }

    return normalized


def normalize_jobs_list(old_jobs):
    """
    批量标准化岗位列表

    Args:
        old_jobs: 旧格式岗位列表

    Returns:
        list: 标准化后的岗位列表
    """
    if not old_jobs or not isinstance(old_jobs, list):
        return []

    normalized = []
    for job in old_jobs:
        n_job = normalize_job(job)
        if n_job:
            normalized.append(n_job)

    return normalized


def deduplicate_jobs(jobs_list):
    """
    岗位去重（基于公司名+岗位名）
    跨平台重复时优先保留BOSS直聘
    """
    if not jobs_list:
        return []

    # 按公司+岗位分组
    groups = {}
    for job in jobs_list:
        key = f"{job.get('company', '')}_{job.get('position', '')}"
        if key not in groups:
            groups[key] = []
        groups[key].append(job)

    # 每组选择一个（优先BOSS直聘）
    result = []
    for key, group in groups.items():
        if len(group) == 1:
            result.append(group[0])
        else:
            # 优先选择BOSS直聘
            boss_jobs = [j for j in group if j.get("source") == "BOSS直聘"]
            if boss_jobs:
                result.append(boss_jobs[0])
            else:
                result.append(group[0])

    return result


if __name__ == "__main__":
    # 测试数据标准化
    import sys
    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if workspace not in sys.path:
        sys.path.insert(0, workspace)

    print("=" * 60)
    print("数据标准化工具测试")
    print("=" * 60)

    # 加载岗位库
    jobs_path = os.path.join(workspace, "jobs.json")
    if os.path.exists(jobs_path):
        with open(jobs_path, "r", encoding="utf-8") as f:
            old_jobs = json.load(f)

        print(f"\n原始岗位数: {len(old_jobs)}")

        # 标准化
        normalized_jobs = normalize_jobs_list(old_jobs)
        print(f"标准化后岗位数: {len(normalized_jobs)}")

        # 去重
        deduped_jobs = deduplicate_jobs(normalized_jobs)
        print(f"去重后岗位数: {len(deduped_jobs)}")

        # 验证标准化后的数据
        from utils.validator import validate_jobs_list
        all_errors = validate_jobs_list(deduped_jobs)
        if all_errors:
            print(f"\n验证发现 {len(all_errors)}/{len(deduped_jobs)} 个岗位有错误")
            # 显示前3个岗位的错误
            for i, (idx, errors) in enumerate(list(all_errors.items())[:3]):
                job = deduped_jobs[idx] if idx < len(deduped_jobs) else None
                print(f"\n岗位 {idx}: {job.get('company', '?')} - {job.get('position', '?')}")
                for e in errors[:5]:
                    print(f"  - {e}")
        else:
            print(f"\n全部 {len(deduped_jobs)} 个岗位验证通过 ✓")

        # 显示第一个标准化后的岗位
        if deduped_jobs:
            print("\n" + "=" * 60)
            print("第一个标准化后的岗位示例:")
            print("=" * 60)
            print(json.dumps(deduped_jobs[0], ensure_ascii=False, indent=2)[:1500])

        # 保存标准化后的数据
        output_path = os.path.join(workspace, "jobs_normalized.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deduped_jobs, f, ensure_ascii=False, indent=2)
        print(f"\n标准化后的数据已保存到: {output_path}")

    else:
        print("岗位库文件不存在")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
