# -*- coding: utf-8 -*-
"""
端到端测试：测试job_search.py工作流引擎的基本命令
"""

import os
import sys
import subprocess
import unittest

# 工作区目录
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestWorkflowEngine(unittest.TestCase):
    """测试工作流引擎（job_search.py）"""

    def setUp(self):
        """测试前准备"""
        self.script_path = os.path.join(WORKSPACE_DIR, "job_search.py")
        self.python = sys.executable

    def run_command(self, args, timeout=30):
        """运行命令并返回结果"""
        cmd = [self.python, self.script_path] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=WORKSPACE_DIR,
            timeout=timeout
        )
        return result

    def test_script_exists(self):
        """测试脚本文件存在"""
        self.assertTrue(os.path.exists(self.script_path), f"脚本文件不存在: {self.script_path}")

    def test_help_command(self):
        """测试帮助命令"""
        result = self.run_command(["--help"])
        self.assertEqual(result.returncode, 0, f"帮助命令执行失败: {result.stderr}")
        self.assertIn("job_search.py", result.stdout, "帮助信息应包含脚本名")
        self.assertIn("setup", result.stdout, "帮助信息应包含setup命令")
        self.assertIn("resume", result.stdout, "帮助信息应包含resume命令")
        self.assertIn("rank", result.stdout, "帮助信息应包含rank命令")
        self.assertIn("quality", result.stdout, "帮助信息应包含quality命令")
        print("帮助命令测试通过")

    def test_config_show_command(self):
        """测试配置显示命令"""
        result = self.run_command(["config", "show"])
        self.assertEqual(result.returncode, 0, f"配置显示命令执行失败: {result.stderr}")
        self.assertIn("配置", result.stdout, "输出应包含配置信息")
        print("配置显示命令测试通过")

    def test_validate_command(self):
        """测试数据验证命令"""
        result = self.run_command(["validate"])
        self.assertEqual(result.returncode, 0, f"数据验证命令执行失败: {result.stderr}")
        self.assertIn("验证", result.stdout, "输出应包含验证信息")
        print("数据验证命令测试通过")

    def test_quality_check_command(self):
        """测试质量门禁检查命令"""
        result = self.run_command(["quality", "check"], timeout=60)
        self.assertEqual(result.returncode, 0, f"质量检查命令执行失败: {result.stderr}")
        self.assertIn("质量", result.stdout, "输出应包含质量检查信息")
        print("质量门禁检查命令测试通过")

    def test_jobs_list_command(self):
        """测试岗位库列表命令"""
        result = self.run_command(["jobs", "list"])
        self.assertEqual(result.returncode, 0, f"岗位库列表命令执行失败: {result.stderr}")
        self.assertIn("岗位", result.stdout, "输出应包含岗位信息")
        print("岗位库列表命令测试通过")

    def test_outcome_list_command(self):
        """测试申请归档列表命令"""
        result = self.run_command(["outcome", "list"])
        self.assertEqual(result.returncode, 0, f"申请归档列表命令执行失败: {result.stderr}")
        # 输出可能包含"记录"或"投递"等关键词
        print("申请归档列表命令测试通过")

    def test_config_validate_command(self):
        """测试配置验证命令"""
        result = self.run_command(["config", "validate"])
        self.assertEqual(result.returncode, 0, f"配置验证命令执行失败: {result.stderr}")
        print("配置验证命令测试通过")


class TestDataIntegrity(unittest.TestCase):
    """测试数据完整性"""

    def setUp(self):
        """测试前准备"""
        self.jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        self.resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
        self.config_path = os.path.join(WORKSPACE_DIR, "config.yaml")

    def test_jobs_data_integrity(self):
        """测试岗位库数据完整性"""
        import json
        with open(self.jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)

        self.assertIsInstance(jobs, list, "岗位库应该是列表")
        self.assertGreater(len(jobs), 0, "岗位库不应为空")

        # 检查每个岗位的基本字段
        missing_company = 0
        missing_position = 0
        missing_source = 0
        missing_url = 0

        for job in jobs:
            if not job.get("company"):
                missing_company += 1
            if not job.get("position"):
                missing_position += 1
            if not job.get("source"):
                missing_source += 1
            if not job.get("job_url"):
                missing_url += 1

        print(f"\n岗位库数据完整性检查:")
        print(f"  总岗位数: {len(jobs)}")
        print(f"  缺少公司名: {missing_company}")
        print(f"  缺少岗位名: {missing_position}")
        print(f"  缺少来源: {missing_source}")
        print(f"  缺少链接: {missing_url}")

        # 大部分岗位应该有基本字段
        self.assertLess(missing_company, len(jobs) * 0.1, "超过10%的岗位缺少公司名")
        self.assertLess(missing_position, len(jobs) * 0.1, "超过10%的岗位缺少岗位名")

    def test_resume_data_integrity(self):
        """测试简历数据完整性"""
        import json
        with open(self.resume_path, 'r', encoding='utf-8') as f:
            resume = json.load(f)

        self.assertIsInstance(resume, dict, "简历数据应该是字典")
        self.assertIn("基本信息", resume, "简历应包含基本信息")

        basic = resume.get("基本信息", {})
        print(f"\n简历数据完整性检查:")
        print(f"  姓名: {basic.get('name', '未设置')}")
        print(f"  电话: {basic.get('phone', '未设置')}")
        print(f"  邮箱: {basic.get('email', '未设置')}")

        # 基本信息应该有姓名
        self.assertTrue(basic.get("name"), "简历应包含姓名")

    def test_config_file_integrity(self):
        """测试配置文件完整性"""
        import yaml
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        self.assertIsInstance(config, dict, "配置应该是字典")

        required_sections = ["general", "paths", "scraper", "platforms", "matching"]
        missing_sections = [s for s in required_sections if s not in config]

        print(f"\n配置文件完整性检查:")
        print(f"  缺少的section: {missing_sections if missing_sections else '无'}")

        self.assertEqual(len(missing_sections), 0, f"配置缺少必要的section: {missing_sections}")

        # 检查匹配权重总和
        weights = config.get("matching", {}).get("weights", {})
        total = sum(weights.values())
        print(f"  匹配权重总和: {total}")
        self.assertAlmostEqual(total, 1.0, places=2, msg=f"匹配权重总和应为1.0，当前为{total}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
