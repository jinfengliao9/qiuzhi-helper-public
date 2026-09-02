# -*- coding: utf-8 -*-
# ============================================================================
# 【状态说明】本文件诞生于 Browser Use 自动化抓取时代，但其中的核心能力
# 被现行流水线活跃引用，因此保留在工作区根目录，不归档、不删除。
#   - 活跃复用：JobCollector 类（jobs.json 数据访问层），被 job_pipeline.py、filter_jobs.py 依赖
#   - 已废弃：与 Browser Use 抓取流程绑定的调用路径（v0.2.0 起主路径为
#     Edge 扩展被动采集，见 boss_api/）
# 详见 archive/browser_use_legacy/README.md
# ============================================================================
"""
岗位库管理模块
功能：岗位的增删改查、自动去重、匹配度管理、统计分析
"""

import json
import os
import re
from datetime import datetime


class JobCollector:
    """岗位库管理器"""

    def __init__(self, jobs_file=None):
        if jobs_file is None:
            jobs_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs.json')
        self.jobs_file = jobs_file
        self.jobs = []
        self.load()

    def load(self):
        """从文件加载岗位库"""
        if os.path.exists(self.jobs_file):
            try:
                with open(self.jobs_file, 'r', encoding='utf-8') as f:
                    self.jobs = json.load(f)
                print(f'已加载 {len(self.jobs)} 个岗位')
            except Exception as e:
                print(f'加载岗位库失败: {e}，将创建新库')
                self.jobs = []
        else:
            self.jobs = []
            print('岗位库不存在，将创建新库')

    def save(self):
        """保存岗位库到文件"""
        os.makedirs(os.path.dirname(self.jobs_file), exist_ok=True)
        with open(self.jobs_file, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        print(f'岗位库已保存，共 {len(self.jobs)} 个岗位')

    def _generate_id(self):
        """生成唯一ID"""
        return datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(len(self.jobs) + 1)

    def _parse_salary(self, salary_text):
        """解析薪资文本，返回 (min, max) 单位：元/月"""
        if not salary_text or salary_text in ['**-**', '*-*', '面议']:
            return None, None

        salary_text = salary_text.strip()

        # 处理 "万" 单位
        wan_match = re.search(r'([\d.]+)\s*[-~]\s*([\d.]+)\s*万', salary_text)
        if wan_match:
            return int(float(wan_match.group(1)) * 10000), int(float(wan_match.group(2)) * 10000)

        # 处理 "元" 单位
        yuan_match = re.search(r'([\d,]+)\s*[-~]\s*([\d,]+)\s*元', salary_text)
        if yuan_match:
            return int(yuan_match.group(1).replace(',', '')), int(yuan_match.group(2).replace(',', ''))

        # 处理纯数字范围
        num_match = re.search(r'([\d,]+)\s*[-~]\s*([\d,]+)', salary_text)
        if num_match:
            min_val = int(num_match.group(1).replace(',', ''))
            max_val = int(num_match.group(2).replace(',', ''))
            # 如果数值较小，可能是千为单位
            if max_val < 100:
                return min_val * 1000, max_val * 1000
            return min_val, max_val

        return None, None

    def is_duplicate(self, job):
        """检查岗位是否重复（按公司+岗位名+城市判断）"""
        company = job.get('company', '').strip()
        position = job.get('position', '').strip()
        city = job.get('city', '').strip()

        for existing in self.jobs:
            if (existing.get('company', '').strip() == company and
                existing.get('position', '').strip() == position and
                existing.get('city', '').strip() == city):
                return True
        return False

    def add_job(self, job_data, skip_duplicate_check=False):
        """
        添加岗位
        返回: (success, message, job_id)
        """
        # 自动解析薪资
        if 'salary' in job_data and job_data['salary']:
            salary_min, salary_max = self._parse_salary(job_data['salary'])
            if salary_min is not None:
                job_data['salary_min'] = salary_min
                job_data['salary_max'] = salary_max

        # 去重检查
        if not skip_duplicate_check and self.is_duplicate(job_data):
            return False, '岗位已存在（重复）', None

        # 生成ID和时间
        job_data['id'] = self._generate_id()
        job_data['collected_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 'status' not in job_data:
            job_data['status'] = '未评估'
        if 'source' not in job_data:
            job_data['source'] = '智联招聘'

        self.jobs.append(job_data)
        self.save()
        return True, f'添加成功: {job_data.get("company", "")} - {job_data.get("position", "")}', job_data['id']

    def add_jobs_batch(self, jobs_list):
        """批量添加岗位，返回成功/失败/重复统计
        跨平台去重策略：BOSS直聘优先（有独立URL、匹配度更高），智联后添加
        """
        success = 0
        duplicate = 0
        failed = 0
        new_ids = []

        # 排序：BOSS直聘优先，其他平台后添加
        def source_priority(job):
            source = job.get('source', '')
            if source == 'BOSS直聘':
                return 0  # 最高优先级
            return 1  # 其他平台

        sorted_jobs = sorted(jobs_list, key=source_priority)

        for job in sorted_jobs:
            try:
                ok, msg, job_id = self.add_job(job)
                if ok:
                    success += 1
                    new_ids.append(job_id)
                elif '重复' in msg:
                    duplicate += 1
                else:
                    failed += 1
            except Exception as e:
                print(f'添加岗位失败: {e}')
                failed += 1

        print(f'批量添加完成: 成功{success}个, 重复{duplicate}个, 失败{failed}个')
        return {'success': success, 'duplicate': duplicate, 'failed': failed, 'new_ids': new_ids}

    def update_job(self, job_id, updates):
        """更新岗位信息"""
        for job in self.jobs:
            if job.get('id') == job_id:
                job.update(updates)
                self.save()
                return True, f'更新成功: {job.get("company", "")} - {job.get("position", "")}'
        return False, '未找到该岗位'

    def update_match_score(self, job_id, score, match_detail=None):
        """更新岗位匹配度"""
        updates = {'match_score': score, 'status': '已评估'}
        if match_detail:
            updates['match_detail'] = match_detail
        return self.update_job(job_id, updates)

    def delete_job(self, job_id):
        """删除岗位"""
        for i, job in enumerate(self.jobs):
            if job.get('id') == job_id:
                removed = self.jobs.pop(i)
                self.save()
                return True, f'已删除: {removed.get("company", "")} - {removed.get("position", "")}'
        return False, '未找到该岗位'

    def get_job(self, job_id):
        """根据ID获取岗位"""
        for job in self.jobs:
            if job.get('id') == job_id:
                return job
        return None

    def query_jobs(self, status=None, city=None, min_score=None, max_score=None,
                    keyword=None, source=None, sort_by='match_score', reverse=True):
        """
        查询岗位
        sort_by: match_score / salary_min / collected_at
        """
        results = self.jobs

        if status:
            results = [j for j in results if j.get('status') == status]
        if city:
            results = [j for j in results if city in j.get('city', '')]
        if min_score is not None:
            results = [j for j in results if j.get('match_score', 0) >= min_score]
        if max_score is not None:
            results = [j for j in results if j.get('match_score', 0) <= max_score]
        if source:
            results = [j for j in results if j.get('source') == source]
        if keyword:
            kw = keyword.lower()
            results = [j for j in results if
                       kw in j.get('company', '').lower() or
                       kw in j.get('position', '').lower() or
                       kw in ' '.join(j.get('skills', [])).lower()]

        # 排序
        if sort_by == 'match_score':
            results.sort(key=lambda x: x.get('match_score', 0), reverse=reverse)
        elif sort_by == 'salary_min':
            results.sort(key=lambda x: x.get('salary_min', 0), reverse=reverse)
        elif sort_by == 'collected_at':
            results.sort(key=lambda x: x.get('collected_at', ''), reverse=reverse)

        return results

    def get_unscored_jobs(self):
        """获取未评估匹配度的岗位"""
        return [j for j in self.jobs if j.get('match_score') is None or j.get('status') == '未评估']

    def get_statistics(self):
        """获取岗位库统计信息"""
        total = len(self.jobs)
        if total == 0:
            return {'total': 0}

        # 按状态统计
        status_count = {}
        for job in self.jobs:
            status = job.get('status', '未知')
            status_count[status] = status_count.get(status, 0) + 1

        # 按来源统计
        source_count = {}
        for job in self.jobs:
            source = job.get('source', '未知')
            source_count[source] = source_count.get(source, 0) + 1

        # 按城市统计（前10）
        city_count = {}
        for job in self.jobs:
            city = job.get('city', '未知')
            city_count[city] = city_count.get(city, 0) + 1
        top_cities = sorted(city_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # 匹配度统计
        scored = [j for j in self.jobs if j.get('match_score') is not None]
        avg_score = sum(j['match_score'] for j in scored) / len(scored) if scored else 0
        high_score = len([j for j in scored if j['match_score'] >= 75])
        medium_score = len([j for j in scored if 60 <= j['match_score'] < 75])
        low_score = len([j for j in scored if j['match_score'] < 60])

        # 薪资统计
        with_salary = [j for j in self.jobs if j.get('salary_min') is not None]
        avg_salary = sum((j['salary_min'] + j['salary_max']) / 2 for j in with_salary) / len(with_salary) if with_salary else 0

        return {
            'total': total,
            'scored': len(scored),
            'unscored': total - len(scored),
            'avg_score': round(avg_score, 1),
            'high_score_count': high_score,
            'medium_score_count': medium_score,
            'low_score_count': low_score,
            'avg_salary': round(avg_salary, 0),
            'status_count': status_count,
            'source_count': source_count,
            'top_cities': top_cities
        }


# 命令行接口
if __name__ == '__main__':
    import sys

    collector = JobCollector()

    if len(sys.argv) < 2:
        print('用法:')
        print('  python job_collector.py list                    # 列出所有岗位')
        print('  python job_collector.py stats                   # 统计信息')
        print('  python job_collector.py query --status 已评估   # 按条件查询')
        print('  python job_collector.py delete <job_id>         # 删除岗位')
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'list':
        jobs = collector.query_jobs(sort_by='collected_at', reverse=True)
        print(f'\n共 {len(jobs)} 个岗位:\n')
        for i, job in enumerate(jobs, 1):
            score = job.get('match_score', '未评估')
            print(f'{i}. [{job.get("status", "")}] {job.get("company", "")} - {job.get("position", "")}')
            print(f'   城市: {job.get("city", "")} | 薪资: {job.get("salary", "未知")} | 匹配度: {score}')
            print(f'   ID: {job.get("id", "")}')
            print()

    elif cmd == 'stats':
        stats = collector.get_statistics()
        print('\n=== 岗位库统计 ===')
        print(f'总岗位数: {stats.get("total", 0)}')
        print(f'已评估: {stats.get("scored", 0)} | 未评估: {stats.get("unscored", 0)}')
        print(f'平均匹配度: {stats.get("avg_score", 0)}分')
        print(f'高匹配(≥75): {stats.get("high_score_count", 0)}个')
        print(f'中匹配(60-74): {stats.get("medium_score_count", 0)}个')
        print(f'低匹配(<60): {stats.get("low_score_count", 0)}个')
        print(f'平均薪资: {stats.get("avg_salary", 0)}元/月')
        print(f'\n按状态:')
        for status, count in stats.get('status_count', {}).items():
            print(f'  {status}: {count}个')
        print(f'\n按来源:')
        for source, count in stats.get('source_count', {}).items():
            print(f'  {source}: {count}个')
        print(f'\n热门城市:')
        for city, count in stats.get('top_cities', []):
            print(f'  {city}: {count}个')

    elif cmd == 'query':
        kwargs = {}
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--status' and i + 1 < len(sys.argv):
                kwargs['status'] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--city' and i + 1 < len(sys.argv):
                kwargs['city'] = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--min-score' and i + 1 < len(sys.argv):
                kwargs['min_score'] = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == '--keyword' and i + 1 < len(sys.argv):
                kwargs['keyword'] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        jobs = collector.query_jobs(**kwargs)
        print(f'\n查询到 {len(jobs)} 个岗位:\n')
        for job in jobs:
            score = job.get('match_score', '未评估')
            print(f'[{job.get("status", "")}] {job.get("company", "")} - {job.get("position", "")}')
            print(f'  城市: {job.get("city", "")} | 薪资: {job.get("salary", "未知")} | 匹配度: {score}')
            print()

    elif cmd == 'delete':
        if len(sys.argv) < 3:
            print('请提供要删除的岗位ID')
            sys.exit(1)
        job_id = sys.argv[2]
        ok, msg = collector.delete_job(job_id)
        print(msg)

    else:
        print(f'未知命令: {cmd}')
