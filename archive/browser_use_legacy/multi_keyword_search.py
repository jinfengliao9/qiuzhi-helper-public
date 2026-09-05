# -*- coding: utf-8 -*-
"""
多关键词岗位搜索抓取模块
支持用户随意指定关键词，一次搜索多个关键词，合并结果并去重

支持两种筛选方式：
- 方案A（抓取前筛选）：导航到智联页面后，让用户接管浏览器设置筛选条件（城市/薪资/学历/经验等），然后抓取筛选后的结果
- 方案C（抓取后筛选）：先抓取一批岗位，然后在本地按条件筛选（城市/薪资/国企/匹配度等）

使用方式：
1. 用户告诉助手要搜索的关键词列表（如["测绘工程师", "测量工程师", "GIS工程师"]）
2. 助手逐个关键词在Browser Use中搜索并抓取（方案A：抓取前让用户设置筛选条件）
3. 合并所有结果并去重
4. 导入岗位库并生成报告
5. （可选）方案C：用户告诉助手筛选条件，助手在本地筛选后生成报告

抓取流程（每个关键词）：
1. 导航到 https://sou.zhaopin.com/?kw=关键词
2. 等待页面加载，确认登录状态
3. 【方案A】调用 interaction.request_action 让用户接管浏览器设置筛选条件
4. 抓取所有可见岗位的基本信息（公司名、岗位名、薪资、城市、公司链接）
5. 分两批逐个点击提取详情（每批20个，控制反爬节奏）
6. 保存结果到 scraped_jobs_关键词.json
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jd_parser import parse_job_detail, extract_basic_info


def generate_navigate_code(keyword):
    """
    生成方案A的导航代码（第一步：导航到搜索页面，等待用户设置筛选条件）
    
    执行完此代码后，应调用 interaction.request_action(type="browserControl") 
    让用户接管浏览器设置筛选条件，用户完成后再调用 generate_scrape_code 抓取。
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        str: Browser Use执行代码
    """
    code = f'''
import seed_browser_use as bu
import time

# 导航到搜索页面
print("导航到智联招聘搜索页面，关键词：{keyword}")
bu.navigate("https://sou.zhaopin.com/?kw={keyword}")
bu.wait_for_load(timeout=15)
time.sleep(3)

# 检查登录状态
page_text = bu.get_page_text()
if "登录" in page_text[:500] and "廖锦锋" not in page_text:
    print("⚠️ 未检测到登录状态，请先登录")
else:
    print("✓ 页面加载完成")

print("请在浏览器中设置筛选条件（城市/薪资/学历/经验/公司性质等）")
print("设置完成后，把控制权交回，我会开始抓取筛选后的结果")
'''
    return code


def generate_scrape_code(keyword, batch=1):
    """
    生成Browser Use抓取代码
    
    Args:
        keyword: 搜索关键词
        batch: 批次（1=前20个，2=后20个）
        
    Returns:
        str: Browser Use执行代码
    """
    start = (batch - 1) * 20
    end = batch * 20
    
    code = f'''
import seed_browser_use as bu
import json
import time

# 导航到搜索页面
print("搜索关键词: {keyword}")
bu.navigate("https://sou.zhaopin.com/?kw={keyword}")
bu.wait_for_load(timeout=15)
time.sleep(3)

# 检查登录状态
page_text = bu.get_page_text()
if "登录" in page_text[:500] and "廖锦锋" not in page_text:
    print("⚠️ 未检测到登录状态")
else:
    print("✓ 页面加载完成")

# 抓取所有岗位基本信息
print("抓取岗位基本信息...")
extract_js = """
(function() {{
    var jobs = [];
    var cards = document.querySelectorAll('.job-list-panel > .job-card');
    for (var i = 0; i < cards.length; i++) {{
        var card = cards[i];
        var job = {{}};
        var titleEl = card.querySelector('.job-card__title-main, .job-card__title');
        job.position = titleEl ? titleEl.textContent.trim() : '';
        var salaryEl = card.querySelector('.job-card__salary, [class*="salary"]');
        job.salary = salaryEl ? salaryEl.textContent.trim() : '';
        var companyLink = card.querySelector('a[href*="companydetail"]');
        if (companyLink) {{
            job.company = companyLink.textContent.trim();
            job.company_link = companyLink.href;
        }}
        var tagEls = card.querySelectorAll('.job-card__tag, [class*="tag"]');
        var tags = [];
        for (var j = 0; j < tagEls.length; j++) {{
            var t = tagEls[j].textContent.trim();
            if (t && t.length < 20) tags.push(t);
        }}
        job.tags = tags;
        job.card_text = card.textContent.trim();
        jobs.push(job);
    }}
    return JSON.stringify(jobs);
}})()
"""
result = bu.js(extract_js)
basic_jobs = json.loads(result)
print(f"抓取到 {{len(basic_jobs)}} 个岗位")

# 提取指定批次的详情
print(f"提取第 {batch} 批详情（{start+1}-{end}）...")
detailed_jobs = []
for i in range({start}, min({end}, len(basic_jobs))):
    job = basic_jobs[i]
    print(f"[{{i+1}}/{{len(basic_jobs)}}] {{job['company'][:12]}} - {{job['position'][:12]}}", end='')
    
    try:
        click_js = f"""
        (function() {{
            var cards = document.querySelectorAll('.job-list-panel > .job-card');
            if (cards[{{i}}]) {{
                cards[{{i}}].scrollIntoView({{behavior: 'smooth', block: 'center'}});
                setTimeout(function() {{ cards[{{i}}].click(); }}, 200);
                return 'ok';
            }}
            return 'not found';
        }})()
        """
        bu.js(click_js)
        time.sleep(2.2)
        
        bu.js("""
        (function() {{
            var s = document.querySelector('.job-detail-modules__scroll');
            if (s) s.scrollTop = s.scrollHeight;
        }})()
        """)
        time.sleep(0.6)
        
        detail_text = bu.js("""
        (function() {{
            var p = document.querySelector('.job-detail-panel');
            return p ? p.textContent.trim() : '';
        }})()
        """)
        
        full_job = {{
            'position': job['position'],
            'company': job['company'],
            'company_link': job.get('company_link', ''),
            'salary': job['salary'],
            'city': '',
            'experience': '',
            'education': '',
            'skills': job.get('tags', []),
            'detail_text': detail_text[:8000],
            'search_keyword': '{keyword}',
        }}
        detailed_jobs.append(full_job)
        print(f" | {{len(detail_text)}}字符")
    except Exception as e:
        print(f" | 错误: {{e}}")
        detailed_jobs.append(job)
    
    time.sleep(1.0)

# 保存
output_path = r'C:\\Users\\32994\\Doubao\\chats\\2026-08-24\\new-chat\\job-search-workspace\\scraped_{keyword}_batch{batch}.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(detailed_jobs, f, ensure_ascii=False, indent=2)
print(f"已保存到 scraped_{keyword}_batch{batch}.json ({{len(detailed_jobs)}}个)")
'''
    return code


def merge_and_parse(keywords):
    """
    合并多个关键词的抓取结果，解析详情，去重
    
    Args:
        keywords: 关键词列表
        
    Returns:
        list: 合并去重后的岗位列表
    """
    all_jobs = []
    
    # 合并所有关键词的抓取结果
    for keyword in keywords:
        for batch in [1, 2]:
            filepath = f'scraped_{keyword}_batch{batch}.json'
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    jobs = json.load(f)
                print(f"加载 {keyword} 批次{batch}: {len(jobs)}个岗位")
                all_jobs.extend(jobs)
    
    print(f"\n合并后共 {len(all_jobs)} 个岗位")
    
    # 去重：基于公司名+岗位名
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        key = (job.get('company', '').strip(), job.get('position', '').strip())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    print(f"去重后共 {len(unique_jobs)} 个岗位")
    
    # 用jd_parser解析详情
    print("\n解析详情...")
    parsed_jobs = []
    for job in unique_jobs:
        detail_text = job.get('detail_text', '')
        if detail_text:
            parsed = parse_job_detail(detail_text)
            basic = extract_basic_info(detail_text)
            if parsed['responsibilities']:
                job['responsibilities'] = parsed['responsibilities']
            if parsed['requirements']:
                job['requirements'] = parsed['requirements']
            if parsed['benefits_text']:
                job['benefits_text'] = parsed['benefits_text']
            if parsed['job_description']:
                job['job_description'] = parsed['job_description']
            if basic['company_size']:
                job['company_size'] = basic['company_size']
            if basic['company_industry']:
                job['company_industry'] = basic['company_industry']
            
            # 从详情文本中解析城市、经验、学历
            city_match = re.search(r'([\u4e00-\u9fa5]+)·([\u4e00-\u9fa5]+)', detail_text)
            if city_match and not job.get('city'):
                job['city'] = city_match.group(1)
            exp_match = re.search(r'(经验不限|应届毕业生|在校|1-3年|1年|2年|3年|3-5年|5年以上)', detail_text)
            if exp_match and not job.get('experience'):
                job['experience'] = exp_match.group(1)
            edu_match = re.search(r'(高中|中专|大专|本科|硕士|博士|学历不限)', detail_text)
            if edu_match and not job.get('education'):
                job['education'] = edu_match.group(1)
        
        parsed_jobs.append(job)
    
    # 统计
    has_resp = sum(1 for j in parsed_jobs if j.get('responsibilities'))
    has_req = sum(1 for j in parsed_jobs if j.get('requirements'))
    print(f"有工作职责: {has_resp}/{len(parsed_jobs)} ({has_resp*100//len(parsed_jobs)}%)")
    print(f"有任职要求: {has_req}/{len(parsed_jobs)} ({has_req*100//len(parsed_jobs)}%)")
    
    # 保存合并结果
    output_path = 'scraped_jobs_merged.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(parsed_jobs, f, ensure_ascii=False, indent=2)
    print(f"\n已保存到 {output_path}")
    
    return parsed_jobs


if __name__ == '__main__':
    # 测试：合并现有的40个岗位数据
    print("=== 多关键词搜索模块测试 ===")
    print("使用方式：")
    print("1. 调用 generate_scrape_code(keyword, batch) 生成抓取代码")
    print("2. 在Browser Use中执行抓取代码")
    print("3. 调用 merge_and_parse(keywords) 合并解析")
    print("\n示例：搜索['测绘工程师', '测量工程师', 'GIS工程师']")
