# -*- coding: utf-8 -*-
"""
阶段2-网申雷达：两源合并报告生成器
输入：国聘网岗位JSON + 牛客公司JSON
输出：统一HTML报告（岗位推荐板块 + 校招日程板块）
用法：python radar_merged_report.py <guopin_json> <nowcoder_json>
"""
import json, io, os, sys, html as html_mod
from datetime import datetime
import sys as _sys, os as _os
_WS = _os.path.dirname(_os.path.abspath(__file__))
if _WS not in _sys.path: _sys.path.insert(0, _WS)
import report_theme as T

WS = os.path.dirname(os.path.abspath(__file__))
RADAR_DIR = os.path.join(WS, "radar")

USER_PROFILE = {
    "name": "张三",
    "major": "测绘工程",
    "degree": "本科",
    "job_intention": "测绘工程师",
    "expected_salary_min": 6000,
    "expected_salary_max": 8000,
    "skills": ["测绘", "测量", "GIS", "ArcGIS", "CAD", "遥感", "摄影测量", "无人机", "航摄",
               "RTK", "全站仪", "GNSS", "地籍", "土地", "空间数据", "地形", "DEM", "数据库"],
}

def calc_match_score(job):
    """国聘网岗位匹配评分"""
    score = 50
    reasons = []
    jd_text = (job.get("jd_full", "") + job.get("title", "") + job.get("category", "")).lower()
    skill_hits = sum(1 for s in USER_PROFILE["skills"] if s.lower() in jd_text)
    matched = [s for s in USER_PROFILE["skills"] if s.lower() in jd_text]

    if skill_hits >= 5: score += 25; reasons.append(f"专业匹配高({skill_hits}关键词)")
    elif skill_hits >= 3: score += 15; reasons.append(f"专业匹配中({skill_hits}关键词)")
    elif skill_hits >= 1: score += 5; reasons.append(f"部分匹配({skill_hits})")
    else: score -= 10; reasons.append("专业匹配低")

    edu = job.get("education", "")
    if any(k in edu for k in ["硕士", "博士", "研究生"]): score -= 20; reasons.append(f"学历要求{edu}(不匹配)")
    elif any(k in edu for k in ["本科", "大专", "不限"]) or not edu: score += 15; reasons.append("学历匹配(本科)")

    exp = job.get("experience", "")
    if any(k in exp for k in ["应届", "不限"]) or not exp: score += 10; reasons.append("经验匹配(应届/不限)")
    elif any(k in exp for k in ["1年", "2年", "3年"]): score -= 5; reasons.append(f"要求{exp}经验")
    else: score -= 10; reasons.append(f"经验要求{exp}(不匹配)")

    if job.get("is_soe"): score += 10; reasons.append("国企(符合偏好)")
    if job.get("is_campus"): score += 10; reasons.append("校园招聘")

    sal_min = job.get("salary_min", 0) or 0
    sal_max = job.get("salary_max", 0) or 0
    if sal_min > 0 and sal_max > 0:
        if sal_min <= USER_PROFILE["expected_salary_max"] and sal_max >= USER_PROFILE["expected_salary_min"]:
            score += 10; reasons.append(f"薪资匹配({job['salary']})")
        elif sal_max < USER_PROFILE["expected_salary_min"]: score -= 5; reasons.append("薪资偏低")
        else: score += 5; reasons.append("薪资可接受")

    if job.get("jd_full") and len(job["jd_full"]) > 50: score += 5; reasons.append("JD完整")
    score = max(0, min(100, score))
    return score, reasons, matched

def get_match_level(score):
    if score >= 80: return "高度匹配", "#52c41a"
    elif score >= 65: return "较匹配", "#1890ff"
    elif score >= 50: return "一般匹配", "#faad14"
    else: return "不匹配", "#ff4d4f"

def generate_merged_html(guopin_data, nowcoder_data):
    """生成合并HTML报告"""
    jobs = guopin_data.get("jobs", [])
    companies = nowcoder_data.get("companies", [])

    # 岗位匹配评分
    for job in jobs:
        score, reasons, matched = calc_match_score(job)
        job["_score"] = score
        job["_reasons"] = reasons
        job["_matched"] = matched
    jobs.sort(key=lambda x: x["_score"], reverse=True)

    # 公司按网申截止时间排序
    def get_end_date(c):
        return c.get("wangshen_end", "")
    companies.sort(key=get_end_date)

    # 统计
    total_jobs = len(jobs)
    soe_jobs = sum(1 for j in jobs if j.get("is_soe"))
    campus_jobs = sum(1 for j in jobs if j.get("is_campus"))
    high_match = sum(1 for j in jobs if j["_score"] >= 80)
    avg_score = sum(j["_score"] for j in jobs) / total_jobs if total_jobs else 0

    total_companies = len(companies)
    soe_companies = sum(1 for c in companies if c.get("is_soe"))
    active_companies = sum(1 for c in companies if c.get("wangshen_active"))

    # 岗位卡片
    job_cards = ""
    for i, job in enumerate(jobs, 1):
        level, color = get_match_level(job["_score"])
        reasons_html = "".join(f'<span class="reason-tag">{html_mod.escape(r)}</span>' for r in job["_reasons"])
        matched_html = "".join(f'<span class="skill-tag">{html_mod.escape(s)}</span>' for s in job["_matched"]) if job["_matched"] else '<span class="no-skill">无明显技能匹配</span>'
        jd_full = html_mod.escape(job.get("jd_full", "")[:2000])
        job_cards += f'''
        <div class="job-card">
            <div class="job-header">
                <div class="job-rank">#{i}</div>
                <div class="job-title-area">
                    <div class="job-title">{html_mod.escape(job.get("title", ""))}</div>
                    <div class="job-company">
                        <span class="company-name">{html_mod.escape(job.get("company", ""))}</span>
                        <span class="company-type">{html_mod.escape(job.get("company_type", ""))}</span>
                        {"<span class='campus-badge'>校招</span>" if job.get("is_campus") else ""}
                    </div>
                </div>
                <div class="job-score" style="border-color:{color}">
                    <div class="score-num" style="color:{color}">{job["_score"]}</div>
                    <div class="score-label" style="color:{color}">{level}</div>
                </div>
            </div>
            <div class="job-meta">
                <span class="meta-item">💰 {html_mod.escape(job.get("salary", "面议"))}</span>
                <span class="meta-item">🎓 {html_mod.escape(job.get("education", "不限"))}</span>
                <span class="meta-item">📋 {html_mod.escape(job.get("experience", "不限"))}</span>
                <span class="meta-item">📍 {html_mod.escape(job.get("location", "不限"))}</span>
                <span class="meta-item">⏰ 截止{html_mod.escape(str(job.get("deadline", ""))[:10])}</span>
            </div>
            <div class="job-reasons">{reasons_html}</div>
            <div class="job-skills"><span class="skills-label">命中技能：</span>{matched_html}</div>
            <div class="job-actions">
                <a href="{html_mod.escape(job.get('detail_url', ''))}" target="_blank" class="btn btn-primary">查看岗位</a>
                <a href="{html_mod.escape(job.get('company_url', ''))}" target="_blank" class="btn btn-secondary">查看公司</a>
                <button class="btn btn-toggle" onclick="toggleJD(this)">展开JD详情</button>
            </div>
            <div class="job-jd-detail" style="display:none">
                <div class="jd-section">
                    <div class="jd-title">📄 完整JD原文</div>
                    <div class="jd-content jd-full">{jd_full}</div>
                </div>
            </div>
        </div>'''

    # 公司卡片
    company_cards = ""
    for i, comp in enumerate(companies, 1):
        cities = ", ".join(comp["cities"][:5]) if comp["cities"] else "不限"
        if len(comp["cities"]) > 5: cities += f" 等{len(comp['cities'])}城"
        careers = ", ".join(comp["job_categories"][:6]) if comp["job_categories"] else "多类别"
        if len(comp["job_categories"]) > 6: careers += f" 等{len(comp['job_categories'])}类"
        active_badge = '<span class="active-badge">网申中</span>' if comp.get("wangshen_active") else '<span class="inactive-badge">未开始/已结束</span>'
        official_link = f'<a href="{html_mod.escape(comp.get("official_url", ""))}" target="_blank" class="btn btn-primary">官方网申入口</a>' if comp.get("official_url") else '<span class="no-link">暂无官方链接</span>'
        company_cards += f'''
        <div class="company-card">
            <div class="company-header">
                <div class="company-rank">#{i}</div>
                <div class="company-info">
                    <div class="company-name">{html_mod.escape(comp.get("company", ""))} {active_badge}</div>
                    <div class="company-meta">
                        <span class="meta-item">📍 {html_mod.escape(cities)}</span>
                        <span class="meta-item">📅 网申 {html_mod.escape(comp.get("wangshen_start", ""))} ~ {html_mod.escape(comp.get("wangshen_end", ""))}</span>
                        <span class="meta-item">🏢 {html_mod.escape(comp.get("company_type", ""))}</span>
                    </div>
                </div>
            </div>
            <div class="company-categories">
                <span class="cat-label">招聘类别：</span>
                <span class="cat-text">{html_mod.escape(careers)}</span>
            </div>
            <div class="company-actions">{official_link}</div>
        </div>'''

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>网申雷达综合报告</title>
<style>{T.THEME_CSS}</style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <h1>🎯 网申雷达综合报告</h1>
        <div class="subtitle">数据来源：国聘网（岗位推荐）+ 牛客校招日程（公司校招） | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")} | 求职者：{USER_PROFILE["name"]}（{USER_PROFILE["major"]}·{USER_PROFILE["degree"]}）</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card"><div class="stat-num">{total_jobs}</div><div class="stat-label">国聘岗位数</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#52c41a">{soe_jobs}</div><div class="stat-label">国企岗位</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#1890ff">{campus_jobs}</div><div class="stat-label">校招岗位</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#faad14">{high_match}</div><div class="stat-label">高度匹配(≥80)</div></div>
        <div class="stat-card"><div class="stat-num">{avg_score:.0f}</div><div class="stat-label">平均匹配分</div></div>
        <div class="stat-card"><div class="stat-num">{total_companies}</div><div class="stat-label">牛客校招公司</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#52c41a">{active_companies}</div><div class="stat-label">网申进行中</div></div>
    </div>

    <div class="section-title">📋 板块一：国聘网岗位推荐（按匹配度排序）</div>
    <div class="section-desc">基于你的专业背景、技能、学历、薪资期望自动评分，建议对高度匹配岗位点击"查看岗位"深入了解后人工判断是否投递。</div>
    <div id="job-list">{job_cards}</div>

    <div class="section-title">🏢 板块二：牛客校招日程（按网申截止时间排序）</div>
    <div class="section-desc">大型企业校招日程汇总，点击"官方网申入口"直达企业招聘官网查看是否有测绘/地理信息相关岗位。</div>
    <div id="company-list">{company_cards}</div>

    <div class="report-footer">
        网申雷达 v1.0 | 数据源：国聘网 + 牛客 | 匹配算法基于用户画像自动评分，仅供参考<br>
        建议：对感兴趣的岗位/公司点击链接深入了解，人工判断后再投递
    </div>
</div>
<script>
function toggleJD(btn) {{
    const detail = btn.closest('.job-card').querySelector('.job-jd-detail');
    if (detail.style.display === 'none') {{ detail.style.display = 'block'; btn.textContent = '收起JD详情'; }}
    else {{ detail.style.display = 'none'; btn.textContent = '展开JD详情'; }}
}}
</script>
</body>
</html>'''
    return html_content

def main():
    if len(sys.argv) < 3:
        print("用法: python radar_merged_report.py <guopin_json> <nowcoder_json>")
        sys.exit(1)

    guopin_path = sys.argv[1]
    nowcoder_path = sys.argv[2]

    with io.open(guopin_path, encoding="utf-8") as f:
        guopin_data = json.load(f)
    with io.open(nowcoder_path, encoding="utf-8") as f:
        nowcoder_data = json.load(f)

    html_content = generate_merged_html(guopin_data, nowcoder_data)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(RADAR_DIR, f"网申雷达综合报告_{len(guopin_data.get('jobs',[]))}岗位_{len(nowcoder_data.get('companies',[]))}公司_{timestamp}.html")

    with io.open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"综合报告已生成: {output_path}")
    print(f"  国聘岗位: {len(guopin_data.get('jobs', []))} 条")
    print(f"  牛客公司: {len(nowcoder_data.get('companies', []))} 家")

if __name__ == "__main__":
    main()
