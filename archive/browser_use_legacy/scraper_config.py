# -*- coding: utf-8 -*-
"""
通用岗位抓取配置模板
使用说明：
1. 修改下方的配置参数
2. 运行此脚本会生成对应的Browser Use抓取代码
3. 将生成的代码复制到computer_use_tool中执行

注意：由于Browser Use需要在浏览器环境中执行，此脚本只生成代码，不直接执行
"""

import json
import os

# ============== 抓取配置（修改这里） ==============
CONFIG = {
    # 平台选择：'zhaopin' 或 'boss'
    'platform': 'zhaopin',
    
    # 抓取数量：建议5-20个，太多容易触发风控
    'count': 5,
    
    # 每个岗位详情页访问间隔（秒）：建议3-5秒，反爬控制
    'interval': 4,
    
    # 滚动加载次数：每次滚动加载更多岗位，0表示不滚动
    'scroll_times': 0,
    
    # 滚动间隔（秒）
    'scroll_interval': 3,
    
    # 输出文件路径
    'output_file': 'scraped_jobs.json',
    
    # 是否测试模式：测试模式下只抓取，不合并到岗位库
    'test_mode': True,
}

# ============== 平台URL配置 ==============
PLATFORM_URLS = {
    'zhaopin': {
        'name': '智联招聘',
        'search_url': 'https://www.zhaopin.com/jobs?jl=765&pageMode=search&kw=测绘',
        'card_selector': '.joblist-box__item, .job-card',
        'detail_selector': 'a[href*="jobdetail"]',
    },
    'boss': {
        'name': 'BOSS直聘',
        'search_url': 'https://www.zhipin.com/web/geek/jobs?query=测绘&city=100010000',
        'card_selector': '.job-card-box',
        'detail_selector': 'a[href*="job_detail"]',
    }
}

def generate_browser_code(config):
    """生成Browser Use抓取代码"""
    
    platform = config['platform']
    count = config['count']
    interval = config['interval']
    scroll_times = config['scroll_times']
    scroll_interval = config['scroll_interval']
    output_file = config['output_file']
    
    platform_info = PLATFORM_URLS[platform]
    platform_name = platform_info['name']
    search_url = platform_info['search_url']
    
    if platform == 'zhaopin':
        # 智联招聘抓取代码（左右分栏，点击左侧卡片，右侧显示详情）
        code = f'''
import seed_browser_use as bu
import time
import json
import re

jobs = []

# 等待用户设置筛选条件
print("请确认已在页面上设置好筛选条件和关键词")
time.sleep(2)

# 滚动加载更多岗位
for i in range({scroll_times}):
    bu.scroll(500, 500, "down", amount=5)
    time.sleep({scroll_interval})
    print(f"第{{i+1}}次滚动完成")

# 观察页面，找到岗位卡片
snapshot = bu.snapshot()
print("页面已加载，开始提取岗位...")

# 用JavaScript获取所有岗位卡片的文本
js_result = bu.js("""
    const items = document.querySelectorAll('.joblist-box__item, .job-card');
    return Array.from(items).map((item, index) => ({{
        index: index,
        text: item.textContent.trim().substring(0, 200)
    }}));
""")

print(f"找到 {{len(js_result) if js_result else 0}} 个岗位卡片")

# 逐个点击前{count}个岗位提取详情
for i in range(min({count}, len(js_result))):
    print(f"\\n=== 抓取第 {{i+1}}/{{count}} 个岗位 ===")
    
    # 点击岗位卡片（需要根据实际页面调整ref）
    # 这里使用JavaScript点击第i个卡片
    bu.js(f"""
        const items = document.querySelectorAll('.joblist-box__item, .job-card');
        if (items[{{i}}]) items[{{i}}].click();
    """)
    time.sleep(3)
    
    # 提取详情
    page_text = bu.get_page_text()
    
    # 提取岗位名称和薪资
    job_title = ""
    salary = ""
    h1_elements = bu.read_all("h1", fields=["text"], limit=5)
    if h1_elements:
        title_text = h1_elements[0].get("text", "").strip()
        parts = title_text.split()
        if len(parts) >= 2:
            salary = parts[-1]
            job_title = " ".join(parts[:-1])
        else:
            job_title = title_text
    
    # 提取公司名称（从页面文本中匹配）
    company = ""
    company_matches = re.findall(r'([\\u4e00-\\u9fa5()（）]+(?:有限公司|公司|集团))', page_text)
    if company_matches:
        company = max(company_matches, key=len)
    
    # 提取职位描述
    job_description = ""
    desc_start = page_text.find("职位描述")
    if desc_start != -1:
        desc_content = page_text[desc_start:]
        end_markers = ["职位发布者", "工作地点", "联系方式", "收藏", "分享", "举报", "立即投递"]
        desc_end = len(desc_content)
        for marker in end_markers:
            pos = desc_content.find(marker, 10)
            if pos != -1 and pos < desc_end:
                desc_end = pos
        job_description = desc_content[:desc_end]
        job_description = re.sub(r'\\s+', ' ', job_description).strip()[:2000]
    
    # 提取专业技能关键词
    desc_lower = job_description.lower()
    professional_skills = []
    skill_patterns = ['arcgis', 'cass', 'cad', 'rtk', '全站仪', 'gps', 'gnss', 'gis', 
                      '遥感', '摄影测量', '无人机', '航测', 'python', 'sql', '测绘', '测量',
                      '地籍', '工程测量', '地形测量', '控制测量', '空间分析', '数据处理',
                      '市政工程', '房建工程', '土建工程', '施工员', '资料员', '外业采集',
                      '实地核查', '地理信息', '海洋测绘', '监测', '定位导航', '地铁']
    for pattern in skill_patterns:
        if pattern in desc_lower and pattern not in professional_skills:
            professional_skills.append(pattern)
    
    # 获取当前URL
    info = bu.page_info()
    job_url = info.get("url", "")
    
    job_info = {{
        'job_title': job_title,
        'company': company,
        'salary': salary,
        'city': '深圳',
        'experience': '',
        'education': '',
        'job_description': job_description,
        'professional_skills': professional_skills,
        'job_url': job_url,
        'source': '智联招聘'
    }}
    
    jobs.append(job_info)
    print(f"岗位名称: {{job_title}}")
    print(f"公司: {{company}}")
    print(f"薪资: {{salary}}")
    print(f"职位描述长度: {{len(job_description)}}")
    
    # 间隔
    if i < {count} - 1:
        print(f"等待{{interval}}秒...")
        time.sleep({interval})

# 保存结果
output_path = r'{os.path.join(os.path.dirname(__file__), output_file)}'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

print(f"\\n=== 抓取完成 ===")
print(f"共抓取 {{len(jobs)}} 个岗位")
print(f"结果已保存到: {{output_path}}")
'''
    else:
        # BOSS直聘抓取代码（先获取链接，再逐个访问详情页）
        code = f'''
import seed_browser_use as bu
import time
import json
import re

jobs = []

# 等待用户设置筛选条件
print("请确认已在页面上设置好筛选条件和关键词")
time.sleep(2)

# 滚动加载更多岗位
for i in range({scroll_times}):
    bu.scroll(500, 500, "down", amount=5)
    time.sleep({scroll_interval})
    print(f"第{{i+1}}次滚动完成")

# 获取所有岗位详情链接
all_links = bu.read_all("a", fields=["href", "text"], limit=200)
job_links = []
for link in all_links:
    href = link.get("href", "")
    text = link.get("text", "").strip()
    if href and "job_detail" in href:
        job_links.append({{"url": href, "text": text}})

# 去重
unique_links = []
seen_urls = set()
for link in job_links:
    url = link["url"]
    if url not in seen_urls:
        seen_urls.add(url)
        unique_links.append(link)

print(f"找到 {{len(unique_links)}} 个唯一岗位链接")

# 只取前{count}个
test_links = unique_links[:{count}]

# 逐个访问详情页
for idx, link in enumerate(test_links):
    url = link["url"]
    print(f"\\n=== 抓取第 {{idx+1}}/{{len(test_links)}} 个岗位 ===")
    print(f"URL: {{url}}")
    
    try:
        # 先导航到空白页清空缓存
        bu.navigate("about:blank")
        time.sleep(1)
        
        # 再导航到目标URL
        bu.navigate(url)
        bu.wait_for_load(timeout=15)
        time.sleep({interval})
        
        # 检查页面标题
        info = bu.page_info()
        page_title = info.get("title", "")
        
        # 从页面标题解析岗位名称和公司
        job_title = ""
        company = ""
        match = re.search(r'「(.+?)招聘」_(.+?)招聘-BOSS直聘', page_title)
        if match:
            job_title = match.group(1).strip()
            company = match.group(2).strip()
        
        # 提取薪资
        salary = ""
        salary_elements = bu.read_all(".salary", fields=["text"], limit=5)
        if salary_elements:
            salary = salary_elements[0].get("text", "").strip()
        
        # 提取城市、经验、学历
        city = ""
        experience = ""
        education = ""
        info_elements = bu.read_all(".info-primary p", fields=["text"], limit=10)
        if info_elements and len(info_elements) >= 3:
            city = info_elements[0].get("text", "").strip()
            experience = info_elements[1].get("text", "").strip()
            education = info_elements[2].get("text", "").strip()
        
        # 提取职位描述
        page_text = bu.get_page_text()
        job_description = ""
        desc_start = page_text.find("职位描述")
        if desc_start != -1:
            desc_end = page_text.find("公司基本信息", desc_start)
            if desc_end == -1:
                desc_end = desc_start + 3000
            job_description = page_text[desc_start:desc_end]
            job_description = re.sub(r'\\s+', ' ', job_description).strip()[:2000]
        
        # 提取专业技能关键词
        desc_lower = job_description.lower()
        professional_skills = []
        skill_patterns = ['arcgis', 'cass', 'cad', 'rtk', '全站仪', 'gps', 'gnss', 'gis', 
                          '遥感', '摄影测量', '无人机', '航测', 'python', 'sql', '测绘', '测量',
                          '地籍', '工程测量', '地形测量', '控制测量', '空间分析', '数据处理']
        for pattern in skill_patterns:
            if pattern in desc_lower and pattern not in professional_skills:
                professional_skills.append(pattern)
        
        job_info = {{
            'job_title': job_title,
            'company': company,
            'salary': salary,
            'city': city,
            'experience': experience,
            'education': education,
            'job_description': job_description,
            'professional_skills': professional_skills,
            'job_url': url,
            'source': 'BOSS直聘'
        }}
        
        jobs.append(job_info)
        print(f"岗位名称: {{job_title}}")
        print(f"公司: {{company}}")
        print(f"薪资: {{salary}}")
        print(f"职位描述长度: {{len(job_description)}}")
        
    except Exception as e:
        print(f"抓取失败: {{e}}")
        jobs.append({{
            'job_url': url,
            'source': 'BOSS直聘',
            'error': str(e)
        }})

# 保存结果
output_path = r'{os.path.join(os.path.dirname(__file__), output_file)}'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(jobs, f, ensure_ascii=False, indent=2)

print(f"\\n=== 抓取完成 ===")
print(f"共抓取 {{len(jobs)}} 个岗位")
print(f"结果已保存到: {{output_path}}")
'''
    
    return code

def main():
    """主函数：生成抓取代码并保存"""
    
    print("=" * 60)
    print("通用岗位抓取配置工具")
    print("=" * 60)
    print()
    print("当前配置：")
    for key, value in CONFIG.items():
        print(f"  {key}: {value}")
    print()
    
    # 生成抓取代码
    code = generate_browser_code(CONFIG)
    
    # 保存代码到文件
    code_file = os.path.join(os.path.dirname(__file__), f'generated_scrape_{CONFIG["platform"]}.py')
    with open(code_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"抓取代码已生成: {code_file}")
    print()
    print("使用方法：")
    print("1. 打开生成的代码文件，复制全部内容")
    print("2. 在computer_use_tool中执行（plane='bu'）")
    print("3. 确保浏览器已打开对应平台并设置好筛选条件")
    print()
    print("快速调整参数：")
    print("- 修改 count 可调整抓取数量")
    print("- 修改 interval 可调整访问间隔（反爬控制）")
    print("- 修改 platform 可切换平台（zhaopin/boss）")
    print("- 修改 scroll_times 可滚动加载更多岗位")

if __name__ == '__main__':
    main()
