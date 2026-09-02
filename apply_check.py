#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网申机筛质量检查器（apply_check）
针对网申信息底座 application_profile.json 做多维度检查，
复用 check_resume 的简历检查能力，新增国企机筛关键词、网申特有字段校验。
输出统一主题 HTML 检查报告（问题清单 + 修改建议）。

用法:
    python apply_check.py                           # 检查 application_profile.json
    python apply_check.py --jd job_desc.txt         # 含目标岗位JD的ATS关键词覆盖检查
    python apply_check.py other_profile.json        # 检查指定文件
"""
import json, io, os, sys, re, html as html_mod
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WS)

import check_resume as cr
import report_theme as T

DEFAULT_PROFILE = os.path.join(WS, "application_profile.json")
OUTPUT_DIR = os.path.join(WS, "applications")

# ============================================================
# 网申特有检查函数（每个返回 {'issues':[], 'warnings':[], 'passed':[]}）
# ============================================================

def _empty_result():
    return {"issues": [], "warnings": [], "passed": []}


def adapt_to_check_resume(profile):
    """把 application_profile（中文key）转换成 check_resume 期望的格式（英文key）。
    check_resume 的8个检查函数读取英文字段名，而网申信息底座用中文名，需适配。"""
    adapted = {}

    # 基本信息（check_resume 读取英文key: name/phone/email/job_intention/city/avatar）
    basic = profile.get("基本信息", {})
    adapted["基本信息"] = {
        "name": basic.get("姓名", ""),
        "phone": basic.get("手机", basic.get("电话", "")),
        "email": basic.get("邮箱", ""),
        "job_intention": basic.get("求职意向", ""),
        "city": basic.get("现居住地", basic.get("所在城市", basic.get("现居城市", ""))),
        "avatar": basic.get("证件照", basic.get("头像", "")),
        "性别": basic.get("性别", ""),
    }

    # 教育背景
    edu_list = []
    for edu in profile.get("教育背景", []):
        edu_list.append({
            "school": edu.get("学校", ""),
            "major": edu.get("专业", ""),
            "degree": edu.get("学历", ""),
            "start_date": edu.get("入学时间", edu.get("开始时间", "")),
            "end_date": edu.get("毕业时间", edu.get("结束时间", "")),
            "gpa": edu.get("GPA", edu.get("gpa", "")),
            "courses": edu.get("主修课程", edu.get("课程", "")),
        })
    adapted["教育背景"] = edu_list

    # 实习经历
    def _to_desc_list(raw):
        if isinstance(raw, list):
            return [str(d).strip() for d in raw if str(d).strip()]
        if isinstance(raw, str) and raw.strip():
            return [d.strip() for d in re.split(r'\n|;|；', raw) if d.strip()]
        return []

    exp_list = []
    for exp in profile.get("实习经历", []):
        exp_list.append({
            "company": exp.get("单位名称", exp.get("公司", "")),
            "position": exp.get("岗位", exp.get("岗位名称", exp.get("职位", ""))),
            "start_date": exp.get("入职时间", exp.get("开始时间", "")),
            "end_date": exp.get("离职时间", exp.get("结束时间", "")),
            "description": _to_desc_list(exp.get("工作内容", exp.get("工作描述", exp.get("描述", "")))),
        })
    adapted["实习经历"] = exp_list

    # 项目经历
    proj_list = []
    for proj in profile.get("项目经历", []):
        proj_list.append({
            "name": proj.get("项目名称", proj.get("名称", "")),
            "role": proj.get("担任角色", proj.get("角色", "")),
            "start_date": proj.get("开始时间", ""),
            "end_date": proj.get("结束时间", ""),
            "description": _to_desc_list(proj.get("项目描述", proj.get("描述", ""))),
        })
    adapted["项目经历"] = proj_list

    # 技能清单：合并专业技能和技能证书（check_skills 读取"技能清单"）
    skill_dict = {}
    prof_skills = profile.get("专业技能", {})
    if isinstance(prof_skills, dict):
        for cat, lst in prof_skills.items():
            if isinstance(lst, list) and lst:
                skill_dict[str(cat)] = [str(s) for s in lst]
    certs = profile.get("技能证书", {})
    if isinstance(certs, dict):
        for cat, lst in certs.items():
            if isinstance(lst, list) and lst:
                names = []
                for item in lst:
                    if isinstance(item, dict):
                        names.append(item.get("名称", str(item)))
                    else:
                        names.append(str(item))
                if names:
                    skill_dict[f"证书·{cat}"] = names
    adapted["技能清单"] = skill_dict

    # 其余块直接透传
    adapted["专业技能"] = profile.get("专业技能", {})
    adapted["技能证书"] = profile.get("技能证书", {})
    adapted["获奖经历"] = profile.get("获奖经历", [])
    adapted["自我评价"] = profile.get("自我评价", [])

    return adapted


def check_id_card(data):
    """身份证号格式校验（18位，校验位）"""
    r = _empty_result()
    basic = data.get("基本信息", {})
    id_num = str(basic.get("身份证号", "") or basic.get("id_card", "") or "").strip()
    if not id_num:
        r["warnings"].append("未填写身份证号（国企网申必填）")
        return r
    if not re.match(r"^\d{17}[\dXx]$", id_num):
        r["issues"].append(f"身份证号格式错误：{id_num}（应为18位，末位可为X）")
        return r
    # 校验位验证
    weights = [7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4]
    check_codes = "10X98765432"
    try:
        total = sum(int(id_num[i]) * weights[i] for i in range(17))
        expected = check_codes[total % 11]
        if id_num[17].upper() != expected:
            r["issues"].append(f"身份证号校验位错误：{id_num}（末位应为{expected}）")
        else:
            r["passed"].append("身份证号格式与校验位正确")
            # 提取出生日期和性别
            birth = f"{id_num[6:10]}-{id_num[10:12]}-{id_num[12:14]}"
            gender = "男" if int(id_num[16]) % 2 == 1 else "女"
            r["passed"].append(f"身份证解析：出生日期{birth}，性别{gender}")
    except Exception:
        r["warnings"].append("身份证号校验位计算失败，请人工核对")
    return r


def check_contact_format(data):
    """手机号、邮箱格式校验"""
    r = _empty_result()
    basic = data.get("基本信息", {})
    phone = str(basic.get("电话", "") or basic.get("手机", "") or basic.get("phone", "") or "").strip()
    email = str(basic.get("邮箱", "") or basic.get("email", "") or "").strip()

    if phone:
        if re.match(r"^1[3-9]\d{9}$", phone):
            r["passed"].append("手机号格式正确")
        else:
            r["issues"].append(f"手机号格式错误：{phone}（应为11位，1开头）")
    else:
        r["issues"].append("未填写手机号（网申必填）")

    if email:
        if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            r["passed"].append("邮箱格式正确")
        else:
            r["issues"].append(f"邮箱格式错误：{email}")
    else:
        r["issues"].append("未填写邮箱（网申必填）")
    return r


def check_soe_keywords(data):
    """国企机筛关键词核查（党员/四六级/学生干部/办公软件/属地偏好/服从安排）"""
    r = _empty_result()
    basic = data.get("基本信息", {})
    certs = data.get("技能证书", {})
    awards = data.get("获奖经历", [])
    projects = data.get("项目经历", [])
    self_eval = " ".join(data.get("自我评价", []) or [])
    skills = data.get("专业技能", {})
    skills_text = json.dumps(skills, ensure_ascii=False) if isinstance(skills, dict) else str(skills)
    all_text = self_eval + " " + skills_text + " " + json.dumps(awards, ensure_ascii=False) + " " + json.dumps(projects, ensure_ascii=False)

    # 1. 政治面貌
    politics = str(basic.get("政治面貌", "") or "").strip()
    if politics in ["党员", "中共党员", "预备党员"]:
        r["passed"].append(f"政治面貌：{politics}（国企加分项）")
    elif politics:
        r["warnings"].append(f"政治面貌为'{politics}'，部分国企岗位偏好党员/预备党员")
    else:
        r["warnings"].append("未填写政治面貌（国企网申常问，建议如实填写）")

    # 2. 英语四六级
    lang = certs.get("语言能力", []) if isinstance(certs, dict) else []
    has_cet4 = any("四级" in str(x.get("名称", "")) for x in lang if isinstance(x, dict))
    has_cet6 = any("六级" in str(x.get("名称", "")) for x in lang if isinstance(x, dict))
    if has_cet6:
        r["passed"].append("已通过英语六级（国企普遍要求四级，六级加分）")
    elif has_cet4:
        r["passed"].append("已通过英语四级（满足多数国企基本要求）")
        r["warnings"].append("仅有四级，部分优质国企岗位要求六级，如有机会建议考取")
    else:
        r["warnings"].append("未填写英语四六级证书（多数国企网申要求至少四级，建议补充或说明）")

    # 3. 学生干部经历
    has_cadre = any(kw in all_text for kw in ["班长", "团支书", "学生会", "部长", "主席", "委员", "社长", "会长", "团支书", "学习委员", "生活委员"])
    if has_cadre:
        r["passed"].append("有学生干部经历（国企机筛加分项）")
    else:
        r["warnings"].append("未体现学生干部经历（国企偏好，如有请补充到获奖/项目经历中）")

    # 4. 熟练办公软件
    has_office = any(kw in all_text.lower() for kw in ["office", "excel", "word", "ppt", "办公软件", "wps", "熟练办公"])
    if has_office:
        r["passed"].append("已体现办公软件能力（国企机筛关键词）")
    else:
        r["warnings"].append("未体现'熟练办公软件/Office/Excel'等关键词（国企机筛常查，建议在技能或自我评价中补充）")

    # 5. 服从安排/长期发展/踏实负责
    has_attitude = any(kw in all_text for kw in ["服从", "踏实", "负责", "长期", "稳定", "吃苦耐劳", "责任心", "抗压"])
    if has_attitude:
        r["passed"].append("自我评价含'服从/踏实/负责/稳定'等国企偏好表达")
    else:
        r["warnings"].append("自我评价未体现'服从安排/踏实负责/长期稳定'等表达（国企偏好，建议补充）")

    # 6. 籍贯/生源地
    hometown = str(basic.get("籍贯", "") or basic.get("生源地", "") or "").strip()
    if hometown:
        r["passed"].append(f"已填写籍贯/生源地：{hometown}")
    else:
        r["warnings"].append("未填写籍贯/生源地（国企网申常问，属地偏好稳定）")

    # 7. 期望城市/服从调剂
    expect_city = str(basic.get("期望城市", "") or basic.get("意向城市", "") or "").strip()
    if expect_city:
        r["passed"].append(f"已填写期望城市：{expect_city}")
    else:
        r["warnings"].append("未填写期望城市/意向地（建议填写，或注明'服从调剂/城市不限'）")

    return r


def check_family_members(data):
    """家庭成员及社会关系完整性"""
    r = _empty_result()
    members = data.get("家庭成员及社会关系", [])
    if not members:
        r["issues"].append("未填写家庭成员及社会关系（国企网申必填，通常至少填父母）")
        return r
    r["passed"].append(f"已填写 {len(members)} 位家庭成员")
    for i, m in enumerate(members, 1):
        name = str(m.get("姓名", "") or "").strip()
        relation = str(m.get("称谓", "") or m.get("关系", "") or "").strip()
        if not name:
            r["warnings"].append(f"第{i}位家庭成员未填写姓名")
        if not relation:
            r["warnings"].append(f"第{i}位家庭成员未填写称谓/关系")
        # 工作单位
        work = str(m.get("工作单位", "") or m.get("单位", "") or "").strip()
        if not work:
            r["warnings"].append(f"{relation or '第'+str(i)+'位'} {name or ''} 未填写工作单位（无单位可填'无/务农/个体'）")
    return r


def check_emergency_contact(data):
    """紧急联系人完整性"""
    r = _empty_result()
    ec = data.get("紧急联系人", {})
    if not ec:
        r["issues"].append("未填写紧急联系人（国企网申必填）")
        return r
    name = str(ec.get("姓名", "") or "").strip()
    relation = str(ec.get("关系", "") or ec.get("称谓", "") or "").strip()
    phone = str(ec.get("电话", "") or ec.get("手机", "") or "").strip()
    if name:
        r["passed"].append(f"紧急联系人姓名：{name}")
    else:
        r["issues"].append("紧急联系人未填写姓名")
    if relation:
        r["passed"].append(f"与本人关系：{relation}")
    else:
        r["warnings"].append("紧急联系人未填写与本人关系")
    if phone:
        if re.match(r"^1[3-9]\d{9}$", phone):
            r["passed"].append("紧急联系人电话格式正确")
        else:
            r["issues"].append(f"紧急联系人电话格式错误：{phone}")
    else:
        r["issues"].append("紧急联系人未填写电话")
    return r


def check_attachments(data):
    """附件材料完整性（证件照/成绩单/就业推荐表等）"""
    r = _empty_result()
    att = data.get("附件材料", {})
    if not att:
        r["warnings"].append("未配置附件材料清单（建议准备证件照、成绩单、就业推荐表）")
        return r
    for key, val in att.items():
        if val:
            r["passed"].append(f"{key}：已准备")
        else:
            r["warnings"].append(f"{key}：未准备（国企网申可能需要上传，建议提前准备）")
    return r


def check_net_application_specific(data):
    """网申特有字段：身高/体重/婚姻状况/期望薪资等"""
    r = _empty_result()
    basic = data.get("基本信息", {})
    for field, label in [("身高", "身高"), ("体重", "体重"), ("婚姻状况", "婚姻状况"),
                          ("期望薪资", "期望薪资"), ("民族", "民族")]:
        val = str(basic.get(field, "") or "").strip()
        if val:
            r["passed"].append(f"{label}：{val}")
        else:
            r["warnings"].append(f"未填写{label}（部分国企网申必填）")
    return r


# ============================================================
# 主检查流程
# ============================================================

def run_all_checks(data, jd_text=None):
    """执行所有检查，返回结果字典"""
    results = {}

    # 适配成 check_resume 期望的字段格式（中文key→英文key）
    adapted = adapt_to_check_resume(data)

    # 复用 check_resume 的8项检查（用适配后的数据）
    results["个人信息"] = cr.check_personal_info(adapted)
    results["教育背景"] = cr.check_education(adapted)
    results["实习经历"] = cr.check_experience(adapted)
    results["项目经历"] = cr.check_projects(adapted)
    results["技能清单"] = cr.check_skills(adapted)
    results["时间线"] = cr.check_timeline(adapted)
    results["错别字表述"] = cr.check_typos(adapted)
    results["量化成果"] = cr.check_quantification(adapted)

    # 网申特有检查
    results["身份证校验"] = check_id_card(data)
    results["联系方式"] = check_contact_format(data)
    results["国企机筛关键词"] = check_soe_keywords(data)
    results["家庭成员"] = check_family_members(data)
    results["紧急联系人"] = check_emergency_contact(data)
    results["附件材料"] = check_attachments(data)
    results["网申特有字段"] = check_net_application_specific(data)

    # JD关键词覆盖（可选，用适配后的数据）
    jd_result = None
    if jd_text:
        jd_result = cr.check_jd_keywords(adapted, jd_text)

    # 页数估算（用适配后的数据）
    page_result = cr.estimate_pages(adapted)

    return results, jd_result, page_result


# ============================================================
# 统一主题报告生成
# ============================================================

def generate_check_report(data, results, jd_result, page_result, output_path):
    """用统一主题生成检查报告HTML"""
    name = data.get("基本信息", {}).get("姓名", "网申信息")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 统计
    total_issues = sum(len(r["issues"]) for r in results.values())
    total_warnings = sum(len(r["warnings"]) for r in results.values())
    total_passed = sum(len(r["passed"]) for r in results.values())
    total_checks = len(results)

    # 风险等级
    if total_issues == 0 and total_warnings <= 3:
        risk_level, risk_color, risk_icon = "优秀", "#52c41a", "✅"
    elif total_issues <= 2 and total_warnings <= 8:
        risk_level, risk_color, risk_icon = "良好", "#1890ff", "👍"
    elif total_issues <= 5:
        risk_level, risk_color, risk_icon = "需改进", "#faad14", "⚠️"
    else:
        risk_level, risk_color, risk_icon = "问题较多", "#ff4d4f", "❌"

    # 统计卡
    stats_html = T.stat_grid([
        (str(total_checks), "检查维度"),
        (str(total_issues), "❌ 问题", "#ff4d4f"),
        (str(total_warnings), "⚠️ 警告", "#faad14"),
        (str(total_passed), "✅ 通过", "#52c41a"),
        (risk_level, "综合评级", risk_color),
        (f"{page_result['pages']:.1f}", "预计页数"),
    ])

    # 各维度详情
    sections_html = ""
    for dim_name, res in results.items():
        issues = res["issues"]
        warnings = res["warnings"]
        passed = res["passed"]
        if not issues and not warnings and not passed:
            continue
        dim_icon = "❌" if issues else ("⚠️" if warnings else "✅")
        title = f"{dim_icon} {dim_name}"
        body = ""
        if issues:
            body += '<div style="margin-bottom:8px;"><div style="font-size:12px;font-weight:600;color:#ff4d4f;margin-bottom:4px;">必须修改</div>'
            for item in issues:
                body += f'<div style="font-size:12px;color:#cf1322;padding:3px 0;padding-left:12px;border-left:3px solid #ff4d4f;margin:2px 0;">{T.esc(item)}</div>'
            body += "</div>"
        if warnings:
            body += '<div style="margin-bottom:8px;"><div style="font-size:12px;font-weight:600;color:#faad14;margin-bottom:4px;">建议优化</div>'
            for item in warnings:
                body += f'<div style="font-size:12px;color:#d46b08;padding:3px 0;padding-left:12px;border-left:3px solid #faad14;margin:2px 0;">{T.esc(item)}</div>'
            body += "</div>"
        if passed:
            body += '<div><div style="font-size:12px;font-weight:600;color:#52c41a;margin-bottom:4px;">已达标</div>'
            for item in passed:
                body += f'<div style="font-size:12px;color:#389e0d;padding:3px 0;padding-left:12px;border-left:3px solid #52c41a;margin:2px 0;">{T.esc(item)}</div>'
            body += "</div>"
        sections_html += f'<div class="check-section" style="margin-bottom:16px;">{T.section_title(title)}{body}</div>'

    # JD关键词覆盖（如有）
    jd_section = ""
    if jd_result:
        cov = jd_result.get("coverage", 0)
        matched = jd_result.get("matched", [])
        missing = jd_result.get("missing", [])
        cov_color = "#52c41a" if cov >= 70 else ("#faad14" if cov >= 50 else "#ff4d4f")
        body = f'<div style="margin-bottom:10px;"><span style="font-size:24px;font-weight:700;color:{cov_color};">{cov}%</span><span style="font-size:12px;color:#888;margin-left:8px;">ATS关键词覆盖率（目标≥70%）</span></div>'
        if matched:
            body += '<div style="margin-bottom:8px;"><div style="font-size:12px;font-weight:600;color:#52c41a;margin-bottom:4px;">已覆盖关键词</div><div style="display:flex;flex-wrap:wrap;gap:5px;">'
            for kw in matched[:20]:
                body += f'<span style="font-size:11px;background:#f6ffed;color:#389e0d;padding:2px 8px;border-radius:10px;">{T.esc(kw)}</span>'
            body += "</div></div>"
        if missing:
            body += '<div><div style="font-size:12px;font-weight:600;color:#ff4d4f;margin-bottom:4px;">缺失关键词（建议在简历/自我评价中补充）</div><div style="display:flex;flex-wrap:wrap;gap:5px;">'
            for kw in missing[:20]:
                body += f'<span style="font-size:11px;background:#fff2f0;color:#cf1322;padding:2px 8px;border-radius:10px;">{T.esc(kw)}</span>'
            body += "</div></div>"
        jd_section = f'<div class="check-section" style="margin-bottom:16px;">{T.section_title("🎯 目标岗位ATS关键词覆盖")}{body}</div>'

    # 修改建议汇总
    suggestions = []
    if total_issues > 0:
        suggestions.append(f"优先修复 {total_issues} 个'必须修改'项（红色标记），这些可能直接导致网申被拒")
    if total_warnings > 5:
        suggestions.append(f"建议优化 {total_warnings} 个'建议优化'项，提升机筛通过率")
    soe_res = results.get("国企机筛关键词", {})
    if soe_res.get("warnings"):
        suggestions.append("国企机筛关键词有缺失，建议在自我评价和技能中补充'党员/四六级/学生干部/熟练办公软件/服从安排'等")
    if jd_result and jd_result.get("coverage", 0) < 70:
        suggestions.append(f"ATS关键词覆盖率仅{jd_result['coverage']}%，建议针对目标JD补充缺失关键词")
    suggestions.append("修改后重新运行本检查，直到综合评级达到'良好'以上")

    sug_body = '<ol style="margin:0;padding-left:20px;">'
    for s in suggestions:
        sug_body += f'<li style="font-size:13px;color:#333;margin:5px 0;line-height:1.6;">{T.esc(s)}</li>'
    sug_body += "</ol>"
    sug_section = f'<div class="check-section" style="margin-bottom:16px;">{T.section_title("📋 修改建议与行动清单")}{sug_body}</div>'

    # 组装页面
    subtitle = f"检查对象：{name} | 检查时间：{now} | 共{total_checks}个维度"
    content = stats_html + sections_html + jd_section + sug_section
    html = T.page(f"🔍 网申机筛质量检查报告", subtitle, content)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with io.open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# ============================================================
# 主函数
# ============================================================

def main():
    profile_path = DEFAULT_PROFILE
    jd_path = None
    output_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--jd" and i + 1 < len(args):
            jd_path = args[i + 1]
            i += 2
        elif args[i] == "-o" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i].endswith(".json"):
            profile_path = args[i]
            i += 1
        else:
            i += 1

    if not os.path.exists(profile_path):
        print(f"错误: 网申信息文件不存在: {profile_path}")
        sys.exit(1)

    print(f"加载网申信息: {profile_path}")
    with io.open(profile_path, encoding="utf-8") as f:
        data = json.load(f)

    jd_text = None
    if jd_path and os.path.exists(jd_path):
        print(f"加载目标JD: {jd_path}")
        with io.open(jd_path, encoding="utf-8") as f:
            jd_text = f.read()

    print("执行网申机筛质量检查...")
    results, jd_result, page_result = run_all_checks(data, jd_text)

    total_issues = sum(len(r["issues"]) for r in results.values())
    total_warnings = sum(len(r["warnings"]) for r in results.values())
    total_passed = sum(len(r["passed"]) for r in results.values())

    print()
    print("=" * 55)
    print("  网申机筛质量检查完成")
    print("=" * 55)
    print(f"  检查维度: {len(results)} 个")
    print(f"  ❌ 必须修改: {total_issues} 个")
    print(f"  ⚠️  建议优化: {total_warnings} 个")
    print(f"  ✅ 已达标: {total_passed} 项")
    print(f"  📄 预计页数: {page_result['pages']:.1f} 页")
    if jd_result:
        print(f"  🎯 ATS关键词覆盖: {jd_result['coverage']}%")
    print("=" * 55)

    if not output_path:
        name = data.get("基本信息", {}).get("姓名", "网申信息")
        output_path = os.path.join(OUTPUT_DIR, f"{name}_网申机筛检查报告.html")

    generate_check_report(data, results, jd_result, page_result, output_path)
    print(f"\n报告已生成: {output_path}")
    print("\n使用方法:")
    print("  python apply_check.py                         # 基础检查")
    print("  python apply_check.py --jd job_desc.txt       # 含目标岗位ATS关键词检查")
    print("  python apply_check.py other_profile.json      # 检查指定文件")


if __name__ == "__main__":
    main()
