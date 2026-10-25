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
         ("Duplicate Git repositories", "כפילות repos לא קשורה לתבניות. היא נבדקת, אם בכלל, ברמת הרישום של ה-repos."),
         ("Slow rendering", "missingkey לא משפיע על ביצועים. הוא משנה רק מה קורה כשהתבנית פונה לפרמטר שלא קיים."),
         ("Sync windows", "sync windows מוגדרים ב-AppProject וקובעים מתי מותר לסנכרן. אין להם קשר לרינדור תבניות של ApplicationSet."),
         x="בלי missingkey=error, פרמטר חסר הופך למחרוזת ריקה ונוצר Application שבור. עם האופציה, ה-ApplicationSet מדווח שגיאה."),
       C("You edit an Application that an ApplicationSet generated. What happens?",
         ("The ApplicationSet controller overwrites your change", "נכון. ה-ApplicationSet הוא הבעלים של ה-Applications שהוא מייצר, ומחזיר אותם לתבנית ב-reconcile הבא. שינויים עושים בתבנית או ב-generator."),
         ("The change is kept permanently", "השינוי יישמר רק אם השדה מוגדר ב-ignoreApplicationDifferences. כברירת מחדל ה-controller דורס אותו."),
         ("The ApplicationSet is deleted", "עריכה של Application בן לא משפיעה על ה-ApplicationSet עצמו. הוא ממשיך לרוץ ולהחזיר את הבן לתבנית."),
         ("Argo CD creates a second Application", "ה-controller מזהה את ה-Application לפי השם שהתבנית מייצרת ומעדכן אותו. הוא לא יוצר עותק נוסף."),
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
         ("It is deleted, and with the resources finalizer its workloads are deleted too", "נכון. ה-generator כבר לא מחזיר את התיקייה הישנה, ולכן ה-Application נמחק, ועם ה-finalizer שה-ApplicationSet מוסיף גם המשאבים שלו."),
         ("It is kept with the old name", "ה-controller מסנכרן את רשימת ה-Applications עם ה-generator. Application בלי element תואם נמחק, אלא אם המדיניות היא create-update או create-only."),
         ("It is moved automatically to the new folder", "ל-controller אין דרך לדעת שזו אותה תיקייה בשם חדש. הוא רואה אחת שנעלמה ואחת חדשה."),
         ("Nothing changes until Argo CD restarts", "ה-ApplicationSet controller מריץ את ה-generators כל הזמן, ולא צריך restart כדי לזהות שינוי ב-repo."),
         x="ה-generator כבר לא מחזיר את התיקייה הישנה, ולכן ה-Application שלה נמחק. Application חדש נוצר לתיקייה החדשה."),
       C("Which setting keeps the workloads running when an ApplicationSet deletes one of its Applications?",
         ("`preserveResourcesOnDeletion: true`", "נכון. ההגדרה מונעת מה-ApplicationSet להוסיף את ה-resources finalizer, ולכן מחיקת ה-Application משאירה את המשאבים בקלאסטר."),
         ("`prune: false` on the Applications", "prune קובע אם sync מוחק משאבים שהוסרו מ-Git. הוא לא חל כשמשאב ה-Application כולו נמחק עם finalizer."),
         ("`missingkey=error`", "missingkey=error מגן מפני תבנית עם פרמטר חסר. אין לו השפעה על מה קורה כשמוחקים Application."),
         ("A deny sync window", "sync window חוסם syncs לפי זמן. הוא לא מונע מחיקת Application, ולא את מחיקת המשאבים דרך finalizer."),
         x="preserveResourcesOnDeletion מונע את ה-finalizer, ולכן מחיקת Application שנוצר משאירה את המשאבים בקלאסטר."),
       C("What does the pull request generator do when a PR is closed?",
         ("Removes the PR's Application, cleaning up its preview environment", "נכון. ה-PR כבר לא ברשימת ה-PRs הפתוחים, ולכן ה-Application שלו נמחק, ואיתו הסביבה. זה מה שמונע הצטברות של סביבות ישנות."),
         ("Keeps the environment forever", "זה היה קורה רק עם create-only או create-update. ברירת המחדל מוחקת, וזה בדיוק מה שרוצים בסביבות preview."),
         ("Merges the PR", "ה-generator רק קורא את רשימת ה-PRs מה-provider. הוא לא מבצע שום פעולה על ה-PRs עצמם."),
         ("Deletes the Git branch", "מחיקת branches היא הגדרה של ה-Git provider. ה-generator לא כותב ל-Git בכלל."),
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
         ("As an Application", "Application מתאר מה לפרוס ולאן. הקלאסטר הוא היעד שה-Application מפנה אליו, לא Application בעצמו."),
         ("As a ConfigMap in every namespace", "פרטי התחברות לקלאסטר הם סודות, ולכן נשמרים ב-Secret אחד ב-namespace של Argo CD, לא ב-ConfigMaps."),
         ("As an Ingress", "Ingress חושף שירות HTTP לתעבורה נכנסת. אין לו קשר לאופן שבו Argo CD מתחבר ל-API servers."),
         x="cluster secret מכיל את כתובת ה-API server ואת הדרך להתחבר אליו. הוא גם מה ש-cluster generator קורא."),
       C("What is the main downside of one central Argo CD managing many clusters?",
         ("It holds credentials to every cluster, so its blast radius is large", "נכון. hub מרכזי נוח לניהול, אבל פריצה אליו או תקלה בו משפיעות על כל הקלאסטרים. לכן מאבטחים אותו במיוחד, או מפצלים לפי סביבה."),
         ("It cannot use SSO", "Argo CD מרכזי תומך ב-SSO בדיוק כמו instance יחיד. זה דווקא יתרון שלו: הגדרה אחת לכולם."),
         ("It cannot deploy Helm charts", "סוג המקור לא תלוי במספר הקלאסטרים. hub מרנדר Helm, Kustomize ו-YAML לכל יעד."),
         ("It only supports one namespace", "Argo CD מרכזי פורס לכל namespace שה-AppProject מתיר, בכל אחד מהקלאסטרים הרשומים."),
         x="hub מרכזי נוח לניהול, אבל פריצה אליו או תקלה בו משפיעות על כל הקלאסטרים. לכן מאבטחים אותו במיוחד."),
       C("Syncs lag across hundreds of applications on many clusters. Which scaling step targets the application-controller?",
         ("Sharding the controller across replicas by cluster", "נכון. sharding מחלק את הקלאסטרים בין כמה replicas של ה-controller, כך שכל אחד מחזיק פחות watches ועושה reconcile לפחות Applications."),
         ("Adding more Ingress controllers", "Ingress controllers מטפלים בתעבורה נכנסת לאפליקציות. הם לא משפיעים על עבודת ה-reconcile של Argo CD."),
         ("Increasing the HPA target", "HPA מגדיל replicas של Deployment לפי עומס. ה-controller הוא StatefulSet עם sharding, ולא מתחלק נכון דרך HPA."),
         ("Adding sync waves", "sync waves קובעים סדר בתוך sync של Application אחד. הם לא מקטינים את העומס הכולל על ה-controller."),
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
       ASK("How would you deploy 30 services to 6 clusters with Argo CD?",
           "What happens to the Applications when you delete an ApplicationSet?",
           "Argo CD gets slow with 2,000 Applications. What do you tune?",
           "How do you promote a change from staging to prod with GitOps?"),
      ],
      [C("What does a matrix generator do?",
         ("Combines two generators, producing one Application per pair", "נכון. matrix מחזיר את המכפלה של שני generators, למשל כל תיקיית שירות עם כל קלאסטר, ושני סטי הפרמטרים זמינים בתבנית."),
         ("Runs Applications in parallel", "הקבלה של syncs לא קשורה ל-generators. matrix רק קובע אילו Applications קיימים."),
         ("Creates a matrix of RBAC roles", "RBAC מוגדר ב-argocd-rbac-cm וב-AppProjects. ל-matrix generator אין קשר להרשאות."),
         ("Splits one Application into many syncs", "matrix מייצר הרבה Applications נפרדים, כל אחד עם sync משלו. הוא לא מפצל Application קיים."),
         x="matrix מכפיל את התוצאות של שני generators, למשל כל תיקיית שירות עם כל קלאסטר."),
       C("Do `create-only` or `create-update` stop Applications being removed when the ApplicationSet itself is deleted?",
         ("No; ownerReferences still delete them unless you add a finalizer and use background deletion", "נכון. לפי התיעוד, המדיניות מגבילה את ה-ApplicationSet controller, אבל מחיקת ה-ApplicationSet מוחקת את הבנים דרך ownerReferences."),
         ("Yes; the policies protect Applications in every case", "המדיניות חלה על מה שה-controller עושה בזמן reconcile. כשה-ApplicationSet עצמו נמחק, Kubernetes מוחק את הבנים לפי ownerReferences."),
         ("Yes, but only for Helm-based Applications", "סוג המקור לא משנה את מנגנון המחיקה. ownerReferences חלים על כל Application שנוצר."),
         ("They delete the Applications immediately when set", "הגדרת המדיניות לא מוחקת כלום. היא רק מגבילה עדכונים ומחיקות שה-controller היה עושה."),
         x="create-only ו-create-update לא מונעים מחיקת Applications כשמוחקים את ה-ApplicationSet. צריך finalizer על ה-ApplicationSet ומחיקה ב-background."),
       C("The application-controller is overloaded across many clusters. What is the scaling approach?",
         ("Shard it: run several controller replicas with clusters split between them", "נכון. כל replica מחזיקה watches ו-cache רק לקלאסטרים שלה, וכך העומס והזיכרון מתחלקים."),
         ("Increase the reconciliation timeout to zero", "timeout של 0 מבטל polling לגמרי, ומשאיר את Argo CD תלוי ב-webhooks בלבד. זה לא מחלק את העומס, ועלול להשאיר אפליקציות מאחור."),
         ("Use one Application per cluster only", "צמצום מספר ה-Applications לא פותר את ה-watches על כל סוגי המשאבים בכל קלאסטר, שהם עיקר העומס."),
         ("Disable health checks", "health checks הם חלק קטן מהעבודה, וביטולם מאבד מידע חשוב בלי להקטין את ה-watches."),
         x="sharding מחלק קלאסטרים בין replicas של ה-controller, וכך כל אחד מנטר פחות משאבים."),
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
     ("20 hand-written Applications", "זה עובד, אבל כל שינוי משותף דורש 20 עריכות, וקל לשכוח אחת. בדיוק הבעיה ש-ApplicationSet פותר."),
     ("One Application pointing at all clusters", "ל-Application יש destination אחד בלבד. אין דרך לכוון Application יחיד לכמה קלאסטרים."),
     ("A DaemonSet", "DaemonSet פורס pod על כל node בתוך קלאסטר אחד. הוא לא מגיע לקלאסטרים אחרים."),
     x="cluster generator מחזיר שם וכתובת לכל קלאסטר. התבנית משתמשת בהם כדי לבחור values ויעד."),
   F("appsets", "Which generator combines two other generators, such as every service on every cluster?",
     ("The matrix generator", "נכון. matrix מחזיר את המכפלה של שני generators, וכל צירוף הופך ל-Application."),
     ("The list generator", "list מחזיר רשימה מפורשת אחת שכתבת ביד. הוא לא משלב generators אחרים."),
     ("The SCM provider generator", "SCM provider סורק repos בארגון ומחזיר אחד לכל repo. הוא לא מכפיל שני מקורות."),
     ("The cluster generator", "cluster מחזיר רק את הקלאסטרים הרשומים. כדי לשלב אותם עם שירותים צריך matrix מעליו."),
     x="matrix מחזיר כל צירוף של הפרמטרים משני generators, למשל git directories כפול clusters."),
   F("appsets", "An ApplicationSet reports `ErrorOccurred` and updates nothing. Where do you look first?",
     ("Its status conditions and the ApplicationSet controller logs", "נכון. ה-conditions של ה-ApplicationSet והלוגים של ה-controller שלו מראים שגיאת template או generator, למשל פרמטר חסר או שמות כפולים."),
     ("The application pods' logs", "ה-pods של האפליקציה רצים מה-Applications הקיימים. השגיאה היא ביצירת ה-Applications, לפני שה-pods בכלל מעורבים."),
     ("The Ingress controller", "Ingress controller מטפל בתעבורה ל-pods. אין לו שום תפקיד ברינדור תבניות של ApplicationSet."),
     ("CoreDNS", "DNS לא משתתף ברינדור תבניות. אם repo לא נגיש, ההודעה תופיע ב-conditions, לא ב-CoreDNS."),
     x="describe על ה-ApplicationSet מראה conditions כמו ErrorOccurred עם ההודעה. סיבות נפוצות: פרמטר חסר, שמות כפולים, או בעיית גישה ל-repo."),
   F("deletion", "How do you keep workloads running if an ApplicationSet deletes their Application?",
     ("Set `preserveResourcesOnDeletion: true` in the ApplicationSet sync policy", "נכון. ההגדרה מונעת את הוספת ה-resources finalizer ל-Applications, ולכן מחיקת Application משאירה את המשאבים בקלאסטר."),
     ("Disable the repo-server", "ה-repo-server מרנדר manifests. כיבויו לא משנה את התנהגות המחיקה, ורק שובר את ה-syncs."),
     ("Add a PostSync hook", "PostSync hook רץ אחרי sync מוצלח. הוא לא מעורב במחיקת Application ולא יכול לעצור אותה."),
     ("Use a floating targetRevision", "targetRevision קובע מאיזה commit לקרוא. אין לו שום השפעה על מה שקורה כשה-Application נמחק."),
     x="עם preserveResourcesOnDeletion, מחיקת Application שנוצר ע\"י ApplicationSet משאירה את המשאבים בקלאסטר במקום למחוק אותם."),
   F("deletion", "Why is renaming a folder used by a git directory generator risky?",
     ("The old Application and its workloads are deleted and a new one is created", "נכון. ה-generator רואה תיקייה שנעלמה ותיקייה חדשה, ולכן זו מחיקה ויצירה ולא שינוי שם, עם downtime ואולי אובדן נתונים."),
     ("Git doesn't allow renaming folders", "Git מאפשר שינוי שם של תיקיות בלי בעיה. הסיכון נמצא באופן שבו ה-ApplicationSet מפרש את השינוי."),
     ("It disables SSO", "SSO מוגדר ב-argocd-cm ובספק הזהות. שמות תיקיות ב-repo לא משפיעים עליו."),
     ("It changes the cluster's API version", "גרסת ה-API של הקלאסטר נקבעת בשדרוג Kubernetes. שינוי ב-repo לא נוגע בה."),
     x="ה-generator רואה תיקייה שנעלמה ותיקייה חדשה. בלי הגנות, זה downtime עד שה-Application החדש מסתנכרן, ואובדן נתונים אם יש PVCs."),
   F("deletion", "What is a pull request generator typically used for?",
     ("Ephemeral preview environments, one per open PR", "נכון. כל PR פתוח מקבל Application משלו, עם namespace ו-image לפי SHA, והסביבה נמחקת כשה-PR נסגר."),
     ("Merging PRs automatically", "ה-generator רק קורא את רשימת ה-PRs מה-provider. מיזוג הוא החלטה של אדם או של כלי CI."),
     ("Running unit tests", "בדיקות יחידה רצות ב-CI על כל commit. ה-generator נותן סביבה חיה, לא מריץ בדיקות."),
     ("Creating Git branches", "ה-generator לא כותב ל-Git. הוא מגיב ל-PRs שכבר קיימים מ-branches שמפתחים יצרו."),
     x="כל PR מקבל Application משלו (namespace ו-image לפי SHA). זה נותן סביבה לבדיקה, ומתנקה לבד."),
   F("multicluster", "How should Argo CD authenticate to EKS clusters without static tokens?",
     ("Through an IAM role in the cluster secret's `awsAuthConfig`", "נכון. ה-pods של Argo CD מקבלים IAM role, ו-awsAuthConfig מורה להם לקבל token זמני דרך IAM. אין סוד סטטי לסובב."),
     ("With the cluster creator's access keys", "access keys קבועים של אדם הם בדיוק מה שרוצים למנוע: הם לא פגים, ודליפה שלהם נותנת גישה מלאה."),
     ("By making the API server public without auth", "API server ציבורי בלי אימות פותח את הקלאסטר לכל העולם. זו לא שיטת אימות אלא ביטול שלה."),
     ("By disabling RBAC in the target cluster", "ביטול RBAC נותן לכל זהות הרשאות מלאות. זה פותר את ההתחברות על ידי ויתור על בקרת גישה."),
     x="ה-controller מקבל IAM role, ו-awsAuthConfig מורה לו לקבל token דרך IAM. ה-role ממופה ל-RBAC בקלאסטר היעד דרך access entries."),
   F("multicluster", "After rotating a target cluster's credentials, its apps show Unknown. What is the right fix?",
     ("Update the existing cluster secret with the new credentials", "נכון. ה-cluster secret מחזיק את פרטי ההתחברות. מעדכנים אותו במקום, רצוי דקלרטיבית, ואז refresh ל-Applications."),
     ("Remove the cluster and add it again", "הסרת הקלאסטר מנתקת את ה-Applications מהיעד, וב-ApplicationSet עם cluster generator עלולה למחוק אותם."),
     ("Delete all the Applications", "מחיקת ה-Applications, עם finalizers, מוחקת את השירותים עצמם. הבעיה היא רק בהתחברות של Argo CD."),
     ("Restart every pod in the target cluster", "ה-pods בקלאסטר היעד עובדים כרגיל. הבעיה היא ש-Argo CD לא מצליח להתחבר ל-API server שלו."),
     x="ה-cluster secret מחזיק את פרטי ההתחברות. מעדכנים אותו (רצוי דקלרטיבית), ואחר כך refresh ל-Applications."),
   F("multicluster", "Which is a real advantage of running one Argo CD per cluster?",
     ("A smaller blast radius if one instance is compromised or broken", "נכון. כל instance מחזיק credentials רק לקלאסטר שלו, ולכן פריצה או תקלה נשארות בקלאסטר אחד."),
     ("A single UI for every environment", "UI אחד לכל הסביבות הוא דווקא היתרון של hub מרכזי. עם instance לכל קלאסטר יש UI לכל אחד."),
     ("Fewer instances to upgrade", "זה ההפך: instance לכל קלאסטר אומר יותר התקנות לשדרג, לנטר ולגבות."),
     ("No need for RBAC", "כל instance עדיין צריך RBAC כדי לקבוע מי רשאי לעשות מה, גם אם הוא מנהל קלאסטר אחד."),
     x="instance לכל קלאסטר מבודד תקלות ופריצות. המחיר הוא יותר instances לתחזק ואין תמונה אחת של כל הסביבות."),
   F("scale-in-practice", "Someone removed a line from an ApplicationSet's list generator, and a whole production service vanished. What would have prevented it?",
     ("`preserveResourcesOnDeletion`, or a sync policy that doesn't delete Applications", "נכון. ה-ApplicationSet מחק את ה-Application, וה-finalizer מחק את המשאבים. כל אחת מההגנות הייתה עוצרת את השרשרת."),
     ("A longer reconciliation timeout", "timeout ארוך רק מעכב את אותה מחיקה בכמה דקות. התוצאה הסופית זהה."),
     ("More repo-server replicas", "repo-server מרנדר manifests. הוא לא מחליט על מחיקת Applications ולא יכול למנוע אותה."),
     ("Turning off health checks", "health checks מודדים אם משאבים עובדים. הם לא מעורבים במחיקת Application בכלל."),
     x="ApplicationSet הוא הבעלים של ה-Applications. שורה שנעלמה מה-generator מוחקת Application, ואיתו את המשאבים. preserveResourcesOnDeletion ו-applicationsSync: create-update מונעים מחיקה כזאת."),
 ],
}
