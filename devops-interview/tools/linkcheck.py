#!/usr/bin/env python3
"""linkcheck.py <docsrc_dir> [--out report.json]: check every doc link in the bank (q.r) and interview mode
against the docs' own source repos, since the docs hosts are blocked from cloud sessions.

Clone the sources first (shallow, sparse: git clone --depth 1 --filter=blob:none --sparse, then
git sparse-checkout set <dirs>) into <docsrc_dir>:
  k8s       kubernetes/website            content/en/docs static
  argo-cd   argoproj/argo-cd              docs
  helm      helm/helm-www                 docs versioned_docs   (+ netlify.toml for redirects)
  tf        hashicorp/web-unified-docs    content/terraform/<latest> content/terraform-docs-common
  ghdocs    github/docs                   content
  docker    docker/docs                   content data          (+ _vendor for the Dockerfile reference)
  gitlab    gitlab.com/gitlab-org/gitlab  doc
  runner    gitlab.com/gitlab-org/gitlab-runner  docs
  jenkins   jenkinsci/jenkins.io          content/doc
  eks       awsdocs/amazon-eks-user-guide latest
  mdn       mdn/content                   files/en-us/web files/en-us/glossary (+ files/en-us/_redirects.txt)

Statuses, per page:
  OK         a source file exists (and the #fragment matches a heading, when there is one)
  ANCHOR     the page exists but the #fragment matches no heading in its source
  MOVED      the site's own redirect rules send it to another page (the report gives the new URL)
  MISSING    no file and no redirect
  GENERATED  built by the site from data, not a file (Jenkins step reference): exists, not checked
  ARCHIVE    an AWS page found in that guide's 2023 GitHub archive (awsdocs); NEWER? = not in it (newer page, or wrong)
  UNCHECKED  no source repo for that host
With --out, the report maps every URL as written to {status, new, used_by}; tools/reffix.py applies "new".
"""
import json, os, re, sys, glob, subprocess
from collections import Counter, defaultdict

SRC = sys.argv[1]
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))
S = lambda *p: os.path.join(SRC, *p)
html = open(os.path.join(HERE, "..", "index.html"), encoding="utf-8").read()
blob = lambda i: json.loads(re.search(r'<script id="' + i + r'" type="application/json">(.*?)</script>', html, re.S).group(1))
uses = defaultdict(list)                                  # url as written -> ["q12", "iv:ab12cd34", ...]
for n, q in enumerate(blob("data")["questions"]):
    uses[q["r"]].append("q%d" % n)
for it in blob("ivdata")["items"]:
    if it.get("r"):
        uses[it["r"]].append("iv:" + it["id"])

def read(p):
    try:
        return open(p, encoding="utf-8", errors="ignore").read()
    except OSError:
        return ""

def first(paths):
    return next((p for p in paths if os.path.isfile(p)), None)

def variants(base, rel, exts, index=("index", "_index")):
    rel = rel.strip("/")
    return [os.path.join(base, rel + e) for e in exts] + [os.path.join(base, rel, i + e) for i in index for e in exts]

# ---------- redirect tables, each from the site's own config ----------
def k8s_redirects():
    out = {}
    for l in read(S("k8s/static/_redirects.base")).splitlines():
        p = l.split()
        if len(p) >= 2 and p[0].startswith("/docs/") and "*" not in p[0] and ":" not in p[0]:
            out[p[0].rstrip("/") + "/"] = p[1]
    return out

def tf_redirects():
    t = read(S("tf/content/terraform-docs-common/redirects.jsonc"))
    pairs = re.findall(r'"source":\s*"([^"]+)",\s*"destination":\s*"([^"]+)"', t)
    return pairs                                           # sources may carry :slug patterns

def helm_redirects():
    return dict(re.findall(r'from\s*=\s*"([^"]+)"\s*\n\s*to\s*=\s*"([^"]+)"', read(S("helm/netlify.toml"))))

def mdn_redirects():
    out = {}
    for l in read(S("mdn/files/en-us/_redirects.txt")).splitlines():
        p = l.split("\t")
        if len(p) == 2:
            out[p[0].lower()] = p[1]
    return out

def frontmatter_redirects(root, key):
    """old address -> the file whose front matter lists it (redirect_from / aliases)"""
    out = {}
    r = subprocess.run(["grep", "-rnE", "--include=*.md", r"^\s*-\s*/\S+\s*$", root], capture_output=True, text=True).stdout
    for l in r.splitlines():
        f, _, v = l.split(":", 2)
        out[v.strip().lstrip("- ").strip().rstrip("/").lower()] = f
    return out

# AWS archived its guides on GitHub in mid-2023 (awsdocs/<repo>, emptied, history kept). <docsrc>/aws/<repo>.pages
# lists the page ids of the last commit that still had doc_source/: a hit means the page existed then.
AWS_GUIDES = {"vpc/latest/userguide": "vpc", "AWSEC2/latest/UserGuide": "ec2", "AmazonS3/latest/userguide": "s3",
              "IAM/latest/UserGuide": "iam", "AmazonCloudWatch/latest/monitoring": "cw", "AmazonECR/latest/userguide": "ecr",
              "Route53/latest/DeveloperGuide": "r53", "autoscaling/ec2/userguide": "asg", "kms/latest/developerguide": "kms",
              "secretsmanager/latest/userguide": "sm", "awscloudtrail/latest/userguide": "ct", "AmazonCloudWatch/latest/logs": "logs"}
K8S, TF, HELM, MDN = k8s_redirects(), tf_redirects(), helm_redirects(), mdn_redirects()
GH = frontmatter_redirects(S("ghdocs/content"), "redirect_from")
DOCKER = frontmatter_redirects(S("docker/content"), "aliases")

def tf_target(path):
    for src, dst in TF:
        if ":" not in src:
            if src.rstrip("/") == path.rstrip("/"):
                return dst
        else:
            head = src.split(":")[0]
            if path.startswith(head) and "null_resource" not in path:
                return re.sub(r":slug\*?", path[len(head):], dst)
    return None

# ---------- headings, to check #fragments ----------
def slug(t):
    t = re.sub(r"\{#[^}]+\}", "", t)
    t = re.sub(r"<[^>]+>|`|\*\*?|\[([^\]]*)\]\([^)]*\)", r"\1", t).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return re.sub(r" ", "-", t)

def anchors(f):
    t = read(f)
    ids = set(re.findall(r"\{#([\w\-.]+)\}", t)) | set(re.findall(r"^\[#([\w\-.]+)[,\]]", t, re.M))
    ids |= set(re.findall(r'(?:id|name)="([\w\-.]+)"', t))
    # HashiCorp's site also anchors option lists: "- `-out=FILENAME`" becomes #out-filename
    for o in re.findall(r"^\s*[-*]\s+`([^`]+)`", t, re.M):
        ids.add(re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", o.lower())).strip("-"))
    for h in re.findall(r"^#{1,6}\s+(.+?)\s*#*$", t, re.M) + re.findall(r"^={1,6}\s+(.+)$", t, re.M):
        hugo = re.sub(r"[^\w]+", "-", re.sub(r"\{#[^}]+\}|`", "", h).strip().lower())   # Hugo: "Container's" -> container-s
        for x in (slug(h), slug(h).replace("_", "-"), hugo):
            ids.add(x); ids.add(x.strip("-"))
    return ids

def page_file(host, path):
    """the source file for a page, or ('MOVED', new url), or None"""
    if host == "kubernetes.io" and path.startswith("/docs/"):
        f = first(variants(S("k8s/content/en/docs"), path[6:], [".md", ".html"]))
        if f: return f
        t = K8S.get(path.rstrip("/") + "/")
        return ("MOVED", "https://kubernetes.io" + t) if t else None
    if host == "argo-cd.readthedocs.io":
        return first(variants(S("argo-cd/docs"), re.sub(r"^/en/[^/]+/", "", path), [".md"]))
    if host == "helm.sh" and path.startswith("/docs/"):
        rel = path[6:]
        f = first(variants(S("helm/docs"), rel, [".md", ".mdx"]))
        if not f and rel.startswith("v3/"):
            f = first(variants(S("helm/versioned_docs/version-3"), rel[3:], [".md", ".mdx"]))
        if f: return f
        t = HELM.get(path.rstrip("/")) or HELM.get(path)
        return ("MOVED", "https://helm.sh" + t.rstrip("/") + "/") if t else None
    if host == "developer.hashicorp.com" and path.startswith("/terraform/tutorials/"):
        return "unchecked"                                 # tutorials are not in web-unified-docs
    if host == "developer.hashicorp.com" and path.startswith("/terraform/"):
        rel = path[len("/terraform/"):]
        if rel.startswith("cloud-docs"):
            f = first(variants(S("tf/content/terraform-docs-common/docs"), rel, [".mdx", ".md"]))
        else:
            f = None
            for v in sorted(glob.glob(S("tf/content/terraform/v*")), key=lambda x: [int(n) for n in re.findall(r"\d+", x)], reverse=True)[:1]:
                f = first(variants(os.path.join(v, "docs"), rel, [".mdx", ".md"]))
        if f: return f
        t = tf_target(path)
        return ("MOVED", "https://developer.hashicorp.com" + t) if t else None
    if host == "docs.github.com":
        rel = re.sub(r"^/en/", "", path)
        f = first(variants(S("ghdocs/content"), rel, [".md"]))
        if f: return f
        t = GH.get("/" + rel.strip("/").lower())
        if t:
            new = os.path.relpath(t, S("ghdocs/content"))
            new = re.sub(r"(/index)?\.md$", "", new)
            return ("MOVED", "https://docs.github.com/en/" + new)
        return None
    if host == "docs.docker.com":
        rel = path.strip("/")
        if rel == "reference/dockerfile":
            return first(glob.glob(S("docker/_vendor/github.com/moby/buildkit/frontend/dockerfile/docs/reference.md"))) or "vendored"
        m = re.match(r"reference/cli/(docker/.+)", rel)
        if m:
            name = m.group(1).replace("/", "_") + ".yaml"
            hit = glob.glob(S("docker/data/cli/*/" + name))
            return hit[0] if hit else None
        f = first(variants(S("docker/content/manuals"), rel, [".md"]) + variants(S("docker/content"), rel, [".md"]))
        if f: return f
        t = DOCKER.get(path.rstrip("/").lower())
        if t:
            new = os.path.relpath(t, S("docker/content")).replace("manuals/", "", 1)
            return ("MOVED", "https://docs.docker.com/" + re.sub(r"(/_?index)?\.md$", "", new) + "/")
        return None
    if host == "docs.gitlab.com":
        rel = re.sub(r"\.html$", "", re.sub(r"^/ee/", "/", path)).strip("/")
        if rel.startswith("runner"):
            return first(variants(S("runner/docs"), rel[6:] or "_index", [".md"]))
        f = first(variants(S("gitlab/doc"), rel, [".md"]))
        if f and "This document was moved" in read(f)[:1500]:
            m = re.search(r"\]\(([^)]+)\.md\)", read(f))
            return ("MOVED", "https://docs.gitlab.com/" + os.path.normpath(os.path.join(os.path.dirname(rel), m.group(1))) + "/") if m else None
        return f
    if host == "www.jenkins.io" and path.startswith("/doc/"):
        if path.startswith("/doc/pipeline/steps/"):
            return "generated"
        return first(variants(S("jenkins/content/doc"), path[5:], [".adoc", ".html.haml", ".md"]))
    if host == "docs.aws.amazon.com" and path.startswith("/eks/latest/userguide/"):
        pid = re.sub(r"\.html$", "", path.rsplit("/", 1)[1])
        hit = subprocess.run(["grep", "-rlE", r"^\[#" + re.escape(pid) + r"(,|\])", S("eks/latest")], capture_output=True, text=True).stdout.split()
        return hit[0] if hit else None
    if host == "docs.aws.amazon.com":
        guide = "/".join(path.split("/")[1:4])
        repo = AWS_GUIDES.get(guide)
        if repo and os.path.isfile(S("aws", repo + ".pages")):
            pid = re.sub(r"\.html$", "", path.rsplit("/", 1)[1])
            return "archive" if pid in set(read(S("aws", repo + ".pages")).split()) else "not-in-archive"
        return "unchecked"
    if host == "developer.mozilla.org":
        rel = re.sub(r"^/en-US/docs/", "", path).lower()
        f = first([S("mdn/files/en-us", rel, "index.md")])
        if f: return f
        t = MDN.get(path.rstrip("/").lower())
        while t and MDN.get(t.lower()):
            t = MDN[t.lower()]
        return ("MOVED", "https://developer.mozilla.org" + t) if t else None
    return "unchecked"

res = {}
for url in sorted(uses):
    m = re.match(r"https?://([^/]+)(/[^?#]*)(?:#(.*))?", url)
    host, path, frag = m.group(1), m.group(2), m.group(3)
    f = page_file(host, path)
    new = ""
    if f == "unchecked": st = "UNCHECKED"
    elif f == "archive": st = "ARCHIVE"
    elif f == "not-in-archive": st = "NEWER?"
    elif f == "generated": st = "GENERATED"
    elif f is None: st = "MISSING"
    elif isinstance(f, tuple):
        st, new = "MOVED", f[1]
        nm = re.match(r"https?://([^/]+)(/[^?#]*)", new)
        g = page_file(nm.group(1), nm.group(2))
        if isinstance(g, str) and os.path.isfile(g) and frag and frag.lower() in {a.lower() for a in anchors(g)}:
            new += "#" + frag                               # the fragment still lands on the new page
    elif frag and os.path.isfile(f) and not f.endswith(".yaml") and frag.lower() not in {a.lower() for a in anchors(f)}:
        st, new = "ANCHOR", url.split("#")[0]
    else: st = "OK"
    res[url] = {"status": st, "new": new, "used_by": uses[url]}

c = Counter(r["status"] for r in res.values())
pages = {u.split("#")[0] for u in res}
print("urls:", len(res), "pages:", len(pages), dict(c))
for url, r in res.items():
    if r["status"] not in ("OK", "UNCHECKED", "GENERATED", "ARCHIVE"):
        print("%-8s %s%s  <- %s" % (r["status"], url, ("\n         -> " + r["new"]) if r["new"] else "",
                                     ", ".join(r["used_by"][:5]) + (" …" if len(r["used_by"]) > 5 else "")))
if OUT:
    json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False)
