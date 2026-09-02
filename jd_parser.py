# -*- coding: utf-8 -*-
# ============================================================================
# 【状态说明】本文件诞生于 Browser Use 自动化抓取时代，但其中的核心能力
# 被现行流水线活跃引用，因此保留在工作区根目录，不归档、不删除。
#   - 活跃复用：parse_job_detail() / extract_basic_info()，被 job_pipeline.py 的 import 流程用于详情文本拆分
#   - 已废弃：与 Browser Use 抓取流程绑定的调用路径（v0.2.0 起主路径为
#     Edge 扩展被动采集，见 boss_api/）
# 详见 archive/browser_use_legacy/README.md
# ============================================================================
"""
JD详情解析模块
支持多种标题变体和容错处理，提高详情提取率
"""

import re


def parse_job_detail(detail_text):
    """
    解析岗位详情文本，提取工作职责、任职要求、薪资福利等
    
    Args:
        detail_text: 岗位详情原始文本
        
    Returns:
        dict: 包含 responsibilities, requirements, benefits_text, job_description 等字段
    """
    result = {
        'responsibilities': '',
        'requirements': '',
        'benefits_text': '',
        'job_description': '',
    }
    
    if not detail_text:
        return result
    
    text = detail_text
    
    # ========== 1. 提取薪资福利 ==========
    benefit_patterns = [
        r'(薪资福利|福利待遇)\s*\n(.*?)(?=职位描述|工作职责|工作内容|岗位内容|岗位职责|工作职能|任职要求|职位要求|岗位要求|任职资格|岗位资格|应聘要求|职位发布者|工作地点|公司信息|求职工具|$)',
    ]
    for pattern in benefit_patterns:
        benefit_match = re.search(pattern, text, re.DOTALL)
        if benefit_match and benefit_match.group(2).strip():
            result['benefits_text'] = benefit_match.group(2).strip()[:1000]
            break
    
    # ========== 2. 提取工作职责 ==========
    resp_titles = ['工作职责', '工作内容', '岗位内容', '岗位职责', '工作职能', '岗位职能', '工作范围', '岗位描述']
    # 构建正则：匹配任意一个工作职责标题
    resp_title_pattern = '|'.join(re.escape(t) for t in resp_titles)
    resp_pattern = rf'({resp_title_pattern})\s*[：:]?\s*\n?(\d+[\.、].*?|.*?)(?=任职要求|职位要求|岗位要求|任职资格|岗位资格|应聘要求|职位发布者|工作地点|公司信息|求职工具|$)'
    
    resp_match = re.search(resp_pattern, text, re.DOTALL)
    if resp_match and resp_match.group(2).strip():
        result['responsibilities'] = resp_match.group(2).strip()[:2000]
    
    # ========== 3. 提取任职要求 ==========
    req_titles = ['任职要求', '职位要求', '岗位要求', '任职资格', '岗位资格', '应聘要求', 
                   '应聘条件', '任职条件', '岗位条件', '资格要求', '条件要求', '基本要求',
                   '招聘要求', '录用条件', '入职要求', '能力要求', '素质要求']
    req_title_pattern = '|'.join(re.escape(t) for t in req_titles)
    req_pattern = rf'({req_title_pattern})\s*[：:]?\s*\n?(\d+[\.、].*?|.*?)(?=职位发布者|工作地点|公司信息|求职工具|$)'
    
    req_match = re.search(req_pattern, text, re.DOTALL)
    if req_match and req_match.group(2).strip():
        result['requirements'] = req_match.group(2).strip()[:2000]
    
    # ========== 4. 容错处理：如果没有找到任职要求，从职位描述中智能分离 ==========
    if not result['requirements']:
        # 尝试从"职位描述"下面提取内容
        desc_pattern = r'职位描述\s*\n?(\d+[\.、].*?|.*?)(?=职位发布者|工作地点|公司信息|求职工具|$)'
        desc_match = re.search(desc_pattern, text, re.DOTALL)
        if desc_match and desc_match.group(1).strip():
            desc_content = desc_match.group(1).strip()
            # 检查内容中是否有编号列表
            has_numbered_list = bool(re.search(r'\d+[\.、]', desc_content))
            
            if has_numbered_list:
                # 提取所有编号列表项
                items = re.findall(r'\d+[\.、]\s*(.+?)(?=\n?\d+[\.、]|职位发布者|工作地点|公司信息|$)', desc_content, re.DOTALL)
                items = [item.strip() for item in items if len(item.strip()) > 5]
                
                if items:
                    # 智能分离：根据关键词判断条目是职责还是要求
                    req_keywords = ['学历', '专业', '经验', '熟悉', '掌握', '具备', '能接受', '能吃苦', 
                                    '有', '持有', '具有', '了解', '懂得', '会', '优先', '条件', '资格',
                                    '中专', '大专', '本科', '硕士', '博士', '高中', '学历不限',
                                    '沟通能力', '团队协作', '责任心', '学习能力', '抗压能力',
                                    '出差', '外派', '驻场', '加班', '户外', '吃苦耐劳']
                    resp_keywords = ['负责', '协助', '参与', '完成', '进行', '开展', '实施', '整理',
                                    '编写', '制作', '绘制', '采集', '处理', '分析', '测量', '测绘',
                                    '调查', '验收', '审核', '管理', '维护', '保障', '提供', '支持']
                    
                    req_items = []
                    resp_items = []
                    for item in items:
                        item_lower = item.lower()
                        # 计算要求关键词命中数
                        req_hits = sum(1 for kw in req_keywords if kw in item_lower)
                        # 计算职责关键词命中数
                        resp_hits = sum(1 for kw in resp_keywords if kw in item_lower)
                        
                        if req_hits > resp_hits:
                            req_items.append(item)
                        elif resp_hits > req_hits:
                            resp_items.append(item)
                        else:
                            # 命中数相同，默认归为职责
                            resp_items.append(item)
                    
                    # 如果分离出了任职要求，就保存
                    if req_items:
                        result['requirements'] = '\n'.join(f'{i+1}. {item}' for i, item in enumerate(req_items))[:2000]
                    
                    # 如果没有找到工作职责，用分离出的职责项
                    if not result['responsibilities'] and resp_items:
                        result['responsibilities'] = '\n'.join(f'{i+1}. {item}' for i, item in enumerate(resp_items))[:2000]
                    elif not result['responsibilities']:
                        # 没有分离出职责，全部作为工作职责
                        result['responsibilities'] = '\n'.join(f'{i+1}. {item}' for i, item in enumerate(items))[:2000]
            else:
                # 没有编号列表，作为职位描述
                if not result['job_description']:
                    result['job_description'] = desc_content[:1000]
    
    # ========== 5. 容错处理：如果还是没有找到，提取所有编号列表 ==========
    if not result['responsibilities']:
        # 提取详情中所有编号列表项
        numbered_items = re.findall(r'\d+[\.、]\s*(.+?)(?=\n\d+[\.、]|\n\n|职位发布者|工作地点|公司信息|$)', text, re.DOTALL)
        if numbered_items:
            # 过滤掉太短的项（可能不是真正的列表项）
            valid_items = [item.strip() for item in numbered_items if len(item.strip()) > 10]
            if valid_items:
                result['responsibilities'] = '\n'.join(f'{i+1}. {item}' for i, item in enumerate(valid_items))[:2000]
    
    # ========== 6. 提取职位描述（技能标签） ==========
    if not result['job_description']:
        desc_pattern = r'职位描述\s*\n(.*?)(?=工作职责|工作内容|岗位内容|岗位职责|工作职能|任职要求|职位要求|岗位要求|任职资格|岗位资格|应聘要求|职位发布者|工作地点|公司信息|求职工具|$)'
        desc_match = re.search(desc_pattern, text, re.DOTALL)
        if desc_match and desc_match.group(1).strip():
            # 职位描述通常是技能标签，检查是否每一行都很短
            desc_lines = [l.strip() for l in desc_match.group(1).strip().split('\n') if l.strip()]
            if all(len(line) < 30 for line in desc_lines[:5]):
                result['job_description'] = '\n'.join(desc_lines)[:500]
    
    return result


def extract_basic_info(detail_text):
    """
    从详情文本中提取基本信息（公司规模、行业、工作地点等）
    
    Args:
        detail_text: 岗位详情原始文本
        
    Returns:
        dict: 包含 company_size, company_industry, work_location 等字段
    """
    result = {
        'company_size': '',
        'company_industry': '',
        'work_location': '',
    }
    
    if not detail_text:
        return result
    
    # 公司规模和行业
    size_match = re.search(r'/([\d-]+人)\s*·\s*([^\n]+)', detail_text)
    if size_match:
        result['company_size'] = size_match.group(1)
        result['company_industry'] = size_match.group(2).strip()
    
    # 工作地点
    location_match = re.search(r'工作地点\s*\n([^\n]+)', detail_text)
    if location_match:
        result['work_location'] = location_match.group(1).strip()
    
    return result


if __name__ == '__main__':
    # 测试
    test_text = """遥感测绘工程师 5000-8000元
收藏
分享
举报
信阳·平桥区
1-3年
硕士
招4人
立即投递
职位描述
遥感测绘
摄影测量
地理信息系统
岗位内容：
1、负责培训学生遥感数据处理；
2、负责卫星遥感数据的接收、管理、处理；
任职要求：
1、至少熟练掌握一种遥感数据处理软件；
2、熟悉ArcGIS等GIS软件平台；
职位发布者
杜女士
"""
    
    result = parse_job_detail(test_text)
    print("=== 测试解析结果 ===")
    print(f"工作职责: {'✓' if result['responsibilities'] else '✗'}")
    if result['responsibilities']:
        print(result['responsibilities'][:200])
    print(f"\n任职要求: {'✓' if result['requirements'] else '✗'}")
    if result['requirements']:
        print(result['requirements'][:200])
    print(f"\n职位描述: {'✓' if result['job_description'] else '✗'}")
    if result['job_description']:
        print(result['job_description'][:200])
