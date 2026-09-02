#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网申进度看板（apply_track）
阶段5：跟踪国企/大厂网申全流程，含截止提醒、状态时间线、OQ存档、HTML看板。

用法:
    python apply_track.py add --company "中国电信" --position "测绘工程师" --deadline "2026-10-15" --url "https://..."
    python apply_track.py update --id 1 --status 面试中 --note "一面已完成，等二面"
    python apply_track.py list [--status 面试中]
    python apply_track.py stats
    python apply_track.py deadline          # 截止提醒（7天内+已过期）
    python apply_track.py report            # 生成HTML看板报告
    python apply_track.py show --id 1       # 查看单条详情（含OQ存档/时间线）

状态: 待投递 / 已投递 / 测评中 / 面试中 / offer / 已拒绝 / 待定 / 放弃
"""
import json, io, os, sys, argparse, html as html_mod
from datetime import datetime, timedelta

WS = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(WS, "applications", "apply_tracking.json")
REPORT_DIR = os.path.join(WS, "applications")

VALID_STATUSES = ["待投递", "已投递", "测评中", "面试中", "offer", "已拒绝", "待定", "放弃"]
STATUS_COLORS = {
    "待投递": "#8c8c8c", "已投递": "#1890ff", "测评中": "#722ed1",
    "面试中": "#fa8c16", "offer": "#52c41a", "已拒绝": "#ff4d4f",
    "待定": "#faad14", "放弃": "#bfbfbf",
}


# ============================================================
# 数据层
# ============================================================

def load_data():
    if not os.path.exists(DATA_PATH):
        return {"records": []}
    with io.open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with io.open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def next_id(data):
    ids = [r.get("id", 0) for r in data.get("records", [])]
    return max(ids) + 1 if ids else 1


def find_record(data, rid):
    for r in data.get("records", []):
        if r.get("id") == rid:
            return r
    return None


# ============================================================
# 命令实现
# ============================================================

def cmd_add(args):
    data = load_data()
    record = {
        "id": next_id(data),
        "company": args.company,
        "position": args.position or "",
        "city": args.city or "",
        "batch": args.batch or "",
        "source": args.source or "",
        "apply_url": args.url or "",
        "account": args.account or "",
        "volunteer": args.volunteer or "",
        "system_type": args.system or "",
        "salary": args.salary or "",
        "cv_version": args.cv or "",
        "status": args.status or "待投递",
        "deadline": args.deadline or "",
        "apply_date": args.apply_date or datetime.now().strftime("%Y-%m-%d"),
        "oq_answers": {},
        "notes": args.note or "",
        "timeline": [{
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": args.status or "待投递",
            "note": "创建记录"
        }],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    if record["status"] not in VALID_STATUSES:
        print(f"错误: 状态 '{record['status']}' 无效，可选: {', '.join(VALID_STATUSES)}")
        return
    data["records"].append(record)
    save_data(data)
    print(f"✅ 已添加网申记录 #{record['id']}: {record['company']} - {record['position']}")
    print(f"   状态: {record['status']} | 截止: {record['deadline'] or '未设'} | 来源: {record['source'] or '未填'}")


def cmd_update(args):
    data = load_data()
    record = find_record(data, args.id)
    if not record:
        print(f"错误: 找不到记录 #{args.id}")
        return
    changed = []
    if args.status:
        if args.status not in VALID_STATUSES:
            print(f"错误: 状态 '{args.status}' 无效")
            return
        old = record["status"]
        record["status"] = args.status
        changed.append(f"状态: {old} → {args.status}")
        record["timeline"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": args.status,
            "note": args.note or "状态更新"
        })
    if args.note and not args.status:
        record["notes"] = (record.get("notes", "") + "\n" if record.get("notes") else "") + args.note
        changed.append(f"备注追加: {args.note[:30]}...")
    if args.deadline:
        record["deadline"] = args.deadline
        changed.append(f"截止日: {args.deadline}")
    if args.url:
        record["apply_url"] = args.url
        changed.append("网申入口已更新")
    record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_data(data)
    print(f"✅ 记录 #{args.id} 已更新: {record['company']} - {record['position']}")
    for c in changed:
        print(f"   - {c}")


def cmd_list(args):
    data = load_data()
    records = data.get("records", [])
    if args.status:
        records = [r for r in records if r.get("status") == args.status]
    if not records:
        print("暂无网申记录")
        return
    records.sort(key=lambda r: r.get("deadline", "9999") or "9999")
    print(f"共 {len(records)} 条记录（按截止日排序）:\n")
    print(f"{'ID':<4} {'公司':<20} {'岗位':<16} {'状态':<8} {'截止日':<12} {'投递日'}")
    print("-" * 80)
    for r in records:
        print(f"{r['id']:<4} {r['company'][:18]:<20} {r.get('position','')[:14]:<16} "
              f"{r.get('status',''):<8} {r.get('deadline','未设'):<12} {r.get('apply_date','')}")


def cmd_show(args):
    data = load_data()
    record = find_record(data, args.id)
    if not record:
        print(f"错误: 找不到记录 #{args.id}")
        return
    print(f"\n{'='*60}")
    print(f"  #{record['id']} {record['company']} - {record.get('position','')}")
    print(f"{'='*60}")
    for key, label in [("status","状态"),("deadline","截止日"),("apply_date","投递日"),
                        ("city","城市"),("batch","批次"),("source","来源平台"),
                        ("system_type","网申系统"),("salary","薪资"),("cv_version","简历版本"),
                        ("account","账号"),("volunteer","志愿"),("apply_url","网申入口")]:
        val = record.get(key, "")
        if val:
            print(f"  {label}: {val}")
    if record.get("notes"):
        print(f"\n  备注:\n{record['notes']}")
    if record.get("oq_answers"):
        print(f"\n  OQ答案存档 ({len(record['oq_answers'])}题):")
        for q, a in list(record["oq_answers"].items())[:5]:
            print(f"    Q: {q[:40]}\n    A: {str(a)[:60]}...")
    tl = record.get("timeline", [])
    if tl:
        print(f"\n  状态时间线:")
        for t in tl:
            print(f"    [{t.get('date','')}] {t.get('status','')} - {t.get('note','')}")
    print()


def cmd_stats(args):
    data = load_data()
    records = data.get("records", [])
    if not records:
        print("暂无数据")
        return
    print(f"网申进度统计（共 {len(records)} 条）\n")
    # 按状态统计
    print("【按状态】")
    for s in VALID_STATUSES:
        cnt = sum(1 for r in records if r.get("status") == s)
        if cnt:
            print(f"  {s}: {cnt}")
    # 截止提醒
    print("\n【截止提醒】")
    today = datetime.now().date()
    urgent = expired = upcoming = 0
    for r in records:
        dl = r.get("deadline", "")
        if not dl:
            continue
        try:
            dl_date = datetime.strptime(dl, "%Y-%m-%d").date()
            days = (dl_date - today).days
            if days < 0:
                expired += 1
            elif days <= 3:
                urgent += 1
            elif days <= 7:
                upcoming += 1
        except ValueError:
            pass
    print(f"  已过期: {expired} | 3天内截止: {urgent} | 7天内截止: {upcoming}")
    # 通过率
    offers = sum(1 for r in records if r.get("status") == "offer")
    rejected = sum(1 for r in records if r.get("status") == "已拒绝")
    decided = offers + rejected
    if decided > 0:
        print(f"\n【通过率】 offer: {offers} | 拒绝: {rejected} | 通过率: {offers/decided*100:.1f}%")


def cmd_deadline(args):
    data = load_data()
    records = data.get("records", [])
    today = datetime.now().date()
    expired, urgent, upcoming = [], [], []
    for r in records:
        dl = r.get("deadline", "")
        if not dl or r.get("status") in ["已拒绝", "放弃", "offer"]:
            continue
        try:
            dl_date = datetime.strptime(dl, "%Y-%m-%d").date()
            days = (dl_date - today).days
            item = (days, r)
            if days < 0:
                expired.append(item)
            elif days <= 3:
                urgent.append(item)
            elif days <= 7:
                upcoming.append(item)
        except ValueError:
            pass
    print(f"截止提醒（{today}）\n")
    if expired:
        print("❌ 已过期:")
        for days, r in sorted(expired):
            print(f"   #{r['id']} {r['company']} - {r.get('position','')} (截止 {r['deadline']}, 已过{-days}天)")
    if urgent:
        print("\n⚠️  3天内截止:")
        for days, r in sorted(urgent):
            print(f"   #{r['id']} {r['company']} - {r.get('position','')} (截止 {r['deadline']}, 还剩{days}天)")
    if upcoming:
        print("\n📅 7天内截止:")
        for days, r in sorted(upcoming):
            print(f"   #{r['id']} {r['company']} - {r.get('position','')} (截止 {r['deadline']}, 还剩{days}天)")
    if not expired and not urgent and not upcoming:
        print("✅ 近期无截止提醒")


def cmd_report(args):
    """生成HTML看板报告（统一主题）"""
    import report_theme as T
    data = load_data()
    records = data.get("records", [])
    today = datetime.now().date()

    # 统计
    status_counts = {s: sum(1 for r in records if r.get("status") == s) for s in VALID_STATUSES}
    active = sum(1 for r in records if r.get("status") not in ["已拒绝", "放弃"])
    expired = urgent = upcoming = 0
    for r in records:
        dl = r.get("deadline", "")
        if not dl or r.get("status") in ["已拒绝", "放弃", "offer"]:
            continue
        try:
            days = (datetime.strptime(dl, "%Y-%m-%d").date() - today).days
            if days < 0: expired += 1
            elif days <= 3: urgent += 1
            elif days <= 7: upcoming += 1
        except ValueError:
            pass

    # 统计卡
    stats_html = T.stat_grid([
        (str(len(records)), "网申总数"),
        (str(active), "进行中", "#1890ff"),
        (str(status_counts.get("offer", 0)), "已offer", "#52c41a"),
        (str(status_counts.get("已拒绝", 0)), "已拒绝", "#ff4d4f"),
        (str(urgent), "3天内截止", "#fa8c16"),
        (str(expired), "已过期", "#ff4d4f"),
    ])

    # 截止提醒区
    deadline_html = ""
    dl_items = []
    for r in records:
        dl = r.get("deadline", "")
        if not dl or r.get("status") in ["已拒绝", "放弃", "offer"]:
            continue
        try:
            days = (datetime.strptime(dl, "%Y-%m-%d").date() - today).days
            if days <= 7:
                dl_items.append((days, r))
        except ValueError:
            pass
    if dl_items:
        dl_items.sort(key=lambda x: x[0])
        body = '<div style="display:flex;flex-direction:column;gap:6px;">'
        for days, r in dl_items:
            if days < 0:
                color, label = "#ff4d4f", f"已过期{-days}天"
            elif days <= 3:
                color, label = "#fa8c16", f"还剩{days}天"
            else:
                color, label = "#faad14", f"还剩{days}天"
            url_link = f'<a href="{r.get("apply_url","#")}" target="_blank" style="color:#1890ff;text-decoration:none;font-size:12px;">网申入口</a>' if r.get("apply_url") else ""
            body += (f'<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;'
                     f'background:#fafafa;border-radius:6px;border-left:4px solid {color};">'
                     f'<span style="font-weight:600;font-size:13px;min-width:160px;">{T.esc(r["company"])}</span>'
                     f'<span style="font-size:12px;color:#666;flex:1;">{T.esc(r.get("position",""))}</span>'
                     f'<span style="font-size:12px;color:{color};font-weight:600;min-width:80px;">{label}</span>'
                     f'<span style="font-size:11px;color:#999;">截止 {r["deadline"]}</span>'
                     f'{url_link}</div>')
        body += "</div>"
        deadline_html = f'<div class="check-section">{T.section_title("⏰ 截止提醒（7天内）")}{body}</div>'

    # 按状态分组的记录
    sections_html = ""
    for status in VALID_STATUSES:
        group = [r for r in records if r.get("status") == status]
        if not group:
            continue
        color = STATUS_COLORS.get(status, "#888")
        body = '<div style="display:flex;flex-direction:column;gap:8px;">'
        for r in group:
            dl_info = f"截止 {r['deadline']}" if r.get("deadline") else "未设截止"
            meta = f"{r.get('city','')} | {r.get('batch','')} | {r.get('source','')} | 投递 {r.get('apply_date','')}"
            meta = " | ".join(x for x in meta.split(" | ") if x.strip())
            url_link = f'<a href="{r.get("apply_url","#")}" target="_blank" style="color:#1890ff;text-decoration:none;font-size:12px;">网申入口</a>' if r.get("apply_url") else ""
            body += (f'<div style="padding:10px 14px;background:#fff;border:1px solid #e8e8e8;border-radius:8px;'
                     f'border-left:4px solid {color};">'
                     f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                     f'<span style="font-weight:600;font-size:14px;">#{r["id"]} {T.esc(r["company"])}</span>'
                     f'<span style="font-size:12px;color:#666;">{T.esc(r.get("position",""))}</span>'
                     f'<span style="font-size:11px;background:{color};color:#fff;padding:1px 8px;border-radius:10px;margin-left:auto;">{status}</span>'
                     f'</div>'
                     f'<div style="font-size:11px;color:#999;margin-bottom:4px;">{T.esc(meta)} | {dl_info}</div>'
                     f'<div style="display:flex;gap:12px;align-items:center;">'
                     f'{url_link}'
                     f'<a href="javascript:void(0)" onclick="alert(\'ID: {r["id"]}\\n公司: {T.esc(r["company"])}\\n岗位: {T.esc(r.get("position",""))}\\n状态: {r["status"]}\\n备注: {T.esc(str(r.get("notes","无")))}\')" style="color:#8c8c8c;text-decoration:none;font-size:12px;">详情</a>'
                     f'</div></div>')
        body += "</div>"
        sections_html += f'<div class="check-section">{T.section_title(f"{status}（{len(group)}）")}{body}</div>'

    # 空状态
    if not records:
        empty_body = ('<div style="padding:30px;text-align:center;color:#999;font-size:14px;">'
            '还没有网申记录，使用 <code>python apply_track.py add --company "公司名" --position "岗位" --deadline "2026-10-15"</code> 添加第一条</div>')
        sections_html = f'<div class="check-section">{T.section_title("暂无网申记录")}{empty_body}</div>' 

    content = stats_html + deadline_html + sections_html
    html = T.page("📊 网申进度看板",
                  f"跟踪 {len(records)} 条网申记录 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                  content)
    os.makedirs(REPORT_DIR, exist_ok=True)
    output = os.path.join(REPORT_DIR, f"网申进度看板_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    with io.open(output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 看板报告已生成: {output}")
    return output


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="网申进度看板", formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="添加网申记录")
    p_add.add_argument("--company", required=True, help="公司名称")
    p_add.add_argument("--position", help="岗位名称")
    p_add.add_argument("--city", help="工作城市")
    p_add.add_argument("--batch", help="招聘批次（如2027届秋招第一批）")
    p_add.add_argument("--source", help="来源平台（国聘/牛客/前程无忧/公司官网等）")
    p_add.add_argument("--url", help="网申入口URL")
    p_add.add_argument("--account", help="网申账号")
    p_add.add_argument("--volunteer", help="志愿/意向部门")
    p_add.add_argument("--system", help="网申系统类型（北森/Moka/前程/智联/自研）")
    p_add.add_argument("--salary", help="薪资范围")
    p_add.add_argument("--cv", help="使用的简历版本")
    p_add.add_argument("--status", default="待投递", choices=VALID_STATUSES, help="初始状态")
    p_add.add_argument("--deadline", help="截止日期 YYYY-MM-DD")
    p_add.add_argument("--apply-date", help="投递日期 YYYY-MM-DD（默认今天）")
    p_add.add_argument("--note", help="备注")

    p_upd = sub.add_parser("update", help="更新记录状态/备注")
    p_upd.add_argument("--id", type=int, required=True, help="记录ID")
    p_upd.add_argument("--status", choices=VALID_STATUSES, help="新状态")
    p_upd.add_argument("--deadline", help="更新截止日")
    p_upd.add_argument("--url", help="更新网申入口")
    p_upd.add_argument("--note", help="追加备注")

    p_list = sub.add_parser("list", help="查看记录列表")
    p_list.add_argument("--status", choices=VALID_STATUSES, help="按状态筛选")

    p_show = sub.add_parser("show", help="查看单条详情")
    p_show.add_argument("--id", type=int, required=True, help="记录ID")

    sub.add_parser("stats", help="统计分析")
    sub.add_parser("deadline", help="截止提醒")
    sub.add_parser("report", help="生成HTML看板报告")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    {"add": cmd_add, "update": cmd_update, "list": cmd_list, "show": cmd_show,
     "stats": cmd_stats, "deadline": cmd_deadline, "report": cmd_report}[args.command](args)


if __name__ == "__main__":
    main()
