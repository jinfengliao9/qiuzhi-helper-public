# -*- coding: utf-8 -*-
"""
求职工作区 - 统一工作流引擎
整合所有功能，提供统一的命令行接口

使用方法：
    python job_search.py <command> [options]

命令列表：
    setup           初始化个人资料
    resume          生成简历（4套模板）
    rank            职位匹配评估
    apply           生成定制简历（根据JD）
    interview       面试准备
    outcome         申请归档管理
    check           简历格式检查
    jobs            岗位库管理
    collect         扩展采集JSON生成独立报告（不入库）
    config          配置管理
    validate        数据验证
    campus          校招网申模块（机筛检查/网申雷达/OQ生成/信息底座）
    help            显示帮助信息

示例：
    python job_search.py resume
    python job_search.py rank --jd job_description.txt
    python job_search.py apply --jd job_description.txt
    python job_search.py interview --company "广州市城市更新规划设计研究院" --position "测绘技术人员"
    python job_search.py outcome add --company "公司名" --position "岗位名"
    python job_search.py jobs report
    python job_search.py config show
"""

import os
import sys
import argparse
import json
from datetime import datetime

# 添加工作区目录到路径
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# 导入工具模块
from utils.config import get_config, get_workspace_dir, print_config_summary, validate_config
from utils.validator import validate_resume, validate_jobs_list, validate_applications_list


# ============================================================
# 通用工具函数
# ============================================================

def print_banner():
    """打印欢迎横幅"""
    print("=" * 60)
    print("  求职工作区 - 统一工作流引擎")
    print("  Job Search Assistant - Workflow Engine")
    print("=" * 60)
    print()


def print_success(message):
    """打印成功消息"""
    print(f"[✓] {message}")


def print_error(message):
    """打印错误消息"""
    print(f"[✗] {message}")


def print_info(message):
    """打印信息消息"""
    print(f"[i] {message}")


def print_warning(message):
    """打印警告消息"""
    print(f"[!] {message}")


def load_json_file(filepath, description="文件"):
    """
    加载JSON文件

    Args:
        filepath: 文件路径
        description: 文件描述（用于错误消息）

    Returns:
        dict/list: JSON数据
    """
    if not os.path.exists(filepath):
        print_error(f"{description}不存在: {filepath}")
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"加载{description}失败: {str(e)}")
        return None


def save_json_file(data, filepath, description="文件"):
    """
    保存JSON文件

    Args:
        data: 要保存的数据
        filepath: 文件路径
        description: 文件描述（用于错误消息）

    Returns:
        bool: 是否成功
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print_error(f"保存{description}失败: {str(e)}")
        return False


# ============================================================
# 命令处理函数
# ============================================================

def cmd_setup(args):
    """初始化个人资料"""
    print_banner()
    print_info("初始化个人资料...")
    print()

    profile_dir = os.path.join(WORKSPACE_DIR, "profile")
    os.makedirs(profile_dir, exist_ok=True)

    candidate_path = os.path.join(profile_dir, "candidate.md")
    preferences_path = os.path.join(profile_dir, "preferences.md")

    if os.path.exists(candidate_path):
        print_warning("个人资料已存在，是否覆盖？(y/n)")
        choice = input().strip().lower()
        if choice != 'y':
            print_info("已取消初始化")
            return

    # 收集基本信息
    print("请输入您的基本信息：")
    name = input("姓名: ").strip()
    phone = input("电话: ").strip()
    email = input("邮箱: ").strip()
    city = input("所在城市: ").strip()
    job_intention = input("求职意向: ").strip()

    # 生成candidate.md
    candidate_content = f"""# 个人资料

## 基本信息
- 姓名：{name}
- 电话：{phone}
- 邮箱：{email}
- 所在城市：{city}
- 求职意向：{job_intention}

## 教育背景
（请补充）

## 实习/工作经历
（请补充）

## 项目经历
（请补充）

## 技能清单
（请补充）

## 获奖经历
（请补充，如无可删除）

## 证书
（请补充，如无可删除）

## 自我评价
（请补充）
"""

    with open(candidate_path, 'w', encoding='utf-8') as f:
        f.write(candidate_content)

    # 生成preferences.md
    preferences_content = """# 求职偏好

## 目标岗位
（请补充，如：测绘工程师、GIS工程师等）

## 目标行业
（请补充，如：测绘、地理信息、国土资源等）

## 目标城市
（请补充，如：广州、深圳、长沙等）

## 薪资期望
（请补充，如：6000-10000元/月）

## 硬约束
（请补充，如：不接受加班、只考虑国企、不考虑外包等）

## 特别想去的公司类型
（请补充）

## 特别不想去的公司类型
（请补充）
"""

    with open(preferences_path, 'w', encoding='utf-8') as f:
        f.write(preferences_content)

    print_success(f"个人资料已初始化: {candidate_path}")
    print_success(f"求职偏好已初始化: {preferences_path}")
    print()
    print_info("请编辑上述文件，补充完整的个人信息和求职偏好")
    print_info("完成后可以运行 'python job_search.py resume' 生成简历")


def cmd_resume(args):
    """生成简历"""
    print_banner()
    print_info("生成简历...")
    print()

    # 检查简历数据
    resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
    if not os.path.exists(resume_path):
        print_error("简历数据文件不存在: resume_data.json")
        print_info("请先运行 'python job_search.py setup' 初始化个人资料")
        return

    # 验证简历数据
    resume_data = load_json_file(resume_path, "简历数据")
    if resume_data:
        errors = validate_resume(resume_data)
        if errors:
            print_warning(f"简历数据验证发现 {len(errors)} 个问题:")
            for e in errors[:5]:
                print(f"  - {e}")
            print()

    # 调用generate_selected.py生成简历
    try:
        import generate_selected
        # 临时修改sys.argv，避免generate_selected.main()误读job_search.py的参数
        original_argv = sys.argv
        sys.argv = ['generate_selected.py']
        generate_selected.main()
        sys.argv = original_argv
        print_success("简历生成完成！")
    except Exception as e:
        print_error(f"简历生成失败: {str(e)}")
        print_info("请检查resume_data.json格式是否正确")
        import traceback
        traceback.print_exc()


def cmd_rank(args):
    """职位匹配评估"""
    print_banner()
    print_info("职位匹配评估...")
    print()

    # 获取JD文本
    jd_text = ""
    if args.jd:
        if os.path.exists(args.jd):
            with open(args.jd, 'r', encoding='utf-8') as f:
                jd_text = f.read()
            print_info(f"已从文件加载JD: {args.jd}")
        else:
            jd_text = args.jd
            print_info("已从参数获取JD文本")
    else:
        print("请输入职位描述（JD），输入完成后按Ctrl+Z回车结束：")
        jd_text = sys.stdin.read()

    if not jd_text.strip():
        print_error("JD文本为空")
        return

    # 调用rank.py进行匹配评估
    try:
        import rank
        # 临时修改sys.argv，传递JD文件路径或文本
        original_argv = sys.argv
        if args.jd and os.path.exists(args.jd):
            sys.argv = ['rank.py', args.jd]
        elif jd_text:
            # 将JD文本保存为临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(jd_text)
                temp_jd_path = f.name
            sys.argv = ['rank.py', temp_jd_path]
        else:
            sys.argv = ['rank.py']
        rank.main()
        sys.argv = original_argv
        print_success("匹配评估完成！")
    except Exception as e:
        print_error(f"匹配评估失败: {str(e)}")
        import traceback
        traceback.print_exc()


def cmd_apply(args):
    """生成定制简历"""
    print_banner()
    print_info("生成定制简历...")
    print()

    # 先进行匹配评估
    cmd_rank(args)

    print()
    print_info("根据JD生成定制简历...")
    print_info("（定制简历功能正在开发中，当前使用通用简历模板）")
    print()

    # 生成通用简历
    cmd_resume(args)


def cmd_interview(args):
    """面试准备"""
    print_banner()
    print_info("面试准备...")
    print()

    company = args.company
    position = args.position

    if not company or not position:
        print_error("请提供公司名称和岗位名称")
        print_info("使用方法: python job_search.py interview --company <公司> --position <岗位>")
        return

    print_info(f"公司: {company}")
    print_info(f"岗位: {position}")
    print()

    # 调用interview.py生成面试准备
    try:
        import interview
        # 临时修改sys.argv传递参数
        original_argv = sys.argv
        sys.argv = ['interview.py', '--company', company, '--position', position]
        interview.main()
        sys.argv = original_argv
        print_success("面试准备完成！")
    except Exception as e:
        print_error(f"面试准备失败: {str(e)}")
        import traceback
        traceback.print_exc()


def cmd_outcome(args):
    """申请归档管理"""
    print_banner()
    print_info("申请归档管理...")
    print()

    # 调用outcome.py
    try:
        import outcome
        # 构建参数
        outcome_args = ['outcome.py']
        if hasattr(args, 'subcommand') and args.subcommand:
            outcome_args.append(args.subcommand)
            if args.subcommand == 'add':
                if args.company:
                    outcome_args.extend(['--company', args.company])
                if args.position:
                    outcome_args.extend(['--position', args.position])
                if args.city:
                    outcome_args.extend(['--city', args.city])
                if args.status:
                    outcome_args.extend(['--status', args.status])
            elif args.subcommand == 'update':
                if args.id:
                    outcome_args.extend(['--id', str(args.id)])
                if args.status:
                    outcome_args.extend(['--status', args.status])

        original_argv = sys.argv
        sys.argv = outcome_args
        outcome.main()
        sys.argv = original_argv
    except Exception as e:
        print_error(f"申请归档操作失败: {str(e)}")
        import traceback
        traceback.print_exc()



def cmd_campus(args):
    """校招网申模块"""
    print_banner()
    subcommand = getattr(args, 'campus_subcommand', None)

    if subcommand == 'check' or not subcommand:
        print_info("网申机筛质量检查...")
        print()
        try:
            import apply_check
            original_argv = sys.argv
            check_args = ['apply_check.py']
            jd = getattr(args, 'jd', None)
            if jd:
                check_args.extend(['--jd', jd])
            out = getattr(args, 'output', None)
            if out:
                check_args.extend(['-o', out])
            sys.argv = check_args
            apply_check.main()
            sys.argv = original_argv
            print_success("机筛检查完成！")
        except Exception as e:
            print_error(f"机筛检查失败: {str(e)}")
            import traceback
            traceback.print_exc()

    elif subcommand == 'radar':
        print_info("网申雷达采集...")
        print()
        try:
            import radar_guopin, radar_nowcoder, radar_merged_report
            keyword = getattr(args, 'keyword', '') or '测绘'
            pages = getattr(args, 'pages', 2)
            # 国聘
            print_info(f"采集国聘网（关键词: {keyword}, {pages}页）...")
            guopin_jobs = radar_guopin.collect(keywords=[keyword], pages=pages, delay=1.5)
            radar_guopin.save_jobs(guopin_jobs, keywords=[keyword])
            print_success(f"国聘网采集 {len(guopin_jobs)} 个岗位")
            # 牛客
            print_info(f"采集牛客校招日程（{pages}页）...")
            nowcoder_companies = radar_nowcoder.collect(pages=pages, keyword=keyword, delay=1.0)
            radar_nowcoder.save_companies(nowcoder_companies)
            print_success(f"牛客采集 {len(nowcoder_companies)} 家公司")
            # 合并报告
            print_info("生成合并报告...")
            html = radar_merged_report.generate_merged_html(
                {"jobs": guopin_jobs}, {"companies": nowcoder_companies})
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(WORKSPACE_DIR, 'radar',
                f'网申雷达综合报告_{len(guopin_jobs)}岗位_{len(nowcoder_companies)}公司_{ts}.html')
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print_success(f"合并报告已生成: {report_path}")
        except Exception as e:
            print_error(f"网申雷达采集失败: {str(e)}")
            import traceback
            traceback.print_exc()

    elif subcommand == 'oq':
        print_info("开放性问题(OQ)答案生成...")
        print()
        try:
            import oq_generator
            original_argv = sys.argv
            oq_args = ['oq_generator.py']
            oq_sub = getattr(args, 'oq_subcommand', None)
            if oq_sub:
                oq_args.append(oq_sub)
            sys.argv = oq_args
            oq_generator.main()
            sys.argv = original_argv
            print_success("OQ生成完成！")
        except Exception as e:
            print_error(f"OQ生成失败: {str(e)}")
            import traceback
            traceback.print_exc()

    elif subcommand == 'profile':
        print_info("网申信息底座摘要...")
        print()
        profile_path = os.path.join(WORKSPACE_DIR, "application_profile.json")
        if not os.path.exists(profile_path):
            print_error("信息底座文件不存在: application_profile.json")
            return
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        basic = profile.get('基本信息', {})
        print(f"  姓名: {basic.get('姓名', '未填')}")
        print(f"  求职意向: {basic.get('求职意向', '未填')}")
        print(f"  期望薪资: {basic.get('期望薪资', '未填')}")
        print(f"  教育背景: {len(profile.get('教育背景', []))} 条")
        print(f"  实习经历: {len(profile.get('实习经历', []))} 条")
        print(f"  项目经历: {len(profile.get('项目经历', []))} 条")
        print(f"  获奖经历: {len(profile.get('获奖经历', []))} 条")
        print(f"  家庭成员: {len(profile.get('家庭成员及社会关系', []))} 条")
        print(f"  紧急联系人: {'已填' if profile.get('紧急联系人') else '未填'}")
        print()
        print_info(f"完整信息底座: {profile_path}")

    elif subcommand == 'track':
        print_info("网申进度看板...")
        print()
        try:
            import apply_track
            original_argv = sys.argv
            track_args = getattr(args, 'track_args', []) or []
            sys.argv = ['apply_track.py'] + track_args
            apply_track.main()
            sys.argv = original_argv
        except SystemExit:
            sys.argv = original_argv
        except Exception as e:
            print_error(f"进度看板失败: {str(e)}")
            import traceback
            traceback.print_exc()

    else:
        print_error(f"未知的 campus 子命令: {subcommand}")
        print_info("可用子命令: check / radar / oq / profile")


def cmd_check(args):
    """简历格式检查"""
    print_banner()
    print_info("简历格式检查...")
    print()

    try:
        import check_resume
        # 临时修改sys.argv，避免check_resume.main()误读job_search.py的参数
        original_argv = sys.argv
        sys.argv = ['check_resume.py']
        check_resume.main()
        sys.argv = original_argv
        print_success("简历格式检查完成！")
    except Exception as e:
        print_error(f"简历格式检查失败: {str(e)}")
        import traceback
        traceback.print_exc()


def cmd_jobs(args):
    """岗位库管理"""
    print_banner()
    print_info("岗位库管理...")
    print()

    subcommand = args.subcommand

    if subcommand == 'list':
        # 查看岗位库
        jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        jobs = load_json_file(jobs_path, "岗位库")
        if jobs:
            print(f"岗位总数: {len(jobs)}")
            print()
            # 按匹配度排序，显示前10个
            jobs_sorted = sorted(jobs, key=lambda x: x.get('match_score', 0) or 0, reverse=True)
            print("前10个高匹配岗位:")
            for i, job in enumerate(jobs_sorted[:10]):
                score = job.get('match_score', 0) or 0
                company = job.get('company', '未知')
                position = job.get('position', '未知')
                city = job.get('city', '未知')
                source = job.get('source', '未知')
                print(f"  {i+1}. [{score}分] {company} - {position} ({city}, {source})")

    elif subcommand == 'report':
        # 生成岗位推荐报告
        jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        jobs = load_json_file(jobs_path, "岗位库")
        if jobs:
            # 按匹配度排序
            jobs_sorted = sorted(jobs, key=lambda x: x.get('match_score', 0) or 0, reverse=True)

            # 生成报告
            from report_generator import generate_report
            output_path = os.path.join(WORKSPACE_DIR, "applications", "岗位推荐报告.html")
            generate_report(
                jobs_sorted,
                output_path,
                title="岗位推荐报告",
                subtitle=f"共{len(jobs_sorted)}个岗位，按匹配度排序"
            )
            print_success(f"岗位推荐报告已生成: {output_path}")

    elif subcommand == 'filter':
        # 筛选岗位
        print_info("启动交互式筛选...")
        try:
            import filter_jobs
            filter_jobs.interactive_filter()
        except Exception as e:
            print_error(f"筛选失败: {str(e)}")

    else:
        print_error(f"未知的子命令: {subcommand}")
        print_info("可用子命令: list, report, filter")


def cmd_collect(args):
    """扩展采集JSON → 独立匹配报告（不写入岗位库）"""
    print_banner()
    print_info("扩展采集 → 独立匹配报告（不写入岗位库 jobs.json）...")
    print()

    inputs = getattr(args, 'inputs', None) or []
    if not inputs:
        print_error("请提供至少一个扩展导出的JSON文件")
        print_info("用法: python job_search.py collect <导出1.json> [导出2.json ...] [-o 输出.html]")
        return

    # boss_api 加入模块搜索路径（make_standalone_report 内部会自行处理其子依赖）
    boss_api_dir = os.path.join(WORKSPACE_DIR, "boss_api")
    if boss_api_dir not in sys.path:
        sys.path.insert(0, boss_api_dir)

    try:
        from make_standalone_report import generate_standalone_report
        out, _scored, stats = generate_standalone_report(
            inputs, output=getattr(args, 'output', '') or '', verbose=True
        )
        print()
        print_success(f"独立报告已生成: {out}")
        print_info(f"共{stats['total']}个（BOSS直聘{stats['n_boss']} / 智联招聘{stats['n_zh']}），"
                   f"平均{stats['avg']}分，最高{stats['max']}分，≥75分{stats['high']}个")
        print_info("本报告未写入岗位库；如需正式积累，走 job_pipeline import→rank→report")
    except Exception as e:
        print_error(f"生成采集报告失败: {str(e)}")
        import traceback
        traceback.print_exc()


def cmd_config(args):
    """配置管理"""
    print_banner()
    print_info("配置管理...")
    print()

    subcommand = args.subcommand

    if subcommand == 'show':
        # 显示配置
        print_config_summary()

    elif subcommand == 'validate':
        # 验证配置
        is_valid, errors = validate_config()
        if is_valid:
            print_success("配置验证通过！")
        else:
            print_error(f"配置验证失败，发现 {len(errors)} 个问题:")
            for e in errors:
                print(f"  - {e}")

    elif subcommand == 'path':
        # 显示配置文件路径
        config_path = os.path.join(WORKSPACE_DIR, "config.yaml")
        print(f"配置文件路径: {config_path}")
        print(f"工作区目录: {get_workspace_dir()}")

    else:
        print_error(f"未知的子命令: {subcommand}")
        print_info("可用子命令: show, validate, path")


def cmd_validate(args):
    """数据验证"""
    print_banner()
    print_info("数据验证...")
    print()

    all_valid = True

    # 验证简历数据
    resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
    if os.path.exists(resume_path):
        resume_data = load_json_file(resume_path, "简历数据")
        if resume_data:
            errors = validate_resume(resume_data)
            if errors:
                print_warning(f"简历数据验证发现 {len(errors)} 个问题:")
                for e in errors[:5]:
                    print(f"  - {e}")
                all_valid = False
            else:
                print_success("简历数据验证通过")
    else:
        print_warning("简历数据文件不存在")

    # 验证岗位库
    jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
    if os.path.exists(jobs_path):
        jobs = load_json_file(jobs_path, "岗位库")
        if jobs:
            errors = validate_jobs_list(jobs)
            if errors:
                print_warning(f"岗位库验证发现 {len(errors)}/{len(jobs)} 个岗位有问题")
                all_valid = False
            else:
                print_success(f"岗位库验证通过（{len(jobs)}个岗位）")
    else:
        print_warning("岗位库文件不存在")

    # 验证申请记录
    apps_path = os.path.join(WORKSPACE_DIR, "applications", "applications.json")
    if os.path.exists(apps_path):
        apps_data = load_json_file(apps_path, "申请记录")
        if apps_data:
            apps_list = apps_data.get("applications", [])
            errors = validate_applications_list(apps_list)
            if errors:
                print_warning(f"申请记录验证发现 {len(errors)}/{len(apps_list)} 条记录有问题")
                all_valid = False
            else:
                print_success(f"申请记录验证通过（{len(apps_list)}条记录）")
    else:
        print_warning("申请记录文件不存在")

    print()
    if all_valid:
        print_success("所有数据验证通过！")
    else:
        print_warning("部分数据验证未通过，请检查上述问题")


def cmd_quality(args):
    """质量门禁检查"""
    print_banner()
    print_info("质量门禁检查...")
    print()

    try:
        from utils.quality_gate import QualityGate, quick_quality_check
    except ImportError:
        print_error("质量门禁模块不可用")
        return

    subcommand = getattr(args, 'subcommand', None)

    if subcommand == 'check' or not subcommand:
        # 运行完整质量检查
        success = quick_quality_check(WORKSPACE_DIR)
        print()
        if success:
            print_success("所有质量检查通过！")
        else:
            print_warning("部分质量检查未通过，请检查上述问题")

    elif subcommand == 'resume':
        # 检查简历数据质量
        qg = QualityGate()
        resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
        if os.path.exists(resume_path):
            resume_data = load_json_file(resume_path, "简历数据")
            if resume_data:
                result = qg.validate_resume(resume_data)
                print(result)
                if result.errors:
                    for e in result.errors:
                        print(f"  ✗ {e}")
                if result.warnings:
                    for w in result.warnings:
                        print(f"  ! {w}")
        else:
            print_error("简历数据文件不存在")

    elif subcommand == 'jobs':
        # 检查岗位库质量
        qg = QualityGate()
        jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        if os.path.exists(jobs_path):
            jobs = load_json_file(jobs_path, "岗位库")
            if jobs:
                result = qg.validate_jobs_list(jobs)
                print(result)
                if result.errors:
                    for e in result.errors[:5]:
                        print(f"  ✗ {e}")
                if result.warnings:
                    for w in result.warnings[:5]:
                        print(f"  ! {w}")
                if result.info:
                    print(f"  信息: {result.info}")
        else:
            print_error("岗位库文件不存在")

    elif subcommand == 'report':
        # 检查报告质量
        qg = QualityGate()
        report_path = os.path.join(WORKSPACE_DIR, "applications", "岗位推荐报告.html")
        if os.path.exists(report_path):
            result = qg.validate_report_file(report_path)
            print(result)
            if result.errors:
                for e in result.errors:
                    print(f"  ✗ {e}")
            if result.warnings:
                for w in result.warnings:
                    print(f"  ! {w}")
            if result.info:
                print(f"  信息: {result.info}")
        else:
            print_error("报告文件不存在")

    else:
        print_error(f"未知的子命令: {subcommand}")
        print_info("可用子命令: check, resume, jobs, report")


# ============================================================
# 主函数
# ============================================================

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="求职工作区 - 统一工作流引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python job_search.py resume
  python job_search.py rank --jd job_description.txt
  python job_search.py apply --jd job_description.txt
  python job_search.py interview --company "公司名" --position "岗位名"
  python job_search.py outcome add --company "公司名" --position "岗位名"
  python job_search.py jobs report
  python job_search.py collect 导出1.json 导出2.json -o applications/测试.html
  python job_search.py config show
  python job_search.py validate
  python job_search.py quality check
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # setup命令
    parser_setup = subparsers.add_parser('setup', help='初始化个人资料')

    # resume命令
    parser_resume = subparsers.add_parser('resume', help='生成简历')

    # rank命令
    parser_rank = subparsers.add_parser('rank', help='职位匹配评估')
    parser_rank.add_argument('--jd', help='JD文本或文件路径')
    parser_rank.add_argument('--output', help='匹配结果输出文件')

    # apply命令
    parser_apply = subparsers.add_parser('apply', help='生成定制简历')
    parser_apply.add_argument('--jd', help='JD文本或文件路径')

    # interview命令
    parser_interview = subparsers.add_parser('interview', help='面试准备')
    parser_interview.add_argument('--company', required=True, help='公司名称')
    parser_interview.add_argument('--position', required=True, help='岗位名称')

    # outcome命令
    parser_outcome = subparsers.add_parser('outcome', help='申请归档管理')
    outcome_subparsers = parser_outcome.add_subparsers(dest='subcommand')
    # add
    parser_outcome_add = outcome_subparsers.add_parser('add', help='添加申请记录')
    parser_outcome_add.add_argument('--company', required=True, help='公司名称')
    parser_outcome_add.add_argument('--position', required=True, help='岗位名称')
    parser_outcome_add.add_argument('--city', help='工作城市')
    parser_outcome_add.add_argument('--status', default='已投递', help='状态')
    # update
    parser_outcome_update = outcome_subparsers.add_parser('update', help='更新申请状态')
    parser_outcome_update.add_argument('--id', type=int, required=True, help='记录ID')
    parser_outcome_update.add_argument('--status', required=True, help='新状态')
    # list
    outcome_subparsers.add_parser('list', help='查看申请记录')
    # stats
    outcome_subparsers.add_parser('stats', help='统计分析')

    # check命令
    parser_check = subparsers.add_parser('check', help='简历格式检查')

    # jobs命令
    parser_jobs = subparsers.add_parser('jobs', help='岗位库管理')
    jobs_subparsers = parser_jobs.add_subparsers(dest='subcommand')
    jobs_subparsers.add_parser('list', help='查看岗位库')
    jobs_subparsers.add_parser('report', help='生成岗位推荐报告')
    jobs_subparsers.add_parser('filter', help='筛选岗位')

    # collect命令（扩展采集JSON → 独立报告，不写岗位库）
    parser_collect = subparsers.add_parser('collect', help='扩展采集JSON生成独立报告（不入库）')
    parser_collect.add_argument('inputs', nargs='+', help='扩展导出的岗位JSON，可传多个（BOSS/智联）自动合并')
    parser_collect.add_argument('-o', '--output', help='输出HTML路径（默认applications/自动命名）')

    # config命令
    parser_config = subparsers.add_parser('config', help='配置管理')
    config_subparsers = parser_config.add_subparsers(dest='subcommand')
    config_subparsers.add_parser('show', help='显示配置')
    config_subparsers.add_parser('validate', help='验证配置')
    config_subparsers.add_parser('path', help='显示配置文件路径')

    # validate命令
    parser_validate = subparsers.add_parser('validate', help='数据验证')

    # campus命令（校招网申模块）
    parser_campus = subparsers.add_parser('campus', help='校招网申模块')
    campus_sub = parser_campus.add_subparsers(dest='campus_subcommand')
    _c_check = campus_sub.add_parser('check', help='机筛质量检查')
    _c_check.add_argument('--jd', help='目标岗位JD文本文件（含ATS关键词覆盖）')
    _c_check.add_argument('-o', '--output', help='输出HTML路径')
    _c_radar = campus_sub.add_parser('radar', help='网申雷达采集+合并报告')
    _c_radar.add_argument('--keyword', default='测绘', help='搜索关键词（默认测绘）')
    _c_radar.add_argument('--pages', type=int, default=2, help='采集页数（默认2）')
    _c_oq = campus_sub.add_parser('oq', help='开放性问题(OQ)答案生成')
    _oq_sub = _c_oq.add_subparsers(dest='oq_subcommand')
    _oq_sub.add_parser('list', help='列出支持的OQ问题')
    _oq_sub.add_parser('gen', help='生成全部OQ答案')
    campus_sub.add_parser('profile', help='查看信息底座摘要')
    _c_track = campus_sub.add_parser('track', help='网申进度看板（add/update/list/show/stats/deadline/report）')
    _c_track.add_argument('track_args', nargs='*', help='透传给 apply_track.py 的参数')

    # quality命令
    parser_quality = subparsers.add_parser('quality', help='质量门禁检查')
    quality_subparsers = parser_quality.add_subparsers(dest='subcommand')
    quality_subparsers.add_parser('check', help='运行完整质量检查')
    quality_subparsers.add_parser('resume', help='检查简历数据质量')
    quality_subparsers.add_parser('jobs', help='检查岗位库质量')
    quality_subparsers.add_parser('report', help='检查报告质量')

    # 解析参数
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 执行命令
    if args.command == 'setup':
        cmd_setup(args)
    elif args.command == 'resume':
        cmd_resume(args)
    elif args.command == 'rank':
        cmd_rank(args)
    elif args.command == 'apply':
        cmd_apply(args)
    elif args.command == 'interview':
        cmd_interview(args)
    elif args.command == 'outcome':
        cmd_outcome(args)
    elif args.command == 'check':
        cmd_check(args)
    elif args.command == 'jobs':
        cmd_jobs(args)
    elif args.command == 'collect':
        cmd_collect(args)
    elif args.command == 'config':
        cmd_config(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'quality':
        cmd_quality(args)
    elif args.command == 'campus':
        cmd_campus(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
