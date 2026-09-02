# -*- coding: utf-8 -*-
"""
统一的岗位推荐报告生成脚本（统一主题版）
================================================================
视觉标准来自 report_theme.py（与网申雷达报告同一套主题），不再使用外部 CSS。
支持标准化岗位 Schema，覆盖 智联招聘 / BOSS直聘 / 前程无忧 / 猎聘 / 国聘网。

对外接口保持稳定（make_standalone_report、job_search、job_pipeline 均依赖）：
    from report_generator import generate_report
    out = generate_report(jobs, output_path, title="岗位推荐报告", subtitle="", notice="")
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_theme as T


def get_company_search_link(company, source):
    """公司详情页没有直链时的兜底：跳到对应平台搜索该公司。"""
    if source == '智联招聘':
        return f'https://sou.zhaopin.com/?kw={company}'
    elif source == 'BOSS直聘':
        return f'https://www.zhipin.com/web/geek/jobs?query={company}'
    elif source == '前程无忧':
        return f'https://we.51job.com/pc/search?keyword={company}'
    elif source == '猎聘':
        return f'https://www.liepin.com/zhaopin/?key={company}'
    elif source == '国聘网':
        return f'https://www.iguopin.com/search?keyword={company}'
    else:
        return f'https://www.baidu.com/s?wd={company}'


def _extract_dimensions(match_detail):
    """从 match_detail 提取五维分数，兼容扁平(tech_score)与嵌套(dimensions.tech.score)两种结构。"""
    if not isinstance(match_detail, dict):
        return []
    flat = [
        ('技术', match_detail.get('tech_score')),
        ('经验', match_detail.get('exp_score')),
        ('相关', match_detail.get('relevance_score')),
        ('硬约束', match_detail.get('hard_score')),
        ('偏好', match_detail.get('preference_score')),
    ]
    if any(v is not None for _, v in flat):
        return [(n, v) for n, v in flat if v is not None]
    # 兼容嵌套结构
    dims = match_detail.get('dimensions', {})
    keymap = [('技术匹配', 'tech_match'), ('经验匹配', 'experience_match'),
              ('行为匹配', 'behavior_match'), ('硬约束', 'hard_constraints')]
    out = []
    if isinstance(dims, dict):
        for name, key in keymap:
            d = dims.get(key)
            if isinstance(d, dict) and d.get('score') is not None:
                out.append((name, d.get('score')))
    return out


def generate_job_card_html(job, index):
    """生成单个岗位卡片（统一主题风格）。index 从 0 开始。"""
    company = job.get('company', '') or '未知公司'
    position = job.get('position', '') or '未知岗位'
    city = job.get('work_location', '') or job.get('city', '')
    salary = job.get('salary', '面议')
    education = job.get('education', '')
    experience = job.get('experience', '')
    source = job.get('source', '其他')
    company_size = job.get('company_size', '')
    company_industry = job.get('company_industry', '')

    score = job.get('match_score', 0)
    if score is None:
        score = 0
    match_detail = job.get('match_detail', {}) or {}

    # 平台徽标
    badges = T.source_badge(source)

    # 公司行：公司名 +（规模/行业放进 meta，这里只留名字）
    company_line = f'<span class="company-name">🏢 {T.esc(company)}</span>'

    # meta 标签
    meta = T.meta_items([
        (salary, 'salary'),
        (city, ''),
        (experience, ''),
        (education, ''),
        (company_size, ''),
        (company_industry, ''),
    ])

    # 五维评分
    dim_html = T.dimensions_bar(_extract_dimensions(match_detail))

    # 推荐语
    recommend = match_detail.get('recommendation', '') or ''

    # 技能标签：命中 / 缺失 / 岗位自带
    matched = match_detail.get('matched_skills', []) or []
    missing = match_detail.get('missing_skills', []) or []
    plain = [s for s in (job.get('skills', []) or []) if s not in matched and s not in missing]
    skills_html = T.skill_block(matched, missing, plain)

    # 按钮：岗位直链 + 公司链接（优先直链，缺失则平台搜索兜底）+ 展开JD
    job_url = job.get('job_url', '') or job.get('url', '')
    company_url = job.get('company_link', '') or get_company_search_link(company, source)
    company_label = '查看公司' if job.get('company_link') else '搜索公司'
    actions = T.action_buttons(job_url, company_url, company_label=company_label, show_toggle=True)

    # JD 折叠区块
    blocks = [
        ('📋 岗位职责', job.get('responsibilities', '')),
        ('✅ 任职要求', job.get('requirements', '')),
        ('🎁 薪资福利', job.get('benefits_text', '') or job.get('benefits', '')),
        ('🏷️ 职位描述', job.get('job_description', '')),
    ]
    # 都没有时回退原始详情文本
    if not any(b[1] for b in blocks):
        dt = job.get('detail_text', '')
        blocks = [('📄 原始详情', (dt[:2000] if dt else ''))]
    jd_html = T.jd_detail(blocks)

    return T.job_card(
        rank=index + 1,
        title=position,
        score=score,
        meta_html=meta,
        badges_html=badges,
        company_line=company_line,
        dimensions_html=dim_html,
        recommend=recommend,
        skills_html=skills_html,
        actions_html=actions,
        jd_html=jd_html,
    )


def generate_report(jobs, output_path, title="岗位推荐报告", subtitle="", notice=""):
    """生成岗位推荐报告 HTML（统一主题）。返回输出路径。"""
    total = len(jobs)
    scores = [(j.get('match_score', 0) or 0) for j in jobs]
    avg_score = round(sum(scores) / total, 1) if total else 0
    max_score = max(scores) if scores else 0
    high_count = len([s for s in scores if s >= 80])
    mid_count = len([s for s in scores if 65 <= s < 80])
    low_count = len([s for s in scores if s < 65])

    # 平台分布
    platform_counts = {}
    for j in jobs:
        src = j.get('source', '其他')
        platform_counts[src] = platform_counts.get(src, 0) + 1

    # 统计卡
    stat_list = [
        (total, '岗位总数'),
        (avg_score, '平均匹配'),
        (max_score, '最高匹配'),
        (high_count, '高度匹配(≥80)', '#52c41a'),
        (mid_count, '较匹配(65-79)', '#faad14'),
        (low_count, '匹配较低(<65)', '#ff7875'),
    ]
    for pname, pcnt in platform_counts.items():
        if pcnt > 0:
            bg, fg = T.SOURCE_STYLE.get(pname, ('#f0f0f0', '#666'))
            stat_list.append((pcnt, pname, fg))
    stats_html = T.stat_grid(stat_list)

    # 筛选栏（岗位场景：高匹配 + 本科可投）
    filter_html = T.filter_bar(soe=False, campus=False, high=True, bachelor=True)

    # 岗位卡片（已按匹配度排序的前提下）
    cards = ''.join(generate_job_card_html(j, i) for i, j in enumerate(jobs)) or \
        '<div class="section-desc">暂无已评估岗位</div>'

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    sub = subtitle or f'共{total}个岗位，按匹配度排序'
    notice_html = f'<div class="notice">{T.esc(notice)}</div>' if notice else ''

    body = (
        stats_html
        + filter_html
        + notice_html
        + T.section_title(f'📋 岗位推荐列表（按匹配度排序）')
        + f'<div class="section-desc">生成时间：{today} · 共 {total} 个岗位</div>'
        + f'<div id="job-list">{cards}</div>'
    )

    html = T.page(title, sub, body, extra_js=T.FILTER_JS)

    _d = os.path.dirname(output_path)
    if _d:
        os.makedirs(_d, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"报告已生成: {output_path}")
    print(f"岗位总数: {total} | 平均: {avg_score} | 最高: {max_score} | ≥80: {high_count}")
    print("平台分布: " + ", ".join(f"{k}:{v}" for k, v in platform_counts.items()))
    return output_path


def generate_match_report(job, match_result, output_path):
    """单个岗位的匹配度报告（保持原接口）。"""
    job_with_match = dict(job)
    job_with_match['match_score'] = match_result.get('match_score', 0)
    job_with_match['match_detail'] = match_result
    return generate_report(
        [job_with_match],
        output_path,
        title=f"匹配度报告 - {job.get('company', '')} {job.get('position', '')}",
        subtitle="单个岗位匹配度详细评估"
    )


if __name__ == '__main__':
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    jobs_path = os.path.join(workspace_dir, 'jobs.json')
    if os.path.exists(jobs_path):
        import json
        with open(jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        jobs.sort(key=lambda x: x.get('match_score', 0) or 0, reverse=True)
        generate_report(
            jobs,
            os.path.join(workspace_dir, 'applications', '岗位推荐报告_统一主题.html'),
            title="岗位推荐报告",
            subtitle=f"共{len(jobs)}个岗位，按匹配度排序"
        )
    else:
        print(f"岗位库文件不存在: {jobs_path}")
