# -*- coding: utf-8 -*-
from _h import *

CHAPTER = {
 "nm": "Helm", "em": "⛵", "dom": 0, "secs": [17, 18],
 "sub": "דף עזר: מבנה chart, values ו-templates, upgrade ו-rollback, ו-releases תקועים.",
 "topics": [
  {"nm": "Charts, values & templates", "blocks": [
    FLOW("values.yaml של ה-chart", "values של parent", "קבצי -f לפי הסדר", "--set", cap="סדר עדיפות: האחרון גובר."),
    TABLE(["זכור", "פירוש"],
          ["lists", "מוחלפים בשלמותם, לא מתמזגים"],
          ["version / appVersion", "גרסת chart (עולה בכל שינוי) / גרסת האפליקציה"],
          ["release history", "Secret לכל revision ב-namespace"],
          ["crds/", "מותקן פעם אחת; לא מתעדכן ולא נמחק"],
          ["subchart values", "תחת השם שלו; global לכולם"]),
    TABLE(["פונקציה", "למה"],
          ["`include` + `nindent`", "helpers עם הזחה נכונה"],
          ["`toYaml`", "בלוק שלם מ-values"],
          ["`required`", "לעצור כשחסר ערך חובה"],
          ["`default`", "ערך חלופי"],
          ["`quote`", "\"false\" ו-1.10 לא יפתיעו"]),
    CODE("""
helm template api ./chart -f values-prod.yaml --debug
helm lint ./chart
helm template api ./chart | kubeconform -strict -
""", cap="דיבוג ובדיקה בלי קלאסטר."),
    KEY("checksum annotation על ה-pod template (sha256 של ה-configmap) גורם ל-rollout בכל שינוי קונפיגורציה."),
    ASK("How are values merged and in what order?",
        "A template breaks with a YAML parse error. How do you debug it?",
        "How does Helm handle CRDs, and why is it tricky?",
        "How do you test a chart before releasing it?"),
  ]},
  {"nm": "Releases & troubleshooting", "blocks": [
    TABLE(["דגל", "למה ב-CI"],
          ["--install", "אותה פקודה גם בפעם הראשונה"],
          ["--wait", "pods קורסים = pipeline נכשל"],
          ["--atomic", "rollback אוטומטי"],
          ["--timeout", "גבול ברור"],
          ["--history-max", "לא לצבור Secrets"]),
    TABLE(["שגיאה", "צעד ראשון"],
          ["another operation is in progress", "`helm history`, ואז rollback"],
          ["resource already exists", "אימוץ: annotations ו-label managed-by"],
          ["timed out waiting", "pods ו-events"],
          ["helm list ריק", "`-A --all`; או Argo CD בלי release"]),
    CODE("""
helm upgrade --install api ./chart -n shop -f values-prod.yaml --atomic --timeout 10m
helm history api -n shop
helm rollback api 41 -n shop --wait
helm diff upgrade api ./chart -n shop -f values-prod.yaml
""", cap="upgrade בטוח, היסטוריה, rollback ו-diff."),
    TRAP("rollback של Helm מחזיר manifests, לא את ה-DB, נתונים ב-PVC, CRDs או משאבים חיצוניים."),
    KEY("סודות לא ב-values: existingSecret, ESO או SOPS. Helm שומר manifests מרונדרים, כולל Secrets, בהיסטוריה."),
    ASK("A release is stuck in pending-upgrade. How do you fix it?",
        "What does --atomic do?",
        "A rollback didn't fix the app. What didn't roll back?",
        "How do you change a third-party chart without forking it?"),
  ]},
 ],
 "quiz": [
   QZ("A values file overrides a list. What happens to the default list?",
      "It is replaced entirely", "The lists are merged", "The default wins", "Helm errors out",
      x="maps מתמזגים לעומק, lists מוחלפים. זו הפתעה נפוצה עם tolerations ו-env."),
   QZ("Where does Helm 3 store release revisions?",
      "As Secrets in the release namespace", "In Tiller", "In the chart repo", "On the local machine",
      x="כל revision הוא Secret בקלאסטר, ולכן אין צורך ב-Tiller וההיסטוריה זמינה לכל מי שיש לו גישה."),
   QZ("Which flag makes CI fail when the new pods crash after an upgrade?",
      "`--wait`", "`--dry-run`", "`--reuse-values`", "`--create-namespace`",
      x="בלי wait, Helm מסתיים ברגע שה-API קיבל את ה-manifests. wait מחכה שה-workloads יהיו Ready."),
 ],
}
