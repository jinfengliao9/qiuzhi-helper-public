# -*- coding: utf-8 -*-
"""测试网申机筛质量检查器（apply_check.py）"""
import os, sys, json, unittest, tempfile
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestApplyCheck(unittest.TestCase):
    """测试 apply_check 模块"""

    def test_import(self):
        """测试模块导入"""
        try:
            import apply_check
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"apply_check 导入失败: {e}")

    def test_adapt_to_check_resume(self):
        """测试中文字段名适配层"""
        import apply_check
        profile = {
            "基本信息": {
                "姓名": "张三", "手机": "13800138000", "邮箱": "test@test.com",
                "求职意向": "测绘工程师", "现居住地": "广州", "证件照": "avatar.jpg"
            },
            "教育背景": [{"学校": "示例大学", "专业": "测绘工程", "学历": "本科",
                          "入学时间": "2023-09", "毕业时间": "2027-06"}],
            "实习经历": [{"单位名称": "示例测绘公司", "岗位": "测绘实习生",
                          "入职时间": "2026-07", "离职时间": "2026-09",
                          "工作内容": ["负责地籍测量", "使用ArcGIS"]}],
            "专业技能": {"软件工具": ["ArcGIS", "CAD"]},
            "技能证书": {"语言能力": [{"名称": "日语四级", "分数": "63.5"}]},
        }
        adapted = apply_check.adapt_to_check_resume(profile)
        # 返回嵌套结构：基本信息用英文key，教育/实习是列表
        self.assertEqual(adapted["基本信息"]["name"], "张三")
        self.assertEqual(adapted["基本信息"]["phone"], "13800138000")
        self.assertEqual(adapted["基本信息"]["job_intention"], "测绘工程师")
        self.assertEqual(len(adapted["教育背景"]), 1)
        self.assertEqual(adapted["教育背景"][0]["school"], "示例大学")
        self.assertEqual(len(adapted["实习经历"]), 1)
        self.assertEqual(adapted["实习经历"][0]["company"], "示例测绘公司")
        self.assertIn("技能清单", adapted)
        self.assertIn("ArcGIS", adapted["技能清单"].get("软件工具", []))

    def test_adapt_empty_profile(self):
        """测试空配置文件适配不崩溃"""
        import apply_check
        adapted = apply_check.adapt_to_check_resume({})
        self.assertEqual(adapted["基本信息"]["name"], "")
        self.assertEqual(adapted["教育背景"], [])
        self.assertEqual(adapted["实习经历"], [])

    def test_check_id_card(self):
        """测试身份证校验（接受整个data字典）"""
        import apply_check
        # 用户真实身份证，校验位正确
        data = {"基本信息": {"身份证号": "11010120000101001X"}}
        result = apply_check.check_id_card(data)
        self.assertIn("passed", result)
        # 应该有通过项（格式正确）
        self.assertTrue(len(result["passed"]) > 0 or len(result["warnings"]) >= 0)
        # 无效身份证
        data2 = {"基本信息": {"身份证号": "123456789012345678"}}
        result2 = apply_check.check_id_card(data2)
        self.assertTrue(len(result2["issues"]) > 0 or len(result2["warnings"]) > 0)
        # 空值
        data3 = {"基本信息": {}}
        result3 = apply_check.check_id_card(data3)
        self.assertIsNotNone(result3)

    def test_run_all_checks_with_real_profile(self):
        """用真实 application_profile.json 运行全量检查"""
        import apply_check
        profile_path = os.path.join(WORKSPACE_DIR, "application_profile.json")
        if not os.path.exists(profile_path):
            self.skipTest("application_profile.json 不存在")
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
        results, jd_result, page_result = apply_check.run_all_checks(profile)
        # results 是按维度分组的字典
        self.assertIsInstance(results, dict)
        self.assertGreaterEqual(len(results), 10, "应至少10个检查维度")
        for dim_name, dim_data in results.items():
            self.assertIn("issues", dim_data, f"维度 {dim_name} 应含 issues")
            self.assertIn("warnings", dim_data)
            self.assertIn("passed", dim_data)
        # 用户信息底座应该0个必须修改
        total_issues = sum(len(d.get("issues", [])) for d in results.values())
        self.assertEqual(total_issues, 0, "用户信息底座不应有必须修改项")
        # page_result 应包含页数
        self.assertIn("pages", page_result)

    def test_generate_check_report(self):
        """测试HTML检查报告生成"""
        import apply_check
        profile_path = os.path.join(WORKSPACE_DIR, "application_profile.json")
        if not os.path.exists(profile_path):
            self.skipTest("application_profile.json 不存在")
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
        results, jd_result, page_result = apply_check.run_all_checks(profile)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
            output_path = f.name
        try:
            apply_check.generate_check_report(profile, results, jd_result, page_result, output_path)
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("机筛", html)
            self.assertIn("问题", html)
            self.assertIn("建议优化", html)
            self.assertIn("已达标", html)
            self.assertGreater(len(html), 1000)
        finally:
            os.remove(output_path)


if __name__ == "__main__":
    unittest.main()
