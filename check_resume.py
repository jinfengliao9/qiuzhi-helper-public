#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历格式自动检查工具（check_resume）
对简历数据进行多维度检查，生成检查报告。

用法:
    python check_resume.py [简历数据文件] [--jd JD文本文件]
    python check_resume.py --jd job_description.txt

检查维度:
    1. 个人信息完整性
    2. 教育背景
    3. 实习/工作经历
    4. 项目经历
    5. 技能清单
    6. 时间线（矛盾/重叠/倒序）
    7. 错别字与表述
    8. 量化成果
    9. STAR法则
    10. JD关键词覆盖（可选）
    11. 页数估算
    12. 排版建议
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


def load_resume_data(path):
    """加载简历数据"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str):
    """解析日期字符串，返回 (year, month) 或 None"""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # 匹配 YYYY.MM 或 YYYY-MM 或 YYYY/MM
    m = re.match(r'(\d{4})[.\-/](\d{1,2})', date_str)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    # 匹配 YYYY
    m = re.match(r'(\d{4})', date_str)
    if m:
        return (int(m.group(1)), 0)
    return None


def date_to_float(date_tuple):
    """将 (year, month) 转为浮点数用于比较"""
    if not date_tuple:
        return 0
    return date_tuple[0] + date_tuple[1] / 12.0


def check_personal_info(data):
    """检查个人信息完整性"""
    issues = []
    warnings = []
    passed = []
    basic = data.get('基本信息', {})

    # 姓名
    name = basic.get('name', '')
    if not name:
        issues.append('缺少姓名')
    else:
        passed.append(f'姓名：{name}')

    # 电话
    phone = basic.get('phone', '')
    if not phone:
        issues.append('缺少联系电话')
    elif not re.match(r'^1[3-9]\d{9}$', str(phone).replace(' ', '').replace('-', '')):
        warnings.append(f'电话格式可能不正确：{phone}（应为11位手机号）')
    else:
        passed.append('电话格式正确')

    # 邮箱
    email = basic.get('email', '')
    if not email:
        issues.append('缺少邮箱')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(email)):
        warnings.append(f'邮箱格式可能不正确：{email}')
    else:
        passed.append('邮箱格式正确')

    # 求职意向
    job = basic.get('job_intention', '')
    if not job:
        issues.append('缺少求职意向')
    else:
        passed.append(f'求职意向：{job}')

    # 城市
    city = basic.get('city', '')
    if not city:
        warnings.append('缺少所在城市（建议填写，部分HR会筛选）')
    else:
        passed.append(f'所在城市：{city}')

    # 头像
    avatar = basic.get('avatar', '')
    if not avatar:
        warnings.append('未设置头像（建议添加证件照，提升简历专业度）')
    else:
        passed.append('已设置头像')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_education(data):
    """检查教育背景"""
    issues = []
    warnings = []
    passed = []
    education = data.get('教育背景', [])

    if not education:
        issues.append('缺少教育背景')
        return {'issues': issues, 'warnings': warnings, 'passed': passed}

    for i, edu in enumerate(education):
        prefix = f'教育经历{i+1}'
        school = edu.get('school', '')
        major = edu.get('major', '')
        degree = edu.get('degree', '')
        start = edu.get('start_date', '')
        end = edu.get('end_date', '')

        if not school:
            issues.append(f'{prefix}：缺少学校名称')
        if not major:
            issues.append(f'{prefix}：缺少专业')
        if not degree:
            warnings.append(f'{prefix}：缺少学历（建议填写本科/硕士等）')
        if not start or not end:
            issues.append(f'{prefix}：缺少入学或毕业时间')
        else:
            # 检查时间逻辑
            start_d = parse_date(start)
            end_d = parse_date(end)
            if start_d and end_d:
                if date_to_float(start_d) > date_to_float(end_d):
                    issues.append(f'{prefix}：入学时间晚于毕业时间（{start} - {end}）')
                else:
                    passed.append(f'{prefix}：{school} {major}（{start}-{end}）时间合理')

        # 检查GPA（可选）
        gpa = edu.get('gpa', '')
        if gpa:
            try:
                gpa_val = float(gpa)
                if gpa_val > 0 and gpa_val <= 4:
                    passed.append(f'{prefix}：GPA {gpa}（建议保留，如果GPA较高）')
                elif gpa_val > 4 and gpa_val <= 5:
                    passed.append(f'{prefix}：GPA {gpa}（5分制）')
                else:
                    warnings.append(f'{prefix}：GPA {gpa} 格式可能不正确')
            except:
                warnings.append(f'{prefix}：GPA {gpa} 格式可能不正确')

        # 检查课程
        courses = edu.get('courses', '')
        if not courses:
            warnings.append(f'{prefix}：未填写主修课程（建议填写与岗位相关的课程）')
        else:
            course_count = len([c for c in re.split(r'[、,，]', courses) if c.strip()])
            if course_count < 3:
                warnings.append(f'{prefix}：主修课程较少（建议填写5-8门核心课程）')
            else:
                passed.append(f'{prefix}：主修课程{course_count}门')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_experience(data):
    """检查实习/工作经历"""
    issues = []
    warnings = []
    passed = []
    experience = data.get('实习经历', [])

    if not experience:
        warnings.append('暂无实习/工作经历（应届生可以理解，但建议补充实训/项目经历）')
        return {'issues': issues, 'warnings': warnings, 'passed': passed}

    for i, exp in enumerate(experience):
        prefix = f'实习经历{i+1}'
        company = exp.get('company', '')
        position = exp.get('position', '')
        start = exp.get('start_date', '')
        end = exp.get('end_date', '')
        description = exp.get('description', [])

        if not company:
            issues.append(f'{prefix}：缺少公司名称')
        if not position:
            issues.append(f'{prefix}：缺少岗位名称')
        if not start or not end:
            issues.append(f'{prefix}：缺少开始或结束时间')
        else:
            start_d = parse_date(start)
            end_d = parse_date(end)
            if start_d and end_d and end != '至今':
                if date_to_float(start_d) > date_to_float(end_d):
                    issues.append(f'{prefix}：开始时间晚于结束时间（{start} - {end}）')

        # 检查描述
        if not description or len(description) == 0:
            issues.append(f'{prefix}：缺少工作描述')
        else:
            total_len = sum(len(str(d)) for d in description)
            if total_len < 50:
                warnings.append(f'{prefix}：工作描述过短（共{total_len}字，建议每段经历至少100字）')
            else:
                passed.append(f'{prefix}：工作描述{len(description)}条，共{total_len}字')

            # 检查量化成果
            has_number = False
            for d in description:
                if re.search(r'\d+', str(d)):
                    has_number = True
                    break
            if not has_number:
                warnings.append(f'{prefix}：工作描述中没有量化数据（建议加入数字，如"完成XX宗地测量""效率提升XX%"）')
            else:
                passed.append(f'{prefix}：包含量化数据')

            # 检查STAR法则（简单检查是否有行动和结果）
            has_action = any(('负责' in str(d) or '参与' in str(d) or '完成' in str(d) or '开发' in str(d) or '制作' in str(d)) for d in description)
            has_result = any(('提升' in str(d) or '确保' in str(d) or '通过' in str(d) or '实现' in str(d) or '完成' in str(d)) for d in description)
            if not has_action or not has_result:
                warnings.append(f'{prefix}：描述可能不符合STAR法则（建议包含：背景-任务-行动-结果）')
            else:
                passed.append(f'{prefix}：描述符合STAR法则')

    # 检查时间倒序（最新的在最前面）
    dates = []
    for exp in experience:
        start_d = parse_date(exp.get('start_date', ''))
        if start_d:
            dates.append(date_to_float(start_d))
    if len(dates) >= 2:
        if dates != sorted(dates, reverse=True):
            warnings.append('实习经历未按时间倒序排列（建议最新的经历放在最前面）')
        else:
            passed.append('实习经历按时间倒序排列')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_projects(data):
    """检查项目经历"""
    issues = []
    warnings = []
    passed = []
    projects = data.get('项目经历', [])

    if not projects:
        warnings.append('暂无项目经历（建议补充课程设计、实训项目等）')
        return {'issues': issues, 'warnings': warnings, 'passed': passed}

    for i, proj in enumerate(projects):
        prefix = f'项目经历{i+1}'
        name = proj.get('name', '')
        role = proj.get('role', '')
        start = proj.get('start_date', '')
        end = proj.get('end_date', '')
        description = proj.get('description', [])

        if not name:
            issues.append(f'{prefix}：缺少项目名称')
        if not role:
            warnings.append(f'{prefix}：缺少项目角色（建议填写，如"核心成员""项目负责人"）')
        if not start or not end:
            warnings.append(f'{prefix}：缺少项目时间')

        if not description or len(description) == 0:
            issues.append(f'{prefix}：缺少项目描述')
        else:
            total_len = sum(len(str(d)) for d in description)
            if total_len < 50:
                warnings.append(f'{prefix}：项目描述过短（共{total_len}字）')
            else:
                passed.append(f'{prefix}：项目描述{len(description)}条，共{total_len}字')

            # 检查量化成果
            has_number = any(re.search(r'\d+', str(d)) for d in description)
            if not has_number:
                warnings.append(f'{prefix}：项目描述中没有量化数据')
            else:
                passed.append(f'{prefix}：包含量化数据')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_skills(data):
    """检查技能清单"""
    issues = []
    warnings = []
    passed = []
    skills = data.get('技能清单', {})

    if not skills:
        issues.append('缺少技能清单')
        return {'issues': issues, 'warnings': warnings, 'passed': passed}

    all_skills = []
    if isinstance(skills, dict):
        for category, skill_list in skills.items():
            if not category:
                warnings.append('存在空的技能分类')
            if not skill_list or len(skill_list) == 0:
                warnings.append(f'分类"{category}"下没有技能')
            else:
                for s in skill_list:
                    all_skills.append(str(s))
                passed.append(f'{category}：{len(skill_list)}项')
    elif isinstance(skills, list):
        all_skills = [str(s) for s in skills]
        passed.append(f'技能清单：{len(all_skills)}项')
    else:
        warnings.append('技能清单格式不正确（应为字典或列表）')

    # 技能数量
    if len(all_skills) == 0:
        issues.append('技能清单为空')
    elif len(all_skills) < 3:
        warnings.append(f'技能数量较少（仅{len(all_skills)}项，建议5-15项）')
    elif len(all_skills) > 20:
        warnings.append(f'技能数量过多（{len(all_skills)}项，建议精简到15项以内，突出核心技能）')
    else:
        passed.append(f'技能数量合理（{len(all_skills)}项）')

    # 检查过于笼统的技能
    vague_skills = ['熟练', '精通', '了解', '一般', '会用', '电脑', '办公软件']
    for s in all_skills:
        if s in vague_skills or len(str(s)) < 2:
            warnings.append(f'技能"{s}"过于笼统（建议具体到软件/工具/技术名称）')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_timeline(data):
    """检查时间线（教育、实习、项目之间的重叠和矛盾）"""
    issues = []
    warnings = []
    passed = []

    all_periods = []

    # 教育经历
    for i, edu in enumerate(data.get('教育背景', [])):
        start = parse_date(edu.get('start_date', ''))
        end = parse_date(edu.get('end_date', ''))
        if start and end:
            all_periods.append({
                'type': '教育',
                'name': edu.get('school', ''),
                'start': date_to_float(start),
                'end': date_to_float(end) if edu.get('end_date') != '至今' else 9999
            })

    # 实习经历
    for i, exp in enumerate(data.get('实习经历', [])):
        start = parse_date(exp.get('start_date', ''))
        end = parse_date(exp.get('end_date', ''))
        if start and end:
            all_periods.append({
                'type': '实习',
                'name': exp.get('company', ''),
                'start': date_to_float(start),
                'end': date_to_float(end) if exp.get('end_date') != '至今' else 9999
            })

    # 检查实习与教育的重叠（正常，在校生实习）
    # 检查实习之间的重叠
    internships = [p for p in all_periods if p['type'] == '实习']
    for i in range(len(internships)):
        for j in range(i+1, len(internships)):
            a, b = internships[i], internships[j]
            if a['start'] < b['end'] and b['start'] < a['end']:
                warnings.append(f'实习经历时间重叠：{a["name"]} 与 {b["name"]}（如果是兼职/远程同时进行可以忽略，否则建议核实）')

    if len(all_periods) > 0:
        passed.append(f'共{len(all_periods)}段经历时间线已检查')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_typos(data):
    """检查错别字和表述问题"""
    issues = []
    warnings = []
    passed = []

    # 常见错别字对（测绘专业常见）
    typo_pairs = [
        ('测量', '侧量'),
        ('测绘', '侧绘'),
        ('地籍', '地藉'),
        ('权属', '权署'),
        ('高程', '高成'),
        ('误差', '误查'),
        ('坐标', '坐票'),
        ('比例尺', '比例迟'),
        ('等高线', '等高现'),
        ('全站仪', '全站义'),
        ('经纬仪', '经纬义'),
        ('水准仪', '水准义'),
        ('RTK', 'rtk'),
        ('GIS', 'gis'),
        ('GPS', 'gps'),
        ('DEM', 'dem'),
        ('DOM', 'dom'),
        ('DLG', 'dlg'),
    ]

    # 收集所有文本
    all_text = json.dumps(data, ensure_ascii=False)

    # 检查错别字
    for correct, wrong in typo_pairs:
        if wrong in all_text:
            warnings.append(f'可能存在错别字："{wrong}"，建议改为"{correct}"')

    # 检查重复字（如"的的"、"了了"）
    repeat_patterns = [r'的的', r'了了', r'是是', r'在在', r'和和', r'与与']
    for pattern in repeat_patterns:
        if re.search(pattern, all_text):
            warnings.append(f'可能存在重复字："{pattern}"')

    # 检查英文缩写大小写（简单检查）
    # 检查手机号是否有多余空格
    basic = data.get('基本信息', {})
    phone = str(basic.get('phone', ''))
    if phone and (' ' in phone or '-' in phone):
        warnings.append(f'电话号码包含空格或横线：{phone}（建议纯数字11位）')

    if not warnings and not issues:
        passed.append('未发现明显错别字和表述问题')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_quantification(data):
    """检查量化成果（整体）"""
    issues = []
    warnings = []
    passed = []

    all_descriptions = []
    for exp in data.get('实习经历', []):
        all_descriptions.extend(exp.get('description', []))
    for proj in data.get('项目经历', []):
        all_descriptions.extend(proj.get('description', []))

    if not all_descriptions:
        warnings.append('没有经历描述，无法检查量化成果')
        return {'issues': issues, 'warnings': warnings, 'passed': passed}

    quantified = 0
    for d in all_descriptions:
        if re.search(r'\d+', str(d)):
            quantified += 1

    ratio = quantified / len(all_descriptions) * 100
    if ratio < 30:
        warnings.append(f'量化成果比例偏低：仅{quantified}/{len(all_descriptions)}条描述包含数字（{ratio:.0f}%），建议至少50%的描述包含量化数据')
    elif ratio >= 50:
        passed.append(f'量化成果比例良好：{quantified}/{len(all_descriptions)}条描述包含数字（{ratio:.0f}%）')
    else:
        passed.append(f'量化成果比例一般：{quantified}/{len(all_descriptions)}条描述包含数字（{ratio:.0f}%），建议提升到50%以上')

    return {'issues': issues, 'warnings': warnings, 'passed': passed}


def check_jd_keywords(data, jd_text):
    """检查JD关键词覆盖度"""
    if not jd_text:
        return None

    # 技能关键词库
    skill_keywords = [
        'ArcGIS', 'ArcGIS Pro', 'ArcMap', 'QGIS', 'MapGIS', 'SuperMap',
        'AutoCAD', 'CASS', '南方CASS', 'ENVI', 'ERDAS', 'PCI',
        'Python', 'R', 'MATLAB', 'SQL', 'MySQL', 'PostgreSQL', 'PostGIS',
        'JavaScript', 'HTML', 'CSS', 'Vue', 'React', 'Java', 'C#', 'C++',
        'RTK', '全站仪', 'GPS', 'GNSS', '水准仪', '经纬仪', '无人机', '倾斜摄影',
        '遥感', '摄影测量', '激光雷达', 'LiDAR', 'InSAR',
        '土地调查', '地籍调查', '不动产登记', '国土空间规划', '土地整治',
        '测绘工程', '地理信息', 'GIS', 'RS', '3S',
        '数据处理', '空间分析', '地图制图', '数据库',
        'BIM', 'Revit', 'Navisworks',
        '深度学习', '机器学习', '人工智能', 'AI',
        '地形测量', '工程测量', '控制测量', '变形监测', '施工放样',
        'DEM', 'DOM', 'DLG', 'DRG',
    ]

    # 从JD提取技能关键词
    jd_skills = []
    for skill in skill_keywords:
        if re.search(re.escape(skill), jd_text, re.IGNORECASE):
            if skill not in jd_skills:
                jd_skills.append(skill)

    if not jd_skills:
        return {'jd_skills': [], 'matched': [], 'missing': [], 'coverage': 0, 'note': '未从JD中识别到明确的技能关键词'}

    # 收集简历中的所有技能文本
    resume_text = json.dumps(data, ensure_ascii=False).lower()
    # 加上经历描述
    for exp in data.get('实习经历', []):
        resume_text += ' ' + ' '.join(exp.get('description', [])).lower()
    for proj in data.get('项目经历', []):
        resume_text += ' ' + ' '.join(proj.get('description', [])).lower()

    matched = []
    missing = []
    for skill in jd_skills:
        if skill.lower() in resume_text:
            matched.append(skill)
        else:
            missing.append(skill)

    coverage = int(len(matched) / len(jd_skills) * 100) if jd_skills else 0

    return {
        'jd_skills': jd_skills,
        'matched': matched,
        'missing': missing,
        'coverage': coverage,
        'note': ''
    }


def estimate_pages(data):
    """估算简历页数"""
    # 估算内容量
    total_chars = 0
    basic = data.get('基本信息', {})
    total_chars += len(str(basic.get('name', '')))
    total_chars += len(str(basic.get('phone', '')))
    total_chars += len(str(basic.get('email', '')))
    total_chars += len(str(basic.get('job_intention', '')))

    for edu in data.get('教育背景', []):
        total_chars += len(str(edu.get('school', '')))
        total_chars += len(str(edu.get('major', '')))
        total_chars += len(str(edu.get('courses', '')))
        for d in edu.get('description', []):
            total_chars += len(str(d))

    for exp in data.get('实习经历', []):
        total_chars += len(str(exp.get('company', '')))
        total_chars += len(str(exp.get('position', '')))
        for d in exp.get('description', []):
            total_chars += len(str(d))

    for proj in data.get('项目经历', []):
        total_chars += len(str(proj.get('name', '')))
        total_chars += len(str(proj.get('role', '')))
        for d in proj.get('description', []):
            total_chars += len(str(d))

    skills = data.get('技能清单', {})
    if isinstance(skills, dict):
        for skill_list in skills.values():
            total_chars += sum(len(str(s)) for s in skill_list)

    for item in data.get('自我评价', []):
        total_chars += len(str(item))

    # 估算：A4纸一页大约能放800-1200字（含标题、留白）
    # 双栏模板可以放更多
    estimated_chars_per_page = 1000
    estimated_pages = total_chars / estimated_chars_per_page

    if estimated_pages <= 1:
        level = 'good'
        message = f'内容量约{total_chars}字，预计1页以内（应届生建议1页，符合要求）'
    elif estimated_pages <= 1.3:
        level = 'warning'
        message = f'内容量约{total_chars}字，预计{estimated_pages:.1f}页，可能接近或略超1页（建议精简，应届生尽量控制在1页）'
    else:
        level = 'issue'
        message = f'内容量约{total_chars}字，预计{estimated_pages:.1f}页，超过1页（应届生强烈建议控制在1页，需要精简内容）'

    return {'pages': estimated_pages, 'chars': total_chars, 'level': level, 'message': message}


def generate_report(data, check_results, jd_result, page_result, output_path):
    """生成HTML格式的检查报告"""
    basic = data.get('基本信息', {})
    name = basic.get('name', '候选人')

    # 统计
    total_issues = sum(len(r['issues']) for r in check_results.values())
    total_warnings = sum(len(r['warnings']) for r in check_results.values())
    total_passed = sum(len(r['passed']) for r in check_results.values())

    # 评分
    score = 100
    score -= total_issues * 5
    score -= total_warnings * 2
    score = max(score, 0)

    if score >= 90:
        score_color = '#27ae60'
        score_level = '优秀'
    elif score >= 75:
        score_color = '#2980b9'
        score_level = '良好'
    elif score >= 60:
        score_color = '#f39c12'
        score_level = '一般'
    else:
        score_color = '#e74c3c'
        score_level = '需改进'

    # 生成各检查项的HTML
    sections_html = ''
    section_names = {
        'personal': '个人信息',
        'education': '教育背景',
        'experience': '实习经历',
        'projects': '项目经历',
        'skills': '技能清单',
        'timeline': '时间线',
        'typos': '错别字与表述',
        'quantification': '量化成果',
    }

    for key, section_name in section_names.items():
        result = check_results.get(key, {'issues': [], 'warnings': [], 'passed': []})
        issues_html = ''.join(f'<li class="issue">❌ {escape(i)}</li>' for i in result['issues'])
        warnings_html = ''.join(f'<li class="warning">⚠️ {escape(w)}</li>' for w in result['warnings'])
        passed_html = ''.join(f'<li class="pass">✅ {escape(p)}</li>' for p in result['passed'])

        if not issues_html:
            issues_html = '<li class="text-muted">无</li>'
        if not warnings_html:
            warnings_html = '<li class="text-muted">无</li>'
        if not passed_html:
            passed_html = '<li class="text-muted">无</li>'

        sections_html += f'''
        <div class="check-section">
            <h3>{section_name}</h3>
            <div class="check-grid">
                <div class="check-col issues">
                    <h4>❌ 问题（{len(result["issues"])}）</h4>
                    <ul>{issues_html}</ul>
                </div>
                <div class="check-col warnings">
                    <h4>⚠️ 警告（{len(result["warnings"])}）</h4>
                    <ul>{warnings_html}</ul>
                </div>
                <div class="check-col passed">
                    <h4>✅ 通过（{len(result["passed"])}）</h4>
                    <ul>{passed_html}</ul>
                </div>
            </div>
        </div>'''

    # JD关键词覆盖
    jd_html = ''
    if jd_result:
        matched_tags = ''.join(f'<span class="skill-tag matched">{escape(s)}</span>' for s in jd_result['matched'])
        missing_tags = ''.join(f'<span class="skill-tag missing">{escape(s)}</span>' for s in jd_result['missing'])
        if not matched_tags:
            matched_tags = '<span class="text-muted">无</span>'
        if not missing_tags:
            missing_tags = '<span class="text-muted">无</span>'

        jd_html = f'''
        <div class="check-section">
            <h3>JD关键词覆盖度</h3>
            <div class="jd-score">
                <div class="jd-circle" style="background: conic-gradient({ '#27ae60' if jd_result['coverage'] >= 70 else '#f39c12' if jd_result['coverage'] >= 40 else '#e74c3c'} {jd_result['coverage']*3.6}deg, #e0e0e0 0)">
                    <div class="jd-circle-inner">
                        <div class="jd-number">{jd_result['coverage']}%</div>
                        <div class="jd-label">覆盖度</div>
                    </div>
                </div>
                <div class="jd-detail">
                    <p><strong>JD识别到技能：</strong>{len(jd_result['jd_skills'])}项</p>
                    <p><strong>已覆盖：</strong>{len(jd_result['matched'])}项</p>
                    <p><strong>缺失：</strong>{len(jd_result['missing'])}项</p>
                    {f'<p class="text-muted">{escape(jd_result["note"])}</p>' if jd_result.get('note') else ''}
                </div>
            </div>
            <div style="margin-top:15px">
                <p style="font-size:13px;color:#666;margin-bottom:8px">✅ 已覆盖的关键词：</p>
                <div class="skill-tags">{matched_tags}</div>
                <p style="font-size:13px;color:#666;margin:15px 0 8px">❌ 缺失的关键词（建议在简历中补充）：</p>
                <div class="skill-tags">{missing_tags}</div>
            </div>
        </div>'''

    # 页数估算
    page_level_color = {'good': '#27ae60', 'warning': '#f39c12', 'issue': '#e74c3c'}
    page_html = f'''
    <div class="check-section">
        <h3>页数估算</h3>
        <div class="page-estimate" style="border-left:4px solid {page_level_color.get(page_result['level'], '#999')};padding:15px;background:#f9f9f9;border-radius:0 8px 8px 0">
            <p style="font-size:15px;color:#333"><strong>{escape(page_result['message'])}</strong></p>
            <p style="font-size:13px;color:#666;margin-top:8px">总字符数：约{page_result['chars']}字 | 预计页数：{page_result['pages']:.1f}页</p>
        </div>
    </div>'''

    # 综合建议
    suggestions = []
    if total_issues > 0:
        suggestions.append(f'有 {total_issues} 个必须修复的问题，建议优先处理')
    if total_warnings > 0:
        suggestions.append(f'有 {total_warnings} 个警告项，建议根据情况优化')
    if page_result['level'] != 'good':
        suggestions.append('简历页数可能超过1页，建议精简内容')
    if jd_result and jd_result['coverage'] < 70:
        suggestions.append(f'JD关键词覆盖度仅{jd_result["coverage"]}%，建议在简历中补充缺失的关键词')
    if not suggestions:
        suggestions.append('简历整体质量良好，继续保持！')

    suggestions_html = ''.join(f'<li>{escape(s)}</li>' for s in suggestions)

    report_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>简历格式检查报告 - {escape(name)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 30px; color: #333; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #e74c3c); color: white; padding: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        .score-section {{ display: flex; align-items: center; gap: 30px; padding: 30px; border-bottom: 1px solid #eee; }}
        .score-circle {{ width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({score_color} {score*3.6}deg, #e0e0e0 0); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
        .score-circle-inner {{ width: 90px; height: 90px; border-radius: 50%; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .score-number {{ font-size: 28px; font-weight: bold; color: {score_color}; }}
        .score-label {{ font-size: 12px; color: #999; }}
        .score-detail {{ flex: 1; }}
        .score-detail h2 {{ font-size: 20px; color: {score_color}; margin-bottom: 8px; }}
        .score-stats {{ display: flex; gap: 20px; margin-top: 10px; }}
        .stat-item {{ text-align: center; }}
        .stat-item .num {{ font-size: 24px; font-weight: bold; }}
        .stat-item .num.issue {{ color: #e74c3c; }}
        .stat-item .num.warning {{ color: #f39c12; }}
        .stat-item .num.pass {{ color: #27ae60; }}
        .stat-item .label {{ font-size: 12px; color: #999; }}
        .content {{ padding: 30px; }}
        .check-section {{ margin-bottom: 25px; padding-bottom: 20px; border-bottom: 1px solid #eee; }}
        .check-section:last-child {{ border-bottom: none; }}
        .check-section h3 {{ font-size: 16px; color: #2c3e50; margin-bottom: 15px; padding-left: 10px; border-left: 4px solid #e74c3c; }}
        .check-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }}
        .check-col {{ background: #f9f9f9; border-radius: 8px; padding: 15px; }}
        .check-col h4 {{ font-size: 14px; margin-bottom: 10px; }}
        .check-col ul {{ list-style: none; padding: 0; }}
        .check-col li {{ font-size: 12px; line-height: 1.6; margin-bottom: 6px; padding: 4px 8px; border-radius: 4px; }}
        .check-col li.issue {{ background: #ffebee; color: #c62828; }}
        .check-col li.warning {{ background: #fff8e1; color: #e65100; }}
        .check-col li.pass {{ background: #e8f5e9; color: #2e7d32; }}
        .text-muted {{ color: #999 !important; background: transparent !important; }}
        .jd-score {{ display: flex; align-items: center; gap: 25px; }}
        .jd-circle {{ width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
        .jd-circle-inner {{ width: 75px; height: 75px; border-radius: 50%; background: white; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .jd-number {{ font-size: 22px; font-weight: bold; }}
        .jd-label {{ font-size: 11px; color: #999; }}
        .jd-detail {{ flex: 1; font-size: 13px; line-height: 1.8; color: #555; }}
        .skill-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
        .skill-tag {{ padding: 3px 10px; border-radius: 12px; font-size: 12px; }}
        .skill-tag.matched {{ background: #e8f5e9; color: #27ae60; }}
        .skill-tag.missing {{ background: #ffebee; color: #e74c3c; }}
        .suggestions {{ background: #f0f7ff; border-left: 4px solid #2980b9; padding: 20px; border-radius: 0 8px 8px 0; margin-top: 20px; }}
        .suggestions h3 {{ font-size: 16px; color: #2980b9; margin-bottom: 10px; border-left: none; padding-left: 0; }}
        .suggestions ul {{ padding-left: 20px; font-size: 14px; line-height: 1.8; color: #555; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>简历格式检查报告</h1>
            <div class="meta">候选人：{escape(name)} | 检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 检查维度：8项+JD关键词+页数</div>
        </div>

        <div class="score-section">
            <div class="score-circle">
                <div class="score-circle-inner">
                    <div class="score-number">{score}</div>
                    <div class="score-label">{score_level}</div>
                </div>
            </div>
            <div class="score-detail">
                <h2>简历质量评分：{score}/100（{score_level}）</h2>
                <p style="font-size:14px;color:#666">扣分规则：每个问题扣5分，每个警告扣2分</p>
                <div class="score-stats">
                    <div class="stat-item"><div class="num issue">{total_issues}</div><div class="label">❌ 问题</div></div>
                    <div class="stat-item"><div class="num warning">{total_warnings}</div><div class="label">⚠️ 警告</div></div>
                    <div class="stat-item"><div class="num pass">{total_passed}</div><div class="label">✅ 通过</div></div>
                </div>
            </div>
        </div>

        <div class="content">
            {sections_html}
            {jd_html}
            {page_html}

            <div class="suggestions">
                <h3>📋 综合改进建议</h3>
                <ul>{suggestions_html}</ul>
            </div>
        </div>

        <div class="footer">
            本报告由 job-search-assistant 自动生成，检查结果仅供参考，具体内容请结合实际情况调整。
        </div>
    </div>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    return output_path


def main():
    workspace = os.path.dirname(os.path.abspath(__file__))
    default_data = os.path.join(workspace, 'resume_data.json')
    default_output = os.path.join(workspace, 'cv')

    resume_path = default_data
    jd_path = None
    output_dir = default_output

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--jd' and i + 1 < len(args):
            jd_path = args[i + 1]
            i += 2
        elif args[i].endswith('.json'):
            resume_path = args[i]
            i += 1
        elif os.path.isdir(args[i]):
            output_dir = args[i]
            i += 1
        else:
            i += 1

    if not os.path.exists(resume_path):
        print(f'错误: 简历数据文件不存在: {resume_path}')
        sys.exit(1)

    print('加载简历数据...')
    data = load_resume_data(resume_path)

    # 加载JD（可选）
    jd_text = None
    if jd_path and os.path.exists(jd_path):
        print('加载JD文本...')
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_text = f.read()

    # 执行各项检查
    print('执行检查...')
    check_results = {
        'personal': check_personal_info(data),
        'education': check_education(data),
        'experience': check_experience(data),
        'projects': check_projects(data),
        'skills': check_skills(data),
        'timeline': check_timeline(data),
        'typos': check_typos(data),
        'quantification': check_quantification(data),
    }

    # JD关键词检查
    jd_result = None
    if jd_text:
        print('检查JD关键词覆盖度...')
        jd_result = check_jd_keywords(data, jd_text)

    # 页数估算
    print('估算页数...')
    page_result = estimate_pages(data)

    # 统计
    total_issues = sum(len(r['issues']) for r in check_results.values())
    total_warnings = sum(len(r['warnings']) for r in check_results.values())
    total_passed = sum(len(r['passed']) for r in check_results.values())

    print()
    print('='*50)
    print('检查完成！')
    print(f'  ❌ 问题：{total_issues} 个')
    print(f'  ⚠️ 警告：{total_warnings} 个')
    print(f'  ✅ 通过：{total_passed} 项')
    print(f'  📄 预计页数：{page_result["pages"]:.1f}页')
    if jd_result:
        print(f'  🎯 JD关键词覆盖度：{jd_result["coverage"]}%')
    print('='*50)

    # 生成报告
    os.makedirs(output_dir, exist_ok=True)
    name = data.get('基本信息', {}).get('name', '简历')
    output_path = os.path.join(output_dir, f'{name}_简历检查报告.html')
    generate_report(data, check_results, jd_result, page_result, output_path)
    print(f'\n报告已生成: {output_path}')
    print('\n使用方法:')
    print('  python check_resume.py                    # 基础检查')
    print('  python check_resume.py --jd job.txt       # 含JD关键词覆盖检查')


if __name__ == '__main__':
    main()
