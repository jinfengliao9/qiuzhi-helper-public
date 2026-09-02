# -*- coding: utf-8 -*-
"""
阶段4a：生成 Edge 轻量点填扩展
从 application_profile.json 读取所有字段，展平后嵌入 content.js，生成完整 MV3 扩展。
用法：python gen_fill_extension.py
生成目录：fill_extension/
  - manifest.json
  - content.js（含嵌入的字段数据 + 侧边栏UI + 填充逻辑）
  - icon.svg（简单图标）
"""
import json, io, os

WS = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(WS, "application_profile.json")
EXT_DIR = os.path.join(WS, "fill_extension")
os.makedirs(EXT_DIR, exist_ok=True)

def load_profile():
    with io.open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)

def flatten_fields(p):
    """把profile展平成 [{category, label, value}] 列表"""
    fields = []
    
    # 基本信息
    b = p.get("基本信息", {})
    for k, v in b.items():
        if k == "期望城市" and isinstance(v, list):
            v = "、".join(v)
        fields.append({"category": "基本信息", "label": k, "value": str(v) if v else ""})
    
    # 教育背景
    for i, e in enumerate(p.get("教育背景", []), 1):
        for k, v in e.items():
            if k == "主修课程" and isinstance(v, list):
                v = "、".join(v)
            fields.append({"category": f"教育背景{i}", "label": k, "value": str(v) if v else ""})
    
    # 实习经历
    for i, it in enumerate(p.get("实习经历", []), 1):
        for k, v in it.items():
            fields.append({"category": f"实习经历{i}", "label": k, "value": str(v) if v else ""})
    
    # 项目经历
    for i, pr in enumerate(p.get("项目经历", []), 1):
        for k, v in pr.items():
            fields.append({"category": f"项目经历{i}", "label": k, "value": str(v) if v else ""})
    
    # 获奖经历
    for i, a in enumerate(p.get("获奖经历", []), 1):
        for k, v in a.items():
            fields.append({"category": f"获奖经历{i}", "label": k, "value": str(v) if v else ""})
    
    # 技能证书
    sc = p.get("技能证书", {})
    for cat, items in sc.items():
        if isinstance(items, list):
            for j, item in enumerate(items, 1):
                if isinstance(item, dict):
                    val = " | ".join(f"{kk}:{vv}" for kk, vv in item.items() if vv)
                else:
                    val = str(item)
                fields.append({"category": cat, "label": f"{cat}{j}", "value": val})
    
    # 专业技能
    ps = p.get("专业技能", {})
    for cat, items in ps.items():
        if isinstance(items, list):
            val = "、".join(items)
            fields.append({"category": "专业技能", "label": cat, "value": val})
    
    # 培训经历
    for i, t in enumerate(p.get("培训经历", []), 1):
        for k, v in t.items():
            fields.append({"category": f"培训经历{i}", "label": k, "value": str(v) if v else ""})
    
    # 家庭成员
    for i, f in enumerate(p.get("家庭成员及社会关系", []), 1):
        for k, v in f.items():
            fields.append({"category": f"家庭成员{i}", "label": k, "value": str(v) if v else ""})
    
    # 紧急联系人
    ec = p.get("紧急联系人", {})
    for k, v in ec.items():
        fields.append({"category": "紧急联系人", "label": k, "value": str(v) if v else ""})
    
    # 兴趣特长
    fields.append({"category": "其他", "label": "兴趣特长", "value": p.get("兴趣特长", "")})
    
    # 自我评价
    sa = p.get("自我评价", [])
    if isinstance(sa, list):
        val = "\n".join(sa)
    else:
        val = str(sa)
    fields.append({"category": "其他", "label": "自我评价", "value": val})
    
    return fields

# ============ 生成 manifest.json ============
manifest = {
    "manifest_version": 3,
    "name": "网申轻量点填（求职助手）",
    "version": "1.0.0",
    "description": "网申时先点页面输入框，再点侧边栏字段，自动填入。纯本地，不上传任何数据。",
    "content_scripts": [{
        "matches": ["<all_urls>"],
        "js": ["content.js"],
        "run_at": "document_idle",
        "all_frames": False
    }],
    "permissions": ["storage"],
    "icons": {
        "128": "icon.svg"
    }
}

with io.open(os.path.join(EXT_DIR, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# ============ 生成 icon.svg ============
icon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="20" fill="#2c5f8a"/>
  <text x="64" y="78" font-size="56" text-anchor="middle" fill="white" font-family="Arial" font-weight="bold">填</text>
</svg>'''
with io.open(os.path.join(EXT_DIR, "icon.svg"), "w", encoding="utf-8") as f:
    f.write(icon_svg)

# ============ 生成 content.js（含嵌入数据） ============
fields = flatten_fields(load_profile())
fields_json = json.dumps(fields, ensure_ascii=False)

# 按分类分组
categories = []
seen = set()
for fld in fields:
    if fld["category"] not in seen:
        seen.add(fld["category"])
        categories.append(fld["category"])

content_js = f'''// ===== 网申轻量点填扩展 content.js =====
// 数据来源：application_profile.json（由 gen_fill_extension.py 生成时嵌入）
// 纯本地运行，不上传任何数据

const FIELDS = {fields_json};
const CATEGORIES = {json.dumps(categories, ensure_ascii=False)};

let lastFocusedElement = null;
let panelVisible = true;

// 记录用户最后点击/聚焦的输入框
document.addEventListener('focusin', function(e) {{
    const el = e.target;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {{
        lastFocusedElement = el;
        updateStatus();
    }}
}}, true);

document.addEventListener('mousedown', function(e) {{
    const el = e.target;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {{
        lastFocusedElement = el;
        updateStatus();
    }}
}}, true);

// 核心填充函数：兼容 React/Vue 受控组件
function fillValue(el, value) {{
    if (!el) {{
        showToast('请先点击页面上的输入框');
        return false;
    }}
    if (!value) {{
        showToast('该字段为空，未填写');
        return false;
    }}
    
    const tag = el.tagName;
    
    if (tag === 'SELECT') {{
        // 下拉框：尝试匹配文本或值
        let matched = false;
        for (let i = 0; i < el.options.length; i++) {{
            const opt = el.options[i];
            if (opt.text.includes(value) || opt.value.includes(value) || value.includes(opt.text)) {{
                el.selectedIndex = i;
                matched = true;
                break;
            }}
        }}
        if (!matched && el.options.length > 1) {{
            el.selectedIndex = 0;
        }}
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        markFilled(el);
        showToast('已填入下拉框: ' + value.substring(0, 15));
        return true;
    }}
    
    // input / textarea：用原生 setter 赋值，兼容 React 受控组件
    const proto = tag === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    
    try {{
        nativeSetter.call(el, value);
    }} catch(e) {{
        el.value = value;
    }}
    
    // 触发完整事件链
    el.dispatchEvent(new MouseEvent('mousedown', {{ bubbles: true }}));
    el.dispatchEvent(new FocusEvent('focus', {{ bubbles: true }}));
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    
    // compositionend（中文输入法场景）
    try {{
        el.dispatchEvent(new CompositionEvent('compositionend', {{ bubbles: true, data: value }}));
    }} catch(e) {{}}
    
    el.dispatchEvent(new FocusEvent('blur', {{ bubbles: true }}));
    
    markFilled(el);
    showToast('已填入: ' + value.substring(0, 20));
    return true;
}}

// 标记已填字段（黄色高亮1秒）
function markFilled(el) {{
    const orig = el.style.backgroundColor;
    el.style.backgroundColor = '#fff3cd';
    setTimeout(function() {{
        el.style.backgroundColor = orig;
    }}, 1000);
}}

// 创建侧边栏
function createPanel() {{
    const panel = document.createElement('div');
    panel.id = 'fill-extension-panel';
    panel.style.cssText = `
        position: fixed; top: 0; right: 0; width: 300px; height: 100vh;
        background: #fff; border-left: 1px solid #ddd; box-shadow: -2px 0 8px rgba(0,0,0,0.1);
        z-index: 2147483647; font-family: 'Microsoft YaHei', sans-serif; font-size: 13px;
        display: flex; flex-direction: column; transition: transform 0.2s;
    `;
    
    // 头部
    const header = document.createElement('div');
    header.style.cssText = 'padding: 10px 12px; background: #2c5f8a; color: #fff; display: flex; justify-content: space-between; align-items: center;';
    header.innerHTML = '<b>📋 网申点填</b>';
    
    const toggleBtn = document.createElement('span');
    toggleBtn.textContent = '—';
    toggleBtn.style.cssText = 'cursor:pointer; font-size:18px; padding:0 6px;';
    toggleBtn.onclick = togglePanel;
    header.appendChild(toggleBtn);
    panel.appendChild(header);
    
    // 状态栏
    const status = document.createElement('div');
    status.id = 'fill-status';
    status.style.cssText = 'padding: 6px 12px; background: #f0f7ff; font-size: 12px; color: #666; border-bottom: 1px solid #e0e0e0;';
    status.textContent = '请先点击页面上的输入框';
    panel.appendChild(status);
    
    // 搜索框
    const searchBox = document.createElement('input');
    searchBox.type = 'text';
    searchBox.placeholder = '🔍 搜索字段...';
    searchBox.style.cssText = 'margin: 8px; padding: 6px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; width: calc(100% - 16px); box-sizing: border-box;';
    searchBox.oninput = function() {{ filterFields(this.value); }};
    panel.appendChild(searchBox);
    
    // 字段容器
    const container = document.createElement('div');
    container.id = 'fill-fields-container';
    container.style.cssText = 'flex: 1; overflow-y: auto; padding: 0 8px 8px;';
    panel.appendChild(container);
    
    // 底部提示
    const footer = document.createElement('div');
    footer.style.cssText = 'padding: 8px 12px; background: #f9f9f9; font-size: 11px; color: #999; border-top: 1px solid #e0e0e0;';
    footer.textContent = '先点输入框 → 再点字段 | 数据纯本地';
    panel.appendChild(footer);
    
    document.body.appendChild(panel);
    renderFields();
    return panel;
}}

// 渲染字段（按分类分组）
function renderFields(filter) {{
    const container = document.getElementById('fill-fields-container');
    if (!container) return;
    container.innerHTML = '';
    
    const keyword = (filter || '').toLowerCase();
    
    CATEGORIES.forEach(function(cat) {{
        const catFields = FIELDS.filter(function(f) {{ return f.category === cat; }});
        const matched = catFields.filter(function(f) {{
            return !keyword || f.label.toLowerCase().includes(keyword) || f.value.toLowerCase().includes(keyword);
        }});
        if (keyword && matched.length === 0) return;
        
        const catDiv = document.createElement('div');
        catDiv.style.cssText = 'margin-top: 8px;';
        
        const catTitle = document.createElement('div');
        catTitle.style.cssText = 'font-weight: 600; color: #2c5f8a; padding: 4px 0; font-size: 12px; border-bottom: 1px solid #e8e8e8;';
        catTitle.textContent = cat + ' (' + (keyword ? matched.length : catFields.length) + ')';
        catDiv.appendChild(catTitle);
        
        (keyword ? matched : catFields).forEach(function(f) {{
            const fieldDiv = document.createElement('div');
            const isEmpty = !f.value;
            fieldDiv.style.cssText = `
                padding: 5px 6px; margin: 2px 0; border-radius: 4px; cursor: pointer;
                background: ${{isEmpty ? '#f5f5f5' : '#fff'}}; border: 1px solid #eee;
                display: flex; justify-content: space-between; align-items: center;
                transition: background 0.1s;
            `;
            fieldDiv.onmouseenter = function() {{ this.style.background = isEmpty ? '#f0f0f0' : '#e8f4ff'; }};
            fieldDiv.onmouseleave = function() {{ this.style.background = isEmpty ? '#f5f5f5' : '#fff'; }};
            fieldDiv.onclick = function() {{ fillValue(lastFocusedElement, f.value); }};
            
            const labelSpan = document.createElement('span');
            labelSpan.style.cssText = 'color: #333; font-size: 12px;';
            labelSpan.textContent = f.label;
            fieldDiv.appendChild(labelSpan);
            
            const valSpan = document.createElement('span');
            valSpan.style.cssText = 'color: #999; font-size: 11px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;';
            valSpan.textContent = isEmpty ? '(空)' : f.value;
            valSpan.title = f.value;
            fieldDiv.appendChild(valSpan);
            
            catDiv.appendChild(fieldDiv);
        }});
        
        container.appendChild(catDiv);
    }});
}}

function filterFields(keyword) {{
    renderFields(keyword);
}}

function updateStatus() {{
    const status = document.getElementById('fill-status');
    if (!status) return;
    if (lastFocusedElement) {{
        const tag = lastFocusedElement.tagName;
        const placeholder = lastFocusedElement.placeholder || lastFocusedElement.name || '';
        status.textContent = '✅ 已选中: ' + tag + (placeholder ? ' (' + placeholder.substring(0,15) + ')' : '');
        status.style.color = '#2c5f8a';
    }} else {{
        status.textContent = '请先点击页面上的输入框';
        status.style.color = '#666';
    }}
}}

// 折叠/展开面板
function togglePanel() {{
    const panel = document.getElementById('fill-extension-panel');
    if (!panel) return;
    panelVisible = !panelVisible;
    panel.style.transform = panelVisible ? 'translateX(0)' : 'translateX(280px)';
}}

// Toast 提示
let toastEl = null;
function showToast(msg) {{
    if (!toastEl) {{
        toastEl = document.createElement('div');
        toastEl.style.cssText = 'position:fixed;bottom:30px;right:320px;background:#333;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;z-index:2147483647;opacity:0;transition:opacity 0.2s;pointer-events:none;';
        document.body.appendChild(toastEl);
    }}
    toastEl.textContent = msg;
    toastEl.style.opacity = '1';
    setTimeout(function() {{ toastEl.style.opacity = '0'; }}, 1500);
}}

// 初始化
if (document.body) {{
    createPanel();
}} else {{
    document.addEventListener('DOMContentLoaded', createPanel);
}}

console.log('[网申点填扩展] 已加载，共 ' + FIELDS.length + ' 个字段，' + CATEGORIES.length + ' 个分类');
'''

with io.open(os.path.join(EXT_DIR, "content.js"), "w", encoding="utf-8") as f:
    f.write(content_js)

print(f"扩展已生成到: {EXT_DIR}")
print(f"  - manifest.json")
print(f"  - content.js ({len(content_js)} 字符)")
print(f"  - icon.svg")
print(f"字段总数: {len(fields)}")
print(f"分类数: {len(categories)}")
print(f"\n加载方法：Edge 地址栏输入 edge://extensions → 开启'开发人员模式' → '加载解压缩的扩展' → 选择 {EXT_DIR} 文件夹")
