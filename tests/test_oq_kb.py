# -*- coding: utf-8 -*-
"""测试 OQ 开放式问题知识库管理器（oq_kb.py）"""
import os, sys, json, unittest, tempfile, shutil, io

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestOqKb(unittest.TestCase):
    """测试 oq_kb 模块"""

    def setUp(self):
        """每个测试前创建临时知识库目录"""
        self.temp_dir = tempfile.mkdtemp(prefix='oq_kb_test_')
        import oq_kb
        self._original_dir = oq_kb.ANSWER_DIR
        oq_kb.ANSWER_DIR = self.temp_dir

    def tearDown(self):
        """每个测试后清理临时目录"""
        import oq_kb
        oq_kb.ANSWER_DIR = self._original_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_import(self):
        """测试模块导入"""
        try:
            import oq_kb
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"oq_kb 导入失败: {e}")

    def test_get_company_dir_special_chars(self):
        """测试公司目录特殊字符处理"""
        import oq_kb
        # 包含特殊字符的公司名应该被清洗
        result = oq_kb.get_company_dir("测试/公司:\\*?\"<>|")
        # 路径中不应该包含特殊字符
        self.assertNotIn("/", os.path.basename(result))
        self.assertNotIn("\\", os.path.basename(result))
        self.assertNotIn(":", os.path.basename(result))
        # get_company_dir 只返回路径，不创建目录（目录在 add_answer 中创建）
        # 手动创建后验证
        oq_kb.ensure_dir(result)
        self.assertTrue(os.path.isdir(result))

    def test_get_company_dir_normal(self):
        """测试正常公司名目录"""
        import oq_kb
        result = oq_kb.get_company_dir("正常公司名")
        self.assertTrue(result.endswith("正常公司名"))
        # get_company_dir 只返回路径，不创建目录
        oq_kb.ensure_dir(result)
        self.assertTrue(os.path.isdir(result))

    def test_list_companies_empty(self):
        """测试空知识库列出公司"""
        import oq_kb
        companies = oq_kb.list_companies()
        self.assertEqual(len(companies), 0)

    def test_add_answer(self):
        """测试添加答案"""
        import oq_kb
        fpath = oq_kb.add_answer(
            company="测试公司",
            question="为什么选择我们公司？",
            answer="因为贵公司在行业内领先...",
            category="求职动机类",
            qid="1.1"
        )
        # 返回的应该是文件路径
        self.assertTrue(isinstance(fpath, str))
        self.assertTrue(fpath.endswith('.json'))
        # 验证文件已创建
        self.assertTrue(os.path.exists(fpath))
        # 验证文件内容
        with io.open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['company'], '测试公司')
        self.assertEqual(data['question'], '为什么选择我们公司？')
        self.assertEqual(data['answer'], '因为贵公司在行业内领先...')
        self.assertEqual(data['category'], '求职动机类')
        self.assertEqual(data['qid'], '1.1')
        self.assertEqual(data['version'], 1)
        self.assertIsNone(data['rating'])

    def test_add_answer_auto_qid(self):
        """测试添加答案时自动生成 qid"""
        import oq_kb
        fpath = oq_kb.add_answer(
            company="测试公司",
            question="你的职业规划是什么？",
            answer="我希望在3年内成为..."
        )
        self.assertTrue(os.path.exists(fpath))
        with io.open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        # 自动生成的 qid 应该以 custom_ 开头
        self.assertTrue(data['qid'].startswith('custom_'))

    def test_list_answers_empty(self):
        """测试空知识库列出答案"""
        import oq_kb
        answers = oq_kb.list_answers()
        self.assertEqual(len(answers), 0)

    def test_list_answers(self):
        """测试列出答案"""
        import oq_kb
        # 添加两个答案
        oq_kb.add_answer(company="公司A", question="问题1", answer="答案1", qid="1.1")
        oq_kb.add_answer(company="公司B", question="问题2", answer="答案2", qid="2.1")
        # 列出所有
        answers = oq_kb.list_answers()
        self.assertEqual(len(answers), 2)
        # 按公司筛选
        answers_a = oq_kb.list_answers(company="公司A")
        self.assertEqual(len(answers_a), 1)
        self.assertEqual(answers_a[0]['company'], '公司A')

    def test_list_companies(self):
        """测试列出公司"""
        import oq_kb
        oq_kb.add_answer(company="公司A", question="问题1", answer="答案1", qid="1.1")
        oq_kb.add_answer(company="公司B", question="问题2", answer="答案2", qid="2.1")
        companies = oq_kb.list_companies()
        self.assertEqual(len(companies), 2)
        self.assertIn("公司A", companies)
        self.assertIn("公司B", companies)

    def test_search_answers(self):
        """测试搜索答案"""
        import oq_kb
        oq_kb.add_answer(company="公司A", question="为什么选择我们公司？", answer="因为行业领先", qid="1.1")
        oq_kb.add_answer(company="公司B", question="你的职业规划？", answer="3年内成为专家", qid="2.1")
        # 搜索"公司"
        results = oq_kb.search_answers("公司")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['company'], '公司A')
        # 搜索"规划"
        results = oq_kb.search_answers("规划")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['company'], '公司B')
        # 搜索不存在的关键词
        results = oq_kb.search_answers("不存在的关键词")
        self.assertEqual(len(results), 0)

    def test_show_answer_by_file(self):
        """测试通过文件路径查看答案（替代 get_answer 函数）"""
        import oq_kb
        fpath = oq_kb.add_answer(company="测试公司", question="问题1", answer="答案1", qid="1.1")
        # 直接读文件验证
        self.assertTrue(os.path.exists(fpath))
        with io.open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['question'], '问题1')
        self.assertEqual(data['answer'], '答案1')

    def test_show_stats_runs(self):
        """测试 show_stats 函数能正常运行（不报错）"""
        import oq_kb
        oq_kb.add_answer(company="公司A", question="问题1", answer="答案1", qid="1.1")
        # show_stats 是打印函数，只要不报错就算通过
        try:
            # 捕获 stdout 避免测试输出混乱
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            oq_kb.show_stats()
            sys.stdout = old_stdout
            self.assertTrue(True)
        except Exception as e:
            sys.stdout = old_stdout
            self.fail(f"show_stats 运行失败: {e}")

    def test_stats_by_counting(self):
        """通过 list_companies 和 list_answers 验证统计数据"""
        import oq_kb
        oq_kb.add_answer(company="公司A", question="问题1", answer="答案1", qid="1.1")
        oq_kb.add_answer(company="公司A", question="问题2", answer="答案2", qid="1.2")
        oq_kb.add_answer(company="公司B", question="问题3", answer="答案3", qid="2.1")
        # 验证公司数量
        companies = oq_kb.list_companies()
        self.assertEqual(len(companies), 2)
        # 验证答案总数
        all_answers = oq_kb.list_answers()
        self.assertEqual(len(all_answers), 3)
        # 验证各公司答案数
        self.assertEqual(len(oq_kb.list_answers(company="公司A")), 2)
        self.assertEqual(len(oq_kb.list_answers(company="公司B")), 1)

    def test_export_company(self):
        """测试导出公司答案为 Markdown"""
        import oq_kb
        oq_kb.add_answer(company="测试公司", question="问题1", answer="答案1", category="分类A", qid="1.1")
        oq_kb.add_answer(company="测试公司", question="问题2", answer="答案2", category="分类B", qid="1.2")
        # 导出
        output_path = os.path.join(self.temp_dir, "export.md")
        result = oq_kb.export_company("测试公司", output_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))
        # 验证内容
        with io.open(output_path, encoding='utf-8') as f:
            content = f.read()
        self.assertIn("测试公司", content)
        self.assertIn("问题1", content)
        self.assertIn("答案1", content)
        self.assertIn("问题2", content)
        self.assertIn("答案2", content)

    def test_export_company_empty(self):
        """测试导出不存在的公司（应该返回 False）"""
        import oq_kb
        output_path = os.path.join(self.temp_dir, "empty_export.md")
        result = oq_kb.export_company("不存在的公司", output_path)
        self.assertFalse(result)
        self.assertFalse(os.path.exists(output_path))

    def test_answer_json_structure(self):
        """测试答案 JSON 结构完整性"""
        import oq_kb
        fpath = oq_kb.add_answer(
            company="结构测试公司",
            question="结构测试问题",
            answer="结构测试答案",
            category="测试分类",
            qid="struct.1"
        )
        with io.open(fpath, encoding='utf-8') as f:
            data = json.load(f)
        # 验证所有必需字段存在
        required_fields = ['qid', 'category', 'question', 'answer', 'company',
                          'created', 'updated', 'version', 'rating']
        for field in required_fields:
            self.assertIn(field, data, f"缺少必需字段: {field}")
        # 验证版本号
        self.assertEqual(data['version'], 1)
        # 验证评分默认值
        self.assertIsNone(data['rating'])

    def test_ensure_dir(self):
        """测试 ensure_dir 函数"""
        import oq_kb
        test_path = os.path.join(self.temp_dir, "new_subdir", "deep_dir")
        self.assertFalse(os.path.exists(test_path))
        oq_kb.ensure_dir(test_path)
        self.assertTrue(os.path.isdir(test_path))
        # 再次调用不应该报错
        oq_kb.ensure_dir(test_path)
        self.assertTrue(os.path.isdir(test_path))


if __name__ == '__main__':
    unittest.main()
