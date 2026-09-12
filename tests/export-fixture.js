const {createApp}=require('./app-harness');const a=createApp();
a.run(`S.session={hall:'rwc',date:'2026-09-01',weekday:'Tuesday',time:'18:30',slot:'Tuesday'};freshState(S.session);
 DATA.sales.length=0;DATA.sales.push(
 {channel:'online',category:'Flash',item_name:'Casino City',qty:80,value:160},
 {channel:'online',category:'Strips',item_name:'Casino City',qty:6,value:120},
 {channel:'online',category:'Flash',item_name:'Big Fish',qty:60,value:60});
 S.flashPre=[{name:'Casino City',presold:80,tickets:3920,boxes:1},
 {name:'Big Fish',presold:60,tickets:1995,boxes:1}];S.flashOnsite=[];
 S.runners=[{name:'Runner',checkouts:[5695],returned:[0],unsold:[0],cash:[5695],credit:[0],
 smFlash:[0],smCherry:[0],lgFlash:[0],lgCherry:[0],buyin:[0],start:0}];compute();`);
if(process.argv.includes('--historical')){
 const fs=require('node:fs'),path=require('node:path');
 a.sandbox.real=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/rwc-2026-08-04.json'),'utf8'));
 a.run('applySessionData(real);S.session={hall:"rwc",date:"2026-08-04",weekday:"Tuesday",time:"18:30",slot:"Tuesday"};freshState(S.session);compute()');
}
process.stdout.write(JSON.stringify(a.json('snapshot()')));
