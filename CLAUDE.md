# Ship It: DevOps interview prep (CLAUDE.md)

This is the handbook for every Claude session on this repo. Read it all before you touch anything.
Deeper detail: `devops-interview/PLAN.md` (decisions, distribution, sources) and `devops-interview/STATE.md`
(how the code works, plus engine notes inherited from Skyforge).

---

## 1. What the project is

**Ship It** is a static, single-page site that prepares one person, Nehoray (the owner), for **DevOps job interviews**.
It was made by copying **Skyforge**, an AWS SAA-C03 exam trainer (repo `NehorayM/neon-grid-aws`, live on GitHub Pages),
into `devops-interview/` and replacing all of its content.

- **From Skyforge:** the exam engine, per-question clocks, pause and resume, profile and XP, badges, themes, read-aloud,
  Supabase sync code, the casino and duel games, and the design system.
- **New:** every question, explanation, lesson, reference page and interview question, and the interview mode itself.

`devops-interview/index.html` is the whole site: one file, no build step to serve it. Content lives inside it as
JSON blobs that Python scripts generate from source files.

## 2. Working with Nehoray (process rules)

- **Reply in Hebrew.** Code, commit messages and docs stay in English.
- Work in **stages**. At the end of each stage: run all QA, commit, push, then give a short Hebrew summary
  (what was done, test numbers, anything open) and **ask before starting the next stage**.
- Don't re-open decisions in section 3 without asking. They were agreed with Nehoray before any work started.
- `main` holds stages 0–7. Use the branch the session assigns, or `main` if there is none. Push after every stage.
  Open or merge a PR only when asked. (The repo had no `main` until stage 7; it was created from `ccr-19c6e368-wdrow7`.
  If GitHub's default branch is not `main` yet, mention it.)
- When a tool or the proxy blocks something (for example, docs hosts can't be fetched from the cloud), say so
  plainly. Don't claim a link or answer was verified when it wasn't.
- Commit messages: `Area: what changed`, for example `Questions: Helm complete (133)` or `Learn: Terraform subjects`.

## 3. Decisions (final)

| Topic | Decision |
|---|---|
| MCQs | **1,300**, 4 options. Each has a Hebrew line per option, a Hebrew "how to answer in an interview" tip, and a link to the documentation page the answer was checked against |
| Open questions | **300** in interview mode: English question → Hebrew points a strong answer covers (3–6) → English follow-up → Hebrew trap → doc link → self-mark (knew / partly / didn't) |
| Language | Questions, options, code and follow-ups in **English** (as in a real interview). All explanations, lessons, tips and callouts in **Hebrew**, with technical terms in English, rendered RTL with code isolated LTR |
| Splits | In every topic: **50% troubleshooting / 50% knowledge** and **50% Junior–Mid / 50% Mid–Senior** (exactly 650 / 650 overall) |
| Papers | **20 × 65**, each mixed by topic weight. **1–10 Junior–Mid**, which teach: a briefing before each question and an explanation after each answer. **11–20 Mid–Senior**, silent until submit |
| Timer | **1:30 per question** (`SIM_QSEC=90`) |
| Score | Skyforge's arithmetic: 100–1000, **720 to pass** (72%), weighted over 4 areas: K8s & Helm 31%, GitOps & CI 37%, Cloud & IaC 22%, Foundations 10%. Shown as "Ship It score" |
| Sources | **Original questions only.** Public lists (bregman-arie/devops-exercises is CC BY-NC-ND; NotHarshhaa and sayhellorob are unlicensed) are a topic map, never copied. Answers are checked against official docs (kubernetes.io, argo-cd.readthedocs.io, helm.sh, developer.hashicorp.com, docs.aws.amazon.com, docs.docker.com, docs.github.com, docs.gitlab.com, jenkins.io, man7.org) |
| AWS scope | AWS *for DevOps* only: EKS, IAM/IRSA/Pod Identity, VPC, EC2/ASG/ELB, ECR, S3, CloudWatch, KMS/Secrets Manager, Route 53 |
| CI scope | Docker builds, DevSecOps (SAST/SCA/Trivy/cosign/SBOM/OIDC), testing in the pipeline, pipeline design and deploy strategies |
| Accounts | Supabase **on** since stage 8: Ship It's own project `rkebneaecaprfolafolg` (Tokyo, free tier). Guests still play on `localStorage`; signing in syncs |
| Games | Casino, duel, tournament and leaderboard are **visible** (stage 8). They hide again (`.nocloud`) if `SUPA` is emptied |

### Weights and counts

| Topic | Weight | MCQ | Open | ≈ per paper |
|---|---|---|---|---|
| Kubernetes | 10 | 265 | 61 | 13 |
| Argo CD | 8 | 212 | 49 | 11 |
| CI (security, testing, building) | 7 | 186 | 43 | 9 |
| AWS | 6 | 159 | 37 | 8 |
| Helm | 5 | 133 | 31 | 7 |
| Terraform | 5 | 133 | 31 | 7 |
| Linux | 3 | 80 | 18 | 4 |
| Jenkins / GitLab CI / GitHub Actions | 3 | 79 | 18 | 4 |
| Networking | 2 | 53 | 12 | 3 |

### The 24 subjects (= sectors, `q.s`; order is fixed, only append)

K8s: pods · networking · config & storage · scheduling · security · troubleshooting —
Argo CD: core · sync · at scale · ops —
CI: docker · devsecops · testing · deploy strategies —
AWS: eks & iam · vpc & compute · storage/secrets/observability —
Helm: charts · releases — Terraform: core · state — Linux — Networking — CI tools.
Slugs and counts: `SECTIONS` in `qsrc/qlib.py`. The section index is stored in user progress, so never reorder it.

## 4. Repository layout

```
CLAUDE.md                 this file
index.html .nojekyll      Pages root: redirects to devops-interview/ (the site URL 404'd without it)
devops-interview/
  index.html              the site. Blobs: #data (bank), #ivdata (interview), #learndata, #studydata
  PLAN.md STATE.md SETUP.md
  qsrc/qlib.py            Q(), O(), TOPICS, SECTIONS, COUNTS, IV_COUNTS, REF_HOSTS, levels JM/MS, kinds T/K
  qsrc/<sub>.py           MCQ sources (k8s_pods, argo_sync, ci_sec, aws_eks, helm_ops, tf_state, linux, net, cicd_tools …)
  isrc/<topic>.py         open interview questions (k8s, argocd, ci, aws, helm, terraform, linux, cicd_tools, net)
  learn_src/_h.py         block shorthand shared by Learn and Study
  learn_src/s00..s23_*.py one Learn subject per file (SUBJECT dict)
  study_src/c1..c9_*.py   one Study chapter per file (CHAPTER dict)
  learn_engine.js learn_screens.html learn_styles.css   Learn engine, injected between LEARN: markers
  study_engine.js study_screens.html study_styles.css   Study engine, injected between STUDY: markers
  build_*.py inject_*.py  builders (validate, then write)
  gen_duel_v2.py build_duel_key.py   server-side duel answer key from the bank
  qa_bank.js qa_learn.js audit_runtime.js audit2..8.js fuzz_exam.js audit_static.py   tests (page suites)
  qa_progress.js          node test: a stored profile survives a reworded bank (BANKV_OK) and resets on an unknown stamp
  tools/                  sql_all.sh (→ supabase_all.sql), qtool.py (dump/write/stats questions), brief.py, merge_apply.sh, short.py, longest.py, shortest.py, fitcheck.py, repl.py, partcheck.py, patch.py, stubs.py,
                          add_part.py (append a Learn module + replace the last final), add_topic.py (append Study pages + quiz), deepstats.py (depth of a Learn subject),
                          linkcheck.py + reffix.py (doc-link check against docs source repos, and the fixer),
                          contentlint.py (one line per audited content defect with its allowed maximum; --strict fails on a regression),
                          bankfix.py (show/apply edits to exam questions by bank index), ivtool.py (dump/apply interview traps, points, follow-ups),
                          learnq.py (dump/apply/stats Learn checks and finals and Study quizzes; askdump/askapply for ASK answer outlines)
  supabase_*.sql sql_tests/          backend for stage 8 (sql_tests/run.sh needs Docker; run_local.sh needs local Postgres)
```

## 5. Authoring formats

**MCQ** (`qsrc/*.py`). The right option always comes first; the build moves it to a balanced position.
```python
Q("k8s-pods", JM, T,                       # sector slug, level JM|MS, kind T(roubleshooting)|K(nowledge)
  "A pod is in CrashLoopBackOff. What do you check first?",
  ("kubectl logs <pod> --previous", "Hebrew: why it's right"),
  ("…", "Hebrew: why it's wrong"), ("…", "…"), ("…", "…"),
  tip="Hebrew: how to say it in an interview",
  ref="https://kubernetes.io/docs/…")      # host must be in REF_HOSTS
```
Built fields per question: `s` sector, `q`, `o` [[letter, text]], `a` [letter], `y` Hebrew line per option,
`x` tip, `lv`, `k`, `r`.

**Open question** (`isrc/*.py`):
`O(sec, lv, kind, "English question", ["Hebrew point", …3–6], follow="English", trap="Hebrew", ref="https://…")`.
The id is the first 8 characters of the sha1 of the normalised question, so editing the wording resets that question's progress.

**Learn subject**: `SUBJECT = {sec, nm, tag, modules:[MOD(id, nm_he, goal_he, blocks, checks)], recap, final:[F(...)]}`.
Each subject has 3 modules, 3 checks each `C(q, right, *wrong, x=Hebrew)`, a recap (≥1,400 characters, two or more tables)
and 10 finals `F(module_id, q, (text, why_he), …, x=…)`. A check option may be `(text, why_he)`; the check feedback then lists
every option with its note. A subject with `"deep": True` must have parts of **≥ 3,000 chars** and a note of **≥ 60 chars on
every option of every check and final** (`build_learn.py` enforces it; `tools/deepstats.py learn_src/sNN.py` shows the numbers).
**Every** Learn check and final (deep or not) must also pass the balance rules in `build_learn.py`: 4 options, each with a
Hebrew note of ≥ 60 chars; no distractor under 55% of the right option's length; the right option at most 1.15× the longest
distractor; per subject the right option longest in ≤ 40% and shortest in ≤ 40% of questions (aim near 23% / 15%); and no stem
copied from the bank. `python3 tools/learnq.py stats learn_src/sNN.py` shows the numbers; `dump`/`apply` rewrite questions.

**Study chapter**: `CHAPTER = {nm, em, sub(he), dom 0–3, secs:[sector ids], topics:[{nm, blocks}], quiz:[QZ(q, right, *wrong, x=he)]}`.
Every sector must belong to exactly one chapter. Each `QZ` option is `(text, why_he)`; the quiz feedback lists every option
with its note (`stuWhyEach`), and `build_study.py` applies the same balance rules per chapter (`learnq.py` edits quizzes as `z0, z1…`).

**Blocks** (`_h.py`): `H P UL STEPS KEY TRAP NOTE TABLE FLOW SPLIT CODE TREE ASK`. Inline markdown: `**bold**`
and `` `code` ``. Keep `**` and backticks balanced; the validators check.
`ASK(("English question", "Hebrew answer outline"), …)` renders each item as a tap-to-open `<details>`; both builders require an
outline of ≥ 120 chars with Hebrew in it. Put commands in backticks so they render as isolated LTR code.

## 6. Build

```bash
cd devops-interview
python3 build_bank.py && python3 inject_bank.py            # qsrc → #data
python3 gen_duel_v2.py && python3 build_duel_key.py        # ALWAYS after a bank change (QA_BANK fails on drift)
python3 build_interview.py && python3 inject_interview.py  # isrc → #ivdata
python3 build_learn.py                                     # learn_src → #learndata
python3 inject_learn.py                                    # Learn engine files → index.html
python3 build_study.py && python3 inject_study.py          # study_src → #studydata, Study engine files
```

**Never hand-edit a blob, or anything between `LEARN:` / `STUDY:` markers.** The next build overwrites it.
`BANKV` identifies the bank by sector + stem per slot. `inject_bank.py` keeps the last build's slots in `qsrc/bankv.json`;
when ≥ 95% of stems are unchanged in place, older stamps stay valid (`BANKV_OK`), so rewording options or explanations keeps
users' seen, wrong and marks. Inserting, deleting or reordering questions still resets them.

## 7. Test (all green before every push)

```bash
cd devops-interview && python3 -m http.server 8765   # http://localhost:8765/index.html?test=1
```

A minimal headless runner (Playwright is preinstalled in cloud sessions; run with `NODE_PATH=$(npm root -g)`):
```js
const {chromium}=require('playwright');
(async()=>{ const [file,fn,args]=process.argv.slice(2);
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:390,height:844}});
  await p.goto('http://localhost:8765/index.html?test=1'); await p.waitForTimeout(2000);
  const r=await p.evaluate(async([f,fn,a])=>{ eval(await (await fetch('/'+f)).text());
    return await window[fn](...(a?JSON.parse(a):[])); },[file,fn,args||null]);
  console.log(JSON.stringify(r).slice(0,6000)); await b.close(); })();
// node runqa.js qa_bank.js QA_BANK   |  qa_learn.js QA_LEARN  |  audit_runtime.js AUDIT  |  fuzz_exam.js FUZZ_EXAM '[3000,7]'
```

No Playwright (local desktop sessions): serve the folder, open `index.html?test=1` in the app's built-in browser and run
the suites from the page's console. Load a harness with an *indirect* eval so its functions become globals:
```js
const load=async f=>{ (0,eval)(await (await fetch(f+'?'+Date.now())).text()); };
await load('qa_bank.js'); await QA_BANK();   // likewise qa_learn.js, audit_runtime.js, audit2..8.js, fuzz_exam.js
```
After a rebuild, reload the page and confirm the `#data` blob holds a new string before trusting a run.

| Suite | File | Last green (after the October 2026 audit) |
|---|---|---|
| `QA_BANK()` | qa_bank.js | 22,996 assertions / 0 fail (runs about 10 minutes) |
| `QA_UI()` | qa_bank.js | 37 screens, no problems |
| `QA_INTEG()` | qa_bank.js | 40 / 0 |
| `QA_LEARN()` | qa_learn.js | 6,790 / 0 (24 subjects, 96 modules) |
| `AUDIT()`, `AUDIT2()`…`AUDIT8()` | audit_runtime.js, audit2..8.js | no HIGH or MED findings |
| `FUZZ_EXAM(3000,7)` | fuzz_exam.js | clean |
| `audit_static.py` | — | advisory only: unused-looking code is mostly reached through strings |
| `tools/contentlint.py --strict` | — | 34 / 34 lines within limits (run after any content change) |
| `qa_progress.js` (node) | — | 6 / 6 |

Notes:
- Run `node --check` on a harness file first. One syntax error makes the whole suite look missing.
- Every `QA_BANK` group runs inside `step()`, so a crash is reported and the run goes on.
- `authoredChecks` enforces the explanation rules, requires zero terse wrong-option lines (was 1,558 before stage 7b) and caps
  questions whose right option is the longest at `<=294` (was 1,096), and shortest at `<=373`. Keep them there or lower.
- Run `FUZZ_EXAM` on a freshly loaded page. Run after the audits on the same page, it once reported
  "two sheets open" (leftover state); on a fresh page the same build was clean.
- When a check fails, decide whether it's a real bug or an old Skyforge assumption (AWS counts, SAA wording).
  Fix the bug, or update the assumption and explain why in the commit.

## 8. Key code in index.html

| What | Where |
|---|---|
| Answer panel | `renderExplain` → `authoredExplain(q,picked)` (Hebrew per option, tip, doc link, 🔊 Read); duels: `duelWhy` (the right option's Hebrew line) |
| Read aloud | `ttsSpeak` (splits Hebrew and English chunks, `he-IL` via `ttsVoiceHe()`), `exReadText` |
| Briefing (papers 1–10) | `buildBriefing`, `CODEX` (312 Hebrew terms, each < 120 chars; also the flashcards), `conceptsFor` (whole-word match), `learnCallouts(sec,kind)` |
| Doc link label | `docLabel(url)` ("Kubernetes docs", "Terraform docs" …), in the answer panel and interview mode |
| Papers / exam | `startPaper`, `paperQs`, `PAPER_LEN=65`, `SIM_QSEC=90`, `simBudget` |
| Score | `DOMAINS`, `domainOf`, `examDomainOf`, `scoreOf`, `scoreScaled`, `SCORE_PASS=720`, `SCORE_SHRINK` (renamed from `saa*` in the cleanup) |
| Interview mode | `IV`, `openInterview`, `ivPick`, `ivNext`, `ivReveal`, `ivMark`; progress `P.iv[id]=[mark,times,when]` |
| Study weights | `STUDY_T.STU_CH`, `STU_SECS`, `stuWeight` |
| Ranks / labels | `RANKS` (Intern … Neon Ascendant), `skillLabel` (Junior/Mid-level/Senior) |
| Cloud switch | `const SUPA={url,anonKey}` (publishable key) → `CLOUD_ON` → otherwise `<html class="nocloud">` hides casino and leaderboard |
| Test surface | `window.__t` with `?test=1` |

## 9. Gotchas (each one has bitten before)

- `inject_learn.py` replaces the whole `LEARN:JS` band, and the `STUDY:JS` block is nested inside it. The script
  carries it over; if it ever stops, the page throws "STUDY_T is not defined".
- RTL goes on the Hebrew element, never on a shared selector (English punctuation jumps). Code inside Hebrew needs `unicode-bidi:isolate`.
- An English list inside Hebrew (`ב-if, changes ו-exists`) would render as one LTR block with the Hebrew prefix against the
  last item. `qtx`/`mdInline` wrap each item in `<bdi>` (`heLists`, only in strings with Hebrew, never inside backticks);
  `QA_BANK` checks the text is otherwise unchanged. Text rendered some other way doesn't get this.
- Backtick text renders as `<code>` through `qtx()`. Tests compare the stripped text.
- `fmtClock` takes milliseconds.
- In tests, drive exams by tapping a real `.opt`. `submitAnswer()` and `qConfirm.click()` run the practice path.
- A local `const` with a global function's name shadows that function for the whole body.
- `.screen` is a stacking context (z-index 10); a back button inside it can't rise above `#topbar`.
- `overflow:hidden` on a direct child of `.screen` needs `flex:none`, or it collapses.
- Builders `sys.exit` on the first bad file. A chapter-level `continue` once skipped validating later chapters; validate each one.
- Cloud sessions: shell `cd` resets. Use absolute paths, and never `rm` a path built from a variable that might be unset.
- Terse-line rewrites: "לא." appears hundreds of times, so never search-and-replace the text. Replace the string literal
  at its exact position (`ast` gives `lineno`/`col_offset` of each `Q(...)` option tuple; `col_offset` is in UTF-8 bytes),
  key each line by question index and option index within its file, and re-parse the file before writing.
- Changing a question's options or answer, or a few stems, keeps progress (`BANKV_OK`, see section 6); adding, removing or
  reordering questions, or rewording most stems, resets everyone's seen/wrong/marks. Run `qa_progress.js` after a bank change.
  Ask before touching an option's text (stage 9 and the October 2026 audit have that approval).
- In Bash heredocs, quote the delimiter (`<<'EOF'`): backticks in Hebrew content otherwise run as command substitution.
- The cloud proxy blocks the docs hosts, so `ref` links can't be fetched there. Verify them from a normal browser.

## 10. History

| Stage | Done |
|---|---|
| 0 | Ship It rebrand, Supabase off, games hidden, 90 s/question, old AWS files deleted |
| 1 | Question pipeline + validator (counts, levels, kinds, answer-position spread, Hebrew, ref hosts) |
| 2–3 | 1,300 MCQs written in weight order; 20 papers |
| 4 | Interview mode: 300 open questions + screen + self-marking |
| 5 | Learn: 24 Hebrew subjects (72 parts, 216 checks, 240 finals) |
| 6 | Study: 9 chapters, 30 pages; Study engine moved into source files |
| 7 | AWS remnants removed from the UI; Hebrew TTS and Read on explanations; old explanation QA replaced by `authoredChecks`; mock no longer shows a paper's briefing; duel key regenerated; STATE.md rewritten; merged to `main` |
| 7b *(superseded by 9)* | Terse wrong-option lines expanded for K8s (30), Argo CD (99), CI (168), AWS (230), Helm (253), `tf_core` (150): 930 of 1,558. One commit per topic, cap lowered each time to `<=628`. Full QA green; pushed to `main` |
| 9 | Hard distractors + full explanations for all 1,300 MCQs (24 files): right-is-longest 84% → 23%, shortest 29%, every option explained in Hebrew, fuller tips; validator rules for `HARD = True` files; QA caps (longest ≤ 303, shortest ≤ 376, no terse lines); tf_core `user_data` and helm_ops hook-policy facts fixed |
| 10 | Deeper Learn and Study: a 4th "in practice" module in every Learn subject (24 new parts: real command output, troubleshooting tables, edge cases; 3 checks each, one final replaced so each subject still has 10) and 15 new Study pages across c1–c9 (cheat sheets, review drills, checklists) with 15 quiz checks. Facts checked against docs via raw.githubusercontent.com where unsure (e.g. S3 backend `use_lockfile`). Users who finished a subject see the new part as unfinished |
| 8 | Supabase on: own project, `supabase_all.sql`, publishable key in `SUPA`; casino, duel, tournament and leaderboard visible; duel SQL suite moved to the DevOps bank; Docker-free `sql_tests/run_local.sh`; SQL comments renamed to Ship It |
| 11 (partial) | Deep Learn pass: check options explain themselves (`C()` with `(text, why)`), `deep` subjects enforced by the builder; Argo CD s06–s09 rewritten in depth |
| Links | 822 doc pages checked against source repos; 154 refs fixed (moved pages, dead anchors, wrong paths); `LINKS.md` lists what needs a browser. Ship It rocket icon replaces the AWS badge |
| Cleanup | Skyforge explanation fallback, dead course mode, empty blobs, their CSS and `audit9.js` removed (~850 lines); `saa*` → `score*`; root `index.html` redirect fixes the Pages 404 |
| Audit (Oct 2026) | 30 content improvements, each guarded by a `contentlint.py` line (34/34 green). Progress survives a reworded bank (`BANKV_OK`). Bank: answer tells removed (`code` only on the right option 73 → 0, absolute-word distractors 31 → 0, stem echo 33 → 0), a duplicate reworded, landing-page refs replaced. Interview: 294 short traps and 256 short points rewritten. 8 facts fixed across bank, interview, Learn and Study (seccomp default, `kubectl debug node` + chroot, Argo CD polling, Ingress NGINX retirement, `create-only`, hook delete policy, `helm --wait`, `Replace=true`). Briefing: CODEX 102 → 312 terms, questions with no term 259 → 18. Learn: all 528 checks and finals rebalanced (right option longest 73–95% per subject → ≤ 27%; 976 throwaway distractors, 1,698 short notes → 0), 96 ASK answers. Study: 46 quiz questions with notes per option (longest 31 → 10), 165 ASK answers. Builders enforce all of it |

## 11. Left to do (in this order unless Nehoray says otherwise)

1. **Stage 9: hard distractors and full explanations — DONE (all 24 files, 1,300 q).** Kept here as the rulebook for
   any future question edit: every `qsrc` file is `HARD = True`, so `build_bank.py` enforces these rules on every change.
   **The bug (found by Nehoray):** the right answer was the longest option in 84% of questions (1,096/1,300), on average 1.56× the
   wrong ones, so it could be picked without knowing the material. Some distractors were throwaways ("Build only on Mondays").
   And many explanations were too thin. Nehoray asked for answers that are hard to tell apart, and for much more depth,
   based on the official documentation of each tool.
   **What every rewritten question gets:** 3 plausible distractors about as long and specific as the right answer (real-sounding
   flags, common misconceptions, half-truths; never jokes), a Hebrew explanation of 1–3 sentences for **every** option (what
   it actually does and why it does or doesn't answer), and a fuller interview tip. Stems, levels, kinds, refs and the
   right answer's meaning stay. **Option text changes `BANKV`, so users' seen/wrong/marks reset; Nehoray approved this rewrite.**
   **Enforced by `build_bank.py`** for any `qsrc` file that declares `HARD = True` (put it above `S = ...`):
   the right option at most 15% longer than the longest distractor; no distractor under 55% of the right one's length;
   every explanation ≥ 70 chars; tip ≥ 80 chars; and per file the right option is the longest in ≤ 40% **and the shortest
   in ≤ 40%** of questions. (Fixing the first tell created the second: after the first pass the right answer was the
   shortest in up to 56% of a file. Aim for both near 25%: the right answer should sit mid-pack by length.)
   `qa_bank.js` `authoredChecks` holds the bank-wide line: right option longest in ≤ **303** questions, shortest in ≤ **376**,
   and **zero** terse wrong-option lines (lowered to **294** / **373** in the October 2026 audit). Keep them there (or lower) when you edit questions.
   **Done (HARD = True):** Kubernetes (`k8s_pods`, `k8s_net`, `k8s_config`, `k8s_sched`, `k8s_sec`, `k8s_debug`, 265 q) and
   Argo CD (`argo_core`, `argo_sync`, `argo_scale`, `argo_ops`, 212 q), CI (`ci_docker`, `ci_sec`, `ci_test`, `ci_deploy`, 186 q),
   AWS (`aws_eks`, `aws_net`, `aws_ops`, 159 q), Helm (`helm_charts`, `helm_ops`, 133 q), Terraform (`tf_core`, `tf_state`, 133 q),
   Linux (80 q), CI tools (`cicd_tools`, 79 q), Networking (`net`, 53 q). Final: right-is-longest 303/1,300 (23%, was 84%),
   shortest 376 (29%), no terse lines left. Per-file numbers: `python3 tools/qtool.py stats <file>.py`.
   **Workflow for rewriting a file** (from `devops-interview/`; tools in `tools/`):
   - `python3 tools/brief.py <file>.py` — stems and options, compact; `python3 tools/qtool.py dump <file>.py` — full JSON.
   - Write the new content as JSON `[{"i":N,"r":[text,why],"w":[[text,why]×3],"tip":"..."}]` (split into parts of ~22).
     **Write the right answer short and the distractors full** — the habit is the other way round.
   - **Before merging, check each draft part:** `python3 tools/partcheck.py part_a.json [part_b.json ...]` flags right options
     that are longest or too long, short distractors, explanations < 72 and tips < 82, and prints longest/shortest totals.
     Fix a part with `python3 tools/patch.py part.json fixes.json`, where fixes is
     `{"<i>": {"r": "new right text", "w1".."w3": "new wrong text", "y0": "right why", "y1".."y3": "wrong whys", "tip": "..."}}`.
     Fixing drafts this way is much cheaper than fixing the merged file. Split big files into 3 parts of ~22.
   - `tools/merge_apply.sh <file>.py part_a.json part_b.json` — checks every index is covered, rewrites the `Q(...)` calls
     in place (comments survive), adds `HARD = True`, runs the validator.
   - Fix what it reports: `tools/short.py <file>.py` lists explanations < 70; `tools/longest.py <file>.py` lists questions where
     the right one is longest; `tools/shortest.py <file>.py` where it is shortest; `tools/fitcheck.py <file>.py cands.json`
     (`{"i": "new right text"}`) reports which candidate right-option rewrites land between the shortest and longest
     distractor and writes those to `/tmp/fit_ok.json` for `tools/repl.py <file>.py /tmp/fit_ok.json`.
     `tools/repl.py` replaces exact string literals (`[[old,new],...]`, each must occur once).
     **Habits that save a fix round:** write each wrong-option explanation as two full sentences (~90–120 chars); the
     first pass kept producing 55–69-char lines. Write the right option a little shorter than the distractors, but not
     the shortest.
   - Per topic: `build_bank.py`, `inject_bank.py`, `gen_duel_v2.py`, `build_duel_key.py`, lower the caps in `authoredChecks`,
     run QA_BANK / QA_INTEG / QA_UI, commit `Questions: <topic> hard distractors and full explanations`, push to the branch and `main`.
   **Documentation:** the docs sites are blocked by the cloud proxy, but `raw.githubusercontent.com` works, and most tools keep
   their docs there as Markdown: `kubernetes/website/main/content/en/docs/...`, `argoproj/argo-cd/master/docs/...`,
   `hashicorp/web-unified-docs/main/content/terraform/...`, `awsdocs/amazon-eks-user-guide/mainline/latest/ug/...`,
   `docker/docs/main/content/manuals/...`, `github/docs/main/content/actions/...`, `jenkinsci/jenkins.io/master/content/doc/...`.
   Use them to check any fact you aren't sure of; when unsure and unverifiable, leave the claim out rather than guess.
   (Fixed in the Terraform pass: the tf_core `user_data` question now says a change stops and starts the instance by default,
   and replaces it only with `user_data_replace_on_change = true`.)
2. **Stage 10: deeper Learn and Study content — DONE (first pass).** Every Learn subject has a 4th module `*-in-practice`
   (add more with `tools/add_part.py <learn_src/sNN.py> <snippet>`: `MOD(...)`, a line `#---FINAL---`, one `F(...)`), and
   every Study chapter has 1–2 extra pages (`tools/add_topic.py <study_src/cN.py> <snippet>`: topic dicts, `#---QUIZ---`, `QZ(...)`).
   A further pass can add more parts per subject the same way (builders allow up to 8 modules).
2b. **Stage 11 (IN PROGRESS): deep Learn pass** (Nehoray: "one sentence about something isn't enough", and explain why every
   answer is right or wrong). Per subject: rewrite each part as real explanation (how it works, why, examples, real commands),
   give every check option a `(text, why)` note, lengthen every final note, add `"deep": True`, check facts against the
   docs source (`/tmp/docsrc` clones; see `tools/linkcheck.py`). **Done:** Argo CD s06–s09 (each ~23K → ~46K chars).
   Corrections found on the way: polling is 120 s + up to 60 s jitter (not 180 s); with no hook-delete-policy Argo CD assumes
   BeforeHookCreation; `create-only`/`create-update` don't protect Applications when the ApplicationSet itself is deleted;
   progressive syncs are Beta since 3.3. **Next:** Kubernetes s00–s05, then CI, AWS, Helm, Terraform, Linux, Networking, CI tools.
3. **Stage 8: games and multiplayer — DONE.** Nehoray created the project and ran `supabase_all.sql` (all nine SQL files
   in order; rebuilt by `tools/sql_all.sh`). `SUPA` holds the URL and the **publishable** key (never `sb_secret_`).
   `sql_tests/duel_v2_suite.sql` moved from the AWS bank (1,201 q, 19 exams) to the DevOps bank (1,300 q, 20 exams);
   SQL suites pass via `sql_tests/run_local.sh` (no Docker in cloud sessions). Mini-game badges ("Arcade Regular",
   "Triple Threat") come from the local mini-games, not the cloud. **The cloud proxy blocks `*.supabase.co` and
   cdn.jsdelivr.net**, so sign-in, duels and the leaderboard can only be tried from a normal browser.
   **After any bank change:** `gen_duel_v2.py`, `build_duel_key.py`, `tools/sql_all.sh`, then re-run `supabase_duel_v2.sql`
   in the Supabase SQL Editor, or duels mark against the old key.
4. **Cleanup — DONE.** Removed the Skyforge explanation fallback (`buildExplain`, `whyByOption`, `exCue`, `renderStory`,
   `optionLine`, `noLine`, the glossary, `EXPLAIN`), the dead course mode (`blueprintHTML`, `deepDiveHTML`, AWS `TRIGGERS`/`PILLARS`,
   `mdRender`), the three empty blobs, 55 CSS rules only those parts used, and `audit9.js`; `saa*` → `score*`.
   About 850 lines fewer; pixel compare of all 37 screens unchanged. `exFallback(sec)` (Learn key callouts) stays: the briefing uses it.
   **STATE.md predates this**: its notes on the explanation fallback, `saa*` names and `AUDIT9` are out of date (Nehoray asked
   for progress notes in this file only).
5. **Doc links — first pass DONE.** `tools/linkcheck.py <docsrc>` checks all 1,600 refs (822 pages) against each docs site's
   source repo and its redirect rules (k8s `_redirects`, Terraform `redirects.jsonc`, Helm `netlify.toml`, GitHub
   `redirect_from`, Docker aliases, MDN `_redirects.txt`), plus #anchors against headings; AWS guides against their 2023
   GitHub archives. `tools/reffix.py fixes.json` rewrites refs through ast (handles `D+"path"`). 154 refs fixed: moved pages
   (GitHub Actions docs reorganised, Terraform `language/*` → `block/*`, MDN `HTTP/Reference`, k8s probes/HPA/autoscaling,
   Helm 2→3 FAQ under `/docs/v3/`, Trivy `docs/` → `guide/`), dead anchors dropped, wrong paths (PrivateLink, EKS add-ons).
   Refs aren't in `BANKV`, so progress is untouched. **Left:** `devops-interview/LINKS.md` lists the 254 pages with no source
   (man7, most AWS outside the 12 archived guides, RFCs, blogs) and 2 AWS pages newer than the archive: check in a browser.
6. **Deploy — live.** GitHub Pages builds from branch `ccr-19c6e368-wdrow7` (also the repo's default branch), repo root:
   https://nehoraym.github.io/devops-websites/ redirects to `/devops-interview/`. Push to that branch to deploy. In Supabase,
   set Authentication → URL Configuration → Site URL to that address so sign-up emails link back to the site.
7. **October 2026 content audit — DONE (30 points).** `tools/contentlint.py` holds one line per point with its allowed
   maximum (34/34 green); run it with `--strict` after any content change. **Left, found on the way:**
   18 Junior–Mid questions still get no glossary term in the briefing (limit 65). English lists inside Hebrew (1,448 in
   1,272 strings) now render item by item through `heLists` (see section 9).
