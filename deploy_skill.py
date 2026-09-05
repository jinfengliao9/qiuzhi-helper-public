# -*- coding: utf-8 -*-
"""
部署同步脚本：把工作区的 SKILL.md 同步到已安装的 skill 目录。

每次修改 SKILL.md 后必须运行本脚本，否则豆包下次启动时读到的还是旧版。

用法：
    python deploy_skill.py

功能：
    1. 检查源文件（工作区 SKILL.md）存在
    2. 检查目标目录（已安装 skill 目录）存在
    3. 复制 SKILL.md 到目标目录
    4. 用 SHA256 哈希验证复制成功
    5. 输出成功/失败信息
"""
import os
import sys
import hashlib
import shutil


def get_paths():
    """计算源文件和目标文件的绝对路径。"""
    # 脚本所在目录就是工作区根目录
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(workspace_dir, "SKILL.md")

    # 已安装 skill 目录（豆包用户级 skill 路径）
    target_dir = os.path.join(
        os.environ.get("USERPROFILE", ""),
        "AppData", "Local", "Doubao", "User Data", "Default",
        ".doubao", "agent_mode", "workspace", ".user_skills",
        "job-search-assistant"
    )
    target = os.path.join(target_dir, "SKILL.md")
    return source, target, target_dir


def sha256_file(path):
    """计算文件的 SHA256 哈希。"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    source, target, target_dir = get_paths()

    print("=" * 60)
    print("SKILL.md 部署同步")
    print("=" * 60)

    # 1. 检查源文件
    if not os.path.isfile(source):
        print(f"[错误] 源文件不存在: {source}")
        print("       请确认本脚本放在 job-search-workspace/ 目录下。")
        sys.exit(1)

    source_size = os.path.getsize(source)
    source_hash = sha256_file(source)
    print(f"[源文件] {source}")
    print(f"         大小: {source_size:,} 字节")
    print(f"         SHA256: {source_hash[:16]}...")

    # 2. 检查目标目录
    if not os.path.isdir(target_dir):
        print(f"\n[错误] 目标目录不存在: {target_dir}")
        print("       请先在豆包中安装 job-search-assistant skill。")
        print("       如果已安装但路径不同，请检查豆包的用户级 skill 目录位置。")
        sys.exit(1)

    # 3. 检查目标文件是否已存在（用于对比）
    target_exists = os.path.isfile(target)
    if target_exists:
        target_hash_old = sha256_file(target)
        if target_hash_old == source_hash:
            print(f"\n[跳过] 目标文件与源文件哈希一致，无需同步。")
            print(f"       目标: {target}")
            print("=" * 60)
            sys.exit(0)
        print(f"\n[目标] 已有文件，将被覆盖（哈希不同，检测到更新）")
    else:
        print(f"\n[目标] 文件不存在，将新建")

    print(f"       路径: {target}")

    # 4. 复制文件
    try:
        shutil.copy2(source, target)
    except Exception as e:
        print(f"\n[错误] 复制失败: {e}")
        sys.exit(1)

    # 5. 验证复制结果
    if not os.path.isfile(target):
        print(f"\n[错误] 复制后目标文件不存在: {target}")
        sys.exit(1)

    target_size = os.path.getsize(target)
    target_hash = sha256_file(target)

    if target_hash != source_hash:
        print(f"\n[错误] 复制后哈希不一致！")
        print(f"       源文件哈希: {source_hash}")
        print(f"       目标哈希:   {target_hash}")
        sys.exit(1)

    # 6. 成功
    print(f"\n[成功] SKILL.md 已同步到部署目录")
    print(f"       大小: {target_size:,} 字节（一致）")
    print(f"       SHA256: {target_hash[:16]}...（一致）")
    print(f"       豆包下次启动时将读取新版 SKILL.md。")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
