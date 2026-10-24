# -*- coding: utf-8 -*-
from _h import *

CHAPTER = {
 "nm": "Jenkins, GitLab CI & GitHub Actions", "em": "🔁", "dom": 1, "secs": [23],
 "sub": "דף עזר: המבנה של כל כלי, runners ו-artifacts, סודות, הרשאות ותפעול Jenkins.",
 "topics": [
  {"nm": "GitHub Actions", "blocks": [
    CODE("""
on: {pull_request: {}, push: {branches: [main]}}
permissions: {contents: read}
concurrency: {group: deploy-prod, cancel-in-progress: false}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<full-commit-sha>
      - run: make test
  deploy:
    needs: test
    environment: production        # required reviewers
    permissions: {id-token: write, contents: read}   # OIDC to AWS
    runs-on: ubuntu-latest
    steps:
      - run: make deploy
""", cap="jobs מקבילים, needs לסדר, environment לאישור, OIDC ו-concurrency."),
    TABLE(["נושא", "זכור"],
          ["שימוש חוזר", "reusable workflows (`workflow_call`), composite actions"],
          ["actions צד שלישי", "pin ל-SHA מלא"],
          ["fork PRs", "בלי secrets; זהירות עם pull_request_target"],
          ["workflow לא רץ", "triggers ו-paths, YAML, push של GITHUB_TOKEN"],
          ["matrix", "תת-קבוצה ב-PR, הכול ב-nightly"]),
    KEY("permissions מינימליות לכל job. Resource not accessible by integration = ה-token בלי הרשאת כתיבה."),
    ASK("Explain the structure of a GitHub Actions workflow.",
        "Why pin third-party actions to a SHA?",
        "How do you prevent secrets leaking from fork PRs?",
        "A workflow doesn't run on push. What do you check?"),
  ]},
  {"nm": "GitLab CI", "blocks": [
    CODE("""
stages: [test, build, deploy]
test:
  stage: test
  script: [make test]
  rules: [{changes: ["api/**/*"]}]
build:
  stage: build
  needs: [test]
  script: [make build]
  artifacts: {paths: [dist/]}
deploy-prod:
  stage: deploy
  resource_group: production
  environment: production
  rules: [{if: '$CI_COMMIT_BRANCH == "main"', when: manual}]
  script: [make deploy]
""", cap="stages, rules, needs, artifacts, resource_group ו-environment."),
    TABLE(["נושא", "זכור"],
          ["rules", "החליפו את only/except; לא לערבב"],
          ["needs", "DAG; מתחיל לפני שה-stage נגמר"],
          ["cache מול artifacts", "האצה / העברת תוצרים"],
          ["job ב-pending", "tags של runner, runner מוגן, concurrent"],
          ["שימוש חוזר", "include, CI/CD components; trigger ל-downstream"]),
    TRAP("תוצרי build דרך cache. cache יכול להיות ריק; תוצרים עוברים כ-artifacts."),
    ASK("Explain stages, jobs, rules and needs.",
        "A job is stuck in pending. Why?",
        "Cache vs artifacts?",
        "How do you stop two deploys running at once?"),
  ]},
  {"nm": "Jenkins", "blocks": [
    CODE("""
@Library('ci-lib@v3') _
pipeline {
  agent { kubernetes { yamlFile 'ci/pod.yaml' } }
  options { timeout(time: 30, unit: 'MINUTES'); buildDiscarder(logRotator(numToKeepStr: '30')) }
  stages {
    stage('Test')  { steps { sh 'make test' } }
    stage('Build') { steps { sh 'make build' } }
    stage('Deploy') { when { branch 'main' } steps { deployApp env: 'prod' } }
  }
  post { failure { notifySlack() } }
}
""", cap="declarative pipeline עם shared library, agent זמני ו-post."),
    TABLE(["בפרודקשן", "למה"],
          ["0 executors על ה-controller", "builds לא נוגעים ב-credentials וב-config"],
          ["agents זמניים (Kubernetes plugin)", "בידוד וסקייל"],
          ["JCasC ו-plugins.txt ב-image", "Jenkins ניתן לשחזור"],
          ["credentials עם folders", "scope לכל צוות"],
          ["SSO ו-roles", "בלי גישה אנונימית"]),
    KEY("plugin update ששובר pipelines: לבדוק ב-staging Jenkins, לנעול גרסאות, ולשמור דרך לחזור."),
    ASK("Declarative vs scripted pipelines? What's a shared library?",
        "The Jenkins controller is slow and unstable. What do you check?",
        "How do you secure Jenkins?",
        "Jenkins vs GitLab CI vs GitHub Actions: when each?"),
  ]},
 ],
 "quiz": [
   QZ("What replaced `only`/`except` in GitLab CI?",
      "`rules`", "`needs`", "`stages`", "`extends`",
      x="rules תומכים ב-if, changes ו-exists. לא מערבבים אותם עם only/except באותו job."),
   QZ("Which should pass build output between jobs?",
      "Artifacts", "Cache", "Environment variables", "Git tags",
      x="artifacts מובטחים להגיע ל-job הבא. cache נועד להאצה ויכול להיות ריק."),
   QZ("Why set Jenkins controller executors to zero?",
      "So builds never run on the controller", "To speed up the UI", "To disable plugins", "To allow anonymous access",
      x="build על ה-controller יכול לגשת לכל ה-credentials וה-config. agents נפרדים מבודדים אותו."),
 ],
}
