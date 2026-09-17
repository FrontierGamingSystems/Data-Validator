const assert=require('node:assert/strict');
const {createApp}=require('./app-harness');
const a=createApp();
const cases=[];
for(const hall of ['rwc','sc']){
  a.run(`S.session={hall:'${hall}',date:'2026-09-17',weekday:'Thursday',time:'18:30',slot:'Thursday'};
    freshState(S.session);S.pm.adj=[{n:'Refunds',v:90},{n:'Rounding-Up Splits',v:10},{n:'Flash Payout Unclaimed',v:0}];compute()`);
  const baseline=a.json('({payouts:T.payouts,os:T.os,pm:T.stationOS.Paymaster,net:T.net,other:T.notAtPaymaster,small:T.runnerSmFlash})');
  for(const value of [0,250,-250,250.75,-250.75]){
    a.run(`S.pm.adj[2].v=${value};compute()`);
    const reduction=Math.abs(value);
    assert.equal(a.run('T.pmAdj'),100-reduction);
    assert.equal(a.run('T.payouts'),baseline.payouts-reduction);
    assert.equal(a.run('T.net'),baseline.net+reduction);
    assert.equal(a.run('T.os'),baseline.os-reduction);
    assert.equal(a.run('T.stationOS.Paymaster'),baseline.pm-reduction);
    assert.equal(a.run('T.notAtPaymaster'),baseline.other);
    assert.equal(a.run('T.runnerSmFlash'),baseline.small);
    const snap=a.json('snapshot()');
    assert.equal(snap.payout_lines.find(x=>x.label==='Flash Game Payout Un-Claimed').amount,0-reduction);
    assert.equal(snap.payout_lines.find(x=>x.label==='Refunds').amount,90);
    assert.equal(snap.payout_lines.find(x=>x.label==='Rounding Up Game Splits').amount,10);
    const html=a.run('vPaymaster()');
    assert.match(html,/Automatically subtracted from payouts/);
    if(value===250||value===-250) assert.match(html,/Flash Payout Unclaimed<\/td><td class="n">\(\$250\)<\/td>/);
    cases.push({hall,value,snap});
    a.sandbox.restoreInput=snap;
    a.run('applySnapshot(restoreInput);compute()');
    assert.equal(a.run('T.payouts'),baseline.payouts-reduction,'same result after reopening');
  }
  a.run("S.pm.adj=[{n:'Refunds',v:-15},{n:'Rounding-Up Splits',v:2}];compute()");
  assert.equal(a.run('T.pmAdj'),-13,'other adjustments retain their signs');
}
if(process.argv.includes('--json')) process.stdout.write(JSON.stringify(cases));
else console.log('PASS unclaimed flash: both halls, positive/negative/zero/cents, totals, drawer display, exports, reopening, other adjustments');
