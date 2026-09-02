// 双平台岗位采集器（BOSS直聘 + 智联招聘）—— Edge 原生扩展 MAIN world, document-start v1.2
// 被动镜像页面自身发出的岗位列表/详情响应；BOSS支持拟人节奏补全JD；不自动投递、不自动打招呼。
(function () {
  'use strict';
  if (window.__bossCapLoaded) return;
  window.__bossCapLoaded = true;

  // ============ 配置 ============
  var BOSS_LIST = '/wapi/zpgeek/search/joblist.json';
  var BOSS_DETAIL = '/wapi/zpgeek/job/detail.json';
  var state = {
    boss: { jobs: {}, order: [] },
    zh: { jobs: {}, order: [] },
    job51: { jobs: {}, order: [], raw: [] },
    liepin: { jobs: {}, order: [], raw: [] }
  };
  var panelEl = null, countEl = null, lastEl = null, fillEl = null;
  var filling = false, stopFlag = false;

  function safeParse(t) { try { return JSON.parse(t); } catch (e) { return null; } }
  function nowHM() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; }; return p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds()); }
  function nowStr() { var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds()); }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function getQuery(u, k) { try { return new URL(u, location.origin).searchParams.get(k) || ''; } catch (e) { return ''; } }
  function bossBucket() { return state.boss; }
  function detailDone() { return state.boss.order.reduce(function (n, id) { return n + (state.boss.jobs[id].__detail ? 1 : 0); }, 0); }

  // ---------- 智联列表识别 ----------
  function zhJobName(o) { return o && (o.jobName || o.name || o.positionName || o.jobTitle || (o.position && o.position.name)); }
  function zhJobComp(o) {
    if (!o) return '';
    var c = o.company;
    if (c && typeof c === 'object') return c.name || c.companyName || c.fullName || c.companyFullName || '';
    return o.companyName || o.orgName || o.companyFullName || '';
  }
  function zhLooksLikeJob(o) {
    if (!o || typeof o !== 'object' || Array.isArray(o)) return false;
    var name = zhJobName(o), comp = zhJobComp(o);
    var id = o.number || o.positionNumber || o.jobNumber || o.jobId || o.advertiseId;
    return !!(name && (comp || id));
  }
  // 在响应对象里递归找出"岗位数组"（抗接口路径变化）
  function findJobArrays(obj, depth, out, seen) {
    depth = depth || 0; if (depth > 6 || !obj || typeof obj !== 'object') return;
    if (seen.has(obj)) return; seen.add(obj);
    if (Array.isArray(obj)) {
      if (obj.length >= 2) {
        var hit = 0;
        for (var i = 0; i < obj.length; i++) if (zhLooksLikeJob(obj[i])) hit++;
        if (hit >= Math.max(2, Math.ceil(obj.length * 0.6))) out.push(obj);
      }
      for (var j = 0; j < obj.length; j++) findJobArrays(obj[j], depth + 1, out, seen);
    } else {
      for (var k in obj) { if (Object.prototype.hasOwnProperty.call(obj, k)) findJobArrays(obj[k], depth + 1, out, seen); }
    }
  }
  function isZhSearchUrl(u) {
    var s = ('' + u).toLowerCase();
    return s.indexOf('zhaopin') !== -1 &&
      (s.indexOf('/search') !== -1 || s.indexOf('positions') !== -1 || s.indexOf('/sou') !== -1 || s.indexOf('job/search') !== -1 || s.indexOf('positionlist') !== -1);
  }
  function zhIdOf(o) {
    return String(o.number || o.positionNumber || o.jobNumber || o.jobId || o.advertiseId ||
      ((zhJobComp(o) || '') + '|' + (zhJobName(o) || '')));
  }

  // ============ 被动捕获 ============
  function ingest(url, text) {
    if (!text) return;
    var u = '' + url;
    // ---- BOSS 列表 ----
    if (u.indexOf(BOSS_LIST) !== -1) {
      var obj = safeParse(text); if (!obj || obj.code !== 0) return;
      var list = (obj.zpData && obj.zpData.jobList) || [], added = 0, b = bossBucket();
      for (var i = 0; i < list.length; i++) {
        var j = list[i], id = j.encryptJobId || (j.brandName + '|' + j.jobName);
        if (!b.jobs[id]) { b.jobs[id] = j; b.order.push(id); added++; }
      }
      if (added > 0) refreshPanel('BOSS +' + added);
      return;
    }
    // ---- BOSS 详情 ----
    if (u.indexOf(BOSS_DETAIL) !== -1) {
      var d = safeParse(text); if (!d || d.code !== 0 || !d.zpData) return;
      var sid = getQuery(u, 'securityId'), bb = bossBucket();
      for (var bi = 0; bi < bb.order.length; bi++) {
        var bj = bb.jobs[bb.order[bi]];
        if (bj.securityId === sid && !bj.__detail) { bj.__detail = d.zpData; break; }
      }
      if (fillEl) fillEl.textContent = 'BOSS JD ' + detailDone() + '/' + bb.order.length;
      return;
    }
    // ---- 智联列表（URL特征 + 形状识别）----
    if (isZhSearchUrl(u)) {
      var zo = safeParse(text); if (!zo) return;
      var arrs = []; findJobArrays(zo, 0, arrs, new Set());
      if (!arrs.length) return;
      var z = state.zh, zadded = 0;
      arrs.forEach(function (arr) {
        arr.forEach(function (it) {
          if (!zhLooksLikeJob(it)) return;
          var zid = zhIdOf(it);
          if (!z.jobs[zid]) { it.__platform = '智联招聘'; z.jobs[zid] = it; z.order.push(zid); zadded++; }
        });
      });
      if (zadded > 0) refreshPanel('智联 +' + zadded);
    }
    // ---- 前程无忧51job列表（URL特征 + 形状识别 + 原始响应记录）----
    if (u.indexOf('51job.com') !== -1) {
      var j5o = safeParse(text);
      if (j5o) {
        state.job51.raw.push({ url: u, data: j5o, time: nowStr() });
        var j5arrs = []; findJobArrays(j5o, 0, j5arrs, new Set());
        if (j5arrs.length) {
          var j5 = state.job51, j5added = 0;
          j5arrs.forEach(function (arr) {
            arr.forEach(function (it) {
              if (!zhLooksLikeJob(it)) return;
              var j5id = zhIdOf(it);
              if (!j5.jobs[j5id]) { it.__platform = '前程无忧'; j5.jobs[j5id] = it; j5.order.push(j5id); j5added++; }
            });
          });
          if (j5added > 0) refreshPanel('51job +' + j5added);
        }
      }
      return;
    }
    // ---- 猎聘liepin列表（直接定位pc-search-job API，提取jobCardList）----
    if (u.indexOf('liepin.com') !== -1) {
      var lp = safeParse(text);
      if (lp) {
        state.liepin.raw.push({ url: u, data: lp, time: nowStr() });
        // 专门处理岗位搜索API: data.data.data.jobCardList
        if (u.indexOf('pc-search-job') !== -1 && u.indexOf('cond-init') === -1) {
          try {
            var lpCards = lp && lp.data && lp.data.data && lp.data.data.jobCardList;
            if (lpCards && lpCards.length) {
              var lpb2 = state.liepin, lpadded2 = 0;
              lpCards.forEach(function (card) {
                if (!card || !card.job) return;
                var lpid = card.job.jobId || (card.dataParams && JSON.parse(card.dataParams).jobId);
                if (!lpid) return;
                if (!lpb2.jobs[lpid]) {
                  card.jobId = String(lpid);
                  card.__platform = '猎聘';
                  lpb2.jobs[lpid] = card;
                  lpb2.order.push(lpid);
                  lpadded2++;
                }
              });
              if (lpadded2 > 0) refreshPanel('猎聘 +' + lpadded2);
            }
          } catch (e) {}
        }
      }
      return;
    }
  }

  var _fetch = window.fetch;
  if (_fetch) {
    window.fetch = function () {
      var args = arguments, url = args[0]; if (url && url.url) url = url.url;
      var p = _fetch.apply(this, args);
      return p.then(function (res) { try { res.clone().text().then(function (t) { ingest(url, t); }); } catch (e) {} return res; });
    };
  }
  var _open = XMLHttpRequest.prototype.open, _send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__u = u; return _open.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function () {
    var self = this;
    this.addEventListener('readystatechange', function () { if (self.readyState === 4) { try { ingest(self.__u, self.responseText); } catch (e) {} } });
    return _send.apply(this, arguments);
  };

  function bossJobs() { return state.boss.order.map(function (id) { return state.boss.jobs[id]; }); }
  function zhJobs() { return state.zh.order.map(function (id) { return state.zh.jobs[id]; }); }
  function job51Jobs() { return state.job51.order.map(function (id) { return state.job51.jobs[id]; }); }
  function liepinJobs() { return state.liepin.order.map(function (id) { return state.liepin.jobs[id]; }); }

  // ============ BOSS 补全JD（拟人节奏，可停止）============
  async function fillDetails() {
    if (filling) return;
    var ids = state.boss.order.slice();
    var todo = ids.filter(function (id) { return !state.boss.jobs[id].__detail && state.boss.jobs[id].securityId; });
    if (!ids.length) { flash('还没抓到BOSS岗位'); return; }
    if (!todo.length) { flash('BOSS岗位都已有JD'); return; }
    filling = true; stopFlag = false;
    var stopBtn = panelEl.querySelector('#__bc_stop'); if (stopBtn) stopBtn.style.display = 'inline-block';
    var done = 0, fail = 0, processed = 0;
    for (var k = 0; k < ids.length; k++) {
      if (stopFlag) break;
      var job = state.boss.jobs[ids[k]];
      if (job.__detail || !job.securityId) { if (!job.securityId) fail++; continue; }
      processed++;
      try {
        var r = await _fetch(BOSS_DETAIL + '?securityId=' + encodeURIComponent(job.securityId), { credentials: 'include' });
        var d = await r.json();
        if (d && d.code === 0 && d.zpData) { job.__detail = d.zpData; done++; } else { fail++; }
      } catch (e) { fail++; }
      if (fillEl) fillEl.textContent = '补全中 ' + processed + '/' + todo.length + '  ✓' + done + ' ✗' + fail;
      var wait = 6000 + Math.random() * 5000;
      if (processed % 10 === 0) wait += 15000 + Math.random() * 10000;
      await sleep(wait);
    }
    filling = false;
    if (stopBtn) stopBtn.style.display = 'none';
    if (fillEl) fillEl.textContent = (stopFlag ? '已停止·' : '补全完成·') + 'BOSS JD ' + detailDone() + '/' + state.boss.order.length + '（失败' + fail + '）';
  }


  // ============ 猎聘 补全JD（fetch详情页HTML，提取schema.org JobPosting）============
  async function fillLiepinDetails() {
    if (filling) return;
    var ids = state.liepin.order.slice();
    var todo = ids.filter(function (id) { return !state.liepin.jobs[id].__detail; });
    if (!ids.length) { flash('还没抓到猎聘岗位'); return; }
    if (!todo.length) { flash('猎聘岗位都已有JD'); return; }
    filling = true; stopFlag = false;
    var stopBtn = panelEl.querySelector('#__bc_stop'); if (stopBtn) stopBtn.style.display = 'inline-block';
    var done = 0, fail = 0, processed = 0;
    for (var k = 0; k < ids.length; k++) {
      if (stopFlag) break;
      var job = state.liepin.jobs[ids[k]];
      if (job.__detail) { continue; }
      processed++;
      try {
        var jobId = job.jobId || (job.dataParams && JSON.parse(job.dataParams).jobId);
        if (!jobId) { fail++; continue; }
        var detailUrl = 'https://www.liepin.com/lptjob/' + jobId;
        var r = await _fetch(detailUrl, { credentials: 'include' });
        var html = await r.text();
        // 提取 schema.org JobPosting 的 description
        var jd = '';
        var m = html.match(/"@type"\s*:\s*"JobPosting"[\s\S]*?"description"\s*:\s*"((?:[^"\\]|\\.)*)"/);
        if (m && m[1]) {
          jd = m[1].replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\"/g, '"');
        }
        if (jd) {
          job.__detail = { description: jd, source: 'schema_org', url: detailUrl };
          done++;
        } else {
          fail++;
        }
      } catch (e) { fail++; }
      if (fillEl) fillEl.textContent = '猎聘补全中 ' + processed + '/' + todo.length + '  ✓' + done + ' ✗' + fail;
      var wait = 6000 + Math.random() * 5000;
      if (processed % 10 === 0) wait += 15000 + Math.random() * 10000;
      await sleep(wait);
    }
    filling = false;
    if (stopBtn) stopBtn.style.display = 'none';
    var lpDone = state.liepin.order.filter(function (id) { return state.liepin.jobs[id].__detail; }).length;
    if (fillEl) fillEl.textContent = (stopFlag ? '已停止·' : '补全完成·') + '猎聘 JD ' + lpDone + '/' + state.liepin.order.length + '（失败' + fail + '）';
  }

  // ============ 导出（双平台信封，兼容BOSS旧解析）============
  function exportJSON() {
    var bj = bossJobs(), zj = zhJobs(), j5j = job51Jobs(), lpj = liepinJobs();
    if (!bj.length && !zj.length && !j5j.length && !lpj.length && !state.job51.raw.length && !state.liepin.raw.length) { flash('还没有捕获到岗位'); return; }
    var meta = {};
    try { var uu = new URL(location.href); meta = { url: location.href, host: location.host, query: uu.searchParams.get('kw') || uu.searchParams.get('query') || '' }; } catch (e) { meta = { url: location.href, host: location.host }; }
    var payload = {
      platform: 'multi', capture_method: 'edge_extension_passive', exported_at: nowStr(),
      meta: meta, total: bj.length + zj.length + j5j.length,
      boss_count: bj.length, zhaopin_count: zj.length, job51_count: j5j.length, liepin_count: lpj.length, boss_with_detail: detailDone(),
      zpData: { jobList: bj },
      zhaopin_jobs: zj,
      job51_jobs: j5j,
      job51_raw: state.job51.raw,
      liepin_jobs: lpj,
      liepin_raw: state.liepin.raw
    };
    var blob = new Blob([JSON.stringify(payload)], { type: 'application/json;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '岗位采集_BOSS' + bj.length + '_智联' + zj.length + '_51job' + j5j.length + '_猎聘' + lpj.length + '_' + nowStr().replace(/[: ]/g, '-') + '.json';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    flash('已导出 BOSS ' + bj.length + ' / 智联 ' + zj.length + ' / 51job ' + j5j.length + ' / 猎聘 ' + lpj.length + '(原始' + state.liepin.raw.length + ')');
  }
  function clearStore() { state = { boss: { jobs: {}, order: [] }, zh: { jobs: {}, order: [] }, job51: { jobs: {}, order: [], raw: [] }, liepin: { jobs: {}, order: [], raw: [] } }; refreshPanel(null, null, true); flash('已清空'); }

  // ============ 面板 ============
  function refreshPanel(msg, _, isClear) {
    if (!panelEl) return;
    if (countEl) countEl.innerHTML = 'BOSS <b style="color:#0969da">' + state.boss.order.length + '</b>（JD ' + detailDone() + '）<br>智联 <b style="color:#1a7f37">' + state.zh.order.length + '</b><br>51job <b style="color:#bf8700">' + state.job51.order.length + '</b><br>猎聘 <b style="color:#7b1fa2">' + state.liepin.order.length + '</b>（原始' + state.liepin.raw.length + '）';
    if (lastEl) lastEl.textContent = isClear ? '等待搜索/翻页' : (msg ? (msg + '  ' + nowHM()) : nowHM());
    if (isClear && fillEl) fillEl.textContent = '';
  }
  function flash(msg) {
    if (!panelEl) return;
    var t = document.createElement('div'); t.textContent = msg;
    t.style.cssText = 'margin-top:4px;font-size:12px;color:#1a7f37;';
    panelEl.appendChild(t); setTimeout(function () { t.remove(); }, 2500);
  }
  function buildPanel() {
    if (panelEl || !document.body) return;
    var box = document.createElement('div');
    box.id = '__boss_cap_panel';
    box.style.cssText = 'position:fixed;top:90px;right:16px;z-index:2147483647;width:220px;background:#fff;border:1px solid #d0d7de;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:10px;font:13px/1.5 "Microsoft YaHei",sans-serif;color:#1f2328;user-select:none;';
    box.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;cursor:move;margin-bottom:6px;">' +
      '<b style="font-size:13px;">🎯 四平台采集</b><span id="__bc_min" style="cursor:pointer;color:#57606a;">—</span></div>' +
      '<div id="__bc_count" style="font-size:13px;font-weight:bold;color:#1f2328;line-height:1.5;">BOSS <b style="color:#0969da">0</b>（JD 0）<br>智联 <b style="color:#1a7f37">0</b><br>51job <b style="color:#bf8700">0</b><br>猎聘 <b style="color:#7b1fa2">0</b>（原始0）</div>' +
      '<div id="__bc_last" style="font-size:11px;color:#57606a;margin:2px 0 4px;min-height:14px;">等待搜索/翻页</div>' +
      '<div id="__bc_fillp" style="font-size:11px;color:#9a6700;margin:0 0 6px;min-height:14px;"></div>' +
      '<button id="__bc_fill" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#bf8700;color:#fff;cursor:pointer;font-size:13px;">补全BOSS的JD</button>' +
      '<button id="__bc_fill_lp" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#7b1fa2;color:#fff;cursor:pointer;font-size:13px;">补全猎聘JD</button>' +
      '<button id="__bc_stop" style="width:100%;padding:5px;margin-bottom:5px;border:1px solid #d0d7de;border-radius:6px;background:#f6f8fa;cursor:pointer;font-size:12px;display:none;">停止补全</button>' +
      '<button id="__bc_exp" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#0969da;color:#fff;cursor:pointer;font-size:13px;">导出JSON</button>' +
      '<button id="__bc_clr" style="width:100%;padding:5px;border:1px solid #d0d7de;border-radius:6px;background:#f6f8fa;cursor:pointer;font-size:12px;">清空重抓</button>' +
      '<div style="font-size:10px;color:#8c959f;margin-top:6px;line-height:1.4;">在BOSS/智联/51job/猎聘页面滚动自动抓；不自动投递</div>';
    document.body.appendChild(box);
    panelEl = box; countEl = box.querySelector('#__bc_count'); lastEl = box.querySelector('#__bc_last'); fillEl = box.querySelector('#__bc_fillp');
    box.querySelector('#__bc_exp').onclick = exportJSON;
    box.querySelector('#__bc_clr').onclick = clearStore;
    box.querySelector('#__bc_fill').onclick = fillDetails;
    box.querySelector('#__bc_fill_lp').onclick = fillLiepinDetails;
    box.querySelector('#__bc_stop').onclick = function () { stopFlag = true; this.textContent = '正在停止…'; };
    var body = box;
    box.querySelector('#__bc_min').onclick = function () {
      var nodes = box.querySelectorAll('div,button'); var hidden = body.dataset.h === '1';
      for (var i = 2; i < nodes.length; i++) nodes[i].style.display = hidden ? '' : 'none';
      body.dataset.h = hidden ? '0' : '1'; this.textContent = hidden ? '—' : '+';
    };
    var bar = box.firstElementChild, sx = 0, sy = 0, ox = 0, oy = 0, drag = false;
    bar.onmousedown = function (e) { drag = true; sx = e.clientX; sy = e.clientY; var r = box.getBoundingClientRect(); ox = r.left; oy = r.top; e.preventDefault(); };
    document.addEventListener('mousemove', function (e) { if (!drag) return; box.style.left = (ox + e.clientX - sx) + 'px'; box.style.top = (oy + e.clientY - sy) + 'px'; box.style.right = 'auto'; });
    document.addEventListener('mouseup', function () { drag = false; });
  }
  var iv = setInterval(function () { if (document.body) { buildPanel(); clearInterval(iv); } }, 200);

  window.__cap = { export: exportJSON, clear: clearStore, fillBoss: fillDetails, boss: bossJobs, zh: zhJobs, job51: job51Jobs, liepin: liepinJobs };
})();
