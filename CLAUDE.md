# Ship It: DevOps interview prep (CLAUDE.md)

The app lives in `devops-interview/`. `index.html` is the whole site: one file with the content in JSON blobs.
Read `devops-interview/PLAN.md` (decisions and stages) and `devops-interview/STATE.md` (how it works)
before changing anything.

## Rules

- **Language:** questions, options and code in English. Explanations, lessons, tips and callouts in Hebrew (RTL, code isolated LTR).
- **Never hand-edit a JSON blob** (`#data`, `#ivdata`, `#learndata`, `#studydata`) **or anything between `LEARN:`/`STUDY:` markers.**
  Edit the source and rebuild; the builders validate and write nothing on error.
- `main` holds the merged work (stages 0–7). Work on the branch the session assigns, commit after every stage, push. Open or merge a PR only when asked.
- Reply to the user in Hebrew, with a summary at the end of every stage, and ask before moving to the next one.

## What the project is

**Ship It** is a static, single-page site for preparing for **DevOps job interviews**. It was made by copying
Skyforge (an AWS SAA-C03 exam trainer, repo `NehorayM/neon-grid-aws`) and replacing all of its content. The
exam engine, clocks, profile, sync code and design come from Skyforge; the questions, explanations, lessons,
reference pages and interview questions are new. The owner is Nehoray. All decisions below were agreed with
them, so don't re-open them without asking.

## Decisions (see PLAN.md for the full tables)

| Topic | Decision |
|---|---|
| MCQs | **1,300**, 4 options each, a Hebrew line for every option (`y`), a Hebrew "how to answer in an interview" tip (`x`), a doc link (`r`) |
| Open questions | **300** in interview mode: Hebrew points a strong answer covers, an English follow-up, a Hebrew trap, self-marking |
| Weights (1–10) | K8s 10 (265 / 61 open) · Argo CD 8 (212/49) · CI 7 (186/43) · AWS 6 (159/37) · Helm 5 (133/31) · Terraform 5 (133/31) · Linux 3 (80/18) · Jenkins/GitLab/GHA 3 (79/18) · Networking 2 (53/12) |
| Splits | In every topic: 50% troubleshooting / 50% knowledge, 50% Junior–Mid / 50% Mid–Senior (`lv`, `k` fields) |
| Papers | 20 × 65, mixed by weight. Papers 1–10 Junior–Mid and teaching (brief + explain); 11–20 Mid–Senior, silent until submit |
| Timer | 1:30 per question (`SIM_QSEC=90`) |
| Score | Kept from Skyforge: 100–1000, 720 to pass, weighted over 4 areas (K8s & Helm 31%, GitOps & CI 37%, Cloud & IaC 22%, Foundations 10%). Shown as "Ship It score" |
| Subjects | **24** (K8s 6, Argo CD 4, CI 4, AWS 3, Helm 2, Terraform 2, Linux 1, Networking 1, CI tools 1). One sector each, used by Learn, Study and practice |
| AWS scope | AWS *for DevOps* only: EKS, IAM/IRSA/Pod Identity, VPC, EC2/ASG/ELB, ECR, S3, CloudWatch, KMS/Secrets Manager, Route 53 |
| Sources | **Original questions.** Public question lists (devops-exercises is CC BY-NC-ND; others unlicensed) are used as a topic map only, never copied. Answers are checked against official docs |
| Accounts | Supabase **off** (`nocloud`) because the copied keys point at the AWS site's project. Progress is in `localStorage` |
| Games | Casino, duel, tournament and leaderboard stay in the code but are **hidden** until a new Supabase project exists (stage 8) |

## Where things are

```
devops-interview/
  index.html            the site (blobs: #data bank, #ivdata interview, #learndata, #studydata)
  qsrc/<topic>.py       MCQ sources; qsrc/qlib.py has Q(), O(), COUNTS, IV_COUNTS, REF_HOSTS
  isrc/<topic>.py       open interview questions
  learn_src/s00..s23    Learn subjects; learn_src/_h.py = block shorthand (P, TABLE, FLOW, KEY, TRAP, CODE, ASK, QZ...)
  study_src/c1..c9      Study chapters (same shorthand)
  learn_*.{js,html,css} / study_*.{js,html,css}   engine sources injected between markers
  qa_bank.js qa_learn.js audit*.js fuzz_exam.js   browser test suites
  supabase_*.sql sql_tests/ SETUP.md              backend for stage 8
```

Useful code entry points in `index.html`: `renderExplain` → `authoredExplain` (the answer panel), `buildBriefing`
(papers 1–10), `CODEX` (102-term Hebrew glossary → flashcards), `DOMAINS`/`saaScore`/`saaScaled` (score),
`IV`/`ivPick`/`ivReveal` (interview mode), `ttsSpeak`/`ttsVoiceHe` (read aloud), `window.__t` (test surface, `?test=1`).

## Gotchas

- `inject_learn.py` replaces the whole `LEARN:JS` band; the `STUDY:JS` block is nested inside it and is carried over by the script.
- Text with backticks renders as `<code>` via `qtx()`; tests compare stripped text.
- RTL goes on the Hebrew element itself, not on a shared selector, with code isolated (`unicode-bidi:isolate`).
- Drive exams in tests by tapping a real `.opt`, not `submitAnswer()`.
- Any bank change → rebuild the duel key, or `QA_BANK` fails on drift.
- Docs hosts are blocked by the cloud proxy, so doc links can't be fetched from a cloud session.

## Build

```bash
cd devops-interview
python3 build_bank.py && python3 inject_bank.py            # qsrc/*.py      -> #data (1,300 MCQs)
python3 build_interview.py && python3 inject_interview.py  # isrc/*.py      -> #ivdata (300 open questions)
python3 build_learn.py                                     # learn_src/*.py -> #learndata (24 subjects)
python3 inject_learn.py                                    # learn_engine.js / learn_screens.html / learn_styles.css
python3 build_study.py && python3 inject_study.py          # study_src/c*.py + study_engine.js / study_screens.html / study_styles.css
python3 gen_duel_v2.py && python3 build_duel_key.py        # after ANY bank change (QA fails otherwise)
```

## Test (all must pass before a push)

```bash
python3 -m http.server 8765    # http://localhost:8765/index.html?test=1
```
Headless with Playwright (`NODE_PATH=$(npm root -g)`): load the file, `eval` it, then call
`QA_BANK()`, `QA_UI()` and `QA_INTEG()` from `qa_bank.js`, `QA_LEARN()` from `qa_learn.js`,
`AUDIT()` from `audit_runtime.js`, `AUDIT2()`…`AUDIT9()`, and `FUZZ_EXAM(3000,7)`. Then run `python3 audit_static.py` (advisory).
Last green run (stage 7): QA_BANK 22,662/0 · QA_UI 37 screens · QA_INTEG 40/0 · QA_LEARN 5,710/0 · audits: no HIGH/MED.
Run `node --check` on a harness file before loading it.

## Done

| Stage | Content |
|---|---|
| 0 | Ship It rebrand, Supabase off, games hidden, 90 s/question |
| 1 | Question pipeline + validator |
| 2–3 | 1,300 MCQs by weight (K8s, Argo CD, CI, AWS, Helm, Terraform, Linux, CI tools, networking); 20 papers of 65 |
| 4 | Interview mode: 300 open questions, Hebrew points, follow-up, trap, self-marking |
| 5 | Learn: 24 Hebrew subjects |
| 6 | Study: 9 chapters, 30 reference pages |
| 7 | AWS remnants removed from the UI, Hebrew TTS + Read on explanations, QA updated (`authoredChecks`), STATE.md rewritten |

## Left to do

1. **Stage 7b: expand terse explanations.** 1,558 wrong-option Hebrew lines are a word or two ("לא.", "לא קשור.") across 789 questions.
   Fix them topic by topic in `qsrc/`, rebuild, regenerate the duel key, and lower the cap in `authoredChecks` (`qa_bank.js`, currently `<=1558`).
2. **Stage 8: games and multiplayer.** Create a new Supabase project (see `SETUP.md`), run `supabase_*.sql`
   (test first with `sql_tests/run.sh`), set the keys, turn cloud on, and un-hide the games, casino, duel and tournament. Badges that need games unlock then.
3. **Cleanup (after stage 8):** remove the Skyforge explanation fallback (`whyByOption`, `exCue`, `renderStory`, `buildExplain` glossary parts)
   and the empty `#explaindata` / `#subjectdata` / `#coursedata` blobs. The `saa*` function names could become `score*`.
4. Doc links in the content could not be verified from this environment (the proxy blocks the docs hosts). Spot-check them in a normal browser.
