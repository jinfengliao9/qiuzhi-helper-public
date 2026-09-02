# -*- coding: utf-8 -*-
"""
求职助手 · 统一报告主题（唯一视觉标准 / Single Source of Truth）
================================================================
所有 HTML 报告共用本主题，保证视觉一致：
  - 网申雷达：radar_report.py / radar_merged_report.py
  - 岗位采集独立报告：report_generator.py（job_search.py collect → make_standalone_report）
  - 岗位库推荐报告：job_pipeline.py

设计基准（用户已确认）：网申雷达报告风格
  主色 #2c5f8a，蓝色渐变圆角头部 + 独立统计卡（grid）+ 白色岗位卡（微阴影）
  + 左侧蓝色序号块 + 右侧描边匹配分 + 灰底 meta 标签 + 三按钮（查看岗位/查看公司/展开JD）

对外只暴露纯函数，返回 HTML 字符串，不读写文件、不依赖其它业务模块。
注意：THEME_CSS 是普通字符串常量，内部花括号是原生 CSS，禁止对其调用 str.format。
"""

import html as _html

PRIMARY = "#2c5f8a"
PRIMARY_DARK = "#1a4a75"
PRIMARY_GRAD = "linear-gradient(135deg, #2c5f8a, #3a7bd5)"

# ---------------------------------------------------------------- 基础工具
def esc(v):
    """HTML 转义，None/空安全。"""
    if v is None:
        return ""
    return _html.escape(str(v))


# ---------------------------------------------------------------- 平台配色
# (浅底色, 文字色)
SOURCE_STYLE = {
    "智联招聘": ("#e6f7ff", "#1890ff"),
    "BOSS直聘": ("#fff3e0", "#e65100"),
    "前程无忧": ("#e8f5e9", "#2e7d32"),
    "猎聘": ("#f3e5f5", "#7b1fa2"),
    "国聘网": ("#e6f0ff", "#2c5f8a"),
    "牛客": ("#f0f5ff", "#2f54eb"),
}


def source_badge(source):
    """平台来源小胶囊。"""
    if not source:
        return ""
    bg, fg = SOURCE_STYLE.get(source, ("#f0f0f0", "#666"))
    return f'<span class="src-badge" style="background:{bg};color:{fg}">{esc(source)}</span>'


def tag_badge(text, kind="blue"):
    """通用小徽标（国企/校招/网申中等）。kind: green/red/blue/orange"""
    color_map = {
        "green": ("#f6ffed", "#52c41a"),
        "red": ("#fff1f0", "#ff4d4f"),
        "blue": ("#e6f7ff", "#1890ff"),
        "orange": ("#fff7e6", "#fa8c16"),
    }
    bg, fg = color_map.get(kind, color_map["blue"])
    return f'<span class="mini-badge" style="background:{bg};color:{fg}">{esc(text)}</span>'


# ---------------------------------------------------------------- 匹配分
def score_bucket(score):
    """返回 (等级文案, 颜色)。口径与网申雷达一致。"""
    try:
        s = float(score)
    except (TypeError, ValueError):
        s = 0
    if s >= 80:
        return "高度匹配", "#52c41a"
    if s >= 65:
        return "较匹配", "#faad14"
    if s >= 50:
        return "一般", "#fa8c16"
    return "匹配较低", "#ff4d4f"


# ---------------------------------------------------------------- 统一 CSS
THEME_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Microsoft YaHei','PingFang SC','Segoe UI',Arial,sans-serif; background:#f5f7fa; color:#333; padding:20px; line-height:1.6; }
.container { max-width:1100px; margin:0 auto; }

/* 头部 */
.report-header { background:linear-gradient(135deg,#2c5f8a,#3a7bd5); color:#fff; padding:24px; border-radius:12px; margin-bottom:20px; }
.report-header h1 { font-size:22px; margin-bottom:8px; font-weight:600; }
.report-header .subtitle { font-size:13px; opacity:.92; line-height:1.7; }

/* 统计卡 */
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:12px; margin-bottom:20px; }
.stat-card { background:#fff; padding:14px; border-radius:10px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.stat-num { font-size:24px; font-weight:700; color:#2c5f8a; }
.stat-label { font-size:11px; color:#888; margin-top:4px; }

/* 区块标题 */
.section-title { font-size:18px; font-weight:700; color:#2c5f8a; margin:24px 0 12px; padding-left:12px; border-left:4px solid #2c5f8a; }
.section-desc { font-size:12px; color:#888; margin-bottom:12px; }

/* 筛选栏 */
.filter-bar { background:#fff; padding:12px 16px; border-radius:10px; margin-bottom:16px; display:flex; gap:14px; flex-wrap:wrap; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,.05); }
.filter-bar .filter-title { font-weight:600; color:#333; font-size:13px; }
.filter-bar label { font-size:13px; color:#666; cursor:pointer; display:flex; align-items:center; gap:4px; }

/* 提示条 */
.notice { background:#fffbe6; border-left:4px solid #faad14; padding:10px 14px; border-radius:6px; margin-bottom:16px; font-size:12.5px; color:#874d00; line-height:1.7; }

/* 岗位卡片 */
.job-card { background:#fff; border-radius:12px; padding:16px 18px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,.06); transition:box-shadow .2s; }
.job-card:hover { box-shadow:0 4px 16px rgba(0,0,0,.10); }
.job-header { display:flex; align-items:flex-start; gap:12px; margin-bottom:8px; }
.job-rank { width:28px; height:28px; background:#2c5f8a; color:#fff; border-radius:6px; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:13px; flex-shrink:0; }
.job-title-area { flex:1; min-width:0; }
.job-title { font-size:15px; font-weight:600; color:#1a1a1a; margin-bottom:4px; line-height:1.4; }
.job-company { display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-size:13px; color:#555; }
.company-name { color:#555; }
.header-badges { display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin-left:8px; }
.src-badge, .mini-badge { padding:2px 8px; border-radius:10px; font-size:11px; font-weight:500; white-space:nowrap; }
.job-score { width:66px; text-align:center; border:2px solid; border-radius:10px; padding:4px 0; flex-shrink:0; }
.score-num { font-size:20px; font-weight:700; line-height:1.1; }
.score-label { font-size:10px; color:#888; }
.score-level { font-size:10px; margin-top:1px; }

/* meta 标签 */
.job-meta { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0; }
.meta-item { font-size:12px; color:#666; background:#f5f7fa; padding:3px 9px; border-radius:4px; }
.meta-item.is-salary { background:#f6ffed; color:#389e0d; font-weight:500; }
.meta-item.is-company { background:#e6f7ff; color:#1890ff; font-weight:500; }

/* 推荐理由 / 建议 */
.job-reasons { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:6px; }
.reason-tag { font-size:11px; padding:2px 8px; border-radius:10px; background:#f0f5ff; color:#2c5f8a; }
.company-type { font-size:11px; background:#e6f7ff; color:#1890ff; padding:2px 6px; border-radius:4px; white-space:nowrap; }
.campus-badge { font-size:11px; background:#f6ffed; color:#52c41a; padding:2px 6px; border-radius:4px; white-space:nowrap; }
.recommend-line { font-size:12.5px; padding:8px 12px; background:#f8fafc; border-radius:6px; margin:6px 0 8px; color:#555; }

/* 五维评分（岗位报告用，紧凑） */
.dimensions { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; margin:8px 0; padding:10px 12px; background:#fafbfc; border-radius:8px; }
.dimension { min-width:0; }
.dim-top { display:flex; justify-content:space-between; font-size:11px; color:#888; margin-bottom:3px; }
.dim-score { font-weight:700; color:#2c5f8a; }
.dim-bar { height:4px; background:#e8eaed; border-radius:2px; overflow:hidden; }
.dim-fill { height:100%; border-radius:2px; background:#3a7bd5; }

/* 技能标签 */
.job-skills { display:flex; align-items:center; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
.skills-label, .cat-label { font-size:12px; color:#888; }
.skill-tag { font-size:11px; padding:2px 8px; border-radius:10px; background:#fff7e6; color:#fa8c16; margin:1px; }
.skill-tag.matched { background:#e8f8f0; color:#27ae60; }
.skill-tag.missing { background:#fdedec; color:#e74c3c; }
.no-skill, .text-muted { font-size:11px; color:#bbb; }

/* 按钮 */
.job-actions, .company-actions { display:flex; gap:8px; flex-wrap:wrap; }
.btn { padding:5px 14px; border-radius:6px; font-size:12px; text-decoration:none; cursor:pointer; border:none; display:inline-block; }
.btn-primary { background:#2c5f8a; color:#fff; }
.btn-primary:hover { background:#1a4a75; }
.btn-secondary { background:#f0f0f0; color:#555; }
.btn-secondary:hover { background:#e2e2e2; }
.btn-toggle { background:#fff; color:#2c5f8a; border:1px solid #2c5f8a; }
.btn-toggle:hover { background:#f0f5ff; }
.no-link { font-size:12px; color:#ccc; }

/* JD 折叠区 */
.job-jd-detail { margin-top:10px; padding-top:10px; border-top:1px solid #eee; }
.jd-section { margin-bottom:10px; }
.jd-title { font-size:12.5px; font-weight:600; color:#2c5f8a; margin-bottom:4px; }
.jd-content { font-size:12px; color:#666; line-height:1.7; white-space:pre-wrap; max-height:280px; overflow-y:auto; background:#fafafa; padding:9px 11px; border-radius:6px; word-break:break-word; }
.jd-full { font-size:11px; color:#888; }

/* 公司卡片（雷达板块二） */
.company-card { background:#fff; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 2px 8px rgba(0,0,0,.06); }
.company-header { display:flex; align-items:flex-start; gap:12px; }
.company-info { flex:1; min-width:0; }
.company-name { font-size:14px; font-weight:600; color:#1a1a1a; }
.company-meta { display:flex; flex-wrap:wrap; gap:8px; margin-top:6px; }
.company-categories { margin:8px 0; }
.cat-text { font-size:12px; color:#555; }
.active-badge { font-size:11px; background:#f6ffed; color:#52c41a; padding:2px 6px; border-radius:4px; }
.inactive-badge { font-size:11px; background:#fff1f0; color:#ff4d4f; padding:2px 6px; border-radius:4px; }

.report-footer { text-align:center; padding:20px; color:#aaa; font-size:12px; line-height:1.8; }

@media (max-width:600px) {
  body { padding:12px; }
  .job-header { flex-wrap:wrap; }
  .job-score { width:58px; }
  .stats-grid { grid-template-columns:repeat(auto-fit,minmax(96px,1fr)); }
}
"""


# ---------------------------------------------------------------- 组件
def stat_grid(stats):
    """统计卡区。stats: [(数字, 标签, 可选颜色)]"""
    cards = []
    for item in stats:
        num, label = item[0], item[1]
        color = item[2] if len(item) > 2 and item[2] else PRIMARY
        cards.append(
            f'<div class="stat-card"><div class="stat-num" style="color:{color}">{num}</div>'
            f'<div class="stat-label">{esc(label)}</div></div>'
        )
    return f'<div class="stats-grid">{"".join(cards)}</div>'


def section_title(icon_text):
    return f'<div class="section-title">{icon_text}</div>'


_GENERIC_META = {"", "不限", "学历不限", "经验不限", "全国", "未知", "其他", "None"}


def meta_items(items, salary_first=True):
    """meta 标签行。items: [(文本, 类型)]，类型 salary/company/''；薪资(含面议)始终保留，其余空泛值跳过。"""
    out = []
    for text, kind in items:
        s = "" if text is None else str(text).strip()
        if not s:
            continue
        if kind != "salary" and s in _GENERIC_META:
            continue
        cls = "meta-item"
        if kind == "salary":
            cls += " is-salary"
        elif kind == "company":
            cls += " is-company"
        out.append(f'<span class="{cls}">{esc(s)}</span>')
    return f'<div class="job-meta">{"".join(out)}</div>'


def dimensions_bar(dim_detail):
    """五维紧凑评分条。dim_detail: {'技术':80,'经验':70,...}；空则返回 ''。"""
    if not dim_detail:
        return ""
    cells = []
    for name, score in dim_detail:
        try:
            s = max(0, min(100, float(score)))
        except (TypeError, ValueError):
            continue
        cells.append(
            f'<div class="dimension"><div class="dim-top"><span>{esc(name)}</span>'
            f'<span class="dim-score">{s:.0f}</span></div>'
            f'<div class="dim-bar"><div class="dim-fill" style="width:{s:.0f}%"></div></div></div>'
        )
    if not cells:
        return ""
    return f'<div class="dimensions">{"".join(cells)}</div>'


def skill_block(matched, missing, plain, label="技能标签"):
    """技能标签区：命中(绿)/缺失(红)/普通(橙)。"""
    parts = []
    seen = set()
    for s in (matched or []):
        if s and s not in seen:
            seen.add(s); parts.append(f'<span class="skill-tag matched">{esc(s)} ✓</span>')
    for s in (missing or []):
        if s and s not in seen:
            seen.add(s); parts.append(f'<span class="skill-tag missing">{esc(s)} ✗</span>')
    for s in (plain or []):
        if s and s not in seen:
            seen.add(s); parts.append(f'<span class="skill-tag">{esc(s)}</span>')
    if not parts:
        return ""
    return (f'<div class="job-skills"><span class="skills-label">{esc(label)}：</span>'
            f'{"".join(parts)}</div>')


def jd_detail(blocks, toggle_id_hint=""):
    """折叠的 JD 区。blocks: [(标题, 文本)]，自动跳过空文本。"""
    secs = []
    for title, text in blocks:
        if not text or not str(text).strip():
            continue
        secs.append(f'<div class="jd-section"><div class="jd-title">{esc(title)}</div>'
                    f'<div class="jd-content">{esc(str(text).strip())}</div></div>')
    if not secs:
        secs.append('<div class="jd-section"><div class="jd-content text-muted">暂无详细JD信息</div></div>')
    return f'<div class="job-jd-detail" style="display:none">{"".join(secs)}</div>'


def action_buttons(job_url, company_url, job_label="查看岗位", company_label="查看公司",
                   show_toggle=True, toggle_label="展开JD详情"):
    """统一三按钮：查看岗位 / 查看公司 / 展开JD。无链接时优雅降级。"""
    btns = []
    if job_url:
        btns.append(f'<a href="{esc(job_url)}" target="_blank" rel="noopener" class="btn btn-primary">🔗 {esc(job_label)}</a>')
    if company_url:
        btns.append(f'<a href="{esc(company_url)}" target="_blank" rel="noopener" class="btn btn-secondary">🏢 {esc(company_label)}</a>')
    if show_toggle:
        btns.append(f'<button type="button" class="btn btn-toggle" onclick="toggleJD(this)">📄 {esc(toggle_label)}</button>')
    return f'<div class="job-actions">{"".join(btns)}</div>'


def job_card(rank, title, score, meta_html="", badges_html="", company_line="",
             reasons_html="", recommend="", dimensions_html="", skills_html="",
             actions_html="", jd_html="", extra_top=""):
    """组装一张标准岗位卡片（各区块均为已渲染 HTML，空串则不显示）。"""
    level, color = score_bucket(score)
    try:
        score_num = int(round(float(score)))
    except (TypeError, ValueError):
        score_num, color, level = 0, "#bbb", "未评分"
    head_badges = f'<div class="header-badges">{badges_html}</div>' if badges_html else ""
    company_block = ""
    if company_line:
        company_block = f'<div class="job-company">{company_line}{head_badges}</div>'
    reasons = f'<div class="job-reasons">{reasons_html}</div>' if reasons_html else ""
    rec = f'<div class="recommend-line">💡 {esc(recommend)}</div>' if recommend else ""
    return f'''
        <div class="job-card" data-score="{score_num}">
            <div class="job-header">
                <div class="job-rank">{rank}</div>
                <div class="job-title-area">
                    <div class="job-title">{esc(title)}</div>
                    {company_block}
                </div>
                <div class="job-score" style="color:{color};border-color:{color}">
                    <div class="score-num">{score_num}</div>
                    <div class="score-label">匹配度</div>
                    <div class="score-level" style="color:{color}">{level}</div>
                </div>
            </div>
            {extra_top}
            {meta_html}
            {reasons}
            {dimensions_html}
            {rec}
            {skills_html}
            {actions_html}
            {jd_html}
        </div>'''


TOGGLE_JD_JS = """
function toggleJD(btn){
  var card = btn.closest('.job-card'); if(!card) return;
  var d = card.querySelector('.job-jd-detail'); if(!d) return;
  if(d.style.display === 'none'){ d.style.display='block'; btn.textContent='📄 收起JD详情'; }
  else { d.style.display='none'; btn.textContent='📄 展开JD详情'; }
}
"""

FILTER_JS = """
function applyFilters(){
  var soe=document.getElementById('filter-soe'), camp=document.getElementById('filter-campus'),
      high=document.getElementById('filter-high'), bach=document.getElementById('filter-bachelor');
  var fSoe=soe&&soe.checked, fCamp=camp&&camp.checked, fHigh=high&&high.checked, fBach=bach&&bach.checked;
  document.querySelectorAll('.job-card').forEach(function(card){
    var score=parseInt(card.dataset.score||'0',10), text=card.textContent, show=true;
    if(fSoe && !text.includes('国企')) show=false;
    if(fCamp && !text.includes('校招')) show=false;
    if(fHigh && score<80) show=false;
    if(fBach && /硕士|博士|研究生/.test(text)) show=false;
    card.style.display=show?'block':'none';
  });
}
"""


def filter_bar(soe=False, campus=False, high=True, bachelor=False):
    """标准筛选栏，参数控制是否出现对应复选框。"""
    opts = []
    if soe:
        opts.append('<label><input type="checkbox" id="filter-soe" onchange="applyFilters()"> 仅国企</label>')
    if campus:
        opts.append('<label><input type="checkbox" id="filter-campus" onchange="applyFilters()"> 仅校招</label>')
    if high:
        opts.append('<label><input type="checkbox" id="filter-high" onchange="applyFilters()"> 仅高度匹配(≥80)</label>')
    if bachelor:
        opts.append('<label><input type="checkbox" id="filter-bachelor" onchange="applyFilters()"> 仅本科可投</label>')
    if not opts:
        return ""
    return '<div class="filter-bar"><span class="filter-title">筛选：</span>' + "".join(opts) + "</div>"


def page(title, subtitle, body_html, extra_js="", footer_note=""):
    """整页骨架。body_html 为已渲染的统计卡+区块+卡片等全部主体内容。"""
    footer = footer_note or "匹配度由算法基于你的简历自动评分，仅供参考；是否投递请结合岗位详情与个人判断。"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>{THEME_CSS}</style>
</head>
<body>
<div class="container">
    <div class="report-header">
        <h1>{esc(title)}</h1>
        <div class="subtitle">{subtitle}</div>
    </div>
    {body_html}
    <div class="report-footer">{footer}</div>
</div>
<script>{TOGGLE_JD_JS}{extra_js}</script>
</body>
</html>"""
