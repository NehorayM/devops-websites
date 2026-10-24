# -*- coding: utf-8 -*-
"""The shape of a Ship It question, and the syllabus every question is filed under.

Questions are authored in qsrc/<topic>.py as calls to Q(). The correct option is always
written first; build_bank.py moves it to a balanced position, so an author never has to
think about letters and the answer key can never drift from the option it describes.

    Q("k8s-pods", JM, T,
      "A pod is in CrashLoopBackOff ... What do you check first?",
      ("kubectl logs <pod> --previous", "why it is right, in Hebrew"),
      ("...", "why it is wrong, in Hebrew"),
      ("...", "..."),
      ("...", "..."),
      tip="how to say it in an interview, in Hebrew",
      ref="https://kubernetes.io/docs/...")
"""

JM, MS = 0, 1          # level: Junior–Mid, Mid–Senior
T, K = "t", "k"        # kind: troubleshooting, knowledge

# The nine interview topics and the weight Nehoray gave each (1–10). The question counts
# are the weights scaled to 1,300; LV0 is how many of them are Junior–Mid, chosen so the
# two levels come to exactly 650 each — papers 1–10 and 11–20.
TOPICS = [
    # key,        name,                                  weight, count, lv0
    ("k8s",       "Kubernetes",                              10, 265, 132),
    ("argocd",    "ArgoCD",                                   8, 212, 106),
    ("ci",        "CI: security, testing, building",          7, 186,  93),
    ("aws",       "AWS",                                      6, 159,  79),
    ("helm",      "Helm",                                     5, 133,  66),
    ("terraform", "Terraform",                                5, 133,  67),
    ("linux",     "Linux",                                    3,  80,  40),
    ("cicd",      "Jenkins, GitLab CI & GitHub Actions",      3,  79,  40),
    ("net",       "Networking",                               2,  53,  27),
]

# The 24 subjects. Their order is the section index the page stores (q.s), so append
# rather than reorder once anyone has progress.
#   slug,              topic,      full name,                                       short,               count
SECTIONS = [
    ("k8s-pods",       "k8s",      "Kubernetes: Pods & Workloads",                  "K8s workloads",       49),
    ("k8s-net",        "k8s",      "Kubernetes: Services, Ingress & Networking",    "K8s networking",      46),
    ("k8s-config",     "k8s",      "Kubernetes: Config, Secrets & Storage",         "K8s config & storage",44),
    ("k8s-sched",      "k8s",      "Kubernetes: Scheduling, Resources & Autoscaling","K8s scheduling",     44),
    ("k8s-sec",        "k8s",      "Kubernetes: RBAC & Security",                   "K8s security",        41),
    ("k8s-debug",      "k8s",      "Kubernetes: Troubleshooting & Observability",   "K8s troubleshooting", 41),
    ("argo-core",      "argocd",   "ArgoCD: Core Concepts & Applications",          "ArgoCD core",         53),
    ("argo-sync",      "argocd",   "ArgoCD: Sync, Health, Hooks & Waves",           "ArgoCD sync",         51),
    ("argo-scale",     "argocd",   "ArgoCD: ApplicationSets & Multi-cluster",       "ArgoCD at scale",     52),
    ("argo-ops",       "argocd",   "ArgoCD: RBAC, SSO, Secrets & Operations",       "ArgoCD ops",          56),
    ("ci-docker",      "ci",       "CI: Docker Image Builds",                       "Docker builds",       47),
    ("ci-sec",         "ci",       "CI: DevSecOps",                                 "DevSecOps",           47),
    ("ci-test",        "ci",       "CI: Testing in the Pipeline",                   "Pipeline testing",    46),
    ("ci-deploy",      "ci",       "CI: Pipeline Design & Deployment Strategies",   "Deploy strategies",   46),
    ("aws-eks",        "aws",      "AWS: EKS & IAM",                                "EKS & IAM",           53),
    ("aws-net",        "aws",      "AWS: VPC, Compute & DNS",                       "VPC & compute",       53),
    ("aws-ops",        "aws",      "AWS: Storage, Secrets & Observability",         "S3, secrets, CW",     53),
    ("helm-charts",    "helm",     "Helm: Charts & Templating",                     "Helm charts",         67),
    ("helm-ops",       "helm",     "Helm: Releases, Upgrades & Troubleshooting",    "Helm releases",       66),
    ("tf-core",        "terraform","Terraform: Core Workflow, Providers & Modules", "Terraform core",      67),
    ("tf-state",       "terraform","Terraform: State, Drift & Team Workflows",      "Terraform state",     66),
    ("linux",          "linux",    "Linux",                                         "Linux",               80),
    ("net",            "net",      "Networking",                                    "Networking",          53),
    ("cicd-tools",     "cicd",     "Jenkins, GitLab CI & GitHub Actions",           "CI tools",            79),
]
SEC_INDEX = {s[0]: i for i, s in enumerate(SECTIONS)}

# Answers are checked against documentation, and every question says which page.
REF_HOSTS = (
    "kubernetes.io", "argo-cd.readthedocs.io", "argoproj.github.io", "helm.sh",
    "developer.hashicorp.com", "docs.aws.amazon.com", "aws.amazon.com", "docs.docker.com",
    "docs.github.com", "docs.gitlab.com", "www.jenkins.io", "jenkins.io", "man7.org",
    "www.kernel.org", "docs.kernel.org", "www.rfc-editor.org", "datatracker.ietf.org",
    "owasp.org", "slsa.dev", "docs.sigstore.dev", "aquasecurity.github.io", "trivy.dev",
    "martinfowler.com", "prometheus.io", "opentelemetry.io", "kustomize.io",
    "github.com", "www.gnu.org", "systemd.io", "www.freedesktop.org", "docs.sonarsource.com",
    "external-secrets.io", "cert-manager.io", "karpenter.sh", "kubernetes-sigs.github.io",
    "argoproj.github.io", "www.terraform.io", "coredns.io", "kubernetes.github.io", "keda.sh", "kyverno.io", "falco.org", "etcd.io", "sre.google", "opengitops.dev", "fluxcd.io", "argocd-image-updater.readthedocs.io", "kubectl.docs.kubernetes.io", "docs.kargo.io", "argocd-agent.readthedocs.io", "argocd-vault-plugin.readthedocs.io", "nginx.org", "git-scm.com", "semver.org",
    "cheatsheetseries.owasp.org", "cloud.google.com", "learn.microsoft.com", "en.wikipedia.org",
)


class Question:
    __slots__ = ("sec", "lv", "kind", "q", "opts", "tip", "ref", "src")

    def __init__(self, sec, lv, kind, q, opts, tip, ref, src):
        self.sec, self.lv, self.kind, self.q = sec, lv, kind, q
        self.opts, self.tip, self.ref, self.src = opts, tip, ref, src


def Q(sec, lv, kind, q, right, *wrong, tip="", ref=""):
    """One multiple-choice question. `right` and each of `wrong` are (option, why)."""
    import inspect
    fr = inspect.stack()[1]
    src = "%s:%d" % (fr.filename.rsplit("/", 1)[-1], fr.lineno)
    return Question(sec, lv, kind, q, [right] + list(wrong), tip, ref, src)
