# -*- coding: utf-8 -*-
"""
岗位URL抓取模块
支持从招聘网站URL自动抓取岗位JD，保存为中间JSON供后续步骤复用。

支持平台：
- 国聘网 (iguopin.com) - 公开页面，直接抓取
- 通用网页 - 兜底方案，抓取页面文本

用法：
    python job_fetcher.py <岗位URL> [输出文件路径]
    python job_fetcher.py --list  # 列出已抓取的岗位
"""

import os
import sys
import re
import json
import io
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urlparse


# ============================================================
# 配置
# ============================================================
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "applications", "00_岗位缓存")
os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ============================================================
# 工具函数
# ============================================================
def clean_html(html_text):
    """清理HTML标签，提取纯文本"""
    if not html_text:
        return ""
    # 移除script和style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 替换换行标签
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # HTML实体解码
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&middot;', '·')
    # 清理多余空白
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)


def fetch_url(url, timeout=15):
    """抓取URL内容"""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()
            # 尝试检测编码
            content_type = response.headers.get('Content-Type', '')
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].strip()
            else:
                charset = 'utf-8'
            try:
                return content.decode(charset, errors='replace')
            except:
                return content.decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        print(f"  HTTP错误: {e.code} {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL错误: {e.reason}")
        return None
    except Exception as e:
        print(f"  抓取失败: {e}")
        return None


def detect_platform(url):
    """识别招聘平台"""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if 'iguopin.com' in domain:
        return 'guopin'
    elif 'zhaopin.com' in domain:
        return 'zhaopin'
    elif 'zhipin.com' in domain:
        return 'zhipin'
    elif '51job.com' in domain or 'jobs.51job.com' in domain:
        return '51job'
    elif 'liepin.com' in domain:
        return 'liepin'
    else:
        return 'generic'


# ============================================================
# 各平台解析器
# ============================================================
def parse_guopin(html_text, url):
    """解析国聘网岗位页面"""
    result = {
        'source': '国聘网',
        'url': url,
        'platform': 'guopin',
        'job_title': '',
        'company': '',
        'salary': '',
        'city': '',
        'job_nature': '',
        'headcount': '',
        'education': '',
        'experience': '',
        'major_requirement': '',
        'deadline': '',
        'job_description': '',
        'responsibilities': '',
        'requirements': '',
        'company_type': '',
        'company_size': '',
        'company_industry': '',
        'raw_text': '',
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    text = clean_html(html_text)
    result['raw_text'] = text[:5000]
    
    # 提取岗位名（通常在页面标题或H1）
    title_match = re.search(r'([^\n]+?)\s*\n\s*更新于', text)
    if title_match:
        result['job_title'] = title_match.group(1).strip()
    
    # 提取薪资
    salary_match = re.search(r'(\d+[~\-]\d+K?|\d+K\s*[-~]\s*\d+K|面议)', text)
    if salary_match:
        result['salary'] = salary_match.group(1).strip()
    
    # 提取公司名（通常在"单位信息"或"公司"附近）
    company_patterns = [
        r'([^\n]+?有限公司)\s*\n',
        r'([^\n]+?研究院)\s*\n',
        r'([^\n]+?集团)\s*\n',
        r'单位信息\s*\n\s*([^\n]+)',
    ]
    for pattern in company_patterns:
        match = re.search(pattern, text)
        if match:
            result['company'] = match.group(1).strip()
            break
    
    # 提取地点
    city_match = re.search(r'([\u4e00-\u9fa5]+[市省][\u4e00-\u9fa5\-]*区?)\s*(?:有限公司|研究院|集团)', text)
    if city_match:
        result['city'] = city_match.group(1).strip()
    
    # 提取职位性质
    if '校招' in text:
        result['job_nature'] = '校招'
    elif '社招' in text:
        result['job_nature'] = '社招'
    elif '实习' in text:
        result['job_nature'] = '实习'
    
    # 提取学历
    edu_match = re.search(r'最低学历[：:]\s*([\u4e00-\u9fa5]+)', text)
    if edu_match:
        result['education'] = edu_match.group(1).strip()
    
    # 提取经验
    exp_match = re.search(r'工作经验[：:]\s*([\u4e00-\u9fa5]+)', text)
    if exp_match:
        result['experience'] = exp_match.group(1).strip()
    
    # 提取招聘人数
    count_match = re.search(r'招聘人数[：:]\s*(\d+)\s*人', text)
    if count_match:
        result['headcount'] = count_match.group(1)
    
    # 提取截止时间
    deadline_match = re.search(r'报名截止[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if deadline_match:
        result['deadline'] = deadline_match.group(1)
    
    # 提取专业要求
    major_match = re.search(r'专业要求[：:]\s*([\u4e00-\u9fa5、]+)', text)
    if major_match:
        result['major_requirement'] = major_match.group(1).strip()
    
    # 提取职位介绍/岗位职责
    jd_match = re.search(r'职位介绍\s*\n(.*?)(?=竞争力分析|工作地点|单位信息|$)', text, re.DOTALL)
    if jd_match:
        jd_text = jd_match.group(1).strip()
        result['job_description'] = jd_text[:3000]
        # 尝试拆分职责和要求
        if '任职要求' in jd_text or '岗位要求' in jd_text:
            parts = re.split(r'任职要求|岗位要求', jd_text, maxsplit=1)
            result['responsibilities'] = parts[0].strip()[:2000]
            if len(parts) > 1:
                result['requirements'] = parts[1].strip()[:2000]
        else:
            result['responsibilities'] = jd_text[:2000]
    
    # 提取公司信息
    if '国企' in text:
        result['company_type'] = '国企'
    elif '民营' in text or '私企' in text:
        result['company_type'] = '民营'
    elif '外企' in text:
        result['company_type'] = '外企'
    
    size_match = re.search(r'(\d+-\d+人|\d+人以上)', text)
    if size_match:
        result['company_size'] = size_match.group(1)
    
    return result


def parse_generic(html_text, url):
    """通用网页解析（兜底）"""
    result = {
        'source': '通用网页',
        'url': url,
        'platform': 'generic',
        'job_title': '',
        'company': '',
        'salary': '',
        'city': '',
        'job_description': '',
        'responsibilities': '',
        'requirements': '',
        'raw_text': '',
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    text = clean_html(html_text)
    result['raw_text'] = text[:5000]
    result['job_description'] = text[:3000]
    
    # 尝试从<title>提取
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.DOTALL | re.IGNORECASE)
    if title_match:
        result['job_title'] = clean_html(title_match.group(1)).strip()[:100]
    
    # 尝试提取薪资
    salary_match = re.search(r'(\d+[~\-]\d+K?|\d+K\s*[-~]\s*\d+K|面议|\d+万/年)', text)
    if salary_match:
        result['salary'] = salary_match.group(1).strip()
    
    # 尝试提取公司名
    company_match = re.search(r'([^\n]+?有限公司)', text)
    if company_match:
        result['company'] = company_match.group(1).strip()
    
    return result


# ============================================================
# 主抓取函数
# ============================================================
def parse_job_html(html_text, url, output_path=None):
    """
    从HTML内容解析岗位信息（主agent用web.fetch抓取后调用此函数）
    
    Args:
        html_text: HTML内容
        url: 岗位URL（用于识别平台和保存）
        output_path: 输出文件路径
    
    Returns:
        dict: 岗位信息
    """
    if not html_text:
        print("  ❌ HTML内容为空")
        return None
    
    # 识别平台
    platform = detect_platform(url)
    platform_names = {
        'guopin': '国聘网',
        'zhaopin': '智联招聘',
        'zhipin': 'BOSS直聘',
        '51job': '前程无忧',
        'liepin': '猎聘',
        'generic': '通用网页',
    }
    print(f"  识别平台: {platform_names.get(platform, platform)}")
    print(f"  HTML大小: {len(html_text)} 字节")
    
    # 检查是否是JS动态加载的空页面
    text = clean_html(html_text)
    if len(text) < 100 or 'enable JavaScript' in text or 'JavaScript to run this app' in text:
        print("  ⚠️  页面是JS动态加载的，简单抓取无法获取内容")
        print("  💡 建议：主agent使用web.fetch工具抓取（支持JS渲染），或手动复制JD文本")
    
    # 解析页面
    print(f"  📝 正在解析岗位信息...")
    if platform == 'guopin':
        result = parse_guopin(html_text, url)
    else:
        result = parse_generic(html_text, url)
    
    # 打印提取结果摘要
    print(f"\n  📋 提取结果:")
    print(f"    岗位: {result.get('job_title', '未提取')}")
    print(f"    公司: {result.get('company', '未提取')}")
    print(f"    薪资: {result.get('salary', '未提取')}")
    print(f"    地点: {result.get('city', '未提取')}")
    print(f"    JD长度: {len(result.get('job_description', ''))} 字符")
    
    # 保存缓存
    url_hash = abs(hash(url)) % 100000
    cache_file = os.path.join(CACHE_DIR, f"job_{platform}_{url_hash}.json")
    with io.open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 已保存缓存: {os.path.basename(cache_file)}")
    
    # 保存到指定路径
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with io.open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  💾 已保存到: {output_path}")
    
    return result


def parse_jd_text(jd_text, company='', job_title='', url='', output_path=None):
    """
    从纯文本JD解析岗位信息（用户手动复制JD文本时使用）
    
    Args:
        jd_text: JD纯文本
        company: 公司名（可选）
        job_title: 岗位名（可选）
        url: 岗位URL（可选）
        output_path: 输出文件路径
    
    Returns:
        dict: 岗位信息
    """
    print(f"📝 从JD文本解析岗位信息...")
    print(f"  文本长度: {len(jd_text)} 字符")
    
    result = {
        'source': '手动输入',
        'url': url,
        'platform': 'manual',
        'job_title': job_title,
        'company': company,
        'salary': '',
        'city': '',
        'job_nature': '',
        'headcount': '',
        'education': '',
        'experience': '',
        'major_requirement': '',
        'deadline': '',
        'job_description': jd_text[:3000],
        'responsibilities': '',
        'requirements': '',
        'company_type': '',
        'company_size': '',
        'company_industry': '',
        'raw_text': jd_text[:5000],
        'fetched_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # 尝试从文本中提取薪资（更准确，排除日期干扰）
    salary_patterns = [
        r'(\d+[~\-]\d+K)',
        r'(\d+K\s*[-~]\s*\d+K)',
        r'(\d+\s*[-~]\s*\d+\s*千)',
        r'(\d+\s*[-~]\s*\d+\s*万/月)',
        r'(\d+\s*[-~]\s*\d+\s*万/年)',
        r'(面议)',
        r'薪资[：:]\s*([^\n，。]+)',
    ]
    for pattern in salary_patterns:
        salary_match = re.search(pattern, jd_text)
        if salary_match:
            salary = salary_match.group(1).strip()
            # 排除日期干扰（如2026-06）
            if not re.match(r'^\d{4}', salary):
                result['salary'] = salary
                break
    
    # 提取地点
    city_match = re.search(r'([\u4e00-\u9fa5]+[市省]?[\u4e00-\u9fa5\-]*区?)\s*(?:有限公司|研究院|集团|科技)', jd_text)
    if city_match:
        result['city'] = city_match.group(1).strip()
    else:
        city_match2 = re.search(r'工作地点[：:]\s*([^\n，。]+)', jd_text)
        if city_match2:
            result['city'] = city_match2.group(1).strip()
    else:
        # 尝试从文本开头提取地点（如"沈阳-浑南区 公司名"）
        city_match3 = re.search(r'^([\u4e00-\u9fa5]+[\-~][\u4e00-\u9fa5]+区)', jd_text, re.MULTILINE)
        if city_match3:
            result['city'] = city_match3.group(1).strip()
    
    # 提取职位性质
    if '校招' in jd_text or '校园招聘' in jd_text:
        result['job_nature'] = '校招'
    elif '社招' in jd_text or '社会招聘' in jd_text:
        result['job_nature'] = '社招'
    elif '实习' in jd_text:
        result['job_nature'] = '实习'
    
    # 提取招聘人数
    count_match = re.search(r'招聘人数[：:]\s*(\d+)\s*人', jd_text)
    if count_match:
        result['headcount'] = count_match.group(1)
    
    # 提取学历
    edu_match = re.search(r'最低学历[：:]\s*([\u4e00-\u9fa5]+)', jd_text)
    if edu_match:
        result['education'] = edu_match.group(1).strip()
    else:
        edu_match2 = re.search(r'(本科|硕士|博士|大专|学历不限)', jd_text)
        if edu_match2:
            result['education'] = edu_match2.group(1)
    
    # 提取经验
    exp_match = re.search(r'工作经验[：:]\s*([\u4e00-\u9fa5]+)', jd_text)
    if exp_match:
        result['experience'] = exp_match.group(1).strip()
    else:
        exp_match2 = re.search(r'(应届生|经验不限|\d+-\d+年|\d+年以上)', jd_text)
        if exp_match2:
            result['experience'] = exp_match2.group(1)
    
    # 提取专业要求
    major_match = re.search(r'专业要求[：:]\s*([\u4e00-\u9fa5、，]+)', jd_text)
    if major_match:
        result['major_requirement'] = major_match.group(1).strip()
    
    # 提取截止时间
    deadline_match = re.search(r'报名截止[：:]\s*(\d{4}-\d{2}-\d{2})', jd_text)
    if deadline_match:
        result['deadline'] = deadline_match.group(1)
    else:
        deadline_match2 = re.search(r'截止[：:]\s*(\d{4}-\d{2}-\d{2})', jd_text)
        if deadline_match2:
            result['deadline'] = deadline_match2.group(1)
    
    # 提取公司类型
    if '国企' in jd_text or '国有企业' in jd_text:
        result['company_type'] = '国企'
    elif '民营' in jd_text or '私企' in jd_text:
        result['company_type'] = '民营'
    elif '外企' in jd_text or '外资' in jd_text:
        result['company_type'] = '外企'
    elif '事业单位' in jd_text:
        result['company_type'] = '事业单位'
    
    # 提取公司规模
    size_match = re.search(r'(\d+-\d+人|\d+人以上|\d+人以下)', jd_text)
    if size_match:
        result['company_size'] = size_match.group(1)
    
    # 提取行业
    industry_match = re.search(r'行业要求[：:]\s*([\u4e00-\u9fa5]+)', jd_text)
    if industry_match:
        result['company_industry'] = industry_match.group(1).strip()
    
    # 尝试拆分职责和要求
    if '任职要求' in jd_text or '岗位要求' in jd_text:
        parts = re.split(r'任职要求|岗位要求', jd_text, maxsplit=1)
        result['responsibilities'] = parts[0].strip()[:2000]
        if len(parts) > 1:
            result['requirements'] = parts[1].strip()[:2000]
    else:
        result['responsibilities'] = jd_text[:2000]
    
    # 打印提取结果摘要
    print(f"\n  📋 提取结果:")
    print(f"    岗位: {result.get('job_title', '未提供')}")
    print(f"    公司: {result.get('company', '未提供')}")
    print(f"    薪资: {result.get('salary', '未提取')}")
    print(f"    JD长度: {len(result.get('job_description', ''))} 字符")
    
    # 保存
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with io.open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 已保存到: {output_path}")
    
    return result


def fetch_job(url, output_path=None, use_cache=True):
    """
    抓取岗位信息
    
    Args:
        url: 岗位URL
        output_path: 输出文件路径（默认自动命名）
        use_cache: 是否使用缓存
    
    Returns:
        dict: 岗位信息
    """
    print(f"🔍 开始抓取: {url}")
    
    # 识别平台
    platform = detect_platform(url)
    platform_names = {
        'guopin': '国聘网',
        'zhaopin': '智联招聘',
        'zhipin': 'BOSS直聘',
        '51job': '前程无忧',
        'liepin': '猎聘',
        'generic': '通用网页',
    }
    print(f"  识别平台: {platform_names.get(platform, platform)}")
    
    # 检查缓存
    cache_file = None
    if use_cache:
        url_hash = abs(hash(url)) % 100000
        cache_file = os.path.join(CACHE_DIR, f"job_{platform}_{url_hash}.json")
        if os.path.exists(cache_file):
            print(f"  📦 使用缓存: {os.path.basename(cache_file)}")
            with io.open(cache_file, encoding='utf-8') as f:
                return json.load(f)
    
    # 抓取页面
    print(f"  📡 正在抓取页面...")
    html_text = fetch_url(url)
    
    if not html_text:
        print("  ❌ 抓取失败")
        return None
    
    print(f"  ✅ 页面抓取成功 ({len(html_text)} 字节)")
    
    # 解析页面
    print(f"  📝 正在解析岗位信息...")
    if platform == 'guopin':
        result = parse_guopin(html_text, url)
    else:
        result = parse_generic(html_text, url)
    
    # 打印提取结果摘要
    print(f"\n  📋 提取结果:")
    print(f"    岗位: {result.get('job_title', '未提取')}")
    print(f"    公司: {result.get('company', '未提取')}")
    print(f"    薪资: {result.get('salary', '未提取')}")
    print(f"    地点: {result.get('city', '未提取')}")
    print(f"    JD长度: {len(result.get('job_description', ''))} 字符")
    
    # 保存缓存
    if cache_file:
        with io.open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 已保存缓存: {os.path.basename(cache_file)}")
    
    # 保存到指定路径
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with io.open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  💾 已保存到: {output_path}")
    
    return result


def list_cached_jobs():
    """列出已缓存的岗位"""
    if not os.path.exists(CACHE_DIR):
        print("暂无缓存岗位")
        return
    
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.json')]
    if not files:
        print("暂无缓存岗位")
        return
    
    print(f"已缓存 {len(files)} 个岗位:\n")
    for f in sorted(files):
        filepath = os.path.join(CACHE_DIR, f)
        try:
            with io.open(filepath, encoding='utf-8') as fp:
                data = json.load(fp)
            print(f"  [{data.get('source', '?')}] {data.get('company', '?')} - {data.get('job_title', '?')}")
            print(f"    {data.get('url', '')}")
            print(f"    抓取时间: {data.get('fetched_at', '?')}\n")
        except:
            print(f"  ⚠️  {f} (解析失败)\n")


# ============================================================
# 命令行入口
# ============================================================
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python job_fetcher.py <岗位URL> [输出文件路径]")
        print("  python job_fetcher.py --list  # 列出已缓存的岗位")
        print("  python job_fetcher.py --clear  # 清除缓存")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == '--list':
        list_cached_jobs()
    elif arg == '--clear':
        import shutil
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
            os.makedirs(CACHE_DIR)
            print("✅ 缓存已清除")
        else:
            print("暂无缓存")
    else:
        url = arg
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        result = fetch_job(url, output_path)
        if result:
            print("\n✅ 抓取完成!")
        else:
            print("\n❌ 抓取失败")
            sys.exit(1)
