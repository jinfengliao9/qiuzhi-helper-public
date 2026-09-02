# -*- coding: utf-8 -*-
"""
阶段1：OQ 开放题生成器
读取 application_profile.json 用户真实经历，按题目类型生成针对性答案，按公司存档。
用法：
  python oq_generator.py list                          # 列出题库（按分类）
  python oq_generator.py gen --company "公司名" --job "岗位" --type 1   # 生成第1类所有题
  python oq_generator.py gen --company "公司名" --job "岗位" --qid 1.2   # 生成指定题
  python oq_generator.py gen --company "公司名" --job "岗位" --custom "你的题目"  # 自定义题目
"""
import json, io, os, sys, argparse, re
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(WS, "application_profile.json")
ANSWER_DIR = os.path.join(WS, "oq_answers")

# ============ 题库（8大类，每类3-5题）============
QUESTION_BANK = {
    1: {
        "name": "求职动机类",
        "questions": {
            "1.1": "为什么选择我们公司？",
            "1.2": "为什么应聘这个岗位？",
            "1.3": "你对我们公司有哪些了解？",
            "1.4": "你还投递了哪些公司？如果都给你offer你怎么选？",
        }
    },
    2: {
        "name": "职业规划类",
        "questions": {
            "2.1": "你的短期和长期职业规划是什么？",
            "2.2": "3-5年内你希望达到什么水平？",
            "2.3": "你为什么选择测绘这个行业？",
        }
    },
    3: {
        "name": "个人特质类",
        "questions": {
            "3.1": "你的优点和缺点分别是什么？",
            "3.2": "你最大的成就是什么？",
            "3.3": "你遇到过的最大困难是什么？如何解决的？",
        }
    },
    4: {
        "name": "经历深挖类",
        "questions": {
            "4.1": "介绍一次你团队合作的经历。",
            "4.2": "介绍一次你独立解决问题的经历。",
            "4.3": "你在实习中最大的收获是什么？",
            "4.4": "你在学校做过的实训中，最有成就感的是哪一次？",
        }
    },
    5: {
        "name": "价值观态度类",
        "questions": {
            "5.1": "你如何看待加班和长期出差？",
            "5.2": "你如何看待从基层/一线做起？",
            "5.3": "你的职业价值观是什么？",
        }
    },
    6: {
        "name": "情景应变类",
        "questions": {
            "6.1": "如果和同事发生矛盾，你会怎么处理？",
            "6.2": "如果领导安排你不喜欢的工作，你怎么办？",
            "6.3": "如果项目赶进度但你发现数据有问题，你会怎么做？",
        }
    },
    7: {
        "name": "专业认知类",
        "questions": {
            "7.1": "你对测绘行业有什么理解？",
            "7.2": "你认为测绘工程师最重要的能力是什么？",
            "7.3": "你在学校学的课程中，哪些对工作最有帮助？",
        }
    },
    8: {
        "name": "国企特有类",
        "questions": {
            "8.1": "你对我们企业的文化/使命有什么理解？",
            "8.2": "你是否接受异地调配/服从组织安排？",
            "8.3": "你对薪资有什么期望？",
            "8.4": "你为什么选择国企而不是私企？",
        }
    },
}

# ============ 国企话术库 ============
SOE_PHRASES = {
    "stability": ["希望在一个稳定的平台长期发展", "倾向于在一家企业深耕而非频繁跳槽", "看重企业的长期发展空间"],
    "responsibility": ["具备较强的责任心", "对待工作认真负责", "能够承担压力和责任"],
    "teamwork": ["注重团队协作", "善于与同事沟通配合", "能够融入团队共同完成目标"],
    "hardworking": ["能吃苦耐劳", "愿意从基层做起", "不怕外业和艰苦环境"],
    "learning": ["学习能力强", "能够快速适应新环境和新技术", "保持持续学习的态度"],
    "loyalty": ["对企业有认同感", "愿意与企业共同成长", "认同企业的价值观和发展理念"],
    "grassroots": ["愿意从一线/基层做起", "不排斥外业和基础工作", "认为基层经历是成长的必经之路"],
}

def load_profile():
    with io.open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)

def get_user_context(p):
    """从profile提取生成答案所需的用户素材"""
    b = p.get("基本信息", {})
    edu = p.get("教育背景", [{}])[0]
    intern = p.get("实习经历", [{}])[0] if p.get("实习经历") else {}
    proj = p.get("项目经历", [{}])[0] if p.get("项目经历") else {}
    skills = p.get("专业技能", {})
    return {
        "name": b.get("姓名", ""),
        "major": edu.get("专业", "测绘工程"),
        "school": edu.get("学校", "示例大学"),
        "college": edu.get("学院", ""),
        "degree": edu.get("degree", "工学学士"),
        "gpa": edu.get("GPA", ""),
        "rank": edu.get("专业排名", ""),
        "intern_company": intern.get("单位名称", ""),
        "intern_position": intern.get("岗位", ""),
        "intern_desc": intern.get("工作内容", ""),
        "intern_start": intern.get("入职时间", ""),
        "intern_end": intern.get("离职时间", ""),
        "proj_name": proj.get("项目名称", ""),
        "proj_role": proj.get("担任角色", ""),
        "proj_desc": proj.get("项目描述", ""),
        "skills_software": "、".join(skills.get("软件工具", [])),
        "skills_instrument": "、".join(skills.get("测量仪器", [])),
        "skills_pro": "、".join(skills.get("专业技能", [])),
        "skills_lang": "、".join(skills.get("编程语言", [])),
        "job_intention": b.get("求职意向", "测绘工程师"),
        "expected_salary": b.get("期望薪资", ""),
        "accept_transfer": b.get("是否服从调剂", "是"),
        "self_eval": p.get("自我评价", []),
    }

def star_framework(situation, task, action, result):
    """STAR框架格式化"""
    return f"【背景】{situation}\n【任务】{task}\n【行动】{action}\n【结果】{result}"

# ============ 各类题目生成函数 ============

def gen_q1_1(ctx, company, job):
    """为什么选择我们公司"""
    return f"""我选择{company}，主要基于以下几点考虑：

首先，{company}作为行业内具有影响力的企业，拥有稳定的发展平台和完善的人才培养体系，这与我希望在一个稳定平台长期发展的职业诉求高度契合。我了解到贵公司在测绘/地理信息领域有着深厚的技术积累和丰富的项目资源，能够为应届生提供系统的成长路径。

其次，贵公司的业务方向与我的专业背景高度匹配。我是{ctx['school']}{ctx['major']}专业的学生，在校期间系统学习了测量学、GIS、遥感等专业课程，熟练掌握{ctx['skills_software']}等软件工具，能够使用{ctx['skills_instrument']}进行外业数据采集。我相信这些专业能力能够在贵公司的项目中得到充分发挥。

最后，我认同贵公司的企业文化和价值观。作为一名应届生，我希望能够加入一家有社会责任感、重视技术传承的企业，与企业共同成长。{company}正是我理想中的平台，我非常期待能够加入贵公司，从基层做起，为公司的发展贡献自己的力量。"""

def gen_q1_2(ctx, company, job):
    """为什么应聘这个岗位"""
    return f"""我应聘{job}岗位，是基于对自身能力和岗位需求的深入匹配：

第一，专业对口。我在校期间主修{ctx['major']}，核心课程包括地形测量、控制测量、GIS空间分析、摄影测量等，专业基础知识扎实，能够快速适应{job}岗位的技术要求。

第二，技能匹配。我熟练使用{ctx['skills_software']}等专业软件，能够操作{ctx['skills_instrument']}进行外业数据采集，具备{ctx['skills_pro']}等专业技能。在实习期间，我在{ctx['intern_company']}参与了实际项目，将理论知识应用于实践，积累了一定的项目经验。

第三，兴趣驱动。我对测绘地理信息行业有着浓厚的兴趣，享受从外业数据采集到内业数据处理、再到成果输出的完整工作流程。我认为{job}岗位能够让我充分发挥专业特长，同时在实践中不断提升自己。

第四，态度匹配。我能接受长期出差和外业工作，具备吃苦耐劳的精神，愿意从一线做起，这与{job}岗位的工作性质相契合。"""

def gen_q1_3(ctx, company, job):
    """对公司有哪些了解"""
    return f"""通过官网、招聘信息以及行业交流，我对{company}有以下了解：

{company}是一家专注于测绘地理信息领域的企业，业务涵盖国土测绘、城市规划、地理信息系统建设等多个方向，在行业内具有良好的口碑和技术实力。公司拥有一支专业技术过硬的团队，注重技术创新和人才培养，为员工提供了广阔的发展空间。

我了解到贵公司近年来参与了多个重点项目，在智慧城市、自然资源调查、国土空间规划等领域有着丰富的项目经验。这些业务方向与我的专业背景和职业兴趣高度一致，我非常希望能够在这样的平台上学习和成长。

同时，我也注意到贵公司重视企业文化建设，倡导团队协作和精益求精的工作态度，这与我的价值观相契合。我相信加入{company}不仅能够提升我的专业能力，也能够让我在一个积极向上的团队氛围中实现个人价值。"""

def gen_q2_1(ctx, company, job):
    """短期和长期职业规划"""
    return f"""我的职业规划分为短期和长期两个阶段：

【短期规划（1-3年）】
作为一名应届生，我首先希望能够快速融入{company}的团队，熟悉公司的业务流程和技术规范。在这一阶段，我的重点是夯实专业基础，熟练掌握公司常用的技术工具和工作方法，争取在1年内能够独立承担基础的测绘/GIS项目任务。同时，我希望通过参与实际项目，将在校所学的理论知识与实践相结合，不断提升自己的外业操作和内业数据处理能力。

【长期规划（3-5年及以上）】
在积累了一定的项目经验后，我希望能够向技术骨干或项目负责人的方向发展，能够独立负责中小型项目的技术方案设计和实施管理。同时，我希望持续关注测绘地理信息行业的新技术发展，如无人机航测、三维激光扫描、GIS与AI结合等，不断拓展自己的技术视野。

我希望能够在{company}这样一个稳定的平台上长期发展，与公司共同成长，最终成为一名技术过硬、能够独当一面的测绘工程师。"""

def gen_q3_1(ctx, company, job):
    """优点和缺点"""
    return f"""【优点】
第一，学习能力强，能够快速掌握新技术。在校期间，我通过课程学习和自主实践，熟练掌握了{ctx['skills_software']}等多种专业软件，能够较快适应新的工作环境和技术要求。

第二，工作认真负责，具备较强的执行力。在实习和实训中，我对待每一项任务都认真细致，确保数据采集和处理的准确性，能够按时完成分配的工作。

第三，具备团队协作精神。测绘项目往往需要团队配合完成，我善于与同学和同事沟通协作，能够在团队中发挥自己的作用，共同完成项目目标。

【缺点】
我的不足之处在于项目经验还不够丰富，作为应届生，在复杂项目的整体把控和技术方案设计方面还有待提升。此外，在沟通表达方面，我有时过于内敛，在公开场合表达自己观点时还不够自信。

针对这些不足，我正在通过积极参与项目实践、主动向有经验的同事请教来弥补，同时也在有意识地锻炼自己的沟通表达能力。我相信通过在{company}的学习和实践，这些不足能够逐步得到改善。"""

def gen_q4_1(ctx, company, job):
    """团队合作经历"""
    s = f"在{ctx['school']}的专业实训课程中，我所在的小组需要完成一项完整的测绘实训任务"
    t = "包括外业控制测量、数据采集、内业数据处理和成果图件输出，任务量大、时间紧，需要小组4-5人密切配合"
    a = "我在小组中主要负责外业数据采集和部分内业处理工作。在项目开始前，我与小组成员一起制定了详细的工作计划和分工，明确了每个人的职责和时间节点。在外业采集过程中，我严格按照测量规范操作，确保数据的准确性和完整性，同时与负责内业的同学保持及时沟通，发现问题及时反馈和修正。在项目后期，我主动协助其他同学完成数据检查和成果整理工作，确保项目按时交付。"
    r = "通过这次团队合作，我们小组顺利完成了实训任务，成果获得了指导老师的好评。更重要的是，我深刻体会到了团队协作的重要性——测绘项目不是一个人能够完成的，只有团队成员之间密切配合、及时沟通，才能高效高质量地完成任务。这段经历也让我学会了如何在团队中发挥自己的优势，同时尊重和配合他人的工作。"
    return star_framework(s, t, a, r)

def gen_q4_3(ctx, company, job):
    """实习中最大的收获"""
    return f"""在{ctx['intern_company']}实习期间，我最大的收获是将在校所学的理论知识真正应用到了实际项目中，完成了从学生到职场人的初步转变。

具体来说，有以下几点收获：

第一，专业技能的实战提升。在实习中，我参与了地籍测量和土地相关项目，实际操作了{ctx['skills_instrument']}等测量仪器，使用{ctx['skills_software']}进行数据处理和图件制作。通过真实项目的锻炼，我对测绘工作的完整流程有了更深入的理解，操作熟练度和数据处理能力都有了明显提升。

第二，工作态度和职业素养的培养。实习让我认识到，测绘工作对数据准确性要求极高，任何一个小的误差都可能影响最终成果。因此，我养成了认真细致、反复核对的工作习惯。同时，我也学会了如何与同事和客户沟通，如何按照项目进度要求完成工作，这些都是在学校里学不到的。

第三，对行业和职业的更清晰认知。通过实习，我对测绘地理信息行业的实际工作内容、技术发展趋势和职业发展路径有了更直观的认识，也更加坚定了我在这个行业长期发展的决心。

这段实习经历为我正式步入职场打下了良好的基础，我相信这些收获能够帮助我更快地适应{company}的工作。"""

def gen_q5_1(ctx, company, job):
    """如何看待加班和长期出差"""
    return f"""对于加班和长期出差，我持完全接受和理解的态度。

首先，测绘行业的工作性质决定了外业作业和项目驻场是常态。测绘项目往往有明确的时间节点和工期要求，在项目攻坚阶段，适当的加班是保障项目按时交付的必要手段，我对此有充分的心理准备。

其次，长期出差是测绘工作的重要组成部分。作为测绘工程师，需要深入项目现场进行数据采集和技术指导，这是工作的核心内容之一。我在校期间的实训和实习中已经有过外业作业和异地工作的经历，能够适应出差的工作节奏和生活环境。

第三，我认为加班和出差也是个人成长的重要途径。在项目一线能够接触到更多实际问题，积累更丰富的项目经验，快速提升专业能力。对于应届生来说，这是非常宝贵的学习机会。

当然，我也理解公司会合理安排工作节奏，保障员工的基本休息和健康。我会在保证工作质量和效率的前提下，积极配合公司的工作安排，不推诿、不抱怨，以认真负责的态度完成每一项任务。"""

def gen_q7_2(ctx, company, job):
    """测绘工程师最重要的能力"""
    return f"""我认为测绘工程师最重要的能力可以概括为以下几个方面：

第一，扎实的专业技术能力。这是测绘工程师的立身之本，包括熟练掌握测量学、控制测量、GIS、遥感等专业理论知识，能够操作{ctx['skills_instrument']}等测量仪器进行高精度数据采集，熟练使用{ctx['skills_software']}等软件进行数据处理和成果输出。只有技术过硬，才能保障测绘成果的准确性和可靠性。

第二，认真细致的工作态度。测绘工作对数据精度要求极高，"差之毫厘，谬以千里"，任何一个小的疏忽都可能导致整个项目成果的错误。因此，测绘工程师必须具备高度的责任心和严谨细致的工作作风，在数据采集、处理、检查的每个环节都严格把关。

第三，解决实际问题的能力。测绘项目现场情况复杂多变，经常会遇到各种突发问题，如地形复杂导致通视困难、仪器故障、数据异常等。优秀的测绘工程师需要具备较强的问题分析和解决能力，能够在现场快速判断问题原因并采取有效的应对措施。

第四，团队协作和沟通能力。测绘项目通常需要团队配合完成，外业和内业之间、不同工序之间需要密切协作。同时，还需要与甲方、施工方等多方进行沟通协调。因此，良好的团队协作和沟通能力是必不可少的。

第五，持续学习的能力。测绘技术发展迅速，无人机航测、三维激光扫描、GIS与AI结合等新技术不断涌现。测绘工程师需要保持学习的热情，及时掌握新技术、新方法，不断提升自己的技术水平。

作为应届生，我在专业技术和工作态度方面已有一定基础，但在解决复杂问题和项目经验方面还需要持续提升，我希望能够在{company}的平台上不断学习和成长。"""

def gen_q8_2(ctx, company, job):
    """是否接受异地调配"""
    return f"""我完全接受异地调配，服从组织的工作安排。

首先，我在求职意向中已经明确表示期望工作城市不限，并且愿意服从调剂。测绘行业的项目分布在全国各地，作为测绘工程师，跟随项目到不同的地方工作是职业的常态，我对此有充分的认知和心理准备。

其次，我在校期间的实训和实习中已经有过异地工作的经历，能够适应不同地区的生活环境和工作节奏。我性格适应能力较强，能够快速融入新的工作和生活环境。

第三，我认为异地工作对个人成长也是非常有益的。不同地区的项目类型和技术要求各不相同，能够接触到更多样化的项目经验，拓宽技术视野。同时，在异地工作也能够锻炼独立生活和独立解决问题的能力。

当然，如果公司能够结合我的个人意愿和项目需要进行合理安排，我会非常感激。但无论被分配到哪里，我都会以工作为重，认真履行岗位职责，不辜负公司的信任和培养。"""

def gen_q8_4(ctx, company, job):
    """为什么选择国企而不是私企"""
    return f"""我选择国企，主要基于以下几点考虑：

第一，稳定性和长期发展。国企通常具有更稳定的经营状况和更完善的人才培养体系，能够为员工提供长期的职业发展平台。作为一名应届生，我希望能够在一个稳定的环境中深耕技术，逐步成长，而不是频繁跳槽。国企的稳定性正好契合我的职业诉求。

第二，项目资源和技术积累。国企往往承担着国家和地方的重点项目，项目规模大、技术要求高，能够接触到更前沿的技术和更复杂的项目场景。这对于应届生的技术成长和经验积累非常有利。我了解到{company}在测绘地理信息领域有着丰富的项目资源和深厚的技术积累，这是非常吸引我的地方。

第三，企业文化和价值观。国企通常注重社会责任和员工关怀，有着较为完善的福利保障体系和人性化的管理制度。我认同国企"踏实做事、稳健发展"的文化氛围，希望能够在这样的环境中工作和成长。

第四，职业归属感。在国企工作，能够更强烈地感受到自己的工作与国家发展、社会进步的联系，这种职业归属感和成就感是我非常看重的。

当然，我也认识到国企和私企各有优势，选择国企是基于我个人的职业规划和价值观做出的决定。我非常期待能够加入{company}，在国企的平台上实现个人价值。"""

# 题目编号到生成函数的映射
GENERATORS = {
    "1.1": gen_q1_1, "1.2": gen_q1_2, "1.3": gen_q1_3,
    "2.1": gen_q2_1,
    "3.1": gen_q3_1,
    "4.1": gen_q4_1, "4.3": gen_q4_3,
    "5.1": gen_q5_1,
    "7.2": gen_q7_2,
    "8.2": gen_q8_2, "8.4": gen_q8_4,
}

def generate_answer(qid, company, job, ctx):
    """生成指定题目的答案"""
    if qid in GENERATORS:
        return GENERATORS[qid](ctx, company, job)
    else:
        # 未专门编写的题目，用通用模板
        question = ""
        for cat in QUESTION_BANK.values():
            if qid in cat["questions"]:
                question = cat["questions"][qid]
                break
        return f"""关于"{question}"，我的回答如下：

结合我在{ctx['school']}{ctx['major']}专业的学习经历，以及在{ctx['intern_company']}的实习经验，我认为...

（注：此题为通用模板生成，建议根据具体公司和岗位进行针对性修改。）"""

def save_answers(company, job, answers, ctx):
    """按公司存档答案"""
    safe_company = re.sub(r'[\\/:*?"<>|]', '_', company)
    company_dir = os.path.join(ANSWER_DIR, safe_company)
    os.makedirs(company_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"OQ答案_{safe_company}_{job}_{timestamp}.md"
    filepath = os.path.join(company_dir, filename)
    
    content = f"# {company} - {job} 岗位 OQ 开放题答案\n\n"
    content += f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    content += f"> 求职者：{ctx['name']} | 专业：{ctx['major']}\n\n"
    content += "---\n\n"
    
    for qid, (question, answer) in answers.items():
        content += f"## {qid} {question}\n\n{answer}\n\n---\n\n"
    
    with io.open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return filepath

def cmd_list():
    """列出题库"""
    print("=" * 60)
    print("OQ 开放题题库（共8大类）")
    print("=" * 60)
    for cat_id, cat in QUESTION_BANK.items():
        print(f"\n【第{cat_id}类】{cat['name']}")
        for qid, qtext in cat["questions"].items():
            has_gen = "✅" if qid in GENERATORS else "📝"
            print(f"  {has_gen} {qid}: {qtext}")
    print(f"\n✅=已编写针对性生成函数  📝=通用模板生成")
    print(f"\n用法：python oq_generator.py gen --company \"公司名\" --job \"岗位\" --type 1")
    print(f"      python oq_generator.py gen --company \"公司名\" --job \"岗位\" --qid 1.1")

def cmd_gen(args):
    """生成答案"""
    company = args.company
    job = args.job
    ctx = get_user_context(load_profile())
    
    answers = {}
    
    if args.qid:
        # 生成指定题目
        qid = args.qid
        question = ""
        for cat in QUESTION_BANK.values():
            if qid in cat["questions"]:
                question = cat["questions"][qid]
                break
        if not question:
            print(f"错误：找不到题目编号 {qid}")
            sys.exit(1)
        answer = generate_answer(qid, company, job, ctx)
        answers[qid] = (question, answer)
        print(f"已生成: {qid} {question}")
    
    elif args.type:
        # 生成某类所有题目
        cat_id = int(args.type)
        if cat_id not in QUESTION_BANK:
            print(f"错误：找不到第{cat_id}类")
            sys.exit(1)
        cat = QUESTION_BANK[cat_id]
        for qid, qtext in cat["questions"].items():
            answer = generate_answer(qid, company, job, ctx)
            answers[qid] = (qtext, answer)
            print(f"已生成: {qid} {qtext}")
    
    elif args.custom:
        # 自定义题目（用通用模板）
        question = args.custom
        answer = f"""关于"{question}"，我的回答如下：

结合我在{ctx['school']}{ctx['major']}专业的学习经历，以及在{ctx['intern_company']}的实习经验...

（注：此题为自定义题目，使用通用模板生成，建议根据具体情况进行修改。）"""
        answers["custom"] = (question, answer)
        print(f"已生成自定义题目: {question}")
    
    else:
        print("错误：请指定 --type / --qid / --custom 之一")
        sys.exit(1)
    
    # 存档
    filepath = save_answers(company, job, answers, ctx)
    print(f"\n答案已存档: {filepath}")
    
    # 同时输出到控制台
    print("\n" + "=" * 60)
    for qid, (question, answer) in answers.items():
        print(f"\n【{qid}】{question}")
        print("-" * 40)
        print(answer)
        print()

def main():
    parser = argparse.ArgumentParser(description="OQ开放题生成器")
    subparsers = parser.add_subparsers(dest="command")
    
    sub_list = subparsers.add_parser("list", help="列出题库")
    
    sub_gen = subparsers.add_parser("gen", help="生成答案")
    sub_gen.add_argument("--company", required=True, help="公司名称")
    sub_gen.add_argument("--job", required=True, help="岗位名称")
    sub_gen.add_argument("--type", help="生成某类所有题目（1-8）")
    sub_gen.add_argument("--qid", help="生成指定题目（如1.1）")
    sub_gen.add_argument("--custom", help="自定义题目")
    
    args = parser.parse_args()
    
    if args.command == "list":
        cmd_list()
    elif args.command == "gen":
        cmd_gen(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
