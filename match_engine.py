# -*- coding: utf-8 -*-
"""
优化版岗位匹配引擎 v2
增加更多匹配维度，提高区分度，避免大量相同分数

主要改进：
1. 技术匹配：从职责和要求中自动提取技能关键词，不依赖skills_required字段
2. 岗位相关性：增加岗位名称与用户求职意向的精确匹配度
3. 增加负向匹配：岗位要求的核心技能用户完全没有，大幅扣分
4. 细化各个维度的评分逻辑，增加区分度
5. 增加综合评分的微调，避免大量相同分数

维度：
1. 技术匹配（25%）：核心技能权重更高，区分匹配深度，自动提取技能
2. 经验匹配（20%）：区分实习/项目相关性，细化经验要求
3. 岗位相关性（20%）：岗位名称精确匹配、职责/要求相关性
4. 硬约束（15%）：学历、城市、经验年限
5. 偏好匹配（20%）：薪资、公司规模、公司性质（国企/大公司偏好）
"""

import re
import hashlib


def extract_skills_from_text(text):
    """从文本中自动提取技能关键词"""
    if not text:
        return []
    
    text_lower = text.lower()
    skills = []
    
    # 测绘工程核心技能库
    skill_patterns = [
        # 专业软件
        r'arcgis', r'arc\s*gis', r'cass', r'cad', r'auto\s*cad',
        r'envi', r'er\s*das', r'qgis', r'mapgis', r'supermap',
        r'global\s*mapper', r'erdas', r'pix4d', r'contextcapture',
        # 编程语言/数据库
        r'python', r'java', r'c\+\+', r'c#', r'\.net', r'sql',
        r'mysql', r'oracle', r'postgresql', r'postgis', r'javascript',
        r'html', r'css', r'vue', r'react', r'flask', r'django',
        # 专业技能
        r'测绘', r'测量', r'地籍', r'土地调查', r'不动产登记',
        r'gis', r'地理信息', r'遥感', r'摄影测量', r'空间分析',
        r'地图制图', r'地形测量', r'工程测量', r'房产测绘',
        r'无人机', r'航测', r'倾斜摄影', r'三维建模', r'bim',
        r'rtk', r'全站仪', r'gps', r'gnss', r'水准仪', r'经纬仪',
        r'控制测量', r'导线测量', r'水准测量', r'三角测量',
        r'数据处理', r'数据采集', r'数据建库', r'数据入库',
        r'空间数据库', r'地理数据库', r'国土空间规划',
        r'国土调查', r'三调', r'第三次国土调查',
        r'农村土地承包经营权', r'二轮延包', r'土地确权',
        r'地质灾害', r'滑坡', r'泥石流', r'灾害监测',
        r'环境监测', r'生态修复', r'矿山测量', r'隧道测量',
        r'桥梁测量', r'道路测量', r'市政测量', r'建筑测量',
        # 软技能
        r'团队协作', r'沟通能力', r'学习能力', r'责任心',
        r'能吃苦', r'能出差', r'能加班', r'抗压能力',
        r'项目管理', r'文档编写', r'报告撰写',
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            # 标准化技能名称
            skill = matches[0].strip()
            # 一些别名标准化
            skill_aliases = {
                'arc gis': 'arcgis',
                'auto cad': 'cad',
                'er das': 'erdas',
                'global mapper': 'globalmapper',
                'c  #': 'c#',
            }
            if skill in skill_aliases:
                skill = skill_aliases[skill]
            if skill not in skills:
                skills.append(skill)
    
    return skills


def calculate_match(jd_info, resume_data):
    """
    计算岗位匹配度（优化版v2）
    
    Args:
        jd_info: 岗位信息字典
        resume_data: 用户简历数据
        
    Returns:
        dict: 包含 total_score, recommendation, rec_color, dimensions 等
    """
    basic = resume_data.get('基本信息', {})
    skills = resume_data.get('技能清单', {})
    education = resume_data.get('教育背景', [])
    experience = resume_data.get('实习经历', [])
    projects = resume_data.get('项目经历', [])
    others = resume_data.get('自我评价', [])
    
    # 收集用户所有技能
    user_skills = []
    if isinstance(skills, dict):
        for skill_list in skills.values():
            user_skills.extend([s.lower() for s in skill_list])
    
    # 用户背景关键词（用于岗位相关性匹配）
    user_background = ' '.join([
        basic.get('job_intention', ''),
        ' '.join(user_skills),
        ' '.join([exp.get('company', '') + ' ' + exp.get('position', '') + ' ' + ' '.join(exp.get('description', [])) for exp in experience]),
        ' '.join([proj.get('name', '') + ' ' + proj.get('role', '') + ' ' + ' '.join(proj.get('description', [])) for proj in projects]),
    ]).lower()
    
    # 用户求职意向
    user_job_intention = basic.get('job_intention', '').lower()
    
    # ========== 1. 技术匹配（25%） ==========
    # 从岗位的各个字段中自动提取技能要求
    required_skills = jd_info.get('skills_required', [])
    if not required_skills:
        # 从职责、要求、详情文本中自动提取
        all_text = ' '.join([
            jd_info.get('responsibilities', ''),
            jd_info.get('requirements', ''),
            jd_info.get('detail_text', ''),
            jd_info.get('job_description', ''),
        ])
        required_skills = extract_skills_from_text(all_text)
    
    # 核心技能（测绘工程核心技能，权重更高）
    core_skills = ['arcgis', 'cass', 'cad', 'rtk', '全站仪', 'gps', 'gnss', '水准仪', 
                    '测绘', '测量', '地籍', '土地调查', '不动产登记', 'gis', '遥感',
                    '摄影测量', '空间分析', '地图制图', '地形测量', '工程测量',
                    'python', 'sql', 'envi', '无人机', '航测', '三维建模',
                    '控制测量', '数据处理', '国土调查', '土地确权']
    
    matched_skills = []
    missing_skills = []
    core_matched = 0
    core_total = 0
    
    for skill in required_skills:
        skill_lower = skill.lower()
        is_core = any(c in skill_lower for c in core_skills)
        if is_core:
            core_total += 1
            
        # 模糊匹配：用户技能包含岗位技能，或岗位技能包含用户技能
        is_matched = (skill_lower in user_skills or 
                      any(skill_lower in s for s in user_skills) or
                      any(s in skill_lower for s in user_skills if len(s) > 2))
        
        if is_matched:
            matched_skills.append(skill)
            if is_core:
                core_matched += 1
        else:
            missing_skills.append(skill)
    
    if required_skills:
        # 基础匹配率
        base_match = len(matched_skills) / len(required_skills)
        # 核心技能匹配率（权重更高）
        if core_total > 0:
            core_match = core_matched / core_total
            # 综合：核心技能占65%，普通技能占35%
            tech_score = int((core_match * 0.65 + base_match * 0.35) * 100)
        else:
            tech_score = int(base_match * 100)
    else:
        # 无法提取技能时，从岗位名称和职责判断
        position = jd_info.get('position', '').lower()
        responsibilities = jd_info.get('responsibilities', '').lower()
        if any(k in position for k in ['测绘', '测量', 'gis', '遥感', '地籍']):
            tech_score = 75  # 岗位名称相关，给较高分
        elif any(k in responsibilities for k in ['测绘', '测量', 'gis', 'arcgis', 'cass']):
            tech_score = 65  # 职责相关，给中等分
        else:
            tech_score = 50  # 无法判断，给较低分
    
    # 关键技能缺失额外扣分
    critical_missing = [s for s in missing_skills if any(c in s.lower() for c in core_skills)]
    if critical_missing:
        # 缺失的核心技能越多，扣分越多（但不超过30分）
        penalty = min(len(critical_missing) * 8, 30)
        tech_score = max(tech_score - penalty, 0)
    
    # 技能匹配数量加分（匹配的技能越多，加分越多）
    if len(matched_skills) >= 5:
        tech_score = min(tech_score + 5, 100)
    elif len(matched_skills) >= 3:
        tech_score = min(tech_score + 2, 100)
    
    tech_score = min(tech_score, 100)
    
    # ========== 2. 经验匹配（20%） ==========
    exp_score = 45  # 降低基础分，增加区分度
    exp_notes = []
    
    # 实习经历（区分相关性）
    if experience:
        relevant_exp = 0
        highly_relevant_exp = 0
        for exp in experience:
            exp_text = (exp.get('company', '') + ' ' + exp.get('position', '') + ' ' + 
                       ' '.join(exp.get('description', []))).lower()
            # 检查是否与测绘高度相关
            if any(k in exp_text for k in ['测绘', '测量', '地籍', '土地确权', '二轮延包', '国土调查']):
                highly_relevant_exp += 1
            elif any(k in exp_text for k in ['gis', '遥感', '地理', '数据处理', 'arcgis']):
                relevant_exp += 1
        
        if highly_relevant_exp > 0:
            exp_score += 30
            exp_notes.append(f'有{highly_relevant_exp}段高度相关测绘实习经历')
        elif relevant_exp > 0:
            exp_score += 20
            exp_notes.append(f'有{relevant_exp}段相关GIS/数据处理实习经历')
        else:
            exp_score += 10
            exp_notes.append(f'有{len(experience)}段实习经历，但相关性一般')
    else:
        exp_notes.append('暂无正式实习经历')
    
    # 项目经历（区分相关性）
    if projects:
        relevant_proj = 0
        highly_relevant_proj = 0
        for proj in projects:
            proj_text = (proj.get('name', '') + ' ' + proj.get('role', '') + ' ' + 
                        ' '.join(proj.get('description', []))).lower()
            if any(k in proj_text for k in ['测绘', '测量', '地籍', '土地', '滑坡', '灾害']):
                highly_relevant_proj += 1
            elif any(k in proj_text for k in ['gis', '遥感', '地理', '空间分析', 'arcgis']):
                relevant_proj += 1
        
        if highly_relevant_proj > 0:
            exp_score += 15
            exp_notes.append(f'有{highly_relevant_proj}个高度相关项目经历')
        elif relevant_proj > 0:
            exp_score += 10
            exp_notes.append(f'有{relevant_proj}个相关项目经历')
        else:
            exp_score += 5
            exp_notes.append(f'有{len(projects)}个项目经历')
    
    # 经验要求匹配（细化）
    jd_exp = jd_info.get('experience', '')
    if '应届' in jd_exp or '在校' in jd_exp or '不限' in jd_exp or not jd_exp:
        exp_score += 15
        exp_notes.append('岗位接受应届生/在校生')
    elif '1年以下' in jd_exp or '1年以内' in jd_exp:
        exp_score += 12
        exp_notes.append('岗位要求1年以下经验，实习经历可弥补')
    elif '1-3年' in jd_exp or '1年' in jd_exp:
        exp_score += 8
        exp_notes.append('岗位要求1-3年经验，实习经历可部分弥补')
    elif '3-5年' in jd_exp or '3年' in jd_exp:
        exp_score += 0
        exp_notes.append('岗位要求3-5年经验，存在明显差距')
    elif '5年' in jd_exp or '10年' in jd_exp:
        exp_score -= 10
        exp_notes.append('岗位经验要求较高，差距较大')
    else:
        exp_score += 5
        exp_notes.append('经验要求不明确')
    
    exp_score = max(min(exp_score, 100), 0)
    
    # ========== 3. 岗位相关性（20%） ==========
    relevance_score = 50  # 降低基础分，增加区分度
    relevance_notes = []
    
    # 岗位名称与用户求职意向的精确匹配
    position = jd_info.get('position', '').lower()
    
    # 定义岗位类型与匹配度
    position_match_level = 0  # 0=不匹配, 1=部分匹配, 2=高度匹配, 3=完全匹配
    
    # 完全匹配：岗位名称包含用户求职意向
    if user_job_intention and user_job_intention in position:
        position_match_level = 3
        relevance_score += 25
        relevance_notes.append(f'岗位名称与求职意向"{user_job_intention}"完全匹配')
    else:
        # 高度匹配：岗位名称包含测绘/测量/GIS/遥感等核心关键词
        high_match_keywords = ['测绘工程师', '测量工程师', '测绘员', '测量员', 
                               'gis工程师', '遥感工程师', '地籍测绘', '工程测量',
                               '测绘技术', '测量技术', '测绘数据', 'gis数据']
        if any(k in position for k in high_match_keywords):
            position_match_level = 2
            relevance_score += 18
            relevance_notes.append('岗位名称与测绘专业高度匹配')
        # 部分匹配：岗位名称包含测绘/测量/GIS等关键词
        elif any(k in position for k in ['测绘', '测量', 'gis', '遥感', '地籍', '地理信息', '航测', '无人机']):
            position_match_level = 1
            relevance_score += 10
            relevance_notes.append('岗位名称与测绘专业部分匹配')
        else:
            position_match_level = 0
            relevance_score -= 5
            relevance_notes.append('岗位名称与测绘专业不匹配')
    
    # 岗位职责相关性
    responsibilities = jd_info.get('responsibilities', '')
    if responsibilities:
        resp_lower = responsibilities.lower()
        # 检查职责中是否有用户熟悉的技能
        familiar_count = sum(1 for skill in user_skills if skill in resp_lower and len(skill) > 2)
        if familiar_count >= 4:
            relevance_score += 12
            relevance_notes.append(f'岗位职责涉及{familiar_count}项用户熟悉技能')
        elif familiar_count >= 2:
            relevance_score += 7
            relevance_notes.append(f'岗位职责涉及{familiar_count}项用户熟悉技能')
        elif familiar_count >= 1:
            relevance_score += 3
            relevance_notes.append('岗位职责涉及部分用户熟悉技能')
        else:
            relevance_score -= 2
        
        # 检查职责是否与测绘相关
        if any(k in resp_lower for k in ['测绘', '测量', '地籍', 'gis', '遥感', 'arcgis', 'cass']):
            relevance_score += 5
            relevance_notes.append('岗位职责涉及测绘相关工作')
    
    # 任职要求相关性
    requirements = jd_info.get('requirements', '')
    if requirements:
        req_lower = requirements.lower()
        # 学历
        user_edu = education[0].get('degree', '') if education else ''
        user_major = education[0].get('major', '') if education else ''
        if '本科' in req_lower and '本科' in user_edu:
            relevance_score += 3
        # 专业
        if '测绘' in req_lower or '地理信息' in req_lower or '遥感' in req_lower:
            if '测绘' in user_major or '地理' in user_major:
                relevance_score += 5
                relevance_notes.append('任职要求涉及测绘相关专业，用户专业匹配')
            else:
                relevance_score += 2
                relevance_notes.append('任职要求涉及测绘相关专业')
    
    relevance_score = max(min(relevance_score, 100), 0)
    
    # ========== 4. 硬约束（15%） ==========
    hard_score = 100
    hard_issues = []
    hard_passes = []
    
    # 学历检查
    jd_edu = jd_info.get('education', '')
    user_edu = education[0].get('degree', '') if education else ''
    if jd_edu:
        if '博士' in jd_edu:
            hard_score -= 40
            hard_issues.append(f'岗位要求博士学历')
        elif '硕士' in jd_edu and '本科' in user_edu:
            hard_score -= 20
            hard_issues.append(f'岗位要求硕士学历')
        elif '大专' in jd_edu and '本科' in user_edu:
            hard_score += 5  # 学历超过要求，加分
            hard_passes.append('学历超过要求')
        elif '本科' in jd_edu and '本科' in user_edu:
            hard_passes.append(f'学历要求满足')
        else:
            hard_passes.append(f'学历要求满足')
    
    # 经验年限检查
    if jd_exp:
        if '5年' in jd_exp or '10年' in jd_exp:
            hard_score -= 25
            hard_issues.append(f'岗位要求{jd_exp}经验，差距较大')
        elif '3-5年' in jd_exp or '3年' in jd_exp:
            hard_score -= 12
            hard_issues.append(f'岗位要求3年以上经验，存在差距')
        elif '1-3年' in jd_exp or '1年' in jd_exp:
            hard_score -= 3
            hard_passes.append(f'经验要求{jd_exp}，实习可弥补')
        elif '应届' in jd_exp or '在校' in jd_exp or '不限' in jd_exp:
            hard_score += 5
            hard_passes.append('岗位接受应届生')
    
    # 城市检查
    jd_city = jd_info.get('city', '')
    user_city = basic.get('city', '')
    if jd_city and user_city:
        if jd_city == user_city:
            hard_score += 8
            hard_passes.append(f'工作地点在{jd_city}，与用户同城')
        elif any(k in jd_city for k in ['广州', '深圳', '珠海', '佛山', '东莞', '中山', '惠州', '肇庆', '江门']):
            # 广东省内，用户接受出差
            hard_score += 3
            hard_passes.append(f'工作地点{jd_city}（广东省内），用户可接受')
        else:
            # 用户接受出差，所以不严格扣分
            all_others = ' '.join(others)
            if '出差' in all_others or '外派' in all_others or '加班' in all_others:
                hard_passes.append(f'工作地点{jd_city}，用户接受出差')
            else:
                hard_score -= 8
                hard_issues.append(f'工作地点{jd_city}，与用户城市不同')
    
    hard_score = max(min(hard_score, 100), 0)
    
    # ========== 5. 偏好匹配（20%） ==========
    preference_score = 55  # 降低基础分，增加区分度
    preference_notes = []
    
    # 薪资匹配（用户期望：待遇合理，优先国企大公司）
    salary_min = jd_info.get('salary_min', 0)
    salary_max = jd_info.get('salary_max', 0)
    if salary_min and salary_max:
        avg_salary = (salary_min + salary_max) / 2
        if avg_salary >= 10000:
            preference_score += 18
            preference_notes.append(f'薪资范围{jd_info.get("salary", "")}，待遇很好')
        elif avg_salary >= 8000:
            preference_score += 12
            preference_notes.append(f'薪资范围{jd_info.get("salary", "")}，待遇较好')
        elif avg_salary >= 6000:
            preference_score += 6
            preference_notes.append(f'薪资范围{jd_info.get("salary", "")}，待遇中等')
        elif avg_salary >= 4000:
            preference_score += 0
            preference_notes.append(f'薪资范围{jd_info.get("salary", "")}，待遇偏低')
        else:
            preference_score -= 5
            preference_notes.append(f'薪资范围{jd_info.get("salary", "")}，待遇很低')
    elif jd_info.get('salary'):
        # 有薪资文本但无法解析数值
        preference_score += 3
        preference_notes.append(f'薪资范围{jd_info.get("salary", "")}')
    
    # 公司规模匹配（用户偏好大公司）
    company_size = jd_info.get('company_size', '')
    if company_size:
        if '10000' in company_size or '1000-9999' in company_size or '5000' in company_size:
            preference_score += 12
            preference_notes.append(f'公司规模{company_size}，大型公司')
        elif '500-999' in company_size or '1000' in company_size:
            preference_score += 8
            preference_notes.append(f'公司规模{company_size}，中大型公司')
        elif '100-499' in company_size or '100-299' in company_size:
            preference_score += 4
            preference_notes.append(f'公司规模{company_size}，中等规模')
        elif '20-99' in company_size or '100' in company_size:
            preference_score += 0
            preference_notes.append(f'公司规模{company_size}，中小规模')
        else:
            preference_score -= 3
            preference_notes.append(f'公司规模{company_size}，规模较小')
    
    # 公司性质匹配（用户偏好国企）
    company_name = jd_info.get('company', '')
    state_owned_keywords = ['国企', '国有', '中核', '中铁', '中建', '中交', '中水', '中煤', 
                            '地质', '勘查', '勘测', '研究院', '设计院', '规划院',
                            '事业单位', '集体', '国资', '集团', '科学院', '研究所']
    if any(k in company_name for k in state_owned_keywords):
        preference_score += 15
        preference_notes.append('公司可能为国企/事业单位，符合用户偏好')
    elif '有限' in company_name and '科技' not in company_name:
        preference_score += 3
        preference_notes.append('公司为有限责任公司')
    elif '科技' in company_name or '信息' in company_name:
        preference_score += 0
        preference_notes.append('公司为科技/信息技术公司')
    
    # 公司行业匹配
    company_industry = jd_info.get('company_industry', '')
    if company_industry:
        if any(k in company_industry for k in ['测绘', '地理', '地质', '勘查', '勘测', '规划', '国土', '自然资源']):
            preference_score += 8
            preference_notes.append(f'公司行业{company_industry}，与专业高度相关')
        elif any(k in company_industry for k in ['工程', '建筑', '房地产', '市政', '交通']):
            preference_score += 4
            preference_notes.append(f'公司行业{company_industry}，与专业相关')
        elif any(k in company_industry for k in ['互联网', '软件', '信息技术', '数据']):
            preference_score += 2
            preference_notes.append(f'公司行业{company_industry}，可发挥GIS/数据技能')
    
    preference_score = max(min(preference_score, 100), 0)
    
    # ========== 综合评分 ==========
    weights = {'tech': 0.25, 'exp': 0.20, 'relevance': 0.20, 'hard': 0.15, 'preference': 0.20}
    total_score = int(
        tech_score * weights['tech'] +
        exp_score * weights['exp'] +
        relevance_score * weights['relevance'] +
        hard_score * weights['hard'] +
        preference_score * weights['preference']
    )
    
    # 基于公司名+岗位名的微调，避免大量相同分数（使用哈希值产生微小差异）
    # 这样即使两个岗位各维度分数相同，总分也会有1-2分的差异
    hash_input = (company_name + position).encode('utf-8')
    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
    fine_adjust = (hash_value % 3) - 1  # -1, 0, 或 +1
    total_score = total_score + fine_adjust
    
    total_score = max(min(total_score, 100), 0)
    
    # 投递建议（根据优化后的分数分布调整阈值）
    if total_score >= 72:
        recommendation = '强烈推荐投递'
        rec_color = '#27ae60'
        rec_detail = '匹配度很高，技能、经验、偏好都比较对口，建议优先投递。'
    elif total_score >= 64:
        recommendation = '推荐投递'
        rec_color = '#2980b9'
        rec_detail = '匹配度较好，有部分gap但可以通过实习经历和学习能力弥补，建议投递。'
    elif total_score >= 55:
        recommendation = '可以尝试'
        rec_color = '#f39c12'
        rec_detail = '匹配度一般，存在较明显的gap，如果对该岗位很感兴趣可以尝试。'
    else:
        recommendation = '不太建议'
        rec_color = '#e74c3c'
        rec_detail = '匹配度较低，硬约束或核心技能差距较大，建议优先考虑更匹配的岗位。'
    
    return {
        'total_score': total_score,
        'recommendation': recommendation,
        'rec_color': rec_color,
        'rec_detail': rec_detail,
        'dimensions': {
            'tech': {'score': tech_score, 'matched': matched_skills, 'missing': missing_skills, 
                    'core_matched': core_matched, 'core_total': core_total,
                    'required_skills': required_skills},
            'exp': {'score': exp_score, 'notes': exp_notes},
            'relevance': {'score': relevance_score, 'notes': relevance_notes, 
                         'position_match_level': position_match_level},
            'hard': {'score': hard_score, 'issues': hard_issues, 'passes': hard_passes},
            'preference': {'score': preference_score, 'notes': preference_notes},
        }
    }


if __name__ == '__main__':
    # 测试
    test_jd = {
        'position': '测绘工程师',
        'company': '广州市城市更新规划设计研究院有限公司',
        'city': '广州',
        'salary': '6000-10000元',
        'salary_min': 6000,
        'salary_max': 10000,
        'education': '本科',
        'experience': '1-3年',
        'skills_required': ['ArcGIS', 'CASS', 'CAD', '测绘', '地籍调查'],
        'responsibilities': '负责测绘项目实施，使用ArcGIS进行空间分析，地籍调查',
        'requirements': '本科以上学历，测绘相关专业，能接受出差',
        'company_size': '100-299人',
        'company_industry': '规划设计',
    }
    
    test_resume = {
        '基本信息': {'job_intention': '测绘工程师', 'city': '示例城市A'},
        '技能清单': {'专业软件': ['ArcGIS', 'CASS', 'CAD', 'RTK', '全站仪'],
                    '专业技能': ['测绘', '测量', '地籍调查', '土地调查']},
        '教育背景': [{'degree': '本科', 'major': '测绘工程'}],
        '实习经历': [{'company': '示例测绘公司', 'position': '测绘实习生', 
                     'description': ['参与二轮土地承包延包项目', '使用ArcGIS进行数据处理']}],
        '项目经历': [{'name': '滑坡灾害监测', 'role': '负责人', 
                     'description': ['使用ArcGIS进行空间分析', '测绘工程相关']}],
        '自我评价': ['能接受长期出差和加班', '有责任心'],
    }
    
    result = calculate_match(test_jd, test_resume)
    print(f"匹配度: {result['total_score']}分")
    print(f"建议: {result['recommendation']}")
    for dim, info in result['dimensions'].items():
        print(f"  {dim}: {info['score']}分")
