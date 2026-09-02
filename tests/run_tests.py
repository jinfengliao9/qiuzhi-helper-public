# -*- coding: utf-8 -*-
"""
测试运行器：运行所有单元测试和端到端测试
"""

import os
import sys
import unittest

# 工作区目录
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# 测试目录
TESTS_DIR = os.path.join(WORKSPACE_DIR, "tests")


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("  求职工作区 - 测试运行器")
    print("  Job Search Assistant - Test Runner")
    print("=" * 70)
    print()

    # 发现所有测试
    loader = unittest.TestLoader()
    suite = loader.discover(TESTS_DIR, pattern="test_*.py")

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    print(f"  运行测试数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")
    print()

    if result.failures:
        print("  失败的测试:")
        for test, traceback in result.failures:
            print(f"    - {test}")
        print()

    if result.errors:
        print("  错误的测试:")
        for test, traceback in result.errors:
            print(f"    - {test}")
        print()

    if result.wasSuccessful():
        print("  ✓ 所有测试通过！")
    else:
        print("  ✗ 部分测试未通过，请检查上述问题")

    print("=" * 70)

    return result.wasSuccessful()


def run_specific_test(test_module):
    """运行特定的测试模块"""
    print(f"运行测试模块: {test_module}")
    print()

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_module)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 运行特定的测试模块
        test_module = sys.argv[1]
        success = run_specific_test(test_module)
    else:
        # 运行所有测试
        success = run_all_tests()

    sys.exit(0 if success else 1)
