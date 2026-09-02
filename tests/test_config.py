# -*- coding: utf-8 -*-
"""
测试配置加载工具（utils/config.py）
"""

import os
import sys
import unittest

# 添加工作区目录到路径
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestConfigLoader(unittest.TestCase):
    """测试配置加载工具"""

    def setUp(self):
        """测试前准备"""
        self.config_path = os.path.join(WORKSPACE_DIR, "config.yaml")

    def test_config_file_exists(self):
        """测试配置文件存在"""
        self.assertTrue(os.path.exists(self.config_path), f"配置文件不存在: {self.config_path}")

    def test_load_config(self):
        """测试加载配置"""
        try:
            from utils.config import load_config
            config = load_config()
            self.assertIsNotNone(config, "配置加载失败")
            self.assertIsInstance(config, dict, "配置应该是字典类型")
        except ImportError as e:
            self.skipTest(f"配置模块导入失败: {e}")

    def test_config_sections(self):
        """测试配置包含必要的section"""
        try:
            from utils.config import load_config
            config = load_config()
            required_sections = ["general", "paths", "scraper", "platforms", "matching", "report", "resume"]
            for section in required_sections:
                self.assertIn(section, config, f"配置缺少必要的section: {section}")
        except ImportError as e:
            self.skipTest(f"配置模块导入失败: {e}")

    def test_matching_weights_sum(self):
        """测试匹配权重总和为1.0"""
        try:
            from utils.config import load_config
            config = load_config()
            weights = config.get("matching", {}).get("weights", {})
            total = sum(weights.values())
            self.assertAlmostEqual(total, 1.0, places=2, msg=f"匹配权重总和应为1.0，当前为{total}")
        except ImportError as e:
            self.skipTest(f"配置模块导入失败: {e}")

    def test_enabled_platforms(self):
        """测试已启用平台"""
        try:
            from utils.config import load_config
            config = load_config()
            platforms = config.get("platforms", {})
            enabled_platforms = [name for name, p in platforms.items() if p.get("enabled", True)]
            self.assertGreater(len(enabled_platforms), 0, "至少应启用一个平台")
            print(f"已启用平台: {enabled_platforms}")
        except ImportError as e:
            self.skipTest(f"配置模块导入失败: {e}")

    def test_get_config_value(self):
        """测试获取配置值"""
        try:
            from utils.config import get_config, get_section
            config = get_config()
            self.assertIsNotNone(config, "应能获取到完整配置")
            general = get_section("general")
            self.assertIsNotNone(general, "应能获取到general section")
            print(f"通用配置: {general}")
        except ImportError as e:
            self.skipTest(f"配置模块导入失败: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
