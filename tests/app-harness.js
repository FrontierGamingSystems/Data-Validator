// Real application code, controlled timers, and a network that is closed by default.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function createApp(options = {}) {
  const elements = {}, storage = options.storage || {}, timers = new Map();
  let timerId = 0;
  const el = id => elements[id] ||= {id, innerHTML:'', textContent:'', value:'', style:{}, dataset:{},
    classList:{add(){},remove(){},contains(){return false}}, querySelectorAll:()=>[], querySelector:()=>null,
    contains:()=>false, appendChild(){}, focus(){}, setSelectionRange(){}};
  const sandbox = {
    document:{getElementById:el,querySelectorAll:()=>[],querySelector:()=>null,addEventListener(){},
      createElement:()=>el('tmp'),body:el('body'),activeElement:null,title:''},
    window:{addEventListener(){},removeEventListener(){},print(){}},navigator:{userAgent:'test'},
    console,localStorage:{getItem:k=>storage[k]||null,setItem:(k,v)=>storage[k]=v,removeItem:k=>delete storage[k],
      key:i=>Object.keys(storage)[i]||null,get length(){return Object.keys(storage).length}},
    setTimeout:(fn,ms)=>{timers.set(++timerId,{fn,ms});return timerId},clearTimeout:id=>timers.delete(id),
    setInterval:()=>0,clearInterval(){},alert:()=>{},confirm:()=>true,prompt:()=>'',
    fetch:async()=>{throw new Error('Unexpected network request in test')},
    Date,Math,JSON,Object,Array,String,Number,Boolean,Set,Map,Intl,Promise,Error,RegExp,
    isNaN,isFinite,parseInt,parseFloat,encodeURIComponent,decodeURIComponent,btoa,atob,
    ...options.globals
  };
  sandbox.globalThis=sandbox;
  vm.createContext(sandbox);
  const html=fs.readFileSync(options.file || path.join(__dirname,'..','index.html'),'utf8');
  vm.runInContext(html.match(/<script>([\s\S]*)<\/script>/)[1],sandbox,{filename:'index.html'});
  const run=code=>vm.runInContext(code,sandbox);
  const json=code=>JSON.parse(run(`JSON.stringify(${code})`));
  const flush=async ms=>{const jobs=[...timers].filter(([,t])=>t.ms===ms);for(const [id,t] of jobs){timers.delete(id);await t.fn();}};
  return {run,json,sandbox,elements,storage,timers,flush};
}
module.exports={createApp};
