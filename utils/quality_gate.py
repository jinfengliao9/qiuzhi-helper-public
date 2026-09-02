# -*- coding: utf-8 -*-
"""
质量门禁模块 - 自动验证和错误处理
确保每个步骤完成后自动检查，问题不传递到下一步

使用方法：
    from utils.quality_gate import QualityGate

    # 创建质量门禁实例
    qg = QualityGate()

    # 验证数据
    result = qg.validate_resume(resume_data)
    if result.passed:
        print("验证通过")
    else:
        print("验证失败:", result.errors)

    # 验证报告
    result = qg.validate_report(html_content)
    if result.passed:
        print("报告验证通过")
    else:
        print("报告验证失败:", result.errors)

    # 验证岗位数据
    result = qg.validate_job(job_data)
    if result.passed:
        print("岗位数据验证通过")
    else:
        print("岗位数据验证失败:", result.errors)
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加工作区目录到路径
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

# 导入验证工具
from utils.validator import validate_job, validate_resume, validate_match_result, validate_application


class ValidationResult:
    """验证结果类"""

    def __init__(self, passed: bool, errors: List[str] = None, warnings: List[str] = None,
                 info: Dict[str, Any] = None):
        self.passed = passed
        self.errors = errors or []
        self.warnings = warnings or []
        self.info = info or {}
        self.timestamp = datetime.now().isoformat()

    def __str__(self):
        status = "通过 ✓" if self.passed else "失败 ✗"
        result = f"[{status}]"
        if self.errors:
            result += f" 错误: {len(self.errors)}"
        if self.warnings:
            result += f" 警告: {len(self.warnings)}"
        return result

    def to_dict(self):
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "timestamp": self.timestamp
        }


class QualityGate:
    """质量门禁类 - 自动验证和错误处理"""

    def __init__(self, strict_mode: bool = False, log_enabled: bool = True):
        """
        初始化质量门禁

        Args:
            strict_mode: 严格模式（警告也视为失败）
            log_enabled: 是否启用日志记录
        """
        self.strict_mode = strict_mode
        self.log_enabled = log_enabled
        self.log_entries = []

    def _log(self, level: str, message: str, details: Dict[str, Any] = None):
        """记录日志"""
        if not self.log_enabled:
            return

        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {}
        }
        self.log_entries.append(entry)

    def _create_result(self, errors: List[str], warnings: List[str] = None,
                       info: Dict[str, Any] = None) -> ValidationResult:
        """创建验证结果"""
        passed = len(errors) == 0
        if self.strict_mode and warnings:
            passed = False

        return ValidationResult(passed, errors, warnings, info)

    # ============================================================
    # 数据验证门禁
    # ============================================================

    def validate_resume(self, resume_data: Dict) -> ValidationResult:
        """
        验证简历数据

        Args:
            resume_data: 简历数据

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {}

        # Schema验证
        schema_errors = validate_resume(resume_data)
        errors.extend(schema_errors)

        # 业务逻辑验证
        if not errors:
            # 检查基本信息完整性
            basic = resume_data.get("基本信息", {})
            required_fields = ["name", "phone", "email"]
            for field in required_fields:
                if not basic.get(field):
                    errors.append(f"基本信息缺少必填字段: {field}")

            # 检查邮箱格式
            email = basic.get("email", "")
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errors.append(f"邮箱格式不正确: {email}")

            # 检查电话格式
            phone = basic.get("phone", "")
            if phone and not re.match(r'^1[3-9]\d{9}$', phone):
                warnings.append(f"电话格式可能不正确: {phone}")

            # 检查是否有经历
            has_experience = bool(resume_data.get("实习经历") or resume_data.get("项目经历"))
            if not has_experience:
                warnings.append("简历没有实习经历或项目经历")

            # 检查技能清单
            skills = resume_data.get("技能清单", {})
            if not skills:
                warnings.append("简历没有技能清单")

            info["has_experience"] = has_experience
            info["skill_categories"] = len(skills)

        self._log("validate_resume", "简历数据验证", {"passed": len(errors) == 0, "errors": len(errors)})

        return self._create_result(errors, warnings, info)

    def validate_job(self, job_data: Dict) -> ValidationResult:
        """
        验证岗位数据

        Args:
            job_data: 岗位数据

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {}

        # Schema验证
        schema_errors = validate_job(job_data)
        errors.extend(schema_errors)

        # 业务逻辑验证
        if not errors:
            # 检查必填字段
            required_fields = ["company", "position", "source", "job_url"]
            for field in required_fields:
                if not job_data.get(field):
                    errors.append(f"岗位数据缺少必填字段: {field}")

            # 检查公司链接
            company_link = job_data.get("company_link", "")
            if company_link and company_link == "#":
                warnings.append("公司链接为#，可能无法访问")

            # 检查岗位URL有效性
            job_url = job_data.get("job_url", "")
            if job_url and not job_url.startswith("http"):
                warnings.append(f"岗位URL可能无效: {job_url}")

            # 检查匹配度
            match_score = job_data.get("match_score")
            if match_score is not None and (match_score < 0 or match_score > 100):
                errors.append(f"匹配度超出范围: {match_score}")

            info["has_match_score"] = match_score is not None
            info["has_responsibilities"] = bool(job_data.get("responsibilities"))
            info["has_requirements"] = bool(job_data.get("requirements"))

        self._log("validate_job", "岗位数据验证", {"passed": len(errors) == 0, "errors": len(errors)})

        return self._create_result(errors, warnings, info)

    def validate_jobs_list(self, jobs_list: List[Dict]) -> ValidationResult:
        """
        批量验证岗位列表

        Args:
            jobs_list: 岗位列表

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {"total": len(jobs_list), "valid": 0, "invalid": 0}

        invalid_jobs = []
        for i, job in enumerate(jobs_list):
            result = self.validate_job(job)
            if result.passed:
                info["valid"] += 1
            else:
                info["invalid"] += 1
                invalid_jobs.append({"index": i, "company": job.get("company", "未知"),
                                      "position": job.get("position", "未知"), "errors": result.errors})

        if invalid_jobs:
            errors.append(f"有 {len(invalid_jobs)}/{len(jobs_list)} 个岗位验证失败")
            for job in invalid_jobs[:5]:
                errors.append(f"  - 岗位 {job['index']}: {job['company']} - {job['position']}: {job['errors'][0] if job['errors'] else '未知错误'}")

        # 检查重复岗位
        seen = set()
        duplicates = []
        for job in jobs_list:
            key = f"{job.get('company', '')}_{job.get('position', '')}"
            if key in seen:
                duplicates.append(key)
            else:
                seen.add(key)

        if duplicates:
            warnings.append(f"发现 {len(duplicates)} 个重复岗位")

        info["duplicates"] = len(duplicates)

        self._log("validate_jobs_list", "岗位列表批量验证",
                   {"total": len(jobs_list), "valid": info["valid"], "invalid": info["invalid"]})

        return self._create_result(errors, warnings, info)

    def validate_application(self, app_data: Dict) -> ValidationResult:
        """
        验证申请记录

        Args:
            app_data: 申请记录

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []

        # Schema验证
        schema_errors = validate_application(app_data)
        errors.extend(schema_errors)

        # 业务逻辑验证
        if not errors:
            # 检查状态变更历史
            history = app_data.get("history", [])
            if not history:
                warnings.append("申请记录没有状态变更历史")

            # 检查日期格式
            apply_date = app_data.get("apply_date", "")
            if apply_date:
                try:
                    datetime.strptime(apply_date, "%Y-%m-%d")
                except ValueError:
                    errors.append(f"申请日期格式不正确: {apply_date}")

        self._log("validate_application", "申请记录验证", {"passed": len(errors) == 0})

        return self._create_result(errors, warnings)

    # ============================================================
    # 报告验证门禁
    # ============================================================

    def validate_report(self, html_content: str) -> ValidationResult:
        """
        验证HTML报告

        Args:
            html_content: HTML内容

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {}

        if not html_content:
            errors.append("报告内容为空")
            return self._create_result(errors, warnings, info)

        # 检查HTML基本结构
        if "<!DOCTYPE html>" not in html_content and "<html" not in html_content:
            errors.append("报告缺少HTML基本结构")

        if "</html>" not in html_content:
            errors.append("报告缺少</html>结束标签")

        # 检查标题
        if "<title>" not in html_content:
            warnings.append("报告没有标题")

        # 检查样式
        if "<style>" not in html_content and 'class=' not in html_content:
            warnings.append("报告可能没有样式")

        # 检查链接
        links = re.findall(r'href="([^"]*)"', html_content)
        info["total_links"] = len(links)

        invalid_links = []
        for link in links:
            if link == "#" or link == "":
                invalid_links.append(link)
            elif not link.startswith("http") and not link.startswith("#") and not link.startswith("mailto:"):
                warnings.append(f"链接可能无效: {link}")

        if invalid_links:
            errors.append(f"发现 {len(invalid_links)} 个无效链接（#或空）")

        # 检查岗位卡片数量
        job_cards = re.findall(r'class="job-card"', html_content)
        info["job_cards"] = len(job_cards)

        if job_cards:
            # 检查每个岗位卡片是否有匹配度
            score_circles = re.findall(r'class="score-circle', html_content)
            if len(score_circles) < len(job_cards):
                warnings.append(f"有 {len(job_cards) - len(score_cards)} 个岗位卡片缺少匹配度")

        # 检查是否有查看岗位按钮
        view_buttons = re.findall(r'>查看岗位<', html_content)
        info["view_buttons"] = len(view_buttons)

        # 检查是否有搜索公司按钮
        search_buttons = re.findall(r'>搜索公司<', html_content)
        info["search_buttons"] = len(search_buttons)

        self._log("validate_report", "报告验证",
                   {"passed": len(errors) == 0, "job_cards": info.get("job_cards", 0)})

        return self._create_result(errors, warnings, info)

    def validate_report_file(self, filepath: str) -> ValidationResult:
        """
        验证报告文件

        Args:
            filepath: 报告文件路径

        Returns:
            ValidationResult: 验证结果
        """
        if not os.path.exists(filepath):
            return self._create_result([f"报告文件不存在: {filepath}"])

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.validate_report(content)
        except Exception as e:
            return self._create_result([f"读取报告文件失败: {str(e)}"])

    # ============================================================
    # 简历生成门禁
    # ============================================================

    def validate_resume_html(self, html_content: str) -> ValidationResult:
        """
        验证简历HTML

        Args:
            html_content: HTML内容

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {}

        if not html_content:
            errors.append("简历内容为空")
            return self._create_result(errors, warnings, info)

        # 检查HTML基本结构
        if "<!DOCTYPE html>" not in html_content and "<html" not in html_content:
            errors.append("简历缺少HTML基本结构")

        # 检查关键内容
        key_sections = ["教育", "经历", "技能"]
        found_sections = []
        for section in key_sections:
            if section in html_content:
                found_sections.append(section)

        info["found_sections"] = found_sections

        if len(found_sections) < 2:
            warnings.append(f"简历可能缺少关键部分，只找到: {found_sections}")

        # 检查联系方式
        has_phone = bool(re.search(r'1[3-9]\d{9}', html_content))
        has_email = bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_content))

        info["has_phone"] = has_phone
        info["has_email"] = has_email

        if not has_phone:
            warnings.append("简历可能没有电话号码")
        if not has_email:
            warnings.append("简历可能没有邮箱地址")

        self._log("validate_resume_html", "简历HTML验证", {"passed": len(errors) == 0})

        return self._create_result(errors, warnings, info)

    # ============================================================
    # 配置验证门禁
    # ============================================================

    def validate_config(self, config: Dict) -> ValidationResult:
        """
        验证配置

        Args:
            config: 配置字典

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        info = {}

        # 检查必要的section
        required_sections = ["general", "paths", "scraper", "platforms", "matching", "report", "resume"]
        missing_sections = [s for s in required_sections if s not in config]

        if missing_sections:
            errors.append(f"配置缺少必要的section: {missing_sections}")

        # 检查匹配权重
        if "matching" in config:
            weights = config["matching"].get("weights", {})
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                errors.append(f"匹配权重总和应为1.0，当前为{total_weight}")
            info["total_weight"] = total_weight

        # 检查平台配置
        if "platforms" in config:
            enabled_platforms = []
            for name, platform in config["platforms"].items():
                if platform.get("enabled", True):
                    enabled_platforms.append(name)
                    if "search_url" not in platform:
                        warnings.append(f"平台{name}缺少search_url配置")
            info["enabled_platforms"] = enabled_platforms

        self._log("validate_config", "配置验证", {"passed": len(errors) == 0})

        return self._create_result(errors, warnings, info)

    # ============================================================
    # 综合质量门禁
    # ============================================================

    def run_full_quality_check(self, workspace_dir: str = None) -> Dict[str, ValidationResult]:
        """
        运行完整的质量检查

        Args:
            workspace_dir: 工作区目录

        Returns:
            dict: 各模块的验证结果
        """
        if workspace_dir is None:
            workspace_dir = WORKSPACE_DIR

        results = {}

        # 验证简历数据
        resume_path = os.path.join(workspace_dir, "resume_data.json")
        if os.path.exists(resume_path):
            try:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                results["resume_data"] = self.validate_resume(resume_data)
            except Exception as e:
                results["resume_data"] = self._create_result([f"加载简历数据失败: {str(e)}"])

        # 验证岗位库
        jobs_path = os.path.join(workspace_dir, "jobs.json")
        if os.path.exists(jobs_path):
            try:
                with open(jobs_path, 'r', encoding='utf-8') as f:
                    jobs_data = json.load(f)
                results["jobs_db"] = self.validate_jobs_list(jobs_data)
            except Exception as e:
                results["jobs_db"] = self._create_result([f"加载岗位库失败: {str(e)}"])

        # 验证申请记录
        apps_path = os.path.join(workspace_dir, "applications", "applications.json")
        if os.path.exists(apps_path):
            try:
                with open(apps_path, 'r', encoding='utf-8') as f:
                    apps_data = json.load(f)
                apps_list = apps_data.get("applications", [])
                if apps_list:
                    results["applications"] = self._create_result(
                        [], [], {"total": len(apps_list)}
                    )
            except Exception as e:
                results["applications"] = self._create_result([f"加载申请记录失败: {str(e)}"])

        # 验证配置
        config_path = os.path.join(workspace_dir, "config.yaml")
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                results["config"] = self.validate_config(config_data)
            except Exception as e:
                results["config"] = self._create_result([f"加载配置失败: {str(e)}"])

        return results

    def print_results(self, results: Dict[str, ValidationResult]):
        """打印验证结果"""
        print("=" * 60)
        print("  质量门禁 - 完整质量检查结果")
        print("=" * 60)
        print()

        total_passed = 0
        total_failed = 0
        total_warnings = 0

        for module, result in results.items():
            status = "通过 ✓" if result.passed else "失败 ✗"
            print(f"[{status}] {module}")

            if result.errors:
                total_failed += 1
                for error in result.errors[:3]:
                    print(f"  ✗ 错误: {error}")
                if len(result.errors) > 3:
                    print(f"  ... 还有 {len(result.errors) - 3} 个错误")
            else:
                total_passed += 1

            if result.warnings:
                total_warnings += len(result.warnings)
                for warning in result.warnings[:2]:
                    print(f"  ! 警告: {warning}")
                if len(result.warnings) > 2:
                    print(f"  ... 还有 {len(result.warnings) - 2} 个警告")

            print()

        print("=" * 60)
        print(f"  总计: {total_passed} 通过, {total_failed} 失败, {total_warnings} 警告")
        print("=" * 60)

        return total_failed == 0


# ============================================================
# 便捷函数
# ============================================================

def quick_quality_check(workspace_dir: str = None) -> bool:
    """
    快速质量检查

    Args:
        workspace_dir: 工作区目录

    Returns:
        bool: 是否全部通过
    """
    qg = QualityGate()
    results = qg.run_full_quality_check(workspace_dir)
    return qg.print_results(results)


if __name__ == '__main__':
    # 测试质量门禁
    print("质量门禁模块测试")
    print()

    # 运行完整质量检查
    success = quick_quality_check()

    print()
    if success:
        print("所有质量检查通过！")
    else:
        print("部分质量检查未通过，请检查上述问题")
