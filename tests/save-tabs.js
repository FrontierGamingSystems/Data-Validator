const assert=require('node:assert/strict');const {createApp}=require('./app-harness');
function init(a){a.run(`AUTH={email:'test',access_token:'stub',expires_at:Date.now()+3600000};
 S.session={hall:'rwc',date:'2026-09-01',weekday:'Tuesday',time:'18:30',slot:'Tuesday'};freshState(S.session);
 rememberSessionRow({...sessionRow(),id:'row',updated_at:'2026-09-01T01:00:00.000Z'});`);}
(async()=>{
 const storage={},a=createApp({storage}),b=createApp({storage});init(a);init(b);
 assert.notEqual(a.run('localSessionKey(S.session)'),b.run('localSessionKey(S.session)'));
 let release,server;
 a.sandbox.write=async(q,opts)=>new Promise(resolve=>{release=()=>{
   server={...JSON.parse(opts.body),id:'row'};resolve({ok:true,status:200,json:async()=>[server]});};});
 a.run('sbFetch=write;S.pm.redeem[0].v=111;saveNow()');
 const pending=a.run('dbSave()');await new Promise(setImmediate);
 b.run('S.pm.redeem[1].v=222;saveNow()');
 release();assert.equal(await pending,true);
 const raw=JSON.parse(storage[b.run('localSessionKey(S.session)')]);
 assert.equal(raw.state.pm.redeem[1].v,222);
 assert.equal(raw.sync.base.updated_at,'2026-09-01T01:00:00.000Z','A must never advance B\'s original version');
 assert.equal(raw.sync.dirty,true);
 // A's newer clean save must not hide B's unsaved backup after a reload.
 a.run('saveNow()');
 const c=createApp({storage});c.sandbox.server=server;
 c.run(`AUTH={email:'test',access_token:'stub',expires_at:Date.now()+3600000};
  dbLoad=async()=>server;fetchCommissionTerms=async()=>null;loadCatalogs=loadTicketRules=async()=>{};lastCherry=async()=>null;`);
 await c.run("resumeSession('rwc','2026-09-01','18:30')");
 assert.equal(c.run('S.pm.redeem[1].v'),222,'restore the unsaved tab');
 assert.equal(c.run('SAVE_CONFLICTS.has(sessionIdentity(S.session))'),true);
 assert.equal(await c.run('dbSave()'),false,'block replacing the saved $111 without explicit conflict resolution');
 assert.equal(server.state.pm.redeem[0].v,111);
 // Backups from earlier builds remain discoverable.
 const legacy={...raw,savedAt:'2099-01-01T00:00:00Z'};delete legacy.sync.owner;
 storage['recon:session:rwc|2026-09-01|18:30']=JSON.stringify(legacy);
 assert.equal(c.run('readLocalSnapshot(S.session).savedAt'),legacy.savedAt);
 console.log('PASS shared-tab saves, late acknowledgements, reload conflicts, dirty-backup discovery, older backups');
})().catch(e=>{console.error(e);process.exitCode=1;});
