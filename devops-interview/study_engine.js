// ================= STUDY =================
// The reference half of the app: the syllabus as pages you can read in any order.
// Learn mode teaches and gates; this one just explains, and checks at the end that
// the page went in. Blocks render through the Learn mode's renderer.
const STUDY=(()=>{ const el=$('studydata'); if(!el) return {chapters:[]};
  try{ return JSON.parse(el.textContent); }catch(e){ return {chapters:[]}; } })();
const STU_CH=STUDY.chapters||[];
// Each chapter carries the question sectors it covers and its domain (build_study.py
// checks every sector belongs to exactly one chapter), so the weights add up to the
// whole bank and the card colour means the same thing as everywhere else in the app.
const STU_DOM=STU_CH.map(c=>c.dom|0);
const STU_SECS=STU_CH.map(c=>c.secs||[]);
function stuWeight(i){
  const secs=STU_SECS[i]||[];
  const n=secs.reduce((a,s)=>a+((bySec[s]||[]).length),0);
  return {n, pct:QS.length?Math.round(n/QS.length*1000)/10:0, secs};
}
// how well you have done on the sectors a chapter covers, and how much of it you have seen
function stuMastery(i){
  let a=0,c=0,pool=0;
  (STU_SECS[i]||[]).forEach(s=>{
    const st=(P.secStats||{})[s]; if(st){ a+=st.a; c+=st.c; }
    pool+=(bySec[s]||[]).length;
  });
  return {a, c, pool, acc:a?Math.round(c/a*100):0, seen:pool?Math.round(Math.min(1,a/pool)*100):0};
}
let stuIdx=-1;

function stuRec(i){ return (P.study||{})[i]||null; }
function stuMarkRead(i){
  P.study=P.study||{};
  const r=P.study[i]||{read:0,best:0};
  r.read=1; r.at=dayKey(); P.study[i]=r; saveProfile();
}
function stuMarkQuiz(i,pct){
  P.study=P.study||{};
  const r=P.study[i]||{read:0,best:0};
  r.read=1; r.best=Math.max(r.best||0,pct); r.at=dayKey(); P.study[i]=r; saveProfile();
}
function renderStudyPick(){
  const L=$('stuPickList'); if(!L) return;
  L.innerHTML='';
  const read=STU_CH.filter((c,i)=>stuRec(i)&&stuRec(i).read).length;
  const aced=STU_CH.filter((c,i)=>stuRec(i)&&stuRec(i).best>=100).length;
  const mins=STU_CH.reduce((a,c)=>a+c.min,0);
  $('stuStats').innerHTML=
    '<div class="stat"><b>'+read+' / '+STU_CH.length+'</b><span>Chapters read</span></div>'+
    '<div class="stat"><b>'+aced+'</b><span>Checks aced</span></div>'+
    '<div class="stat"><b>'+mins+'m</b><span>Whole syllabus</span></div>';
  const mb=$('stuMotiv');
  if(mb) mb.innerHTML='<span class="mem">\u{1f4da}</span>'+hebHTML('daily',read+3);
  STU_CH.forEach((c,i)=>{
    const rec=stuRec(i);
    const b=document.createElement('button'); b.className='stucard';
    b.style.setProperty('--dcol',DOMAIN_COL[STU_DOM[i]]||'var(--cyan)');
    b.innerHTML='<span class="sem">'+c.em+'</span>'+
      '<span style="flex:1;min-width:0"><span class="snm">'+esc(c.nm)+'</span>'+
      '<div class="ssub">'+esc(c.sub)+'</div>'+
      '<div class="smeta">'+c.topics.length+' topics · '+c.min+' min read · '+
      c.quiz.length+' checks'+(rec&&rec.best?' · check '+(Number(rec.best)|0)+'%':'')+'</div>'+
      stuWeightHTML(i)+'</span>'+
      (rec&&rec.read?'<span class="studone">✓ read</span>':'');
    b.onclick=()=>stuOpen(i);
    L.appendChild(b);
  });
}
// The number a learner actually wants: how much of the exam this chapter is, and
// how much of it they have already proved they know.
function stuWeightHTML(i){
  const w=stuWeight(i), m=stuMastery(i);
  if(!w.n) return '';
  const band=w.pct>=10?'heavy':w.pct>=5?'mid':'light';
  return '<div class="stuw '+band+'">'+
    '<div class="wbar"><i style="width:'+pctW(w.pct*6)+'"></i></div>'+
    '<div class="wtxt"><b>'+w.pct+'%</b> of the exam · '+w.n+' questions'+
    (m.a?' · you are '+m.acc+'% right on '+m.a+' of them':' · none attempted yet')+
    '</div></div>';
}
function stuOpen(i){
  if(i<0||i>=STU_CH.length) return;
  stuIdx=i;
  const c=STU_CH[i];
  $('stuTag').textContent='CHAPTER '+(i+1)+' / '+STU_CH.length;
  $('stuCount').textContent=c.topics.length+' topics · '+c.min+' min';
  $('stuTitle').textContent=c.em+'  '+c.nm;
  $('stuSub').textContent=c.sub;
  const w=stuWeight(i), m=stuMastery(i);
  $('stuWeight').innerHTML=w.n
    ? '<div class="stat"><b>'+w.pct+'%</b><span>Of the exam</span></div>'+
      '<div class="stat"><b>'+w.n+'</b><span>Questions</span></div>'+
      '<div class="stat"><b>'+(m.a?m.acc+'%':'—')+'</b><span>You are right</span></div>'
    : '';
  const jump=$('stuJump'); jump.innerHTML='';
  c.topics.forEach((t,k)=>{
    const b=document.createElement('button'); b.textContent=t.nm; b.dataset.topic=k;
    b.onclick=()=>{ const el=$('stuT'+k); if(el) el.scrollIntoView({behavior:'smooth',block:'start'}); };
    jump.appendChild(b);
  });
  stuJumpSync();
  if(ttsOn&&ttsOwner==='para') ttsStop();       // a new chapter: the old paragraph stops
  $('stuBody').innerHTML=c.topics.map((t,k)=>
    '<section class="stutopic" id="stuT'+k+'"><h2>'+esc(t.nm)+'</h2>'+studyBlocksHTML(t.blocks)+'</section>'
  ).join('');
  $('stuBody').querySelectorAll('.parread').forEach(b=>{ b.onclick=()=>paraRead(b); });
  stuRenderQuiz(c);
  $('stuNext').textContent=i<STU_CH.length-1?('Next: '+STU_CH[i+1].nm+' ▸'):'Back to chapters';
  stuMarkRead(i);
  go('stuReadScreen');
  const sc=$('stuReadScreen'); if(sc) sc.scrollTop=0;
}
// Marks which topic you are reading. The .on style existed from the start; nothing applied it.
function stuJumpSync(){
  const bar=$('stuJump'); if(!bar||!bar.children.length) return;
  const secs=[...document.querySelectorAll('#stuBody .stutopic')];
  if(!secs.length) return;
  const line=140;
  let cur=0;
  secs.forEach((el,k)=>{ if(el.getBoundingClientRect().top<=line) cur=k; });
  [...bar.children].forEach((b,k)=>b.classList.toggle('on',k===cur));
  const act=bar.children[cur];
  if(act&&bar.scrollWidth>bar.clientWidth){
    const want=act.offsetLeft-bar.clientWidth/2+act.offsetWidth/2;
    bar.scrollTo({left:Math.max(0,want),behavior:'smooth'});
  }
}
function stuRenderQuiz(c){
  const box=$('stuQuiz'); box.innerHTML='';
  const state={done:0,right:0};
  c.quiz.forEach((q,qi)=>{
    const card=document.createElement('div'); card.className='stuq';
    const opts=q.o.map((o,oi)=>'<button class="stuo" data-i="'+oi+'">'+qtx(o)+'</button>').join('');
    card.innerHTML='<div class="qq">'+qtx(q.q)+'</div>'+opts+'<div class="stufeed"></div>';
    const feed=card.querySelector('.stufeed');
    [...card.querySelectorAll('.stuo')].forEach(btn=>{
      btn.onclick=()=>{
        if(card.dataset.done) return;
        card.dataset.done='1';
        const picked=+btn.dataset.i, ok=picked===q.a;
        [...card.querySelectorAll('.stuo')].forEach((b2,i2)=>{
          b2.disabled=true;
          if(i2===q.a) b2.classList.add('ok');
          else if(i2===picked) b2.classList.add('no');
        });
        feed.innerHTML=(ok?'✓ Correct. ':'✗ The answer is '+qtx(q.o[q.a])+'. ')+
          (q.x?'<span class="stux">'+qtx(q.x)+'</span>':hebHTML(ok?'right':'wrong'));
        state.done++; if(ok){ state.right++; sfx.right(); } else sfx.wrong();
        if(state.done===c.quiz.length){
          const pct=Math.round(state.right/c.quiz.length*100);
          stuMarkQuiz(stuIdx,pct);
          addXP(state.right*8); addCoins(state.right*2);
          toast('Quick check — '+state.right+' / '+c.quiz.length);
          checkBadges();
        }
      };
    });
    box.appendChild(card);
  });
}
function stuNext(){
  if(stuIdx<STU_CH.length-1) stuOpen(stuIdx+1);
  else { renderStudyPick(); go('stuPickScreen'); }
}
function stuPractise(){
  // practise the chapter's weakest sector so far, or its first one if none is attempted yet
  const secs=STU_SECS[stuIdx]||[];
  let pick=secs.length?secs[0]:-1, worst=2;
  secs.forEach(s=>{
    const st=(P.secStats||{})[s];
    if(st&&st.a&&st.c/st.a<worst){ worst=st.c/st.a; pick=s; }
  });
  startSession(pick);
}
function openStudy2(){ renderStudyPick(); go('stuPickScreen'); }
$('stuPickBack').onclick=()=>{ go('homeScreen'); renderHome(); };
$('stuReadBack').onclick=()=>{ renderStudyPick(); go('stuPickScreen'); };
$('stuNext').onclick=stuNext;
$('stuPractise').onclick=stuPractise;
const STUDY_T={ STUDY, STU_CH, STU_SECS, get stuIdx(){return stuIdx;}, stuOpen, stuNext,
  stuPractise, renderStudyPick, stuRec, openStudy2, stuRenderQuiz, stuWeight, stuMastery,
  stuWeightHTML };
