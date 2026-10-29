// qa_progress.js — node test (not a page suite): does a stored profile survive a reworded bank?
// Run with the site served on :8765:  NODE_PATH=$(npm root -g) node qa_progress.js
// It loads the page three times with a profile already in localStorage: stamped with the
// current BANKV, with a compatible older stamp (BANKV_OK), and with an unknown stamp.
// The first two must keep seen/wrong/marks; the third must reset them.
const {chromium}=require('playwright');
(async()=>{
  const b=await chromium.launch(); const out={pass:0,fail:[]};
  const ok=(c,m)=>{ if(c) out.pass++; else out.fail.push(m); };
  async function boot(stamp){
    const p=await b.newPage();
    await p.addInitScript(s=>{
      const prof={bank:s, seen:{5:1,9:2}, wrong:[5], marks:[9], xp:777};
      try{ localStorage.setItem('shipit_profile', JSON.stringify(prof)); }catch(e){}
    }, stamp);
    await p.goto('http://localhost:8765/index.html?test=1'); await p.waitForTimeout(2500);
    const r=await p.evaluate(()=>{ const t=window.__t; return {bank:t.P.bank, v:t.BANKV, ok:t.BANKV_OK,
      seen:Object.keys(t.P.seen||{}).length, wrong:(t.P.wrong||[]).length, marks:(t.P.marks||[]).length, xp:t.P.xp}; });
    await p.close(); return r;
  }
  const probe=await b.newPage(); await probe.goto('http://localhost:8765/index.html?test=1'); await probe.waitForTimeout(2000);
  const {v,okv}=await probe.evaluate(()=>({v:window.__t.BANKV, okv:window.__t.BANKV_OK})); await probe.close();
  ok(Array.isArray(okv),'BANKV_OK is exposed as a list');
  const same=await boot(v);
  ok(same.seen===2&&same.wrong===1&&same.marks===1,'the current stamp keeps seen/wrong/marks');
  if(okv&&okv.length){
    const old=await boot(okv[0]);
    ok(old.seen===2&&old.wrong===1&&old.marks===1,'a compatible older stamp keeps seen/wrong/marks');
    ok(old.bank===v,'and the profile is restamped with the current version');
  }
  const unknown=await boot('not-a-real-version');
  ok(unknown.seen===0&&unknown.wrong===0&&unknown.marks===0,'an unknown stamp resets index-keyed progress');
  ok(unknown.xp===777,'but keeps the rest of the profile (XP)');
  console.log(JSON.stringify(out)); await b.close(); process.exit(out.fail.length?1:0);
})();
