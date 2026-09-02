// ==UserScript==
// @name         BOSS直聘岗位采集器（求职助手）
// @namespace    job-search-assistant
// @version      1.0.0
// @description  在BOSS直聘搜索页【被动捕获】页面自己发出的 joblist.json 响应，自动累积去重，一键导出JSON（明文薪资）。只读取、不主动发请求、不自动投递，规避自动化检测。
// @author       job-search-assistant
// @match        *://*.zhipin.com/*
// @include      *://*.zhipin.com/*
// @include      https://www.zhipin.com/*
// @include      https://m.zhipin.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function () {
  'use strict';

  // ============ 配置 ============
  var LIST_API = '/wapi/zpgeek/search/joblist.json'; // 列表接口（明文薪资）
  var STORE_KEY = '__boss_capture_store_v1';
  var state = { jobs: {}, order: [] };                 // 按 encryptJobId 去重
  var panelEl = null, countEl = null, lastEl = null;

  // ============ 工具 ============
  function safeParse(txt) {
    try { return JSON.parse(txt); } catch (e) { return null; }
  }
  function nowStr() {
    var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) +
      ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds());
  }
  function getMeta() {
    try {
      var u = new URL(location.href);
      return { query: u.searchParams.get('query') || '', city: u.searchParams.get('city') || '', url: location.href };
    } catch (e) { return { query: '', city: '', url: location.href }; }
  }

  // ============ 核心：被动捕获，只镜像页面自己的响应，不发起任何请求 ============
  function ingest(url, text, status) {
    if (!text || ('' + url).indexOf(LIST_API) === -1) return;
    var obj = safeParse(text);
    if (!obj || obj.code !== 0) return;
    var list = (obj.zpData && obj.zpData.jobList) || [];
    var added = 0;
    for (var i = 0; i < list.length; i++) {
      var j = list[i];
      var id = j.encryptJobId || (j.brandName + '|' + j.jobName);
      if (!state.jobs[id]) { state.jobs[id] = j; state.order.push(id); added++; }
    }
    if (added > 0) refreshPanel(added, list.length);
  }

  // hook fetch
  var _fetch = window.fetch;
  if (_fetch) {
    window.fetch = function () {
      var args = arguments, url = args[0];
      if (url && url.url) url = url.url;
      var p = _fetch.apply(this, args);
      return p.then(function (res) {
        try { var st = res.status; res.clone().text().then(function (t) { ingest(url, t, st); }); } catch (e) {}
        return res;
      });
    };
  }
  // hook XHR（axios 走这里）
  var _open = XMLHttpRequest.prototype.open, _send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return _open.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function () {
    var self = this;
    this.addEventListener('readystatechange', function () {
      if (self.readyState === 4) { try { ingest(self.__u, self.responseText, self.status); } catch (e) {} }
    });
    return _send.apply(this, arguments);
  };

  // ============ 导出：格式对齐 parse_joblist_api.py（zpData.jobList）============
  function collectJobs() {
    return state.order.map(function (id) { return state.jobs[id]; });
  }
  function exportJSON() {
    var jobs = collectJobs();
    if (!jobs.length) { flash('还没有捕获到岗位，请先搜索/翻页'); return; }
    var payload = {
      platform: 'BOSS直聘',
      capture_method: 'tampermonkey_passive',
      exported_at: nowStr(),
      meta: getMeta(),
      total: jobs.length,
      code: 0, message: 'Success',
      zpData: { jobList: jobs }
    };
    var blob = new Blob([JSON.stringify(payload)], { type: 'application/json;charset=utf-8' });
    var a = document.createElement('a');
    var meta = getMeta();
    a.href = URL.createObjectURL(blob);
    a.download = 'boss岗位_' + (meta.query || '全部') + '_' + jobs.length + '条_' +
      nowStr().replace(/[: ]/g, '-') + '.json';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    flash('已导出 ' + jobs.length + ' 条岗位JSON');
  }
  function clearStore() {
    state = { jobs: {}, order: [] };
    refreshPanel(0, 0, true);
    flash('已清空');
  }

  // ============ 浮动面板 ============
  function refreshPanel(added, pageTotal, isClear) {
    if (!panelEl) return;
    var n = state.order.length;
    if (countEl) countEl.textContent = n + ' 个岗位';
    if (lastEl && !isClear) lastEl.textContent = added > 0 ? ('本页+' + added + '（共' + pageTotal + '）  ' + nowStr().slice(11)) : ('已去重  ' + nowStr().slice(11));
    if (isClear && lastEl) lastEl.textContent = '等待搜索/翻页';
  }
  function flash(msg) {
    if (!panelEl) return;
    var t = document.createElement('div');
    t.textContent = msg;
    t.style.cssText = 'margin-top:4px;font-size:12px;color:#1a7f37;';
    panelEl.appendChild(t);
    setTimeout(function () { t.remove(); }, 2500);
  }
  function buildPanel() {
    if (panelEl || !document.body) return;
    var box = document.createElement('div');
    box.id = '__boss_cap_panel';
    box.style.cssText = 'position:fixed;top:90px;right:16px;z-index:2147483647;width:172px;' +
      'background:#fff;border:1px solid #d0d7de;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.15);' +
      'padding:10px;font:13px/1.5 "Microsoft YaHei",sans-serif;color:#1f2328;user-select:none;';
    box.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;cursor:move;margin-bottom:6px;">' +
      '<b style="font-size:13px;">🎯 岗位采集</b><span id="__bc_min" style="cursor:pointer;color:#57606a;">—</span></div>' +
      '<div id="__bc_count" style="font-size:15px;font-weight:bold;color:#0969da;">0 个岗位</div>' +
      '<div id="__bc_last" style="font-size:11px;color:#57606a;margin:2px 0 8px;min-height:14px;">等待搜索/翻页</div>' +
      '<button id="__bc_exp" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#0969da;color:#fff;cursor:pointer;font-size:13px;">导出JSON</button>' +
      '<button id="__bc_clr" style="width:100%;padding:5px;border:1px solid #d0d7de;border-radius:6px;background:#f6f8fa;cursor:pointer;font-size:12px;">清空重抓</button>' +
      '<div style="font-size:10px;color:#8c959f;margin-top:6px;line-height:1.4;">正常搜索/翻页即可自动捕获，不自动投递</div>';
    document.body.appendChild(box);
    panelEl = box;
    countEl = box.querySelector('#__bc_count');
    lastEl = box.querySelector('#__bc_last');
    box.querySelector('#__bc_exp').onclick = exportJSON;
    box.querySelector('#__bc_clr').onclick = clearStore;
    var body = box;
    box.querySelector('#__bc_min').onclick = function () {
      var nodes = box.querySelectorAll('div,button');
      var hidden = body.dataset.h === '1';
      for (var i = 2; i < nodes.length; i++) nodes[i].style.display = hidden ? '' : 'none';
      body.dataset.h = hidden ? '0' : '1';
      this.textContent = hidden ? '—' : '+';
    };
    // 拖动
    var bar = box.firstElementChild, sx = 0, sy = 0, ox = 0, oy = 0, drag = false;
    bar.onmousedown = function (e) {
      drag = true; sx = e.clientX; sy = e.clientY;
      var r = box.getBoundingClientRect(); ox = r.left; oy = r.top; e.preventDefault();
    };
    document.addEventListener('mousemove', function (e) {
      if (!drag) return;
      box.style.left = (ox + e.clientX - sx) + 'px';
      box.style.top = (oy + e.clientY - sy) + 'px';
      box.style.right = 'auto';
    });
    document.addEventListener('mouseup', function () { drag = false; });
  }
  // document-start 时 body 可能还没好，轮询挂载
  var iv = setInterval(function () {
    if (document.body) { buildPanel(); clearInterval(iv); }
  }, 200);

  // SPA 路由变化时无需特殊处理，hook 常驻；暴露一个调试句柄
  window.__bossCapture = { export: exportJSON, clear: clearStore, jobs: collectJobs };
})();
