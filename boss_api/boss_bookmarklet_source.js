// BOSS直聘岗位采集器 —— 纯Bookmarklet源码（免安装油猴时使用）
// 由 build_bookmarklet.py 压缩转码为 javascript: 书签，并生成可拖拽安装的HTML
(function () {
  if (window.__bossCapLoaded) { alert('采集器已在运行，看右上角浮动面板'); return; }
  window.__bossCapLoaded = true;
  var LIST_API = '/wapi/zpgeek/search/joblist.json';
  var state = { jobs: {}, order: [] };
  var panelEl, countEl, lastEl, autoOn = false, autoLeft = 0;

  function parse(t){ try{return JSON.parse(t);}catch(e){return null;} }
  function now(){ var d=new Date(),p=function(n){return(n<10?'0':'')+n;}; return p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds()); }
  function ingest(url, text){
    if(!text||(''+url).indexOf(LIST_API)===-1) return;
    var o=parse(text); if(!o||o.code!==0) return;
    var list=(o.zpData&&o.zpData.jobList)||[], added=0;
    for(var i=0;i<list.length;i++){ var j=list[i], id=j.encryptJobId||(j.brandName+'|'+j.jobName);
      if(!state.jobs[id]){state.jobs[id]=j;state.order.push(id);added++;} }
    refresh(added,list.length);
  }
  var _f=window.fetch;
  if(_f){window.fetch=function(){var a=arguments,u=a[0];if(u&&u.u)u=u.u;var p=_f.apply(this,a);
    return p.then(function(r){try{r.clone().text().then(function(t){ingest(u,t);});}catch(e){}return r;});};}
  var _o=XMLHttpRequest.prototype.open,_s=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return _o.apply(this,arguments);};
  XMLHttpRequest.prototype.send=function(){var self=this;
    this.addEventListener('readystatechange',function(){if(self.readyState===4){try{ingest(self.__u,self.responseText);}catch(e){}}});
    return _s.apply(this,arguments);};

  function collect(){ return state.order.map(function(id){return state.jobs[id];}); }
  function exportJSON(){
    var jobs=collect();
    if(!jobs.length){alert('还没捕获到岗位：请先点"开始自动翻页"或手动翻页');return;}
    var q='';try{q=new URL(location.href).searchParams.get('query')||'';}catch(e){}
    var payload={platform:'BOSS直聘',capture_method:'bookmarklet_passive',exported_at:new Date().toISOString(),
      total:jobs.length,code:0,message:'Success',zpData:{jobList:jobs}};
    var blob=new Blob([JSON.stringify(payload)],{type:'application/json;charset=utf-8'});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);
    a.download='boss岗位_'+q+'_'+jobs.length+'条.json';document.body.appendChild(a);a.click();
    setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1000);
  }
  // 点击页面"原生"下一页按钮（让页面自己发请求，不注入XHR，规避code37）
  function clickNativeNext(){
    var cands=document.querySelectorAll('a,button,li,.ui-icon-arrow-right,[class*=next],[class*=Next]');
    for(var i=0;i<cands.length;i++){var el=cands[i],t=(el.textContent||'').trim();
      if((t==='下一页'||t==='>'||/next/i.test(el.className))&&!el.classList.contains('disabled')&&el.offsetParent!==null){el.click();return true;}}
    return false;
  }
  function autoLoop(n){
    autoOn=true;autoLeft=n;
    function step(){
      if(!autoOn||autoLeft<=0){lastEl.textContent='自动翻页结束，共'+state.order.length+'条';return;}
      var ok=clickNativeNext();autoLeft--;
      lastEl.textContent='自动翻页中…剩余约'+autoLeft+'页，当前'+state.order.length+'条';
      if(!ok){lastEl.textContent='没有找到下一页按钮（已到底），共'+state.order.length+'条';autoOn=false;return;}
      setTimeout(step, 9000+Math.floor(Math.random()*6000)); // 9-15秒拟人间隔
    }
    step();
  }

  function refresh(added,total){ if(!panelEl)return; countEl.textContent=state.order.length+' 个岗位';
    if(added>0)lastEl.textContent='本页+'+added+'（共'+total+'） '+now(); }
  function build(){
    if(panelEl||!document.body)return;
    var box=document.createElement('div');
    box.style.cssText='position:fixed;top:90px;right:16px;z-index:2147483647;width:180px;background:#fff;border:1px solid #d0d7de;border-radius:10px;box-shadow:0 4px 16px rgba(0,0,0,.15);padding:10px;font:13px/1.5 "Microsoft YaHei",sans-serif;color:#1f2328;';
    box.innerHTML='<b style="display:block;margin-bottom:6px;">🎯 岗位采集(书签)</b>'+
      '<div id="__bc_c" style="font-size:15px;font-weight:bold;color:#0969da;">0 个岗位</div>'+
      '<div id="__bc_l" style="font-size:11px;color:#57606a;margin:2px 0 8px;min-height:14px;">等待翻页</div>'+
      '<button id="__bc_a5" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#1a7f37;color:#fff;cursor:pointer;">自动翻5页并采集</button>'+
      '<button id="__bc_e" style="width:100%;padding:6px;margin-bottom:5px;border:0;border-radius:6px;background:#0969da;color:#fff;cursor:pointer;">导出JSON</button>'+
      '<button id="__bc_x" style="width:100%;padding:5px;border:1px solid #d0d7de;border-radius:6px;background:#f6f8fa;cursor:pointer;">清空</button>'+
      '<div style="font-size:10px;color:#8c959f;margin-top:6px;line-height:1.4;">也可手动翻页，自动捕获；不自动投递</div>';
    document.body.appendChild(box);panelEl=box;countEl=box.querySelector('#__bc_c');lastEl=box.querySelector('#__bc_l');
    box.querySelector('#__bc_a5').onclick=function(){autoLoop(5);};
    box.querySelector('#__bc_e').onclick=exportJSON;
    box.querySelector('#__bc_x').onclick=function(){state={jobs:{},order:[]};refresh(0,0);lastEl.textContent='已清空';};
  }
  var iv=setInterval(function(){if(document.body){build();clearInterval(iv);}},200);
  window.__bossCapture={export:exportJSON,jobs:collect};
})();
