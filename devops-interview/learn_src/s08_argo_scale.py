# -*- coding: utf-8 -*-
from _h import *

SUBJECT = {
 "sec": 8, "nm": "ArgoCD: ApplicationSets & Multi-cluster", "tag": "Many apps, many clusters, one template",
 "deep": True,
 "modules": [

  MOD("appsets", "ApplicationSet ו-generators",
      "להשתמש ב-ApplicationSet כדי לייצר Applications רבים מתבנית אחת, לבחור generator מתאים לכל מצב, ולהבין מי הבעלים של מה.",
      [H("הבעיה: עשרות Applications כמעט זהים"),
       P("ברגע שיש 30 שירותים ו-3 סביבות, או אפליקציה אחת שצריכה לרוץ על 20 קלאסטרים, כתיבת Application ביד לכל צירוף הופכת למאות קבצים כמעט זהים. כל שינוי (project חדש, sync option נוסף) דורש עריכה של כולם, ובדרך מישהו שוכח אחד. **ApplicationSet** פותר את זה: זה CRD עם controller משלו (applicationset-controller), שמחזיק **תבנית** של Application אחד ו**רשימת פרמטרים**, ומייצר Application לכל שורת פרמטרים."),
       P("הפרמטרים מגיעים מ-**generators**. ה-controller מריץ את ה-generators שוב ושוב, ומסנכרן את רשימת ה-Applications עם מה שהם מחזירים: פרמטר חדש → Application חדש; פרמטר שהשתנה → Application מתעדכן; פרמטר שנעלם → Application נמחק (כברירת מחדל). ה-Applications שנוצרו הם Applications רגילים לכל דבר; Argo CD מסנכרן אותם בדיוק כמו Application שנכתב ביד."),
       TABLE(["Generator", "מאיפה מגיעים הפרמטרים", "שימוש נפוץ"],
             ["list", "רשימה מפורשת ב-YAML", "כמה סביבות קבועות עם ערכים שונים"],
             ["cluster", "ה-cluster secrets הרשומים ב-Argo CD, מסוננים לפי labels", "אותה אפליקציה לכל קלאסטר prod"],
             ["git (directories)", "תיקיות ב-repo שמתאימות ל-glob", "Application לכל תיקייה של שירות"],
             ["git (files)", "קבצי JSON או YAML ב-repo; כל שדה הופך לפרמטר", "פרמטרים לכל סביבה או לכל tenant בקובץ"],
             ["matrix / merge", "מכפלה או מיזוג של שני generators", "כל שירות על כל קלאסטר"],
             ["pull request / SCM provider", "PRs פתוחים, או repos בארגון", "סביבות preview; Application לכל repo"]),
       CODE("""
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: {name: guestbook, namespace: argocd}
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
  - clusters: {selector: {matchLabels: {env: prod}}}
  template:
    metadata: {name: 'guestbook-{{.name}}'}
    spec:
      project: prod
      source: {repoURL: https://github.com/acme/gitops, path: apps/guestbook, targetRevision: main}
      destination: {server: '{{.server}}', namespace: guestbook}
""", cap="Application אחד לכל קלאסטר עם label env=prod"),
       P("איך קוראים את זה: ה-cluster generator מחזיר לכל קלאסטר רשום שיש לו label `env=prod` את הפרמטרים `name` ו-`server` (ועוד, כמו labels של הקלאסטר). התבנית משתמשת בהם בשם ה-Application וב-destination. הוספת label `env=prod` ל-cluster secret חדש מספיקה כדי שהאפליקציה תיפרס אליו, בלי לגעת ב-ApplicationSet."),
       H("git files: פרמטרים מקבצים"),
       P("git files generator קורא קבצים שמתאימים ל-glob (למשל `envs/*/config.json`), וכל שדה בקובץ הופך לפרמטר. כך צוות יכול להוסיף סביבה או tenant חדש בקובץ JSON של כמה שורות (שם, קלאסטר, גרסה, גודל), בלי לגעת בתבנית. השילוב הנפוץ: קובץ לכל סביבה עם `cluster`, `namespace` ו-`imageTag`, ותבנית אחת שמשתמשת בהם. ב-Go templates אפשר גם תנאים ופונקציות, למשל `{{ if eq .env \"prod\" }}` לבחירת sync policy שונה לפרודקשן, ו-`templatePatch` לשינויים מורכבים שתבנית פשוטה לא מבטאת."),
       KEY("`goTemplate: true` עם `missingkey=error` הוא הצירוף המומלץ: Go templates נותנים פונקציות ותנאים, ו-`missingkey=error` גורם לשגיאה מיידית כשפרמטר חסר, במקום Application עם ערך ריק ב-destination או ב-path."),
       TRAP("עורכים את ה-ApplicationSet, לא את ה-Applications שהוא יצר. ה-controller הוא הבעלים, ועריכה ידנית של Application שנוצר תידרס ב-reconcile הבא. אם צריך שדה שמשתנה ידנית (למשל targetRevision זמני), מגדירים אותו ב-`ignoreApplicationDifferences`."),
      ],
      [C("Which generator creates one Application for every registered cluster with a given label?",
         ("The cluster generator", "נכון. ה-cluster generator קורא את ה-cluster secrets הרשומים ב-Argo CD, מסנן לפי labels, ומחזיר name ו-server לכל קלאסטר."),
         ("The list generator", "list מחזיר רק את הרשימה שכתבת בו ביד. הוא לא יודע אילו קלאסטרים רשומים ולא קורא labels."),
         ("The pull request generator", "pull request generator מחזיר PRs פתוחים מ-GitHub או GitLab, לסביבות preview. אין לו קשר לקלאסטרים רשומים."),
         ("The git files generator", "git files קורא קבצי JSON או YAML מה-repo. אפשר לכתוב בהם רשימת קלאסטרים ביד, אבל הוא לא מגלה אותם לבד."),
         x="cluster generator עובר על ה-cluster secrets שרשומים ב-Argo CD ומסנן לפי labels."),
       C("What does `goTemplateOptions: [\"missingkey=error\"]` prevent?",
         ("Applications generated with silently empty parameters", "נכון. בלי האופציה, פרמטר חסר הופך למחרוזת ריקה ונוצר Application שבור; איתה, ה-ApplicationSet מדווח שגיאה ולא מייצר כלום."),
         ("Two Applications rendering with the same generated name", "שמות כפולים גורמים לשגיאה בכל מקרה, עם missingkey או בלעדיו. האופציה משנה רק מה קורה כשהתבנית פונה לפרמטר שלא קיים."),
         ("Rendering slowdowns when a generator returns many items", "missingkey לא משפיע על ביצועים. הוא משנה רק את ההתנהגות כשפרמטר חסר, ולא את הזמן שלוקח לרנדר."),
         ("Syncs that start outside the project's allowed windows", "sync windows מוגדרים ב-AppProject וקובעים מתי מותר לסנכרן. אין להם קשר לרינדור תבניות של ApplicationSet."),
         x="בלי missingkey=error, פרמטר חסר הופך למחרוזת ריקה ונוצר Application שבור. עם האופציה, ה-ApplicationSet מדווח שגיאה."),
       C("You edit an Application that an ApplicationSet generated. What happens?",
         ("The ApplicationSet controller overwrites your change", "נכון. ה-ApplicationSet הוא הבעלים של ה-Applications שהוא מייצר, ומחזיר אותם לתבנית ב-reconcile הבא. שינויים עושים בתבנית או ב-generator."),
         ("The change is kept, since Applications are independent", "השינוי יישמר רק אם השדה מוגדר ב-ignoreApplicationDifferences. כברירת מחדל ה-controller דורס אותו."),
         ("The ApplicationSet is marked OutOfSync until you revert", "ל-ApplicationSet אין sync status מול הבנים שלו. ה-controller פשוט מחזיר את ה-Application לתבנית, בלי לחכות שמישהו יבטל."),
         ("Argo CD creates a second Application next to yours", "ה-controller מזהה את ה-Application לפי השם שהתבנית מייצרת ומעדכן אותו. הוא לא יוצר עותק נוסף."),
         x="ה-ApplicationSet הוא הבעלים של ה-Applications שהוא מייצר. שינויים עושים בתבנית או ב-generator."),
      ]),

  MOD("deletion", "מחיקות ו-preview environments",
      "להבין בדיוק מתי ApplicationSet מוחק Applications ומשאבים, איזו הגנה עובדת באיזה מקרה, ואיך להריץ סביבות preview.",
      [H("שתי שכבות של מחיקה"),
       P("כדי להבין מחיקות ב-ApplicationSet צריך להפריד בין שתי שכבות. **שכבה ראשונה**: ה-ApplicationSet מוחק את משאב ה-**Application** כשה-element שלו נעלם מה-generator (תיקייה ששינו את שמה, label שהוסר מקלאסטר, PR שנסגר), או כשמוחקים את ה-ApplicationSet עצמו. **שכבה שנייה**: כשמשאב Application נמחק, השאלה אם גם **המשאבים בקלאסטר** (Deployments, Services, PVCs) נמחקים תלויה ב-finalizer בשם `resources-finalizer.argocd.argoproj.io` על ה-Application. ApplicationSet מוסיף את ה-finalizer הזה לכל Application שהוא יוצר, אלא אם הוגדר `preserveResourcesOnDeletion: true`."),
       FLOW("element נעלם מה-generator", "ה-ApplicationSet מוחק את ה-Application", "resources finalizer", "Argo CD מוחק את כל משאבי ה-Application", cap="ברירת המחדל: מחיקה מגיעה עד ה-workloads"),
       TABLE(["הגנה", "מה היא מונעת", "מה היא לא מונעת"],
             ["`syncPolicy.preserveResourcesOnDeletion: true`", "מחיקת ה-workloads כשה-Application נמחק (ה-finalizer לא מתווסף)", "את מחיקת משאב ה-Application עצמו"],
             ["`applicationsSync: create-update`", "שה-ApplicationSet ימחק Application כשה-element נעלם", "מחיקה דרך ownerReferences כשמוחקים את ה-ApplicationSet עצמו"],
             ["`applicationsSync: create-only`", "גם עדכונים וגם מחיקות של Applications קיימים", "אותו דבר: לא מגן כשה-ApplicationSet נמחק"],
             ["finalizer על ה-ApplicationSet + מחיקה ב-background cascading", "מחיקת ה-Applications כשמוחקים את ה-ApplicationSet", "הגדרה עדינה; foreground cascading לא מבטיח שימור"]),
       P("הכלל המעשי: לסביבות פרודקשן, `preserveResourcesOnDeletion: true` הוא ההגנה החשובה ביותר, כי הוא שובר את הקשר בין \"משאב Application נמחק\" לבין \"השירות נמחק\". `create-update` מוסיף שכבה: גם אם מישהו מוחק שורה מה-generator, ה-Application לא נמחק בכלל. ושינויים ב-generators עוברים review כמו כל שינוי שיכול למחוק שירות."),
       TRAP("שינוי שם של תיקייה ב-git directory generator נראה תמים, אבל מבחינת ה-controller זו תיקייה שנעלמה ותיקייה חדשה: ה-Application הישן נמחק (ואיתו ה-workloads, אם יש finalizer), ו-Application חדש נוצר ומסונכרן מאפס. יש downtime, ו-PVCs שנמחקו לוקחים איתם את הנתונים."),
       P("איך מוחקים ApplicationSet בלי לאבד את השירותים: ה-Applications שהוא יצר מסומנים ב-ownerReferences שמצביעים עליו, ולכן Kubernetes מוחק אותם כשה-ApplicationSet נמחק, גם אם המדיניות היא create-update. לפי התיעוד, כדי לשמור אותם מוסיפים ל-ApplicationSet את ה-finalizer `resources-finalizer.argocd.argoproj.io` ומוחקים ב-background cascading; עם foreground אין הבטחה. ואם כבר רוצים לשמור רק את ה-workloads, preserveResourcesOnDeletion מספיק."),
       H("סביבות preview"),
       P("pull request generator שואל את ה-Git provider (GitHub, GitLab, Bitbucket, Gitea) אילו PRs פתוחים, ומחזיר לכל PR פרמטרים כמו `number`, `branch` ו-`head_sha`. התבנית יוצרת Application לכל PR, למשל ב-namespace בשם `pr-123` עם image שתויג לפי ה-SHA. כשה-PR נסגר או מתמזג, הוא נעלם מהרשימה, וה-Application והסביבה נמחקים אוטומטית. אפשר לסנן לפי labels של PR (למשל רק PRs עם label `preview`)."),
       UL("צריך token ל-Git provider, ועדיף webhook כדי שסביבה תעלה מיד כשנפתח PR ולא בסבב ה-polling הבא.",
          "לשים לב ל-rate limits של ה-API של ה-provider כשיש הרבה ApplicationSets.",
          "כל PR הוא סביבה שעולה כסף: ResourceQuota ל-namespaces של preview, ומגבלה על מספר PRs פתוחים עם label."),
       KEY("בסביבות preview, המחיקה האוטומטית היא בדיוק היתרון: אין סביבות ישנות שנשכחו. בסביבות פרודקשן, אותה התנהגות היא סיכון. בוחרים מדיניות sync ו-preserveResourcesOnDeletion לכל ApplicationSet לפי מה שהוא מנהל."),
      ],
      [C("A git directory generator's folder is renamed. What happens to the old Application?",
         ("It's deleted, and the resources finalizer removes its workloads too", "נכון. ה-generator כבר לא מחזיר את התיקייה הישנה, ולכן ה-Application נמחק, ועם ה-finalizer שה-ApplicationSet מוסיף גם המשאבים שלו."),
         ("It is kept under its old name until someone deletes it by hand", "ה-controller מסנכרן את רשימת ה-Applications עם ה-generator. Application בלי element תואם נמחק, אלא אם המדיניות היא create-update או create-only."),
         ("It's renamed in place, so its workloads keep running unchanged", "ל-controller אין דרך לדעת שזו אותה תיקייה בשם חדש. הוא רואה אחת שנעלמה ואחת חדשה, ולכן מוחק ויוצר."),
         ("Nothing changes until the ApplicationSet controller restarts", "ה-ApplicationSet controller מריץ את ה-generators כל הזמן, ולא צריך restart כדי לזהות שינוי ב-repo."),
         x="ה-generator כבר לא מחזיר את התיקייה הישנה, ולכן ה-Application שלה נמחק. Application חדש נוצר לתיקייה החדשה."),
       C("Which setting keeps the workloads running when an ApplicationSet deletes one of its Applications?",
         ("`preserveResourcesOnDeletion: true`", "נכון. ההגדרה מונעת מה-ApplicationSet להוסיף את ה-resources finalizer, ולכן מחיקת ה-Application משאירה את המשאבים בקלאסטר."),
         ("`prune: false` on the Applications", "prune קובע אם sync מוחק משאבים שהוסרו מ-Git. הוא לא חל כשמשאב ה-Application כולו נמחק עם finalizer."),
         ("`goTemplateOptions: [\"missingkey=error\"]`", "missingkey=error מגן מפני תבנית עם פרמטר חסר. אין לו השפעה על מה קורה כשמוחקים Application."),
         ("A deny sync window on the project", "sync window חוסם syncs לפי זמן. הוא לא מונע מחיקת Application, ולא את מחיקת המשאבים דרך finalizer."),
         x="preserveResourcesOnDeletion מונע את ה-finalizer, ולכן מחיקת Application שנוצר משאירה את המשאבים בקלאסטר."),
       C("What does the pull request generator do when a PR is closed?",
         ("Removes the PR's Application, cleaning up its preview environment", "נכון. ה-PR כבר לא ברשימת ה-PRs הפתוחים, ולכן ה-Application שלו נמחק, ואיתו הסביבה. זה מה שמונע הצטברות של סביבות ישנות."),
         ("Keeps the environment until someone deletes the namespace", "זה היה קורה רק עם create-only או create-update. ברירת המחדל מוחקת, וזה בדיוק מה שרוצים בסביבות preview."),
         ("Merges the PR's branch into the default branch for you", "ה-generator רק קורא את רשימת ה-PRs מה-provider. הוא לא מבצע שום פעולה על ה-PRs עצמם."),
         ("Deletes the Git branch so no new commits can reach it", "מחיקת branches היא הגדרה של ה-Git provider. ה-generator לא כותב ל-Git בכלל."),
         x="ה-PR כבר לא ברשימה, ולכן ה-Application שלו נמחק, וכך גם הסביבה. זה מה שמונע הצטברות של סביבות ישנות."),
      ]),

  MOD("multicluster", "ריבוי קלאסטרים וסקייל",
      "לבחור בין Argo CD מרכזי ל-instance לכל קלאסטר, לרשום קלאסטרים בלי סודות סטטיים, ולהבין איך ה-controller מתחלק בין קלאסטרים.",
      [H("איך Argo CD מכיר קלאסטרים"),
       P("Argo CD יכול לנהל את הקלאסטר שהוא רץ בו (`https://kubernetes.default.svc`, באמצעות ה-ServiceAccount של ה-controller), וגם קלאסטרים חיצוניים שנרשמו אליו. כל קלאסטר חיצוני הוא **Secret** ב-namespace של Argo CD עם label `argocd.argoproj.io/secret-type: cluster`, שמכיל את כתובת ה-API server ואת הדרך להתחבר אליו. ה-labels על ה-Secret הזה הם גם מה שה-cluster generator מסנן לפיו, ולכן הם חלק מהעיצוב: `env=prod`, `region=eu-west-1`, `tier=edge`."),
       TABLE(["רישום קלאסטר", "איך", "הערה"],
             ["`argocd cluster add <context>`", "יוצר ServiceAccount עם cluster-admin בקלאסטר היעד ושומר token", "נוח לנסיונות; לא דקלרטיבי, והרשאות רחבות"],
             ["Cluster secret דקלרטיבי", "server, ו-config עם bearerToken, exec או IAM", "נשמר ב-Git (עם Sealed Secrets או ESO) ונוצר כמו כל משאב"],
             ["EKS", "`awsAuthConfig` עם clusterName ו-roleARN", "בלי token סטטי; IAM נותן credentials זמניים"]),
       KEY("ב-EKS עדיף שה-application-controller וה-argocd-server יקבלו IAM role (IRSA או Pod Identity), וה-cluster secret ישתמש ב-`awsAuthConfig`. ה-role ממופה להרשאות Kubernetes בקלאסטר היעד דרך access entries. אין token שצריך לסובב או שיכול לדלוף."),
       CODE("""apiVersion: v1
kind: Secret
metadata:
  name: prod-eu
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: cluster
    env: prod
    region: eu-west-1
stringData:
  name: prod-eu
  server: https://ABC123.gr7.eu-west-1.eks.amazonaws.com
  config: |
    {"awsAuthConfig": {"clusterName": "prod-eu", "roleARN": "arn:aws:iam::111122223333:role/argocd-deployer"},
     "tlsClientConfig": {"caData": "LS0tLS1CRUdJTi..."}}""", cap="קלאסטר EKS רשום דקלרטיבית, עם labels ל-cluster generator"),
       P("שימו לב שה-AppProject מגביל גם כאן: `destinations` יכול לכלול קלאסטר לפי `name` או `server`, כך ש-Application של צוות dev לא יוכל לבחור את prod-eu כיעד גם אם הקלאסטר רשום באותו Argo CD. רישום קלאסטר הוא לא הרשאה לפרוס אליו."),
       H("hub מרכזי או instance לכל קלאסטר"),
       SPLIT(("Argo CD מרכזי (hub)", ["תמונה אחת של כל הסביבות, UI אחד", "RBAC, SSO ו-ApplicationSets במקום אחד", "מחזיק credentials לכל הקלאסטרים: blast radius גדול", "צריך גישת רשת לכל API server"]),
             ("Argo CD לכל קלאסטר", ["בידוד: פריצה או תקלה משפיעות על קלאסטר אחד", "סקייל טבעי: כל instance קטן", "יותר instances לשדרג ולנטר", "אין תמונה מרוכזת בלי כלי נוסף"])),
       P("יש גם דרך ביניים: hub לכל סביבה (אחד ל-prod ואחד ל-non-prod), כך שפריצה ל-Argo CD של dev לא נותנת גישה לפרודקשן. ההחלטה תלויה בכמה קלאסטרים יש, בדרישות הבידוד, ובשאלה אם צוות אחד מנהל הכול."),
       H("סקייל"),
       P("ה-application-controller מחזיק watch על כל סוגי המשאבים בכל קלאסטר שהוא מנהל, ושומר cache שלהם בזיכרון. כשיש הרבה קלאסטרים, replica אחת לא עומדת בזה. **sharding** מריץ כמה replicas של ה-controller (StatefulSet), וכל replica אחראית לחלק מהקלאסטרים; האלגוריתם (legacy לפי hash, round-robin, ועוד) קובע איך מחלקים. חשוב להבין שהחלוקה היא **לפי קלאסטר**: קלאסטר אחד ענק עדיין יושב על replica אחת."),
       UL("**repo-server**: עוד replicas, ו-`--parallelismlimit` כדי שרינדורים כבדים לא יפילו אותו (OOM).",
          "**`resource.exclusions`** ב-argocd-cm: לא לעקוב אחרי משאבים רועשים שלא מנוהלים ב-Git (Events, Leases, EndpointSlices), וכך להקטין זיכרון ותנועה.",
          "**webhooks** במקום polling, ו-`timeout.reconciliation` ארוך יותר כשיש webhook.",
          "**Redis HA** והתקנת HA של Argo CD בפרודקשן."),
       TRAP("להסיר ולרשום מחדש קלאסטר כדי לתקן credentials שפגו יכול לגרום לכל ה-Applications שמפנים אליו לאבד את היעד, וב-ApplicationSet עם cluster generator, להימחק. מעדכנים את ה-cluster secret הקיים במקום."),
      ],
      [C("How is an external cluster represented in Argo CD?",
         ("As a Secret labelled `argocd.argoproj.io/secret-type: cluster`", "נכון. ה-cluster secret מכיל את כתובת ה-API server ואת פרטי ההתחברות, וה-labels שלו הם מה שה-cluster generator מסנן לפיו."),
         ("As an Application whose destination points at the cluster's API", "Application מתאר מה לפרוס ולאן. הקלאסטר הוא היעד שה-Application מפנה אליו, ולכן הוא חייב להיות רשום בנפרד."),
         ("As a ConfigMap entry in `argocd-cm` with the server URL", "argocd-cm מחזיק הגדרות כלליות של Argo CD. פרטי התחברות לקלאסטר הם סודות, ולכן נשמרים ב-Secret, לא ב-ConfigMap."),
         ("As a kubeconfig file mounted into the argocd-server pod", "Argo CD לא קורא kubeconfig מקובץ. `argocd cluster add` משתמש ב-kubeconfig המקומי רק כדי ליצור את ה-cluster secret."),
         x="cluster secret מכיל את כתובת ה-API server ואת הדרך להתחבר אליו. הוא גם מה ש-cluster generator קורא."),
       C("What is the main downside of one central Argo CD managing many clusters?",
         ("It holds credentials to every cluster, so its blast radius is large", "נכון. hub מרכזי נוח לניהול, אבל פריצה אליו או תקלה בו משפיעות על כל הקלאסטרים. לכן מאבטחים אותו במיוחד, או מפצלים לפי סביבה."),
         ("It can't use SSO across clusters, so each needs its own login", "Argo CD מרכזי תומך ב-SSO בדיוק כמו instance יחיד. זה דווקא יתרון שלו: הגדרה אחת לכולם."),
         ("It can only deploy Helm charts to clusters other than the one it runs in", "סוג המקור לא תלוי במספר הקלאסטרים או במיקומם. hub מרנדר Helm, Kustomize ו-YAML לכל יעד."),
         ("It can target just one namespace in each remote cluster", "Argo CD מרכזי פורס לכל namespace שה-AppProject מתיר, בכל אחד מהקלאסטרים הרשומים."),
         x="hub מרכזי נוח לניהול, אבל פריצה אליו או תקלה בו משפיעות על כל הקלאסטרים. לכן מאבטחים אותו במיוחד."),
       C("Syncs lag across hundreds of applications on many clusters. Which scaling step targets the application-controller?",
         ("Sharding the controller across replicas by cluster", "נכון. sharding מחלק את הקלאסטרים בין כמה replicas של ה-controller, כך שכל אחד מחזיק פחות watches ועושה reconcile לפחות Applications."),
         ("Adding more replicas to the argocd-server Deployment", "argocd-server מגיש API ו-UI. הוספת replicas שלו עוזרת למשתמשים, אבל ה-reconcile קורה ב-controller."),
         ("Putting an HPA on the controller's CPU usage", "ה-controller הוא StatefulSet עם sharding לפי קלאסטר. replica נוספת מ-HPA לא מקבלת קלאסטרים בלי הגדרת shards, ולכן לא מחלקת עומס."),
         ("Splitting each sync into more sync waves", "sync waves קובעים סדר בתוך sync של Application אחד. הם לא מקטינים את העומס הכולל על ה-controller."),
         x="sharding מחלק את הקלאסטרים בין כמה replicas של ה-controller, כך שכל אחד עושה reconcile לפחות Applications."),
      ]),

  MOD("scale-in-practice", "בפועל: matrix generator, sharding ו-progressive syncs",
      "לכתוב ApplicationSet שמשלב שירותים וקלאסטרים, ולהסביר איך Argo CD גדל לאלפי Applications.",
      [P("ב-Mid-Senior שואלים איך מנהלים 30 שירותים על 6 קלאסטרים בלי 180 קבצים שכתובים ביד, ומה נשבר כש-Argo CD גדל. התשובה היא שילוב של matrix generator, הגנות מחיקה, וכוונון של הרכיבים."),
       H("Matrix generator"),
       P("matrix מקבל בדיוק שני generators ומחזיר את **המכפלה** שלהם: כל צירוף של פרמטר מהראשון ופרמטר מהשני. בדוגמה: git directories מחזיר שירות לכל תיקייה, cluster מחזיר כל קלאסטר prod, והתוצאה היא Application לכל זוג שירות-קלאסטר. הפרמטרים של שני ה-generators זמינים בתבנית יחד. **merge** שונה: הוא מאחד פרמטרים של כמה generators לפי מפתח משותף, למשל ערכי ברירת מחדל ועקיפה לקלאסטר מסוים."),
       CODE("""apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata: {name: services}
spec:
  goTemplate: true
  generators:
  - matrix:
      generators:
      - git:                       # כל תיקייה תחת services/ היא שירות
          repoURL: https://github.com/org/deploy.git
          revision: main
          directories: [{path: services/*}]
      - clusters:                  # כל קלאסטר עם label env=prod
          selector: {matchLabels: {env: prod}}
  template:
    metadata: {name: '{{.path.basename}}-{{.name}}'}
    spec:
      project: prod
      source: {repoURL: https://github.com/org/deploy.git, targetRevision: main, path: '{{.path.path}}'}
      destination: {server: '{{.server}}', namespace: '{{.path.basename}}'}
  syncPolicy:
    preserveResourcesOnDeletion: true   # מחיקת Application לא מוחקת את השירות""", cap="שירות לכל תיקייה × קלאסטר לכל prod"),
       KEY("ApplicationSet הוא הבעלים של ה-Applications שהוא יוצר. שורה שנעלמה מה-generator מוחקת Application, ועם finalizer גם את המשאבים. `preserveResourcesOnDeletion` שומר את המשאבים, ו-`applicationsSync: create-update` מונע את מחיקת ה-Application כשה-element נעלם."),
       H("מה נשבר כשגדלים"),
       TABLE(["סימפטום", "סיבה", "פתרון"],
             ["רענונים איטיים, CPU גבוה ב-controller", "controller אחד על הרבה קלאסטרים", "sharding: כמה replicas ל-application-controller, קלאסטרים מחולקים ביניהם"],
             ["manifests נבנים לאט, ComparisonError עם timeout", "repo-server מרנדר Helm ו-Kustomize שוב ושוב", "עוד replicas ל-repo-server, parallelism limit, monorepo עם manifest-generate-paths"],
             ["OOM ב-controller", "watch על כל סוגי המשאבים בכל קלאסטר", "`resource.exclusions` למשאבים שלא צריך (Events, Leases)"],
             ["Git rate limit", "polling של הרבה Applications", "webhooks, ו-timeout.reconciliation ארוך יותר"]),
       P("איך יודעים מה הצוואר: Argo CD חושף metrics ל-Prometheus. עומק ה-workqueue של ה-controller ומשך ה-reconcile מראים אם ה-controller לא עומד בקצב; משך הבקשות ל-repo-server מראה אם הרינדור הוא הבעיה. מכוונים לפי מדידה, לא לפי ניחוש."),
       H("Progressive syncs"),
       P("ApplicationSet יכול לעדכן את ה-Applications שלו בשלבים: קודם אלה עם label `env=dev`, ורק כשהם Healthy, אלה של staging, ואז prod. זה `strategy.type: RollingSync` עם steps לפי labels, ואפשר להגביל כמה Applications מתעדכנים במקביל בכל שלב. התכונה ב-**Beta** מגרסה 3.3, ולכן הרבה צוותים מממשים את אותו רעיון עם promotion ב-Git: PR לכל סביבה, ממוזג רק אחרי שהקודמת בריאה."),
       TRAP("cluster generator עם selector ריק (`clusters: {}`) בוחר את **כל** הקלאסטרים הרשומים, כולל ה-in-cluster המקומי. selector שכוח אחד, ושירות של dev מגיע לפרודקשן. תמיד מסננים לפי labels."),
       ASK(("How would you deploy 30 services to 6 clusters with Argo CD?",
            "ApplicationSet אחד עם matrix generator: git directories מחזיר שירות לכל תיקייה תחת services/, ו-cluster generator עם selector לפי labels (למשל env=prod) מחזיר את הקלאסטרים. התוצאה היא Application לכל צירוף, 180 בסך הכול, מתבנית אחת. values לכל קלאסטר נבחרים לפי שם הקלאסטר או labels שלו. מוסיפים goTemplate עם missingkey=error, preserveResourcesOnDeletion: true לפרודקשן, AppProject שמגביל repos ו-destinations, ו-RollingSync אם רוצים שהשינוי יגיע לפרודקשן בשלבים."),
           ("What happens to the Applications when you delete an ApplicationSet?",
            "ה-Applications שהוא יצר מסומנים ב-ownerReferences אליו, ולכן Kubernetes מוחק אותם יחד איתו, גם אם applicationsSync הוא create-only או create-update. אם ל-Applications יש resources finalizer, גם ה-workloads נמחקים. כדי לשמור עליהם: preserveResourcesOnDeletion: true מראש (המשאבים נשארים), או לפי התיעוד, מחיקה של ה-ApplicationSet ב-background cascading עם finalizer מתאים. לפני מחיקה כזאת בפרודקשן בודקים את זה בסביבת ניסוי."),
           ("Argo CD gets slow with 2,000 Applications. What do you tune?",
            "קודם מודדים: metrics של Argo CD (עומק ה-workqueue ומשך reconcile של ה-controller, זמני תשובה של ה-repo-server). אחר כך לפי הצוואר: sharding של ה-application-controller בין כמה replicas לפי קלאסטר; עוד replicas ל-repo-server ו-parallelism limit; resource.exclusions למשאבים רועשים שלא מנוהלים ב-Git (Events, Leases); webhooks במקום polling, עם timeout.reconciliation ארוך יותר; manifest-generate-paths ב-monorepo; Redis HA."),
           ("How do you promote a change from staging to prod with GitOps?",
            "promotion הוא commit, לא לחיצה. כל סביבה מצביעה על values או overlay משלה (או על tag), והקידום הוא PR שמעתיק את גרסת ה-image או את השינוי מ-staging ל-prod, אחרי שהבדיקות ב-staging עברו. ה-PR הוא שער האישור, וה-git log הוא ההיסטוריה. בפרודקשן לא משתמשים ב-targetRevision צף כמו HEAD. אפשר גם RollingSync של ApplicationSet כדי שהשינוי יעבור dev, staging ו-prod בשלבים עם המתנה ל-health.")),
      ],
      [C("What does a matrix generator do?",
         ("Combines two generators, producing one Application per pair", "נכון. matrix מחזיר את המכפלה של שני generators, למשל כל תיקיית שירות עם כל קלאסטר, ושני סטי הפרמטרים זמינים בתבנית."),
         ("Runs the Applications' syncs in parallel across clusters", "הקבלה של syncs לא קשורה ל-generators. matrix רק קובע אילו Applications קיימים."),
         ("Merges two generators' items that share a matching key", "זה merge generator: הוא מאחד פרמטרים של items עם מפתח משותף. matrix מחזיר את כל הצירופים, בלי מפתח."),
         ("Splits one Application into many smaller syncs", "matrix מייצר הרבה Applications נפרדים, כל אחד עם sync משלו. הוא לא מפצל Application קיים."),
         x="matrix מכפיל את התוצאות של שני generators, למשל כל תיקיית שירות עם כל קלאסטר."),
       C("Do `create-only` or `create-update` stop Applications being removed when the ApplicationSet itself is deleted?",
         ("No; ownerReferences delete them unless there's a finalizer and background deletion", "נכון. לפי התיעוד, המדיניות מגבילה את ה-ApplicationSet controller, אבל מחיקת ה-ApplicationSet מוחקת את הבנים דרך ownerReferences."),
         ("Yes; both policies protect the Applications in every case, and that one is included", "המדיניות חלה על מה שה-controller עושה בזמן reconcile. כשה-ApplicationSet עצמו נמחק, Kubernetes מוחק את הבנים לפי ownerReferences."),
         ("Yes, but only for Applications whose source is a Helm chart repository", "סוג המקור לא משנה את מנגנון המחיקה. ownerReferences חלים על כל Application שנוצר."),
         ("They delete every Application as soon as the policy is set on the AppSet", "הגדרת המדיניות לא מוחקת כלום. היא רק מגבילה עדכונים ומחיקות שה-controller היה עושה."),
         x="create-only ו-create-update לא מונעים מחיקת Applications כשמוחקים את ה-ApplicationSet. צריך finalizer על ה-ApplicationSet ומחיקה ב-background."),
       C("What does an ApplicationSet with `strategy.type: RollingSync` do?",
         ("Updates its Applications in label-based steps, waiting for health", "נכון. progressive sync מעדכן קודם את ה-Applications של השלב הראשון (למשל env=dev), ורק כשהם Healthy עובר לשלב הבא."),
         ("Rolls each Deployment's pods one by one, like `maxUnavailable: 1`", "זה rolling update של Deployment בתוך Application אחד. RollingSync פועל ברמה גבוהה יותר: על סדר ה-Applications."),
         ("Syncs every generated Application at once, then retries any that failed", "זה בערך ההתנהגות בלי strategy. RollingSync עושה את ההפך: שלבים, עם המתנה ל-health בין שלב לשלב."),
         ("Recreates every Application whenever the template changes", "שינוי בתבנית מעדכן Applications קיימים, הוא לא מוחק ויוצר אותם. RollingSync רק קובע באיזה סדר הם מסונכרנים."),
         x="RollingSync מגדיר steps לפי labels, ואפשר להגביל כמה Applications מתעדכנים במקביל בכל שלב. כך שינוי מגיע לפרודקשן רק אחרי ש-dev ו-staging בריאים."),
      ], min=12),

 ],

 "recap": [
   H("ApplicationSet"),
   P("תבנית אחת ו-generators שמחזירים פרמטרים. כל element הופך ל-Application, וה-controller מסנכרן את הרשימה כל הזמן. משנים את התבנית או את ה-generator, לא את ה-Applications שנוצרו. `goTemplate` עם `missingkey=error` תופס פרמטרים חסרים."),
   TABLE(["רוצים", "Generator"],
         ["אותה אפליקציה בכל קלאסטר prod", "cluster עם selector"],
         ["Application לכל תיקיית שירות", "git directories"],
         ["כל שירות בכל קלאסטר", "matrix"],
         ["סביבה לכל PR", "pull request"]),
   H("מחיקות"),
   P("element שנעלם מוחק את ה-Application, ועם resources finalizer גם את ה-workloads. preserveResourcesOnDeletion שומר את המשאבים; create-update מונע מחיקת Application כשה-element נעלם, אבל לא כשמוחקים את ה-ApplicationSet עצמו. שינויים ב-generators עוברים review."),
   TABLE(["מודל", "יתרון", "חיסרון"],
         ["hub מרכזי", "תמונה אחת", "blast radius גדול"],
         ["instance לכל קלאסטר", "בידוד", "יותר לתחזק"],
         ["hub לכל סביבה", "פשרה: prod מבודד", "שני מקומות לנהל"]),
   KEY("ב-EKS, Argo CD מתחבר לקלאסטרים עם IAM role דרך awsAuthConfig. אין tokens סטטיים לסובב."),
   H("סקייל"),
   P("sharding ל-application-controller לפי קלאסטר, יותר replicas ו-parallelism ל-repo-server, resource.exclusions למשאבים רועשים, webhooks במקום polling. מודדים עם עומק ה-workqueue ומשך ה-reconcile."),
   H("preview environments"),
   P("pull request generator נותן סביבה לכל PR ומנקה אותה כשה-PR נסגר. מגבילים משאבים ל-namespaces של preview, ושמים לב ל-rate limits של ה-Git provider."),
   TRAP("שתי טעויות שגורמות להשבתות: לשנות שם תיקייה ב-git generator בלי להבין שזה מוחק Application, ולרשום מחדש קלאסטר במקום לעדכן את ה-secret שלו."),
   H("איך לענות בראיון"),
   P("על \"איך היית פורס אפליקציה ל-20 קלאסטרים עם ערכים שונים לכל אחד\": ApplicationSet עם cluster generator, labels על ה-cluster secrets, ו-values לפי שם הקלאסטר. תוסיף איך מגינים מפני מחיקה ואיך בודקים שינוי לפני merge."),
 ],

 "final": [
   F("appsets", "You need the same app on 20 clusters with per-cluster values. What fits best?",
     ("An ApplicationSet with a cluster generator and per-cluster values", "נכון. תבנית אחת, Application לכל קלאסטר, ו-values שנבחרים לפי שם הקלאסטר או labels שלו. קלאסטר חדש מקבל את האפליקציה רק מ-label."),
     ("Twenty hand-written Applications, one per cluster, all kept in Git", "זה עובד, אבל כל שינוי משותף דורש 20 עריכות, וקל לשכוח אחת. בדיוק הבעיה ש-ApplicationSet פותר."),
     ("One Application whose destination lists all twenty clusters", "ל-Application יש destination אחד בלבד. אין דרך לכוון Application יחיד לכמה קלאסטרים."),
     ("One Helm release per cluster, installed from the CI pipeline", "זה push-based: ל-CI צריך credentials לכל 20 הקלאסטרים, ואין זיהוי drift. בדיוק מה ש-GitOps מחליף."),
     x="cluster generator מחזיר שם וכתובת לכל קלאסטר. התבנית משתמשת בהם כדי לבחור values ויעד."),
   F("appsets", "Teams want to add a tenant by committing a short JSON file with its settings. Which generator fits?",
     ("The git files generator", "נכון. git files קורא קבצים שמתאימים ל-glob, וכל שדה בקובץ הופך לפרמטר. tenant חדש הוא קובץ JSON של כמה שורות."),
     ("The git directories generator", "git directories מחזיר רק את נתיב התיקייה ושמה. הוא לא קורא שדות מתוך קבצים, ולכן הגדרות ה-tenant לא יגיעו לתבנית."),
     ("The list generator", "list מוגדר בתוך ה-ApplicationSet עצמו. כדי להוסיף tenant צריך לערוך את ה-ApplicationSet, לא להוסיף קובץ."),
     ("The SCM provider generator", "SCM provider סורק repos בארגון ומחזיר אחד לכל repo. הוא לא קורא קבצי הגדרות בתוך repo אחד."),
     x="git files generator קורא קבצי JSON או YAML לפי glob, וכל שדה הופך לפרמטר. צוות מוסיף סביבה או tenant בלי לגעת בתבנית."),
   F("appsets", "An ApplicationSet reports `ErrorOccurred` and updates nothing. Where do you look first?",
     ("Its status conditions and the ApplicationSet controller logs", "נכון. ה-conditions של ה-ApplicationSet והלוגים של ה-controller שלו מראים שגיאת template או generator, למשל פרמטר חסר או שמות כפולים."),
     ("The logs of the pods that the generated Applications deployed", "ה-pods של האפליקציה רצים מה-Applications הקיימים. השגיאה היא ביצירת ה-Applications, לפני שה-pods בכלל מעורבים."),
     ("The argocd-server access logs and the events it shows in the UI", "argocd-server מגיש API ו-UI. הוא לא מריץ את ה-generators, ולכן הלוגים שלו לא יכילו את שגיאת התבנית."),
     ("The repo-server's cache of rendered manifests stored in Redis", "ה-cache מחזיק manifests של Applications קיימים. שגיאה ביצירת Applications מתועדת ב-conditions של ה-ApplicationSet."),
     x="describe על ה-ApplicationSet מראה conditions כמו ErrorOccurred עם ההודעה. סיבות נפוצות: פרמטר חסר, שמות כפולים, או בעיית גישה ל-repo."),
   F("deletion", "What does `applicationsSync: create-update` prevent?",
     ("The ApplicationSet deleting Applications whose element is gone", "נכון. עם create-update ה-controller יוצר ומעדכן, אבל לא מוחק Application כשה-element שלו נעלם מה-generator."),
     ("Anyone editing the generated Applications by hand", "עדכונים עדיין מותרים, ולכן ה-controller ממשיך לדרוס עריכות ידניות של Applications שנוצרו."),
     ("Deletion of the Applications when the ApplicationSet itself is deleted", "זה בדיוק המקרה ש-create-update לא מכסה: ownerReferences מוחקים את הבנים כשמוחקים את ה-ApplicationSet."),
     ("Argo CD pruning resources that were removed from Git", "prune הוא הגדרה של ה-Application עצמו, ב-syncPolicy שלו. applicationsSync חל על Applications, לא על המשאבים שבתוכם."),
     x="create-update מונע מה-ApplicationSet למחוק Applications, ו-preserveResourcesOnDeletion שומר את ה-workloads גם כשה-Application נמחק. שתי שכבות הגנה שונות."),
   F("deletion", "Preview environments from a pull request generator keep piling up cost. What fits?",
     ("A ResourceQuota per preview namespace and a cap on labelled PRs", "נכון. ResourceQuota מגביל כמה כל סביבה צורכת, ומגבלה על PRs עם label קובעת כמה סביבות יש בכלל."),
     ("A longer reconciliation timeout so fewer previews get created", "timeout ארוך רק מעכב את יצירת הסביבות ואת מחיקתן. בסוף יהיו אותן סביבות, רק עם עיכוב."),
     ("Turning off the webhook so previews start only on polling", "בלי webhook הסביבות עולות כמה דקות מאוחר יותר, אבל עדיין לכל PR. זה פוגע בחוויה ולא חוסך."),
     ("Running every preview environment on its own dedicated cluster", "קלאסטר לכל preview הוא הדרך היקרה ביותר: control plane ו-nodes לכל PR. זה מגדיל את העלות."),
     x="כל PR הוא סביבה שעולה כסף. ResourceQuota ל-namespaces של preview ומגבלה על מספר PRs פתוחים עם label שומרים על העלות."),
   F("deletion", "What is a pull request generator typically used for?",
     ("Ephemeral preview environments, one per open PR", "נכון. כל PR פתוח מקבל Application משלו, עם namespace ו-image לפי SHA, והסביבה נמחקת כשה-PR נסגר."),
     ("Merging approved PRs automatically once CI passes", "ה-generator רק קורא את רשימת ה-PRs מה-provider. מיזוג הוא החלטה של אדם או של כלי CI."),
     ("Running the unit tests of each PR inside the cluster", "בדיקות יחידה רצות ב-CI על כל commit. ה-generator נותן סביבה חיה, לא מריץ בדיקות."),
     ("Creating a Git branch for every new Application", "ה-generator לא כותב ל-Git. הוא מגיב ל-PRs שכבר קיימים מ-branches שמפתחים יצרו."),
     x="כל PR מקבל Application משלו (namespace ו-image לפי SHA). זה נותן סביבה לבדיקה, ומתנקה לבד."),
   F("multicluster", "How should Argo CD authenticate to EKS clusters without static tokens?",
     ("Through an IAM role in the cluster secret's `awsAuthConfig`", "נכון. ה-pods של Argo CD מקבלים IAM role, ו-awsAuthConfig מורה להם לקבל token זמני דרך IAM. אין סוד סטטי לסובב."),
     ("With long-lived access keys of the user who created the cluster", "access keys קבועים של אדם הם בדיוק מה שרוצים למנוע: הם לא פגים, ודליפה שלהם נותנת גישה מלאה."),
     ("With a ServiceAccount token copied from the target cluster", "זה מה ש-argocd cluster add עושה, וזה עובד, אבל זה token סטטי שצריך לסובב ושיכול לדלוף. השאלה מבקשת בלי tokens כאלה."),
     ("By opening the API server publicly with anonymous auth on", "API server ציבורי עם גישה אנונימית פותח את הקלאסטר לכל העולם. זו לא שיטת אימות אלא ביטול שלה."),
     x="ה-controller מקבל IAM role, ו-awsAuthConfig מורה לו לקבל token דרך IAM. ה-role ממופה ל-RBAC בקלאסטר היעד דרך access entries."),
   F("multicluster", "After rotating a target cluster's credentials, its apps show Unknown. What is the right fix?",
     ("Update the existing cluster secret with the new credentials", "נכון. ה-cluster secret מחזיק את פרטי ההתחברות. מעדכנים אותו במקום, רצוי דקלרטיבית, ואז refresh ל-Applications."),
     ("Remove the cluster with argocd cluster rm and add it again", "הסרת הקלאסטר מנתקת את ה-Applications מהיעד, וב-ApplicationSet עם cluster generator עלולה למחוק אותם."),
     ("Delete the Applications and let the ApplicationSet recreate them", "מחיקת ה-Applications, עם finalizers, מוחקת את השירותים עצמם. הבעיה היא רק בהתחברות של Argo CD."),
     ("Restart every pod in the target cluster to pick up the change", "ה-pods בקלאסטר היעד עובדים כרגיל. הבעיה היא ש-Argo CD לא מצליח להתחבר ל-API server שלו."),
     x="ה-cluster secret מחזיק את פרטי ההתחברות. מעדכנים אותו (רצוי דקלרטיבית), ואחר כך refresh ל-Applications."),
   F("multicluster", "Which is a real advantage of running one Argo CD per cluster?",
     ("A smaller blast radius if one instance is compromised or broken", "נכון. כל instance מחזיק credentials רק לקלאסטר שלו, ולכן פריצה או תקלה נשארות בקלאסטר אחד."),
     ("A single UI and RBAC model that covers every environment at once", "UI אחד לכל הסביבות הוא דווקא היתרון של hub מרכזי. עם instance לכל קלאסטר יש UI ו-RBAC לכל אחד."),
     ("Fewer Argo CD installations to upgrade, monitor and back up over time", "זה ההפך: instance לכל קלאסטר אומר יותר התקנות לשדרג, לנטר ולגבות."),
     ("No need for AppProjects at all, since each cluster has a single team", "גם instance לקלאסטר אחד צריך AppProjects ו-RBAC, כי כמה צוותים חולקים בדרך כלל את אותו קלאסטר."),
     x="instance לכל קלאסטר מבודד תקלות ופריצות. המחיר הוא יותר instances לתחזק ואין תמונה אחת של כל הסביבות."),
   F("scale-in-practice", "An ApplicationSet uses `clusters: {}` with no selector. Which clusters does it target?",
     ("Every registered cluster, including the local in-cluster one", "נכון. selector ריק בוחר את כל הקלאסטרים הרשומים, כולל ה-in-cluster המקומי. selector שנשכח, ושירות של dev מגיע לפרודקשן."),
     ("Only clusters that carry the label `env=prod` by default", "אין label ברירת מחדל. בלי selector אין שום סינון, ולכן כל הקלאסטרים נבחרים, prod או לא."),
     ("No clusters at all until at least one label is given", "ההפך: selector ריק לא מסנן כלום ולכן בוחר הכול. זו בדיוק הסיבה שזו מלכודת מסוכנת."),
     ("Only external clusters; the local one is always excluded", "ה-in-cluster המקומי נכלל גם הוא כשאין selector. רק סינון לפי labels מוציא אותו."),
     x="cluster generator עם selector ריק בוחר את כל הקלאסטרים הרשומים. תמיד מסננים לפי labels, וכך גם קלאסטר חדש מקבל רק את מה שה-label שלו מתיר."),
 ],
}
