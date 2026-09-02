#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键生成选中的4个模板简历（HTML + PDF）
从 resume_data.json 数据源生成4个选中模板的HTML，然后用Edge无头模式转PDF。

4个模板：
1. 左右结构（he11x现代双栏）
2. 上下结构（he11x经典单栏）
3. 活泼创意
4. 现代双栏（render_cv_html.py的modern模板）

用法:
    python generate_selected.py [数据文件路径] [输出目录]
"""

import json
import sys
import os
import subprocess
import time
import html as html_module


def escape(text):
    """转义HTML特殊字符"""
    if not text:
        return ''
    return html_module.escape(str(text))


def get_edge_path():
    """获取Edge浏览器路径"""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def html_to_pdf(html_path, pdf_path):
    """用Edge无头模式将HTML转PDF"""
    edge_path = get_edge_path()
    if not edge_path:
        print('  未找到Edge浏览器，跳过PDF')
        return False
    subprocess.run(
        [edge_path, '--headless', '--disable-gpu', '--no-pdf-header-footer',
         f'--print-to-pdf={pdf_path}', html_path],
        capture_output=True, text=True
    )
    time.sleep(2)
    if os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path) / 1024
        print(f'  PDF生成成功 ({size:.1f} KB)')
        return True
    print('  PDF生成失败')
    return False


# ============================================================
# 模板1：左右结构（he11x现代双栏）
# ============================================================
def generate_left_right(data):
    """左右结构模板"""
    name = escape(data.get('name', ''))
    phone = escape(data.get('phone', ''))
    email = escape(data.get('email', ''))
    city = escape(data.get('city', ''))
    job = escape(data.get('job_intention', ''))

    # 技能清单
    skills_html = ''
    skills = data.get('skills', {})
    if isinstance(skills, dict):
        for cat, skill_list in skills.items():
            skills_html += f'''            <div class="info-item"><div class="label">{escape(cat)}</div><div class="text">{escape("、".join(skill_list))}</div></div>\n'''

    # 教育背景
    edu_html = ''
    for edu in data.get('education', []):
        title_parts = [p for p in [edu.get('school', ''), edu.get('major', ''), edu.get('degree', '')] if p]
        title = escape(' · '.join(title_parts))
        date = escape(f'{edu.get("start_date", "")} - {edu.get("end_date", "至今")}')
        major = escape(f'{edu.get("major", "")} | {edu.get("degree", "")}')
        courses = escape(edu.get('courses', ''))
        edu_html += f'''                <div class="item">
                    <div class="education-title">
                        <span class="time">{date}</span>
                        <span class="school">{title}</span>
                    </div>
                    <span class="major">{major}</span>
                    <p>主修课程：{courses}</p>
                </div>\n'''

    # 实习经历
    exp_html = ''
    for exp in data.get('experience', []):
        company = escape(exp.get('company', ''))
        position = escape(exp.get('position', ''))
        date = escape(f'{exp.get("start_date", "")} - {exp.get("end_date", "至今")}')
        city = escape(exp.get('city', ''))
        desc_html = ''.join(f'                        <li>{escape(d)}</li>\n' for d in exp.get('description', []))
        exp_html += f'''                <div class="item">
                    <div class="intern-title">
                        <strong>{company}</strong>
                        <span>（{date} {position}）</span>
                    </div>
                    <p>工作地点：{city}</p>
                    <ul>
{desc_html}                    </ul>
                </div>\n'''

    # 项目经历
    proj_html = ''
    for proj in data.get('projects', []):
        pname = escape(proj.get('name', ''))
        role = escape(proj.get('role', ''))
        date = escape(f'{proj.get("start_date", "")} - {proj.get("end_date", "至今")}')
        desc_html = ''.join(f'                        <li>{escape(d)}</li>\n' for d in proj.get('description', []))
        proj_html += f'''                <div class="item">
                    <div class="project-title">
                        <strong>{pname}</strong>
                        <span>（{date} {role}）</span>
                    </div>
                    <ul>
{desc_html}                    </ul>
                </div>\n'''

    # 自我评价
    eval_html = ''.join(f'                <li>{escape(item)}</li>\n' for item in data.get('others', []))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - {job}简历</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: "Microsoft YaHei", sans-serif; }}
        body {{ background-color: #f5f5f5; padding: 30px 20px; }}
        .resume {{ width: 210mm; min-height: 297mm; margin: 0 auto; background: white; display: flex; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }}
        .left {{ width: 250px; background-color: rgb(235, 238, 251); padding: 35px 20px; border-right: 1px solid #eee; }}
        .avatar {{ width: 150px; height: 200px; margin: 0 auto 20px; background-color: #ddd; display: flex; align-items: center; justify-content: center; color: #666; font-size: 13px; overflow: hidden; }}
        .avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
        .left-title {{ font-size: 16px; color: rgb(46, 81, 219); border-left: 4px solid #3498db; padding-left: 10px; margin-bottom: 12px; }}
        .info-item {{ display: flex; margin-bottom: 8px; font-size: 13px; }}
        .info-item .label {{ width: 60px; font-weight: 500; color: #555; }}
        .info-item .text {{ flex: 1; color: #333; }}
        .right {{ flex: 1; padding: 35px 30px; }}
        .resume-name {{ font-size: 24px; font-weight: bold; color: #2c3e50; text-align: center; padding-bottom: 10px; }}
        .section {{ margin-bottom: 24px; }}
        .section h2 {{ font-size: 16px; color: rgb(46, 81, 219); border-left: 4px solid #3498db; padding-left: 10px; margin-bottom: 12px; }}
        .item {{ margin-bottom: 12px; }}
        .education-title {{ display: flex; flex-direction: row; justify-content: space-between; color: rgb(46, 81, 219); font-size: 14px; }}
        .project-title, .intern-title {{ display: flex; flex-direction: row; justify-content: space-between; margin-bottom: 4px; font-size: 14px; }}
        .item .time {{ font-weight: bold; font-size: 14px; }}
        .item .school {{ font-weight: bold; margin-left: 10px; font-size: 14px; }}
        .item p {{ color: #555; font-size: 13px; margin-bottom: 5px; }}
        .item .major {{ font-size: 13px; }}
        ul {{ padding-left: 20px; color: #333; font-size: 13px; }}
        @page {{ size: A4; margin: 0; }}
        @media print {{ body {{ background-color: white; padding: 0; margin: 0; }} .resume {{ width: 210mm; min-height: 297mm; box-shadow: none; margin: 0; page-break-after: always; }} }}
    </style>
</head>
<body>
    <div class="resume">
        <div class="left">
            <div class="avatar"><img src="avatar.jpg" alt="头像"></div>
            <h2 class="resume-name">{name}</h2>
            <h2 class="left-title">基本信息</h2>
            <div class="info-item"><div class="label">电话</div><div class="text">{phone}</div></div>
            <div class="info-item"><div class="label">邮箱</div><div class="text">{email}</div></div>
            <div class="info-item"><div class="label">城市</div><div class="text">{city}</div></div>
            <div class="info-item"><div class="label">求职意向</div><div class="text">{job}</div></div>
            <h2 class="left-title">技能清单</h2>
{skills_html}        </div>
        <div class="right">
            <div class="section">
                <h2>教育经历</h2>
{edu_html}            </div>
            <div class="section">
                <h2>实习经历</h2>
{exp_html}            </div>
            <div class="section">
                <h2>项目经历</h2>
{proj_html}            </div>
            <div class="section">
                <h2>自我评价</h2>
                <ul>
{eval_html}                </ul>
            </div>
        </div>
    </div>
</body>
</html>'''


# ============================================================
# 模板2：上下结构（he11x经典单栏）
# ============================================================
def generate_top_bottom(data):
    """上下结构模板"""
    name = escape(data.get('name', ''))
    phone = escape(data.get('phone', ''))
    email = escape(data.get('email', ''))
    city = escape(data.get('city', ''))
    job = escape(data.get('job_intention', ''))

    # 教育背景
    edu_html = ''
    for edu in data.get('education', []):
        title_parts = [p for p in [edu.get('school', ''), edu.get('major', ''), edu.get('degree', '')] if p]
        title = escape(' · '.join(title_parts))
        date = escape(f'{edu.get("start_date", "")} - {edu.get("end_date", "至今")}')
        major = escape(f'{edu.get("major", "")} | {edu.get("degree", "")}')
        courses = escape(edu.get('courses', ''))
        edu_html += f'''                <div class="item">
                    <div class="education-title">
                        <span class="time">{date}</span>
                        <span class="school">{title}</span>
                    </div>
                    <span class="major">{major}</span>
                    <p>主修课程：{courses}</p>
                </div>\n'''

    # 实习经历
    exp_html = ''
    for exp in data.get('experience', []):
        company = escape(exp.get('company', ''))
        position = escape(exp.get('position', ''))
        date = escape(f'{exp.get("start_date", "")} - {exp.get("end_date", "至今")}')
        ecity = escape(exp.get('city', ''))
        desc_html = ''.join(f'                        <li>{escape(d)}</li>\n' for d in exp.get('description', []))
        exp_html += f'''                <div class="item">
                    <div class="intern-title">
                        <strong>{company}</strong>
                        <span class="time">{date} {position}</span>
                    </div>
                    <p>工作地点：{ecity}</p>
                    <ul>
{desc_html}                    </ul>
                </div>\n'''

    # 项目经历
    proj_html = ''
    for proj in data.get('projects', []):
        pname = escape(proj.get('name', ''))
        role = escape(proj.get('role', ''))
        date = escape(f'{proj.get("start_date", "")} - {proj.get("end_date", "至今")}')
        desc_html = ''.join(f'                        <li>{escape(d)}</li>\n' for d in proj.get('description', []))
        proj_html += f'''                <div class="item">
                    <div class="project-title">
                        <strong>{pname}</strong>
                        <span class="time">{date} {role}</span>
                    </div>
                    <ul>
{desc_html}                    </ul>
                </div>\n'''

    # 技能标签
    all_skills = []
    skills = data.get('skills', {})
    if isinstance(skills, dict):
        for skill_list in skills.values():
            all_skills.extend(skill_list)
    skills_tags = ''.join(f'                    <span>{escape(s)}</span>\n' for s in all_skills)

    # 自我评价
    eval_html = ''.join(f'                    <li>{escape(item)}</li>\n' for item in data.get('others', []))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} - {job}简历</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: "Microsoft YaHei", sans-serif; }}
        body {{ background-color: #f5f5f5; padding: 30px 20px; }}
        .resume {{ width: 210mm; min-height: 297mm; margin: 0 auto; background: white; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.15); }}
        .top-header {{ background-color: rgb(235, 238, 251); padding: 30px 35px; display: flex; align-items: center; gap: 28px; border-bottom: 1px solid #e0e0e0; }}
        .avatar {{ width: 110px; height: 147px; flex-shrink: 0; background-color: #d0d0d0; overflow: hidden; }}
        .avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
        .header-info {{ flex: 1; }}
        .header-name {{ font-size: 26px; font-weight: bold; color: #2c3e50; margin-bottom: 14px; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px 20px; }}
        .info-row {{ display: flex; font-size: 13px; }}
        .info-row .label {{ width: 60px; font-weight: 500; color: #555; flex-shrink: 0; }}
        .info-row .text {{ flex: 1; color: #333; }}
        .body-content {{ padding: 30px 35px; }}
        .section {{ margin-bottom: 26px; }}
        .section h2 {{ font-size: 16px; color: rgb(46, 81, 219); border-left: 4px solid #3498db; padding-left: 10px; margin-bottom: 14px; }}
        .item {{ margin-bottom: 14px; }}
        .education-title, .intern-title, .project-title {{ display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 14px; }}
        .education-title .time, .intern-title .time, .project-title .time {{ font-weight: bold; }}
        .item .school {{ font-weight: bold; margin-left: 10px; }}
        .item .major {{ font-size: 13px; }}
        .item p {{ color: #555; font-size: 13px; margin-bottom: 3px; }}
        ul {{ padding-left: 20px; color: #333; font-size: 13px; }}
        li {{ margin-bottom: 4px; }}
        .skills-tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .skills-tags span {{ background-color: rgb(235, 238, 251); color: rgb(46, 81, 219); padding: 4px 14px; border-radius: 4px; font-size: 13px; }}
        @page {{ size: A4; margin: 0; }}
        @media print {{ body {{ background-color: white; padding: 0; margin: 0; }} .resume {{ width: 210mm; min-height: 297mm; box-shadow: none; margin: 0; }} }}
    </style>
</head>
<body>
    <div class="resume">
        <div class="top-header">
            <div class="avatar"><img src="avatar.jpg" alt="头像"></div>
            <div class="header-info">
                <div class="header-name">{name}</div>
                <div class="info-grid">
                    <div class="info-row"><div class="label">电话</div><div class="text">{phone}</div></div>
                    <div class="info-row"><div class="label">邮箱</div><div class="text">{email}</div></div>
                    <div class="info-row"><div class="label">城市</div><div class="text">{city}</div></div>
                    <div class="info-row"><div class="label">求职意向</div><div class="text">{job}</div></div>
                </div>
            </div>
        </div>
        <div class="body-content">
            <div class="section">
                <h2>教育经历</h2>
{edu_html}            </div>
            <div class="section">
                <h2>实习经历</h2>
{exp_html}            </div>
            <div class="section">
                <h2>项目经历</h2>
{proj_html}            </div>
            <div class="section">
                <h2>技能清单</h2>
                <div class="skills-tags">
{skills_tags}                </div>
            </div>
            <div class="section">
                <h2>自我评价</h2>
                <ul>
{eval_html}                </ul>
            </div>
        </div>
    </div>
</body>
</html>'''


# ============================================================
# 模板3：活泼创意
# ============================================================
def generate_creative(data):
    """活泼创意模板"""
    name = escape(data.get('name', ''))
    phone = escape(data.get('phone', ''))
    email = escape(data.get('email', ''))
    city = escape(data.get('city', ''))
    job = escape(data.get('job_intention', ''))

    # 技能清单（左栏）
    skills_html = ''
    skills = data.get('skills', {})
    if isinstance(skills, dict):
        for cat, skill_list in skills.items():
            tags = ''.join(f'<span class="skill-tag">{escape(s)}</span>' for s in skill_list)
            skills_html += f'''            <div class="skill-category">
                <div class="skill-cat-name">{escape(cat)}</div>
                <div class="skill-tags">{tags}</div>
            </div>\n'''

    # 自我评价（左栏）
    eval_html = ''.join(f'            <div class="self-eval-item">{escape(item)}</div>\n' for item in data.get('others', []))

    # 教育背景（右栏）
    edu_html = ''
    for edu in data.get('education', []):
        title_parts = [p for p in [edu.get('school', ''), edu.get('major', ''), edu.get('degree', '')] if p]
        title = escape(' · '.join(title_parts))
        date = escape(f'{edu.get("start_date", "")} - {edu.get("end_date", "至今")}')
        courses = escape(edu.get('courses', ''))
        edu_html += f'''            <div class="entry">
                <div class="entry-header">
                    <span class="entry-title">{title}</span>
                    <span class="entry-date">{date}</span>
                </div>
                <div class="edu-courses">主修课程：{courses}</div>
            </div>\n'''

    # 实习经历（右栏）
    exp_html = ''
    for exp in data.get('experience', []):
        company = escape(exp.get('company', ''))
        position = escape(exp.get('position', ''))
        date = escape(f'{exp.get("start_date", "")} - {exp.get("end_date", "至今")}')
        ecity = escape(exp.get('city', ''))
        desc_html = ''.join(f'                    <li>{escape(d)}</li>\n' for d in exp.get('description', []))
        exp_html += f'''            <div class="entry">
                <div class="entry-header">
                    <span class="entry-title">{company}</span>
                    <span class="entry-date">{date}</span>
                </div>
                <div class="entry-subtitle">{position} · {ecity}</div>
                <div class="entry-desc">
                    <ul>
{desc_html}                    </ul>
                </div>
            </div>\n'''

    # 项目经历（右栏）
    proj_html = ''
    for proj in data.get('projects', []):
        pname = escape(proj.get('name', ''))
        role = escape(proj.get('role', ''))
        date = escape(f'{proj.get("start_date", "")} - {proj.get("end_date", "至今")}')
        desc_html = ''.join(f'                    <li>{escape(d)}</li>\n' for d in proj.get('description', []))
        proj_html += f'''            <div class="entry">
                <div class="entry-header">
                    <span class="entry-title">{pname}</span>
                    <span class="entry-date">{date}</span>
                </div>
                <div class="entry-subtitle">{role}</div>
                <div class="entry-desc">
                    <ul>
{desc_html}                    </ul>
                </div>
            </div>\n'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{name} - {job}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Comic Sans MS", "Microsoft YaHei", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #333; line-height: 1.6; padding: 30px 20px; min-height: 100vh; }}
        .resume {{ width: 210mm; min-height: 297mm; margin: 0 auto; background: #fff; border-radius: 20px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3); display: flex; }}
        .sidebar {{ width: 32%; background: linear-gradient(180deg, #ff6b6b 0%, #feca57 50%, #48dbfb 100%); color: #fff; padding: 25px 20px; position: relative; }}
        .sidebar::before {{ content: ""; position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: rgba(255,255,255,0.1); border-radius: 50%; }}
        .avatar {{ width: 110px; height: 140px; margin: 0 auto 15px; border-radius: 20px; overflow: hidden; border: 4px solid #fff; box-shadow: 0 8px 25px rgba(0,0,0,0.2); transform: rotate(-2deg); position: relative; z-index: 1; }}
        .avatar img {{ width: 100%; height: 100%; object-fit: cover; }}
        .name {{ text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 3px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); position: relative; z-index: 1; }}
        .job-title {{ text-align: center; font-size: 13px; background: rgba(255,255,255,0.25); padding: 4px 12px; border-radius: 20px; display: inline-block; margin: 0 auto 15px; width: 100%; text-align: center; position: relative; z-index: 1; }}
        .section-title-l {{ font-size: 14px; font-weight: bold; margin: 15px 0 10px; padding: 6px 12px; background: rgba(255,255,255,0.25); border-radius: 15px; text-align: center; position: relative; z-index: 1; }}
        .contact-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 12px; background: rgba(255,255,255,0.15); padding: 6px 10px; border-radius: 12px; position: relative; z-index: 1; }}
        .contact-item .icon {{ margin-right: 8px; font-size: 14px; }}
        .skill-category {{ margin-bottom: 10px; position: relative; z-index: 1; }}
        .skill-cat-name {{ font-size: 12px; font-weight: bold; margin-bottom: 5px; }}
        .skill-tags {{ display: flex; flex-wrap: wrap; gap: 4px; }}
        .skill-tag {{ background: rgba(255,255,255,0.3); padding: 3px 10px; border-radius: 15px; font-size: 10.5px; }}
        .self-eval-item {{ font-size: 11.5px; margin-bottom: 6px; padding: 5px 10px; background: rgba(255,255,255,0.15); border-radius: 10px; border-left: 3px solid #fff; position: relative; z-index: 1; }}
        .main-content {{ width: 68%; padding: 25px 25px 25px 20px; background: #fffafa; }}
        .section {{ margin-bottom: 18px; }}
        .section-title-r {{ font-size: 16px; font-weight: bold; color: #ff6b6b; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
        .section-title-r .icon {{ font-size: 20px; }}
        .section-title-r .line {{ flex: 1; height: 3px; background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb); border-radius: 2px; }}
        .entry {{ margin-bottom: 14px; padding: 12px 15px; background: #fff; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 4px solid #ff6b6b; }}
        .entry:nth-child(even) {{ border-left-color: #feca57; }}
        .entry:nth-child(3n) {{ border-left-color: #48dbfb; }}
        .entry-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px; }}
        .entry-title {{ font-size: 13.5px; font-weight: bold; color: #333; }}
        .entry-date {{ font-size: 11px; color: #999; background: #f0f0f0; padding: 2px 8px; border-radius: 10px; }}
        .entry-subtitle {{ font-size: 12px; color: #666; margin-bottom: 6px; font-style: italic; }}
        .entry-desc {{ font-size: 12px; color: #555; line-height: 1.7; }}
        .entry-desc ul {{ padding-left: 16px; }}
        .entry-desc li {{ margin-bottom: 3px; }}
        .entry-desc li::marker {{ color: #ff6b6b; }}
        .edu-courses {{ font-size: 11.5px; color: #777; margin-top: 5px; background: #f9f9f9; padding: 6px 10px; border-radius: 8px; }}
        @media print {{ body {{ background: #fff; padding: 0; }} .resume {{ border-radius: 0; box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="resume">
        <div class="sidebar">
            <div class="avatar"><img src="avatar.jpg" alt="头像"></div>
            <div class="name">{name}</div>
            <div class="job-title">🎯 {job}</div>
            <div class="section-title-l">📞 联系方式</div>
            <div class="contact-item"><span class="icon">📱</span><span>{phone}</span></div>
            <div class="contact-item"><span class="icon">✉️</span><span>{email}</span></div>
            <div class="contact-item"><span class="icon">📍</span><span>{city}</span></div>
            <div class="section-title-l">🛠️ 技能清单</div>
{skills_html}            <div class="section-title-l">💪 自我评价</div>
{eval_html}        </div>
        <div class="main-content">
            <div class="section">
                <div class="section-title-r"><span class="icon">🎓</span>教育背景<span class="line"></span></div>
{edu_html}            </div>
            <div class="section">
                <div class="section-title-r"><span class="icon">💼</span>实习经历<span class="line"></span></div>
{exp_html}            </div>
            <div class="section">
                <div class="section-title-r"><span class="icon">🚀</span>项目经历<span class="line"></span></div>
{proj_html}            </div>
        </div>
    </div>
</body>
</html>'''


# ============================================================
# 模板4：现代双栏（调用render_cv_html.py的modern模板）
# ============================================================
def generate_modern(data, output_html, script_dir):
    """现代双栏模板（调用render_cv_html.py）"""
    temp_json = output_html.replace('.html', '_temp.json')
    with open(temp_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    script_path = os.path.join(script_dir, 'render_cv_html.py')
    result = subprocess.run(
        ['python', script_path, temp_json, output_html, 'modern'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if os.path.exists(temp_json):
        os.remove(temp_json)
    return os.path.exists(output_html)


# ============================================================
# 主函数
# ============================================================
def main():
    workspace = os.path.dirname(os.path.abspath(__file__))
    default_data = os.path.join(workspace, 'resume_data.json')
    default_output = os.path.join(workspace, 'cv')
    script_dir = r'C:\Users\32994\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.user_skills\job-search-assistant\scripts'

    data_path = sys.argv[1] if len(sys.argv) > 1 else default_data
    output_dir = sys.argv[2] if len(sys.argv) > 2 else default_output

    if not os.path.exists(data_path):
        print(f'错误: 数据文件不存在: {data_path}')
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 读取数据
    print(f'读取数据文件: {data_path}')
    with open(data_path, 'r', encoding='utf-8') as f:
        data_cn = json.load(f)

    # 转换为英文键名
    basic = data_cn.get('基本信息', {})
    data = {
        'name': basic.get('name', ''),
        'phone': basic.get('phone', ''),
        'email': basic.get('email', ''),
        'city': basic.get('city', ''),
        'job_intention': basic.get('job_intention', ''),
        'avatar': basic.get('avatar', 'avatar.jpg'),
        'education': data_cn.get('教育背景', []),
        'experience': data_cn.get('实习经历', []),
        'projects': data_cn.get('项目经历', []),
        'skills': data_cn.get('技能清单', {}),
        'others': data_cn.get('自我评价', [])
    }

    name = data.get('name', '简历')
    job = data.get('job_intention', '')
    base_name = f'{name}_{job}' if job else name

    # 复制头像到输出目录
    avatar_src = os.path.join(workspace, 'cv', 'avatar.jpg')
    avatar_dst = os.path.join(output_dir, 'avatar.jpg')
    if os.path.exists(avatar_src) and not os.path.exists(avatar_dst):
        import shutil
        shutil.copy(avatar_src, avatar_dst)

    print('\n' + '='*60)
    print('开始生成4个选中模板的简历（HTML + PDF）')
    print('='*60)

    templates = [
        ('左右结构', generate_left_right),
        ('上下结构', generate_top_bottom),
        ('活泼创意', generate_creative),
    ]

    results = {}

    # 生成前3个模板
    for idx, (tpl_name, gen_func) in enumerate(templates, 1):
        print(f'\n[{idx}/4] 生成「{tpl_name}」...')
        html_path = os.path.join(output_dir, f'{base_name}_{tpl_name}.html')
        pdf_path = os.path.join(output_dir, f'{base_name}_{tpl_name}.pdf')

        html_content = gen_func(data)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f'  HTML生成成功')

        pdf_ok = html_to_pdf(html_path, pdf_path)
        results[tpl_name] = {'html': True, 'pdf': pdf_ok}

    # 生成第4个模板（现代双栏，调用render_cv_html.py）
    print(f'\n[4/4] 生成「现代双栏」...')
    html_path = os.path.join(output_dir, f'{base_name}_现代双栏.html')
    pdf_path = os.path.join(output_dir, f'{base_name}_现代双栏.pdf')
    html_ok = generate_modern(data, html_path, script_dir)
    if html_ok:
        print(f'  HTML生成成功')
        pdf_ok = html_to_pdf(html_path, pdf_path)
    else:
        print(f'  HTML生成失败')
        pdf_ok = False
    results['现代双栏'] = {'html': html_ok, 'pdf': pdf_ok}

    # 总结
    print('\n' + '='*60)
    print('生成完成！')
    print('='*60)
    for tpl_name, status in results.items():
        html_ok = '✅' if status.get('html') else '❌'
        pdf_ok = '✅' if status.get('pdf') else '❌'
        print(f'{html_ok} HTML  {pdf_ok} PDF  {tpl_name}')

    print(f'\n所有文件保存在: {output_dir}')
    print('\n使用方法:')
    print('  1. 用记事本打开 resume_data.json 修改内容')
    print('  2. 运行 python generate_selected.py 重新生成4个模板')
    print('  3. Word版需要时单独生成')


if __name__ == '__main__':
    main()
