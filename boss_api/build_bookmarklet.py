# -*- coding: utf-8 -*-
"""
把 boss_bookmarklet_source.js 构建为：
1) javascript: 书签URL（写入 boss_bookmarklet.txt）
2) 可拖拽安装的网页 install_bookmarklet.html（把链接拖到收藏夹栏即完成安装）

只做安全的轻量处理：去注释、合并行、URL编码，不做激进压缩以避免破坏JS。
"""
import os
import re
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "boss_bookmarklet_source.js")
TXT = os.path.join(HERE, "boss_bookmarklet.txt")
HTML = os.path.join(HERE, "install_bookmarklet.html")


def build_bookmarklet(js: str) -> str:
    lines = []
    for raw in js.splitlines():
        # 去掉整行注释
        s = raw.strip()
        if s.startswith("//"):
            continue
        # 去掉行内 // 注释（简单处理，本源码行内没有URL中的//，安全）
        # 为稳妥只在出现 " //" 时截断
        m = re.search(r"\s//(?!/)", raw)
        if m:
            raw = raw[: m.start()]
        lines.append(raw.strip())
    code = " ".join(l for l in lines if l)
    code = re.sub(r"\s{2,}", " ", code)
    return "javascript:" + quote(code, encoding="utf-8")


def main():
    with open(SRC, "r", encoding="utf-8") as f:
        js = f.read()
    bm = build_bookmarklet(js)
    with open(TXT, "w", encoding="utf-8") as f:
        f.write(bm)

    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>安装 BOSS直聘岗位采集器 书签</title>
<style>
body{{font-family:"Microsoft YaHei",sans-serif;max-width:760px;margin:40px auto;padding:0 20px;color:#1f2328;line-height:1.8;}}
h1{{font-size:22px;}} .tip{{background:#fff8c5;border:1px solid #d4a72c;border-radius:8px;padding:12px 16px;margin:16px 0;}}
.bm{{display:inline-block;background:#0969da;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;cursor:grab;user-select:none;}}
.bm:active{{cursor:grabbing;}} code{{background:#f6f8fa;padding:2px 6px;border-radius:4px;}}
ol li{{margin:6px 0;}}
</style></head>
<body>
<h1>🎯 BOSS直聘岗位采集器 — 书签安装</h1>
<div class="tip">
<b>第一步：显示浏览器收藏夹栏</b><br>
Edge / Chrome 按 <code>Ctrl+Shift+B</code> 调出收藏夹栏。
</div>
<p><b>第二步：</b>把下面这个蓝色按钮 <b>拖到</b> 上方的收藏夹栏（或右键→添加到收藏夹）：</p>
<p><a class="bm" href="{bm}">采集BOSS岗位</a></p>
<div class="tip">
<b>使用方法：</b>
<ol>
<li>正常登录 BOSS直聘，搜索关键词、设置好城市/薪资等筛选；</li>
<li>在搜索结果页，点击收藏夹里的「采集BOSS岗位」；</li>
<li>右上角出现浮动面板，点「自动翻5页并采集」，或自己手动滚动/翻页（自动捕获）；</li>
<li>采集够了点「导出JSON」，得到一个 .json 文件，发给豆包即可生成匹配报告。</li>
</ol>
全程在你自己的浏览器里运行，不自动投递、不自动打招呼。
</div>
</body></html>""".format(bm=bm)

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("书签URL长度:", len(bm))
    print("已生成:")
    print(" -", TXT)
    print(" -", HTML)
    print("\n预览前120字符:\n", bm[:120], "...")


if __name__ == "__main__":
    main()
