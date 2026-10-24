# Ship It: DevOps interview prep (CLAUDE.md)

The app lives in `devops-interview/`. `index.html` is the whole site: one file with the content in JSON blobs.
Read `devops-interview/PLAN.md` (decisions and stages) and `devops-interview/STATE.md` (how it works)
before changing anything.

## Rules

- **Language:** questions, options and code in English. Explanations, lessons, tips and callouts in Hebrew (RTL, code isolated LTR).
- **Never hand-edit a JSON blob** (`#data`, `#ivdata`, `#learndata`, `#studydata`) **or anything between `LEARN:`/`STUDY:` markers.**
  Edit the source and rebuild; the builders validate and write nothing on error.
- Work on the assigned branch, commit after every stage, and push. No PR unless asked.
- Reply to the user in Hebrew, with a summary at the end of every stage, and ask before moving to the next one.

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
