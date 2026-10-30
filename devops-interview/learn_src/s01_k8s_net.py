# -*- coding: utf-8 -*-
from _h import *

SUBJECT = {
 "sec": 1, "nm": "Kubernetes: Services, Ingress & Networking", "tag": "How traffic finds a pod, and what blocks it",
 "deep": True,
 "modules": [

  MOD("services", "Services: איך תנועה מגיעה ל-pod",
      "להסביר את סוגי ה-Service, איך selector ו-EndpointSlices עובדים, ומה kube-proxy עושה.",
      [H("הבעיה ש-Service פותר"),
       P("ל-pods יש IP, אבל הוא משתנה בכל פעם שה-pod מוחלף, ובזמן rollout יש בכל רגע קבוצה אחרת של pods. **Service** נותן שם DNS ו-IP וירטואלי יציבים (ה-**ClusterIP**, מטווח כתובות נפרד מזה של ה-pods), ומפזר את התנועה בין ה-pods שה-**selector** שלו בוחר לפי labels. הלקוח מדבר עם `api.shop`, ולא יודע ולא צריך לדעת כמה pods יש ואיפה."),
       CODE("""
apiVersion: v1
kind: Service
metadata: {name: api, namespace: shop}
spec:
  selector: {app: api}          # must match the pod labels exactly
  ports:
  - name: http
    port: 80                    # what clients call: api.shop:80
    targetPort: http            # the named containerPort in the pod (8080)
""", cap="targetPort בשם: אם הפורט בקונטיינר משתנה, ה-Service לא צריך לשתנות"),
       FLOW("Service עם selector", "EndpointSlices עם IPs של pods", "kube-proxy מתכנת חוקים על כל node", "חבילה ל-ClusterIP מגיעה ל-pod"),
       H("EndpointSlices: הרשימה החיה"),
       P("ה-Service עצמו לא מחזיק רשימת pods. controller צופה ב-pods שמתאימים ל-selector וכותב **EndpointSlices**: אובייקטים עם כתובות ה-pods, הפורטים, ו-conditions לכל כתובת (`ready`, `serving`, `terminating`). כל slice מחזיק עד 100 כתובות כברירת מחדל, וכך שינוי ב-pod אחד לא מחייב לשלוח לכל ה-nodes רשימה ענקית. Service **בלי selector** לא מקבל EndpointSlices אוטומטית, ואפשר לכתוב אותם ידנית, למשל כדי להפנות שם פנימי ל-DB מחוץ לקלאסטר."),
       KEY("רק pods שהם **Ready** מקבלים תנועה חדשה. pod שנכשל ב-readiness נשאר ב-slice עם `ready: false`, ולא מקבל בקשות גם אם הוא Running."),
       TABLE(["סוג", "מה הוא נותן", "מתי"],
             ["ClusterIP", "IP וירטואלי בתוך הקלאסטר בלבד", "תקשורת בין שירותים. ברירת המחדל"],
             ["NodePort", "פורט (30000 עד 32767) על כל node, מעל ClusterIP", "גישה פשוטה מבחוץ, או בסיס ל-LoadBalancer"],
             ["LoadBalancer", "load balancer מהענן שמפנה ל-nodes או ישירות ל-pods", "חשיפת שירות לאינטרנט או ל-VPC"],
             ["Headless", "`clusterIP: None`: אין IP וירטואלי, וה-DNS מחזיר את כתובות ה-pods", "StatefulSets, לקוחות שבוחרים pod בעצמם"],
             ["ExternalName", "רשומת CNAME לשם חיצוני, בלי proxy", "כינוי לשירות מחוץ לקלאסטר"]),
       H("kube-proxy: מי באמת מעביר את החבילה"),
       P("ה-ClusterIP לא שייך לשום ממשק רשת, ואין תהליך שמאזין עליו. **kube-proxy** רץ על כל node, צופה ב-Services וב-EndpointSlices, ומתכנת חוקים ב-kernel. כש-pod שולח חבילה ל-ClusterIP, ה-kernel של ה-node **המקור** עושה DNAT לכתובת של pod אחד, וזוכר את הבחירה ב-conntrack. התנועה עצמה לא עוברת דרך התהליך של kube-proxy."),
       TABLE(["Mode", "איך הוא עובד", "מצב"],
             ["`iptables`", "שרשראות חוקים; בחירת pod אקראית", "ברירת המחדל היום. עדכונים איטיים בקלאסטרים עם אלפי Services"],
             ["`nftables`", "היורש של iptables ב-kernel, עדכונים מהירים יותר", "GA ב-1.33, דורש kernel 5.13 ומעלה; מתוכנן להיות ברירת המחדל"],
             ["`ipvs`", "טבלאות hash ואלגוריתמים כמו least-connection", "deprecated מ-1.35, ויכובה כברירת מחדל ב-1.40"],
             ["eBPF (למשל Cilium)", "ה-CNI מחליף את kube-proxy לגמרי", "לא חלק מ-Kubernetes עצמו"]),
       P("מכאן נובעת תופעה שחוזרת בראיונות: Service מאזן **חיבורים**, לא בקשות. לקוח gRPC או HTTP/2 שפותח חיבור אחד ארוך ישלח את כל הבקשות לאותו pod, וה-pods החדשים אחרי scale-up לא יקבלו כלום. הפתרון הוא איזון בצד הלקוח, service mesh, או חיבורים שמתחדשים. `sessionAffinity: ClientIP` עושה את ההפך: מצמיד כל לקוח ל-pod אחד בכוונה."),
       TRAP("ה-selector חייב להתאים בדיוק ל-labels של ה-pods, ו-`targetPort` חייב להתאים לפורט שהאפליקציה מאזינה עליו. טעות ב-selector נותנת Service בלי endpoints. טעות ב-targetPort נותנת connection refused, למרות שה-endpoints נראים תקינים."),
       CODE("""
kubectl get endpointslices -n shop -l kubernetes.io/service-name=api
kubectl get pods -n shop -l app=api -o wide      # the same set the selector picks?
""", cap="שתי הפקודות שמראות אם ה-Service באמת רואה pods"),
      ],
      [C("Which pods does a Service send traffic to?",
         ("Pods that match its selector and are currently Ready", "נכון. ה-Service בוחר pods לפי selector, ורק pods שעוברים readiness נכנסים ל-EndpointSlices ומקבלים תנועה."),
         ("Every pod in the namespace that exposes the same port", "Service לא בוחר לפי namespace או פורט. רק pods שה-labels שלהם תואמים ל-selector נכנסים, ורק אם הם Ready."),
         ("Only pods running on the same node as the client", "זו לא ברירת המחדל. internalTrafficPolicy: Local מגביל ל-node המקומי, אבל רגיל התנועה מתחלקת בין כל ה-endpoints."),
         ("Pods started from the same image as the Service names", "Service לא מכיר images בכלל. הבחירה היא רק לפי labels ב-selector, ומשם ל-EndpointSlices."),
         x="ה-Service בוחר pods לפי selector, ורק pods שעוברים readiness נכנסים ל-EndpointSlices ומקבלים תנועה."),
       C("What does a headless Service (`clusterIP: None`) return from DNS?",
         ("The IP addresses of the individual pods behind it", "נכון. headless Service לא מקבל IP וירטואלי, וה-DNS מחזיר רשומת A לכל pod. StatefulSet משתמש בזה לשם קבוע לכל pod."),
         ("A single virtual ClusterIP shared by all the pods", "זה Service רגיל. ב-headless אין IP וירטואלי בכלל, ולכן ה-DNS מחזיר את ה-pods עצמם."),
         ("The IP address of the node that runs the first pod", "DNS של Service לא מחזיר כתובות של nodes. headless מחזיר רשומת A לכל pod שהוא Ready."),
         ("Nothing, because headless Services skip DNS entirely", "ל-headless Service יש רשומות DNS, ודווקא לכל pod. בלי IP וירטואלי, ה-DNS הוא הדרך להגיע אליהם."),
         x="headless Service לא מקבל IP וירטואלי. ה-DNS מחזיר רשומת A לכל pod, וזה מה ש-StatefulSets צריכים."),
       C("What does kube-proxy actually do?",
         ("Programs kernel rules that send Service traffic to pods", "נכון. kube-proxy עוקב אחרי Services ו-EndpointSlices ומתכנת חוקי iptables או nftables על כל node. החבילות עצמן עוברות בקרנל."),
         ("Receives every packet and forwards it in user space", "זה היה מצב userspace הישן. היום kube-proxy רק מתכנת iptables או nftables, והקרנל מעביר את החבילות."),
         ("Assigns an IP address to each pod when it is created", "כתובות של pods מגיעות מה-CNI (IPAM), לא מ-kube-proxy. kube-proxy מטפל רק ב-Services."),
         ("Runs the cluster DNS that resolves the Service names", "DNS בקלאסטר הוא CoreDNS. kube-proxy לא עונה על שאילתות, רק מתרגם ClusterIP ל-pods."),
         x="kube-proxy מתכנת חוקי iptables או nftables. ה-IPs של pods הם עבודה של ה-CNI, וה-DNS הוא CoreDNS."),
      ]),

  MOD("ingress-dns", "Ingress, Gateway API ו-DNS בקלאסטר",
      "להסביר מה Ingress controller עושה, במה Gateway API שונה, ואיך שמות DNS של Services נבנים.",
      [H("Ingress: משאב ו-controller"),
       P("**Ingress** הוא משאב שמתאר ניתוב HTTP ו-HTTPS ב-L7: לפי host ולפי path, עם TLS. המשאב לבד לא עושה כלום. צריך **Ingress controller** שקורא את המשאבים ומגדיר proxy או load balancer אמיתי, למשל AWS Load Balancer Controller שיוצר ALB, או Traefik. ה-controller נבחר לפי `ingressClassName`. ingress-nginx, שהיה הנפוץ ביותר, הופסק במרץ 2026 (אין יותר גרסאות ותיקוני אבטחה), ולכן בפרויקטים חדשים בוחרים controller אחר או Gateway API."),
       CODE("""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: shop, namespace: shop}
spec:
  ingressClassName: alb
  tls: [{hosts: [shop.example.com], secretName: shop-tls}]
  rules:
  - host: shop.example.com
    http:
      paths:
      - {path: /api, pathType: Prefix, backend: {service: {name: api, port: {number: 80}}}}
      - {path: /, pathType: Prefix, backend: {service: {name: web, port: {number: 80}}}}
""", cap="host אחד, שני Services לפי path, ו-TLS מתוך Secret"),
       P("`pathType` חובה. `Exact` דורש התאמה מלאה. `Prefix` מתאים לפי רכיבי path מופרדים ב-`/`, ולכן `/api` מתאים ל-`/api/users` אבל לא ל-`/apis`. `ImplementationSpecific` משאיר את ההחלטה ל-controller, ולכן מתנהג אחרת בין controllers. כשכמה paths מתאימים, ה-path הארוך ביותר מנצח."),
       SPLIT(("Service מסוג LoadBalancer", ["L4: TCP ו-UDP", "load balancer לכל Service", "לא מבין HTTP, hosts או paths"]),
             ("Ingress", ["L7: HTTP ו-HTTPS", "load balancer אחד להרבה Services", "ניתוב לפי host ו-path, וסיום TLS"])),
       P("ה-API של Ingress **קפוא**: הוא GA ולא יוסר, אבל לא יקבל יכולות חדשות. כל מה שחסר בו (חלוקת תנועה לפי משקל, ניתוב לפי header, timeouts) מומש בכל controller כ-annotations משלו, ולכן Ingress שעובד עם controller אחד לא בהכרח עובד עם אחר. Kubernetes ממליץ היום על Gateway API."),
       H("Gateway API"),
       P("Gateway API הוא היורש של Ingress, ומותקן כ-CRDs נפרדים. הוא מפריד בין תפקידים: ספק התשתית מגדיר `GatewayClass`, צוות הפלטפורמה מגדיר `Gateway` (listeners, פורטים, תעודות TLS, ואילו namespaces רשאים לחבר routes), וצוותי האפליקציות מגדירים `HTTPRoute` או `GRPCRoute` ב-namespace שלהם. הפניה ל-Service ב-namespace אחר מחייבת `ReferenceGrant` מהצד השני, כך שצוות לא יכול למשוך תנועה ל-Service של צוות אחר בלי הסכמה."),
       CODE("""
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: {name: api, namespace: shop}
spec:
  parentRefs: [{name: public, namespace: infra}]   # the Gateway the platform team owns
  hostnames: [shop.example.com]
  rules:
  - matches: [{path: {type: PathPrefix, value: /api}}]
    backendRefs:
    - {name: api-v1, port: 80, weight: 90}
    - {name: api-v2, port: 80, weight: 10}           # canary without annotations
""", cap="חלוקת תנועה לפי משקל היא חלק מה-API, לא annotation של controller"),
       H("DNS בתוך הקלאסטר"),
       P("**CoreDNS** רץ כ-Deployment ב-`kube-system` מאחורי Service בשם `kube-dns`. ה-kubelet כותב לכל pod `resolv.conf` שמצביע על ה-ClusterIP של `kube-dns`, עם search domains של ה-namespace. CoreDNS עונה על שמות הקלאסטר מתוך ה-API (התוסף `kubernetes`), ומעביר כל שם אחר ל-DNS של ה-node (`forward . /etc/resolv.conf`), עם cache של 30 שניות."),
       TABLE(["מה", "השם"],
             ["Service", "`<svc>.<ns>.svc.cluster.local`"],
             ["מאותו namespace", "מספיק `<svc>`, בזכות search domains"],
             ["מ-namespace אחר", "`<svc>.<ns>`"],
             ["pod של StatefulSet", "`<pod>.<headless-svc>.<ns>.svc.cluster.local`"],
             ["פורט עם שם", "רשומת SRV: `_http._tcp.<svc>.<ns>.svc.cluster.local`"]),
       TRAP("`dnsPolicy: Default` הוא לא ברירת המחדל. ברירת המחדל היא `ClusterFirst`, ו-`Default` דווקא נותן ל-pod את ה-DNS של ה-node, כך ששמות של Services לא נפתרים. pod עם `hostNetwork: true` צריך `ClusterFirstWithHostNet` כדי לפתור שמות של הקלאסטר."),
       P("`ndots:5` ב-`resolv.conf` גורם לשם חיצוני כמו `api.example.com` לעבור קודם דרך כל ה-search domains, וזה מכפיל את מספר השאילתות ל-CoreDNS. כשיש תקלות DNS לסירוגין בודקים את ה-pods של CoreDNS, את הלוגים שלהם ואת ה-CPU throttling, ושוקלים NodeLocal DNSCache, שמוסיף cache על כל node."),
      ],
      [C("What happens if you create an Ingress but no Ingress controller is installed?",
         ("Nothing; no proxy or load balancer gets set up", "נכון. Ingress הוא רק הגדרה. בלי controller שקורא אותו, אף אחד לא מקים proxy ולא מגיעה תנועה."),
         ("Kubernetes creates a default cloud load balancer", "Kubernetes לא יוצר load balancer בשביל Ingress. רק controller שקורא את ה-Ingress מקים proxy או ALB."),
         ("The Ingress is turned into a NodePort Service", "אין המרה כזו. Ingress ו-Service הם משאבים נפרדים, וה-Ingress פשוט יושב ב-API בלי שאף אחד מטפל בו."),
         ("The API server rejects it until a controller exists", "ה-API מקבל את ה-Ingress בלי בדיקה כזו. הוא נשמר, אבל לא קורה כלום עד שיש controller."),
         x="Ingress הוא רק הגדרה. בלי controller שקורא אותו, אף אחד לא מקים proxy ולא מגיעה תנועה."),
       C("What is the full DNS name of Service `api` in namespace `shop`?",
         ("`api.shop.svc.cluster.local`", "נכון. הפורמט הוא `<service>.<namespace>.svc.cluster.local`. מתוך אותו namespace מספיק `api`, ומ-namespace אחר `api.shop`."),
         ("`shop.api.svc.cluster.local`", "הסדר הפוך. קודם שם ה-Service ואחר כך ה-namespace: `<service>.<namespace>.svc.cluster.local`."),
         ("`api.svc.shop.cluster.local`", "`svc` בא אחרי ה-namespace, לא לפניו. השם הנכון הוא `api.shop.svc.cluster.local`."),
         ("`api.shop.pod.cluster.local`", "`pod` שייך לרשומות של pods לפי IP, לא ל-Services. Service יושב תחת `svc`."),
         x="הפורמט הוא `<service>.<namespace>.svc.cluster.local`. מתוך אותו namespace מספיק `api`."),
       C("What does Gateway API separate that Ingress mixes together?",
         ("Infrastructure (Gateway) from application routing (HTTPRoute)", "נכון. צוות התשתית מנהל GatewayClass ו-Gateway, וצוותי האפליקציה מנהלים HTTPRoute. ב-Ingress הכול באותו משאב, ועוד annotations לכל controller."),
         ("TCP traffic from UDP traffic, with separate controllers", "Gateway API תומך בכמה פרוטוקולים (TCPRoute, UDPRoute), אבל ההפרדה המרכזית היא בין תפקידים, לא בין פרוטוקולים."),
         ("Pods from nodes, so routing never touches the node IPs", "Gateway API לא עוסק בהפרדה בין pods ל-nodes. הוא מגדיר מי מנהל את ה-load balancer ומי את חוקי הניתוב."),
         ("TLS secrets from routing rules, in two separate namespaces", "אפשר לשמור תעודות במקום נפרד עם ReferenceGrant, אבל זו לא ההפרדה המרכזית. העיקר: Gateway מול HTTPRoute."),
         x="ב-Gateway API צוות התשתית מנהל GatewayClass ו-Gateway, וצוותי האפליקציה מנהלים HTTPRoute. ב-Ingress הכול באותו משאב."),
      ]),

  MOD("netpol-debug", "NetworkPolicy ודיבוג רשת",
      "לכתוב NetworkPolicy בסיסית, ולדבג Service שלא עונה צעד אחרי צעד.",
      [H("NetworkPolicy: איך הבידוד עובד"),
       P("כברירת מחדל, כל pod יכול לדבר עם כל pod בקלאסטר, בכל namespace. **NetworkPolicy** בוחרת pods לפי labels (`podSelector`) ומגדירה מאיפה מותר להם לקבל תנועה (ingress) ולאן מותר להם לשלוח (egress). ההיגיון הוא allow-list: ברגע ש-pod נבחר על ידי policy כלשהי בכיוון מסוים, הוא **מבודד** בכיוון הזה, וכל מה שלא מותר במפורש נחסם. pod שאף policy לא בוחרת נשאר פתוח לגמרי."),
       UL("אין חוקי deny. policies רק מוסיפות היתרים, וכמה policies על אותו pod מתחברות לאיחוד (union), כך שסדר ההגדרה לא משנה.",
          "תנועת תשובה של חיבור מותר מותרת אוטומטית. מספיק לאפשר את כיוון פתיחת החיבור.",
          "תנועה בין pod ל-node שהוא רץ עליו תמיד מותרת, ולכן probes של ה-kubelet ממשיכים לעבוד.",
          "האכיפה היא של ה-CNI (Calico, Cilium, VPC CNI עם network policy מופעל). בלי CNI שתומך, policy נשמרת ב-API ולא עושה כלום, בלי שום שגיאה."),
       CODE("""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: {name: db-from-web, namespace: data}
spec:
  podSelector: {matchLabels: {app: db}}
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: web}}
    ports: [{port: 5432}]
""", cap="רק pods מ-namespace web יכולים להגיע ל-DB בפורט 5432. ה-label `kubernetes.io/metadata.name` קיים על כל namespace"),
       H("AND מול OR: הרווח שמשנה הכול"),
       P("בתוך `from`, כל פריט ברשימה הוא מקור נפרד, והפריטים מתחברים ב-OR. `namespaceSelector` ו-`podSelector` **באותו פריט** מתחברים ב-AND. ההבדל ב-YAML הוא מקף אחד, וההבדל בפועל הוא בין \"pods עם label מסוים מ-namespace מסוים\" לבין \"כל pod מה-namespace, או pod עם ה-label מכל namespace\"."),
       CODE("""
  ingress:
  # ONE item = AND
  - from:
    - namespaceSelector: {matchLabels: {team: web}}
      podSelector: {matchLabels: {app: frontend}}
  # TWO items = OR
  - from:
    - namespaceSelector: {matchLabels: {team: web}}
    - podSelector: {matchLabels: {app: frontend}}
""", cap="פריט אחד: pods של frontend בתוך namespaces של team=web. שני פריטים: כל pod מ-team=web, או frontend מה-namespace הזה. מקף אחד הופך AND ל-OR"),
       H("default-deny, ואז היתרים"),
       P("הדפוס המקובל הוא policy של default-deny לכל namespace, ואחריה היתרים מפורשים לכל זרימה שצריכה לעבוד. `podSelector: {}` בוחר את כל ה-pods ב-namespace, ורשימה ריקה של חוקים לא מתירה כלום."),
       CODE("""
kind: NetworkPolicy
metadata: {name: default-deny, namespace: shop}
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
---
kind: NetworkPolicy
metadata: {name: allow-dns, namespace: shop}
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to: [{namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: kube-system}}}]
    ports: [{port: 53, protocol: UDP}, {port: 53, protocol: TCP}]
""", cap="בלי ההיתר השני שום שם לא נפתר, וכל האפליקציות נראות שבורות"),
       TRAP("default-deny על egress שובר גם DNS. צריך לאפשר במפורש UDP ו-TCP 53 ל-kube-dns, אחרת שום שם לא נפתר, והשגיאה נראית כמו בעיה באפליקציה ולא ברשת."),
       H("Service לא עונה: סדר הבדיקה"),
       P("מדבגים מבפנים החוצה, שכבה אחרי שכבה, מ-pod זמני עם כלים: `kubectl run tmp -it --rm --image=nicolaka/netshoot -- bash`. כל שלב מצמצם את החשודים לרכיב אחד."),
       TREE(["יש endpoints? `kubectl get endpointslices`", "אם ריק: selector לא תואם, או pods לא Ready"],
            ["pod IP עונה ישירות מ-pod דיבאג?", "אם לא: האפליקציה, הפורט, או האזנה על 127.0.0.1 במקום 0.0.0.0"],
            ["pod IP עונה, ה-ClusterIP לא?", "kube-proxy או ה-CNI על ה-node, או targetPort שגוי"],
            ["ה-ClusterIP עונה, השם לא?", "DNS: CoreDNS, resolv.conf, או egress חסום לפורט 53"],
            ["עובד מ-namespace אחד ולא מאחר?", "NetworkPolicy"]),
       P("refused מול timeout הוא רמז חשוב: **connection refused** אומר שהחבילה הגיעה ואין שם מי שמאזין (פורט שגוי, אפליקציה שלא עלתה). **timeout** אומר שהחבילה נזרקה בדרך, וזה סימן ל-NetworkPolicy, security group או בעיית ניתוב."),
       P("Ingress שמחזיר 502 או 504: הבקשה הגיעה ל-controller, אז הבעיה מאחוריו. בודקים את הלוגים של ה-controller, את ה-endpoints של ה-Service, התאמת פורטים ופרוטוקול (HTTP מול HTTPS ל-backend), ו-timeouts שקצרים מזמן התגובה של האפליקציה."),
      ],
      [C("Without any NetworkPolicy, which pods can talk to each other?",
         ("All pods, across all namespaces", "נכון. ברירת המחדל היא רשת פתוחה. רק NetworkPolicy, ו-CNI שאוכף אותה, מגבילים תנועה בין pods."),
         ("Only pods inside the same namespace", "namespace לא מבודד רשת. בלי NetworkPolicy כל pod מגיע לכל pod, בכל namespace."),
         ("Only pods scheduled on the same node", "הרשת של Kubernetes שטוחה: pods מדברים בין nodes בלי NAT. אין מגבלה לפי node."),
         ("None, until a policy allows the traffic", "זה המצב אחרי default-deny. בלי policy בכלל, ברירת המחדל היא רשת פתוחה לגמרי."),
         x="ברירת המחדל ב-Kubernetes היא רשת פתוחה. רק NetworkPolicy (ו-CNI שאוכף אותה) מגבילה."),
       C("After applying default-deny egress, no DNS lookups work. What was forgotten?",
         ("An egress rule allowing port 53 to kube-dns", "נכון. default-deny egress חוסם גם את שאילתות ה-DNS. צריך חוק egress ל-kube-dns בפורט 53, ב-UDP וב-TCP."),
         ("A readiness probe on every CoreDNS pod", "ל-CoreDNS כבר יש probes. הבעיה היא שה-policy חוסמת את היציאה מה-pods אל ה-DNS."),
         ("A LoadBalancer Service in front of CoreDNS", "CoreDNS זמין דרך ה-ClusterIP של kube-dns. load balancer לא יעקוף policy שחוסמת egress."),
         ("An ingress rule letting kube-dns reach the pods", "התשובות חוזרות בחיבור שה-pod פתח, ולכן לא צריך חוק ingress. מה שחסר הוא egress לפורט 53."),
         x="default-deny egress חוסם גם את שאילתות ה-DNS. צריך חוק egress ל-kube-dns בפורט 53, ב-UDP וב-TCP."),
       C("A Service has no endpoints. What is the most likely cause?",
         ("No pod matches its selector, or none of them is Ready", "נכון. EndpointSlices ריקים אומרים שאין pods שתואמים ל-selector, או שאף אחד מהם לא Ready. זה הדבר הראשון לבדוק."),
         ("CoreDNS is down, so the Service can't find its pods", "Service לא משתמש ב-DNS כדי למצוא pods. ה-EndpointSlices נבנים מה-selector, בלי קשר ל-CoreDNS."),
         ("No Ingress controller is installed for this Service", "Ingress controller לא קשור ל-endpoints של Service. ה-endpoints נקבעים לפי selector ו-readiness."),
         ("The node running the pods has too little free disk", "לחץ דיסק יכול לפנות pods, אבל הוא לא הסיבה הראשונה ל-endpoints ריקים. קודם בודקים selector ו-readiness."),
         x="EndpointSlices ריקים אומרים שאין pods שתואמים ל-selector ושהם Ready. זה הדבר הראשון לבדוק."),
      ]),

  MOD("net-in-practice", "בפועל: מסלול של בקשה, EndpointSlices ו-externalTrafficPolicy",
      "לעקוב אחרי בקשה מה-load balancer עד ה-pod, לקרוא EndpointSlices, ולהסביר מתי מאבדים את ה-IP של הלקוח.",
      [P("רוב שאלות הרשת בראיון הן בעצם 'תעקוב אחרי הבקשה'. כאן עוברים על המסלול, על הפקודות שמראות כל שלב, ועל ההגדרות שמשנות את ההתנהגות."),
       FLOW("DNS של הלקוח מחזיר את ה-load balancer", "LB שולח ל-node (או ישר ל-pod IP)", "kube-proxy או eBPF מתרגם ClusterIP ל-pod", "ה-pod עונה", cap="מסלול של בקשה מבחוץ"),
       H("EndpointSlices: מי באמת מקבל traffic"),
       CODE("""$ kubectl get endpointslices -l kubernetes.io/service-name=api
NAME        ADDRESSTYPE   PORTS   ENDPOINTS                AGE
api-x7k2d   IPv4          8080    10.0.3.17,10.0.5.88      3h

$ kubectl get endpointslice api-x7k2d -o yaml | grep -A3 conditions
    conditions:
      ready: false        # ה-pod לא עובר readiness
      serving: true
      terminating: true   # ה-pod בתהליך כיבוי""", cap="Service בלי endpoints מוכנים = אף pod לא מקבל traffic"),
       KEY("Service שלא עונה: קודם `kubectl get endpointslices`. אם הרשימה ריקה, ה-selector לא תואם ל-labels של ה-pods, או שאף pod לא Ready. רק אם יש endpoints בודקים את הרשת עצמה."),
       H("externalTrafficPolicy"),
       TABLE(["הגדרה", "IP הלקוח", "פיזור עומס", "סיכון"],
             ["`Cluster` (ברירת מחדל)", "אובד: עובר SNAT ל-IP של ה-node", "שווה בין כל ה-pods", "hop נוסף בין nodes"],
             ["`Local`", "נשמר", "רק ל-pods על ה-node שקיבל", "node בלי pod נכשל ב-health check של ה-LB"]),
       P("ב-EKS עם AWS Load Balancer Controller ו-`target-type: ip`, ה-LB שולח ישר ל-IP של ה-pod, בלי לעבור דרך NodePort. כך שומרים על מסלול קצר, ואפשר לשמור IP לקוח עם proxy protocol או עם `X-Forwarded-For` ב-ALB."),
       H("DNS ו-ndots"),
       CODE("""$ kubectl exec -it api-7d9f8c6b5-2xkqp -- cat /etc/resolv.conf
search prod.svc.cluster.local svc.cluster.local cluster.local
nameserver 172.20.0.10
options ndots:5""", cap="ה-resolv.conf שכל pod מקבל"),
       P("עם `ndots:5`, שם כמו `api.example.com` (שתי נקודות) נחשב 'קצר', וה-resolver מנסה קודם את כל ה-search domains: `api.example.com.prod.svc.cluster.local` ועוד. כל בקשה חיצונית הופכת לכמה שאילתות. פתרון: נקודה בסוף השם, או `dnsConfig` עם `ndots: 2`, ו-NodeLocal DNSCache."),
       TRAP("headless Service (`clusterIP: None`) לא מקבל IP ולא עובר דרך kube-proxy: DNS מחזיר ישר את כתובות ה-pods. זה מה ש-StatefulSet צריך (`db-0.db.prod.svc.cluster.local`), אבל אין בו load balancing ברמת הקלאסטר."),
       ASK(("מה קורה מרגע שבקשה מגיעה ל-NodePort ועד שהיא מגיעה ל-pod?",
            "הבקשה מגיעה לפורט ב-node (30000 עד 32767). חוקי iptables או nftables ש-kube-proxy תכנת מתרגמים אותה ב-DNAT לאחד ה-pods ב-EndpointSlices, אולי על node אחר. עם externalTrafficPolicy: Cluster יש גם SNAT, כדי שהתשובה תחזור דרך אותו node. ה-CNI מעביר את החבילה ל-pod, ו-conntrack זוכר את החיבור בשביל התשובה."),
           ("למה האפליקציה רואה את ה-IP של ה-node ולא של הלקוח, ואיך מתקנים?",
            "עם externalTrafficPolicy: Cluster, ה-node שקיבל את הבקשה יכול להעביר אותה ל-pod על node אחר, ועושה SNAT לכתובת שלו. פתרונות: externalTrafficPolicy: Local (בלי SNAT, אבל פיזור עומס לא שווה), או ב-load balancer של L7 לקרוא את X-Forwarded-For, וב-NLB להשתמש ב-IP targets או ב-proxy protocol."),
           ("מה ההבדל בין Service רגיל ל-headless Service?",
            "Service רגיל מקבל ClusterIP וירטואלי אחד, ו-kube-proxy מפזר ממנו ל-pods. headless (clusterIP: None) לא מקבל IP, וה-DNS מחזיר את הכתובות של ה-pods עצמם. משתמשים בו כשהלקוח צריך לבחור pod מסוים, למשל ב-StatefulSet שבו לכל pod יש שם קבוע כמו db-0.db."),
           ("למה שאילתות DNS חיצוניות מקלאסטר איטיות לפעמים?",
            "ndots:5 גורם לכל שם עם פחות מחמש נקודות לעבור קודם דרך כל ה-search domains, וכל ניסיון הוא שאילתה שנכשלת. בנוסף יש race ב-conntrack כשבקשות A ו-AAAA יוצאות במקביל ב-UDP, ו-CoreDNS עמוס. פתרונות: FQDN עם נקודה בסוף, ndots נמוך יותר, NodeLocal DNSCache ויותר replicas ל-CoreDNS.")),
      ],
      [C("A Service has `port: 80` and `targetPort: 8080`. What does each one mean?",
         ("`port` is what clients call; `targetPort` is the pod's port", "נכון. port הוא הפורט שלקוחות פונים אליו ב-ClusterIP, ו-targetPort הוא הפורט שהאפליקציה מאזינה עליו בתוך ה-pod."),
         ("`port` is on the node; `targetPort` is on the load balancer", "פורט על ה-node הוא nodePort, ו-load balancer הוא סוג של Service. port ו-targetPort מתארים את ה-Service ואת ה-pod."),
         ("`targetPort` is what clients call; `port` is the pod's port", "זה הפוך. לקוחות פונים ל-port של ה-Service, וה-Service מעביר ל-targetPort, הפורט שהאפליקציה מאזינה עליו."),
         ("Both must be equal, or the Service is rejected by the API", "הם לא חייבים להיות שווים, וזה בדיוק היתרון: Service על 80 מול אפליקציה שמאזינה על 8080."),
         x="port הוא הפורט של ה-Service, ו-targetPort הוא הפורט על ה-pod. אם targetPort לא תואם לפורט שהאפליקציה מאזינה עליו, החיבור נכשל."),
       C("Which `externalTrafficPolicy` keeps the client's source IP?",
         ("`Local`, which skips the SNAT hop", "נכון. Local שולח רק ל-pods על ה-node שקיבל את הבקשה, בלי SNAT, ולכן ה-IP של הלקוח נשמר. המחיר הוא פיזור עומס לא שווה."),
         ("`Cluster`, which spreads traffic evenly", "Cluster היא ברירת המחדל. היא מפזרת טוב, אבל עושה SNAT כשהבקשה עוברת node, וה-IP של הלקוח הולך לאיבוד."),
         ("`Preserve`, which keeps client headers", "אין ערך Preserve ל-externalTrafficPolicy. הערכים הם Cluster ו-Local בלבד, ו-headers לא קשורים לזה."),
         ("`Direct`, which bypasses kube-proxy", "אין ערך Direct. הערכים הם Cluster ו-Local, ורק Local שומר את כתובת הלקוח."),
         x="Local לא עושה SNAT ושולח רק ל-pods על אותו node, ולכן ה-IP של הלקוח נשמר. המחיר: פיזור לא שווה."),
       C("Why can lookups of external names from a pod be slow with `ndots:5`?",
         ("Short names are tried with every search domain first", "נכון. שם עם פחות מחמש נקודות עובר קודם דרך כל ה-search domains, וכל ניסיון הוא שאילתה שנכשלת לפני השם האמיתי."),
         ("ndots caps DNS at five queries per second per pod", "ndots לא מגביל קצב. הוא קובע כמה נקודות צריכות להיות בשם כדי שינוסה כמו שהוא, לפני ה-search domains."),
         ("ndots turns off the DNS cache inside each pod", "ndots לא נוגע ב-cache. הבעיה היא מספר השאילתות לכל שם חיצוני, לא caching."),
         ("ndots forces every lookup to go over TCP instead", "ndots לא קובע פרוטוקול. DNS עובר ל-TCP רק בתשובות גדולות, בלי קשר להגדרה הזו."),
         x="שם עם פחות מ-5 נקודות עובר קודם דרך כל ה-search domains, וכל אחד הוא שאילתה נוספת שנכשלת."),
      ], min=10),

 ],

 "recap": [
   H("השרשרת"),
   FLOW("לקוח", "שם DNS של Service", "ClusterIP", "חוקי kube-proxy", "pod שהוא Ready"),
   TABLE(["סוג Service", "במשפט"],
         ["ClusterIP", "IP פנימי יציב"],
         ["NodePort", "פורט על כל node"],
         ["LoadBalancer", "load balancer מהענן"],
         ["Headless", "DNS שמחזיר IPs של pods"],
         ["ExternalName", "CNAME לשם חיצוני"]),
   TABLE(["כלי", "שכבה", "מה צריך בשבילו"],
         ["Service", "L4", "selector ו-pods שהם Ready"],
         ["Ingress", "L7", "Ingress controller"],
         ["Gateway API", "L4 ו-L7", "implementation של Gateway"],
         ["NetworkPolicy", "L3/L4", "CNI שאוכף policies"]),
   KEY("רק pods שהם Ready מקבלים תנועה. readiness הוא החיבור בין בריאות האפליקציה לבין הרשת."),
   H("DNS"),
   P("שם מלא של Service הוא `<svc>.<ns>.svc.cluster.local`. מאותו namespace מספיק השם הקצר. `ndots:5` גורם לשמות חיצוניים לעבור דרך search domains, ולכן תקלות DNS לסירוגין מתחילות בבדיקה של CoreDNS ושל ה-`resolv.conf` של ה-pod."),
   H("NetworkPolicy"),
   P("בלי policies הכול פתוח. pod שנבחר על ידי policy חסום בכל מה שלא הותר באותו כיוון. ב-default-deny egress זוכרים לפתוח DNS. ושום policy לא עובדת אם ה-CNI לא אוכף אותה."),
   H("Ingress מול Gateway API"),
   P("Ingress נותן ניתוב HTTP לפי host ו-path ו-TLS, ומחייב Ingress controller. Gateway API מוסיף הפרדת תפקידים (Gateway לתשתית, HTTPRoute לאפליקציה), חלוקת תנועה לפי משקל וניתוב לפי headers בלי annotations ספציפיים ל-controller. Service מסוג LoadBalancer נשאר הפתרון ל-L4 ולפרוטוקולים שאינם HTTP."),
   H("502 ו-504 מ-Ingress"),
   P("הבקשה הגיעה ל-controller. 502 אומר שה-backend החזיר תשובה לא תקינה או סגר חיבור; 504 אומר שהוא לא ענה בזמן. בודקים endpoints, התאמת פורט ופרוטוקול, pods שקורסים, ו-timeouts של ה-proxy מול זמן התגובה של האפליקציה."),
   TRAP("בראיון, Service שלא עונה הוא שאלה על סדר מחשבה: endpoints, אחר כך pod IP ישירות, אחר כך ClusterIP, אחר כך DNS, ורק בסוף NetworkPolicy. לקפוץ ישר ל-NetworkPolicy זה סימן שאין שיטה."),
 ],

 "final": [
   F("services", "Which Service type gives each pod its own DNS record instead of one virtual IP?",
     ("Headless, with `clusterIP: None`", "נכון. headless Service לא מקבל IP וירטואלי, וה-DNS מחזיר רשומת A לכל pod. ב-StatefulSet כל pod מקבל גם שם קבוע."),
     ("NodePort, with a port on every node", "NodePort פותח פורט על כל node ומעביר ל-Service. עדיין יש לו ClusterIP אחד, לא רשומה לכל pod."),
     ("LoadBalancer, with one DNS name per pod", "LoadBalancer מוסיף load balancer מהענן מעל ClusterIP. אין לו רשומת DNS לכל pod."),
     ("ExternalName, pointing at each pod's IP", "ExternalName מחזיר CNAME לשם חיצוני, בלי pods ובלי endpoints. הוא לא מצביע על pods בכלל."),
     x="headless Service משמש StatefulSets ולקוחות שצריכים לפנות ל-pod מסוים. כל pod מקבל רשומת A, ול-StatefulSet גם שם קבוע."),
   F("services", "A pod is Running but fails its readiness probe. Does it receive Service traffic?",
     ("No; it is left out of the EndpointSlices", "נכון. EndpointSlices כוללים רק pods שעוברים readiness. כך Kubernetes מוציא pod לא בריא מהתנועה בלי לאתחל אותו."),
     ("Yes; a Running pod always gets its share", "Running לא מספיק. רק pods שעוברים readiness נכנסים ל-EndpointSlices ומקבלים תנועה."),
     ("Only from clients on the same node as it", "אין חריג לפי node. pod שלא Ready לא נמצא ב-endpoints בכלל, לאף לקוח."),
     ("Only while a rolling update is in progress", "דווקא ב-rolling update readiness הכי חשוב: הוא מונע תנועה ל-pods חדשים שעוד לא מוכנים."),
     x="EndpointSlices כוללים רק pods שעוברים readiness. ככה Kubernetes מוציא pod לא בריא מהתנועה בלי להפעיל אותו מחדש."),
   F("services", "Your app listens on port 8080, but the Service's `targetPort` is 80. What happens?",
     ("Connections to the Service are refused or time out", "נכון. targetPort הוא הפורט על ה-pod. אם הוא לא תואם לפורט שהאפליקציה מאזינה עליו, החיבור נכשל, למרות שה-endpoints נראים תקינים."),
     ("Kubernetes detects the right port and corrects it", "Kubernetes לא בודק על איזה פורט האפליקציה מאזינה. הוא שולח בדיוק ל-targetPort שהוגדר."),
     ("The Service is created without any ClusterIP", "ה-ClusterIP נוצר כרגיל. הבעיה מתגלה רק כשהתנועה מגיעה לפורט שאף אחד לא מאזין עליו."),
     ("The pods fail readiness and leave the endpoints", "readiness נבדק לפי ה-probe, לא לפי targetPort. ה-pods יכולים להיות Ready וה-Service עדיין ייכשל."),
     x="`targetPort` הוא הפורט על ה-pod. אם הוא לא תואם לפורט שהאפליקציה מאזינה עליו, החיבור נכשל, למרות שה-endpoints נראים תקינים."),
   F("ingress-dns", "What does an Ingress need in order to route traffic?",
     ("An Ingress controller running in the cluster", "נכון. Ingress הוא רק תיאור של חוקי ניתוב. controller (למשל AWS Load Balancer Controller או Traefik) קורא אותו ומגדיר proxy או ALB."),
     ("A headless Service in front of each backend", "Ingress עובד עם Services רגילים. headless לא נדרש, ובלי controller אף Service לא יקבל תנועה מה-Ingress."),
     ("A NetworkPolicy that allows the incoming port", "NetworkPolicy רק מגבילה תנועה. בלי policy הרשת פתוחה, אבל עדיין אין מי שיקים proxy."),
     ("A LoadBalancer Service for every single host", "load balancer לכל host הוא בדיוק מה ש-Ingress חוסך. ה-controller מקים כניסה אחת לכל ה-hosts."),
     x="Ingress הוא רק תיאור של חוקי ניתוב. Ingress controller (למשל AWS Load Balancer Controller או Traefik) קורא אותו ומגדיר proxy או ALB."),
   F("ingress-dns", "Why can `ndots:5` slow down lookups of external names from pods?",
     ("Each external name is tried with every search domain", "נכון. שם עם פחות מחמש נקודות מנוסה קודם עם כל ה-search domains, וזה מכפיל את מספר השאילתות ל-CoreDNS."),
     ("It disables DNS caching for names outside the cluster", "ndots לא קשור ל-cache. הוא קובע מתי שם מנוסה כמו שהוא ומתי עם search domains."),
     ("It forces DNS over TCP for every external lookup", "הפרוטוקול לא תלוי ב-ndots. DNS עובר ל-TCP רק כשהתשובה גדולה מדי ל-UDP."),
     ("It sends every lookup straight to a public resolver", "pods פונים ל-CoreDNS בכל מקרה. ndots רק מוסיף ניסיונות עם search domains לפני השם המלא."),
     x="שם עם פחות מחמש נקודות מנוסה קודם עם כל ה-search domains. שם מלא עם נקודה בסוף, או ndots נמוך יותר, חוסך את השאילתות המיותרות."),
   F("ingress-dns", "From namespace `web`, how do you reach Service `db` in namespace `data`?",
     ("`db.data`, or `db.data.svc.cluster.local`", "נכון. צריך את ה-namespace בשם. `db.data` עובד בזכות search domain של `svc.cluster.local`, והשם המלא תמיד עובד."),
     ("`db`, since search domains cover every namespace", "search domains משלימים רק את ה-namespace של ה-pod עצמו, `web`. `db` לבד יחפש את `db.web`."),
     ("`data.db`, with the namespace written first", "הסדר הפוך: קודם שם ה-Service ואחר כך ה-namespace. `data.db` מחפש Service בשם data ב-namespace בשם db."),
     ("`db.data.local`, without the `svc` part", "בלי `svc.cluster.local` השם לא קיים. משתמשים ב-`db.data`, שה-search domain משלים, או בשם המלא."),
     x="search domains משלימים רק את ה-namespace של ה-pod עצמו. לשירות ב-namespace אחר כותבים לפחות `<svc>.<ns>`."),
   F("netpol-debug", "You apply a NetworkPolicy, but traffic is not blocked at all. What is a likely reason?",
     ("The cluster's CNI doesn't enforce NetworkPolicy", "נכון. NetworkPolicy נאכפת על ידי ה-CNI. Calico, Cilium ו-VPC CNI (עם network policy מופעל) אוכפים; flannel לבד לא."),
     ("NetworkPolicies only apply to Ingress resources", "NetworkPolicy חלה על pods, לא על Ingress. היא נאכפת ברמת הרשת על ידי ה-CNI."),
     ("Policies need about an hour to take effect", "אכיפה מתחילה תוך שניות כשה-CNI תומך. עיכוב כזה לא קיים, ולכן הבעיה היא באכיפה עצמה."),
     ("Pods must be restarted before policies apply", "policies חלות על pods רצים בלי restart. אם אין חסימה בכלל, ה-CNI כנראה לא אוכף."),
     x="NetworkPolicy נאכפת על ידי ה-CNI. Calico, Cilium ו-VPC CNI (עם network policy מופעל) אוכפים; flannel לבד לא."),
   F("netpol-debug", "A Service's endpoints are fine and the pod IP answers directly, but the ClusterIP doesn't. Where do you look?",
     ("kube-proxy or the CNI on that node", "נכון. כשה-pod עונה ישירות וה-ClusterIP לא, השכבה שמתרגמת ClusterIP ל-pod היא החשודה: kube-proxy (iptables או nftables) או ה-CNI."),
     ("The application code inside the pod", "ה-pod עונה ישירות, ולכן האפליקציה עובדת. הבעיה בשכבה שמתרגמת את ה-ClusterIP ל-pod."),
     ("The Ingress controller's routing rules", "Ingress לא מעורב בתנועה ל-ClusterIP מתוך הקלאסטר. ההמרה נעשית בחוקים של kube-proxy."),
     ("The image registry's pull credentials", "ה-pod כבר רץ ועונה, ולכן ה-image ירד. registry לא קשור לניתוב של ClusterIP."),
     x="כשה-pod עונה ישירות וה-ClusterIP לא, השכבה שמתרגמת ClusterIP ל-pod היא החשודה: kube-proxy (חוקי iptables או nftables) או ה-CNI."),
   F("netpol-debug", "An Ingress returns 502 for one service. What does that tell you first?",
     ("The request reached the controller; the backend failed", "נכון. 502 מה-controller אומר שהוא קיבל את הבקשה, אבל ה-backend החזיר תשובה לא תקינה או שהחיבור אליו נכשל."),
     ("DNS for the domain is broken for some of the clients", "אם DNS היה שבור, הבקשה לא הייתה מגיעה ל-controller בכלל. 502 אומר שהיא הגיעה."),
     ("The client's browser is blocking the response", "502 נוצר בצד השרת, ב-proxy. הדפדפן רק מציג את מה שה-controller החזיר."),
     ("The TLS certificate on the Ingress has already expired", "תעודה שפגה נותנת שגיאת TLS בדפדפן, לפני שיש תשובת HTTP. 502 אומר שה-TLS עבר והבקשה הגיעה."),
     x="502 מה-Ingress controller אומר שהוא קיבל את הבקשה אבל קיבל תשובה לא תקינה או חיבור שנכשל מה-backend: endpoints, פורט, פרוטוקול או pods שקורסים."),
   F("net-in-practice", "Your app logs show the node IP instead of the client IP behind a NodePort Service. What setting changes that?",
     ("`externalTrafficPolicy: Local` on the Service", "נכון. עם Cluster (ברירת המחדל) הבקשה יכולה לעבור ל-node אחר ועוברת SNAT. עם Local היא נשארת על ה-node שקיבל אותה, וה-IP נשמר."),
     ("`sessionAffinity: ClientIP` on the Service", "sessionAffinity שולח לקוח לאותו pod, אבל לא מונע SNAT. האפליקציה עדיין תראה את ה-IP של ה-node."),
     ("`clusterIP: None` to make the Service headless", "headless מבטל את ה-ClusterIP ולא משפיע על NodePort ועל SNAT. הבעיה היא המעבר בין nodes."),
     ("`type: ExternalName` pointing at the app's host", "ExternalName מחזיר CNAME לשם חיצוני ולא מקבל תנועה בכלל. הוא לא קשור לשמירת ה-IP."),
     x="עם Cluster (ברירת המחדל) הבקשה יכולה לעבור ל-node אחר ועוברת SNAT. עם Local היא נשארת על ה-node שקיבל אותה, וה-IP של הלקוח נשמר."),
 ],
}
