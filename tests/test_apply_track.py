# -*- coding: utf-8 -*-
"""测试网申进度看板（apply_track.py）"""
import os, sys, json, unittest, tempfile, shutil
from datetime import datetime, timedelta
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)


class TestApplyTrack(unittest.TestCase):
    """测试 apply_track 模块"""

    def setUp(self):
        """测试前备份真实数据，用临时数据"""
        import apply_track
        self.real_path = apply_track.DATA_PATH
        self.backup_path = self.real_path + ".bak"
        if os.path.exists(self.real_path):
            shutil.copy2(self.real_path, self.backup_path)
        # 清空为测试数据
        apply_track.save_data({"records": []})

    def tearDown(self):
        """测试后恢复真实数据"""
        import apply_track
        if os.path.exists(self.backup_path):
            shutil.copy2(self.backup_path, self.real_path)
            os.remove(self.backup_path)

    def test_import(self):
        """测试模块导入"""
        try:
            import apply_track
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"apply_track 导入失败: {e}")

    def test_valid_statuses(self):
        """测试8种有效状态"""
        import apply_track
        self.assertEqual(len(apply_track.VALID_STATUSES), 8)
        for s in ["待投递", "已投递", "测评中", "面试中", "offer", "已拒绝", "待定", "放弃"]:
            self.assertIn(s, apply_track.VALID_STATUSES)

    def test_load_save_data(self):
        """测试数据加载和保存"""
        import apply_track
        data = apply_track.load_data()
        self.assertIn("records", data)
        self.assertEqual(len(data["records"]), 0)
        # 保存测试数据
        apply_track.save_data({"records": [{"id": 1, "company": "测试公司"}]})
        data2 = apply_track.load_data()
        self.assertEqual(len(data2["records"]), 1)
        self.assertEqual(data2["records"][0]["company"], "测试公司")

    def test_next_id(self):
        """测试ID生成"""
        import apply_track
        self.assertEqual(apply_track.next_id({"records": []}), 1)
        self.assertEqual(apply_track.next_id({"records": [{"id": 1}, {"id": 5}]}), 6)

    def test_find_record(self):
        """测试查找记录"""
        import apply_track
        data = {"records": [{"id": 1, "company": "A"}, {"id": 2, "company": "B"}]}
        self.assertEqual(apply_track.find_record(data, 1)["company"], "A")
        self.assertIsNone(apply_track.find_record(data, 99))

    def test_add_record_via_function(self):
        """测试通过函数添加记录"""
        import apply_track
        record = {
            "id": 1, "company": "中国电信", "position": "测绘工程师",
            "status": "待投递", "deadline": "2026-10-15",
            "timeline": [{"date": "2026-09-02", "status": "待投递", "note": "创建"}]
        }
        data = apply_track.load_data()
        data["records"].append(record)
        apply_track.save_data(data)
        data2 = apply_track.load_data()
        self.assertEqual(len(data2["records"]), 1)
        self.assertEqual(data2["records"][0]["company"], "中国电信")

    def test_deadline_logic(self):
        """测试截止日期判断逻辑"""
        import apply_track
        today = datetime.now().date()
        # 构造3天内截止的记录
        urgent_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
        future_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        expired_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        data = {"records": [
            {"id": 1, "company": "紧急", "status": "待投递", "deadline": urgent_date},
            {"id": 2, "company": "远期", "status": "待投递", "deadline": future_date},
            {"id": 3, "company": "过期", "status": "待投递", "deadline": expired_date},
            {"id": 4, "company": "无截止", "status": "待投递", "deadline": ""},
        ]}
        apply_track.save_data(data)
        # 验证 cmd_deadline 能正常运行不崩溃
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            class Args: pass
            apply_track.cmd_deadline(Args())
        output = f.getvalue()
        self.assertIn("紧急", output)
        self.assertIn("过期", output)
        self.assertNotIn("远期", output)

    def test_report_generation(self):
        """测试HTML看板报告生成"""
        import apply_track
        today = datetime.now().date()
        data = {"records": [
            {"id": 1, "company": "中国电信", "position": "测绘工程师",
             "city": "广州", "status": "待投递", "deadline": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
             "apply_date": "2026-09-02", "source": "国聘", "notes": "国企",
             "timeline": [{"date": "2026-09-02", "status": "待投递", "note": "创建"}]},
            {"id": 2, "company": "示例测绘公司", "position": "测绘实习生",
             "city": "示例城市B", "status": "面试中", "deadline": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
             "apply_date": "2026-09-01", "source": "实习",
             "timeline": [{"date": "2026-09-01", "status": "面试中", "note": "二面"}]},
        ]}
        apply_track.save_data(data)
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            class Args: pass
            output_path = apply_track.cmd_report(Args())
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("网申进度看板", html)
        self.assertIn("中国电信", html)
        self.assertIn("示例测绘公司", html)
        self.assertIn("待投递", html)
        self.assertIn("面试中", html)
        # 清理测试报告
        os.remove(output_path)

    def test_empty_report(self):
        """测试空数据报告不崩溃"""
        import apply_track
        apply_track.save_data({"records": []})
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            class Args: pass
            output_path = apply_track.cmd_report(Args())
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("暂无网申记录", html)
        os.remove(output_path)


if __name__ == "__main__":
    unittest.main()
