const assert=require('node:assert/strict');
const {createApp}=require('./app-harness');
const a=createApp();
a.run(`DATA.sales.length=0;DATA.sales.push(
  {channel:'online',category:'Flash',item_name:'Casino City (RWC)',qty:80,value:160},
  {channel:'online',category:'Flash',item_name:'Casino City',qty:10,value:20},
  {channel:'online',category:'Strips',item_name:'Casino City',qty:6,value:120},
  {channel:'pos',category:'Flash',item_name:'Casino City',qty:10,value:20},
  {channel:'online',category:'Flash',item_name:'Big Fish',qty:60,value:60},
  {channel:'online',category:'Strips',item_name:'Diamonds & Emeralds',qty:6,value:120},
  {channel:'online',category:'Flash',item_name:'Refunded game',value:20},
  {channel:'online',category:'Flash',item_name:'Refunded game',value:-20});`);
assert.equal(a.run("fxPreSoldValue({name:'Casino City',presold:90})"),180,'$2 flash uses dollars, excluding other categories and channels');
assert.equal(a.run("fxPreSoldValue({name:'Big Fish',presold:60})"),60,'$1 games retain their value');
assert.equal(a.run("fxPreSoldValue({name:'Diamonds & Emeralds',presold:60})"),120,'legacy scheduled flash games can carry the old Strips label');
assert.equal(a.run("fxPreSoldValue({name:'Old game',presold:40})"),40,'older sessions without matching sales retain the legacy $1 fallback');
assert.equal(a.run("fxPreSoldValue({name:'Refunded game',presold:20})"),0,'matched net-zero sales must remain zero');
assert.equal(a.run("fxPreSoldValue({name:'Casino City',presold:0})"),0);
console.log('PASS flash sales: $1/$2, multiple rows, category/channel separation, refunds, older nights and legacy product labels');

// Real pre-sale records, not invented category labels: 40 $2 tickets = $80.
const fs=require('node:fs'),path=require('node:path');
const real=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/rwc-2026-08-04.json'),'utf8'));
a.sandbox.real=real;
a.run('applySessionData(real);S.session={hall:"rwc",date:"2026-08-04",weekday:"Tuesday",time:"18:30",slot:"Tuesday"};freshState(S.session);compute()');
assert.equal(a.run('T.fxSoldPre'),400,'real advance sales dollars, including the $2 game');
assert.equal(a.run('S.flashPre.reduce((n,f)=>n+Number(f.presold),0)'),360,'the real ticket count differs from dollars');
console.log('PASS historical August 4 sales: 360 tickets, $400 advance sales');
