# -*- coding: utf-8 -*-
from _h import *

CHAPTER = {
 "nm": "ArgoCD", "em": "🐙", "dom": 1, "secs": [6, 7, 8, 9],
 "sub": "דף עזר: GitOps, Application, sync ו-health, waves ו-hooks, ApplicationSets ותפעול.",
 "topics": [
  {"nm": "GitOps & the Application", "blocks": [
    P("Git הוא מקור האמת, ו-controller בקלאסטר מושך ומיישם כל הזמן. ה-CI כותב ל-Git ולא נוגע בקלאסטר."),
    TABLE(["רכיב", "תפקיד", "כשהוא איטי"],
          ["repo-server", "רינדור Helm/Kustomize", "replicas, memory, parallelism limit"],
          ["application-controller", "reconcile ו-sync", "sharding לפי קלאסטר"],
          ["argocd-server", "UI, API, SSO", "replicas"],
          ["Redis", "cache", "Redis HA"]),
    CODE("""
spec:
  project: shop
  source: {repoURL: https://github.com/acme/gitops, path: apps/api/overlays/prod, targetRevision: main}
  destination: {server: https://kubernetes.default.svc, namespace: shop}
  syncPolicy:
    automated: {prune: true, selfHeal: true}
    syncOptions: [CreateNamespace=true]
""", cap="Application: מאיפה, לאן, מה מותר, ואיך מסנכרנים."),
    KEY("polling כל כ-3 דקות. webhook מה-Git provider מביא שינויים מיד. AppProject מגביל repos, destinations וסוגי משאבים; default מתיר הכול."),
    ASK("Explain GitOps and how Argo CD implements it.",
        "Push-based CD vs pull-based GitOps: what changes for security?",
        "How do you structure repos for multiple environments?",
        "What's the app-of-apps pattern?"),
  ]},
  {"nm": "Sync, health & diff", "blocks": [
    TABLE(["", "Healthy", "Degraded"],
          ["Synced", "תקין", "Git עצמו שבור"],
          ["OutOfSync", "drift שעובד", "דחוף"]),
    TABLE(["OutOfSync בלי שינוי", "פתרון"],
          ["HPA משנה replicas", "להוריד replicas מה-manifest"],
          ["webhook מזריק sidecar או caBundle", "ignoreDifferences + RespectIgnoreDifferences"],
          ["kubectl edit ידני", "selfHeal, או commit לשינוי"],
          ["targetRevision צף", "tag או PR של promotion"]),
    TABLE(["Sync option", "מתי"],
          ["CreateNamespace=true", "namespace לא קיים"],
          ["ServerSideApply=true", "annotation too long, CRDs גדולים"],
          ["Replace=true", "field is immutable (מסוכן)"],
          ["SkipDryRunOnMissingResource=true", "CR עם CRD באותו sync"],
          ["Prune=false (על משאב)", "להגן ממחיקה"]),
    TRAP("Healthy לא אומר שהאפליקציה עובדת: הוא מבוסס על status של משאבים ו-readiness. בדיקה אמיתית: PostSync hook או analysis ב-Argo Rollouts."),
    ASK("An app shows OutOfSync but nobody changed anything. Why?",
        "Synced but Degraded: what does it mean?",
        "How do you stop the HPA and Argo CD fighting?",
        "A sync fails with metadata.annotations: Too long. Fix?"),
  ]},
  {"nm": "Waves, hooks & rollback", "blocks": [
    FLOW("PreSync", "Sync: waves בסדר עולה", "PostSync", "SyncFail", cap="בין waves מחכים ל-Healthy."),
    TABLE(["Annotation", "משמעות"],
          ["`argocd.argoproj.io/sync-wave: \"-1\"`", "קודם; ברירת מחדל 0"],
          ["`argocd.argoproj.io/hook: PreSync`", "migration לפני deploy"],
          ["`argocd.argoproj.io/hook-delete-policy: BeforeHookCreation`", "מוחק את ה-Job הקודם"]),
    TABLE(["רוצים לחזור אחורה", "איך"],
          ["GitOps רגיל", "`git revert`"],
          ["`argocd app rollback`", "רק כש-auto-sync כבוי"],
          ["אוטומטי לפי מדדים", "Argo Rollouts עם analysis"]),
    KEY("Argo CD לא עושה rollback לבד כש-PostSync נכשל. המשאבים כבר הוחלו. בחירום: מכבים auto-sync ל-Application אחד, מתקנים, עושים commit ומדליקים חזרה."),
    TRAP("migration שלא תואמת לגרסה הקודמת שוברת את ה-pods הישנים בזמן ה-rollout ומונעת rollback. expand/contract."),
    ASK("How do you run a DB migration before a deploy with Argo CD?",
        "A sync is stuck Running. How do you unstick it?",
        "How do you handle emergency changes when selfHeal is on?",
        "Why can't argocd app rollback run with auto-sync on?"),
  ]},
  {"nm": "ApplicationSets & operations", "blocks": [
    TABLE(["Generator", "שימוש"],
          ["cluster", "Application לכל קלאסטר לפי labels"],
          ["git directories / files", "Application לכל תיקייה או קובץ"],
          ["matrix", "כל שירות בכל קלאסטר"],
          ["pull request", "סביבת preview לכל PR"]),
    TABLE(["סיכון", "הגנה"],
          ["element נעלם ומוחק Application", "preserveResourcesOnDeletion, applicationsSync: create-update"],
          ["מחיקת Application מוחקת workloads", "`--cascade=false`, RBAC על delete"],
          ["סוד ב-Git", "רוטציה; ESO או Sealed Secrets"],
          ["SSO בלי גישה", "scopes: [groups], שמות קבוצות (Entra: object IDs)"]),
    CODE("""
p, role:shop-dev, applications, get,  shop/*, allow
p, role:shop-dev, applications, sync, shop/*, allow
g, shop-developers, role:shop-dev
""", cap="RBAC ב-argocd-rbac-cm: הרשאות לפי project."),
    KEY("ניטור: argocd_app_info (sync ו-health), sync failures, עומק התור של ה-controller. Notifications עם on-sync-failed לבעלי ה-Application."),
    ASK("Deploy one app to 20 clusters with per-cluster values. How?",
        "An ApplicationSet change deleted apps. What happened?",
        "How do you handle secrets with Argo CD?",
        "One central Argo CD or one per cluster?"),
  ]},
 ],
 "quiz": [
   QZ("Which Argo CD component performs syncs?",
      "The application-controller", "argocd-server", "repo-server", "Dex",
      x="ה-application-controller משווה live מול Git ומבצע sync. repo-server מרנדר, ו-server מגיש UI ו-API."),
   QZ("Which annotation makes a Job run before the rest of the sync?",
      "`argocd.argoproj.io/hook: PreSync`", "`argocd.argoproj.io/sync-wave: \"100\"`",
      "`helm.sh/hook-weight: \"1\"`", "`argocd.argoproj.io/compare-options: IgnoreExtraneous`",
      x="PreSync hook רץ לפני phase ה-Sync. אם הוא נכשל, ה-sync נעצר."),
   QZ("What protects workloads when an ApplicationSet deletes an Application?",
      "`preserveResourcesOnDeletion: true`", "`prune: true`", "`selfHeal: true`", "A sync wave",
      x="עם preserveResourcesOnDeletion, מחיקת Application שנוצר ע\"י ApplicationSet משאירה את המשאבים בקלאסטר."),
   QZ("What is the preferred rollback in a GitOps setup?",
      "Revert the commit in Git", "kubectl edit the Deployment", "Delete the Application", "Restart the repo-server",
      x="git revert משאיר את Git כמקור האמת, ו-Argo CD מיישם את המצב הקודם. עריכה ידנית תידרס ע\"י selfHeal."),
 ],
}
