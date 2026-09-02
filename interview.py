#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面试准备工具（interview）
根据公司和岗位信息，生成针对性的面试准备材料。

用法:
    python interview.py --company "公司名" --position "岗位名" [输出目录]
    python interview.py --company "示例测绘公司" --position "测绘工程师"

输出:
    HTML格式的面试准备报告，包含：
    - 公司和岗位分析
    - 针对性面试问题（专业+行为+项目）
    - 自我介绍定制版
    - 反问环节建议
    - 面试注意事项
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


def load_question_bank(workspace):
    """加载面试题库（从Markdown文件解析）"""
    bank_path = os.path.join(workspace, 'interview-prep', '测绘工程面试题库.md')
    if not os.path.exists(bank_path):
        return {}
    with open(bank_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return {'raw': content}


def analyze_position(position, company):
    """分析岗位类型，返回相关的技能和问题方向"""
    pos_lower = position.lower()
    analysis = {
        'position_type': '',
        'key_skills': [],
        'focus_areas': [],
        'likely_questions': []
    }

    # 判断岗位类型
    if any(k in pos_lower for k in ['gis', '地理信息', '空间数据', '数据处理']):
        analysis['position_type'] = 'GIS工程师'
        analysis['key_skills'] = ['ArcGIS', '空间分析', '数据库', 'Python', '遥感影像处理']
        analysis['focus_areas'] = ['GIS基础', '空间分析', '数据处理', '数据库']
    elif any(k in pos_lower for k in ['地籍', '不动产', '土地调查', '确权', '延包']):
        analysis['position_type'] = '地籍测绘工程师'
        analysis['key_skills'] = ['RTK', '地籍测量', '权属调查', 'ArcGIS', 'CASS']
        analysis['focus_areas'] = ['地籍测量', '权属调查', 'RTK操作', '数据库建设']
    elif any(k in pos_lower for k in ['工程测量', '施工测量', '放样', '变形监测']):
        analysis['position_type'] = '工程测量工程师'
        analysis['key_skills'] = ['全站仪', '水准仪', 'RTK', 'CASS', 'AutoCAD']
        analysis['focus_areas'] = ['控制测量', '施工放样', '变形监测', '仪器操作']
    elif any(k in pos_lower for k in ['遥感', '影像', '无人机', '航测', '摄影测量']):
        analysis['position_type'] = '遥感/航测工程师'
        analysis['key_skills'] = ['ENVI', '遥感影像处理', '无人机', '摄影测量', 'ArcGIS']
        analysis['focus_areas'] = ['遥感基础', '影像分类', '无人机航测', '数据处理']
    else:
        analysis['position_type'] = '测绘工程师（通用）'
        analysis['key_skills'] = ['RTK', '全站仪', 'ArcGIS', 'CASS', 'AutoCAD', '水准仪']
        analysis['focus_areas'] = ['测量基础', '仪器操作', 'GIS应用', '地籍测量']

    return analysis


def generate_self_introduction(resume_data, company, position, analysis):
    """生成定制版自我介绍"""
    basic = resume_data.get('基本信息', {})
    education = resume_data.get('教育背景', [])
    experience = resume_data.get('实习经历', [])
    skills = resume_data.get('技能清单', {})

    name = basic.get('name', '')
    school = education[0].get('school', '') if education else ''
    major = education[0].get('major', '') if education else ''
    grade = education[0].get('grade', '2023级') if education else ''
    graduate = education[0].get('end_date', '2027.06') if education else ''

    # 实习经历摘要
    exp_summary = ''
    if experience:
        exp = experience[0]
        exp_summary = f"我在{exp.get('company', '')}进行了{exp.get('position', '')}实习，参与了{exp.get('project', '相关项目')}，主要负责{exp.get('description', ['相关工作'])[0] if exp.get('description') else '相关工作'}。"

    # 技能摘要
    skill_summary = ''
    all_skills = []
    if isinstance(skills, dict):
        for skill_list in skills.values():
            all_skills.extend(skill_list)
    if all_skills:
        skill_summary = f"技能方面，我能熟练使用{'、'.join(all_skills[:5])}等工具。"

    intro = f"""各位面试官好，我叫{name}，是{school}{major}专业{grade}本科生，预计{graduate}毕业。

专业方面，我系统学习了测量学、控制测量、地籍测量、GIS、遥感等核心课程，掌握了测绘工程的基本理论和方法。

实践方面，{exp_summary}

{skill_summary}

求职意向是{position}，我能接受长期出差和外业工作，希望能在{company}从基础工作做起，逐步成长为能独立承担项目的技术人员。

以上是我的自我介绍，谢谢！"""

    return intro


def generate_targeted_questions(analysis, resume_data):
    """生成针对性面试问题"""
    questions = {
        '经历深挖（重点）': [],
        '专业知识': [],
        '软件操作': [],
        '仪器操作': [],
        '项目经验': [],
        '行为面试': [],
    }

    pos_type = analysis['position_type']

    # ========== 经历深挖题（重点，根据用户具体经历生成） ==========
    # 通用经历深挖框架
    deep_questions = [
        '请详细介绍一下你在实习中做的最有成就感的一件事，具体是怎么做的？',
        '你在实习/实训中遇到过最大的困难是什么？你是怎么分析和解决的？',
        '你用ArcGIS做过的最复杂的一个分析任务是什么？用了哪些工具？流程是怎样的？',
        '你在数据处理中遇到过数据质量问题吗？具体是什么问题？怎么检查和修复的？',
        '你在实习中独立负责了什么工作？如果让你重新做，你会怎么优化？',
        '你在团队项目中，和同学/同事配合时遇到过什么问题？怎么解决的？',
        '你实习的这个项目，整体的技术路线是什么？你在其中哪个环节？',
        '你在实训中做过地形测图吗？从外业到内业的完整流程是什么？你负责哪部分？',
        '你用过AI工具辅助工作，具体是怎么用的？AI工具在测绘工作中有什么优势和局限？',
        '你在实习中有没有发现过流程或方法上的问题？你提出过什么改进建议吗？',
    ]

    # 根据用户实习经历生成定制问题
    experience = resume_data.get('实习经历', [])
    for exp in experience:
        company = exp.get('company', '')
        desc = exp.get('description', [])
        desc_text = ' '.join(desc)

        if 'ArcGIS' in desc_text and ('图件' in desc_text or '矢量' in desc_text):
            deep_questions.append(f'你在{company}用ArcGIS制作房屋宗地一体占压耕地图件，具体用了哪些叠加分析工具？拓扑检查了哪些规则？')
        if '拓扑' in desc_text:
            deep_questions.append(f'你说做了拓扑检查，具体是怎么操作的？发现了哪些典型错误？怎么修复的？')
        if 'AI' in desc_text or 'Claude' in desc_text or '校验工具' in desc_text:
            deep_questions.append(f'你独立开发权属信息校验工具，具体是怎么实现的？身份证重复检测和户主唯一性校验的逻辑是什么？')
        if '土地承包' in desc_text or '延包' in desc_text:
            deep_questions.append(f'二轮土地承包延包项目的9个阶段具体是什么？你在每个阶段做了什么？')
        if '权属' in desc_text and '入库' in desc_text:
            deep_questions.append(f'权属数据入库的完整流程是什么？数据格式是什么？遇到过什么数据质量问题？')
        if '农户' in desc_text and ('录入' in desc_text or '核实' in desc_text):
            deep_questions.append(f'农户资料录入核实具体是怎么做的？需要核对哪些信息？遇到过信息不一致怎么处理？')

    # 根据用户项目/实训经历生成定制问题
    projects = resume_data.get('项目经历', [])
    for proj in projects:
        desc = proj.get('description', [])
        desc_text = ' '.join(desc)

        if 'RTK' in desc_text or '全站仪' in desc_text:
            deep_questions.append('你在实训中用RTK做地形测图，点校正怎么做的？用了几个已知点？校正残差一般多少？')
        if 'CASS' in desc_text or '地形测图' in desc_text:
            deep_questions.append('CASS绘制地形图的完整流程是什么？等高线是怎么生成的？DTM建模需要注意什么？')
        if '空间数据库' in desc_text or '数据入库' in desc_text:
            deep_questions.append('你搭建空间数据库的流程是什么？用了什么格式？数据入库要注意哪些问题？')
        if '地质灾害' in desc_text or '专题图' in desc_text:
            deep_questions.append('你做地质灾害专题图用了哪些空间分析方法？评价因子是怎么提取的？权重怎么确定的？')
        if 'DEM' in desc_text or '摄影测量' in desc_text:
            deep_questions.append('摄影测量实训中DEM制作的步骤是什么？DEM和DSM有什么区别？')
        if 'C语言' in desc_text or '程序设计' in desc_text:
            deep_questions.append('你用C语言做测量程序设计，实现了什么功能？核心算法是什么？')

    questions['经历深挖（重点）'] = deep_questions[:15]  # 最多15道，避免太多

    # 专业知识题（根据岗位类型）
    if '地籍' in pos_type:
        questions['专业知识'] = [
            '什么是地籍调查？地籍调查的内容和流程是什么？',
            '宗地草图和宗地图有什么区别？',
            '界址点测量的精度要求是多少？用什么方法测量？',
            '二轮土地承包延包工作的主要内容和原则是什么？',
            '土地权属调查中遇到权属争议如何处理？',
        ]
    elif 'GIS' in pos_type:
        questions['专业知识'] = [
            '什么是GIS？GIS由哪些部分组成？',
            '矢量数据和栅格数据有什么区别？各自适用什么场景？',
            '什么是空间参考？地理坐标系和投影坐标系有什么关系？',
            '常见的空间分析方法有哪些？请举例说明。',
            '拓扑关系有哪些？在GIS中有什么作用？',
        ]
    elif '工程测量' in pos_type:
        questions['专业知识'] = [
            '控制测量的方法有哪些？导线测量的外业工作是什么？',
            '施工放样的基本方法有哪些？',
            '变形监测的目的和方法是什么？',
            '水准测量的原理是什么？水准路线有哪些形式？',
            '测量误差的来源有哪些？如何减小误差？',
        ]
    elif '遥感' in pos_type:
        questions['专业知识'] = [
            '遥感的基本原理是什么？遥感系统由哪些部分组成？',
            '遥感影像的分辨率有哪些？各自的含义是什么？',
            '监督分类和非监督分类有什么区别？',
            '无人机航测的流程是什么？',
            '影像融合的目的和方法是什么？',
        ]
    else:
        questions['专业知识'] = [
            '什么是测量学？测量的三项基本工作是什么？',
            '什么是大地水准面？它有什么作用？',
            '等高线有哪些特性？',
            '比例尺精度是多少？如何计算？',
            '平面控制测量和高程控制测量分别有哪些方法？',
        ]

    # 软件操作题
    key_skills = analysis['key_skills']
    if 'ArcGIS' in key_skills:
        questions['软件操作'].append('ArcGIS中如何进行坐标转换？需要注意什么？')
        questions['软件操作'].append('ArcGIS中如何做缓冲区分析和叠加分析？')
        questions['软件操作'].append('ArcGIS中如何进行土地利用分类统计？')
    if 'CASS' in key_skills:
        questions['软件操作'].append('CASS中地形图绘制的流程是什么？')
        questions['软件操作'].append('CASS中如何计算土方量？有哪些方法？')
    if 'ENVI' in key_skills:
        questions['软件操作'].append('ENVI中遥感影像分类的流程是什么？')
        questions['软件操作'].append('如何评价遥感影像分类的精度？')
    if 'Python' in key_skills:
        questions['软件操作'].append('你如何用Python处理空间数据？用过哪些库？')
    if not questions['软件操作']:
        questions['软件操作'] = [
            '你最熟练的测绘软件是什么？请描述一个用它完成的具体任务。',
            'ArcGIS中如何进行坐标转换？',
            'CASS中如何绘制地形图？',
        ]

    # 仪器操作题
    if 'RTK' in key_skills:
        questions['仪器操作'].append('RTK测量的原理是什么？固定解和浮点解有什么区别？')
        questions['仪器操作'].append('RTK测量的操作流程是什么？点校正需要注意什么？')
    if '全站仪' in key_skills:
        questions['仪器操作'].append('全站仪的操作流程是什么？如何进行对中整平？')
    if '水准仪' in key_skills:
        questions['仪器操作'].append('水准测量的操作流程是什么？如何消除视差？')
    if '无人机' in key_skills:
        questions['仪器操作'].append('无人机航测的外业和内业流程分别是什么？')
    if not questions['仪器操作']:
        questions['仪器操作'] = [
            'RTK测量的原理是什么？操作流程是什么？',
            '全站仪如何进行对中整平？',
            '你使用过哪些测量仪器？最熟练的是哪个？',
        ]

    # 项目经验题
    questions['项目经验'] = [
        '请介绍一个你参与过的测绘项目，你在其中负责什么工作？',
        '你在项目中遇到过什么困难？如何解决的？',
        '你参与的项目中，数据质量是如何检查和控制的？',
        '如果让你独立负责一个小型测绘项目，你会怎么安排工作流程？',
        '你在实习/项目中最大的收获是什么？',
    ]

    # 行为面试题
    questions['行为面试'] = [
        '你为什么选择测绘这个行业？为什么选择我们公司？',
        '你能接受长期出差和外业工作吗？',
        '你的职业规划是什么？',
        '你在团队项目中扮演什么角色？',
        '如果和同事意见不一致，你怎么处理？',
        '你如何学习新技术？请举例说明。',
        '这个岗位要求Python，你目前不太熟练，你怎么办？',
        '你有什么想问我们的？',
    ]

    return questions


def generate_report(company, position, analysis, resume_data, questions, self_intro, output_path):
    """生成HTML格式的面试准备报告"""
    basic = resume_data.get('基本信息', {})
    name = basic.get('name', '候选人')

    # 生成问题HTML
    questions_html = ''
    for category, qs in questions.items():
        qs_html = ''.join(f'<div class="question"><span class="q-num">Q{i+1}</span><span class="q-text">{escape(q)}</span></div>' for i, q in enumerate(qs))
        questions_html += f'''
        <div class="section">
            <h3>{escape(category)}</h3>
            {qs_html}
        </div>'''

    # 关键技能标签
    skills_tags = ''.join(f'<span class="skill-tag">{escape(s)}</span>' for s in analysis['key_skills'])

    report_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>面试准备报告 - {escape(company)} {escape(position)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 30px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #27ae60); color: white; padding: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ font-size: 18px; color: #2c3e50; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #27ae60; }}
        .section h3 {{ font-size: 15px; color: #27ae60; margin: 15px 0 10px; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
        .info-item {{ font-size: 14px; }}
        .info-item .label {{ color: #999; margin-right: 8px; }}
        .info-item .value {{ color: #333; font-weight: 500; }}
        .skill-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .skill-tag {{ background: #e8f5e9; color: #27ae60; padding: 5px 14px; border-radius: 15px; font-size: 13px; }}
        .intro-box {{ background: #f9f9f9; border-left: 4px solid #27ae60; padding: 20px; border-radius: 0 8px 8px 0; white-space: pre-line; font-size: 14px; line-height: 1.8; color: #444; }}
        .question {{ display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }}
        .question:last-child {{ border-bottom: none; }}
        .q-num {{ background: #27ae60; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; flex-shrink: 0; }}
        .q-text {{ font-size: 14px; color: #333; line-height: 1.6; }}
        .tips {{ background: #fff8e1; border-left: 4px solid #ffa000; padding: 15px 20px; border-radius: 0 8px 8px 0; }}
        .tips h3 {{ color: #e65100; margin-top: 0; }}
        .tips ul {{ padding-left: 20px; font-size: 13px; line-height: 1.8; color: #555; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>面试准备报告</h1>
            <div class="meta">候选人：{escape(name)} | 公司：{escape(company)} | 岗位：{escape(position)} | 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>

        <div class="content">
            <div class="section">
                <h2>一、岗位分析</h2>
                <div class="info-grid">
                    <div class="info-item"><span class="label">岗位类型：</span><span class="value">{escape(analysis['position_type'])}</span></div>
                    <div class="info-item"><span class="label">目标公司：</span><span class="value">{escape(company)}</span></div>
                </div>
                <div style="font-size:14px;color:#666;margin-bottom:8px">核心技能要求：</div>
                <div class="skill-tags">{skills_tags}</div>
                <div style="font-size:14px;color:#666;margin:15px 0 8px">重点准备方向：</div>
                <div style="font-size:14px;color:#444;line-height:1.8">{'、'.join(analysis['focus_areas'])}</div>
            </div>

            <div class="section">
                <h2>二、定制版自我介绍（3分钟）</h2>
                <div class="intro-box">{escape(self_intro)}</div>
            </div>

            <div class="section">
                <h2>三、针对性面试问题</h2>
                {questions_html}
            </div>

            <div class="section">
                <h2>四、反问环节建议</h2>
                <div class="tips">
                    <h3>推荐问的问题</h3>
                    <ul>
                        <li>请问这个岗位的主要工作内容和项目类型是什么？</li>
                        <li>公司对新人的培养体系是怎样的？有没有导师带教？</li>
                        <li>这个岗位在项目中的角色和发展路径是怎样的？</li>
                        <li>公司目前主要使用哪些技术和软件？</li>
                        <li>如果有幸入职，入职前需要做哪些准备？</li>
                    </ul>
                    <h3 style="margin-top:15px">避免问的问题</h3>
                    <ul>
                        <li>工资多少（等HR面再问）</li>
                        <li>加不加班（显得怕吃苦）</li>
                        <li>能不能不做外业（与岗位性质冲突）</li>
                        <li>公司是做什么的（说明没做功课）</li>
                    </ul>
                </div>
            </div>

            <div class="section">
                <h2>五、面试注意事项</h2>
                <div class="tips">
                    <ul>
                        <li><strong>提前准备</strong>：研究公司背景、项目类型、岗位要求</li>
                        <li><strong>带好材料</strong>：简历、成绩单、证书、作品集（如有）</li>
                        <li><strong>着装得体</strong>：干净整洁，不需要正装但要正式</li>
                        <li><strong>准时到达</strong>：提前10-15分钟到</li>
                        <li><strong>表达清晰</strong>：语速适中，逻辑清楚，用数据说话</li>
                        <li><strong>诚实回答</strong>：不会的就说不会，但可以说学习思路，不要编造</li>
                        <li><strong>保持积极</strong>：展示学习能力和吃苦精神，测绘行业看重踏实肯干</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="footer">
            本报告由 job-search-assistant 自动生成，仅供参考，祝你面试顺利！
        </div>
    </div>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    print(f'面试准备报告已生成: {output_path}')


def main():
    workspace = os.path.dirname(os.path.abspath(__file__))

    company = ''
    position = ''
    output_dir = os.path.join(workspace, 'interview-prep')

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--company' and i + 1 < len(args):
            company = args[i + 1]
            i += 2
        elif args[i] == '--position' and i + 1 < len(args):
            position = args[i + 1]
            i += 2
        else:
            if os.path.isdir(args[i]):
                output_dir = args[i]
            i += 1

    if not company or not position:
        print('用法:')
        print('  python interview.py --company "公司名" --position "岗位名" [输出目录]')
        print()
        print('示例:')
        print('  python interview.py --company "示例测绘公司" --position "测绘工程师"')
        sys.exit(1)

    # 加载数据
    print('加载简历数据...')
    resume_data = load_resume_data(workspace)

    print('加载面试题库...')
    question_bank = load_question_bank(workspace)

    # 分析岗位
    print(f'分析岗位: {company} - {position}')
    analysis = analyze_position(position, company)
    print(f'  岗位类型: {analysis["position_type"]}')
    print(f'  核心技能: {", ".join(analysis["key_skills"])}')
    print(f'  重点方向: {", ".join(analysis["focus_areas"])}')

    # 生成自我介绍
    print('生成定制版自我介绍...')
    self_intro = generate_self_introduction(resume_data, company, position, analysis)

    # 生成针对性问题
    print('生成针对性面试问题...')
    questions = generate_targeted_questions(analysis, resume_data)
    total_qs = sum(len(qs) for qs in questions.values())
    print(f'  共生成 {total_qs} 道面试问题')

    # 生成报告
    os.makedirs(output_dir, exist_ok=True)
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', f'{company}_{position}')
    output_path = os.path.join(output_dir, f'interview_{safe_name}.html')
    generate_report(company, position, analysis, resume_data, questions, self_intro, output_path)

    print()
    print('='*50)
    print('面试准备材料生成完成！')
    print(f'报告路径: {output_path}')
    print(f'详细题库: {os.path.join(workspace, "interview-prep", "测绘工程面试题库.md")}')
    print('='*50)


if __name__ == '__main__':
    main()
