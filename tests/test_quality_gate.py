# -*- coding: utf-8 -*-
"""
测试质量门禁模块（utils/quality_gate.py）
"""

import os
import sys
import json
import unittest

# 添加工作区目录到路径
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestQualityGate(unittest.TestCase):
    """测试质量门禁模块"""

    def setUp(self):
        """测试前准备"""
        self.jobs_path = os.path.join(WORKSPACE_DIR, "jobs.json")
        self.resume_path = os.path.join(WORKSPACE_DIR, "resume_data.json")
        self.report_path = os.path.join(WORKSPACE_DIR, "applications", "岗位推荐报告.html")

    def test_quality_gate_import(self):
        """测试质量门禁模块导入"""
        try:
            from utils.quality_gate import QualityGate, ValidationResult, quick_quality_check
            self.assertTrue(True, "质量门禁模块导入成功")
        except ImportError as e:
            self.fail(f"质量门禁模块导入失败: {e}")

    def test_create_quality_gate(self):
        """测试创建质量门禁实例"""
        try:
            from utils.quality_gate import QualityGate
            qg = QualityGate()
            self.assertIsNotNone(qg, "质量门禁实例创建失败")
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

    def test_validation_result(self):
        """测试验证结果类"""
        try:
            from utils.quality_gate import ValidationResult
            result = ValidationResult(passed=True, errors=[], warnings=[], info={"test": "value"})
            self.assertTrue(result.passed, "验证结果应该通过")
            self.assertEqual(result.info["test"], "value", "验证结果信息不正确")
            self.assertIn("通过", str(result), "验证结果字符串应包含'通过'")
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

    def test_validate_resume(self):
        """测试验证简历数据"""
        try:
            from utils.quality_gate import QualityGate
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

        qg = QualityGate()
        with open(self.resume_path, 'r', encoding='utf-8') as f:
            resume = json.load(f)
        result = qg.validate_resume(resume)
        self.assertIsNotNone(result, "验证结果不应为None")
        print(f"简历验证结果: {result}")
        if result.errors:
            print(f"简历验证错误: {result.errors[:3]}")
        # 简历验证可能有警告，但不应有致命错误
        self.assertIsInstance(result.errors, list, "错误应该是列表")

    def test_validate_jobs_list(self):
        """测试批量验证岗位列表"""
        try:
            from utils.quality_gate import QualityGate
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

        qg = QualityGate()
        with open(self.jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        result = qg.validate_jobs_list(jobs)
        self.assertIsNotNone(result, "验证结果不应为None")
        print(f"岗位列表验证结果: {result}")
        print(f"岗位统计: {result.info}")
        self.assertEqual(result.info.get("total"), len(jobs), "岗位总数不正确")

    def test_validate_report(self):
        """测试验证报告"""
        try:
            from utils.quality_gate import QualityGate
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

        if not os.path.exists(self.report_path):
            self.skipTest(f"报告文件不存在: {self.report_path}")

        qg = QualityGate()
        result = qg.validate_report_file(self.report_path)
        self.assertIsNotNone(result, "验证结果不应为None")
        print(f"报告验证结果: {result}")
        if result.info:
            print(f"报告统计: {result.info}")

    def test_run_full_quality_check(self):
        """测试运行完整质量检查"""
        try:
            from utils.quality_gate import QualityGate
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

        qg = QualityGate(strict_mode=False, log_enabled=True)
        results = qg.run_full_quality_check(WORKSPACE_DIR)
        self.assertIsNotNone(results, "检查结果不应为None")
        self.assertIsInstance(results, dict, "检查结果应该是字典")

        print("\n完整质量检查结果:")
        for module, result in results.items():
            status = "通过" if result.passed else "失败"
            print(f"  [{status}] {module}: {len(result.errors)} 错误, {len(result.warnings)} 警告")

        # 至少应该检查了简历数据和岗位库
        self.assertGreaterEqual(len(results), 2, "至少应检查2个模块")

    def test_quick_quality_check(self):
        """测试快速质量检查函数"""
        try:
            from utils.quality_gate import quick_quality_check
        except ImportError as e:
            self.skipTest(f"质量门禁模块导入失败: {e}")

        # 快速质量检查会打印结果，我们只测试它不报错
        try:
            result = quick_quality_check(WORKSPACE_DIR)
            self.assertIsInstance(result, bool, "快速检查结果应该是布尔值")
            print(f"\n快速质量检查结果: {'通过' if result else '未通过'}")
        except Exception as e:
            self.fail(f"快速质量检查报错: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
