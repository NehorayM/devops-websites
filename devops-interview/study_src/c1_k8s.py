# -*- coding: utf-8 -*-
from _h import *

CHAPTER = {
 "nm": "Kubernetes", "em": "☸️", "dom": 0, "secs": [0, 1, 2, 3, 4, 5],
 "sub": "דף עזר: פקודות kubectl, מצבי pods, Services, אחסון, שיבוץ, RBAC ושיטת דיבוג.",
 "topics": [
  {"nm": "Workloads & pod states", "blocks": [
    P("כמעט כל שאלת Kubernetes בראיון מתחילה מ-pod שלא עובד. הטבלאות כאן הן מה שכדאי לדעת בעל פה: איזה controller למה, ומה כל STATUS אומר."),
    TABLE(["Controller", "מתי", "מה מיוחד"],
          ["Deployment", "שירות stateless", "ReplicaSet חדש בכל שינוי; rolling update"],
          ["StatefulSet", "DB, Kafka", "שם קבוע, PVC לכל pod, סדר"],
          ["DaemonSet", "agent על כל node", "pod אחד לכל node"],
          ["Job / CronJob", "עבודה שמסתיימת / לפי לוח זמנים", "backoffLimit, concurrencyPolicy"]),
    TABLE(["STATUS", "פירוש", "פקודה ראשונה"],
          ["Pending", "לא שובץ", "`kubectl describe pod` (Events)"],
          ["ImagePullBackOff", "image, tag או הרשאות registry", "`kubectl describe pod`"],
          ["CrashLoopBackOff", "עולה ונופל", "`kubectl logs <pod> --previous`"],
          ["OOMKilled (137)", "עבר memory limit", "Last State ב-describe"],
          ["CreateContainerConfigError", "ConfigMap או Secret חסר", "`kubectl describe pod`"],
          ["Running, לא Ready", "readiness נכשל", "probe ופורט"]),
    CODE("""
kubectl get pods -n shop -o wide
kubectl describe pod api-7d9f -n shop
kubectl logs api-7d9f -n shop --previous
kubectl rollout status deploy/api -n shop
kubectl rollout undo deploy/api -n shop
""", cap="חמש הפקודות שכדאי שיהיו בידיים."),
    KEY("liveness נכשל = restart. readiness נכשל = יוצא מה-endpoints. startup מחזיק את שניהם עד שהאפליקציה עלתה. liveness לא בודק תלויות."),
    ASK("A pod is in CrashLoopBackOff. Walk me through it.",
        "Deployment vs StatefulSet vs DaemonSet: when do you use each?",
        "How do you get zero-downtime rollouts?",
        "What's the difference between liveness and readiness probes?"),
  ]},
  {"nm": "Services, Ingress & DNS", "blocks": [
    P("Service נותן IP ושם יציבים ל-pods שמשתנים. רק pods שהם Ready נכנסים ל-EndpointSlices."),
    TABLE(["סוג", "במשפט"],
          ["ClusterIP", "IP פנימי; ברירת מחדל"],
          ["NodePort", "פורט 30000–32767 על כל node"],
          ["LoadBalancer", "load balancer מהענן"],
          ["Headless", "`clusterIP: None`; DNS מחזיר IPs של pods"],
          ["ExternalName", "CNAME לשם חיצוני"]),
    TREE(["אין endpoints", "selector לא תואם, או pods לא Ready"],
         ["pod IP עובד, ClusterIP לא", "kube-proxy או CNI"],
         ["ClusterIP עובד, שם לא", "CoreDNS, resolv.conf"],
         ["עובד מ-namespace אחד בלבד", "NetworkPolicy"],
         ["Ingress מחזיר 502/504", "backend, פורטים, timeouts"],
         cap="Service שלא עונה: לפי הסדר."),
    TABLE(["שם DNS", "דוגמה"],
          ["Service", "`api.shop.svc.cluster.local`"],
          ["pod של StatefulSet", "`db-0.db.data.svc.cluster.local`"]),
    TRAP("default-deny egress בלי חוק ל-DNS (פורט 53 ל-kube-dns) שובר את כל פתרון השמות. ו-NetworkPolicy עובדת רק אם ה-CNI אוכף אותה."),
    ASK("A Service exists but requests time out. How do you debug it?",
        "Ingress vs a LoadBalancer Service: what's the difference?",
        "How does kube-proxy implement Services?",
        "Pods intermittently fail DNS lookups. Where do you look?"),
  ]},
  {"nm": "Config, Secrets & storage", "blocks": [
    P("קונפיגורציה וסודות מחוץ ל-image; נתונים קבועים ב-PVC. ההחלטות כאן משפיעות על זמינות ועל אובדן נתונים."),
    TABLE(["", "env", "volume"],
          ["מתעדכן בלי restart", "לא", "כן, תוך כדקה (לא עם subPath)"],
          ["מתאים ל", "ערכים קטנים", "קבצי קונפיגורציה וסודות"]),
    TABLE(["מושג", "זכור"],
          ["Secret", "base64 בלבד; הגנה = RBAC, KMS ל-etcd, ESO"],
          ["PVC / PV / StorageClass", "בקשה / דיסק / איך יוצרים"],
          ["reclaimPolicy: Delete", "מחיקת PVC מוחקת את הנתונים"],
          ["WaitForFirstConsumer", "הדיסק נוצר ב-AZ של ה-pod"],
          ["RWO / RWX", "EBS / EFS"]),
    CODE("""
kubectl create configmap app --from-file=app.yaml --dry-run=client -o yaml
kubectl rollout restart deploy/api        # pick up env changes
kubectl describe pvc data-db-0 -n data    # why is it Pending?
""", cap="פקודות שימושיות לקונפיגורציה ואחסון."),
    KEY("PVC ב-Pending בלי pod עם WaitForFirstConsumer זה תקין. עם pod: StorageClass, CSI driver והרשאות IAM שלו."),
    ASK("Are Kubernetes Secrets secure?",
        "You updated a ConfigMap but the app still has the old value. Why?",
        "A StatefulSet pod is stuck after its node died. What's happening?",
        "How do you manage secrets for Kubernetes on AWS?"),
  ]},
  {"nm": "Scheduling & autoscaling", "blocks": [
    P("ה-scheduler מסתכל על requests, לא על שימוש. limits נאכפים בזמן ריצה."),
    TABLE(["", "requests", "limits"],
          ["שימוש", "שיבוץ והבטחה", "תקרה"],
          ["CPU מעבר", "—", "throttling"],
          ["זיכרון מעבר", "—", "OOMKilled"]),
    TABLE(["כלי", "מושך / דוחה / מפזר"],
          ["taint + toleration", "node דוחה; toleration רק מתיר"],
          ["node affinity", "מושך ל-nodes"],
          ["pod anti-affinity", "מרחיק מ-pods אחרים"],
          ["topology spread", "פיזור בין zones או nodes"]),
    TABLE(["Autoscaler", "משנה", "לפי"],
          ["HPA", "replicas", "CPU ביחס ל-requests, או custom metrics"],
          ["KEDA", "replicas (גם לאפס)", "אירועים: תור, lag"],
          ["Cluster Autoscaler", "nodes ב-node group", "pods שלא נכנסו"],
          ["Karpenter", "instances לפי הצורך", "pods שלא נכנסו, consolidation"]),
    TRAP("HPA בלי CPU requests מראה `<unknown>`. ו-autoscaler של nodes לא מוסיף node כשה-CPU גבוה, רק כשיש pods ב-Pending."),
    ASK("A pod is Pending with Insufficient cpu, but nodes look idle. Why?",
        "Would you set CPU limits?",
        "How does the HPA decide how many replicas to run?",
        "Taints and tolerations vs node affinity?"),
  ]},
  {"nm": "RBAC & security", "blocks": [
    P("שלושה שערים: authentication, authorization (RBAC), admission. RBAC רק נותן הרשאות; אין deny."),
    TABLE(["אובייקט", "היקף"],
          ["Role + RoleBinding", "namespace"],
          ["ClusterRole + RoleBinding", "תבנית משותפת, namespace אחד"],
          ["ClusterRole + ClusterRoleBinding", "כל הקלאסטר"]),
    TABLE(["securityContext", "למה"],
          ["`runAsNonRoot: true`", "לא root"],
          ["`readOnlyRootFilesystem: true`", "image לא משתנה בזמן ריצה"],
          ["`allowPrivilegeEscalation: false`", "אין העלאת הרשאות"],
          ["`capabilities: drop: [ALL]`", "מינימום הרשאות kernel"],
          ["`seccompProfile: RuntimeDefault`", "פחות syscalls"]),
    CODE("""
kubectl auth can-i list pods -n shop --as system:serviceaccount:shop:api
kubectl auth whoami
kubectl label ns shop pod-security.kubernetes.io/enforce=restricted
""", cap="בדיקת הרשאות ואכיפת Pod Security."),
    KEY("webhook עם failurePolicy: Fail שנפל חוסם יצירת משאבים. מחריגים את kube-system ואת ה-namespace שלו, ומריצים כמה replicas."),
    ASK("How would you harden a pod's securityContext?",
        "A CI pipeline gets Forbidden. How do you fix it properly?",
        "What replaced PodSecurityPolicy?",
        "You suspect a pod was compromised. What do you do?"),
  ]},
  {"nm": "Troubleshooting method", "blocks": [
    P("בראיון, שאלת troubleshooting היא שאלה על שיטה. אומרים את השיטה בקול לפני הפקודות."),
    STEPS("היקף: מה, למי, ממתי.", "מה השתנה: deploy, קונפיגורציה, שדרוג.",
          "לעצור נזק: rollback אם משתמשים נפגעים.", "שכבה אחרי שכבה: pod, Service, node, קלאסטר, תלויות.",
          "postmortem והתראה טובה יותר."),
    TABLE(["Node condition", "לבדוק"],
          ["NotReady", "kubelet, runtime, רשת ל-API"],
          ["MemoryPressure", "requests שלא משקפים שימוש"],
          ["DiskPressure", "images, לוגים, emptyDir"],
          ["PIDPressure", "דליפת תהליכים"]),
    CODE("""
kubectl get events -A --sort-by=.lastTimestamp
kubectl describe node ip-10-0-1-23
kubectl debug -it api-7d9f --image=busybox --target=api
kubectl -v=6 get pods      # which API call is slow?
""", cap="כלים לקלאסטר כולו."),
    KEY("golden signals: latency, traffic, errors, saturation. metrics אומרים שיש בעיה, logs מה קרה, traces איפה."),
    ASK("A node is NotReady. How do you investigate?",
        "After a deploy, errors jump but pods are healthy. What now?",
        "A namespace is stuck in Terminating. Why?",
        "What would you alert on for the cluster itself?"),
  ]},
  {"nm": "kubectl power moves", "blocks": [
    P("בראיון מעשי, או ב-live debugging, מהירות עם kubectl נראית מיד. אלה הפקודות שחוסכות דקות ומראות ניסיון."),
    TABLE(["צורך", "פקודה"],
          ["YAML ראשוני בלי לכתוב", "`kubectl create deploy api --image=nginx --dry-run=client -o yaml`"],
          ["לראות מה apply ישנה", "`kubectl diff -f deploy.yaml`"],
          ["תיעוד של שדה", "`kubectl explain deployment.spec.strategy.rollingUpdate`"],
          ["רק שדות שמעניינים", "`kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName`"],
          ["ערך אחד", "`kubectl get pod api-0 -o jsonpath='{.status.podIP}'`"],
          ["צריכה בפועל", "`kubectl top pods --sort-by=memory`"],
          ["גישה מקומית לשירות", "`kubectl port-forward svc/api 8080:80`"],
          ["restart מסודר", "`kubectl rollout restart deploy/api`"]),
    CODE("""
# כל ה-pods שלא Running בכל הקלאסטר
kubectl get pods -A --field-selector=status.phase!=Running

# images שרצים כרגע, בלי כפילויות
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\\n' | sort -u

# למה ה-pod נמחק או הוחלף: מי הבעלים שלו
kubectl get pod api-7d9f -o jsonpath='{.metadata.ownerReferences[0].kind}'
""", cap="שלוש שורות שכדאי לזכור"),
    KEY("`--dry-run=server` שולח את הבקשה ל-API server ומריץ admission ו-validation בלי לשמור. זה תופס שגיאות ש-`--dry-run=client` לא רואה, כמו מדיניות Kyverno או שדה לא חוקי."),
    TRAP("`kubectl edit` ו-`kubectl scale` בקלאסטר שמנוהל ב-GitOps יוצרים drift: Argo CD יחזיר את השינוי, או יציג OutOfSync. בסביבה כזאת משנים ב-Git."),
    ASK("How would you list every image running in a cluster?",
        "What's the difference between `--dry-run=client` and `--dry-run=server`?",
        "How do you preview what `kubectl apply` will change?"),
  ]},
  {"nm": "Production readiness checklist", "blocks": [
    P("שאלה נפוצה ל-Mid-Senior: 'מה בודקים לפני שמעלים שירות חדש לפרודקשן ב-Kubernetes?'. הרשימה הזאת היא תשובה מסודרת."),
    TABLE(["תחום", "מה צריך להיות", "למה"],
          ["Probes", "readiness לכל שירות; liveness רק לתקיעה אמיתית; startup לאתחול ארוך", "traffic רק ל-pods מוכנים, בלי restart loops"],
          ["Resources", "requests לכל container; memory limit", "שיבוץ נכון, HPA, בלי OOM של שכנים"],
          ["Replicas ו-PDB", "לפחות 2-3 replicas, `maxUnavailable: 1`", "שדרוג nodes בלי downtime"],
          ["פיזור", "topologySpreadConstraints לפי zone", "AZ שנופל לא מוריד את השירות"],
          ["כיבוי", "SIGTERM מטופל, preStop sleep", "בלי 502 ב-rollout"],
          ["אבטחה", "runAsNonRoot, readOnlyRootFilesystem, בלי privileged, ServiceAccount ייעודי", "צמצום נזק אם נפרץ"],
          ["Images", "tag או digest קבועים, נסרקים, חתומים", "חזרתיות ו-supply chain"],
          ["Observability", "metrics, לוגים מובנים, traces, התראות על SLO", "לדעת לפני המשתמשים"]),
    FLOW("PR עם manifests", "CI: lint, kubeconform, policy", "staging + smoke test", "rollout הדרגתי (canary)", "SLO ו-alerts פעילים", cap="המסלול לפרודקשן"),
    KEY("תשובה טובה מסודרת לפי סיכון: מה מונע downtime (probes, replicas, PDB, כיבוי), מה מונע תקלות עומס (resources, HPA), מה מונע פריצה (securityContext, RBAC, NetworkPolicy), ומה מאפשר לדעת שמשהו לא בסדר (observability)."),
    ASK("What do you check before a new service goes to production on Kubernetes?",
        "How do you make a rollout safe for a stateful service?",
        "Which defaults in Kubernetes are unsafe for production?"),
  ]},
 ],
 "quiz": [
   QZ("Which probe failure removes a pod from Service endpoints without restarting it?",
      "Readiness", "Liveness", "Startup", "None of them",
      x="readiness מוציא מהתנועה; liveness עושה restart; startup רק מחכה עם האחרים עד שהאפליקציה עלתה."),
   QZ("What does exit code 137 usually mean in Kubernetes?",
      "The container was SIGKILLed, typically OOMKilled", "A normal shutdown", "The image was not found", "A failed readiness probe",
      x="137 הוא 128+9, כלומר SIGKILL. ברוב המקרים זה OOMKilled אחרי חריגה מה-memory limit."),
   QZ("A Service has no endpoints. What do you check first?",
      "That its selector matches Ready pods' labels", "CoreDNS logs", "The Ingress controller", "The node's disk",
      x="EndpointSlices ריקים אומרים שאין pods תואמים ו-Ready. זה הצעד הראשון לפני DNS או NetworkPolicy."),
   QZ("What triggers the Cluster Autoscaler to add a node?",
      "Pods that can't be scheduled", "High average CPU", "A new namespace", "A failed liveness probe",
      x="Cluster Autoscaler מגיב ל-pods ב-Pending שאין להם מקום. ניצולת גבוהה לבדה לא מוסיפה nodes."),
  QZ("What does `kubectl apply --dry-run=server` catch that `--dry-run=client` doesn't?",
      "Admission and server-side validation errors, such as policy denials", "YAML indentation errors", "Missing kubeconfig", "Slow nodes",
      x="dry-run בצד השרת עובר admission ו-validation בלי לשמור, ולכן תופס מדיניות ושדות לא חוקיים."),
   QZ("Why spread replicas with topologySpreadConstraints by zone?",
      "So losing one availability zone doesn't take the whole service down", "To lower the image size", "To avoid needing a PDB", "To speed up DNS",
      x="בלי פיזור, ה-scheduler יכול לשים את כל ה-replicas באותו AZ, ונפילה שלו מורידה את השירות."),
 ],
}
