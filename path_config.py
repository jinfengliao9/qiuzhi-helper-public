# -*- coding: utf-8 -*-
"""
统一路径配置模块
所有命令的输出路径都从这里获取，确保路径统一、可维护。

用法：
    from path_config import get_path, Paths
    
    # 获取简历输出目录
    resume_dir = get_path('resume', company='中冶沈勘')
    
    # 获取面试题库输出目录
    interview_dir = get_path('interview')
    
    # 获取匹配报告输出目录
    match_dir = get_path('match_report')
"""

import os
import re


# 工作区根目录
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# applications目录
APPLICATIONS_DIR = os.path.join(WORKSPACE_DIR, "applications")

# 分类目录定义
CATEGORY_DIRS = {
    'match_report': '01_岗位匹配报告',      # 匹配评估报告
    'resume': '02_简历',                      # 简历
    'interview': '03_面试题库',               # 面试题库
    'collect_report': '04_岗位采集报告',      # 岗位采集报告
    'campus': '05_网申模块',                   # 网申模块
    'archive': '99_归档_历史测试',             # 归档
    'job_cache': '00_岗位缓存',                # 岗位缓存
}

# 其他重要目录
OTHER_DIRS = {
    'cv': 'cv',                                # 默认简历目录（兼容旧版）
    'interview_prep': 'interview-prep',       # 默认面试题库目录（兼容旧版）
    'oq_answers': 'oq_answers',                # OQ答案
    'radar': 'radar',                          # 网申雷达
    'tests': 'tests',                          # 测试
    'templates': 'templates',                  # 模板
    'references': 'references',                # 参考文档
    'sop': 'references/sop',                   # SOP文档
}


def sanitize_filename(name):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def get_path(category, company=None, job_title=None, filename=None):
    """
    获取统一输出路径
    
    Args:
        category: 分类名称（match_report/resume/interview/collect_report/campus/archive/job_cache）
        company: 公司名（可选，用于创建子文件夹）
        job_title: 岗位名（可选，用于文件名）
        filename: 文件名（可选，如果指定则返回完整文件路径）
    
    Returns:
        str: 目录路径或完整文件路径
    """
    # 获取分类目录
    if category in CATEGORY_DIRS:
        base_dir = os.path.join(APPLICATIONS_DIR, CATEGORY_DIRS[category])
    elif category in OTHER_DIRS:
        base_dir = os.path.join(WORKSPACE_DIR, OTHER_DIRS[category])
    else:
        # 未知分类，使用applications根目录
        base_dir = APPLICATIONS_DIR
    
    # 如果指定了公司名，创建公司子文件夹
    if company:
        company_safe = sanitize_filename(company)
        if category == 'resume':
            base_dir = os.path.join(base_dir, f"{company_safe}_简历")
        elif category == 'match_report':
            # 匹配报告不创建子文件夹，直接放在分类目录下
            pass
        else:
            base_dir = os.path.join(base_dir, company_safe)
    
    # 确保目录存在
    os.makedirs(base_dir, exist_ok=True)
    
    # 如果指定了文件名，返回完整文件路径
    if filename:
        return os.path.join(base_dir, filename)
    
    return base_dir


class Paths:
    """路径常量类，方便直接访问"""
    
    WORKSPACE = WORKSPACE_DIR
    APPLICATIONS = APPLICATIONS_DIR
    
    # 分类目录
    MATCH_REPORT = get_path('match_report')
    RESUME = get_path('resume')
    INTERVIEW = get_path('interview')
    COLLECT_REPORT = get_path('collect_report')
    CAMPUS = get_path('campus')
    ARCHIVE = get_path('archive')
    JOB_CACHE = get_path('job_cache')
    
    # 其他目录
    CV = get_path('cv')
    OQ_ANSWERS = get_path('oq_answers')
    RADAR = get_path('radar')
    TESTS = get_path('tests')
    TEMPLATES = get_path('templates')
    REFERENCES = get_path('references')
    SOP = get_path('sop')
    
    # 重要文件
    RESUME_DATA = os.path.join(WORKSPACE_DIR, 'resume_data.json')
    APPLICATION_PROFILE = os.path.join(WORKSPACE_DIR, 'application_profile.json')
    CONFIG = os.path.join(WORKSPACE_DIR, 'config.yaml')
    SKILL_MD = os.path.join(WORKSPACE_DIR, 'SKILL.md')
    PROJECT_NODE = os.path.join(WORKSPACE_DIR, 'PROJECT_NODE.md')
    FILE_MAP = os.path.join(WORKSPACE_DIR, 'FILE_MAP.md')


def print_path_summary():
    """打印路径配置摘要"""
    print("=" * 60)
    print("  统一路径配置")
    print("=" * 60)
    print(f"\n  工作区: {WORKSPACE_DIR}")
    print(f"  applications: {APPLICATIONS_DIR}")
    print(f"\n  分类目录:")
    for key, value in CATEGORY_DIRS.items():
        print(f"    {key:20s} -> {value}")
    print(f"\n  其他目录:")
    for key, value in OTHER_DIRS.items():
        print(f"    {key:20s} -> {value}")
    print(f"\n  重要文件:")
    print(f"    resume_data.json")
    print(f"    application_profile.json")
    print(f"    config.yaml")
    print(f"    SKILL.md")
    print(f"    PROJECT_NODE.md")
    print(f"    FILE_MAP.md")


if __name__ == '__main__':
    print_path_summary()
    
    # 测试
    print("\n" + "=" * 60)
    print("  路径测试")
    print("=" * 60)
    
    test_cases = [
        ('resume', {'company': '中冶沈勘工程技术有限公司'}),
        ('interview', {}),
        ('match_report', {}),
        ('collect_report', {}),
        ('campus', {}),
        ('job_cache', {}),
    ]
    
    for category, kwargs in test_cases:
        path = get_path(category, **kwargs)
        print(f"\n  get_path('{category}', {kwargs})")
        print(f"    -> {path}")
