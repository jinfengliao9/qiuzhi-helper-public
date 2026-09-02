# -*- coding: utf-8 -*-
"""测试统一报告主题模块（report_theme.py）"""
import os, sys, unittest
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestReportTheme(unittest.TestCase):
    """测试 report_theme 模块"""

    def test_import(self):
        """测试模块导入"""
        try:
            import report_theme
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"report_theme 导入失败: {e}")

    def test_theme_css(self):
        """测试 THEME_CSS 非空且包含核心样式"""
        import report_theme as T
        self.assertTrue(len(T.THEME_CSS) > 1000, "THEME_CSS 不应为空")
        self.assertIn("#2c5f8a", T.THEME_CSS, "应包含主色 #2c5f8a")
        self.assertIn(".job-card", T.THEME_CSS, "应包含 .job-card 样式")

    def test_esc(self):
        """测试 HTML 转义函数"""
        import report_theme as T
        self.assertEqual(T.esc("<script>"), "&lt;script&gt;")
        self.assertEqual(T.esc("a&b"), "a&amp;b")
        self.assertEqual(T.esc(""), "")
        self.assertEqual(T.esc(None), "")

    def test_section_title(self):
        """测试 section_title 只接受1个参数"""
        import report_theme as T
        html = T.section_title("测试标题")
        self.assertIn("测试标题", html)
        self.assertIn("section-title", html)
        # 验证不接受2个参数
        with self.assertRaises(TypeError):
            T.section_title("标题", "body")

    def test_stat_grid(self):
        """测试统计卡网格"""
        import report_theme as T
        html = T.stat_grid([(10, "总数"), (5, "通过", "#52c41a")])
        self.assertIn("10", html)
        self.assertIn("总数", html)
        self.assertIn("5", html)
        self.assertIn("#52c41a", html)

    def test_page(self):
        """测试页面包装函数"""
        import report_theme as T
        html = T.page("测试页", "测试副标题", "<div>内容</div>")
        self.assertIn("测试页", html)
        self.assertIn("测试副标题", html)
        self.assertIn("<div>内容</div>", html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(T.THEME_CSS, html)

    def test_source_badge(self):
        """测试平台徽标"""
        import report_theme as T
        html = T.source_badge("BOSS直聘")
        self.assertIn("BOSS", html)
        html2 = T.source_badge("智联")
        self.assertIn("智联", html2)

    def test_score_bucket(self):
        """测试匹配分桶（返回标签+颜色元组）"""
        import report_theme as T
        label, color = T.score_bucket(85)
        self.assertIn("匹配", label)
        self.assertTrue(color.startswith("#"))
        label2, color2 = T.score_bucket(40)
        self.assertIn("匹配", label2)


if __name__ == "__main__":
    unittest.main()
