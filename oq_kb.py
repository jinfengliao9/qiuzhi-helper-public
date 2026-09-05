# -*- coding: utf-8 -*-
"""
OQ 开放式问题知识库管理器
管理本地生成的OQ答案，支持查询、搜索、添加、导出、统计。

用法：
  python oq_kb.py list                          # 列出所有公司的OQ答案
  python oq_kb.py list --company "公司名"       # 列出指定公司的所有答案
  python oq_kb.py search "关键词"                # 搜索所有答案中的问题/答案
  python oq_kb.py show --company "公司名" --qid "1.1"  # 查看指定答案
  python oq_kb.py add --company "公司名" --question "问题" --answer "答案"  # 添加答案
  python oq_kb.py export --company "公司名" -o output.md  # 导出公司所有答案为Markdown
  python oq_kb.py stats                         # 统计知识库情况
"""
import json, io, os, sys, argparse, re
from datetime import datetime

WS = os.path.dirname(os.path.abspath(__file__))
ANSWER_DIR = os.path.join(WS, "oq_answers")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_company_dir(company):
    """获取公司目录路径，处理特殊字符"""
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', company.strip())
    return os.path.join(ANSWER_DIR, safe_name)


def list_companies():
    """列出所有有OQ答案的公司"""
    if not os.path.exists(ANSWER_DIR):
        return []
    return [d for d in os.listdir(ANSWER_DIR)
            if os.path.isdir(os.path.join(ANSWER_DIR, d))]


def list_answers(company=None):
    """列出答案，可按公司筛选"""
    results = []
    companies = [company] if company else list_companies()
    for comp in companies:
        comp_dir = get_company_dir(comp)
        if not os.path.exists(comp_dir):
            continue
        for f in sorted(os.listdir(comp_dir)):
            if f.endswith('.json'):
                fpath = os.path.join(comp_dir, f)
                try:
                    with io.open(fpath, encoding='utf-8') as fp:
                        data = json.load(fp)
                    results.append({
                        'company': comp,
                        'qid': data.get('qid', f.replace('.json', '')),
                        'question': data.get('question', ''),
                        'category': data.get('category', ''),
                        'created': data.get('created', ''),
                        'answer_len': len(data.get('answer', '')),
                        'file': fpath
                    })
                except Exception:
                    pass
    return results


def search_answers(keyword):
    """搜索所有答案中的问题和答案内容"""
    results = []
    for ans in list_answers():
        text = ans['question'] + ' ' + ans.get('answer', '')
        # 重新读取答案内容
        try:
            with io.open(ans['file'], encoding='utf-8') as f:
                data = json.load(f)
            full_text = data.get('question', '') + ' ' + data.get('answer', '')
            if keyword.lower() in full_text.lower():
                results.append({
                    'company': ans['company'],
                    'qid': ans['qid'],
                    'question': data.get('question', ''),
                    'answer_preview': data.get('answer', '')[:100] + '...' if len(data.get('answer', '')) > 100 else data.get('answer', ''),
                    'file': ans['file']
                })
        except Exception:
            pass
    return results


def add_answer(company, question, answer, category='自定义', qid=None):
    """添加一条OQ答案到知识库"""
    comp_dir = get_company_dir(company)
    ensure_dir(comp_dir)

    if qid is None:
        # 自动生成qid：custom_时间戳
        qid = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    data = {
        'qid': qid,
        'category': category,
        'question': question,
        'answer': answer,
        'company': company,
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': 1,
        'rating': None  # 用户评分：1-5，None表示未评分
    }

    fname = f"{qid}.json"
    fpath = os.path.join(comp_dir, fname)
    with io.open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return fpath


def export_company(company, output_path):
    """导出指定公司的所有答案为Markdown"""
    answers = list_answers(company)
    if not answers:
        return False

    lines = [f"# {company} - OQ开放式问题答案汇总\n"]
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 共 {len(answers)} 道题\n")
    lines.append("---\n")

    # 按分类分组
    by_category = {}
    for ans in answers:
        cat = ans.get('category', '未分类')
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(ans)

    for cat, cat_answers in sorted(by_category.items()):
        lines.append(f"\n## {cat}（{len(cat_answers)}题）\n")
        for ans in sorted(cat_answers, key=lambda x: x['qid']):
            try:
                with io.open(ans['file'], encoding='utf-8') as f:
                    data = json.load(f)
                lines.append(f"### [{ans['qid']}] {data.get('question', '')}\n")
                lines.append(data.get('answer', ''))
                lines.append(f"\n*创建时间：{data.get('created', '')}*\n")
                lines.append("---\n")
            except Exception:
                pass

    with io.open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return True


def show_stats():
    """显示知识库统计"""
    companies = list_companies()
    total_answers = len(list_answers())

    print("=" * 50)
    print("OQ 知识库统计")
    print("=" * 50)
    print(f"公司数量：{len(companies)}")
    print(f"答案总数：{total_answers}")
    print()

    if companies:
        print("各公司答案分布：")
        for comp in sorted(companies):
            count = len(list_answers(comp))
            print(f"  {comp}：{count} 题")

    print()
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='OQ开放式问题知识库管理器')
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # list
    p_list = subparsers.add_parser('list', help='列出答案')
    p_list.add_argument('--company', help='按公司筛选')

    # search
    p_search = subparsers.add_parser('search', help='搜索答案')
    p_search.add_argument('keyword', help='搜索关键词')

    # show
    p_show = subparsers.add_parser('show', help='查看指定答案')
    p_show.add_argument('--company', required=True, help='公司名')
    p_show.add_argument('--qid', required=True, help='题目ID')

    # add
    p_add = subparsers.add_parser('add', help='添加答案')
    p_add.add_argument('--company', required=True, help='公司名')
    p_add.add_argument('--question', required=True, help='问题')
    p_add.add_argument('--answer', required=True, help='答案')
    p_add.add_argument('--category', default='自定义', help='分类')
    p_add.add_argument('--qid', help='题目ID（可选）')

    # export
    p_export = subparsers.add_parser('export', help='导出公司答案为Markdown')
    p_export.add_argument('--company', required=True, help='公司名')
    p_export.add_argument('-o', '--output', required=True, help='输出文件路径')

    # stats
    subparsers.add_parser('stats', help='统计知识库情况')

    args = parser.parse_args()

    if args.command == 'list':
        answers = list_answers(args.company)
        if not answers:
            print("暂无OQ答案")
            return
        print(f"共 {len(answers)} 条答案：\n")
        for ans in answers:
            print(f"[{ans['company']}] [{ans['qid']}] {ans['question'][:50]}... ({ans['answer_len']}字)")

    elif args.command == 'search':
        results = search_answers(args.keyword)
        if not results:
            print(f"未找到包含「{args.keyword}」的答案")
            return
        print(f"找到 {len(results)} 条匹配答案：\n")
        for r in results:
            print(f"[{r['company']}] [{r['qid']}] {r['question']}")
            print(f"  答案预览：{r['answer_preview']}\n")

    elif args.command == 'show':
        comp_dir = get_company_dir(args.company)
        fpath = os.path.join(comp_dir, f"{args.qid}.json")
        if not os.path.exists(fpath):
            print(f"未找到答案：{args.company}/{args.qid}")
            return
        with io.open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        print(f"公司：{data.get('company', '')}")
        print(f"分类：{data.get('category', '')}")
        print(f"问题：{data.get('question', '')}")
        print(f"\n答案：\n{data.get('answer', '')}")
        print(f"\n创建时间：{data.get('created', '')}")
        print(f"版本：{data.get('version', 1)}")

    elif args.command == 'add':
        fpath = add_answer(args.company, args.question, args.answer, args.category, args.qid)
        print(f"✅ 答案已保存：{fpath}")

    elif args.command == 'export':
        success = export_company(args.company, args.output)
        if success:
            print(f"✅ 已导出到：{args.output}")
        else:
            print(f"❌ 未找到公司「{args.company}」的答案")

    elif args.command == 'stats':
        show_stats()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
