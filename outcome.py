#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
申请结果归档工具（outcome）
管理投递记录、状态跟踪、统计分析。

用法:
    python outcome.py add --company "公司名" --position "岗位名" [其他参数]
    python outcome.py update --id <编号> --status <新状态> [--note "备注"]
    python outcome.py list [--status <状态筛选>]
    python outcome.py stats [输出目录]
    python outcome.py report [输出目录]

状态说明:
    待投递 / 已投递 / 笔试中 / 面试中 / 已offer / 已拒绝 / 无回应
"""

import json
import sys
import os
import re
import html as html_module
from datetime import datetime, timedelta


def escape(text):
    if not text:
        return ''
    return html_module.escape(str(text))


def get_apps_path(workspace):
    """获取申请记录文件路径"""
    return os.path.join(workspace, 'applications', 'applications.json')


def load_apps(workspace):
    """加载申请记录"""
    path = get_apps_path(workspace)
    if not os.path.exists(path):
        return {'applications': []}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_apps(workspace, data):
    """保存申请记录"""
    path = get_apps_path(workspace)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_id(apps):
    """生成新的申请编号"""
    existing_ids = [a.get('id', 0) for a in apps.get('applications', [])]
    return max(existing_ids) + 1 if existing_ids else 1


def cmd_add(workspace, args):
    """添加投递记录"""
    company = ''
    position = ''
    city = ''
    source = ''
    cv_version = ''
    salary = ''
    jd_link = ''
    notes = ''
    apply_date = datetime.now().strftime('%Y-%m-%d')
    status = '已投递'

    i = 0
    while i < len(args):
        if args[i] == '--company' and i + 1 < len(args):
            company = args[i + 1]; i += 2
        elif args[i] == '--position' and i + 1 < len(args):
            position = args[i + 1]; i += 2
        elif args[i] == '--city' and i + 1 < len(args):
            city = args[i + 1]; i += 2
        elif args[i] == '--source' and i + 1 < len(args):
            source = args[i + 1]; i += 2
        elif args[i] == '--cv' and i + 1 < len(args):
            cv_version = args[i + 1]; i += 2
        elif args[i] == '--salary' and i + 1 < len(args):
            salary = args[i + 1]; i += 2
        elif args[i] == '--jd' and i + 1 < len(args):
            jd_link = args[i + 1]; i += 2
        elif args[i] == '--notes' and i + 1 < len(args):
            notes = args[i + 1]; i += 2
        elif args[i] == '--date' and i + 1 < len(args):
            apply_date = args[i + 1]; i += 2
        elif args[i] == '--status' and i + 1 < len(args):
            status = args[i + 1]; i += 2
        else:
            i += 1

    if not company or not position:
        print('错误: 公司名和岗位名是必填项')
        print('用法: python outcome.py add --company "公司名" --position "岗位名" [其他参数]')
        return

    apps = load_apps(workspace)
    new_id = generate_id(apps)

    new_app = {
        'id': new_id,
        'company': company,
        'position': position,
        'city': city,
        'apply_date': apply_date,
        'source': source,
        'cv_version': cv_version,
        'status': status,
        'salary': salary,
        'jd_link': jd_link,
        'notes': notes,
        'history': [
            {'date': apply_date, 'status': status, 'note': '创建记录'}
        ]
    }

    apps['applications'].append(new_app)
    save_apps(workspace, apps)

    print(f'✅ 投递记录已添加！')
    print(f'   编号: {new_id}')
    print(f'   公司: {company}')
    print(f'   岗位: {position}')
    print(f'   状态: {status}')
    print(f'   日期: {apply_date}')


def cmd_update(workspace, args):
    """更新投递状态"""
    app_id = None
    new_status = ''
    note = ''

    i = 0
    while i < len(args):
        if args[i] == '--id' and i + 1 < len(args):
            app_id = int(args[i + 1]); i += 2
        elif args[i] == '--status' and i + 1 < len(args):
            new_status = args[i + 1]; i += 2
        elif args[i] == '--note' and i + 1 < len(args):
            note = args[i + 1]; i += 2
        else:
            i += 1

    if app_id is None or not new_status:
        print('错误: 编号和新状态是必填项')
        print('用法: python outcome.py update --id <编号> --status <新状态> [--note "备注"]')
        return

    valid_statuses = ['待投递', '已投递', '笔试中', '面试中', '已offer', '已拒绝', '无回应']
    if new_status not in valid_statuses:
        print(f'错误: 状态必须是以下之一: {", ".join(valid_statuses)}')
        return

    apps = load_apps(workspace)
    found = False
    for app in apps['applications']:
        if app['id'] == app_id:
            old_status = app['status']
            app['status'] = new_status
            today = datetime.now().strftime('%Y-%m-%d')
            app['history'].append({
                'date': today,
                'status': new_status,
                'note': note or f'状态从 {old_status} 变更为 {new_status}'
            })
            found = True
            print(f'✅ 状态已更新！')
            print(f'   编号: {app_id}')
            print(f'   公司: {app["company"]}')
            print(f'   岗位: {app["position"]}')
            print(f'   状态: {old_status} → {new_status}')
            if note:
                print(f'   备注: {note}')
            break

    if not found:
        print(f'错误: 未找到编号为 {app_id} 的记录')

    save_apps(workspace, apps)


def cmd_list(workspace, args):
    """查看投递记录列表"""
    status_filter = None
    i = 0
    while i < len(args):
        if args[i] == '--status' and i + 1 < len(args):
            status_filter = args[i + 1]; i += 2
        else:
            i += 1

    apps = load_apps(workspace)
    app_list = apps.get('applications', [])

    if status_filter:
        app_list = [a for a in app_list if a.get('status') == status_filter]

    if not app_list:
        print('暂无投递记录')
        return

    # 状态颜色映射
    status_colors = {
        '待投递': '\033[90m',
        '已投递': '\033[94m',
        '笔试中': '\033[93m',
        '面试中': '\033[96m',
        '已offer': '\033[92m',
        '已拒绝': '\033[91m',
        '无回应': '\033[90m',
    }
    reset = '\033[0m'

    print(f'{"="*80}')
    print(f'{"ID":<4} {"公司":<15} {"岗位":<15} {"城市":<8} {"日期":<12} {"状态":<8}')
    print(f'{"="*80}')
    for app in sorted(app_list, key=lambda x: x.get('apply_date', ''), reverse=True):
        color = status_colors.get(app.get('status', ''), '')
        print(f'{app.get("id",""):<4} {app.get("company","")[:14]:<15} {app.get("position","")[:14]:<15} {app.get("city","")[:7]:<8} {app.get("apply_date",""):<12} {color}{app.get("status","")}{reset}')
    print(f'{"="*80}')
    print(f'共 {len(app_list)} 条记录')


def cmd_stats(workspace, args):
    """统计分析"""
    apps = load_apps(workspace)
    app_list = apps.get('applications', [])

    if not app_list:
        print('暂无投递记录，无法统计')
        return

    total = len(app_list)

    # 按状态统计
    status_counts = {}
    for app in app_list:
        s = app.get('status', '未知')
        status_counts[s] = status_counts.get(s, 0) + 1

    # 按公司统计
    company_counts = {}
    for app in app_list:
        c = app.get('company', '未知')
        company_counts[c] = company_counts.get(c, 0) + 1

    # 按渠道统计
    source_counts = {}
    for app in app_list:
        s = app.get('source', '未填写')
        source_counts[s] = source_counts.get(s, 0) + 1

    # 按简历版本统计
    cv_counts = {}
    for app in app_list:
        v = app.get('cv_version', '未填写')
        cv_counts[v] = cv_counts.get(v, 0) + 1

    # 计算关键指标
    delivered = status_counts.get('已投递', 0) + status_counts.get('笔试中', 0) + status_counts.get('面试中', 0) + status_counts.get('已offer', 0) + status_counts.get('已拒绝', 0) + status_counts.get('无回应', 0)
    in_process = status_counts.get('笔试中', 0) + status_counts.get('面试中', 0)
    offers = status_counts.get('已offer', 0)
    rejected = status_counts.get('已拒绝', 0)
    no_response = status_counts.get('无回应', 0)

    # 面试转化率
    interview_rate = (status_counts.get('面试中', 0) + offers) / delivered * 100 if delivered > 0 else 0
    # offer率
    offer_rate = offers / delivered * 100 if delivered > 0 else 0

    print()
    print('='*60)
    print('📊 投递统计分析')
    print('='*60)
    print(f'总投递数: {total}')
    print()
    print('【状态分布】')
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        bar = '█' * int(pct / 2) + '░' * (25 - int(pct / 2))
        print(f'  {status:<8} {count:>3} ({pct:>5.1f}%) {bar}')
    print()
    print('【关键指标】')
    print(f'  进行中（笔试/面试）: {in_process}')
    print(f'  已获offer: {offers}')
    print(f'  已拒绝: {rejected}')
    print(f'  无回应: {no_response}')
    print(f'  面试转化率: {interview_rate:.1f}%')
    print(f'  offer率: {offer_rate:.1f}%')
    print()
    print('【投递渠道】')
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {source}: {count}')
    print()
    print('【使用简历版本】')
    for cv, count in sorted(cv_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {cv}: {count}')
    print('='*60)


def cmd_report(workspace, args):
    """生成HTML格式的统计报告"""
    output_dir = os.path.join(workspace, 'applications')
    if args and not args[0].startswith('--'):
        output_dir = args[0]

    apps = load_apps(workspace)
    app_list = apps.get('applications', [])

    if not app_list:
        print('暂无投递记录，无法生成报告')
        return

    total = len(app_list)

    # 按状态统计
    status_counts = {}
    for app in app_list:
        s = app.get('status', '未知')
        status_counts[s] = status_counts.get(s, 0) + 1

    # 按公司统计
    company_counts = {}
    for app in app_list:
        c = app.get('company', '未知')
        company_counts[c] = company_counts.get(c, 0) + 1

    # 计算关键指标
    delivered = sum(status_counts.values())
    in_process = status_counts.get('笔试中', 0) + status_counts.get('面试中', 0)
    offers = status_counts.get('已offer', 0)
    rejected = status_counts.get('已拒绝', 0)
    no_response = status_counts.get('无回应', 0)
    interview_rate = (status_counts.get('面试中', 0) + offers) / delivered * 100 if delivered > 0 else 0
    offer_rate = offers / delivered * 100 if delivered > 0 else 0

    # 状态颜色
    status_colors = {
        '待投递': '#95a5a6',
        '已投递': '#3498db',
        '笔试中': '#f39c12',
        '面试中': '#9b59b6',
        '已offer': '#27ae60',
        '已拒绝': '#e74c3c',
        '无回应': '#7f8c8d',
    }

    # 生成状态分布HTML
    status_bars = ''
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        color = status_colors.get(status, '#999')
        status_bars += f'''
        <div class="stat-row">
            <div class="stat-label">{escape(status)}</div>
            <div class="stat-bar-bg"><div class="stat-bar" style="width:{pct}%;background:{color}"></div></div>
            <div class="stat-value">{count} ({pct:.1f}%)</div>
        </div>'''

    # 生成投递记录表格
    table_rows = ''
    for app in sorted(app_list, key=lambda x: x.get('apply_date', ''), reverse=True):
        status = app.get('status', '')
        color = status_colors.get(status, '#999')
        table_rows += f'''
        <tr>
            <td>{app.get('id','')}</td>
            <td>{escape(app.get('company',''))}</td>
            <td>{escape(app.get('position',''))}</td>
            <td>{escape(app.get('city',''))}</td>
            <td>{escape(app.get('apply_date',''))}</td>
            <td>{escape(app.get('source',''))}</td>
            <td><span class="status-badge" style="background:{color}">{escape(status)}</span></td>
            <td>{escape(app.get('salary',''))}</td>
        </tr>'''

    report_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>求职投递统计报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", sans-serif; background: #f0f2f5; padding: 30px; color: #333; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #2c3e50, #8e44ad); color: white; padding: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 14px; opacity: 0.9; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ font-size: 18px; color: #2c3e50; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #8e44ad; }}
        .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .card {{ background: #f9f9f9; border-radius: 8px; padding: 20px; text-align: center; }}
        .card .number {{ font-size: 32px; font-weight: bold; color: #8e44ad; }}
        .card .label {{ font-size: 13px; color: #666; margin-top: 5px; }}
        .stat-row {{ display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }}
        .stat-label {{ width: 80px; font-size: 14px; color: #555; flex-shrink: 0; }}
        .stat-bar-bg {{ flex: 1; height: 24px; background: #f0f0f0; border-radius: 12px; overflow: hidden; }}
        .stat-bar {{ height: 100%; border-radius: 12px; transition: width 0.3s; }}
        .stat-value {{ width: 100px; font-size: 13px; color: #666; text-align: right; flex-shrink: 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #f5f5f5; padding: 10px 8px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #ddd; }}
        td {{ padding: 10px 8px; border-bottom: 1px solid #eee; }}
        tr:hover {{ background: #f9f9f9; }}
        .status-badge {{ color: white; padding: 3px 10px; border-radius: 10px; font-size: 12px; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>求职投递统计报告</h1>
            <div class="meta">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | 总投递数：{total}</div>
        </div>

        <div class="content">
            <div class="section">
                <h2>关键指标</h2>
                <div class="cards">
                    <div class="card"><div class="number">{total}</div><div class="label">总投递数</div></div>
                    <div class="card"><div class="number" style="color:#f39c12">{in_process}</div><div class="label">进行中</div></div>
                    <div class="card"><div class="number" style="color:#27ae60">{offers}</div><div class="label">已获offer</div></div>
                    <div class="card"><div class="number" style="color:#e74c3c">{rejected}</div><div class="label">已拒绝</div></div>
                </div>
                <div style="font-size:14px;color:#666;line-height:2">
                    无回应：{no_response} 家 | 面试转化率：{interview_rate:.1f}% | offer率：{offer_rate:.1f}%
                </div>
            </div>

            <div class="section">
                <h2>状态分布</h2>
                {status_bars}
            </div>

            <div class="section">
                <h2>投递记录明细</h2>
                <div style="overflow-x:auto">
                <table>
                    <thead>
                        <tr><th>ID</th><th>公司</th><th>岗位</th><th>城市</th><th>投递日期</th><th>渠道</th><th>状态</th><th>薪资</th></tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
                </div>
            </div>
        </div>

        <div class="footer">
            本报告由 job-search-assistant 自动生成
        </div>
    </div>
</body>
</html>'''

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, '投递统计报告.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_html)
    print(f'✅ 统计报告已生成: {output_path}')


def main():
    workspace = os.path.dirname(os.path.abspath(__file__))

    if len(sys.argv) < 2:
        print('用法:')
        print('  python outcome.py add --company "公司" --position "岗位" [其他参数]')
        print('  python outcome.py update --id <编号> --status <新状态> [--note "备注"]')
        print('  python outcome.py list [--status <状态筛选>]')
        print('  python outcome.py stats')
        print('  python outcome.py report [输出目录]')
        print()
        print('状态: 待投递/已投递/笔试中/面试中/已offer/已拒绝/无回应')
        return

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == 'add':
        cmd_add(workspace, args)
    elif command == 'update':
        cmd_update(workspace, args)
    elif command == 'list':
        cmd_list(workspace, args)
    elif command == 'stats':
        cmd_stats(workspace, args)
    elif command == 'report':
        cmd_report(workspace, args)
    else:
        print(f'未知命令: {command}')
        print('可用命令: add, update, list, stats, report')


if __name__ == '__main__':
    main()
