# -*- coding: utf-8 -*-
from _h import *

SUBJECT = {
 "sec": 4, "nm": "Kubernetes: RBAC & Security", "tag": "Who can do what, and how pods are locked down",
 "deep": True,
 "modules": [

  MOD("rbac", "RBAC ו-ServiceAccounts",
      "להסביר Role, ClusterRole ו-bindings, ולבדוק מה זהות מסוימת מורשית לעשות.",
      [H("שלושה שערים לכל בקשה"),
       P("כל בקשה ל-API server עוברת שלושה שלבים לפי הסדר. **authentication** קובע מי אתה: תעודת client, token של ServiceAccount, או OIDC מספק זהויות. ל-Kubernetes אין אובייקט User: שם המשתמש והקבוצות מגיעים מהתעודה או מה-token. **authorization** קובע מה מותר לך, וכמעט תמיד זה RBAC. **admission** בודק אם הבקשה עומדת במדיניות, ויכול גם לשנות אותה. רק בקשה שעברה את שלושתם נשמרת ב-etcd."),
       FLOW("בקשה ל-API", "Authentication", "Authorization (RBAC)", "Admission", "נשמר ב-etcd"),
       H("ארבעת האובייקטים של RBAC"),
       TABLE(["אובייקט", "היקף", "מה הוא עושה"],
             ["Role", "namespace", "רשימת הרשאות: verbs על resources"],
             ["ClusterRole", "קלאסטר", "הרשאות ברמת הקלאסטר, או תבנית לשימוש חוזר בכל namespace"],
             ["RoleBinding", "namespace", "נותן Role או ClusterRole ל-subject בתוך namespace אחד"],
             ["ClusterRoleBinding", "קלאסטר", "נותן ClusterRole בכל הקלאסטר"]),
       P("כל חוק ב-Role הוא שילוב של `apiGroups`, `resources` ו-`verbs` (`get`, `list`, `watch`, `create`, `update`, `patch`, `delete`). אפשר לצמצם לאובייקטים מסוימים עם `resourceNames`, ול-subresources כמו `pods/log` או `pods/exec`. subject הוא User, Group או ServiceAccount. הדפוס הנפוץ הוא ClusterRole אחד (למשל \"מפתח\") ו-RoleBinding שלו בכל namespace של צוות: הגדרה אחת, היקף מוגבל."),
       CODE("""
kind: Role
apiVersion: rbac.authorization.k8s.io/v1
metadata: {name: deployer, namespace: shop}
rules:
- apiGroups: [apps]
  resources: [deployments]
  verbs: [get, list, watch, update, patch]
- apiGroups: [""]
  resources: [pods, pods/log]
  verbs: [get, list, watch]
---
kind: RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
metadata: {name: ci-deployer, namespace: shop}
subjects: [{kind: ServiceAccount, name: ci, namespace: shop}]
roleRef: {kind: Role, name: deployer, apiGroup: rbac.authorization.k8s.io}
""", cap="CI יכול לעדכן Deployments ולקרוא pods ולוגים ב-shop, ותו לא"),
       KEY("RBAC הוא **רק allow**. אין חוקי deny. הרשאה ניתנת אם binding כלשהו נותן אותה, ולכן כדי להסיר הרשאה צריך למצוא את כל ה-bindings שנותנים אותה."),
       H("הרשאות שנראות תמימות"),
       UL("`list` ו-`watch` על `secrets` חושפים את התוכן של כל ה-Secrets, לא רק את השמות. אין דבר כזה \"לראות רק את הרשימה\".",
          "`create` על `pods` מאפשר להריץ pod עם כל ServiceAccount ב-namespace ולחבר כל Secret שלו.",
          "`pods/exec` נותן shell בקונטיינר, כולל גישה לסודות ול-token שלו.",
          "הפעלים `escalate`, `bind` ו-`impersonate` עוקפים את ההגנה של RBAC: בלעדיהם אי אפשר ליצור Role עם הרשאות שאין לך בעצמך.",
          "הקבוצה `system:masters` עוקפת את RBAC לגמרי, ומחיקת bindings לא מבטלת את זה. לא מכניסים אליה משתמשים."),
       P("ל-Kubernetes יש ClusterRoles מוכנים לשימוש: `view` (קריאה, בלי Secrets), `edit` (שינוי רוב המשאבים), `admin` (כולל RBAC בתוך ה-namespace) ו-`cluster-admin`. אחרי יצירת binding אי אפשר לשנות את ה-`roleRef` שלו: מוחקים ויוצרים מחדש."),
       H("ServiceAccount"),
       P("ServiceAccount הוא הזהות של pod מול ה-API server. לכל namespace יש `default`, וכל pod בלי הגדרה מקבל אותו. ה-kubelet מחבר ל-pod **projected token**: קשור ל-pod הספציפי, עם audience, ופג תוקף תוך כשעה (ה-kubelet מחדש אותו לפני כן). tokens ארוכי טווח ב-Secret כבר לא נוצרים אוטומטית מ-1.24. אם האפליקציה לא מדברת עם ה-API, מגדירים `automountServiceAccountToken: false`. ב-EKS אותו token משמש גם לקבלת הרשאות AWS (IRSA או Pod Identity)."),
       CODE("""
kubectl auth can-i list pods -n shop --as system:serviceaccount:shop:api
kubectl auth can-i --list -n shop --as system:serviceaccount:shop:ci
kubectl auth whoami
kubectl get rolebindings,clusterrolebindings -A -o wide | grep shop:ci
""", cap="איך בודקים מה מותר לזהות מסוימת, ומאיפה זה מגיע"),
       TRAP("לתת לאפליקציה את ה-ServiceAccount `default` עם הרשאות, כי \"ככה היה יותר מהר\". כל pod ב-namespace שלא הגדיר SA מקבל אותן הרשאות. לכל אפליקציה שצריכה גישה ל-API יש ServiceAccount משלה."),
      ],
      [C("Can you write a deny rule in Kubernetes RBAC?",
         ("No; RBAC rules only add permissions", "נכון. RBAC הוא additive: אין deny, ולכן הדרך להגביל היא לא לתת את ההרשאה מלכתחילה, ולהסיר bindings רחבים."),
         ("Yes, with `verbs: [deny]` in a Role", "אין verb בשם deny. ה-verbs הם get, list, create וכדומה, וכולם רק מוסיפים הרשאות."),
         ("Yes, but only inside ClusterRoles", "גם ClusterRole רק מוסיף הרשאות. אין ב-RBAC שום חוק שמבטל הרשאה שניתנה במקום אחר."),
         ("Yes, by binding a Role with no rules", "Role בלי rules פשוט לא נותן כלום. הוא לא מבטל הרשאות שהגיעו מ-binding אחר."),
         x="RBAC הוא additive. אין deny, ולכן הדרך להגביל היא לא לתת את ההרשאה מלכתחילה."),
       C("Which command checks whether a ServiceAccount may list pods?",
         ("`kubectl auth can-i list pods --as=system:serviceaccount:ns:sa`", "נכון. auth can-i עם --as מדמה את הזהות (impersonation) ומחזיר yes או no, בלי להתחבר בתור ה-ServiceAccount."),
         ("`kubectl describe serviceaccount <sa> --show-permissions`", "אין דגל --show-permissions. describe של ServiceAccount מראה secrets ו-tokens, לא את ההרשאות שלו."),
         ("`kubectl get rolebindings -n <ns> -o wide --for=<sa>`", "אין דגל --for. רשימת rolebindings מראה מי קשור למה, אבל לא עונה ישירות אם פעולה מותרת."),
         ("`kubectl auth whoami --as=system:serviceaccount:<ns>:<sa>`", "auth whoami מראה איזו זהות ה-API רואה, לא אילו פעולות מותרות לה."),
         x="`kubectl auth can-i` עם `--as` בודק את ההרשאות של זהות אחרת בלי להתחבר בתור הזהות הזאת."),
       C("Which binding grants a ClusterRole's permissions inside one namespace only?",
         ("A RoleBinding that references the ClusterRole", "נכון. RoleBinding יכול להפנות ל-ClusterRole, וההרשאות חלות רק ב-namespace שלו. כך משתמשים באותה תבנית בהרבה namespaces."),
         ("A ClusterRoleBinding with a namespace field", "ClusterRoleBinding חל על כל הקלאסטר ואין לו שדה namespace שמגביל אותו. לכן משתמשים ב-RoleBinding."),
         ("A NetworkPolicy that limits it to one namespace", "NetworkPolicy שולטת בתנועת רשת, לא בהרשאות API. היא לא מגבילה RBAC."),
         ("An annotation on the ServiceAccount naming the role", "annotations לא נותנות הרשאות. הרשאות מגיעות רק מ-RoleBinding או מ-ClusterRoleBinding."),
         x="RoleBinding יכול להפנות ל-ClusterRole. ההרשאות חלות רק ב-namespace של ה-RoleBinding, כך שאפשר להשתמש באותה תבנית בהרבה namespaces."),
      ]),

  MOD("pod-security", "אבטחת pods: securityContext ו-Pod Security Standards",
      "להקשיח קונטיינר עם securityContext, ולאכוף רמת אבטחה על namespace.",
      [H("למה ברירות המחדל מסוכנות"),
       P("קונטיינר הוא תהליך רגיל על ה-node, מבודד ב-namespaces וב-cgroups של ה-kernel. הבידוד הזה חלש יותר ממכונה וירטואלית: כל הקונטיינרים חולקים kernel אחד. ברירות המחדל מתירניות: קונטיינר יכול לרוץ כ-root (UID 0, אותו root של ה-node אם הוא בורח), לכתוב לכל מערכת הקבצים של ה-image, ולקבל סט של Linux capabilities. **securityContext** מצמצם את זה, ברמת ה-pod (לכל הקונטיינרים) או ברמת קונטיינר בודד."),
       TABLE(["הגדרה", "מה היא עושה, וממה היא מגינה"],
             ["`runAsNonRoot:` `true`", "הקונטיינר לא יעלה אם הוא מנסה לרוץ כ-root. מגן מפריצה שמגיעה עם הרשאות root"],
             ["`runAsUser` / `runAsGroup`", "UID ו-GID מפורשים לתהליך, גם כשה-image לא הגדיר USER"],
             ["`readOnlyRoot` `Filesystem: true`", "אי אפשר לכתוב למערכת הקבצים של ה-image. תוקף לא יכול להוריד כלים או לשנות בינאריים"],
             ["`allowPrivilege` `Escalation: false`", "תהליך לא יקבל יותר הרשאות מההורה שלו. חוסם הסלמה דרך בינארי עם setuid"],
             ["`capabilities:` `drop: [ALL]`", "מוריד את כל ה-capabilities; מוסיפים רק מה שצריך"],
             ["`seccompProfile:` `RuntimeDefault`", "מגביל syscalls מסוכנים לפי הפרופיל של ה-runtime, נגד ניצול חולשות kernel"]),
       P("seccomp לא מופעל לבד: ברירת המחדל של pod היא `Unconfined`, אלא אם ה-kubelet הוגדר עם `seccompDefault`. לכן כותבים `RuntimeDefault` במפורש. ה-capability היחידה שאפליקציה רגילה צריכה בדרך כלל היא `NET_BIND_SERVICE`, להאזנה על פורט מתחת ל-1024, וגם אותה אפשר לחסוך אם מאזינים על 8080."),
       CODE("""
spec:
  securityContext:                       # pod level: every container
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
    seccompProfile: {type: RuntimeDefault}
  containers:
  - name: api
    securityContext:                     # container level
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities: {drop: [ALL]}
    volumeMounts: [{name: tmp, mountPath: /tmp}]
  volumes: [{name: tmp, emptyDir: {}}]   # a writable /tmp for the app
""", cap="pod שעובר את רמת restricted, עם /tmp כתיב דרך emptyDir"),
       H("ההגדרות שפותחות את ה-node"),
       P("חלק מההגדרות לא מצמצמות אלא פותחות, והן מה שתוקף מחפש: `privileged: true` נותן לקונטיינר גישה כמעט מלאה ל-node (כל ה-devices וכל ה-capabilities). `hostPath` מחבר קבצים של ה-node, ו-hostPath ל-`/` או ל-socket של ה-runtime שווה ל-root על ה-node. `hostNetwork`, `hostPID` ו-`hostIPC` משתפים את ה-namespaces של ה-node, כך שהקונטיינר רואה את כל התהליכים או את כל התנועה. כלים מערכתיים (CNI, agents) צריכים חלק מאלה. אפליקציות לא."),
       H("Pod Security Standards ו-Pod Security Admission"),
       TABLE(["רמה", "מה היא אוסרת"],
             ["privileged", "כלום. לכלים מערכתיים ב-namespaces מבודדים"],
             ["baseline", "privileged, hostPath, hostNetwork והחלקים המסוכנים של capabilities"],
             ["restricted", "בנוסף: root, privilege escalation; חובה seccomp ו-drop ALL"]),
       P("**Pod Security Admission** הוא admission controller מובנה שאוכף את הרמות לפי labels על ה-namespace, בשלושה מצבים: `enforce` חוסם, `audit` רושם ב-audit log, ו-`warn` מחזיר אזהרה למשתמש. אפשר לנעול את גרסת הכללים עם `enforce-version`, כדי ששדרוג של Kubernetes לא יחמיר אותם פתאום. PodSecurityPolicy הישן הוסר בגרסה 1.25."),
       CODE("""
kubectl label ns shop \\
  pod-security.kubernetes.io/enforce=baseline \\
  pod-security.kubernetes.io/warn=restricted \\
  pod-security.kubernetes.io/audit=restricted
""", cap="אוכפים baseline, ומקבלים אזהרות על כל מה שלא יעבור restricted"),
       KEY("כדי להחמיר בלי לשבור: קודם `warn` ו-`audit` ל-restricted, מתקנים את מה שמופיע, ורק אז `enforce`. `kubectl label --dry-run=server` על ה-namespace מראה מראש אילו pods קיימים יפרו את הרמה."),
       TRAP("`enforce` חל רק על pods, לא על Deployments. Deployment שמפר את הרמה נוצר בהצלחה (עם אזהרה), אבל ה-ReplicaSet לא מצליח ליצור pods. ה-pods פשוט לא מופיעים, והשגיאה נמצאת ב-Events של ה-ReplicaSet."),
       TRAP("`readOnlyRootFilesystem` שובר אפליקציות שכותבות ל-`/tmp` או ל-cache. הפתרון הוא emptyDir על הנתיבים האלה, לא לוותר על ההגדרה."),
      ],
      [C("Which securityContext setting stops a process from gaining more privileges than its parent?",
         ("`allowPrivilegeEscalation: false`", "נכון. allowPrivilegeEscalation: false מפעיל no_new_privs, ומונע מ-setuid וממנגנונים דומים להעלות הרשאות בתוך הקונטיינר."),
         ("`runAsUser: 0` with `runAsGroup: 0`", "UID 0 הוא root, וזה ההפך מהקשחה: התהליך מתחיל כבר עם הרשאות מלאות בתוך הקונטיינר."),
         ("`hostNetwork: false` on the pod spec", "hostNetwork: false היא ברירת המחדל וקשורה לרשת. היא לא מונעת העלאת הרשאות דרך setuid."),
         ("`capabilities: add: [SETUID]`", "הוספת SETUID דווקא מאפשרת לשנות זהות. כדי למנוע העלאת הרשאות מורידים capabilities ומכבים escalation."),
         x="allowPrivilegeEscalation: false מונע מ-setuid וממנגנונים דומים להעלות הרשאות בתוך הקונטיינר."),
       C("What replaced PodSecurityPolicy in Kubernetes?",
         ("Pod Security Admission, with the Pod Security Standards", "נכון. PSP הוסר ב-1.25. Pod Security Admission אוכף את רמות privileged, baseline ו-restricted לפי labels על namespace."),
         ("NetworkPolicy, which now covers pod privileges too", "NetworkPolicy עוסקת רק בתנועת רשת. היא לא בודקת securityContext או הרשאות של pods."),
         ("ResourceQuota, with security fields added in 1.25", "ResourceQuota מגביל כמויות של משאבים ב-namespace. אין בו שדות אבטחה בכלל."),
         ("A built-in OPA engine that ships with the API server", "OPA Gatekeeper הוא פרויקט חיצוני שמתקינים בנפרד. מה שמובנה הוא Pod Security Admission."),
         x="PSP הוסר ב-1.25. Pod Security Admission אוכף את רמות privileged, baseline ו-restricted לפי labels על namespace."),
       C("How do you roll out the restricted level without breaking running workloads?",
         ("Begin with `warn` and `audit`; then switch to `enforce`", "נכון. warn ו-audit מראים מה יישבר בלי לחסום. אחרי שמתקנים את ה-workloads מפעילים enforce, namespace אחרי namespace."),
         ("Set `enforce` on every namespace at once, and fix later", "enforce דוחה pods חדשים מיד, כולל pods שנוצרים מחדש בגלל rollout או node שנפל. זה שובר שירותים."),
         ("Delete all running pods, then label the namespaces", "מחיקת pods לא עוזרת: הם ייווצרו מחדש מאותם manifests, ועם enforce הם פשוט יידחו."),
         ("Turn off RBAC during the rollout to avoid errors", "RBAC לא קשור ל-Pod Security. כיבוי שלו רק פותח את הקלאסטר, ולא מונע הפרות."),
         x="warn ו-audit מראים מה יישבר בלי לחסום. אחרי שמתקנים את ה-workloads מפעילים enforce."),
      ]),

  MOD("admission-supply", "Admission, policy ו-supply chain",
      "להסביר מה admission webhooks עושים, ואיך מוודאים שרק images בטוחים רצים בקלאסטר.",
      [H("מה admission עושה"),
       P("**Admission controllers** בודקים בקשות אחרי RBAC ולפני שהן נשמרות ב-etcd. RBAC עונה על \"מותר לך ליצור Deployment?\", ו-admission עונה על \"מותר ליצור **את ה-Deployment הזה**?\": עם image מ-registry לא מאושר, בלי requests, או כ-root. הם רצים בשני שלבים לפי סדר קבוע: קודם **mutating**, שמשנים את הבקשה (מזריקים sidecar, מוסיפים labels או ברירות מחדל), ואחר כך **validating**, שמאשרים או דוחים את התוצאה הסופית. הסדר הזה הוא הסיבה ש-validating רואה גם את מה שה-mutating הוסיפו."),
       SPLIT(("Mutating", ["הזרקת sidecar של service mesh", "ברירות מחדל ל-resources (LimitRanger)", "הוספת labels ו-tolerations"]),
             ("Validating", ["חסימת `:latest`", "חובת requests ו-limits", "רק registries מאושרים", "Pod Security Admission"])),
       P("חלק מה-admission controllers מובנים ב-API server ופועלים כל הזמן: `NamespaceLifecycle` (לא יוצרים משאבים ב-namespace שנמחק), `LimitRanger`, `ResourceQuota`, `ServiceAccount` ו-`PodSecurity`. מעבר לזה אפשר להוסיף מדיניות משלך בשתי דרכים: **webhooks** שה-API server קורא להם ב-HTTPS, או **policies ב-CEL** שרצות בתוך ה-API server עצמו."),
       TABLE(["כלי", "איך הוא עובד", "מתי לבחור בו"],
             ["Kyverno", "webhook; policies כ-YAML, כולל mutate, generate ואימות חתימות של images", "צוות שרוצה מדיניות קריאה בלי שפה חדשה"],
             ["OPA Gatekeeper", "webhook; policies ב-Rego", "ארגון שכבר משתמש ב-OPA גם מחוץ ל-Kubernetes"],
             ["ValidatingAdmissionPolicy", "חוקי CEL בתוך ה-API server, בלי webhook חיצוני (GA ב-1.30)", "חוקים פשוטים בלי רכיב נוסף שיכול ליפול"]),
       H("webhooks: הכוח והסיכון"),
       P("webhook מוגדר ב-`ValidatingWebhookConfiguration` או `MutatingWebhookConfiguration`: לאילו משאבים ופעולות הוא חל, לאיזה Service לשלוח, ו-`namespaceSelector` או `objectSelector` כדי לצמצם את ההיקף. `timeoutSeconds` קובע כמה לחכות (10 שניות כברירת מחדל), ו-`failurePolicy` קובע מה קורה כשה-webhook לא עונה: `Fail` דוחה את הבקשה, ו-`Ignore` מעביר אותה בלי בדיקה. זו בחירה בין אבטחה לזמינות: מדיניות אבטחה צריכה `Fail`, ואז ה-webhook הופך לרכיב קריטי."),
       TRAP("webhook עם `failurePolicy: Fail` שנפל חוסם יצירת משאבים בכל מקום שהוא חל עליו, לפעמים גם את ה-pods של ה-webhook עצמו, כך שהוא לא יכול לעלות. מחריגים את ה-namespace שלו ואת kube-system, מריצים כמה replicas עם PDB, ומנטרים את זמני התגובה שלו."),
       H("אבטחת images: שרשרת האספקה"),
       P("ה-image הוא הקוד שבאמת רץ, ולכן מאבטחים את כל הדרך שלו: מה נכנס אליו, מי בנה אותו, ומה מוודא שזה אותו image שנבדק. tag כמו `v1.4` הוא מצביע שאפשר להזיז; **digest** (`@sha256:...`) מזהה את התוכן עצמו, ולכן pin לפי digest מבטיח שמה שנסרק הוא מה שרץ."),
       UL("סריקה ב-CI (Trivy, Grype) ועצירה על חולשות קריטיות שיש להן תיקון, וסריקה חוזרת של images שכבר רצים, כי CVEs חדשים מתפרסמים כל יום.",
          "base image מינימלי (distroless, או scratch לבינארי סטטי): פחות חבילות זה פחות חולשות ובלי shell לתוקף.",
          "SBOM לכל image, כדי לדעת תוך דקות איפה רצה ספרייה פגיעה כשמתפרסם CVE.",
          "חתימה עם cosign (גם keyless דרך OIDC של ה-CI), ואימות ב-admission עם Kyverno `verifyImages`: image שלא נחתם על ידי ה-pipeline שלך לא רץ.",
          "רק registries מאושרים, ובעדיפות registry פרטי (ECR) שמשכפל images חיצוניים אחרי סריקה."),
       H("כשיש חשד לפריצה"),
       P("הדחף הראשון הוא למחוק את ה-pod, וזה בדיוק מה שלא עושים. מחיקה מעלימה את הראיות (תהליכים, קבצים, חיבורים), וה-controller יעלה pod זהה שאותה חולשה פתוחה בו."),
       KEY("אם pod נפרץ: מבודדים אותו עם NetworkPolicy ומורידים ממנו את ה-labels של ה-Service כדי שיצא מהתנועה, אוספים ראיות לפני מחיקה, בודקים מה ה-ServiceAccount שלו יכול היה לגשת אליו (גם ב-AWS דרך IRSA), ומבצעים רוטציה לכל הסודות האלה. רק אז מתקנים את החולשה ופורסים מחדש."),
      ],
      [C("A validating webhook is down with `failurePolicy: Fail`. What is the effect?",
         ("Requests it covers are rejected until it recovers", "נכון. עם Fail, ה-API server דוחה בקשות כשה-webhook לא עונה. זה בטוח מבחינת policy, אבל יכול לעצור את כל הקלאסטר."),
         ("Requests are let through without any policy check", "זו ההתנהגות של failurePolicy: Ignore. עם Fail, ה-API server דוחה כל בקשה שה-webhook היה אמור לבדוק."),
         ("Only read requests are blocked; writes still work", "admission webhooks לא מופעלים על קריאות בכלל. הם בודקים יצירה, עדכון ומחיקה, ושם החסימה."),
         ("Nothing happens, since webhooks are optional add-ons", "webhook שהוגדר הוא חלק מהשרשרת של ה-API. עם Fail, הנפילה שלו עוצרת את כל הבקשות שהוא מכסה."),
         x="עם Fail, ה-API server דוחה בקשות כשה-webhook לא עונה. זה בטוח מבחינת policy, אבל יכול לעצור את כל הקלאסטר."),
       C("Which tool can verify image signatures at admission time?",
         ("Kyverno, with a `verifyImages` rule", "נכון. Kyverno (וגם Sigstore policy-controller) בודק ב-admission שה-image חתום על ידי הזהות הנכונה לפני שה-pod נוצר."),
         ("kube-proxy, with a signature filter", "kube-proxy מתכנת חוקי רשת ל-Services. הוא לא רואה images בכלל ולא בודק חתימות."),
         ("The kubelet, through `imagePullPolicy`", "imagePullPolicy רק קובע מתי למשוך image. kubelet לא מאמת חתימות cosign כברירת מחדל."),
         ("The Cluster Autoscaler, on new nodes", "Cluster Autoscaler מוסיף ומוריד nodes. הוא לא מעורב ב-admission ולא בודק images."),
         x="Kyverno (וגם Sigstore policy-controller) בודק שה-image חתום על ידי הזהות הנכונה לפני שה-pod נוצר."),
       C("What is the first step when you suspect a pod is compromised?",
         ("Isolate it with a deny-all NetworkPolicy, and keep it", "נכון. מבודדים עם NetworkPolicy לפי ה-labels של ה-pod, אוספים ראיות (לוגים, קבצים, מידע מה-node), ורק אז מחליפים ומתקנים."),
         ("Delete it at once, so the attacker loses access", "מחיקה מאבדת ראיות, וה-ReplicaSet מעלה עותק עם אותה חולשה. התוקף יכול לחזור באותה דרך."),
         ("Scale the Deployment up so the bad pod gets less traffic", "הגדלה לא מבודדת את ה-pod הפגוע. הוא ממשיך לרוץ עם אותן הרשאות ואותה גישת רשת."),
         ("Restart the API server to cut every open session", "restart של ה-API server לא נוגע בתהליך שרץ בתוך ה-pod, ורק פוגע בכל הקלאסטר."),
         x="מחיקה מאבדת ראיות, וה-ReplicaSet מעלה עותק עם אותה חולשה. קודם מבודדים, אוספים מידע, ואז מתקנים."),
      ]),

  MOD("sec-in-practice", "בפועל: can-i, tokens, ValidatingAdmissionPolicy ו-audit",
      "לבדוק הרשאות בפקודה אחת, להבין tokens של ServiceAccount היום, ולאכוף מדיניות בלי webhook חיצוני.",
      [P("ראיון אבטחה ב-Kubernetes עובר מהר מתיאוריה לשאלה 'איך תבדוק?'. כאן הכלים שעונים על זה."),
       H("לבדוק הרשאות"),
       CODE("""$ kubectl auth can-i delete pods -n prod --as=system:serviceaccount:prod:api
no
$ kubectl auth can-i --list -n prod --as=jane@example.com
Resources        Verbs
pods             [get list watch]
deployments.apps [get list watch update patch]
$ kubectl auth whoami          # מי אני מבחינת ה-API server""", cap="impersonation עם --as דורש הרשאת impersonate"),
       TRAP("הרשאות שנראות תמימות ומעניקות הכול: `create pods` (אפשר להריץ pod עם כל ServiceAccount בנמספייס ולקבל את ההרשאות שלו), `get secrets`, `escalate` ו-`bind` על roles, ו-`impersonate`. ב-review של RBAC מחפשים אותן קודם."),
       H("ServiceAccount tokens היום"),
       TABLE(["פעם", "היום"],
             ["Secret עם token נוצר אוטומטית לכל ServiceAccount", "לא נוצר אוטומטית (מאז 1.24)"],
             ["token בלי תפוגה", "projected token עם תפוגה ו-audience, שה-kubelet מחדש"],
             ["תקף גם אחרי שה-pod נמחק", "קשור ל-pod (bound), ופג כשה-pod נמחק"]),
       P("pod שלא צריך לדבר עם ה-API server בכלל: `automountServiceAccountToken: false`. token כזה שדולף הוא פחות מסוכן, אבל token שלא קיים בכלל עדיף."),
       H("ValidatingAdmissionPolicy"),
       P("מגרסה 1.30 (GA) אפשר לכתוב מדיניות admission בתוך ה-API server עם ביטויי CEL, בלי webhook ובלי pods של Kyverno או Gatekeeper. מתאים לחוקים פשוטים: אין `:latest`, יש limits, אין `hostNetwork`."),
       CODE("""apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: {name: no-latest-tag}
spec:
  matchConstraints:
    resourceRules: [{apiGroups: [""], apiVersions: ["v1"], operations: ["CREATE","UPDATE"], resources: ["pods"]}]
  validations:
  - expression: "object.spec.containers.all(c, !c.image.endsWith(':latest'))"
    message: "image tag :latest is not allowed"
# צריך גם ValidatingAdmissionPolicyBinding שמחבר את המדיניות לנמספייסים""", cap="מדיניות CEL בלי webhook"),
       KEY("webhook של admission שנפל עם `failurePolicy: Fail` חוסם יצירת pods בכל הקלאסטר. לכן Kyverno ו-Gatekeeper רצים ב-HA, ומחריגים את kube-system. ValidatingAdmissionPolicy חוסך את התלות הזאת."),
       H("Audit logs"),
       P("audit log של ה-API server מתעד מי עשה מה ומתי: מי קרא secrets, מי מחק Deployment. ב-EKS מפעילים את סוג הלוג `audit` ל-CloudWatch. בחקירה זה המקור הראשון."),
       ASK(("איך תבדוק אם ServiceAccount מסוים יכול למחוק pods?",
            "`kubectl auth can-i delete pods -n <ns> --as=system:serviceaccount:<ns>:<name>` מחזיר yes או no, ו-`--list` מציג את כל ההרשאות. אם התשובה מפתיעה, מחפשים את ה-RoleBindings וה-ClusterRoleBindings שמפנים ל-ServiceAccount ולקבוצות שלו (system:serviceaccounts). כדאי להזכיר שגם create pods נותן בפועל את ההרשאות של כל ServiceAccount ב-namespace."),
           ("אילו הרשאות RBAC מסוכנות יותר ממה שהן נראות?",
            "create על pods: אפשר להריץ pod עם כל ServiceAccount ולהרכיב כל Secret. get, list או watch על secrets: list מחזיר את הערכים עצמם. pods/exec ו-pods/attach: גישה מלאה לקונטיינר. escalate, bind ו-impersonate: עקיפה של RBAC עצמו. ו-wildcards (*) שמכסים גם משאבים שיתווספו בעתיד. בביקורת RBAC מחפשים את כולן."),
           ("מה השתנה ב-ServiceAccount tokens בגרסאות האחרונות?",
            "בעבר כל ServiceAccount קיבל Secret עם token שלא פג. היום kubelet מרכיב projected token: קשור ל-pod, עם audience, פג תוקף ומתחדש אוטומטית. מ-1.24 לא נוצרים יותר Secrets כאלה לבד. בנוסף: automountServiceAccountToken: false לאפליקציות שלא צריכות את ה-API, ואותו token משמש גם לזהויות ענן כמו IRSA."),
           ("מה הסיכון ב-admission webhook, ואיך מקטינים אותו?",
            "webhook הוא שירות חיצוני בדרך של כל בקשה שהוא מכסה. עם failurePolicy: Fail נפילה שלו חוסמת יצירת משאבים, ולפעמים גם את התיקון של עצמו. מקטינים: כמה replicas עם PDB, namespaceSelector שמחריג את kube-system ואת ה-namespace שלו, timeout קצר, ניטור של latency ושגיאות, ו-ValidatingAdmissionPolicy ב-CEL לחוקים פשוטים, שרץ בתוך ה-API server.")),
      ],
      [C("Which object defines a set of permissions, and which one grants it to a subject?",
         ("A Role defines them; a RoleBinding grants them", "נכון. Role מגדיר verbs על resources ב-namespace, ו-RoleBinding מחבר אותו ל-users, groups או ServiceAccounts."),
         ("A RoleBinding defines them; a Role grants them", "זה הפוך. ה-Role מכיל את ה-rules עם ה-verbs, וה-RoleBinding מחבר אותו ל-subject."),
         ("A ServiceAccount defines them; a Role grants them", "ServiceAccount הוא זהות של pod, לא הגדרת הרשאות. הוא מקבל הרשאות רק דרך binding."),
         ("A NetworkPolicy defines them; a Service grants them", "NetworkPolicy ו-Service עוסקים ברשת, לא בהרשאות API. אלה מוגדרות ב-RBAC בלבד."),
         x="Role או ClusterRole מגדירים verbs על resources. RoleBinding או ClusterRoleBinding מחברים אותם ל-users, groups או ServiceAccounts."),
       C("Why is the `create pods` permission in a namespace dangerous?",
         ("Any pod you create can use any ServiceAccount there", "נכון. מי שיוצר pod בוחר את ה-ServiceAccount שלו ויכול להרכיב כל Secret ב-namespace, ולכן מקבל בפועל את ההרשאות שלהם."),
         ("Pods can delete their own namespace from inside", "pod לא מקבל הרשאות מעצם קיומו. הסיכון הוא בהרשאות של ה-ServiceAccount שהוא מריץ."),
         ("It lets you read the node's system logs directly", "קריאת לוגים של node דורשת גישה ל-node או הרשאות אחרות. create pods מסוכן בגלל בחירת ServiceAccount ו-Secrets."),
         ("Creating a pod turns NetworkPolicies off for it", "NetworkPolicies חלות על pods חדשים בדיוק כמו על ישנים. create pods לא עוקף אותן."),
         x="מי שיוצר pod בוחר את ה-ServiceAccount שלו, ומקבל בפועל את כל ההרשאות של כל ServiceAccount בנמספייס."),
       C("What is ValidatingAdmissionPolicy?",
         ("CEL rules that run inside the API server, with no webhook", "נכון. ValidatingAdmissionPolicy (GA ב-1.30) מריץ ביטויי CEL בתוך ה-API server, בלי שירות webhook חיצוני שיכול ליפול."),
         ("A NetworkPolicy that protects the API server itself", "ValidatingAdmissionPolicy לא קשור לרשת. זה מנגנון admission שבודק אובייקטים לפני שהם נשמרים."),
         ("A Kyverno feature that needs a sidecar in every pod", "זו יכולת מובנית של Kubernetes, לא של Kyverno, ולא צריך sidecar. הכללים רצים בתוך ה-API server."),
         ("An RBAC role that only cluster admins may bind to", "זה לא role ולא קשור ל-RBAC. הוא אוכף חוקים על תוכן האובייקטים, לא על מי מבצע את הבקשה."),
         x="ValidatingAdmissionPolicy (GA ב-1.30) מריץ ביטויי CEL בתוך ה-API server, בלי תלות ב-webhook חיצוני."),
      ], min=10),

 ],

 "recap": [
   H("שלושת השערים"),
   FLOW("Authentication: מי", "Authorization: מה מותר", "Admission: האם עומד במדיניות"),
   TABLE(["RBAC", "היקף"],
         ["Role + RoleBinding", "namespace"],
         ["ClusterRole + RoleBinding", "תבנית משותפת, חלה ב-namespace אחד"],
         ["ClusterRole + ClusterRoleBinding", "כל הקלאסטר"]),
   P("RBAC נותן הרשאות בלבד; אין deny. בודקים עם `kubectl auth can-i --as`. ServiceAccount הוא הזהות של pod, עם token שפג תוקף; מכבים automount כשאין צורך."),
   H("הקשחת pods"),
   TABLE(["הגדרה", "למה"],
         ["runAsNonRoot", "לא root בתוך הקונטיינר"],
         ["readOnlyRootFilesystem", "אין שינוי של ה-image בזמן ריצה"],
         ["allowPrivilegeEscalation: false", "אין העלאת הרשאות"],
         ["drop ALL capabilities", "מינימום הרשאות kernel"],
         ["seccomp RuntimeDefault", "פחות syscalls"]),
   P("Pod Security Standards: privileged, baseline, restricted. Pod Security Admission אוכף אותם לפי labels על namespace, עם warn ו-audit לפני enforce."),
   KEY("admission webhooks הם כוח וסיכון: הם אוכפים policy, אבל webhook שנפל עם failurePolicy: Fail עוצר את הקלאסטר. ValidatingAdmissionPolicy (CEL) רץ בתוך ה-API server ולא יכול ליפול בנפרד."),
   H("supply chain"),
   P("סריקה ב-CI, base images מינימליים, pin לפי digest, חתימה עם cosign ואימות בכניסה לקלאסטר. כך יודעים שמה שרץ הוא מה שנבנה ונבדק."),
   TRAP("טעויות שחוזרות: לתת cluster-admin ל-pipeline \"כדי שיעבוד\", לתת exec קבוע לכולם, ולמחוק pod שנפרץ לפני שאוספים ראיות."),
   H("איך לענות בראיון"),
   P("על \"איך היית מאבטח קלאסטר\" עונים לפי שכבות: גישה ל-API (SSO, RBAC מינימלי, audit logs), workloads (securityContext ו-Pod Security), רשת (NetworkPolicy default-deny), סודות (מקור חיצוני ו-KMS), ו-supply chain (סריקה וחתימות). דוגמה אחת קונקרטית לכל שכבה שווה יותר מרשימה ארוכה."),
 ],

 "final": [
   F("rbac", "A ServiceAccount gets `Forbidden` when it lists pods in its namespace. What is the right fix?",
     ("A Role with just the needed verbs, bound in that namespace", "נכון. בודקים עם auth can-i מה חסר, ונותנים Role מצומצם עם RoleBinding ב-namespace הנכון בלבד. זה least privilege."),
     ("Bind the ServiceAccount to cluster-admin so it is unblocked", "cluster-admin נותן שליטה מלאה בכל הקלאסטר. אם ה-ServiceAccount ייפרץ, התוקף מקבל הכול."),
     ("Turn off RBAC for that namespace until it is fixed", "אי אפשר לכבות RBAC ל-namespace אחד, ונטרול authorization פותח את הקלאסטר לכולם."),
     ("Give the ServiceAccount the node's IAM credentials", "credentials של ה-node הם ל-AWS, לא ל-Kubernetes API. הם לא פותרים Forbidden ורק מרחיבים את הסיכון."),
     x="מזהים את הזהות שנחסמה, בודקים עם `auth can-i`, ונותנים Role מצומצם עם RoleBinding ב-namespace הנכון. לא נותנים cluster-admin כדי לפתור מהר."),
   F("rbac", "What does the `pods/exec` permission effectively give a user?",
     ("Full access to the container and its secrets", "נכון. עם exec אפשר לקרוא קבצים, env vars ו-tokens בתוך הקונטיינר. לכן נותנים אותו זמנית ובאופן מבוקר, עם audit."),
     ("Read-only access to the container's logs", "קריאת לוגים היא pods/log, הרשאה נפרדת ומצומצמת. exec פותח shell בתוך הקונטיינר עצמו."),
     ("Permission to scale the pod's Deployment", "scale היא הרשאה על deployments/scale, נפרדת לגמרי. exec לא נוגע במספר ה-replicas."),
     ("Nothing beyond what `get pods` already gives", "get pods רק מראה את ה-spec ואת ה-status. exec מריץ פקודות בתוך הקונטיינר, וזה הרבה יותר."),
     x="עם exec אפשר לקרוא קבצים, env vars ו-tokens בתוך הקונטיינר. לכן נותנים אותו בצורה זמנית ומבוקרת, עם audit."),
   F("rbac", "Why set `automountServiceAccountToken: false` on most application pods?",
     ("Apps that never call the API shouldn't hold a token", "נכון. token מאפשר לדבר עם ה-API server בשם ה-ServiceAccount. אם האפליקציה לא צריכה את זה, עדיף שהוא לא יהיה בקונטיינר בכלל."),
     ("It makes the pod start faster by skipping one mount", "ההבדל בזמן העלייה זניח. הסיבה היא אבטחה: פחות credentials שאפשר לגנוב מתוך הקונטיינר."),
     ("It is required before any readiness probe can run", "probes מופעלים על ידי kubelet מבחוץ, ולא צריכים token של ServiceAccount בתוך ה-pod."),
     ("It hides the pod from the Services that select it", "token לא קשור ל-Services בכלל. ה-pod ממשיך לקבל תנועה לפי selector ו-readiness."),
     x="token מאפשר לדבר עם ה-API server בשם ה-ServiceAccount. אם האפליקציה לא צריכה את זה, עדיף שהוא לא יהיה בקונטיינר בכלל."),
   F("pod-security", "Your app needs to write temp files, but you want `readOnlyRootFilesystem: true`. What do you do?",
     ("Mount an emptyDir at the paths it writes to", "נכון. emptyDir על /tmp או על תיקיית cache נותן מקום לכתוב, בזמן שה-image עצמו נשאר לקריאה בלבד."),
     ("Run the container as root so it can write", "root לא עוזר מול filesystem שמוגדר לקריאה בלבד, ורק מבטל עוד שכבת הגנה."),
     ("Turn readOnlyRootFilesystem off for that pod", "זה פותר את הכתיבה, אבל מוותר על ההקשחה לגמרי. emptyDir נותן את שני הדברים יחד."),
     ("Add `privileged: true` to the container", "privileged פותח את כל היכולות של ה-host, וזה סיכון גדול. הוא בכלל לא נדרש לכתיבת קבצים זמניים."),
     x="emptyDir על `/tmp` או על תיקיית cache נותן מקום לכתוב, בזמן שה-image עצמו נשאר לקריאה בלבד."),
   F("pod-security", "Which Pod Security level forbids running as root and requires dropping all capabilities?",
     ("`restricted`, the strictest level", "נכון. restricted דורש runAsNonRoot, drop ALL, בלי privilege escalation, ו-seccomp RuntimeDefault. baseline רק מונע את ההגדרות המסוכנות ביותר."),
     ("`baseline`, the default for new pods", "baseline חוסם רק את ההגדרות המסוכנות ביותר, כמו privileged ו-hostPath. הוא עדיין מתיר root."),
     ("`privileged`, with drops added on top", "privileged היא רמה בלי שום הגבלה בכלל. היא לא דורשת כלום, ואין לה דרישות נוספות."),
     ("`hardened`, set per namespace label", "אין רמה בשם hardened. שלוש הרמות של Pod Security Standards הן privileged, baseline ו-restricted."),
     x="restricted דורש runAsNonRoot, drop ALL, אין privilege escalation, ו-seccomp RuntimeDefault. baseline רק מונע את ההגדרות המסוכנות ביותר."),
   F("pod-security", "Which Pod Security Admission mode only records violations without blocking or warning the user?",
     ("`audit`, which writes to the audit log", "נכון. audit רושם הפרות ב-audit log, warn מחזיר אזהרה ל-kubectl, ו-enforce דוחה את ה-pod. מתחילים מ-warn ו-audit."),
     ("`enforce`, which records and blocks it", "enforce דוחה את ה-pod בפועל. השאלה היא על מצב שלא חוסם ולא מחזיר אזהרה למשתמש."),
     ("`warn`, which logs it quietly on nodes", "warn מחזיר אזהרה גלויה ל-kubectl של המשתמש. הוא לא כותב שום דבר ל-nodes, וגם לא שקט."),
     ("`dryrun`, which simulates the policy", "אין מצב dryrun ב-Pod Security Admission. שלושת המצבים הם enforce, audit ו-warn."),
     x="audit רושם הפרות ב-audit log, warn מחזיר אזהרה ל-kubectl, ו-enforce דוחה את ה-pod. מתחילים מ-warn ו-audit לפני enforce."),
   F("admission-supply", "A webhook outage blocks all pod creation. How do you prevent this next time?",
     ("Run it HA, skip system namespaces, and use short timeouts", "נכון. replicas עם PDB, namespaceSelector שמחריג את kube-system ואת ה-namespace של ה-webhook, ו-timeout קצר. לחוקים פשוטים, ValidatingAdmissionPolicy מבטל את התלות."),
     ("Remove RBAC so the webhook can always be reached", "RBAC לא קשור לזמינות של ה-webhook. הסרה שלו רק פותחת את הקלאסטר לכל אחד."),
     ("Give every user cluster-admin so nothing is blocked", "admission חל גם על cluster-admin. הרשאות רחבות לא עוקפות webhook שנפל, ורק מסוכנות."),
     ("Pin the webhook image to `:latest` so it auto-heals", ":latest לא מתקן כלום, ורק מקשה לדעת מה רץ. זמינות מגיעה מ-replicas, PDB ו-timeouts."),
     x="replicas עם PDB, namespaceSelector שמחריג את kube-system ואת ה-namespace של ה-webhook, ו-timeout קצר. לחוקים פשוטים, ValidatingAdmissionPolicy מבטל את התלות בשירות חיצוני."),
   F("admission-supply", "Why pin images by digest instead of a tag?",
     ("A digest names fixed content; a tag can be moved", "נכון. tag כמו v1.2 יכול להצביע מחר על image אחר. digest מבטיח שמה שרץ הוא בדיוק מה שנבדק ונחתם."),
     ("Digests download faster because they skip a lookup", "מהירות ההורדה כמעט זהה. היתרון הוא שהתוכן לא יכול להשתנות מתחת לשם שמפנים אליו."),
     ("Tags are not allowed in production Kubernetes pods", "tags מותרים ונפוצים מאוד. הבעיה היא שאפשר להזיז אותם לתוכן אחר, לא שהם אסורים."),
     ("Digests let the image skip vulnerability scanning", "digest לא פוטר מסריקה. הוא רק מבטיח שמה שנסרק ונחתם הוא בדיוק מה שרץ."),
     x="tag כמו `v1.2` יכול להצביע מחר על image אחר. digest מבטיח שמה שרץ הוא בדיוק מה שנבדק ונחתם."),
   F("admission-supply", "What does a mutating admission webhook typically do?",
     ("Changes the request, such as injecting a sidecar", "נכון. mutating webhooks רצים לפני validating ומשנים את האובייקט: sidecars, labels, ברירות מחדל. validating מאשר או דוחה את התוצאה."),
     ("Authenticates each user before the request runs", "authentication קורה לפני admission, עם tokens, תעודות או OIDC. webhook לא מזהה משתמשים."),
     ("Schedules pods onto nodes that have free room", "שיבוץ הוא עבודה של ה-scheduler, אחרי שהאובייקט כבר נשמר. admission קורה לפני השמירה."),
     ("Pulls images from the registry ahead of time", "משיכת images היא עבודה של kubelet על ה-node. webhook רק רואה את האובייקט ב-API."),
     x="mutating webhooks רצים לפני validating ומשנים את האובייקט: sidecars, labels, ברירות מחדל. validating מאשר או דוחה את התוצאה."),
   F("sec-in-practice", "A developer has only `create` on pods in a namespace, and no access to Secrets. Why is this still risky?",
     ("They can run a pod as a powerful ServiceAccount", "נכון. pod יכול להשתמש בכל ServiceAccount ב-namespace ולהרכיב כל Secret שם כ-volume. לכן create pods שקול כמעט לכל ההרשאות ב-namespace."),
     ("They can change the cluster's Kubernetes version", "שדרוג קלאסטר לא נעשה דרך pods ולא דורש create pods. זה תפקיד של ה-control plane."),
     ("They can delete other namespaces from a pod", "pod לא מקבל הרשאות למחוק namespaces, אלא אם ה-ServiceAccount שלו מורשה. וזה בדיוק הסיכון."),
     ("They can turn off RBAC from inside a container", "RBAC מוגדר ב-API server, ואי אפשר לכבות אותו מתוך pod. הסיכון הוא ההרשאות של ה-ServiceAccount."),
     x="pod יכול להשתמש בכל ServiceAccount בנמספייס ולהרכיב כל Secret שם כ-volume. לכן create pods שקול כמעט לכל ההרשאות בנמספייס, ו-Pod Security ו-admission policies מגבילים את זה."),
 ],
}
