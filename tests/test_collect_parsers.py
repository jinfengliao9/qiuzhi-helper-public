# -*- coding: utf-8 -*-
"""
测试 Edge 扩展采集解析器：
  - boss_api/parse_joblist_api.py（BOSS直聘）
  - boss_api/parse_zhaopin_api.py（智联招聘）

覆盖：字段映射、链接构造、完整JD拆分、技能/福利提取、去重、容错、HTML清洗。
夹具为内联真实结构（与2026-08真实样本字段一致），不依赖外部文件。
"""

import os
import sys
import unittest

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOSS_API_DIR = os.path.join(WORKSPACE_DIR, "boss_api")
for p in (WORKSPACE_DIR, BOSS_API_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


# ============================================================
# 通用夹具
# ============================================================

def make_boss_raw(encrypt_job_id="boss_job_001", encrypt_brand_id="brand_001",
                  with_detail=True):
    """构造一条真实结构的BOSS列表原始记录。"""
    raw = {
        "encryptJobId": encrypt_job_id,
        "encryptBrandId": encrypt_brand_id,
        "brandName": "测试测绘有限公司",
        "jobName": "测绘工程师",
        "cityName": "广州",
        "areaDistrict": "天河区",
        "businessDistrict": "珠江新城",
        "salaryDesc": "8-12K·13薪",
        "jobDegree": "本科",
        "jobExperience": "在校/应届",
        "skills": ["CAD", "CASS"],
        "jobLabels": ["双休"],
        "welfareList": ["五险一金", "包住"],
        "brandScaleName": "100-499人",
        "brandStageName": "未融资",
        "brandIndustry": "测绘地理信息",
        "securityId": "sec_test",
    }
    if with_detail:
        raw["__detail"] = {
            "jobInfo": {
                "postDescription": "负责控制测量、地形测绘。<br/>使用CASS、CAD成图。<br/>任职要求：本科及以上，测绘工程专业，能出差。",
                "showSkills": ["ArcGIS", "RTK"],
            },
            "brandComInfo": {"industryName": "测绘", "stageName": "未融资", "scaleName": "100-499人"},
        }
    return raw


def make_zh_raw(number="CC9001", with_jd=True):
    """构造一条真实结构的智联列表原始记录。"""
    raw = {
        "name": "测量员",
        "companyName": "测试地理信息院",
        "salary60": "5000-8000元",
        "education": "本科",
        "workingExp": "应届",
        "workCity": "示例城市B",
        "cityDistrict": "梅江区",
        "streetName": "",
        "companySize": "500-1000人",
        "industryName": "学术/科研",
        "propertyName": "事业单位",
        "number": number,
        "positionURL": "http://jobs.zhaopin.com/CC9001.htm",
        "companyUrl": "https://company.zhaopin.com/CZ9001.htm",
        "jobSkillTags": [{"name": "全站仪"}, {"name": "水准测量"}],
        "skillLabel": [{"value": "RTK"}],
    }
    if with_jd:
        raw["jobDetailData"] = {"position": {"desc": {
            "description": "负责工程测量、控制网布设。<br/>使用全站仪、水准仪。<br/>任职要求：测绘相关专业，能出差。",
            "welfareLabel": [{"name": "带薪年假"}],
        }}}
    return raw


# ============================================================
# BOSS 解析器测试
# ============================================================

class TestBossParser(unittest.TestCase):
    """BOSS直聘 joblist 解析器"""

    def setUp(self):
        try:
            from parse_joblist_api import (extract_jobs, dedupe, map_one,
                                            html_to_text, split_jd)
            self.extract_jobs = extract_jobs
            self.dedupe = dedupe
            self.map_one = map_one
            self.html_to_text = html_to_text
            self.split_jd = split_jd
        except ImportError as e:
            self.skipTest(f"BOSS解析器导入失败: {e}")

    # --- 信封/容错 ---
    def test_extract_zpData_envelope(self):
        """zpData.jobList 信封能正常抽出岗位"""
        raw = {"zpData": {"jobList": [make_boss_raw()]}}
        jobs = self.extract_jobs(raw)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["position"], "测绘工程师")

    def test_extract_bare_jobList_fallback(self):
        """没有 zpData 时，直接 jobList 兜底"""
        raw = {"jobList": [make_boss_raw()]}
        jobs = self.extract_jobs(raw)
        self.assertEqual(len(jobs), 1)

    def test_extract_empty_and_non_dict(self):
        """空字典、非字典、无jobList都返回空列表，不抛异常"""
        self.assertEqual(self.extract_jobs({}), [])
        self.assertEqual(self.extract_jobs(None), [])
        self.assertEqual(self.extract_jobs("not a dict"), [])

    # --- 字段映射 ---
    def test_field_mapping(self):
        """核心字段映射正确：公司/岗位/城市/薪资/学历/经验/来源"""
        job = self.map_one(make_boss_raw())
        self.assertEqual(job["company"], "测试测绘有限公司")
        self.assertEqual(job["position"], "测绘工程师")
        self.assertEqual(job["city"], "广州")
        self.assertEqual(job["work_location"], "广州·天河区·珠江新城")
        self.assertEqual(job["salary"], "8-12K·13薪")
        self.assertEqual(job["education"], "本科")
        self.assertEqual(job["experience"], "在校/应届")
        self.assertEqual(job["source"], "BOSS直聘")
        self.assertEqual(job["skills"], ["CAD", "CASS", "ArcGIS", "RTK"])  # 列表+详情合并去重
        self.assertEqual(job["benefits"], ["五险一金", "包住"])

    def test_links(self):
        """岗位链接和公司主页链接构造正确"""
        job = self.map_one(make_boss_raw(encrypt_job_id="abc123", encrypt_brand_id="br999"))
        self.assertEqual(job["job_url"], "https://www.zhipin.com/job_detail/abc123.html")
        self.assertEqual(job["company_link"], "https://www.zhipin.com/gongsi/br999.html")

    def test_missing_ids_gives_empty_links(self):
        """缺少 encryptJobId/encryptBrandId 时链接为空字符串，不报错"""
        raw = make_boss_raw()
        raw["encryptJobId"] = ""
        raw["encryptBrandId"] = ""
        job = self.map_one(raw)
        self.assertEqual(job["job_url"], "")
        self.assertEqual(job["company_link"], "")

    # --- 完整JD ---
    def test_detail_jd_split(self):
        """带 __detail 时，JD被清洗并拆分为职责/要求，has_detail=1"""
        job = self.map_one(make_boss_raw(with_detail=True))
        self.assertEqual(job["has_detail"], 1)
        self.assertIn("控制测量", job["responsibilities"])
        self.assertIn("任职要求", job["requirements"])
        self.assertIn("测绘工程专业", job["detail_text"])
        self.assertNotIn("<br/>", job["detail_text"])  # HTML已清洗

    def test_no_detail_has_detail_zero(self):
        """不带 __detail 时 has_detail=0，职责/要求为空"""
        job = self.map_one(make_boss_raw(with_detail=False))
        self.assertEqual(job["has_detail"], 0)
        self.assertEqual(job["responsibilities"], "")
        self.assertEqual(job["requirements"], "")
        self.assertEqual(job["detail_text"], "")
        self.assertEqual(job["skills"], ["CAD", "CASS"])  # 无详情时只有列表技能

    # --- 过滤 ---
    def test_missing_company_or_position_filtered(self):
        """缺少公司名或岗位名的记录被过滤（map_one返回None或extract_jobs跳过）"""
        raw = make_boss_raw()
        raw["brandName"] = ""
        raw["jobName"] = ""
        jobs = self.extract_jobs({"zpData": {"jobList": [raw]}})
        self.assertEqual(jobs, [])

    # --- 去重 ---
    def test_dedupe_by_encrypt_job_id(self):
        """相同 encrypt_job_id 的重复记录只保留一条"""
        r1 = make_boss_raw(encrypt_job_id="same_id")
        r2 = make_boss_raw(encrypt_job_id="same_id")
        jobs = [self.map_one(r1), self.map_one(r2)]
        self.assertEqual(len(self.dedupe(jobs)), 1)

    def test_dedupe_by_company_position_fallback(self):
        """无 encrypt_job_id 时按 公司|岗位 去重"""
        r1 = make_boss_raw(); r1["encryptJobId"] = ""
        r2 = make_boss_raw(); r2["encryptJobId"] = ""
        jobs = [self.map_one(r1), self.map_one(r2)]
        self.assertEqual(len(self.dedupe(jobs)), 1)

    # --- 工具函数 ---
    def test_html_to_text(self):
        """HTML清洗：br转换行、去标签、去实体、去重连续空行"""
        out = self.html_to_text("职责A<br/>职责B<p>职责C</p>&amp;D")
        self.assertIn("职责A", out)
        self.assertIn("职责B", out)
        self.assertIn("职责C", out)
        self.assertIn("&D", out)  # &amp; 解码为 &
        self.assertNotIn("<", out)

    def test_split_jd(self):
        """JD在'任职要求'处切分为职责与要求"""
        resp, req = self.split_jd("负责测绘工作。任职要求：本科，能出差。")
        self.assertIn("负责测绘工作", resp)
        self.assertIn("任职要求", req)
        self.assertIn("能出差", req)

    def test_split_jd_no_marker_returns_all_as_resp(self):
        """没有要求/资格/条件等标记时，整段归入职责，要求为空"""
        resp, req = self.split_jd("只有职责没有别的内容")
        self.assertEqual(resp, "只有职责没有别的内容")
        self.assertEqual(req, "")


# ============================================================
# 智联解析器测试
# ============================================================

class TestZhaopinParser(unittest.TestCase):
    """智联招聘搜索结果解析器"""

    def setUp(self):
        try:
            from parse_zhaopin_api import (parse_zhaopin, map_one_zh,
                                            _txt, _tag_names, _clean_html, _split_jd)
            self.parse_zhaopin = parse_zhaopin
            self.map_one_zh = map_one_zh
            self._txt = _txt
            self._tag_names = _tag_names
            self._clean_html = _clean_html
            self._split_jd = _split_jd
        except ImportError as e:
            self.skipTest(f"智联解析器导入失败: {e}")

    # --- 信封/容错 ---
    def test_parse_list(self):
        """正常列表解析出岗位"""
        jobs = self.parse_zhaopin([make_zh_raw()])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["position"], "测量员")

    def test_parse_empty_none(self):
        """空列表/None返回空，不抛异常"""
        self.assertEqual(self.parse_zhaopin([]), [])
        self.assertEqual(self.parse_zhaopin(None), [])

    # --- 字段映射 ---
    def test_field_mapping(self):
        """核心字段映射：name→position, companyName→company, salary60等"""
        job = self.map_one_zh(make_zh_raw())
        self.assertEqual(job["position"], "测量员")
        self.assertEqual(job["company"], "测试地理信息院")
        self.assertEqual(job["salary"], "5000-8000元")
        self.assertEqual(job["education"], "本科")
        self.assertEqual(job["experience"], "应届")
        self.assertEqual(job["city"], "示例城市B")
        self.assertEqual(job["work_location"], "示例城市B·梅江区")
        self.assertEqual(job["source"], "智联招聘")
        self.assertEqual(job["company_size"], "500-1000人")
        self.assertIn("学术/科研", job["company_industry"])
        self.assertIn("事业单位", job["company_industry"])

    def test_salary_fallback_fields(self):
        """salary60缺失时回退 salaryReal / salary"""
        raw = make_zh_raw()
        raw["salary60"] = ""
        raw["salaryReal"] = "6000-9000元"
        self.assertEqual(self.map_one_zh(raw)["salary"], "6000-9000元")

    # --- 链接 ---
    def test_links_positionURL(self):
        """有 positionURL 时直接用，companyUrl 作为公司主页"""
        job = self.map_one_zh(make_zh_raw())
        self.assertEqual(job["job_url"], "http://jobs.zhaopin.com/CC9001.htm")
        self.assertEqual(job["company_link"], "https://company.zhaopin.com/CZ9001.htm")

    def test_job_url_fallback_by_number(self):
        """positionURL缺失但有number时，拼 http://jobs.zhaopin.com/{number}.htm"""
        raw = make_zh_raw(number="CC12345")
        raw["positionURL"] = ""
        job = self.map_one_zh(raw)
        self.assertEqual(job["job_url"], "http://jobs.zhaopin.com/CC12345.htm")

    def test_company_link_fallback_search(self):
        """companyUrl缺失时回退到站内搜索链接（含公司名）"""
        raw = make_zh_raw()
        raw["companyUrl"] = ""
        job = self.map_one_zh(raw)
        self.assertIn("测试地理信息院", job["company_link"])
        self.assertIn("sou.zhaopin.com", job["company_link"])

    # --- 内嵌完整JD ---
    def test_embedded_jd(self):
        """列表内嵌JD被清洗、拆分，has_detail=1"""
        job = self.map_one_zh(make_zh_raw(with_jd=True))
        self.assertEqual(job["has_detail"], 1)
        self.assertIn("工程测量", job["responsibilities"])
        self.assertIn("任职要求", job["requirements"])
        self.assertIn("测绘相关专业", job["detail_text"])
        self.assertNotIn("<br/>", job["detail_text"])

    def test_no_jd_has_detail_zero(self):
        """无内嵌JD时 has_detail=0，detail_text为空"""
        job = self.map_one_zh(make_zh_raw(with_jd=False))
        self.assertEqual(job["has_detail"], 0)
        self.assertEqual(job["detail_text"], "")

    # --- 技能/福利 ---
    def test_skills_merged_unique(self):
        """jobSkillTags[].name + skillLabel[].value 合并去重"""
        job = self.map_one_zh(make_zh_raw())
        self.assertEqual(job["skills"], ["全站仪", "水准测量", "RTK"])

    def test_welfare_from_desc(self):
        """福利从 desc.welfareLabel 提取"""
        job = self.map_one_zh(make_zh_raw())
        self.assertIn("带薪年假", job["benefits"])

    # --- 过滤/去重 ---
    def test_missing_name_company_filtered(self):
        """缺少岗位名或公司名的记录被过滤"""
        raw = make_zh_raw()
        raw["name"] = ""
        raw["companyName"] = ""
        self.assertEqual(self.parse_zhaopin([raw]), [])

    def test_dedupe_by_number(self):
        """相同 number 的记录只保留一条"""
        jobs = self.parse_zhaopin([make_zh_raw(number="same"), make_zh_raw(number="same")])
        self.assertEqual(len(jobs), 1)

    def test_dedupe_by_company_position(self):
        """无 number 时按 公司|岗位 去重"""
        r1 = make_zh_raw(); r1["number"] = ""
        r2 = make_zh_raw(); r2["number"] = ""
        jobs = self.parse_zhaopin([r1, r2])
        self.assertEqual(len(jobs), 1)

    # --- 工具函数 ---
    def test_txt_variants(self):
        """_txt 处理 str / dict{name} / dict{displayName} / dict{items} / list"""
        self.assertEqual(self._txt("直接字符串"), "直接字符串")
        self.assertEqual(self._txt({"name": "具名"}), "具名")
        self.assertEqual(self._txt({"displayName": "显示名"}), "显示名")
        self.assertEqual(self._txt({"items": [{"name": "a"}, {"name": "b"}]}), "a·b")
        self.assertEqual(self._txt(["x", "y"]), "x·y")
        self.assertEqual(self._txt(None), "")

    def test_tag_names_variants(self):
        """_tag_names 处理 [{'name'}] / [{'value'}] / [{'labelName'}] / ['str']，去重"""
        self.assertEqual(self._tag_names([{"name": "A"}, {"value": "B"}, {"labelName": "C"}]), ["A", "B", "C"])
        self.assertEqual(self._tag_names(["A", "A", "B"]), ["A", "B"])
        self.assertEqual(self._tag_names(None), [])

    def test_clean_html(self):
        """_clean_html 去标签、br转换行、去实体"""
        out = self._clean_html("职责A<br/>职责B<p>职责C</p>&amp;D")
        self.assertIn("职责A", out)
        self.assertIn("职责B", out)
        self.assertIn("职责C", out)
        self.assertIn("&D", out)
        self.assertNotIn("<", out)

    def test_split_jd_behavior(self):
        """智联JD切分：有标记切分，无标记整段归职责"""
        resp, req = self._split_jd("负责测绘。任职要求：本科。")
        self.assertIn("负责测绘", resp)
        self.assertIn("任职要求", req)
        resp2, req2 = self._split_jd("只有职责")
        self.assertEqual(resp2, "只有职责")
        self.assertEqual(req2, "")


# ============================================================
# 前程无忧(51job)解析器测试
# ============================================================

def make_51job_raw(job_id="51job_001", with_jd=True):
    """构造一条真实结构的51job列表原始记录。"""
    raw = {
        "jobId": job_id,
        "jobName": "测绘工程师(J12345)",
        "jobTags": "['本科', '测绘工程', '五险一金']",
        "jobTagsList": [
            {"jobTagName": "本科"},
            {"jobTagName": "测绘工程"},
            {"jobTagName": "五险一金"},
        ],
        "jobAreaString": "广州·天河区",
        "provideSalaryString": "8千-1.2万",
        "jobSalaryMin": 8000,
        "jobSalaryMax": 12000,
        "workYearString": "1-3年",
        "degreeString": "本科",
        "fullCompanyName": "测试测绘科技有限公司",
        "companyName": "测试测绘",
        "companyTypeString": "民营",
        "companySizeString": "100-500人",
        "companyIndustryType1Str": "测绘/地理信息",
        "jobHref": "https://jobs.51job.com/guangzhou-thq/12345.html",
        "companyHref": "https://jobs.51job.com/all/coABC123.html",
        "hrName": "张经理",
        "issueDateString": "2026-08-28 10:00:00",
        "jobWelfareCodeDataList": [
            {"code": "1001", "chineseTitle": "五险一金", "typeTitle": "五险一金"},
            {"code": "1002", "chineseTitle": "带薪年假", "typeTitle": "带薪年假"},
        ],
        "isIntern": False,
        "lon": 113.32,
        "lat": 23.13,
    }
    if with_jd:
        raw["jobDescribe"] = (
            "工作职责:\n"
            "1. 负责控制测量、地形测绘、地籍调查等外业工作；\n"
            "2. 使用CASS、CAD成图，进行数据处理与建库；\n"
            "任职资格:\n"
            "1. 本科及以上学历，测绘工程、地理信息等相关专业；\n"
            "2. 熟练使用ArcGIS、CAD、CASS等软件，能出差。"
        )
    return raw


class Test51jobParser(unittest.TestCase):
    """前程无忧(51job)解析器测试"""

    def setUp(self):
        from parse_51job_api import parse_51job, parse_one, dedupe_51job
        self.parse_51job = parse_51job
        self.parse_one = parse_one
        self.dedupe_51job = dedupe_51job

    def test_field_mapping(self):
        """字段映射：jobName→position, fullCompanyName→company, provideSalaryString→salary"""
        j = self.parse_one(make_51job_raw())
        self.assertEqual(j["position"], "测绘工程师")  # (J12345)被清理
        self.assertEqual(j["company"], "测试测绘科技有限公司")
        self.assertEqual(j["salary"], "8千-1.2万")
        self.assertEqual(j["salary_min"], 8000)
        self.assertEqual(j["salary_max"], 12000)
        self.assertEqual(j["city"], "广州")
        self.assertEqual(j["work_location"], "广州·天河区")
        self.assertEqual(j["education"], "本科")
        self.assertEqual(j["experience"], "1-3年")
        self.assertEqual(j["source"], "前程无忧")
        self.assertEqual(j["encrypt_job_id"], "51job_001")
        self.assertEqual(j["job_url"], "https://jobs.51job.com/guangzhou-thq/12345.html")
        self.assertEqual(j["company_link"], "https://jobs.51job.com/all/coABC123.html")

    def test_job_name_cleanup(self):
        """职位编号清理：(J12345)后缀被移除"""
        j = self.parse_one(make_51job_raw())
        self.assertNotIn("J12345", j["position"])
        self.assertEqual(j["position"], "测绘工程师")

    def test_jd_split(self):
        """JD拆分：工作职责→responsibilities, 任职资格→requirements"""
        j = self.parse_one(make_51job_raw())
        self.assertTrue(j["has_detail"])
        self.assertIn("控制测量", j["responsibilities"])
        self.assertIn("CASS", j["responsibilities"])
        self.assertIn("本科及以上", j["requirements"])
        self.assertIn("ArcGIS", j["requirements"])
        self.assertIn("工作职责", j["detail_text"])

    def test_jd_split_bracket_format(self):
        """JD拆分：【工作内容】【任职要求】格式也能正确拆分，无】残留"""
        raw = make_51job_raw(with_jd=False)
        raw["jobDescribe"] = "【工作内容】\n1、负责现场测量放线。\n【任职要求】\n1、大专及以上学历。"
        j = self.parse_one(raw)
        self.assertIn("现场测量放线", j["responsibilities"])
        self.assertIn("大专及以上", j["requirements"])
        self.assertFalse(j["responsibilities"].startswith("】"))
        self.assertFalse(j["requirements"].startswith("】"))

    def test_tags_parsing(self):
        """标签解析：jobTagsList字典列表→字符串列表"""
        j = self.parse_one(make_51job_raw())
        self.assertIn("本科", j["job_labels"])
        self.assertIn("测绘工程", j["job_labels"])
        self.assertIn("五险一金", j["job_labels"])
        # 不应该有字典格式
        for label in j["job_labels"]:
            self.assertNotIn("jobTagName", label)

    def test_welfare_parsing(self):
        """福利解析：jobWelfareCodeDataList→chineseTitle"""
        j = self.parse_one(make_51job_raw())
        self.assertIn("五险一金", j["benefits"])
        self.assertIn("带薪年假", j["benefits"])

    def test_company_info(self):
        """公司信息：行业/性质/规模"""
        j = self.parse_one(make_51job_raw())
        self.assertEqual(j["company_industry"], "测绘/地理信息")
        self.assertEqual(j["company_type"], "民营")
        self.assertEqual(j["company_size"], "100-500人")

    def test_extra_fields(self):
        """扩展字段：hr_name, publish_date, is_intern, 经纬度"""
        j = self.parse_one(make_51job_raw())
        self.assertEqual(j["hr_name"], "张经理")
        self.assertEqual(j["publish_date"], "2026-08-28 10:00:00")
        self.assertFalse(j["is_intern"])
        self.assertEqual(j["longitude"], 113.32)
        self.assertEqual(j["latitude"], 23.13)

    def test_dedupe(self):
        """去重：同公司同岗位只保留一个"""
        raw1 = make_51job_raw(job_id="id1")
        raw2 = make_51job_raw(job_id="id2")  # 同公司同岗位
        jobs = self.parse_51job([raw1, raw2])
        deduped = self.dedupe_51job(jobs)
        self.assertEqual(len(deduped), 1)

    def test_empty_input(self):
        """容错：空输入返回空列表"""
        self.assertEqual(self.parse_51job([]), [])
        self.assertEqual(self.parse_51job(None), [])

    def test_missing_fields(self):
        """容错：缺失字段不崩溃，返回空字符串"""
        raw = {"jobId": "x", "jobName": "测试岗", "fullCompanyName": "测试公司"}
        j = self.parse_one(raw)
        self.assertEqual(j["position"], "测试岗")
        self.assertEqual(j["company"], "测试公司")
        self.assertEqual(j["salary"], "")
        self.assertEqual(j["work_location"], "")
        self.assertFalse(j["has_detail"])

    def test_no_jd(self):
        """无JD时has_detail为False，responsibilities/requirements为空"""
        raw = make_51job_raw(with_jd=False)
        j = self.parse_one(raw)
        self.assertFalse(j["has_detail"])
        self.assertEqual(j["responsibilities"], "")
        self.assertEqual(j["requirements"], "")

    def test_full_company_name_fallback(self):
        """公司名：优先fullCompanyName，缺失时用companyName"""
        raw = make_51job_raw()
        del raw["fullCompanyName"]
        j = self.parse_one(raw)
        self.assertEqual(j["company"], "测试测绘")

    def test_city_extraction(self):
        """城市提取：广州·天河区→广州"""
        j = self.parse_one(make_51job_raw())
        self.assertEqual(j["city"], "广州")



if __name__ == '__main__':
    unittest.main(verbosity=2)


class TestLiepinParser(unittest.TestCase):
    """猎聘(liepin)解析器测试"""

    def _make_card(self, **kw):
        """构造猎聘岗位卡片"""
        card = {
            "comp": {"compName": "测试公司", "compId": 123, "compScale": "100-200人",
                     "compIndustry": "建筑/工程", "compLogo": "test.png",
                     "link": "https://www.liepin.com/company/123/"},
            "job": {"jobId": "88888", "title": "测绘工程师", "salary": "10-15k",
                    "dq": "广州-天河区", "labels": ["本科"], "campusJobKind": "应届",
                    "link": "https://www.liepin.com/lptjob/88888",
                    "refreshTime": "20260826153345", "jobKind": "6"},
            "recruiter": {"recruiterName": "张女士", "recruiterTitle": "HR经理",
                          "imShowText": "3天前在线"},
            "dataParams": "{}",
        }
        card.update(kw)
        return card

    def test_field_mapping(self):
        """基本字段映射"""
        from boss_api.parse_liepin_api import parse_one
        j = parse_one(self._make_card())
        self.assertIsNotNone(j)
        self.assertEqual(j["company"], "测试公司")
        self.assertEqual(j["position"], "测绘工程师")
        self.assertEqual(j["salary"], "10-15k")
        self.assertEqual(j["city"], "广州")
        self.assertEqual(j["work_location"], "广州-天河区")
        self.assertEqual(j["source"], "猎聘")
        self.assertEqual(j["encrypt_job_id"], "88888")
        self.assertEqual(j["job_url"], "https://www.liepin.com/lptjob/88888")

    def test_city_extraction(self):
        """城市提取：上海-杨浦区→上海"""
        from boss_api.parse_liepin_api import extract_city
        self.assertEqual(extract_city("上海-杨浦区"), "上海")
        self.assertEqual(extract_city("广州"), "广州")
        self.assertEqual(extract_city(""), "")

    def test_refresh_time_parsing(self):
        """刷新时间解析"""
        from boss_api.parse_liepin_api import parse_refresh_time
        self.assertEqual(parse_refresh_time("20260826153345"), "2026-08-26 15:33:45")
        self.assertEqual(parse_refresh_time(""), "")
        self.assertEqual(parse_refresh_time("123"), "")

    def test_labels_include_campus_kind(self):
        """校园招聘类型加入标签"""
        from boss_api.parse_liepin_api import parse_one
        j = parse_one(self._make_card())
        self.assertIn("本科", j["job_labels"])
        self.assertIn("应届", j["job_labels"])

    def test_company_info(self):
        """公司信息"""
        from boss_api.parse_liepin_api import parse_one
        j = parse_one(self._make_card())
        self.assertEqual(j["company_size"], "100-200人")
        self.assertEqual(j["company_industry"], "建筑/工程")
        self.assertEqual(j["company_link"], "https://www.liepin.com/company/123/")

    def test_hr_info(self):
        """HR信息"""
        from boss_api.parse_liepin_api import parse_one
        j = parse_one(self._make_card())
        self.assertEqual(j["hr_name"], "张女士")
        self.assertEqual(j["hr_title"], "HR经理")
        self.assertEqual(j["hr_online"], "3天前在线")

    def test_no_full_jd(self):
        """猎聘列表无完整JD"""
        from boss_api.parse_liepin_api import parse_one
        j = parse_one(self._make_card())
        self.assertFalse(j["has_detail"])
        self.assertEqual(j["responsibilities"], "")
        self.assertEqual(j["requirements"], "")
        self.assertIn("岗位名称：测绘工程师", j["detail_text"])

    def test_missing_title(self):
        """缺少标题返回None"""
        from boss_api.parse_liepin_api import parse_one
        card = self._make_card()
        card["job"]["title"] = ""
        self.assertIsNone(parse_one(card))

    def test_missing_company(self):
        """缺少公司返回None"""
        from boss_api.parse_liepin_api import parse_one
        card = self._make_card()
        card["comp"]["compName"] = ""
        self.assertIsNone(parse_one(card))

    def test_empty_input(self):
        """空输入"""
        from boss_api.parse_liepin_api import parse_liepin, dedupe_liepin
        self.assertEqual(parse_liepin([]), [])
        self.assertEqual(parse_liepin(None), [])
        self.assertEqual(dedupe_liepin([]), [])

    def test_parse_from_raw(self):
        """从liepin_raw原始响应解析"""
        from boss_api.parse_liepin_api import parse_liepin
        raw = [{
            "url": "https://api-c.liepin.com/api/com.liepin.searchfront4c.pc-search-job",
            "data": {"flag": 1, "data": {"data": {"jobCardList": [
                self._make_card(),
                self._make_card(job={"jobId": "99999", "title": "测量工程师",
                                       "salary": "8-12k", "dq": "深圳-南山区",
                                       "labels": ["本科"], "link": "https://www.liepin.com/lptjob/99999"}),
            ]}, "pagination": {"currentPage": 0}}},
            "time": "2026-08-30 21:00:00",
        }]
        jobs = parse_liepin(raw)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["position"], "测绘工程师")
        self.assertEqual(jobs[1]["position"], "测量工程师")

    def test_dedupe(self):
        """去重：同公司同岗位保留第一个"""
        from boss_api.parse_liepin_api import dedupe_liepin
        from boss_api.parse_liepin_api import parse_one
        j1 = parse_one(self._make_card())
        j2 = parse_one(self._make_card())  # 完全相同
        j3 = parse_one(self._make_card(job={"jobId": "77777", "title": "GIS工程师",
                                              "salary": "12-18k", "dq": "北京-朝阳区",
                                              "labels": ["硕士"], "link": "https://www.liepin.com/lptjob/77777"}))
        result = dedupe_liepin([j1, j2, j3])
        self.assertEqual(len(result), 2)

    def test_non_dict_card(self):
        """非字典卡片跳过"""
        from boss_api.parse_liepin_api import parse_one
        self.assertIsNone(parse_one("not a dict"))
        self.assertIsNone(parse_one(None))

    def test_skill_extraction(self):
        """技能标签提取"""
        from boss_api.parse_liepin_api import parse_one
        card = self._make_card(job={"jobId": "66666", "title": "GIS开发工程师",
                                      "salary": "15-25k", "dq": "杭州-西湖区",
                                      "labels": ["本科", "GIS", "Python"],
                                      "link": "https://www.liepin.com/lptjob/66666"})
        j = parse_one(card)
        self.assertIn("GIS", j["skills"])
        self.assertIn("Python", j["skills"])

