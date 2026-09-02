# -*- coding: utf-8 -*-
"""
阶段2-网申雷达：岗位匹配评分 + HTML报告生成器
输入：radar/guopin_*.json（国聘网采集结果）
输出：radar/雷达报告_*.html
用法：python radar_report.py <json文件路径>
"""
import json, io, os, sys, re, html
from datetime import datetime
import sys as _sys, os as _os
_WS = _os.path.dirname(_os.path.abspath(__file__))
if _WS not in _sys.path: _sys.path.insert(0, _WS)
import report_theme as T

WS = os.path.dirname(os.path.abspath(__file__))
RADAR_DIR = os.path.join(WS, "radar")

# 用户画像（从resume_data/application_profile继承）
USER_PROFILE = {
    "name": "张三",
    "major": "测绘工程",
    "degree": "本科",
    "job_intention": "测绘工程师",
    "expected_salary_min": 6000,
    "expected_salary_max": 8000,
    "skills": ["测绘", "测量", "GIS", "ArcGIS", "CAD", "遥感", "摄影测量", "无人机", "航摄",
               "RTK", "全站仪", "GNSS", "地籍", "土地", "空间数据", "地形", "DEM", "数据库"],
    "accept_soe": True,
    "accept_campus": True,
}

def calc_match_score(job):
    """计算岗位匹配度（0-100分）"""
    score = 50  # 基础分
    reasons = []

    # 1. 专业/技能匹配（最重要，+30上限）
    jd_text = (job.get("jd_full", "") + job.get("title", "") + job.get("category", "")).lower()
    skill_hits = 0
    matched_skills = []
    for skill in USER_PROFILE["skills"]:
        if skill.lower() in jd_text:
            skill_hits += 1
            matched_skills.append(skill)
    if skill_hits >= 5:
        score += 25
        reasons.append(f"专业匹配高（命中{skill_hits}个技能关键词）")
    elif skill_hits >= 3:
        score += 15
        reasons.append(f"专业匹配中（命中{skill_hits}个技能关键词）")
    elif skill_hits >= 1:
        score += 5
        reasons.append(f"部分专业匹配（命中{skill_hits}个）")
    else:
        score -= 10
        reasons.append("专业匹配低")

    # 2. 学历匹配（+15/-25）
    edu = job.get("education", "")
    if "硕士" in edu or "博士" in edu or "研究生" in edu:
        score -= 20
        reasons.append(f"学历要求{edu}（用户本科，不匹配）")
    elif "本科" in edu or "大专" in edu or "不限" in edu or edu == "":
        score += 15
        reasons.append("学历匹配（本科）")

    # 3. 经验匹配（+10/-10）
    exp = job.get("experience", "")
    if "应届" in exp or "不限" in exp or exp == "":
        score += 10
        reasons.append("经验要求匹配（应届/不限）")
    elif "1年" in exp or "2年" in exp or "3年" in exp:
        score -= 5
        reasons.append(f"要求{exp}经验（用户应届）")
    else:
        score -= 10
        reasons.append(f"经验要求{exp}（不匹配）")

    # 4. 公司性质（国企+10）
    if job.get("is_soe"):
        score += 10
        reasons.append("国企（符合偏好）")

    # 5. 校招（+10）
    if job.get("is_campus"):
        score += 10
        reasons.append("校园招聘")

    # 6. 薪资匹配（+10/-5）
    sal_min = job.get("salary_min", 0) or 0
    sal_max = job.get("salary_max", 0) or 0
    if sal_min > 0 and sal_max > 0:
        if sal_min <= USER_PROFILE["expected_salary_max"] and sal_max >= USER_PROFILE["expected_salary_min"]:
            score += 10
            reasons.append(f"薪资匹配（{job['salary']}）")
        elif sal_max < USER_PROFILE["expected_salary_min"]:
            score -= 5
            reasons.append(f"薪资偏低（{job['salary']}）")
        else:
            score += 5
            reasons.append(f"薪资可接受（{job['salary']}）")

    # 7. JD完整度（+5）
    if job.get("jd_full") and len(job["jd_full"]) > 50:
        score += 5
        reasons.append("JD信息完整")

    # 限制在0-100
    score = max(0, min(100, score))
    return score, reasons, matched_skills

def get_match_level(score):
    if score >= 80:
        return "高度匹配", "#52c41a"
    elif score >= 65:
        return "较匹配", "#1890ff"
    elif score >= 50:
        return "一般匹配", "#faad14"
    else:
        return "不匹配", "#ff4d4f"

def generate_html(data, json_path):
    """生成HTML报告"""
    jobs = data.get("jobs", [])
    source = data.get("source", "国聘网")
    keywords = data.get("keywords", [])

    # 计算匹配度
    for job in jobs:
        score, reasons, matched = calc_match_score(job)
        job["_score"] = score
        job["_reasons"] = reasons
        job["_matched_skills"] = matched

    # 按匹配度排序
    jobs.sort(key=lambda x: x["_score"], reverse=True)

    # 统计
    total = len(jobs)
    soe_count = sum(1 for j in jobs if j.get("is_soe"))
    campus_count = sum(1 for j in jobs if j.get("is_campus"))
    high_match = sum(1 for j in jobs if j["_score"] >= 80)
    mid_match = sum(1 for j in jobs if 65 <= j["_score"] < 80)
    avg_score = sum(j["_score"] for j in jobs) / total if total else 0

    # 生成岗位卡片
    job_cards = ""
    for i, job in enumerate(jobs, 1):
        level, color = get_match_level(job["_score"])
        reasons_html = "".join(f'<span class="reason-tag">{html.escape(r)}</span>' for r in job["_reasons"])
        matched_html = "".join(f'<span class="skill-tag">{html.escape(s)}</span>' for s in job["_matched_skills"]) if job["_matched_skills"] else '<span class="no-skill">无明显技能匹配</span>'

        jd_duty = html.escape(job.get("jd_duty", "")[:500])
        jd_req = html.escape(job.get("jd_req", "")[:500])
        jd_full = html.escape(job.get("jd_full", "")[:2000])

        job_cards += f'''
        <div class="job-card" data-score="{job['_score']}">
            <div class="job-header">
                <div class="job-rank">#{i}</div>
                <div class="job-title-area">
                    <div class="job-title">{html.escape(job.get("title", ""))}</div>
                    <div class="job-company">
                        <span class="company-name">{html.escape(job.get("company", ""))}</span>
                        <span class="company-type">{html.escape(job.get("company_type", ""))}</span>
                        {"<span class='campus-badge'>校招</span>" if job.get("is_campus") else ""}
                    </div>
                </div>
                <div class="job-score" style="border-color:{color}">
                    <div class="score-num" style="color:{color}">{job["_score"]}</div>
                    <div class="score-label" style="color:{color}">{level}</div>
                </div>
            </div>
            <div class="job-meta">
                <span class="meta-item">💰 {html.escape(job.get("salary", "面议"))}</span>
                <span class="meta-item">🎓 {html.escape(job.get("education", "不限"))}</span>
                <span class="meta-item">📋 {html.escape(job.get("experience", "不限"))}</span>
                <span class="meta-item">📍 {html.escape(job.get("location", "不限"))}</span>
                <span class="meta-item">👥 招{job.get("headcount", 0)}人</span>
                <span class="meta-item">⏰ 截止{html.escape(str(job.get("deadline", ""))[:10])}</span>
            </div>
            <div class="job-reasons">{reasons_html}</div>
            <div class="job-skills">
                <span class="skills-label">命中技能：</span>{matched_html}
            </div>
            <div class="job-actions">
                <a href="{html.escape(job.get('detail_url', ''))}" target="_blank" class="btn btn-primary">查看岗位</a>
                <a href="{html.escape(job.get('company_url', ''))}" target="_blank" class="btn btn-secondary">查看公司</a>
                <button class="btn btn-toggle" onclick="toggleJD(this)">展开JD详情</button>
            </div>
            <div class="job-jd-detail" style="display:none">
                <div class="jd-section">
                    <div class="jd-title">📋 岗位职责</div>
                    <div class="jd-content">{jd_duty if jd_duty else "（暂无）"}</div>
                </div>
                {"<div class='jd-section'><div class='jd-title'>✅ 任职要求</div><div class='jd-content'>" + jd_req + "</div></div>" if jd_req else ""}
                <div class="jd-section">
                    <div class="jd-title">📄 完整JD原文</div>
                    <div class="jd-content jd-full">{jd_full}</div>
                </div>
            </div>
        </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>网申雷达报告 - {source}</title>
<style>{T.THEME_CSS}</style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <h1>🎯 网申雷达岗位推荐报告</h1>
        <div class="subtitle">数据来源：{source} | 关键词：{html.escape(", ".join(keywords))} | 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")} | 求职者：{USER_PROFILE["name"]}（{USER_PROFILE["major"]}·{USER_PROFILE["degree"]}）</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card"><div class="stat-num">{total}</div><div class="stat-label">岗位总数</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#52c41a">{soe_count}</div><div class="stat-label">国企岗位</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#1890ff">{campus_count}</div><div class="stat-label">校园招聘</div></div>
        <div class="stat-card"><div class="stat-num" style="color:#faad14">{high_match}</div><div class="stat-label">高度匹配(≥80)</div></div>
        <div class="stat-card"><div class="stat-num">{mid_match}</div><div class="stat-label">较匹配(65-79)</div></div>
        <div class="stat-card"><div class="stat-num">{avg_score:.0f}</div><div class="stat-label">平均匹配分</div></div>
    </div>

    <div class="filter-bar">
        <span class="filter-title">筛选：</span>
        <label><input type="checkbox" id="filter-soe" onchange="applyFilters()"> 仅国企</label>
        <label><input type="checkbox" id="filter-campus" onchange="applyFilters()"> 仅校招</label>
        <label><input type="checkbox" id="filter-high" onchange="applyFilters()"> 仅高度匹配(≥80)</label>
        <label><input type="checkbox" id="filter-bachelor" onchange="applyFilters()"> 仅本科可投</label>
    </div>

    <div id="job-list">
        {job_cards}
    </div>

    <div class="report-footer">
        网申雷达 v1.0 | 数据来源：{source} | 匹配算法基于用户画像自动评分，仅供参考<br>
        建议对高度匹配岗位点击"查看岗位"深入了解后，人工判断是否投递
    </div>
</div>

<script>
function toggleJD(btn) {{
    const detail = btn.closest('.job-card').querySelector('.job-jd-detail');
    if (detail.style.display === 'none') {{
        detail.style.display = 'block';
        btn.textContent = '收起JD详情';
    }} else {{
        detail.style.display = 'none';
        btn.textContent = '展开JD详情';
    }}
}}

function applyFilters() {{
    const soeOnly = document.getElementById('filter-soe').checked;
    const campusOnly = document.getElementById('filter-campus').checked;
    const highOnly = document.getElementById('filter-high').checked;
    const bachelorOnly = document.getElementById('filter-bachelor').checked;
    const cards = document.querySelectorAll('.job-card');
    let visible = 0;
    cards.forEach(function(card) {{
        const score = parseInt(card.dataset.score);
        const text = card.textContent;
        let show = true;
        if (soeOnly && !text.includes('国企')) show = false;
        if (campusOnly && !text.includes('校招')) show = false;
        if (highOnly && score < 80) show = false;
        if (bachelorOnly && (text.includes('硕士') || text.includes('博士') || text.includes('研究生'))) show = false;
        card.style.display = show ? 'block' : 'none';
        if (show) visible++;
    }});
}}
</script>
</body>
</html>'''
    return html_content

def main():
    if len(sys.argv) < 2:
        print("用法: python radar_report.py <json文件路径>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"文件不存在: {json_path}")
        sys.exit(1)

    with io.open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    html_content = generate_html(data, json_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source = data.get("source", "radar")
    output_path = os.path.join(RADAR_DIR, f"雷达报告_{source}_{len(data.get('jobs',[]))}条_{timestamp}.html")

    with io.open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"报告已生成: {output_path}")
    print(f"岗位数: {len(data.get('jobs', []))}")

if __name__ == "__main__":
    main()
