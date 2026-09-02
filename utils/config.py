"""
配置加载工具 - 统一加载和访问config.yaml配置

使用方法：
    from utils.config import get_config, get_scraper_config, get_matching_config

    # 获取完整配置
    config = get_config()

    # 获取特定配置
    scraper_config = get_scraper_config()
    matching_config = get_matching_config()
    report_config = get_report_config()
    resume_config = get_resume_config()

    # 获取平台配置
    zhaopin_config = get_platform_config("zhaopin")
"""

import os
import yaml
import copy
from datetime import datetime


# 全局配置缓存
_config_cache = None
_config_path = None
_config_mtime = None


def get_workspace_dir():
    """获取工作区目录（自动检测）"""
    # 优先使用环境变量
    env_dir = os.environ.get("JOB_SEARCH_WORKSPACE")
    if env_dir and os.path.exists(env_dir):
        return env_dir

    # 自动检测：从当前文件路径向上查找
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        if os.path.exists(os.path.join(current_dir, "config.yaml")):
            return current_dir
        current_dir = os.path.dirname(current_dir)

    # 回退到当前工作目录
    return os.getcwd()


def get_config_path():
    """获取配置文件路径"""
    global _config_path
    if _config_path:
        return _config_path

    workspace = get_workspace_dir()
    _config_path = os.path.join(workspace, "config.yaml")
    return _config_path


def load_config(force_reload=False):
    """
    加载配置文件

    Args:
        force_reload: 是否强制重新加载（忽略缓存）

    Returns:
        dict: 配置字典
    """
    global _config_cache, _config_mtime

    config_path = get_config_path()

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    # 检查文件修改时间，决定是否需要重新加载
    current_mtime = os.path.getmtime(config_path)
    if not force_reload and _config_cache is not None and _config_mtime == current_mtime:
        return _config_cache

    # 加载配置
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 自动填充工作区目录
    if not config.get("general", {}).get("workspace_dir"):
        config["general"]["workspace_dir"] = get_workspace_dir()

    # 缓存配置
    _config_cache = config
    _config_mtime = current_mtime

    return config


def get_config():
    """获取完整配置（带缓存）"""
    return load_config()


def get_section(section_name):
    """
    获取配置的某个 section

    Args:
        section_name: section名称（如'scraper'、'matching'）

    Returns:
        dict: section配置
    """
    config = get_config()
    if section_name not in config:
        raise KeyError(f"配置section不存在: {section_name}")
    return config[section_name]


def get_general_config():
    """获取通用配置"""
    return get_section("general")


def get_paths_config():
    """获取路径配置"""
    return get_section("paths")


def get_scraper_config():
    """获取抓取配置"""
    return get_section("scraper")


def get_platforms_config():
    """获取所有平台配置"""
    return get_section("platforms")


def get_platform_config(platform_name):
    """
    获取特定平台配置

    Args:
        platform_name: 平台名称（如'zhaopin'、'boss'）

    Returns:
        dict: 平台配置
    """
    platforms = get_platforms_config()
    if platform_name not in platforms:
        raise KeyError(f"平台配置不存在: {platform_name}")
    return platforms[platform_name]


def get_enabled_platforms():
    """获取已启用的平台列表"""
    platforms = get_platforms_config()
    enabled = []
    for name, config in platforms.items():
        if config.get("enabled", True):  # 默认启用
            enabled.append(name)
    return enabled


def get_matching_config():
    """获取匹配引擎配置"""
    return get_section("matching")


def get_report_config():
    """获取报告配置"""
    return get_section("report")


def get_resume_config():
    """获取简历配置"""
    return get_section("resume")


def get_interview_config():
    """获取面试配置"""
    return get_section("interview")


def get_validation_config():
    """获取数据验证配置"""
    return get_section("validation")


def get_version_config():
    """获取版本配置"""
    return get_section("version")


def get_path(key, absolute=True):
    """
    获取配置中的路径

    Args:
        key: 路径键名（如'resume_data'、'jobs_db'）
        absolute: 是否返回绝对路径

    Returns:
        str: 路径
    """
    paths = get_paths_config()
    if key not in paths:
        raise KeyError(f"路径配置不存在: {key}")

    path = paths[key]
    if absolute and not os.path.isabs(path):
        workspace = get_workspace_dir()
        path = os.path.join(workspace, path)

    return path


def validate_config():
    """
    验证配置文件的完整性和正确性

    Returns:
        tuple: (is_valid, errors)
            is_valid: bool，是否验证通过
            errors: list，错误列表
    """
    errors = []

    try:
        config = get_config()
    except Exception as e:
        return False, [f"配置加载失败: {str(e)}"]

    # 检查必要的section
    required_sections = ["general", "paths", "scraper", "platforms", "matching", "report", "resume"]
    for section in required_sections:
        if section not in config:
            errors.append(f"缺少必要的section: {section}")

    # 检查匹配权重总和
    if "matching" in config:
        weights = config["matching"].get("weights", {})
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"匹配权重总和应为1.0，当前为{total_weight}")

    # 检查平台配置
    if "platforms" in config:
        for name, platform in config["platforms"].items():
            if platform.get("enabled", True):
                if "search_url" not in platform:
                    errors.append(f"平台{name}缺少search_url配置")

    # 检查路径配置
    if "paths" in config:
        required_paths = ["resume_data", "jobs_db", "applications"]
        for path_key in required_paths:
            if path_key not in config["paths"]:
                errors.append(f"缺少必要的路径配置: {path_key}")

    is_valid = len(errors) == 0
    return is_valid, errors


def print_config_summary():
    """打印配置摘要"""
    config = get_config()

    print("=" * 60)
    print("求职工作区配置摘要")
    print("=" * 60)

    # 版本信息
    version = config.get("version", {})
    print(f"\n配置版本: {version.get('config_version', '未知')}")
    print(f"最后更新: {version.get('last_updated', '未知')}")

    # 工作区
    general = config.get("general", {})
    print(f"\n工作区目录: {general.get('workspace_dir', '未设置')}")

    # 抓取配置
    scraper = config.get("scraper", {})
    print(f"\n抓取配置:")
    print(f"  默认平台: {scraper.get('default_platform', '未设置')}")
    print(f"  默认数量: {scraper.get('default_count', '未设置')}")
    print(f"  详情间隔: {scraper.get('detail_interval', '未设置')}秒")

    # 已启用平台
    enabled = get_enabled_platforms()
    print(f"\n已启用平台: {', '.join(enabled)}")

    # 匹配配置
    matching = config.get("matching", {})
    weights = matching.get("weights", {})
    print(f"\n匹配权重:")
    for key, value in weights.items():
        print(f"  {key}: {value}")

    # 简历模板
    resume = config.get("resume", {})
    templates = resume.get("templates", [])
    enabled_templates = [t["name"] for t in templates if t.get("enabled", True)]
    print(f"\n已启用简历模板: {', '.join(enabled_templates)}")

    # 验证配置
    is_valid, errors = validate_config()
    print(f"\n配置验证: {'通过 ✓' if is_valid else '失败 ✗'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 测试配置加载
    print_config_summary()
