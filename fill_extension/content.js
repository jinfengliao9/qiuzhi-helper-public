// ===== 网申轻量点填扩展 content.js =====
// 数据来源：application_profile.json（由 gen_fill_extension.py 生成时嵌入）
// 纯本地运行，不上传任何数据

const FIELDS = [{"category": "基本信息", "label": "姓名", "value": "张三"}, {"category": "基本信息", "label": "性别", "value": "男"}, {"category": "基本信息", "label": "民族", "value": "汉族"}, {"category": "基本信息", "label": "出生日期", "value": "2004-04-25"}, {"category": "基本信息", "label": "身份证号", "value": "11010120000101001X"}, {"category": "基本信息", "label": "国籍", "value": "中国"}, {"category": "基本信息", "label": "籍贯", "value": "湖南省示例城市C市"}, {"category": "基本信息", "label": "生源地", "value": "湖南省示例城市C市"}, {"category": "基本信息", "label": "政治面貌", "value": "群众"}, {"category": "基本信息", "label": "婚姻状况", "value": "未婚"}, {"category": "基本信息", "label": "健康状况", "value": "良好"}, {"category": "基本信息", "label": "身高", "value": "158"}, {"category": "基本信息", "label": "体重", "value": "55"}, {"category": "基本信息", "label": "手机", "value": "13800138000"}, {"category": "基本信息", "label": "邮箱", "value": "zhangsan@example.com"}, {"category": "基本信息", "label": "现居住地", "value": "示例城市A"}, {"category": "基本信息", "label": "入学前户口", "value": "湖南省示例城市C市"}, {"category": "基本信息", "label": "求职意向", "value": "测绘工程师"}, {"category": "基本信息", "label": "期望薪资", "value": "6000-8000"}, {"category": "基本信息", "label": "期望城市", "value": "不限"}, {"category": "基本信息", "label": "是否服从调剂", "value": "是"}, {"category": "基本信息", "label": "证件照", "value": "avatar.jpg"}, {"category": "教育背景1", "label": "学校", "value": "示例大学"}, {"category": "教育背景1", "label": "学院", "value": "测绘与地理信息学院"}, {"category": "教育背景1", "label": "专业", "value": "测绘工程"}, {"category": "教育背景1", "label": "学历", "value": "本科"}, {"category": "教育背景1", "label": "学位", "value": "工学学士"}, {"category": "教育背景1", "label": "是否全日制", "value": "是"}, {"category": "教育背景1", "label": "入学时间", "value": "2023.09"}, {"category": "教育背景1", "label": "毕业时间", "value": "2027.06"}, {"category": "教育背景1", "label": "GPA", "value": ""}, {"category": "教育背景1", "label": "专业排名", "value": "前40%"}, {"category": "教育背景1", "label": "主修课程", "value": "测量学、大地测量学、GNSS原理与应用、摄影测量与遥感、GIS原理、空间数据库、测量平差、C语言程序设计"}, {"category": "教育背景1", "label": "毕业设计", "value": ""}, {"category": "实习经历1", "label": "单位名称", "value": "示例测绘科技有限公司"}, {"category": "实习经历1", "label": "单位性质", "value": "民企"}, {"category": "实习经历1", "label": "单位规模", "value": "100-499人"}, {"category": "实习经历1", "label": "岗位", "value": "测绘实习生"}, {"category": "实习经历1", "label": "入职时间", "value": "2026.07"}, {"category": "实习经历1", "label": "离职时间", "value": "2026.09"}, {"category": "实习经历1", "label": "工作地点", "value": "示例城市B"}, {"category": "实习经历1", "label": "工作内容", "value": "['参与示例城市B市五华县示例镇二轮土地承包延包项目全流程，完成农户资料录入核实与权属数据入库，确保数据准确性', '运用ArcGIS按村制作房屋宗地一体占压耕地矢量图件，完成全镇范围的矢量数据处理与拓扑检查', '独立使用Claude Code等AI工具开发权属信息校验工具，实现身份证重复检测、户主唯一性校验、分户清单自动生成，显著提升检查效率', '参与摸底核实、开展调查、审核公示等9个项目阶段，熟悉农村土地承包延包业务规范与政策要求']"}, {"category": "实习经历1", "label": "证明人", "value": ""}, {"category": "实习经历1", "label": "证明人电话", "value": ""}, {"category": "项目经历1", "label": "项目名称", "value": "学期集中实训（全方向实操训练）"}, {"category": "项目经历1", "label": "担任角色", "value": "核心成员"}, {"category": "项目经历1", "label": "开始时间", "value": "2023.09"}, {"category": "项目经历1", "label": "结束时间", "value": "至今"}, {"category": "项目经历1", "label": "项目描述", "value": "['外业测绘：完成地形测量、大地测量、GNSS实习，熟练操作RTK、全站仪，独立完成地形测图、权属测量、航测像控测量等外业任务', '制图遥感：运用CAD、ArcGIS完成专业制图，参与摄影测量实训，具备航测影像处理、DEM制作与成图能力', 'GIS数据库：使用ArcGIS完成空间数据处理与叠加分析，独立制作地质灾害专题图，搭建空间数据库并完成数据入库', '编程开发：运用C语言完成测量程序设计，实现测量数据批量解算处理，参与地理信息工程及应用开发系统实践']"}, {"category": "获奖经历1", "label": "名称", "value": "校园青春舞团体赛特等奖"}, {"category": "获奖经历1", "label": "级别", "value": "校级"}, {"category": "获奖经历1", "label": "时间", "value": ""}, {"category": "获奖经历1", "label": "编号", "value": ""}, {"category": "语言能力", "label": "语言能力1", "value": "名称:大学日语四级 | 分数/等级:63.5"}, {"category": "专业技能", "label": "测量仪器", "value": "RTK、全站仪、GNSS"}, {"category": "专业技能", "label": "软件工具", "value": "ArcGIS、CAD、摄影测量、空间数据库"}, {"category": "专业技能", "label": "编程语言", "value": "C语言、SQL、AI辅助编程"}, {"category": "专业技能", "label": "专业技能", "value": "地形测量、地籍测量、空间分析、数据入库、专题图制作、DEM制作"}, {"category": "专业技能", "label": "其他技能", "value": "C1驾照"}, {"category": "培训经历1", "label": "名称", "value": "校内课程实训"}, {"category": "培训经历1", "label": "机构", "value": "示例大学"}, {"category": "培训经历1", "label": "开始时间", "value": ""}, {"category": "培训经历1", "label": "结束时间", "value": ""}, {"category": "培训经历1", "label": "内容", "value": "每周1-3个实训"}, {"category": "家庭成员1", "label": "称谓", "value": "父亲"}, {"category": "家庭成员1", "label": "姓名", "value": "张建国"}, {"category": "家庭成员1", "label": "年龄", "value": "49"}, {"category": "家庭成员1", "label": "政治面貌", "value": "群众"}, {"category": "家庭成员1", "label": "工作单位", "value": "无"}, {"category": "家庭成员1", "label": "职务", "value": "农民工"}, {"category": "家庭成员1", "label": "电话", "value": "13900139000"}, {"category": "家庭成员2", "label": "称谓", "value": "母亲"}, {"category": "家庭成员2", "label": "姓名", "value": "李秀英"}, {"category": "家庭成员2", "label": "年龄", "value": "48"}, {"category": "家庭成员2", "label": "政治面貌", "value": "群众"}, {"category": "家庭成员2", "label": "工作单位", "value": "无"}, {"category": "家庭成员2", "label": "职务", "value": "农民工"}, {"category": "家庭成员2", "label": "电话", "value": ""}, {"category": "紧急联系人", "label": "姓名", "value": "张建国"}, {"category": "紧急联系人", "label": "关系", "value": "父亲"}, {"category": "紧急联系人", "label": "电话", "value": "13900139000"}, {"category": "其他", "label": "兴趣特长", "value": "羽毛球、乒乓球"}, {"category": "其他", "label": "自我评价", "value": "能接受长期出差与外业工作，吃苦耐劳\n主动学习能力强，能快速掌握新工具并应用于生产\n细心严谨，具备权属数据处理等高精度工作的实操经验"}];
const CATEGORIES = ["基本信息", "教育背景1", "实习经历1", "项目经历1", "获奖经历1", "语言能力", "专业技能", "培训经历1", "家庭成员1", "家庭成员2", "紧急联系人", "其他"];


let lastFocusedElement = null;

// 记录用户最后点击/聚焦的输入框
document.addEventListener('focusin', function(e) {
    const el = e.target;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
        lastFocusedElement = el;
        updateStatus();
    }
}, true);

document.addEventListener('mousedown', function(e) {
    const el = e.target;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
        lastFocusedElement = el;
        updateStatus();
    }
}, true);

// 核心填充函数：兼容 React/Vue 受控组件
function fillValue(el, value) {
    if (!el) {
        showToast('请先点击页面上的输入框');
        return false;
    }
    if (!value) {
        showToast('该字段为空，未填写');
        return false;
    }
    const tag = el.tagName;
    if (tag === 'SELECT') {
        let matched = false;
        for (let i = 0; i < el.options.length; i++) {
            const opt = el.options[i];
            if (opt.text.includes(value) || opt.value.includes(value) || value.includes(opt.text)) {
                el.selectedIndex = i;
                matched = true;
                break;
            }
        }
        if (!matched && el.options.length > 1) {
            el.selectedIndex = 0;
        }
        el.dispatchEvent(new Event('change', { bubbles: true }));
        markFilled(el);
        showToast('已填入下拉框: ' + value.substring(0, 15));
        return true;
    }
    const proto = tag === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
    const nativeSetter = Object.getOwnPropertyDescriptor(proto, 'value').set;
    try {
        nativeSetter.call(el, value);
    } catch(e) {
        el.value = value;
    }
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
    el.dispatchEvent(new FocusEvent('focus', { bubbles: true }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    try {
        el.dispatchEvent(new CompositionEvent('compositionend', { bubbles: true, data: value }));
    } catch(e) {}
    el.dispatchEvent(new FocusEvent('blur', { bubbles: true }));
    markFilled(el);
    showToast('已填入: ' + value.substring(0, 20));
    return true;
}

function markFilled(el) {
    const orig = el.style.backgroundColor;
    el.style.backgroundColor = '#fff3cd';
    setTimeout(function() {
        el.style.backgroundColor = orig;
    }, 1000);
}

// ===== 拖动逻辑 =====
let isDragging = false;
let dragOffsetX = 0;
let dragOffsetY = 0;

function dragStart(e) {
    if (e.target.id === 'fill-toggle-btn') return;
    isDragging = true;
    const panel = document.getElementById('fill-extension-panel');
    const rect = panel.getBoundingClientRect();
    dragOffsetX = e.clientX - rect.left;
    dragOffsetY = e.clientY - rect.top;
    document.addEventListener('mousemove', dragMove);
    document.addEventListener('mouseup', dragEnd);
    e.preventDefault();
}

function dragMove(e) {
    if (!isDragging) return;
    const panel = document.getElementById('fill-extension-panel');
    let newLeft = e.clientX - dragOffsetX;
    let newTop = e.clientY - dragOffsetY;
    newLeft = Math.max(0, Math.min(newLeft, window.innerWidth - 50));
    newTop = Math.max(0, Math.min(newTop, window.innerHeight - 40));
    panel.style.left = newLeft + 'px';
    panel.style.top = newTop + 'px';
    panel.style.right = 'auto';
}

function dragEnd() {
    isDragging = false;
    document.removeEventListener('mousemove', dragMove);
    document.removeEventListener('mouseup', dragEnd);
}

// 创建面板（可拖动、折叠保留头部）
function createPanel() {
    const panel = document.createElement('div');
    panel.id = 'fill-extension-panel';
    const initLeft = Math.max(0, window.innerWidth - 300);
    panel.style.cssText = 'position:fixed;top:0;left:' + initLeft + 'px;width:300px;background:#fff;border:1px solid #ddd;border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.15);z-index:2147483647;font-family:Microsoft YaHei,sans-serif;font-size:13px;display:flex;flex-direction:column;';

    // 头部
    const header = document.createElement('div');
    header.id = 'fill-panel-header';
    header.style.cssText = 'padding:8px 12px;background:#2c5f8a;color:#fff;display:flex;justify-content:space-between;align-items:center;cursor:move;user-select:none;';
    header.innerHTML = '<b>📋 网申点填</b>';
    const toggleBtn = document.createElement('span');
    toggleBtn.id = 'fill-toggle-btn';
    toggleBtn.textContent = '▼';
    toggleBtn.style.cssText = 'cursor:pointer;font-size:14px;padding:0 4px;';
    toggleBtn.onclick = function(e) { e.stopPropagation(); togglePanel(); };
    header.appendChild(toggleBtn);
    header.addEventListener('mousedown', dragStart);
    panel.appendChild(header);

    // 内容区域
    const body = document.createElement('div');
    body.id = 'fill-panel-body';
    body.style.cssText = 'display:flex;flex-direction:column;max-height:calc(100vh - 40px);';

    const status = document.createElement('div');
    status.id = 'fill-status';
    status.style.cssText = 'padding:6px 12px;background:#f0f7ff;font-size:12px;color:#666;border-bottom:1px solid #e0e0e0;';
    status.textContent = '请先点击页面上的输入框';
    body.appendChild(status);

    const searchBox = document.createElement('input');
    searchBox.type = 'text';
    searchBox.placeholder = '🔍 搜索字段...';
    searchBox.style.cssText = 'margin:8px;padding:6px 8px;border:1px solid #ddd;border-radius:4px;font-size:12px;width:calc(100% - 16px);box-sizing:border-box;';
    searchBox.oninput = function() { filterFields(this.value); };
    searchBox.onmousedown = function(e) { e.stopPropagation(); };
    body.appendChild(searchBox);

    const container = document.createElement('div');
    container.id = 'fill-fields-container';
    container.style.cssText = 'flex:1;overflow-y:auto;padding:0 8px 8px;';
    body.appendChild(container);

    const footer = document.createElement('div');
    footer.style.cssText = 'padding:8px 12px;background:#f9f9f9;font-size:11px;color:#999;border-top:1px solid #e0e0e0;';
    footer.textContent = '拖动头部移动 | 先点输入框→再点字段';
    body.appendChild(footer);

    panel.appendChild(body);
    document.body.appendChild(panel);
    renderFields();
    return panel;
}

// 折叠/展开（只隐藏内容，保留头部）
function togglePanel() {
    const body = document.getElementById('fill-panel-body');
    const btn = document.getElementById('fill-toggle-btn');
    if (!body) return;
    if (body.style.display === 'none') {
        body.style.display = 'flex';
        btn.textContent = '▼';
    } else {
        body.style.display = 'none';
        btn.textContent = '▲';
    }
}

function renderFields(filter) {
    const container = document.getElementById('fill-fields-container');
    if (!container) return;
    container.innerHTML = '';
    const keyword = (filter || '').toLowerCase();
    CATEGORIES.forEach(function(cat) {
        const catFields = FIELDS.filter(function(f) { return f.category === cat; });
        const matched = catFields.filter(function(f) {
            return !keyword || f.label.toLowerCase().includes(keyword) || f.value.toLowerCase().includes(keyword);
        });
        if (keyword && matched.length === 0) return;
        const catDiv = document.createElement('div');
        catDiv.style.cssText = 'margin-top:8px;';
        const catTitle = document.createElement('div');
        catTitle.style.cssText = 'font-weight:600;color:#2c5f8a;padding:4px 0;font-size:12px;border-bottom:1px solid #e8e8e8;';
        catTitle.textContent = cat + ' (' + (keyword ? matched.length : catFields.length) + ')';
        catDiv.appendChild(catTitle);
        (keyword ? matched : catFields).forEach(function(f) {
            const fieldDiv = document.createElement('div');
            const isEmpty = !f.value;
            fieldDiv.style.cssText = 'padding:5px 6px;margin:2px 0;border-radius:4px;cursor:pointer;background:' + (isEmpty ? '#f5f5f5' : '#fff') + ';border:1px solid #eee;display:flex;justify-content:space-between;align-items:center;';
            fieldDiv.onmouseenter = function() { this.style.background = isEmpty ? '#f0f0f0' : '#e8f4ff'; };
            fieldDiv.onmouseleave = function() { this.style.background = isEmpty ? '#f5f5f5' : '#fff'; };
            fieldDiv.onclick = function() { fillValue(lastFocusedElement, f.value); };
            const labelSpan = document.createElement('span');
            labelSpan.style.cssText = 'color:#333;font-size:12px;';
            labelSpan.textContent = f.label;
            fieldDiv.appendChild(labelSpan);
            const valSpan = document.createElement('span');
            valSpan.style.cssText = 'color:#999;font-size:11px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
            valSpan.textContent = isEmpty ? '(空)' : f.value;
            valSpan.title = f.value;
            fieldDiv.appendChild(valSpan);
            catDiv.appendChild(fieldDiv);
        });
        container.appendChild(catDiv);
    });
}

function filterFields(keyword) {
    renderFields(keyword);
}

function updateStatus() {
    const status = document.getElementById('fill-status');
    if (!status) return;
    if (lastFocusedElement) {
        const tag = lastFocusedElement.tagName;
        const placeholder = lastFocusedElement.placeholder || lastFocusedElement.name || '';
        status.textContent = '✅ 已选中: ' + tag + (placeholder ? ' (' + placeholder.substring(0,15) + ')' : '');
        status.style.color = '#2c5f8a';
    } else {
        status.textContent = '请先点击页面上的输入框';
        status.style.color = '#666';
    }
}

let toastEl = null;
function showToast(msg) {
    if (!toastEl) {
        toastEl = document.createElement('div');
        toastEl.style.cssText = 'position:fixed;bottom:30px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:8px 16px;border-radius:20px;font-size:13px;z-index:2147483647;opacity:0;transition:opacity 0.2s;pointer-events:none;';
        document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.style.opacity = '1';
    setTimeout(function() { toastEl.style.opacity = '0'; }, 1500);
}

if (document.body) {
    createPanel();
} else {
    document.addEventListener('DOMContentLoaded', createPanel);
}

console.log('[网申点填扩展] 已加载 v1.1，共 ' + FIELDS.length + ' 个字段，' + CATEGORIES.length + ' 个分类');
