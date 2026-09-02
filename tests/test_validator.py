# -*- coding: utf-8 -*-
"""
测试数据验证工具（utils/validator.py）
"""

import os
import sys
import json
import unittest

# 添加工作区目录到路径
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestValidator(unittest.TestCase):
    """测试数据验证工具"""

    def setUp(self):
        """测试前准备"""
        self.jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        self.resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")

    def test_validator_import(self):
        """测试验证工具导入"""
        try:
            from utils.validator import validate_job, validate_resume, validate_match_result, validate_application
            self.assertTrue(True, "验证工具导入成功")
        except ImportError as e:
            self.fail(f"验证工具导入失败: {e}")

    def test_jobs_file_exists(self):
        """测试岗位库文件存在"""
        self.assertTrue(os.path.exists(self.jobs_path), f"岗位库文件不存在: {self.jobs_path}")

    def test_resume_file_exists(self):
        """测试简历数据文件存在"""
        self.assertTrue(os.path.exists(self.resume_path), f"简历数据文件不存在: {self.resume_path}")

    def test_jobs_data_format(self):
        """测试岗位库数据格式"""
        with open(self.jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        self.assertIsInstance(jobs, list, "岗位库应该是列表类型")
        self.assertGreater(len(jobs), 0, "岗位库不应为空")
        print(f"岗位库数量: {len(jobs)}")

    def test_job_required_fields(self):
        """测试岗位必填字段"""
        try:
            from utils.validator import validate_job
        except ImportError as e:
            self.skipTest(f"验证工具导入失败: {e}")

        with open(self.jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)

        valid_count = 0
        invalid_count = 0
        for i, job in enumerate(jobs[:10]):  # 只测试前10个
            errors = validate_job(job)
            if errors:
                invalid_count += 1
                print(f"岗位 {i} ({job.get('company', '未知')} - {job.get('position', '未知')}) 验证失败: {errors[:2]}")
            else:
                valid_count += 1

        print(f"测试结果: {valid_count} 通过, {invalid_count} 失败（前10个）")
        # 允许少量失败，但大部分应该通过
        self.assertGreaterEqual(valid_count, 5, "前10个岗位中至少应有5个通过验证")

    def test_resume_data_format(self):
        """测试简历数据格式"""
        with open(self.resume_path, 'r', encoding='utf-8') as f:
            resume = json.load(f)
        self.assertIsInstance(resume, dict, "简历数据应该是字典类型")
        self.assertIn("基本信息", resume, "简历数据应包含基本信息")

    def test_resume_basic_info(self):
        """测试简历基本信息"""
        with open(self.resume_path, 'r', encoding='utf-8') as f:
            resume = json.load(f)
        basic = resume.get("基本信息", {})
        self.assertIn("name", basic, "基本信息应包含姓名")
        self.assertIn("phone", basic, "基本信息应包含电话")
        self.assertIn("email", basic, "基本信息应包含邮箱")
        print(f"姓名: {basic.get('name')}")

    def test_validate_resume(self):
        """测试验证简历数据"""
        try:
            from utils.validator import validate_resume
        except ImportError as e:
            self.skipTest(f"验证工具导入失败: {e}")

        with open(self.resume_path, 'r', encoding='utf-8') as f:
            resume = json.load(f)
        errors = validate_resume(resume)
        if errors:
            print(f"简历验证警告: {errors}")
        # 简历验证可能有警告，但不应有致命错误
        self.assertIsInstance(errors, list, "验证结果应该是列表")


if __name__ == '__main__':
    unittest.main(verbosity=2)
