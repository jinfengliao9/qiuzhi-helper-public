# -*- coding: utf-8 -*-
"""
岗位处理流水线
功能：导入抓取岗位 → 批量匹配评估 → 生成推荐报告

用法:
    python job_pipeline.py import    # 导入 scraped_jobs.json 到岗位库
    python job_pipeline.py rank      # 对未评估岗位批量匹配评估
    python job_pipeline.py report    # 生成岗位推荐报告
    python job_pipeline.py all       # 全部执行（导入→匹配→报告）
"""

import json
import os
import sys
import html as html_module
from datetime import datetime

# 导入 job_collector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from job_collector import JobCollector
from jd_parser import parse_job_detail, extract_basic_info
from match_engine import calculate_match

# 导入 rank.py 的函数
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rank import parse_jd, evaluate_match, load_resume_data


def escape(text):
    if not text:
        return ''
    return html_module.escape(str(text))


def import_scraped_jobs(collector, scraped_file=None):
    """导入抓取到的岗位到岗位库"""
    if scraped_file is None:
        scraped_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraped_jobs.json')
    
    if not os.path.exists(scraped_file):
        print(f'错误: 抓取文件不存在: {scraped_file}')
        return 0
    
    with open(scraped_file, 'r', encoding='utf-8') as f:
        scraped_jobs = json.load(f)
    
    print(f'读取到 {len(scraped_jobs)} 个抓取岗位')
    
    # 去重：基于公司名+岗位名
    seen = set()
    unique_jobs = []
    for job in scraped_jobs:
        key = (job.get('company', '').strip(), job.get('position', '').strip())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    if len(unique_jobs) < len(scraped_jobs):
        print(f'去重: {len(scraped_jobs)} -> {len(unique_jobs)}（删除 {len(scraped_jobs)-len(unique_jobs)} 个重复）')
    scraped_jobs = unique_jobs
    
    # 转换格式并导入
    jobs_to_import = []
    for job in scraped_jobs:
        # 跳过解析失败的（没有公司名或岗位名）
        if not job.get('company') or not job.get('position'):
            continue
        
        # 使用新解析器重新解析详情文本，确保最高提取率
        detail_text = job.get('detail_text', '')
        if detail_text:
            parsed_detail = parse_job_detail(detail_text)
            parsed_basic = extract_basic_info(detail_text)
            # 用解析结果覆盖原有字段（如果解析结果非空）
            if parsed_detail['responsibilities']:
                job['responsibilities'] = parsed_detail['responsibilities']
            if parsed_detail['requirements']:
                job['requirements'] = parsed_detail['requirements']
            if parsed_detail['benefits_text']:
                job['benefits_text'] = parsed_detail['benefits_text']
            if parsed_detail['job_description']:
                job['job_description'] = parsed_detail['job_description']
            if parsed_basic['company_size']:
                job['company_size'] = parsed_basic['company_size']
            if parsed_basic['company_industry']:
                job['company_industry'] = parsed_basic['company_industry']
            if parsed_basic['work_location']:
                job['work_location'] = parsed_basic['work_location']
        
        # 构建 JD 文本
        jd_parts = []
        jd_parts.append(f"公司: {job.get('company', '')}")
        jd_parts.append(f"岗位: {job.get('position', '')}")
        jd_parts.append(f"城市: {job.get('city', '')}")
        jd_parts.append(f"薪资: {job.get('salary', '')}")
        jd_parts.append(f"学历: {job.get('education', '')}")
        jd_parts.append(f"经验: {job.get('experience', '')}")
        if job.get('skills'):
            jd_parts.append(f"技能要求: {'、'.join(job['skills'])}")
        if job.get('responsibilities'):
            jd_parts.append(f"工作职责:\n{job['responsibilities']}")
        if job.get('requirements'):
            jd_parts.append(f"任职要求:\n{job['requirements']}")
        if job.get('benefits_text'):
            jd_parts.append(f"福利待遇:\n{job['benefits_text']}")
        
        job_data = {
            'company': job.get('company', ''),
            'position': job.get('position', ''),
            'city': job.get('city', ''),
            'salary': job.get('salary', ''),
            'education': job.get('education', ''),
            'experience': job.get('experience', ''),
            'skills': job.get('skills', []),
            'responsibilities': job.get('responsibilities', ''),
            'requirements': job.get('requirements', ''),
            'benefits_text': job.get('benefits_text', ''),
            'job_description': job.get('job_description', ''),
            'detail_text': job.get('detail_text', ''),
            'company_size': job.get('company_size', ''),
            'company_industry': job.get('company_industry', ''),
            'company_link': job.get('company_link', ''),
            'work_location': job.get('work_location', ''),
            'jd_text': '\n\n'.join(jd_parts),
            'source': job.get('source', '智联招聘'),
            'job_url': job.get('job_url', ''),
            'url': job.get('url', ''),
        }
        jobs_to_import.append(job_data)
    
    print(f'有效岗位 {len(jobs_to_import)} 个，开始导入...')
    result = collector.add_jobs_batch(jobs_to_import)
    print(f"导入完成: 成功{result['success']}个, 重复{result['duplicate']}个, 失败{result['failed']}个")
    return result['success']


def batch_rank_jobs(collector, resume_data):
    """对未评估岗位批量匹配评估（使用优化版匹配引擎）"""
    unscored = collector.get_unscored_jobs()
    print(f'找到 {len(unscored)} 个未评估岗位')
    
    if not unscored:
        print('没有需要评估的岗位')
        return 0
    
    success_count = 0
    for job in unscored:
        job_id = job['id']
        company = job.get('company', '')
        position = job.get('position', '')
        
        try:
            # 构建 jd_info（直接从岗位字段构建，不需要解析jd_text）
            jd_info = {
                'position': position,
                'company': company,
                'city': job.get('city', ''),
                'salary': job.get('salary', ''),
                'salary_min': job.get('salary_min', 0),
                'salary_max': job.get('salary_max', 0),
                'education': job.get('education', ''),
                'experience': job.get('experience', ''),
                'skills_required': job.get('skills', []),
                'responsibilities': job.get('responsibilities', ''),
                'requirements': job.get('requirements', ''),
                'company_size': job.get('company_size', ''),
                'company_industry': job.get('company_industry', ''),
            }
            
            # 使用优化版匹配引擎评估
            match_result = calculate_match(jd_info, resume_data)
            total_score = match_result['total_score']
            
            # 构建匹配详情（优化版5维度）
            dims = match_result['dimensions']
            match_detail = {
                'tech_score': dims['tech']['score'],
                'exp_score': dims['exp']['score'],
                'relevance_score': dims['relevance']['score'],
                'hard_score': dims['hard']['score'],
                'preference_score': dims['preference']['score'],
                'matched_skills': dims['tech']['matched'],
                'missing_skills': dims['tech']['missing'],
                'recommendation': match_result['recommendation'],
                'rec_color': match_result['rec_color'],
                'rec_detail': match_result['rec_detail'],
                'exp_notes': dims['exp']['notes'],
                'relevance_notes': dims['relevance']['notes'],
                'preference_notes': dims['preference']['notes'],
                'hard_passes': dims['hard']['passes'],
                'hard_issues': dims['hard']['issues'],
            }
            
            # 更新岗位库
            collector.update_match_score(job_id, total_score, match_detail)
            print(f"  ✓ {company[:15]:15s} | {position[:15]:15s} | 匹配度: {total_score}分 ({match_result['recommendation']})")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {company[:15]} | {position[:15]} | 评估失败: {e}")
    
    print(f'\n批量评估完成: 成功{success_count}/{len(unscored)}个')
    return success_count


def generate_recommendation_report(collector, output_path=None):
    """生成岗位推荐报告（统一主题；委托 report_generator，不再自带第三套样式）"""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'applications', '岗位推荐报告.html')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    jobs = collector.query_jobs(sort_by='match_score', reverse=True)
    scored = [j for j in jobs if j.get('match_score') is not None]
    scored.sort(key=lambda x: x.get('match_score') or 0, reverse=True)
    if not scored:
        print('暂无已评估岗位，无法生成报告（请先运行 rank 评估）')
        return None

    source_counts = {}
    for j in jobs:
        src = j.get('source', '未知')
        source_counts[src] = source_counts.get(src, 0) + 1
    src_text = '、'.join(f'{k}{v}个' for k, v in source_counts.items())

    from report_generator import generate_report
    out = generate_report(
        scored, output_path,
        title='🎯 岗位推荐报告',
        subtitle=f'岗位库共 {len(jobs)} 个，已评估 {len(scored)} 个（{src_text}），按匹配度排序'
    )
    print(f'  已评估岗位: {len(scored)} 个')
    return out


def main():
    if len(sys.argv) < 2:
        print('用法:')
        print('  python job_pipeline.py import    # 导入抓取岗位')
        print('  python job_pipeline.py rank      # 批量匹配评估')
        print('  python job_pipeline.py report    # 生成推荐报告')
        print('  python job_pipeline.py all       # 全部执行')
        sys.exit(0)
    
    cmd = sys.argv[1]
    workspace = os.path.dirname(os.path.abspath(__file__))
    collector = JobCollector(os.path.join(workspace, 'jobs.json'))
    
    if cmd in ('import', 'all'):
        print('\n=== 第一步：导入抓取岗位 ===')
        import_scraped_jobs(collector)
    
    if cmd in ('rank', 'all'):
        print('\n=== 第二步：批量匹配评估 ===')
        resume_data = load_resume_data(workspace)
        batch_rank_jobs(collector, resume_data)
    
    if cmd in ('report', 'all'):
        print('\n=== 第三步：生成推荐报告 ===')
        generate_recommendation_report(collector)
    
    print('\n=== 完成 ===')


if __name__ == '__main__':
    main()
