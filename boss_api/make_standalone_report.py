# -*- coding: utf-8 -*-
"""
独立报告生成器（不写入岗位库 jobs.json）
流程：原生扩展导出的岗位 JSON（BOSS joblist / 智联 zhaopin_jobs / 51job job51_jobs）
     → parse_joblist_api / parse_zhaopin_api / parse_51job_api 解析去重
     → match_engine 按简历评分 → report_generator 出独立HTML

两种用法：
  1) 命令行：python make_standalone_report.py <导出.json> [<导出2.json> ...] [-o 输出.html]
  2) 作为模块被统一引擎 job_search.py 调用：
       from make_standalone_report import generate_standalone_report
       out, scored, stats = generate_standalone_report([json路径...], output='')
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(HERE)  # job-search-workspace 根目录
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from parse_joblist_api import extract_jobs, dedupe            # noqa: E402
from parse_zhaopin_api import parse_zhaopin                    # noqa: E402
from parse_51job_api import parse_51job, dedupe_51job           # noqa: E402
from parse_liepin_api import parse_liepin, dedupe_liepin, parse_liepin_jobs  # noqa: E402
from match_engine import calculate_match                      # noqa: E402
from report_generator import generate_report                  # noqa: E402


def build_match_detail(match_result):
    """与 job_pipeline.batch_rank_jobs 保持一致的 match_detail 结构。"""
    dims = match_result['dimensions']
    return {
        'tech_score': dims['tech']['score'],
        'exp_score': dims['exp']['score'],
        'relevance_score': dims['relevance']['score'],
        'hard_score': dims['hard']['score'],
        'preference_score': dims['preference']['score'],
        'matched_skills': dims['tech']['matched'],
        'missing_skills': dims['tech']['missing'],
        'recommendation': match_result['recommendation'],
        'rec_color': match_result['rec_color'],
        'rec_detail': match_result.get('rec_detail', ''),
        'exp_notes': dims['exp']['notes'],
        'relevance_notes': dims['relevance']['notes'],
        'preference_notes': dims['preference']['notes'],
        'hard_passes': dims['hard']['passes'],
        'hard_issues': dims['hard']['issues'],
    }


def _parse_and_merge(input_paths):
    """读取一个或多个导出文件，分平台解析后跨文件去重，返回 (boss_jobs, zh_jobs, j5_jobs, lp_jobs)。"""
    boss_jobs, zh_jobs, j5_jobs, lp_jobs = [], [], [], []
    for raw_fp in input_paths:
        # 路径解析：先按原样（绝对/相对CWD），找不到再回退到相对工作区根目录
        fp = raw_fp
        if not os.path.exists(fp):
            cand = os.path.join(WORKSPACE, raw_fp)
            if os.path.exists(cand):
                fp = cand
        if not os.path.exists(fp):
            raise FileNotFoundError(f"导出JSON不存在: {raw_fp}（已尝试相对当前目录与工作区根目录）")
        with open(fp, 'r', encoding='utf-8-sig') as f:  # utf-8-sig 兼容Windows工具可能加的BOM
            raw = json.load(f)
        if (raw.get('zpData') or {}).get('jobList'):
            boss_jobs.extend(dedupe(extract_jobs(raw)))
        if raw.get('zhaopin_jobs'):
            zh_jobs.extend(parse_zhaopin(raw['zhaopin_jobs']))
        if raw.get('job51_jobs'):
            j5_jobs.extend(parse_51job(raw['job51_jobs']))
        if raw.get('liepin_jobs'):
            # 优先使用已补全JD的liepin_jobs
            lp_jobs.extend(parse_liepin_jobs(raw['liepin_jobs']))
        elif raw.get('liepin_raw'):
            # 否则从原始响应解析（无JD）
            lp_jobs.extend(parse_liepin(raw['liepin_raw']))

    # 跨文件再去重（同平台同岗位号，缺失时退化到 公司|岗位）
    def _dedup(jobs):
        seen, out = set(), []
        for j in jobs:
            k = (j.get('source', ''), j.get('encrypt_job_id', '') or f"{j.get('company')}|{j.get('position')}")
            if k in seen:
                continue
            seen.add(k)
            out.append(j)
        return out

    return _dedup(boss_jobs), _dedup(zh_jobs), _dedup(j5_jobs), _dedup(lp_jobs)


def generate_standalone_report(input_paths, output='', verbose=True):
    """从扩展导出JSON生成独立匹配报告（不写岗位库）。

    Args:
        input_paths: 一个或多个扩展导出JSON路径（BOSS/智联可混合，自动合并去重）
        output: 输出HTML路径；为空时落到 applications/ 并按岗位数自动命名
        verbose: 是否打印解析进度与Top10简表

    Returns:
        (out_path, scored_jobs, stats)
        stats: {'total','n_boss','n_zh','n_j51','avg','max','high'}
    """
    # 1) 解析合并
    boss_jobs, zh_jobs, j5_jobs, lp_jobs = _parse_and_merge(input_paths)
    jobs = boss_jobs + zh_jobs + j5_jobs + lp_jobs
    n_boss, n_zh, n_j51, n_lp = len(boss_jobs), len(zh_jobs), len(j5_jobs), len(lp_jobs)
    src_text = []
    if n_boss:
        src_text.append(f'BOSS直聘{n_boss}')
    if n_zh:
        src_text.append(f'智联招聘{n_zh}')
    if n_j51:
        src_text.append(f'前程无忧{n_j51}')
    if n_lp:
        src_text.append(f'猎聘{n_lp}')
    if not jobs:
        raise ValueError("这些导出JSON里没有解析到任何岗位（无 zpData.jobList / zhaopin_jobs / job51_jobs / liepin_raw），请确认是扩展导出的原始文件")
    if verbose:
        print(f'解析去重后岗位：{len(jobs)} 个（{"、".join(src_text)}）')

    # 2) 加载简历数据
    resume_path = os.path.join(WORKSPACE, 'resume_data.json')
    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"缺少简历数据文件: {resume_path}，请先生成/维护 resume_data.json")
    with open(resume_path, 'r', encoding='utf-8-sig') as f:
        resume_data = json.load(f)
    if verbose:
        print(f'简历：{resume_data.get("基本信息", {}).get("name", "?")} / '
              f'意向 {resume_data.get("基本信息", {}).get("job_intention", "?")}')

    # 3) 逐个匹配评分（不写岗位库，只在内存里打分）
    scored = []
    for job in jobs:
        jd_info = {
            'position': job.get('position', ''),
            'company': job.get('company', ''),
            'city': job.get('city', ''),
            'salary': job.get('salary', ''),
            'education': job.get('education', ''),
            'experience': job.get('experience', ''),
            'skills_required': job.get('skills', []),
            'responsibilities': job.get('responsibilities', ''),
            'requirements': job.get('requirements', ''),
            'company_size': job.get('company_size', ''),
            'company_industry': job.get('company_industry', ''),
        }
        mr = calculate_match(jd_info, resume_data)
        job['match_score'] = mr['total_score']
        job['match_detail'] = build_match_detail(mr)
        scored.append(job)

    scored.sort(key=lambda x: x.get('match_score', 0) or 0, reverse=True)

    # 4) 输出独立HTML
    if not output:
        out = os.path.join(WORKSPACE, 'applications',
                           f'采集{len(scored)}岗位_独立报告.html')
    else:
        out = output
        # 相对路径以工作区根目录为基准
        if not os.path.isabs(out):
            out = os.path.join(WORKSPACE, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    scores = [j['match_score'] for j in scored]
    src_join = '+'.join(src_text) if src_text else '采集'
    subtitle = f'共{len(scored)}个岗位（{src_join}），浏览器扩展被动采集 · 独立测试 · 未并入岗位库'
    notice = ('本报告由浏览器扩展在你本人Edge中被动采集生成，岗位卡片含明文薪资/技能标签/学历/经验等结构化信息，'
              'BOSS岗位可慢速补全完整JD；匹配度仅供参考，岗位是否投递请结合个人判断。')
    generate_report(scored, out, title=f'{src_join} 采集岗位 · 匹配测试报告',
                    subtitle=subtitle, notice=notice)

    stats = {
        'total': len(scored),
        'n_boss': n_boss,
        'n_zh': n_zh,
        'n_j51': n_j51,
        'n_lp': n_lp,
        'avg': round(sum(scores) / len(scores), 1),
        'max': max(scores),
        'high': len([s for s in scores if s >= 75]),
    }

    if verbose:
        print('\n=== Top 10 ===')
        for j in scored[:10]:
            print(f"  {j['match_score']:3d} | {j['position'][:14]:14s} | "
                  f"{j['salary'][:12]:12s} | {j.get('work_location','')[:12]:12s} | {j['company'][:18]}")
        print(f"\n平均匹配度 {stats['avg']}，最高 {stats['max']}，≥75共{stats['high']}个")
        print('输出:', os.path.abspath(out))

    return out, scored, stats


def main():
    ap = argparse.ArgumentParser(description='扩展采集JSON → 独立匹配报告（不写岗位库）')
    ap.add_argument('inputs', nargs='+', help='扩展导出的岗位JSON，可传多个（BOSS/智联/51job/猎聘）自动合并')
    ap.add_argument('-o', '--output', default='', help='输出HTML路径（默认落到 applications/ 自动命名）')
    args = ap.parse_args()
    try:
        generate_standalone_report(args.inputs, args.output)
    except Exception as e:
        print(f'[✗] 生成独立报告失败: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
