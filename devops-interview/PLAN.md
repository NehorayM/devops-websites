# Ship It: work plan

Turning the AWS SAA site (Skyforge) into a site that prepares you for **DevOps job interviews**.
All the decisions below were made together with Nehoray, before any work started.

## Decisions

| Topic | Decision |
|---|---|
| Name | **Ship It**, folder `devops-interview/` |
| Multiple-choice questions | **1,300**: 4 options, an explanation for every option, and a short "how to answer in an interview" |
| Open questions (interview mode) | **~300** on top: question, then a model answer, then you mark yourself "knew / didn't know" |
| Troubleshooting vs knowledge | **50% / 50%** |
| Level | **Half Junior–Mid, half Mid–Senior**. Each question is tagged with its level |
| Language | Questions in English, explanations in Hebrew (technical terms in English) |
| Sources | **Original questions**: research what gets asked on the prep sites, write new questions, and verify every answer against official documentation |
| Exams | **20 papers × 65 questions**. Every paper is mixed by topic weight. Papers 1–10 are Junior–Mid, papers 11–20 are Mid–Senior |
| Timer | **1:30 per question** (`SIM_QSEC=90`) |
| Accounts (Supabase) | **Turned off for now.** The copy pointed at the original AWS site's project. Progress is saved in the browser |
| Casino / duel / leaderboard | Stay in the code and get updated, but are **hidden** until there is a new Supabase project |
| Learn / Study | Stay, rebuilt around **24 subjects** (sub-topics) |
| AWS | Focus on **AWS for DevOps**: EKS, IAM/IRSA, VPC, EC2/ASG/ELB, ECR, S3, CloudWatch, KMS/Secrets Manager, Route 53 |
| CI | Docker builds, DevSecOps, tests in the pipeline, pipeline design and deployment strategies |

## Question distribution

Weighted by the scores you gave (1–10). Total weight is 49.

| Topic | Weight | Multiple choice | Open | Per paper (≈) |
|---|---|---|---|---|
| Kubernetes | 10 | 265 | 61 | 13 |
| ArgoCD | 8 | 212 | 49 | 11 |
| CI: security, testing, building | 7 | 186 | 43 | 9 |
| AWS | 6 | 159 | 37 | 8 |
| Helm | 5 | 133 | 31 | 7 |
| Terraform | 5 | 133 | 31 | 7 |
| Linux | 3 | 80 | 18 | 4 |
| Jenkins / GitLab CI / GitHub Actions | 3 | 79 | 18 | 4 |
| Networking | 2 | 53 | 12 | 3 |
| **Total** | 49 | **1,300** | **300** | 65 (rounded) |

Within each topic: half troubleshooting and half knowledge, and half Junior–Mid and half Mid–Senior.

## The 24 subjects (Learn, Study, and practice by topic)

- **Kubernetes (6):** Pods & Workloads · Services, Ingress, DNS & NetworkPolicy · ConfigMaps, Secrets & Storage ·
  Scheduling, Resources & Autoscaling · RBAC & Security · Cluster Troubleshooting & Observability
- **ArgoCD (4):** Core concepts & Applications · Sync, Health, Hooks & Waves ·
  ApplicationSets, App-of-Apps & Multi-cluster · RBAC, SSO, Secrets & Troubleshooting
- **CI (4):** Docker image builds · DevSecOps (SAST/SCA/Trivy/cosign/SBOM/OIDC) ·
  Testing in the pipeline · Pipeline design & deployment strategies (blue/green, canary, rollback)
- **AWS (3):** EKS & IAM (IRSA / Pod Identity) · VPC, EC2/ASG/ELB & Route 53 · S3, ECR, KMS/Secrets & CloudWatch
- **Helm (2):** Charts & templating · Releases, upgrades, rollback & troubleshooting
- **Terraform (2):** Core: providers, modules, plan/apply · State, locking, import, drift & workflows
- **Linux (1)** · **Networking (1)** · **Jenkins / GitLab CI / GitHub Actions (1)**

## Research: where the material comes from

What gets asked in interviews (used to map topics and scenarios only, nothing copied):

- [bregman-arie/devops-exercises](https://github.com/bregman-arie/devops-exercises): the largest. Licensed
  CC BY-NC-ND, which **forbids modifying** the questions, so it is used only as a map of topics
- [NotHarshhaa/DevOps-Interview-Questions](https://github.com/NotHarshhaa/DevOps-Interview-Questions),
  [sayhellorob/DevOps-Interview-Questions](https://github.com/sayhellorob/DevOps-Interview-Questions): no license,
  so all rights are reserved. Used as a topic map only
- [KodeKloud](https://kodekloud.com/blog/devops-interview-questions/),
  [techinterview.org](https://www.techinterview.org/post/3233477276/what-kubernetes-interviewers-actually-ask/),
  [adhdecode](https://adhdecode.com/interviews/kubernetes/pod-crashloopbackoff-debugging/): real troubleshooting
  scenarios (CrashLoopBackOff, Pending, OutOfSync caused by HPA drift, and more)

Verifying answers (the source of truth): kubernetes.io/docs · argo-cd.readthedocs.io · helm.sh/docs ·
developer.hashicorp.com/terraform · docs.aws.amazon.com · docs.docker.com · docs.github.com/actions ·
docs.gitlab.com/ee/ci · jenkins.io/doc · man7.org. Every question carries a `ref` to the documentation page.

## Implementation stages (a commit and push after each one)

0. *(done)* **Base:** rename the folder, rebrand to Ship It, turn Supabase off, hide the games, set the timer to 90s.
1. *(done)* **New question pipeline:** `qsrc/devops/<topic>.py` holds the questions, with the fields
   `q, o, a, why, interview, level, kind, sub, ref`. `build_bank.py` reads them instead of the CSV, and a validator
   refuses to build if the counts, the 50/50 split, the levels, or the spread of correct-answer positions are wrong.
2. *(done)* **Writing the questions in batches**, in weight order: K8s → ArgoCD → CI → AWS → Helm → Terraform → Linux →
   CI tools → Networking. Every batch is validated and committed.
3. *(done)* **Building the 20 papers** by topic weight and level.
4. **Interview mode:** a new screen for the 300 open questions, with a model answer and self-marking.
   *Done.* Authored in `isrc/<topic>.py` as `O()` calls (see `qsrc/qlib.py`): an English question, 3–6 Hebrew
   points a strong answer covers, a likely follow-up, the mistake that loses the point, and a documentation link.
   `python3 build_interview.py` validates counts, splits and Hebrew, writes `isrc/interview.json`;
   `python3 inject_interview.py` puts it into `index.html` as `#ivdata`. Progress is `P.iv[id] = [mark, times, when]`.
5. *(done)* **Learn:** 24 files in `learn_src/`, with lessons, check questions and an exam for each subject.
   Each subject has 3 parts (Hebrew lesson with tables, flows and callouts, then 3 English check questions with
   Hebrew explanations), a summary, and a 10-question exam with a Hebrew note on every option. Authored with
   the shorthand in `learn_src/_h.py`; `python3 build_learn.py` validates and injects. `QA_LEARN` passes all
   24 subjects in a real browser.
6. **Study:** reading chapters for each topic.
7. **Hebrew explanations, QA** (`QA_BANK`, `QA_UI`, and the rest) run in a real browser, then update `STATE.md`.
8. **Games:** adapt the duel and casino to the new bank (the SQL is ready), turned on once there is a new Supabase project.
