const assert=require('node:assert/strict');const {createApp}=require('./app-harness');
const a=createApp();
a.run(`S.session={hall:'sc',date:'2026-09-01',weekday:'Tuesday',time:'18:30',slot:'Tuesday'};freshState(S.session);
 globalThis.saved=JSON.parse(JSON.stringify(snapshot()));
 saved.state.session.date='2026-08-01';saved.session.date='2026-08-01';
 delete saved.state.cherryPay;delete saved.state.cherryDep;delete saved.state.notes;
 delete saved.state.bonus.extra;delete saved.state.pm.wheel;
 saved.counts={online_attendance:10};saved.state.pm.redeem[0].v=123;
 S.cherryPay[0].v=777;S.cherryDep=999;S.notes={cash:'Another night'};COUNTS.pos_attendance=44;
 S.bonus.extra=[{n:'Wrong night',v:500}];S.pm.wheel=[{n:'Wrong night',v:600}];
 S.unrecognizedOldField='Must not leak';DATA.flash.push({game_name:'Wrong night'});
 applySnapshot(saved);compute();`);
assert.equal(a.run('T.cherryPaid'),0);assert.equal(a.run('S.cherryDep'),'');
assert.deepEqual(a.json('S.notes'),{});assert.equal(a.run('T.attendance'),10);
assert.deepEqual(a.json('S.bonus.extra'),[]);assert.deepEqual(a.json('S.pm.wheel'),[]);
assert.equal(a.run('S.unrecognizedOldField'),undefined);
assert.equal(a.run('DATA.flash.length'),0);
assert.equal(a.run('S.pm.redeem[0].v'),123,'keep this night\'s saved entries');
// Loading a current snapshot must preserve its money, counts, notes and approvals.
a.run(`S.cherryPay[0].v=400;S.cherryDep=500;S.notes={cherry:'Saved here'};
 S.bonus.extra=[{n:'Saved sale',v:20}];S.pm.wheel=[{n:'Saved prize',v:30}];
 S.status.cherry='approved';globalThis.before=JSON.parse(JSON.stringify(snapshot()));
 applySnapshot(snapshot());compute();`);
for(const field of ['cherryPay','cherryDep','notes','bonus','pm','status'])
 assert.deepEqual(a.json('S.'+field),a.json('before.state.'+field),field);
assert.equal(a.run('S.session.date'),'2026-08-01');
console.log('PASS older-night defaults, nested fields, unrelated data removal and current-night round trip');
