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
    ASK(("Explain the structure of a GitHub Actions workflow.",
         "קובץ YAML בתיקייה `.github/workflows/`. בראש `on:` מגדיר מתי הוא רץ (push, pull_request, schedule, workflow_dispatch), עם סינון לפי branches ו-paths. `permissions:` קובע מה ה-GITHUB_TOKEN רשאי לעשות. תחת `jobs:` כל job רץ על runner משלו לפי `runs-on`, וה-jobs רצים במקביל אלא אם `needs` קובע סדר. כל job הוא רשימת steps: `uses:` מריץ action ו-`run:` מריץ פקודת shell. מעל זה יש `strategy.matrix`, `environment` לאישורים ו-`concurrency` למניעת הרצות חופפות."),
        ("Why pin third-party actions to a SHA?",
         "tag כמו `@v4` אפשר להזיז. אם ה-repo של ה-action נפרץ, התוקף מזיז את ה-tag לקוד זדוני וכל workflow שמשתמש בו מריץ אותו עם ה-secrets וה-token שלכם. זה קרה ב-2025 עם `tj-actions/changed-files`. לפי GitHub, commit SHA מלא הוא הדרך היחידה להפנות לגרסה שלא תשתנה. כותבים `uses: owner/action@<sha> # v4.2.1` ונותנים ל-Dependabot לעדכן את ה-SHA, כדי לא להיתקע על גרסה ישנה."),
        ("How do you prevent secrets leaking from fork PRs?",
         "האירוע `pull_request` מ-fork כבר רץ בלי secrets ועם GITHUB_TOKEN לקריאה בלבד, אז שם הקוד הזר לא רואה כלום. הסכנה היא `pull_request_target`, שרץ בהקשר של ה-repo הראשי עם secrets: אסור לעשות בו checkout לקוד של ה-PR ולהריץ אותו. בנוסף: לדרוש אישור לפני שמריצים workflows של תורמים חיצוניים, לשים secrets של deploy ב-environment עם reviewers, ולתת `permissions` מינימליות לכל job."),
        ("A workflow doesn't run on push. What do you check?",
         "קודם הלשונית Actions: שם רואים שגיאת YAML בקובץ. אחר כך ה-trigger: האם `on.push.branches` או `paths` מסננים את ה-push הזה, והאם הקובץ קיים ב-`.github/workflows/` בענף שנדחף. האם בהודעת ה-commit יש `[skip ci]`. האם ה-push נעשה עם GITHUB_TOKEN, שלא מפעיל workflows חדשים (חוץ מ-workflow_dispatch ו-repository_dispatch). ולבסוף האם Actions או ה-workflow עצמו כבויים בהגדרות ה-repo.")),
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
    ASK(("Explain stages, jobs, rules and needs.",
         "job הוא יחידת עבודה עם `script` שרצה על runner. `stages` קובעים סדר: כל ה-jobs באותו stage רצים במקביל, וה-stage הבא מתחיל רק כשכולם הצליחו. `rules` מחליטים אם job בכלל נכנס ל-pipeline, לפי `if` על משתנים, `changes` על קבצים או `exists`, ויכולים להפוך אותו ל-`when: manual`. `needs` הופך את ה-pipeline ל-DAG: job מתחיל ברגע שה-jobs שהוא תלוי בהם סיימו, בלי לחכות לכל ה-stage, ומוריד רק את ה-artifacts שלהם."),
        ("A job is stuck in pending. Why?",
         "pending אומר שאף runner לא לקח את ה-job. הסיבות הנפוצות: ה-`tags` של ה-job לא תואמים אף runner, או שה-job בלי tags וה-runner מוגדר לא להריץ untagged jobs. runner שמוגדר protected מריץ רק ענפים ו-tags מוגנים. ה-runner offline או paused, או שהגיע למגבלת `concurrent` ב-`config.toml`. גם shared runners כבויים לפרויקט או מכסת compute minutes שנגמרה משאירים jobs ב-pending."),
        ("Cache vs artifacts?",
         "`cache` נועד להאיץ: תלויות כמו `node_modules` או `.m2`, לפי `key`, נשמר על ה-runner או ב-storage משותף, ועובד בגישת best effort. הוא יכול להיות ריק, וה-job חייב לעבוד גם בלעדיו. `artifacts` נועדו להעביר תוצרים: מה שה-build יצר עולה ל-GitLab, יורד אוטומטית ל-jobs ב-stages הבאים (או לפי `needs`), אפשר להוריד אותו מה-UI ויש לו `expire_in`. תוצר שה-deploy צריך עובר תמיד כ-artifact."),
        ("How do you stop two deploys running at once?",
         "ב-GitLab שמים על ה-job `resource_group: production`. GitLab מריץ בכל רגע רק job אחד מאותה קבוצה, גם בין pipelines שונים, והשאר מחכים בתור. אפשר לבחור `process_mode` כמו `oldest_first`. בנוסף כדאי להפעיל את Prevent outdated deployment jobs, כדי ש-pipeline ישן לא יפרוס מעל גרסה חדשה. המקבילות: `concurrency` עם group ב-GitHub Actions, ו-`disableConcurrentBuilds()` או `lock` של Lockable Resources ב-Jenkins.")),
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
    ASK(("Declarative vs scripted pipelines? What's a shared library?",
         "declarative הוא בלוק `pipeline {}` עם מבנה קבוע: `agent`, `stages`, `when`, `post`, `options`. Jenkins בודק את התחביר לפני הריצה והוא קל לקריאה, ולכן הוא ברירת המחדל היום. scripted הוא Groovy חופשי בתוך `node {}`: גמיש יותר וקשה יותר לתחזק. shared library היא repo נפרד עם קוד Groovy: steps גלובליים ב-`vars/` ומחלקות ב-`src/`. טוענים אותה עם `@Library('ci-lib@v3') _` ומנעלים לגרסה, כך שכל הצוותים משתמשים באותם steps."),
        ("The Jenkins controller is slow and unstable. What do you check?",
         "קודם האם builds רצים על ה-controller: צריך 0 executors עליו. אחר כך ה-JVM: heap (`-Xmx`), GC logs ו-thread dumps. הדיסק של `JENKINS_HOME`: היסטוריית builds בלי `buildDiscarder` ממלאת אותו. כמות ה-plugins והגרסאות שלהם, כי plugin עם memory leak מפיל את כל ה-controller. polling של SCM במקום webhooks. ולוגיקת Groovy כבדה ב-pipeline, שרצה על ה-controller ולא על ה-agent."),
        ("How do you secure Jenkins?",
         "אימות דרך SSO והרשאות לפי roles או matrix, בלי גישה אנונימית. 0 executors על ה-controller ו-agents זמניים, כדי ש-build לא יגיע ל-`JENKINS_HOME` ול-credentials. credentials בתוך folders עם scope לכל צוות, ושימוש בהם רק דרך `withCredentials`. עדכון core ו-plugins לפי ה-security advisories, ומחיקת plugins שלא בשימוש. pipelines ב-Groovy sandbox עם אישור סקריפטים מבוקר, CSRF מופעל, ו-Jenkins לא חשוף ישירות לאינטרנט."),
        ("Jenkins vs GitLab CI vs GitHub Actions: when each?",
         "GitHub Actions כשהקוד ב-GitHub: מובנה, Marketplace גדול, hosted runners ו-OIDC לענן בלי הגדרות. GitLab CI כשעובדים ב-GitLab: הכול באותו מקום, כולל registry, environments ו-merge request pipelines, וקל להריץ self-managed. Jenkins כשצריך שליטה מלאה, הרצה on-prem, אינטגרציות ישנות או pipelines מורכבים שכבר קיימים. המחיר הוא תחזוקה: plugins, שדרוגים ואבטחה של ה-controller נופלים עליכם.")),
  ]},
  {"nm": "Same pipeline, three tools", "blocks": [
    P("שאלה נפוצה: 'עבדת עם Jenkins, איך זה נראה ב-GitHub Actions?'. אותו pipeline בשלושת הכלים מראה שהמושגים זהים, ורק התחביר שונה."),
    TABLE(["מושג", "GitHub Actions", "GitLab CI", "Jenkins"],
          ["קובץ", "`.github/workflows/*.yml`", "`.gitlab-ci.yml`", "`Jenkinsfile`"],
          ["יחידת עבודה", "job → steps", "job בתוך stage", "stage → steps"],
          ["איפה רץ", "`runs-on:`", "`tags:` של runner, `image:`", "`agent { ... }`"],
          ["סודות", "`secrets.X`, environments", "CI/CD variables (masked, protected)", "Credentials + `withCredentials`"],
          ["cache", "`actions/cache`", "`cache:` עם key", "plugin או volume ב-agent"],
          ["artifacts", "`upload-artifact`", "`artifacts:`", "`archiveArtifacts`"],
          ["ענף מוגבל", "`if: github.ref == 'refs/heads/main'`", "`rules: - if: $CI_COMMIT_BRANCH == \"main\"`", "`when { branch 'main' }`"]),
    CODE("""pipeline {
  agent { kubernetes { yamlFile 'ci/pod.yaml' } }
  options { disableConcurrentBuilds(); timeout(time: 30, unit: 'MINUTES') }
  stages {
    stage('Test')  { steps { sh 'make test' } }
    stage('Build') { steps { sh 'make image' } }
    stage('Deploy') {
      when { branch 'main' }
      steps { input 'Deploy to prod?'; sh 'make deploy' }
    }
  }
}""", cap="Jenkins declarative: agent ב-Kubernetes, timeout, אישור ידני"),
    KEY("המושגים שעוברים בין כלים: triggers, jobs ו-DAG, runners, cache מול artifacts, סודות מוגנים לפי ענף או סביבה, ואישור ידני ל-deploy. מי שמבין אותם לומד כלי חדש בשבוע."),
    TRAP("ב-GitLab, משתנה שמוגדר protected זמין רק ל-pipelines על branches או tags מוגנים. deploy מ-branch רגיל ייכשל עם משתנה ריק, בלי שגיאה ברורה."),
    ASK(("How would you migrate a Jenkins pipeline to GitHub Actions?",
         "קודם מיפוי: stages הופכים ל-jobs עם `needs`, `agent` ל-`runs-on` (hosted או self-hosted runners), credentials ל-secrets ו-environments, ומפתחות ענן ל-OIDC. shared library הופכת ל-reusable workflows או composite actions, `when { branch }` ל-`if`, ו-`input` ל-environment עם required reviewers. הכלי `gh actions-importer` עושה audit ו-dry-run ונותן טיוטה. מעבירים repo אחד, מריצים במקביל ל-Jenkins ומשווים תוצאות לפני שמכבים את הישן."),
        ("Cache vs artifacts: what's the difference?",
         "cache מאיץ: שומר תלויות בין ריצות לפי key, ואין הבטחה שיהיה שם, אז ה-job צריך לעבוד גם בלעדיו. artifacts מעבירים תוצרים בין jobs ושומרים אותם להורדה, עם תוקף. ב-GitHub Actions אלה `actions/cache` מול `actions/upload-artifact` ו-`download-artifact`. ב-GitLab `cache:` מול `artifacts:`. ב-Jenkins `archiveArtifacts` או `stash`, ו-cache דרך volume או plugin. הטעות הנפוצה היא להעביר את תוצר ה-build דרך cache."),
        ("How do you restrict a deploy job to the main branch in each tool?",
         "ב-GitHub Actions `if: github.ref == 'refs/heads/main'` על ה-job, ו-environment שמאפשר deploy רק מ-main ומחזיק את ה-secrets. ב-GitLab `rules: - if: $CI_COMMIT_BRANCH == \"main\"`, עם protected environment ומשתנים protected שזמינים רק לענפים מוגנים. ב-Jenkins בפרויקט multibranch, `when { branch 'main' }` על ה-stage. התנאי ב-YAML לבד לא מספיק: ההגנה האמיתית היא שה-secrets זמינים רק ל-main.")),
  ]},
 ],
 "quiz": [
   QZ("What replaced `only`/`except` in GitLab CI?",
     ("`rules`", "נכון. `rules` תומכים ב-`if`, `changes` ו-`exists`, ומחליפים את `only` ו-`except`. לא מערבבים אותם באותו job."),
     ("`needs`", "needs קובע תלויות בין jobs (DAG), לא את התנאים שקובעים אם job ירוץ בכלל."),
     ("`stages`", "stages קובעים סדר כללי של ה-pipeline. הם לא תנאים על jobs בודדים."),
     ("`extends`", "extends משמש לשימוש חוזר בהגדרות של job אחר, לא לקביעה מתי job רץ."),
     x="`rules` תומכים ב-`if`, `changes` ו-`exists`. לא מערבבים אותם עם `only`/`except` באותו job."),
   QZ("Which should pass build output between jobs?",
     ("Artifacts", "נכון. artifacts מובטחים להגיע ל-job הבא, עם שם ו-retention. הם המנגנון להעברת תוצרי build."),
     ("The cache", "cache נועד להאצה ויכול להיות ריק. job שסומך עליו לקבל תוצר עלול לרוץ בלעדיו."),
     ("Environment variables", "משתני סביבה מתאימים לערכים קטנים, לא לקבצים, ולא עוברים אוטומטית בין jobs."),
     ("Git tags", "tag מסמן commit מסוים ב-Git. הוא לא מעביר קבצים שנבנו בתוך job לשום מקום."),
     x="artifacts מובטחים להגיע ל-job הבא. cache נועד להאצה ויכול להיות ריק."),
   QZ("Why set Jenkins controller executors to zero?",
     ("So builds never run on the controller", "נכון. build על ה-controller יכול לגשת לכל ה-credentials וה-config. agents נפרדים, רצוי זמניים, מבודדים אותו."),
     ("To make the web UI faster for users", "זה אולי תוצאת לוואי, אבל לא הסיבה. העיקר הוא בידוד של קוד build מהסודות."),
     ("To disable the plugins that run inside the controller", "executors לא קשורים ל-plugins. plugins ממשיכים לרוץ ב-controller."),
     ("To allow anonymous access to builds", "executors לא קשורים להרשאות גישה. גישה אנונימית דווקא צריך לכבות."),
     x="build על ה-controller יכול לגשת לכל ה-credentials וה-config. agents נפרדים מבודדים אותו."),
  QZ("A GitLab deploy job on a feature branch sees an empty value for a CI/CD variable. Why?",
    ("It's protected, so only pipelines on protected branches or tags get it", "נכון. משתנה protected נחשף רק ל-pipelines שרצים על refs מוגנים. זו הגנה מכוונת על סודות פרודקשן."),
    ("CI/CD variables are only available in the test stage", "משתנים זמינים בכל stage. מה שמגביל אותם הוא protected, environment scope או masked."),
    ("The runner's cache is stale and still holds an old, empty value", "משתנים לא נשמרים ב-cache של ה-runner. הם מוזרקים מחדש בכל job."),
    ("The job has no `image:`, so variables aren't injected", "משתנים מוזרקים גם בלי image, למשל ב-shell executor. image לא קשור לזה."),
    x="משתנה protected נחשף רק ל-pipelines שרצים על refs מוגנים. זו הגנה מכוונת על סודות פרודקשן."),
 ],
}
