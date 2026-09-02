"""
数据验证工具 - 轻量级JSON Schema验证器
不依赖外部库，实现基本的Schema验证功能

使用方法：
    from utils.validator import validate_job, validate_resume, validate_match_result, validate_application

    # 验证单个岗位数据
    errors = validate_job(job_data)
    if errors:
        print("验证失败:", errors)
    else:
        print("验证通过")

    # 验证岗位库（批量）
    all_errors = validate_jobs_list(jobs_list)
"""

import os
import json
import re
from datetime import datetime

# Schema文件目录
SCHEMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas")


def load_schema(schema_name):
    """加载Schema文件"""
    schema_path = os.path.join(SCHEMAS_DIR, schema_name)
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema文件不存在: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_type(value, expected_type, path=""):
    """验证值的类型"""
    errors = []

    if expected_type == "string":
        if not isinstance(value, str):
            errors.append(f"{path}: 期望字符串，实际是 {type(value).__name__}")
    elif expected_type == "number":
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{path}: 期望数字，实际是 {type(value).__name__}")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{path}: 期望整数，实际是 {type(value).__name__}")
    elif expected_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{path}: 期望布尔值，实际是 {type(value).__name__}")
    elif expected_type == "array":
        if not isinstance(value, list):
            errors.append(f"{path}: 期望数组，实际是 {type(value).__name__}")
    elif expected_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{path}: 期望对象，实际是 {type(value).__name__}")
    elif expected_type == "null":
        if value is not None:
            errors.append(f"{path}: 期望null，实际是 {type(value).__name__}")

    return errors


def validate_string_format(value, fmt, path=""):
    """验证字符串格式"""
    errors = []

    if fmt == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            errors.append(f"{path}: 邮箱格式不正确: {value}")
    elif fmt == "date":
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            errors.append(f"{path}: 日期格式不正确（期望YYYY-MM-DD）: {value}")
    elif fmt == "date-time":
        try:
            # 支持多种ISO 8601格式
            for fmt_str in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]:
                try:
                    datetime.strptime(value, fmt_str)
                    break
                except ValueError:
                    continue
            else:
                errors.append(f"{path}: 日期时间格式不正确（期望ISO 8601）: {value}")
        except Exception:
            errors.append(f"{path}: 日期时间格式不正确: {value}")

    return errors


def validate_value(value, schema, path=""):
    """递归验证值是否符合Schema"""
    errors = []

    if not isinstance(schema, dict):
        return errors

    # 处理类型（支持多类型，如["number", "null"]）
    if "type" in schema:
        expected_types = schema["type"]
        if isinstance(expected_types, list):
            # 多类型：只要匹配其中一个即可
            type_matched = False
            for t in expected_types:
                if t == "string" and isinstance(value, str):
                    type_matched = True
                    break
                elif t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
                    type_matched = True
                    break
                elif t == "integer" and isinstance(value, int) and not isinstance(value, bool):
                    type_matched = True
                    break
                elif t == "boolean" and isinstance(value, bool):
                    type_matched = True
                    break
                elif t == "array" and isinstance(value, list):
                    type_matched = True
                    break
                elif t == "object" and isinstance(value, dict):
                    type_matched = True
                    break
                elif t == "null" and value is None:
                    type_matched = True
                    break
            if not type_matched:
                errors.append(f"{path}: 类型不匹配，期望 {expected_types}，实际是 {type(value).__name__}")
                return errors  # 类型不匹配，后续验证无意义
        else:
            type_errors = validate_type(value, expected_types, path)
            if type_errors:
                errors.extend(type_errors)
                return errors  # 类型不匹配，后续验证无意义

    # 如果值为null且允许null，跳过后续验证
    if value is None:
        return errors

    # 字符串验证
    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: 字符串长度不足，最小 {schema['minLength']}，实际 {len(value)}")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: 字符串长度超出，最大 {schema['maxLength']}，实际 {len(value)}")
        if "pattern" in schema and not re.match(schema["pattern"], value):
            errors.append(f"{path}: 字符串不匹配模式: {schema['pattern']}")
        if "format" in schema:
            errors.extend(validate_string_format(value, schema["format"], path))
        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{path}: 值不在枚举列表中，允许值: {schema['enum']}，实际: {value}")

    # 数字验证
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: 数值过小，最小 {schema['minimum']}，实际 {value}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: 数值过大，最大 {schema['maximum']}，实际 {value}")

    # 数组验证
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: 数组项数不足，最小 {schema['minItems']}，实际 {len(value)}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: 数组项数超出，最大 {schema['maxItems']}，实际 {len(value)}")
        if "uniqueItems" in schema and schema["uniqueItems"]:
            # 检查重复项
            seen = []
            for i, item in enumerate(value):
                if item in seen:
                    errors.append(f"{path}[{i}]: 数组项重复: {item}")
                else:
                    seen.append(item)
        if "items" in schema:
            for i, item in enumerate(value):
                errors.extend(validate_value(item, schema["items"], f"{path}[{i}]"))

    # 对象验证
    if isinstance(value, dict):
        # 检查必填字段
        if "required" in schema:
            for field in schema["required"]:
                if field not in value:
                    errors.append(f"{path}: 缺少必填字段: {field}")

        # 检查属性
        if "properties" in schema:
            for field, field_schema in schema["properties"].items():
                if field in value:
                    errors.extend(validate_value(value[field], field_schema, f"{path}.{field}"))

        # 检查patternProperties（先处理，用于additionalProperties判断）
        pattern_matched_fields = set()
        if "patternProperties" in schema:
            for pattern, prop_schema in schema["patternProperties"].items():
                for field, field_value in value.items():
                    if re.match(pattern, field):
                        pattern_matched_fields.add(field)
                        errors.extend(validate_value(field_value, prop_schema, f"{path}.{field}"))

        # 检查额外属性（排除properties和patternProperties匹配的字段）
        if "additionalProperties" in schema and schema["additionalProperties"] is False:
            allowed_fields = set(schema.get("properties", {}).keys())
            allowed_fields.update(pattern_matched_fields)
            for field in value.keys():
                if field not in allowed_fields:
                    errors.append(f"{path}: 不允许的额外字段: {field}")

    return errors


def validate_data(data, schema_name):
    """
    验证数据是否符合指定Schema

    Args:
        data: 要验证的数据
        schema_name: Schema文件名（如'job.json'、'resume.json'）

    Returns:
        list: 错误列表，空列表表示验证通过
    """
    try:
        schema = load_schema(schema_name)
        return validate_value(data, schema, "")
    except Exception as e:
        return [f"验证过程出错: {str(e)}"]


def validate_job(job_data):
    """验证单个岗位数据"""
    return validate_data(job_data, "job.json")


def validate_resume(resume_data):
    """验证简历数据"""
    return validate_data(resume_data, "resume.json")


def validate_match_result(match_data):
    """验证匹配度结果"""
    return validate_data(match_data, "match_result.json")


def validate_application(app_data):
    """验证申请记录"""
    return validate_data(app_data, "application.json")


def validate_jobs_list(jobs_list):
    """
    批量验证岗位列表

    Returns:
        dict: {岗位索引: 错误列表}
    """
    all_errors = {}
    for i, job in enumerate(jobs_list):
        errors = validate_job(job)
        if errors:
            all_errors[i] = errors
    return all_errors


def validate_applications_list(apps_list):
    """
    批量验证申请记录列表

    Returns:
        dict: {记录ID: 错误列表}
    """
    all_errors = {}
    for app in apps_list:
        errors = validate_application(app)
        if errors:
            app_id = app.get("id", "unknown")
            all_errors[app_id] = errors
    return all_errors


if __name__ == "__main__":
    # 测试验证工具
    import sys

    workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 60)
    print("数据验证工具测试")
    print("=" * 60)

    # 测试简历数据
    print("\n1. 验证简历数据...")
    resume_path = os.path.join(workspace, "resume_data.json")
    if os.path.exists(resume_path):
        with open(resume_path, "r", encoding="utf-8") as f:
            resume = json.load(f)
        errors = validate_resume(resume)
        if errors:
            print(f"   发现 {len(errors)} 个错误:")
            for e in errors[:10]:
                print(f"   - {e}")
        else:
            print("   验证通过 ✓")
    else:
        print("   简历数据文件不存在")

    # 测试岗位库
    print("\n2. 验证岗位库...")
    jobs_path = os.path.join(workspace, "jobs.json")
    if os.path.exists(jobs_path):
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        all_errors = validate_jobs_list(jobs)
        if all_errors:
            print(f"   发现 {len(all_errors)}/{len(jobs)} 个岗位有错误")
            # 统计错误类型
            error_types = {}
            for idx, errors in all_errors.items():
                for e in errors:
                    error_type = e.split(":")[0] if ":" in e else e
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            print("   错误类型统计:")
            for etype, count in sorted(error_types.items(), key=lambda x: -x[1])[:10]:
                print(f"   - {etype}: {count}次")
        else:
            print(f"   全部 {len(jobs)} 个岗位验证通过 ✓")
    else:
        print("   岗位库文件不存在")

    # 测试申请记录
    print("\n3. 验证申请记录...")
    apps_path = os.path.join(workspace, "applications", "applications.json")
    if os.path.exists(apps_path):
        with open(apps_path, "r", encoding="utf-8") as f:
            apps_data = json.load(f)
        apps_list = apps_data.get("applications", [])
        all_errors = validate_applications_list(apps_list)
        if all_errors:
            print(f"   发现 {len(all_errors)}/{len(apps_list)} 条记录有错误:")
            for app_id, errors in all_errors.items():
                print(f"   - ID {app_id}: {len(errors)} 个错误")
                for e in errors[:3]:
                    print(f"     * {e}")
        else:
            print(f"   全部 {len(apps_list)} 条记录验证通过 ✓")
    else:
        print("   申请记录文件不存在")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
