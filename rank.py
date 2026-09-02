#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职位匹配评估工具（rank）
输入职位描述（JD），自动与用户简历匹配，输出匹配度评估报告。

用法:
    python rank.py <jd文件路径> [输出目录]
    或: python rank.py --text "JD文本内容" [输出目录]

输出:
    HTML格式的匹配度报告，包含：
    - 职位基本信息解析
    - 4维度匹配评分（技术/经验/行为/硬约束）
    - 匹配亮点
    - 存在的gap
    - 投递建议
"""

import json
import sys
import os
import re
import html as html_module
from datetime import datetime


def escape(text):
    if not text:
        return ''
    return html_module.escape(str(text))


def load_resume_data(workspace):
    """加载用户简历数据"""
    data_path = os.path.join(workspace, 'resume_data.json')
    if not os.path.exists(data_path):
        print(f'错误: 简历数据文件不存在: {data_path}')
        sys.exit(1)
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_jd(jd_text):
    """解析JD文本，提取关键字段"""
    result = {
        'company': '',
        'position': '',
        'city': '',
        'salary': '',
        'experience': '',
        'education': '',
        'skills_required': [],
        'responsibilities': [],
        'benefits': [],
        'raw_text': jd_text
    }

    lines = [l.strip() for l in jd_text.split('\n') if l.strip()]

    # 常见技能关键词库（测绘/地理信息相关）
    skill_keywords = [
        'ArcGIS', 'ArcGIS Pro', 'ArcMap', 'QGIS', 'MapGIS', 'SuperMap',
        'AutoCAD', 'CASS', '南方CASS', 'ENVI', 'ERDAS', 'PCI',
        'Python', 'R', 'MATLAB', 'SQL', 'MySQL', 'PostgreSQL', 'PostGIS',
        'JavaScript', 'HTML', 'CSS', 'Vue', 'React', 'Java', 'C#', 'C++',
        'RTK', '全站仪', 'GPS', 'GNSS', '水准仪', '经纬仪', '无人机', '倾斜摄影',
        '遥感', '摄影测量', '激光雷达', 'LiDAR', 'InSAR',
        '土地调查', '地籍调查', '不动产登记', '国土空间规划', '土地整治',
        '测绘工程', '地理信息', 'GIS', 'RS', 'GPS', '3S',
        '数据处理', '空间分析', '地图制图', '数据库',
        'BIM', 'Revit', 'Navisworks',
        '深度学习', '机器学习', '人工智能', 'AI',
    ]

    # 提取公司名（常见模式）
    company_patterns = [
        r'公司名称[：:]\s*(.+)',
        r'招聘单位[：:]\s*(.+)',
        r'单位名称[：:]\s*(.+)',
        r'【公司名称】\s*(.+)',
    ]
    for line in lines[:10]:
        for pat in company_patterns:
            m = re.search(pat, line)
            if m:
                result['company'] = m.group(1).strip()
                break
        if result['company']:
            break

    # 提取岗位名
    position_patterns = [
        r'岗位名称[：:]\s*(.+)',
        r'职位名称[：:]\s*(.+)',
        r'招聘岗位[：:]\s*(.+)',
        r'【岗位名称】\s*(.+)',
        r'招聘职位[：:]\s*(.+)',
    ]
    for line in lines[:10]:
        for pat in position_patterns:
            m = re.search(pat, line)
            if m:
                result['position'] = m.group(1).strip()
                break
        if result['position']:
            break

    # 提取薪资
    salary_patterns = [
        r'薪资[：:]\s*(.+)',
        r'薪酬[：:]\s*(.+)',
        r'工资[：:]\s*(.+)',
        r'待遇[：:]\s*(.+)',
        r'(\d+\.?\d*)\s*[-~到]\s*(\d+\.?\d*)\s*[kK千]',
        r'(\d+)\s*[-~到]\s*(\d+)\s*万',
    ]
    for line in lines:
        for pat in salary_patterns:
            m = re.search(pat, line)
            if m:
                if len(m.groups()) == 2:
                    result['salary'] = f'{m.group(1)}-{m.group(2)}K'
                else:
                    result['salary'] = m.group(1).strip()
                break
        if result['salary']:
            break

    # 提取城市
    city_patterns = [
        r'工作地点[：:]\s*(.+)',
        r'工作城市[：:]\s*(.+)',
        r'工作地址[：:]\s*(.+)',
        r'办公地点[：:]\s*(.+)',
        r'地点[：:]\s*(.+)',
    ]
    for line in lines[:15]:
        for pat in city_patterns:
            m = re.search(pat, line)
            if m:
                result['city'] = m.group(1).strip()
                break
        if result['city']:
            break

    # 提取经验要求
    exp_patterns = [
        r'经验要求[：:]\s*(.+)',
        r'工作经验[：:]\s*(.+)',
        r'(\d+)\s*[-~到]\s*(\d+)\s*年',
        r'(\d+)\s*年以上',
        r'应届毕业生',
        r'在校生',
        r'不限经验',
    ]
    for line in lines:
        for pat in exp_patterns:
            m = re.search(pat, line)
            if m:
                if m.group(0):
                    result['experience'] = m.group(0).strip()
                break
        if result['experience']:
            break

    # 提取学历要求
    edu_patterns = [
        r'学历要求[：:]\s*(.+)',
        r'学历[：:]\s*(.+)',
        r'本科及以上',
        r'大专及以上',
        r'硕士及以上',
        r'博士',
        r'本科',
        r'大专',
        r'不限学历',
    ]
    for line in lines:
        for pat in edu_patterns:
            m = re.search(pat, line)
            if m:
                result['education'] = m.group(0).strip()
                break
        if result['education']:
            break

    # 提取技能关键词
    full_text = jd_text
    for skill in skill_keywords:
        if re.search(re.escape(skill), full_text, re.IGNORECASE):
            if skill not in result['skills_required']:
                result['skills_required'].append(skill)

    # 提取岗位职责（常见标题后的内容）
    resp_keywords = ['岗位职责', '工作内容', '职位描述', '岗位描述', '工作职责', '工作职责']
    in_resp = False
    for line in lines:
        if any(k in line for k in resp_keywords):
            in_resp = True
            continue
        if in_resp:
            if re.match(r'^[一二三四五六七八九十\d]+[、.．]', line) or line.startswith('-') or line.startswith('•'):
                result['responsibilities'].append(re.sub(r'^[一二三四五六七八九十\d]+[、.．]\s*', '', line).lstrip('-• '))
            elif len(line) > 5 and not any(k in line for k in ['任职要求', '岗位要求', '任职资格', '技能要求', '福利待遇', '薪资福利']):
                result['responsibilities'].append(line)
            else:
                in_resp = False

    # 提取福利待遇
    benefit_keywords = ['福利待遇', '薪资福利', '福利', '我们提供', '公司福利']
    in_benefit = False
    for line in lines:
        if any(k in line for k in benefit_keywords):
            in_benefit = True
            continue
        if in_benefit:
            if re.match(r'^[一二三四五六七八九十\d]+[、.．]', line) or line.startswith('-') or line.startswith('•'):
                result['benefits'].append(re.sub(r'^[一二三四五六七八九十\d]+[、.．]\s*', '', line).lstrip('-• '))
            elif len(line) > 3:
                result['benefits'].append(line)
            else:
                in_benefit = False

    return result


def evaluate_match(jd_info, resume_data):
    """评估职位匹配度，返回4维度评分和详细分析"""
    basic = resume_data.get('基本信息', {})
    skills = resume_data.get('技能清单', {})
    education = resume_data.get('教育背景', [])
    experience = resume_data.get('实习经历', [])
    projects = resume_data.get('项目经历', [])
    others = resume_data.get('自我评价', [])

    # 收集用户所有技能
    user_skills = []
    if isinstance(skills, dict):
        for skill_list in skills.values():
            user_skills.extend([s.lower() for s in skill_list])

    # ========== 1. 技术匹配 ==========
    required_skills = jd_info.get('skills_required', [])
    matched_skills = []
    missing_skills = []
    for skill in required_skills:
        if skill.lower() in user_skills or any(skill.lower() in s for s in user_skills):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if required_skills:
        tech_score = int(len(matched_skills) / len(required_skills) * 100)
    else:
        tech_score = 70  # 无法判断时给中等分

    # ========== 2. 经验匹配 ==========
    exp_score = 50
    exp_notes = []

    # 检查实习经历
    if experience:
        exp_score += 20
        exp_notes.append(f'有{len(experience)}段实习经历')
    else:
        exp_notes.append('暂无正式实习经历')

    # 检查项目经历
    if projects:
        exp_score += 15
        exp_notes.append(f'有{len(projects)}个项目经历')

    # 检查经验要求
    jd_exp = jd_info.get('experience', '')
    if '应届' in jd_exp or '在校' in jd_exp or '不限' in jd_exp or not jd_exp:
        exp_score += 15
        exp_notes.append('岗位接受应届生/在校生')
    elif '1年' in jd_exp or '2年' in jd_exp:
        exp_score += 5
        exp_notes.append('岗位要求1-2年经验，实习经历可部分弥补')
    else:
        exp_notes.append('岗位经验要求较高，可能存在差距')

    exp_score = min(exp_score, 100)

    # ========== 3. 行为匹配 ==========
    behavior_score = 60
    behavior_notes = []

    # 检查自我评价中的软技能
    all_others = ' '.join(others)
    soft_skills = {
        '出差': ['出差', '外派', '驻场'],
        '加班': ['加班', '抗压', '压力'],
        '团队': ['团队', '协作', '沟通'],
        '学习': ['学习', '快速上手', '适应'],
        '负责': ['负责', '责任心', '认真'],
    }
    for skill, keywords in soft_skills.items():
        if any(k in all_others for k in keywords):
            behavior_score += 8
            behavior_notes.append(f'具备{skill}相关素质')

    behavior_score = min(behavior_score, 100)

    # ========== 4. 硬约束检查 ==========
    hard_score = 100
    hard_issues = []
    hard_passes = []

    # 学历检查
    jd_edu = jd_info.get('education', '')
    user_edu = education[0].get('degree', '') if education else ''
    if jd_edu:
        if '博士' in jd_edu:
            hard_score -= 40
            hard_issues.append(f'岗位要求博士学历，当前为{user_edu}')
        elif '硕士' in jd_edu and '本科' in user_edu:
            hard_score -= 20
            hard_issues.append(f'岗位要求硕士学历，当前为{user_edu}')
        else:
            hard_passes.append(f'学历要求满足（{jd_edu}）')

    # 城市检查（用户偏好可接受出差，所以不严格扣分）
    jd_city = jd_info.get('city', '')
    user_city = basic.get('city', '')
    if jd_city and user_city and jd_city != user_city:
        if '出差' in all_others or '外派' in all_others:
            hard_passes.append(f'工作地点{jd_city}，用户接受出差/外派')
        else:
            hard_score -= 10
            hard_issues.append(f'工作地点{jd_city}，与当前城市{user_city}不同')

    hard_score = max(hard_score, 0)

    # ========== 综合评分 ==========
    weights = {'tech': 0.35, 'exp': 0.30, 'behavior': 0.15, 'hard': 0.20}
    total_score = int(
        tech_score * weights['tech'] +
        exp_score * weights['exp'] +
        behavior_score * weights['behavior'] +
        hard_score * weights['hard']
    )

    # 投递建议
    if total_score >= 80:
        recommendation = '强烈推荐投递'
        rec_color = '#27ae60'
        rec_detail = '匹配度很高，技能和经验都比较对口，建议优先投递。'
    elif total_score >= 65:
        recommendation = '推荐投递'
        rec_color = '#2980b9'
        rec_detail = '匹配度较好，有部分gap但可以通过实习经历和学习能力弥补，建议投递。'
    elif total_score >= 50:
        recommendation = '可以尝试'
        rec_color = '#f39c12'
        rec_detail = '匹配度一般，存在较明显的gap，如果对该岗位很感兴趣可以尝试，但需要在简历中突出相关经历。'
    else:
        recommendation = '不太建议'
        rec_color = '#e74c3c'
        rec_detail = '匹配度较低，硬约束或核心技能差距较大，投递成功率可能不高，建议优先考虑更匹配的岗位。'

    return {
        'total_score': total_score,
        'recommendation': recommendation,
        'rec_color': rec_color,
        'rec_detail': rec_detail,
        'dimensions': {
            'tech': {'score': tech_score, 'matched': matched_skills, 'missing': missing_skills},
            'exp': {'score': exp_score, 'notes': exp_notes},
            'behavior': {'score': behavior_score, 'notes': behavior_notes},
            'hard': {'score': hard_score, 'issues': hard_issues, 'passes': hard_passes},
        }
    }


def generate_report(jd_info, match_result, resume_data, output_path):
    """生成HTML格式的匹配度报告"""
    basic = resume_data.get('基本信息', {})
    name = basic.get('name', '候选人')
    position = jd_info.get('position', '未知岗位')
    company = jd_info.get('company', '未知公司')

    dims = match_result['dimensions']

    # 技能匹配详情
    matched_html = ''.join(f'<span class="skill-tag matched">{escape(s)}</span>' for s in dims['tech']['matched'])
    missing_html = ''.join(f'<span class="skill-tag missing">{escape(s)}</span>' for s in dims['tech']['missing'])
    if not matched_html:
        matched_html = '<span class="text-muted">未识别到明确匹配的技能</span>'
    if not missing_html:
        missing_html = '<span class="text-muted">未识别到明显缺失的技能</span>'

    # 经验笔记
    exp_notes_html = ''.join(f'<li>{escape(n)}</li>' for n in dims['exp']['notes'])

    # 行为笔记
    behavior_notes_html = ''.join(f'<li>{escape(n)}</li>' for n in dims['behavior']['notes'])
    if not behavior_notes_html:
        behavior_notes_html = '<li class="text-muted">未识别到明确的软技能描述</li>'

    # 硬约束
    hard_passes_html = ''.join(f'<li class="pass">✓ {escape(n)}</li>' for n in dims['hard']['passes'])
    hard_issues_html = ''.join(f'<li class="issue">✗ {escape(n)}</li>' for n in dims['hard']['issues'])
    if not hard_passes_html:
        hard_passes_html = '<li class="text-muted">无</li>'
    if not hard_issues_html:
        hard_issues_html = '<li class="text-muted">无</li>'

    # 岗位职责
    resp_html = ''.join(f'<li>{escape(r)}</li>' for r in jd_info.get('responsibilities', []))
    if not resp_html:
        resp_html = '<li class="text-muted">未解析到明确的岗位职责</li>'

    # 福利
    benefit_html = ''.join(f'<li>{escape(b)}</li>' for b in jd_info.get('benefits', []))
    if not benefit_html:
        benefit_html = '<li class="text-muted">未解析到明确的福利待遇</li>'

    report_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>职位匹配评估报告 - {escape(position)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 30px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        .score-section {{ display: flex; align-items: center; gap: 30px; padding: 30px; border-bottom: 1px solid #eee; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({match_result['rec_color']} {match_result['total_score']*3.6}deg, #e0e0e0 0); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
        .score-circle-inner {{ width: 90px; height: 90px; border-radius: 50%; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .score-number {{ font-size: 28px; font-weight: bold; color: {match_result['rec_color']}; }}
        .score-label {{ font-size: 12px; color: #999; }}
        .recommendation {{ flex: 1; }}
        .recommendation h2 {{ font-size: 20px; color: {match_result['rec_color']}; margin-bottom: 8px; }}
        .recommendation p {{ font-size: 14px; color: #666; line-height: 1.6; }}
        .dimensions {{ padding: 30px; }}
        .dimensions h2 {{ font-size: 18px; margin-bottom: 20px; color: #2c3e50; }}
        .dim-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .dim-card {{ border: 1px solid #eee; border-radius: 8px; padding: 20px; }}
        .dim-card h3 {{ font-size: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        .dim-score {{ font-size: 18px; font-weight: bold; }}
        .dim-bar {{ height: 8px; background: #eee; border-radius: 4px; margin-bottom: 12px; overflow: hidden; }}
        .dim-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
        .skill-tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }}
        .skill-tag {{ padding: 3px 10px; border-radius: 12px; font-size: 12px; }}
        .skill-tag.matched {{ background: #e8f5e9; color: #27ae60; }}
        .skill-tag.missing {{ background: #ffebee; color: #e74c3c; }}
        .dim-card ul {{ padding-left: 18px; font-size: 13px; color: #555; line-height: 1.8; }}
        .dim-card ul li.pass {{ color: #27ae60; }}
        .dim-card ul li.issue {{ color: #e74c3c; }}
        .text-muted {{ color: #999; }}
        .jd-info {{ padding: 30px; border-top: 1px solid #eee; background: #fafafa; }}
        .jd-info h2 {{ font-size: 18px; margin-bottom: 15px; color: #2c3e50; }}
        .jd-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }}
        .jd-item {{ font-size: 13px; }}
        .jd-item .label {{ color: #999; margin-right: 8px; }}
        .jd-item .value {{ color: #333; font-weight: 500; }}
        .jd-section {{ margin-bottom: 15px; }}
        .jd-section h3 {{ font-size: 14px; color: #555; margin-bottom: 8px; }}
        .jd-section ul {{ padding-left: 18px; font-size: 13px; color: #666; line-height: 1.7; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>职位匹配评估报告</h1>
            <div class="meta">候选人：{escape(name)} | 岗位：{escape(position)} | 公司：{escape(company)} | 评估时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>

        <div class="score-section">
            <div class="score-circle">
                <div class="score-circle-inner">
                    <div class="score-number">{match_result['total_score']}</div>
                    <div class="score-label">匹配度</div>
                </div>
            </div>
            <div class="recommendation">
                <h2>{match_result['recommendation']}</h2>
                <p>{match_result['rec_detail']}</p>
            </div>
        </div>

        <div class="dimensions">
            <h2>四维度匹配分析</h2>
            <div class="dim-grid">
                <div class="dim-card">
                    <h3>技术匹配 <span class="dim-score" style="color:#2980b9">{dims['tech']['score']}分</span></h3>
                    <div class="dim-bar"><div class="dim-bar-fill" style="width:{dims['tech']['score']}%;background:#2980b9"></div></div>
                    <div style="font-size:12px;color:#999;margin-bottom:4px">已匹配技能：</div>
                    <div class="skill-tags">{matched_html}</div>
                    <div style="font-size:12px;color:#999;margin:10px 0 4px">缺失技能：</div>
                    <div class="skill-tags">{missing_html}</div>
                </div>

                <div class="dim-card">
                    <h3>经验匹配 <span class="dim-score" style="color:#27ae60">{dims['exp']['score']}分</span></h3>
                    <div class="dim-bar"><div class="dim-bar-fill" style="width:{dims['exp']['score']}%;background:#27ae60"></div></div>
                    <ul>{exp_notes_html}</ul>
                </div>

                <div class="dim-card">
                    <h3>行为匹配 <span class="dim-score" style="color:#f39c12">{dims['behavior']['score']}分</span></h3>
                    <div class="dim-bar"><div class="dim-bar-fill" style="width:{dims['behavior']['score']}%;background:#f39c12"></div></div>
                    <ul>{behavior_notes_html}</ul>
                </div>

                <div class="dim-card">
                    <h3>硬约束 <span class="dim-score" style="color:#8e44ad">{dims['hard']['score']}分</span></h3>
                    <div class="dim-bar"><div class="dim-bar-fill" style="width:{dims['hard']['score']}%;background:#8e44ad"></div></div>
                    <ul>{hard_passes_html}{hard_issues_html}</ul>
                </div>
            </div>
        </div>

        <div class="jd-info">
            <h2>职位信息解析</h2>
            <div class="jd-grid">
                <div class="jd-item"><span class="label">公司：</span><span class="value">{escape(jd_info.get('company','未识别'))}</span></div>
                <div class="jd-item"><span class="label">岗位：</span><span class="value">{escape(jd_info.get('position','未识别'))}</span></div>
                <div class="jd-item"><span class="label">城市：</span><span class="value">{escape(jd_info.get('city','未识别'))}</span></div>
                <div class="jd-item"><span class="label">薪资：</span><span class="value">{escape(jd_info.get('salary','未识别'))}</span></div>
                <div class="jd-item"><span class="label">经验：</span><span class="value">{escape(jd_info.get('experience','未识别'))}</span></div>
                <div class="jd-item"><span class="label">学历：</span><span class="value">{escape(jd_info.get('education','未识别'))}</span></div>
            </div>
            <div class="jd-section">
                <h3>岗位职责</h3>
                <ul>{resp_html}</ul>
            </div>
            <div class="jd-section">
                <h3>福利待遇</h3>
                <ul>{benefit_html}</ul>
            </div>
        </div>

        <div class="footer">
            本报告由 job-search-assistant 自动生成，仅供参考，实际投递请结合个人判断。
        </div>
    </div>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    print(f'匹配度报告已生成: {output_path}')


def main():
    workspace = os.path.dirname(os.path.abspath(__file__))

    # 解析参数
    jd_text = None
    jd_file = None
    output_dir = os.path.join(workspace, 'applications')

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--text' and i + 1 < len(args):
            jd_text = args[i + 1]
            i += 2
        elif args[i].endswith('.txt') or args[i].endswith('.md'):
            jd_file = args[i]
            i += 1
        else:
            if os.path.isdir(args[i]):
                output_dir = args[i]
            i += 1

    if not jd_text and not jd_file:
        print('用法:')
        print('  python rank.py <jd文件路径> [输出目录]')
        print('  python rank.py --text "JD文本内容" [输出目录]')
        print()
        print('示例:')
        print('  python rank.py job_description.txt')
        print('  python rank.py --text "公司：XX测绘院 岗位：测绘工程师..."')
        sys.exit(1)

    # 读取JD文本
    if jd_file:
        if not os.path.exists(jd_file):
            print(f'错误: JD文件不存在: {jd_file}')
            sys.exit(1)
        with open(jd_file, 'r', encoding='utf-8') as f:
            jd_text = f.read()

    # 加载简历数据
    print('加载简历数据...')
    resume_data = load_resume_data(workspace)

    # 解析JD
    print('解析职位描述...')
    jd_info = parse_jd(jd_text)
    print(f'  公司: {jd_info.get("company", "未识别")}')
    print(f'  岗位: {jd_info.get("position", "未识别")}')
    print(f'  城市: {jd_info.get("city", "未识别")}')
    print(f'  薪资: {jd_info.get("salary", "未识别")}')
    print(f'  识别到技能要求: {len(jd_info.get("skills_required", []))}项')

    # 评估匹配度
    print('评估匹配度...')
    match_result = evaluate_match(jd_info, resume_data)
    print(f'  综合匹配度: {match_result["total_score"]}分')
    print(f'  技术匹配: {match_result["dimensions"]["tech"]["score"]}分')
    print(f'  经验匹配: {match_result["dimensions"]["exp"]["score"]}分')
    print(f'  行为匹配: {match_result["dimensions"]["behavior"]["score"]}分')
    print(f'  硬约束: {match_result["dimensions"]["hard"]["score"]}分')
    print(f'  投递建议: {match_result["recommendation"]}')

    # 生成报告
    os.makedirs(output_dir, exist_ok=True)
    position = jd_info.get('position', '未知岗位')
    company = jd_info.get('company', '未知公司')
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', f'{company}_{position}')
    output_path = os.path.join(output_dir, f'rank_{safe_name}.html')
    generate_report(jd_info, match_result, resume_data, output_path)

    print()
    print('='*50)
    print('评估完成！')
    print(f'报告路径: {output_path}')
    print('='*50)


if __name__ == '__main__':
    main()
