# -*- coding: utf-8 -*-
"""
岗位一键处理流水线（prepare pipeline）
串联：抓取JD → 匹配评估 → 生成简历 → 生成OQ → 生成面试题

支持灵活步骤选择：
  --only fetch,rank,resume  # 只做指定步骤
  --skip oq,interview       # 跳过指定步骤

用法：
    python prepare_pipeline.py --url <岗位URL>
    python prepare_pipeline.py --jd-file <JD文本文件> --company "公司名"
    python prepare_pipeline.py --url <URL> --only rank,resume
    python prepare_pipeline.py --url <URL> --skip oq,interview
"""

import os
import sys
import json
import io
import re
from datetime import datetime
from urllib.parse import urlparse


# ============================================================
# 配置
# ============================================================
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
APPLICATIONS_DIR = os.path.join(WORKSPACE_DIR, "applications")

# 步骤定义
STEPS = ['fetch', 'rank', 'resume', 'oq', 'interview']
STEP_NAMES = {
    'fetch': '抓取岗位JD',
    'rank': '匹配评估',
    'resume': '生成简历',
    'oq': '生成OQ答案',
    'interview': '生成面试题',
}


# ============================================================
# 工具函数
# ============================================================
def print_step(step_num, total, step_name, status=''):
    """打印步骤信息"""
    status_str = f" [{status}]" if status else ""
    print(f"\n{'='*60}")
    print(f"  步骤 {step_num}/{total}: {step_name}{status_str}")
    print(f"{'='*60}")


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def load_json_file(path, name="文件"):
    """加载JSON文件"""
    if not os.path.exists(path):
        print(f"  ⚠️  {name}不存在: {path}")
        return None
    try:
        with io.open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  ❌ {name}加载失败: {e}")
        return None


def save_json_file(data, path, name="文件"):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with io.open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 {name}已保存: {os.path.basename(path)}")
        return True
    except Exception as e:
        print(f"  ❌ {name}保存失败: {e}")
        return False


# ============================================================
# 步骤1：抓取岗位JD
# ============================================================
def step_fetch(job_info, context):
    """
    抓取岗位JD
    
    输入：context中的url或jd_text或jd_file
    输出：job_info中的岗位信息
    """
    print("  📡 正在获取岗位信息...")
    
    url = context.get('url', '')
    jd_text = context.get('jd_text', '')
    jd_file = context.get('jd_file', '')
    company = context.get('company', '')
    job_title = context.get('job_title', '')
    
    # 优先从URL抓取
    if url:
        print(f"  🔗 岗位URL: {url}")
        # 检查是否有缓存
        from job_fetcher import CACHE_DIR, detect_platform
        platform = detect_platform(url)
        url_hash = abs(hash(url)) % 100000
        cache_file = os.path.join(CACHE_DIR, f"job_{platform}_{url_hash}.json")
        
        if os.path.exists(cache_file):
            print(f"  📦 使用缓存: {os.path.basename(cache_file)}")
            job_info.update(load_json_file(cache_file, "岗位缓存"))
        else:
            print("  ⚠️  未找到缓存，请先用web.fetch抓取URL内容，然后用--jd-text传入")
            print("  💡 提示：在主agent中调用web.fetch(url)，然后把内容传给prepare")
            # 尝试直接抓取（可能失败，因为很多网站是JS动态加载）
            from job_fetcher import fetch_job
            result = fetch_job(url, use_cache=False)
            if result and result.get('job_description'):
                job_info.update(result)
            else:
                print("  ❌ 直接抓取失败，需要主agent用web.fetch抓取")
                return False
    
    # 从JD文本解析
    elif jd_text:
        print(f"  📝 JD文本长度: {len(jd_text)} 字符")
        from job_fetcher import parse_jd_text
        result = parse_jd_text(jd_text, company=company, job_title=job_title, url=url)
        job_info.update(result)
    
    # 从JD文件读取
    elif jd_file:
        print(f"  📄 JD文件: {jd_file}")
        if os.path.exists(jd_file):
            with io.open(jd_file, encoding='utf-8') as f:
                jd_text = f.read()
            from job_fetcher import parse_jd_text
            result = parse_jd_text(jd_text, company=company, job_title=job_title)
            job_info.update(result)
        else:
            print(f"  ❌ JD文件不存在: {jd_file}")
            return False
    
    else:
        print("  ❌ 未提供岗位信息（需要--url或--jd-text或--jd-file）")
        return False
    
    # 确保有公司名和岗位名
    if not job_info.get('company'):
        job_info['company'] = company or '未知公司'
    if not job_info.get('job_title'):
        job_info['job_title'] = job_title or '未知岗位'
    
    # 保存岗位信息到公司文件夹
    company_safe = sanitize_filename(job_info['company'])
    job_dir = os.path.join(APPLICATIONS_DIR, "01_岗位匹配报告")
    job_info_path = os.path.join(job_dir, f"{company_safe}_{job_info['job_title']}_岗位信息.json")
    save_json_file(job_info, job_info_path, "岗位信息")
    
    print(f"\n  ✅ 岗位信息获取完成:")
    print(f"    公司: {job_info.get('company')}")
    print(f"    岗位: {job_info.get('job_title')}")
    print(f"    薪资: {job_info.get('salary', '未提取')}")
    print(f"    地点: {job_info.get('city', '未提取')}")
    
    return True


# ============================================================
# 步骤2：匹配评估
# ============================================================
def step_rank(job_info, context):
    """匹配评估"""
    print("  📊 正在进行匹配评估...")
    
    company = job_info.get('company', '未知公司')
    job_title = job_info.get('job_title', '未知岗位')
    jd_text = job_info.get('job_description', '') or job_info.get('raw_text', '')
    
    if not jd_text:
        print("  ⚠️  没有JD文本，跳过匹配评估")
        return True
    
    # 调用match_engine进行匹配评估
    try:
        # 读取简历数据
        resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
        resume_data = load_json_file(resume_path, "简历数据")
        if not resume_data:
            print("  ⚠️  简历数据不存在，跳过匹配评估")
            return True
        
        # 简单匹配评估（基于关键词）
        score = calculate_match_score(resume_data, job_info)
        job_info['match_score'] = score
        
        print(f"\n  ✅ 匹配评估完成: {score} 分")
        print(f"    （详细匹配报告需要调用match_engine.py生成HTML）")
        
    except Exception as e:
        print(f"  ⚠️  匹配评估出错: {e}")
    
    return True


def calculate_match_score(resume_data, job_info):
    """简单匹配评分（基于关键词）"""
    score = 60.0  # 基础分
    
    jd_text = (job_info.get('job_description', '') + job_info.get('raw_text', '')).lower()
    
    # 专业匹配
    education = resume_data.get('教育背景', [])
    for edu in education:
        major = edu.get('major', edu.get('专业', '')).lower()
        if major and major in jd_text:
            score += 10
            break
    
    # 技能匹配
    skills = resume_data.get('技能清单', {})
    skill_text = ' '.join(str(v) for v in skills.values()).lower()
    matched_skills = 0
    for skill in ['python', 'sql', 'arcgis', 'cass', 'cad', '全站仪', 'gps', '无人机']:
        if skill in skill_text and skill in jd_text:
            matched_skills += 1
    score += min(matched_skills * 3, 15)
    
    # 经验匹配
    experience = resume_data.get('实习经历', [])
    if experience:
        score += 5
    
    # 地点匹配
    city = resume_data.get('基本信息', {}).get('city', '')
    job_city = job_info.get('city', '')
    if city and job_city and city in job_city:
        score += 5
    
    return round(min(score, 100), 1)


# ============================================================
# 步骤3：生成简历
# ============================================================
def step_resume(job_info, context):
    """生成简历"""
    print("  📄 正在生成简历...")
    
    # 优先使用context中的company（用户指定的），然后用job_info中的
    company = context.get('company') or job_info.get('company', '未知公司')
    company_safe = sanitize_filename(company)
    
    # 输出目录
    output_dir = os.path.join(APPLICATIONS_DIR, "02_简历", f"{company_safe}_简历")
    os.makedirs(output_dir, exist_ok=True)
    
    # 简历数据文件
    resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
    if not os.path.exists(resume_path):
        print("  ⚠️  简历数据不存在，跳过简历生成")
        return True
    
    # 调用generate_selected生成简历
    try:
        import generate_selected
        original_argv = sys.argv
        sys.argv = ['generate_selected.py', resume_path, output_dir]
        generate_selected.main()
        sys.argv = original_argv
        
        print(f"\n  ✅ 简历生成完成:")
        print(f"    输出目录: {output_dir}")
        # 列出生成的文件
        files = os.listdir(output_dir)
        html_files = [f for f in files if f.endswith('.html')]
        pdf_files = [f for f in files if f.endswith('.pdf')]
        print(f"    HTML简历: {len(html_files)} 份")
        print(f"    PDF简历: {len(pdf_files)} 份")
        
    except Exception as e:
        print(f"  ❌ 简历生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


# ============================================================
# 步骤4：生成OQ答案
# ============================================================
def step_oq(job_info, context):
    """生成OQ答案"""
    print("  📝 正在生成OQ答案...")
    
    # 优先使用context中的company
    company = context.get('company') or job_info.get('company', '未知公司')
    company_safe = sanitize_filename(company)
    
    # 输出目录
    output_dir = os.path.join(WORKSPACE_DIR, "oq_answers", company_safe)
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查是否有application_profile.json
    profile_path = os.path.join(WORKSPACE_DIR, "application_profile.json")
    if not os.path.exists(profile_path):
        print("  ⚠️  application_profile.json不存在，跳过OQ生成")
        print("  💡 提示：OQ生成需要个人信息底座，请先运行 campus profile 初始化")
        return True
    
    print(f"  📋 公司: {company}")
    print(f"  📂 输出目录: {output_dir}")
    print(f"  ⚠️  OQ答案需要AI动态生成，请在主agent中根据岗位JD和个人信息生成")
    print(f"  💡 提示：可以参考 oq_kb.py 的模板，生成8个常见OQ答案")
    
    # 生成OQ模板文件（供主agent填充）
    oq_template = {
        "company": company,
        "job_title": job_info.get('job_title', ''),
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "questions": [
            {"id": "zy_001", "question": "请做一个自我介绍", "answer": ""},
            {"id": "zy_002", "question": "为什么选择我们公司？", "answer": ""},
            {"id": "zy_003", "question": "你的职业规划是什么？", "answer": ""},
            {"id": "zy_004", "question": "你的优缺点是什么？", "answer": ""},
            {"id": "zy_005", "question": "你遇到的最大困难是什么？如何解决的？", "answer": ""},
            {"id": "zy_006", "question": "为什么选择这个专业？", "answer": ""},
            {"id": "zy_007", "question": "能接受出差/加班吗？", "answer": ""},
            {"id": "zy_008", "question": "你的薪资期望是多少？", "answer": ""},
        ]
    }
    
    template_path = os.path.join(output_dir, "oq_template.json")
    save_json_file(oq_template, template_path, "OQ模板")
    
    print(f"\n  ✅ OQ模板已生成，请在主agent中填充答案")
    
    return True


# ============================================================
# 步骤5：生成面试题
# ============================================================
def step_interview(job_info, context):
    """生成面试题"""
    print("  🎯 正在生成面试题...")
    
    # 优先使用context中的company和job_title
    company = context.get('company') or job_info.get('company', '未知公司')
    job_title = context.get('job_title') or job_info.get('job_title', '未知岗位')
    company_safe = sanitize_filename(company)
    
    # 输出目录
    output_dir = os.path.join(APPLICATIONS_DIR, "03_面试题库")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{company_safe}_{job_title}_面试题库.html")
    
    print(f"  📋 公司: {company}")
    print(f"  📋 岗位: {job_title}")
    print(f"  📂 输出文件: {os.path.basename(output_file)}")
    print(f"  ⚠️  面试题需要AI动态生成，请在主agent中根据岗位JD和个人经历生成")
    print(f"  💡 提示：可以参考 interview.py 的模板，生成6大类面试题")
    
    # 生成面试题模板文件（供主agent填充）
    interview_template = {
        "company": company,
        "job_title": job_title,
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "categories": [
            {"name": "通用面试题", "questions": []},
            {"name": "专业技术题", "questions": []},
            {"name": "实习经历深挖", "questions": []},
            {"name": "项目经历深挖", "questions": []},
            {"name": "行为面试题", "questions": []},
            {"name": "岗位认知情景题", "questions": []},
        ]
    }
    
    template_path = os.path.join(output_dir, f"{company_safe}_{job_title}_面试题模板.json")
    save_json_file(interview_template, template_path, "面试题模板")
    
    print(f"\n  ✅ 面试题模板已生成，请在主agent中填充题目和答案要点")
    
    return True


# ============================================================
# 主流水线
# ============================================================
def run_pipeline(url='', jd_text='', jd_file='', company='', job_title='',
                 only_steps=None, skip_steps=None):
    """
    运行岗位一键处理流水线
    
    Args:
        url: 岗位URL
        jd_text: JD文本
        jd_file: JD文件路径
        company: 公司名
        job_title: 岗位名
        only_steps: 只执行指定步骤（列表）
        skip_steps: 跳过指定步骤（列表）
    
    Returns:
        dict: 处理结果
    """
    # 确定要执行的步骤
    if only_steps:
        steps_to_run = [s for s in STEPS if s in only_steps]
    elif skip_steps:
        steps_to_run = [s for s in STEPS if s not in skip_steps]
    else:
        steps_to_run = STEPS
    
    # 上下文
    context = {
        'url': url,
        'jd_text': jd_text,
        'jd_file': jd_file,
        'company': company,
        'job_title': job_title,
    }
    
    # 岗位信息
    job_info = {}
    
    # 步骤执行函数映射
    step_functions = {
        'fetch': step_fetch,
        'rank': step_rank,
        'resume': step_resume,
        'oq': step_oq,
        'interview': step_interview,
    }
    
    print("\n" + "="*60)
    print("  🚀 岗位一键处理流水线")
    print("="*60)
    print(f"\n  执行步骤: {' → '.join(STEP_NAMES[s] for s in steps_to_run)}")
    if url:
        print(f"  岗位URL: {url}")
    if company:
        print(f"  公司: {company}")
    if job_title:
        print(f"  岗位: {job_title}")
    
    # 执行步骤
    results = {}
    for i, step in enumerate(steps_to_run, 1):
        print_step(i, len(steps_to_run), STEP_NAMES[step])
        
        try:
            success = step_functions[step](job_info, context)
            results[step] = 'success' if success else 'failed'
            if not success:
                print(f"\n  ❌ 步骤失败: {STEP_NAMES[step]}")
                # 不中断，继续执行后续步骤
        except Exception as e:
            print(f"\n  ❌ 步骤出错: {e}")
            import traceback
            traceback.print_exc()
            results[step] = 'error'
    
    # 汇总
    print("\n" + "="*60)
    print("  📊 处理结果汇总")
    print("="*60)
    for step in steps_to_run:
        status = results.get(step, 'unknown')
        status_icon = '✅' if status == 'success' else '❌'
        print(f"  {status_icon} {STEP_NAMES[step]}: {status}")
    
    # 保存处理结果
    if job_info.get('company'):
        company_safe = sanitize_filename(job_info['company'])
        result_path = os.path.join(APPLICATIONS_DIR, "01_岗位匹配报告", 
                                    f"{company_safe}_{job_info.get('job_title', '')}_处理结果.json")
        save_json_file({
            'job_info': job_info,
            'results': results,
            'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }, result_path, "处理结果")
    
    print(f"\n  🎉 流水线执行完成!")
    print(f"  💡 提示：OQ答案和面试题需要在主agent中根据模板填充")
    
    return {
        'job_info': job_info,
        'results': results,
    }


# ============================================================
# 命令行入口
# ============================================================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='岗位一键处理流水线')
    parser.add_argument('--url', help='岗位URL')
    parser.add_argument('--jd-text', help='JD文本')
    parser.add_argument('--jd-file', help='JD文件路径')
    parser.add_argument('--company', help='公司名')
    parser.add_argument('--job-title', help='岗位名')
    parser.add_argument('--only', help='只执行指定步骤（逗号分隔，如 fetch,rank,resume）')
    parser.add_argument('--skip', help='跳过指定步骤（逗号分隔，如 oq,interview）')
    
    args = parser.parse_args()
    
    # 解析步骤
    only_steps = args.only.split(',') if args.only else None
    skip_steps = args.skip.split(',') if args.skip else None
    
    # 运行流水线
    result = run_pipeline(
        url=args.url,
        jd_text=args.jd_text,
        jd_file=args.jd_file,
        company=args.company,
        job_title=args.job_title,
        only_steps=only_steps,
        skip_steps=skip_steps,
    )
