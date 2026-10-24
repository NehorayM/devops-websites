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
devops-interview/
  index.html              the site. Blobs: #data (bank), #ivdata (interview), #learndata, #studydata
                          (#explaindata, #subjectdata, #coursedata are empty leftovers)
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
  qa_bank.js qa_learn.js audit_runtime.js audit2..9.js fuzz_exam.js audit_static.py   tests
  tools/                  qtool.py (dump/write/stats questions), brief.py, merge_apply.sh, short.py, longest.py, shortest.py, fitcheck.py, repl.py, partcheck.py, patch.py, stubs.py,
                          add_part.py (append a Learn module + replace the last final), add_topic.py (append Study pages + quiz)
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
and 10 finals `F(module_id, q, (text, why_he), …, x=…)`.

**Study chapter**: `CHAPTER = {nm, em, sub(he), dom 0–3, secs:[sector ids], topics:[{nm, blocks}], quiz:[QZ(q, right, *wrong, x=he)]}`.
Every sector must belong to exactly one chapter.

**Blocks** (`_h.py`): `H P UL STEPS KEY TRAP NOTE TABLE FLOW SPLIT CODE TREE ASK`. Inline markdown: `**bold**`
and `` `code` ``. Keep `**` and backticks balanced; the validators check.

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
A bank change also changes `BANKV`, which resets users' seen, wrong and marks on purpose.

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
await load('qa_bank.js'); await QA_BANK();   // likewise qa_learn.js, audit_runtime.js, audit2..9.js, fuzz_exam.js
```
After a rebuild, reload the page and confirm the `#data` blob holds a new string before trusting a run.

| Suite | File | Last green (end of stage 8, cloud on) |
|---|---|---|
| `QA_BANK()` | qa_bank.js | 22,969 assertions / 0 fail (runs about 10 minutes) |
| `QA_UI()` | qa_bank.js | 37 screens, no problems |
| `QA_INTEG()` | qa_bank.js | 40 / 0 |
| `QA_LEARN()` | qa_learn.js | 6,790 / 0 (24 subjects, 96 modules; end of stage 10) |
| `AUDIT()`, `AUDIT2()`…`AUDIT9()` | audit_runtime.js, audit2..9.js | no HIGH or MED findings |
| `FUZZ_EXAM(3000,7)` | fuzz_exam.js | clean |
| `audit_static.py` | — | advisory only: unused-looking code is mostly reached through strings |

Notes:
- Run `node --check` on a harness file first. One syntax error makes the whole suite look missing.
- Every `QA_BANK` group runs inside `step()`, so a crash is reported and the run goes on.
- `authoredChecks` enforces the explanation rules, requires zero terse wrong-option lines (was 1,558 before stage 7b) and caps
  questions whose right option is the longest at `<=303` (was 1,096), and shortest at `<=376`. Keep them there or lower.
- Run `FUZZ_EXAM` on a freshly loaded page. Run after the audits on the same page, it once reported
  "two sheets open" (leftover state); on a fresh page the same build was clean.
- When a check fails, decide whether it's a real bug or an old Skyforge assumption (AWS counts, SAA wording).
  Fix the bug, or update the assumption and explain why in the commit.

## 8. Key code in index.html

| What | Where |
|---|---|
| Answer panel | `renderExplain` → `authoredExplain(q,picked)` (Hebrew per option, tip, doc link, 🔊 Read) |
| Read aloud | `ttsSpeak` (splits Hebrew and English chunks, `he-IL` via `ttsVoiceHe()`), `exReadText` |
| Briefing (papers 1–10) | `buildBriefing`, `CODEX` (102 Hebrew terms; also the flashcards), `learnCallouts(sec,kind)` |
| Papers / exam | `startPaper`, `paperQs`, `PAPER_LEN=65`, `SIM_QSEC=90`, `simBudget` |
| Score | `DOMAINS`, `domainOf`, `examDomainOf`, `saaScore`, `saaScaled`, `SAA_PASS=720` (the names say saa; the UI says Ship It) |
| Interview mode | `IV`, `openInterview`, `ivPick`, `ivNext`, `ivReveal`, `ivMark`; progress `P.iv[id]=[mark,times,when]` |
| Study weights | `STUDY_T.STU_CH`, `STU_SECS`, `stuWeight` |
| Ranks / labels | `RANKS` (Intern … Neon Ascendant), `skillLabel` (Junior/Mid-level/Senior) |
| Cloud switch | `const SUPA={url,anonKey}` (publishable key) → `CLOUD_ON` → otherwise `<html class="nocloud">` hides casino and leaderboard |
| Test surface | `window.__t` with `?test=1` |

## 9. Gotchas (each one has bitten before)

- `inject_learn.py` replaces the whole `LEARN:JS` band, and the `STUDY:JS` block is nested inside it. The script
  carries it over; if it ever stops, the page throws "STUDY_T is not defined".
- RTL goes on the Hebrew element, never on a shared selector (English punctuation jumps). Code inside Hebrew needs `unicode-bidi:isolate`.
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
- Changing a question's stem, options or answer changes `BANKV` and resets everyone's seen/wrong/marks. Explanation
  lines (`y`) and tips don't. Ask before touching an option's text (stage 9 has that approval).
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
   and **zero** terse wrong-option lines. Keep them there (or lower) when you edit questions.
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
3. **Stage 8: games and multiplayer — DONE.** Nehoray created the project and ran `supabase_all.sql` (all nine SQL files
   in order; rebuilt by `tools/sql_all.sh`). `SUPA` holds the URL and the **publishable** key (never `sb_secret_`).
   `sql_tests/duel_v2_suite.sql` moved from the AWS bank (1,201 q, 19 exams) to the DevOps bank (1,300 q, 20 exams);
   SQL suites pass via `sql_tests/run_local.sh` (no Docker in cloud sessions). Mini-game badges ("Arcade Regular",
   "Triple Threat") come from the local mini-games, not the cloud. **The cloud proxy blocks `*.supabase.co` and
   cdn.jsdelivr.net**, so sign-in, duels and the leaderboard can only be tried from a normal browser.
   **After any bank change:** `gen_duel_v2.py`, `build_duel_key.py`, `tools/sql_all.sh`, then re-run `supabase_duel_v2.sql`
   in the Supabase SQL Editor, or duels mark against the old key.
4. **Cleanup:** remove the Skyforge explanation fallback (`whyByOption`, `exCue`, `renderStory`, `optionLine`,
   the glossary parts of `buildExplain`; `renderExplain` still calls `buildExplain` for the header) and the empty blobs.
   Rename `saa*` to `score*`. Retire `AUDIT9`, which measured the old splitter.
5. **Verify doc links** (`r` and `ref`) from a normal browser and fix any 404s.
6. **Deploy:** the site isn't on GitHub Pages yet. Pages from `main` would serve it at `/devops-interview/`.
