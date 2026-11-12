# weather-app on EKS: project facts for question writing

A digest of the project's own handbook (its CLAUDE.md, state of 2026-11-12), kept here because that file is
not in this repository. It is the source for project exams 2-5, a Learn subject and interview questions.

**This repository and the site are public.** Never add: the AWS account id, resource ids (instances, AMIs,
volumes, security groups, VPC), public IP addresses, the domain, mail addresses, user names, token values, or
security gaps that are still open on the live system. `build_project.py` and `tools/contentlint.py` refuse the
mechanical ones; the rest is on the author. Private addresses, tool versions and design facts are fine.

Exam 1 (`p1.py`) covers: access through SSM, the two ALBs, environments and Git Flow, the three repositories,
GitOps basics, Terraform modules / staged apply / the Helm handover, the daily cycle in outline, Buildah, the
chart and Prometheus traps, cost and capacity. Do not repeat its stems.

## Exam 2: the daily cycle and Terraform in depth

- **Two generations of the cycle.** Until 2026-11-11: `state rm` every evening and `import` every morning for what
  must survive. Since the Terragrunt migration (2026-11-12): those resources are the `persistent` unit with its own
  state, excluded from destroy; no daily import. The in-cluster unit is still `state rm`'d (the cluster dies under it).
  Write questions about the old mechanism in the past tense.

- Morning script stages: preflight (tools, AMIs present, adds the current public IP) -> VPC -> EKS, EC2, IAM ->
  SSM tunnel -> imports (ECR, data/Vault disks, LGTM buckets, Vault KMS key, alias, snapshot bucket) and an image
  build only if the image is missing -> in-cluster resources and the load balancer controller -> ArgoCD bootstrap
  -> Jenkins sync -> wait for the cluster ALB -> DNS -> status report. About 17-21 minutes, unattended.
- Evening script steps: bake AMIs (abort on failure) -> destroy the WAF association on the controller's ALB ->
  scale ArgoCD controllers to 0, save prod's last synced revision, Vault raft snapshot to S3, scale DB StatefulSets
  to 0 -> delete Gateways/Ingresses so the controller removes its ALB -> API fallback cleanup -> `state rm` what
  must survive -> destroy -> check for leftovers (PVC volumes, ALBs).
- Why ArgoCD is scaled down first: otherwise auto-synced apps recreate the routes while they are being deleted and
  the controller rebuilds an ALB that then blocks the VPC destroy (seen once: a half-destroyed VPC and a stale
  state lock that needed `terraform force-unlock`).
- The ALB built by the controller is unknown to Terraform. The WAF association on it lives in a root file that
  the scripts rename between `.tf` and `.tf.bak` around that ALB's lifetime (in git it is always `.bak`).
  An older design used a boolean variable `k8s_alb_ready`; it no longer exists.
- Imports sit after the cluster and tunnel exist, because `terraform import` configures every provider, and the
  kubernetes/helm providers need the cluster ("Invalid provider configuration" when it ran too early).
- An IAM policy that references the kept buckets must not be applied before the buckets are imported
  (`BucketAlreadyOwnedByYou` when stage 2 tried to create them).
- `for_each` over values unknown until apply fails (`Invalid for_each argument`): PV/PVC keys came from volume
  ids that exist only after import; fixed with static keys `toset(["pg", "mongo"])`.
- Never `random_password` for DB passwords: the in-cluster module leaves the state nightly, a new value would
  lock the app out of the kept volumes. DB init scripts run only on an empty volume, so a password change also
  needs `ALTER ROLE` / `db.updateUser`.
- Terraform-only attributes show as one in-place change after an import (`force_delete` on ECR,
  `deletion_window_in_days` on the KMS key): expected, no AWS call.
- `terraform state list | grep -q x` under `set -o pipefail` fails at random with 141: grep exits early and
  terraform gets SIGPIPE. Fixed with `grep -x ... >/dev/null`. Likewise a `kubectl ... | while` pipeline died when
  the tunnel reconnected; now `{ ... || true; }`.
- State is in S3 with `use_lockfile` (no DynamoDB); a copy of tfvars is synced to the bucket. The bucket is
  versioned, so old state versions kept old secret values until they were rotated.
- Golden AMIs: newest 3 per server kept; their ids are written into tfvars by the bake script. The GitLab
  runner has `ignore_changes = [ami, user_data]`; its user_data waits for the instance profile.
- 2 nodes since the network-security work; the module ignores `desired_size` after creation.
- EKS identity lesson: a plan run by the pipeline role would have moved cluster-admin from the laptop identity
  to the pipeline role (`enable_cluster_creator_admin_permissions`, default KMS key admins). Now disabled, with an
  explicit access entry and `kms_key_administrators`; the policy protects access entries.
- Terraform CI/CD (GitLab CI, not Jenkins): runner on its own EC2 (t3.medium: a plan peaks at 1.3 GB), GitLab
  OIDC -> role `weather-tf-plan` (any branch, read-only) and `weather-tf-apply` (only `main`), conftest policy gate
  (`plan.rego`, protected resources), manual Apply. The OIDC provider needs a pinned thumbprint (IAM would
  otherwise reach GitLab before its DNS exists). The WAF needed an allow rule for the two OIDC paths (requests
  without a User-Agent were blocked).
- Module reorg: `persistent` (ECR, the pg/mongo/vault disks, LGTM buckets, Vault key/alias/bucket; all
  `prevent_destroy`), `k8s-alb` (the WAF association), LBC `helm_release` in `kubernetes`; done with `moved`
  blocks: plan showed 13 moved, 0 add / 0 change / 0 destroy.
- Terragrunt 1.2.1 migration: six units (vpc, persistent, cicd, infrastructure, kubernetes, k8s-alb) under a
  `root.hcl` (inputs from tfvars, remote state key per unit, generated providers, lock timeout, retry on TLS
  handshake timeout). `exclude` on destroy for persistent, kubernetes, k8s-alb. `run --all plan` = no changes in
  all six after splitting the real state. A before_hook checks `kubectl get --raw /readyz` before plan/apply.
  Terragrunt 1.x always runs in `.terragrunt-cache`, so a generated backend exists only in the copy.
  First full morning and evening on Terragrunt passed (about 21 and 20 minutes).
- Prod morning sync: the evening saves prod's last synced chart revision; the morning syncs prod to exactly that
  revision (never HEAD), after waiting for the monitoring CRDs and for prod's Secrets from Vault.

## Exam 3: CI/CD, DevSecOps and GitOps in depth

- Jenkinsfile stages: build and test (pytest), lint (pylint threshold), gitleaks, Trivy fs/config/image with a
  CRITICAL threshold, hadolint, SAST (Semgrep + Bandit) only on the way to `main`, Buildah build, cosign sign,
  Kyverno CLI check of the rendered chart, commit of `image.tag` to the chart repo.
- cosign v3 key pair in Jenkins credentials; signing flags turn off the new bundle format and the transparency
  log upload because Kyverno 1.19 rejected the v3 bundle in the lab.
- Kyverno: `ImageValidatingPolicy` (signature) and `ValidatingPolicy` (image rules: only the project registry,
  no `latest`, memory limit); ClusterPolicy is deprecated since 1.18. Deny only after all three environments ran
  signed images. `kubectl run` is refused by Pod Security before Kyverno sees it. With a label selector the
  Kyverno CLI prints `pass: 0` and checks nothing unless `--values-file` supplies namespace labels.
- A new CRITICAL can appear between builds with no code change (certifi, pillow, brotli): fixed by bumping or
  removing unused dependencies. The pipeline agent opened the issue and a Draft MR for one of them.
- A heredoc pasted into the Jenkinsfile broke line 1 (`WorkflowScript:1`). `feature/*` is protected, so demo
  branches are `demo/*`. The GitLab plugin skips Draft MRs. `Closes #N` acts only on the default branch.
- Health-check stage hang: `raise SystemExit` made gunicorn respawn forever; fixed by sending app output to a
  log file, killing gunicorn after the check and printing the log tail on failure.
- ApplicationSet (list generator, goTemplate with `missingkey=error`) owns dev and staging; prod stays a plain
  Application. It adopts existing same-name Applications. Without `preserveResourcesOnDeletion` deleting the
  ApplicationSet deleted a real Deployment (lab); a variable typo creates nothing.
- AppProject `weather`: sourceRepos = the chart repo, destinations = the three env namespaces by name (not
  `weather-*`, which would match the data namespace), empty clusterResourceWhitelist, Secret blacklisted,
  sync-wave -1. A ClusterRole or Secret in the app refuses the whole sync; `CreateNamespace=true` is blocked;
  deleting a used project is not blocked (apps go InvalidSpecError, pods keep running).
- Helm library chart `weather-lib` with one template for the five Services; `helm dependency build` in the
  pipeline before the Kyverno render; app MR merged before the chart MR.
- Argo Rollouts (prod only): replica-based canary, steps setWeight 33 -> pause -> analysis of the 5xx rate from
  Mimir (interval 1m, count 3, failureLimit 0). First Rollout goes straight to 100%. Without a NetworkPolicy to
  Mimir the analysis times out and aborts. `{{ "{{args.x}}" }}` escaping inside Helm.
- HPA 3-5 pods at 70% CPU on the Rollout; `ignoreDifferences` on `/spec/replicas` + RespectIgnoreDifferences so
  ArgoCD does not fight it. metrics-server addon on container port 4443 (the default port is closed in the node
  security group). VPA in recommend-only mode on PostgreSQL. `<unknown>` targets mean metrics-server is broken.
- Sync option names are exact: `ServerSideApply=true` (large CRDs fail client-side apply); a typo field in an
  Application is dropped by the API and leaves the parent OutOfSync.
- Gateway API on the ALB: GatewayClass + LoadBalancerConfiguration + Gateway + HTTPRoutes replace the Ingresses.
  The controller detects the Gateway CRDs only at start, so it needs one restart after ArgoCD installs them.
  CRD defaults make ArgoCD's client-side diff report drift: `ServerSideDiff=true`. Renaming the load balancer on
  a programmed Gateway does not replace the ALB (names are immutable); deleting the Gateway did.
- ExternalDNS (sources gateway-httproute, policy sync, TXT owner id) owns the site records since then; Terraform
  keeps only the WAF association. At night it deletes the records when the Gateway is deleted and recreates them
  in the morning. Its pod needed the role policy before start, or it ran with the node role (AccessDenied).
- Preview environments per MR (ApplicationSet pull-request generator, labels gate, Headlamp) are designed and
  lab-tested, not live. A role of `edit` was rejected for developers: it could create a route for the prod host
  on the shared ALB and delete NetworkPolicies.
- cert-manager internal CA (self-signed root -> CA issuer -> short-lived certificate) is written, not merged.
  Karpenter and Falco are designed and lab-tested, not built.

## Exam 4: security, data and secrets

- NetworkPolicy: default-deny ingress + same-namespace in the app namespaces; exceptions for the ALB subnets to
  the app port and for Prometheus/Alloy. ArgoCD's install ships an allow-all policy for its server, and policies
  add up, so the bootstrap deletes it each morning. kube-system and the mesh namespace are not isolated.
- The VPC CNI needs network policy explicitly enabled, or policies are silently ignored.
- WAF: IP reputation, known bad inputs, common rule set with the body-size rule set to count (git push, ArgoCD
  diffs), rate limit per IP. The controller runs with WAF management off so it never removes the association.
  A WAF body rule blocked saving a Jenkins job whose form contained an internal URL (workaround: port forward).
- Istio ambient: namespaces labelled for ambient; data namespace allows only HBONE (15008) from pods labelled
  `db-access`, egress DNS only; PeerAuthentication STRICT + AuthorizationPolicy allowing only the app's
  ServiceAccount of the three environments on the DB ports. In ambient, kubelet probes arrive from a link-local
  address: without allowing it, readiness fails (and it killed the Vault operator every minute once).
  In ambient a TCP connect always succeeds (ztunnel), so only a real reply proves connectivity.
- Data tier: one PostgreSQL, one MongoDB, one Redis in a shared namespace (Pod Security restricted). Per
  environment: database + owner in PostgreSQL, database + user in MongoDB, Redis ACL user limited to `<env>:*`
  and without dangerous commands; `default` Redis user off; a probe user that can only PING. All probes `exec`.
  Static PV/PVC (`storageClassName: ""`, Retain) on Terraform-owned EBS volumes in one AZ. Redis has no disk.
- The app starts and serves anonymous search with no database at all; production refuses to start without
  SECRET_KEY; login lockout after 5 failures / 15 minutes in Redis; scrypt hashes; CSRF protection.
- CPU budget: node allocatable 1930m, a Jenkins build pod requests 800m, DB requests were cut to 25m/50m/10m.
- Vault: Raft, one replica, awskms seal (auto-unseal) through IRSA limited to one key; injector/CSI/UI off;
  TLS off inside because the mesh encrypts; NetworkPolicy + mesh policy allow only the secrets operator.
  kv-v2, audit log to stdout (collected by Loki, tokens HMAC'd), Kubernetes auth with one role per namespace,
  policies per environment. Cross reads return 403; a dev ServiceAccount asking for the prod role gets
  `namespace not authorized`.
- Vault Secrets Operator: VaultAuth + VaultStaticSecret -> a normal Secret, `rolloutRestartTargets`, and
  `excludeRaw: true` (otherwise it adds `_raw` with every value again). `SkipDryRunOnMissingResource` because the
  CRs arrive with their CRD.
- Migration order per secret: write to Vault, compare hashes, `state rm` the Terraform secret, remove the code,
  let the operator own it. Root token revoked; recovery keys 3 of 5; emergency `vault operator generate-root`.
- Rotation: all values rotated because old state and tfvars versions still held them. For databases: change the
  DB first, then Vault. Lessons: never generate a secret with a command whose output enters a chat transcript;
  a `$var` inside double quotes was expanded by the outer shell and wrote an empty token (the service then
  accepted an empty bearer token); the service now refuses short or empty tokens.
- Grafana lockout: a new admin password with an old Grafana DB locks the admin for 5 minutes after the sidecars
  fail to log in.

## Exam 5: observability, agents and incidents

- LGTM replaces Prometheus (Alertmanager stays): Mimir monolithic, Loki and Tempo monolithic, one Alloy
  Deployment, buckets kept overnight. Trimmed to a minimum at the owner's request (no Tempo metrics generator,
  no Loki ruler). `#` comments inside Alloy's config would have broken it (`//`, checked with `alloy fmt`).
- OpenTelemetry in the app: traces to Tempo (spans for the request, the external API call, Redis), log lines
  carry `trace_id` (`inject_trace_context=True`). Images are distroless: check with `kubectl port-forward`.
- The ServiceMonitor story: missing three mornings; real cause = ArgoCD's controller caches the API list from
  start; fix = wait for the CRD and restart the controller once, hard-refresh and retry the prod sync.
- The NetworkPolicy for Alloy must exist before Alloy, or Mimir fires a real "app down" alert.
- Alerts: VaultNotReady, VaultSecretsOperatorDown, app down; Slack route unchanged, first route to the k8s agent
  with `continue: true`.
- Pipeline agent (n8n): Jenkinsfile `post { failure }` -> webhook -> pull the log -> LLM (an open model through a
  cloud API, not Claude; no structured outputs, so a tool call with a JSON fallback and a `Check proposal` node as
  the control) -> Draft MR from `agent/fix-<job>-<build>` + mail. Token: Developer + api; protected branches;
  `agent/*` never protected; Jenkins user with read-only matrix permissions. It skips `agent/*` branches.
- k8s agent: triage rules (transient vs real), MCP tool server with 7 read-only tools, an LLM tool loop, mail;
  webhook from Alertmanager + sweep every 5 minutes with one worker. IAM role describe-only, EKS access entry ->
  read ClusterRole without secrets/configmaps; IMDS hop limit 1 so the n8n container cannot use the role.
  It waits until the cluster is 30 minutes old before sweeping (morning noise).
- Orchestrator: one incident per resource key (`ci:JOB/BRANCH`, `k8s:NS/WORKLOAD`); new -> issue + one mail;
  open and last mail < 30 min -> comment only; worse severity -> mail again; closed issue -> new issue. State file
  + decision log; lost state -> search GitLab for the `incident-key:` line. GitLab token Reporter. Quick actions
  and @mentions in untrusted text are neutralised; a forged result is refused.
- Honest limits said in the project's own defense notes: single replica services, one region, training budget.
- Incidents worth telling: the wrong EBS CSI diagnosis; the ServiceMonitor mornings; the destroy that stopped
  half way; the empty token; the runner that never started (missing directory in user_data, then missing
  credentials before the instance profile attached).
- Working method: explain why and name the rejected alternative; three QA passes over any guide; verify before
  asserting; say plainly when a diagnosis was wrong.
