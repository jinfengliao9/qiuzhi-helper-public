# -*- coding: utf-8 -*-
"""
岗位本地筛选模块
支持按城市、薪资、公司性质、公司规模、经验、学历、匹配度等多维度筛选

使用方式：
1. 交互式筛选：python filter_jobs.py
2. 代码调用：from filter_jobs import filter_jobs, generate_filtered_report
"""

import json
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_jobs(jobs_file='jobs.json'):
    """加载岗位库"""
    if not os.path.exists(jobs_file):
        print(f'错误: 岗位库不存在: {jobs_file}')
        return []
    with open(jobs_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_salary(salary_str):
    """解析薪资字符串，返回(最小值, 最大值)，单位：元/月"""
    if not salary_str:
        return (0, 0)
    
    salary_str = salary_str.strip()
    
    # 处理"万"单位
    if '万' in salary_str:
        # 如 "1-1.5万"、"2-4万"
        match = re.search(r'([\d.]+)\s*[-~]\s*([\d.]+)\s*万', salary_str)
        if match:
            min_sal = int(float(match.group(1)) * 10000)
            max_sal = int(float(match.group(2)) * 10000)
            return (min_sal, max_sal)
        # 如 "2万"
        match = re.search(r'([\d.]+)\s*万', salary_str)
        if match:
            sal = int(float(match.group(1)) * 10000)
            return (sal, sal)
    
    # 处理"元"单位
    if '元' in salary_str:
        match = re.search(r'([\d,]+)\s*[-~]\s*([\d,]+)\s*元', salary_str)
        if match:
            min_sal = int(match.group(1).replace(',', ''))
            max_sal = int(match.group(2).replace(',', ''))
            return (min_sal, max_sal)
    
    # 纯数字范围，如 "6000-10000"
    match = re.search(r'([\d,]+)\s*[-~]\s*([\d,]+)', salary_str)
    if match:
        min_sal = int(match.group(1).replace(',', ''))
        max_sal = int(match.group(2).replace(',', ''))
        # 如果数值很大（如10000以上），可能是元/月
        if max_sal > 1000:
            return (min_sal, max_sal)
        # 否则可能是千/月，如"6-10"表示6000-10000
        return (min_sal * 1000, max_sal * 1000)
    
    return (0, 0)


def is_state_owned(company_name):
    """判断公司是否为国企/事业单位"""
    if not company_name:
        return False
    keywords = ['国企', '国有', '中核', '中铁', '中建', '中交', '中水', '中煤', 
                '地质', '勘查', '勘测', '研究院', '设计院', '规划院', '研究所',
                '事业单位', '集体', '国资', '中物', '中陕核', '核工业',
                '中国四维', '中汇', '中图']
    return any(k in company_name for k in keywords)


def filter_jobs(jobs, filters=None):
    """
    按条件筛选岗位
    
    Args:
        jobs: 岗位列表
        filters: 筛选条件字典，支持以下键：
            - cities: list, 目标城市列表（如['广州', '深圳']）
            - salary_min: int, 最低薪资（元/月）
            - salary_max: int, 最高薪资（元/月）
            - state_owned_only: bool, 仅国企/事业单位
            - company_size_min: str, 最小公司规模（如'100-499人'）
            - match_min: int, 最低匹配度
            - match_max: int, 最高匹配度
            - experience: list, 经验要求列表（如['经验不限', '1-3年']）
            - education: list, 学历要求列表（如['本科', '大专']）
            - keywords: list, 岗位名/公司名包含的关键词
            - exclude_keywords: list, 岗位名/公司名排除的关键词
            - sources: list, 平台来源筛选（如['BOSS直聘', '智联招聘']）
            - has_skills: bool, 仅显示有技能标签的岗位
            
    Returns:
        list: 筛选后的岗位列表
    """
    if not filters:
        return jobs
    
    filtered = []
    for job in jobs:
        # 城市筛选
        if filters.get('cities'):
            job_city = job.get('city', '')
            if not any(c in job_city for c in filters['cities']):
                continue
        
        # 薪资筛选
        if filters.get('salary_min') or filters.get('salary_max'):
            sal_min, sal_max = parse_salary(job.get('salary', ''))
            if filters.get('salary_min') and sal_max < filters['salary_min']:
                continue
            if filters.get('salary_max') and sal_min > filters['salary_max']:
                continue
        
        # 仅国企
        if filters.get('state_owned_only'):
            if not is_state_owned(job.get('company', '')):
                continue
        
        # 公司规模筛选
        if filters.get('company_size_min'):
            size = job.get('company_size', '')
            if not size:
                continue
            # 简单比较：提取人数下限
            size_match = re.search(r'(\d+)', size)
            min_size_match = re.search(r'(\d+)', filters['company_size_min'])
            if size_match and min_size_match:
                if int(size_match.group(1)) < int(min_size_match.group(1)):
                    continue
        
        # 匹配度筛选
        if filters.get('match_min') is not None:
            if job.get('match_score', 0) < filters['match_min']:
                continue
        if filters.get('match_max') is not None:
            if job.get('match_score', 0) > filters['match_max']:
                continue
        
        # 经验要求筛选
        if filters.get('experience'):
            job_exp = job.get('experience', '')
            if not any(e in job_exp for e in filters['experience']):
                continue
        
        # 学历要求筛选
        if filters.get('education'):
            job_edu = job.get('education', '')
            if not any(e in job_edu for e in filters['education']):
                continue
        
        # 关键词筛选（岗位名或公司名包含）
        if filters.get('keywords'):
            text = (job.get('position', '') + ' ' + job.get('company', '')).lower()
            if not any(k.lower() in text for k in filters['keywords']):
                continue
        
        # 排除关键词
        if filters.get('exclude_keywords'):
            text = (job.get('position', '') + ' ' + job.get('company', '')).lower()
            if any(k.lower() in text for k in filters['exclude_keywords']):
                continue
        
        # 平台来源筛选
        if filters.get('sources'):
            job_source = job.get('source', '')
            if job_source not in filters['sources']:
                continue
        
        # 仅显示有技能标签的岗位
        if filters.get('has_skills'):
            if not job.get('skills'):
                continue
        
        filtered.append(job)
    
    return filtered


def generate_filtered_report(jobs, filters=None, output_path=None):
    """
    生成筛选后的岗位推荐报告
    
    Args:
        jobs: 岗位列表
        filters: 筛选条件
        output_path: 输出路径
    """
    from job_pipeline import generate_recommendation_report
    from job_collector import JobCollector
    
    # 筛选岗位
    filtered = filter_jobs(jobs, filters)
    
    # 创建临时岗位库
    collector = JobCollector('jobs_filtered_temp.json')
    collector.add_jobs_batch(filtered)
    
    # 生成报告
    if output_path is None:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   'applications', '岗位筛选报告.html')
    
    generate_recommendation_report(collector, output_path)
    
    # 清理临时文件
    if os.path.exists('jobs_filtered_temp.json'):
        os.remove('jobs_filtered_temp.json')
    
    return filtered, output_path


def print_filter_summary(jobs, filters):
    """打印筛选条件和结果统计"""
    print("\n" + "="*60)
    print("筛选条件")
    print("="*60)
    if filters.get('cities'):
        print(f"  目标城市: {', '.join(filters['cities'])}")
    if filters.get('salary_min'):
        print(f"  最低薪资: {filters['salary_min']}元/月")
    if filters.get('salary_max'):
        print(f"  最高薪资: {filters['salary_max']}元/月")
    if filters.get('state_owned_only'):
        print(f"  仅国企/事业单位")
    if filters.get('match_min') is not None:
        print(f"  最低匹配度: {filters['match_min']}分")
    if filters.get('keywords'):
        print(f"  包含关键词: {', '.join(filters['keywords'])}")
    if filters.get('exclude_keywords'):
        print(f"  排除关键词: {', '.join(filters['exclude_keywords'])}")
    
    print(f"\n筛选结果: {len(jobs)}个岗位")
    
    # 统计
    if jobs:
        scores = [j.get('match_score', 0) for j in jobs]
        print(f"  平均匹配度: {sum(scores)//len(scores)}分")
        print(f"  最高匹配度: {max(scores)}分")
        print(f"  最低匹配度: {min(scores)}分")


def interactive_filter():
    """交互式筛选"""
    jobs = load_jobs()
    if not jobs:
        print("岗位库为空，请先抓取岗位")
        return
    
    print(f"\n当前岗位库共有 {len(jobs)} 个岗位")
    print("\n请选择筛选条件（直接回车表示不筛选）：")
    
    filters = {}
    
    # 城市
    cities_input = input("  目标城市（多个用逗号分隔，如：广州,深圳,长沙）: ").strip()
    if cities_input:
        filters['cities'] = [c.strip() for c in cities_input.split(',') if c.strip()]
    
    # 薪资
    salary_min_input = input("  最低薪资（元/月，如：6000）: ").strip()
    if salary_min_input:
        filters['salary_min'] = int(salary_min_input)
    
    salary_max_input = input("  最高薪资（元/月，如：15000）: ").strip()
    if salary_max_input:
        filters['salary_max'] = int(salary_max_input)
    
    # 国企
    state_input = input("  仅国企/事业单位？(y/n): ").strip().lower()
    if state_input == 'y':
        filters['state_owned_only'] = True
    
    # 匹配度
    match_min_input = input("  最低匹配度（如：65）: ").strip()
    if match_min_input:
        filters['match_min'] = int(match_min_input)
    
    # 关键词
    keywords_input = input("  岗位/公司包含关键词（多个用逗号分隔）: ").strip()
    if keywords_input:
        filters['keywords'] = [k.strip() for k in keywords_input.split(',') if k.strip()]
    
    # 排除关键词
    exclude_input = input("  排除关键词（多个用逗号分隔）: ").strip()
    if exclude_input:
        filters['exclude_keywords'] = [k.strip() for k in exclude_input.split(',') if k.strip()]
    
    if not filters:
        print("\n未设置任何筛选条件，显示全部岗位")
    else:
        # 筛选
        filtered = filter_jobs(jobs, filters)
        print_filter_summary(filtered, filters)
        
        # 生成报告
        if filtered:
            generate = input("\n是否生成筛选报告？(y/n): ").strip().lower()
            if generate == 'y':
                _, output_path = generate_filtered_report(jobs, filters)
                print(f"\n筛选报告已生成: {output_path}")


if __name__ == '__main__':
    interactive_filter()
