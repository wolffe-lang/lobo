#!/usr/bin/env python3
"""ci/tiers-test.py — the planner's own proof (tl28; wolf-lang's
ci/tiers-test.py, tl21, cut to lobo). python3, git and bash only.

    ci/tiers-test.py

  T1  the tiers by event: a trunk push, the nightly, a dispatch (tier full,
      or no tier) and the `full-matrix` label are full on every host;
      another label's `labeled` event is a noop; a dispatch's tier must be
      full or pr.
  T2  the pull-request tiers by path: each path names the jobs THIS
      repository's block below says, on the pull request's hosts; prose
      alone is noop; prose beside code is that code's tier.
  T3  full wins: a path no rule names, alone or beside anything; changed
      paths that cannot be read; a change that names no path; a dispatched
      branch the same.
  T4  the wiring of .github/workflows/ci.yml: the plan is first and the
      verdict last but the nightly's issue; every job needs the plan, runs
      only when the plan names it and takes its hosts from the plan; every
      plan output is read with a default; the `tier` job needs every job,
      runs on `!cancelled()` and checks with `ci/tiers.py verdict`;
      cancel-in-progress is for pull requests only and every other run has a
      concurrency group of its own run id; the trunk push (and no other
      branch's), the nightly, the label and the dispatch's `tier` input are
      there; the full tier's hosts are the ones the jobs ran on before tl28.
  T5  the tripwire: no line of this repository's code that reads a file
      names a path the planner calls prose (THIS repository's block). The
      search is shown to fire on paths it must find. (A WARN, not a
      failure: a tracked path no rule names; its pull request runs full.)
  T6  the verdict: green for a full, a pr and a noop run; red for a chosen
      job failed, skipped or cancelled, a job that ran unasked, a failed
      plan, a plan with no tier, a full run that chose less, a full run on
      the pull request's hosts, and green when GitHub drops an output that
      would have been empty.
  T7  the change read from git: a real merge commit against its first
      parent, with the base moved on meanwhile; red-to-full when HEAD is no
      merge or its second parent is not the pull request's head; a
      dispatched branch against its merge base with origin/trunk, and full
      when there is no origin/trunk to read.
  T8  ci/nightly-red.sh against a stand-in `gh`: no open issue opens one,
      labelled, under the one title; an open one gets a comment and no new
      issue; a label that already exists is no failure.
  T13 a trunk push's macOS legs already green at its commit, against a
      stand-in API and a scratch git repository: a completed, successful pull
      request or dispatch run at the commit, whose plan tested the same tree
      and has the leg once, green, on macOS, lets the push leave it, and the
      plan names the run; anything less runs it: another event, another tree,
      no tree, a missing, duplicate, cancelled or Linux job, a short listing,
      an error, a timeout, a redirect, no token, another commit. Only the
      runner's own push to trunk asks (a labelled pull request's run hands
      its plan EVENT=push). The verdict accepts exactly the covered legs and
      names their runs; the wiring gives the plan its tree step, the runs to
      read and the token, and no job-level permission.

Exit 0 when every check passes, 1 otherwise.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, "ci", "tiers.py")
RED = os.path.join(ROOT, "ci", "nightly-red.sh")
ENV_KEYS = ("EVENT", "ACTION", "LABEL", "LABELS", "HEAD_SHA", "IN_TIER", "NEEDS")
fails = 0


def say(ok, what):
    global fails
    print("tiers-test: %s %s" % ("PASS" if ok else "FAIL", what))
    fails += not ok


# --- this repository's -------------------------------------------------------------
NIGHTLY = None            # (its tier, its jobs); None: the full tier
FULL_LEG_TIERS = ("full",)  # the tiers that run every leg
WORKFLOW_FILE = "ci.yml"
WORKFLOW_NAME = "ci"
WORKFLOW_JOBS = ["plan", "gauntlet", "gauntlet-macos", "tier", "nightly-red"]
FULL_JOBS = ["gauntlet", "gauntlet-macos"]
PUSH_BRANCHES = "trunk"
OTHER_HOST_JOBS = ("gauntlet-macos",)
BEFORE_HOSTS = {}
ALL_HOSTS = {}
PR_HOSTS = {}
CODE_PATH = ("src/main.lu", ["gauntlet"])
PR_PATHS = [(p, ["gauntlet"]) for p in [
    "src/main.lu", "src/config/table.lu", "src/serve/serve.wolfi", "tests/config/user_directive.lu",
    "tests/differential/NGINX-PIN", "tools/lobo-gauntlet", "tools/lobo-dist", "tools/lib-toolchain.sh",
    "docs/metrics.md", "docs/log-variables.md", "docs/GETTING-STARTED.md", "docs/CONTROL.md", "conf/lobo.conf",
    "html/index.html", "demo/README.md", "wolf-toolchain.toml", "CHANGELOG.md", "README.md",
    ".github/workflows/ci.yml", ".github/workflows/release.yml", ".github/actions/acquire-toolchain/action.yml",
    "ci/tiers.py", "ci/tiers-test.py", "ci/nightly-red.sh", "LICENSE", "LICENSE-TRAINING-DATA", ".gitignore",
    ".gitattributes"]]
PROSE_PATHS = ["notes/ws66-evidence.md", "CLAUDE.md", "notes/ws67-contract.md", "notes/ws66-evidence/x.log"]
PR_UNIONS = []
READS = re.compile(r"\bopen\(|\.read\(|read_text|os\.path\.join|\bPath\(|"
                   r"\b(cat|source|cp|diff|cmp|grep|sed|awk|head|tail|wc|ls|find|read|mv|tar|for)\b|<\s*\S|^\s*\.\s+\S|\[\s+!?\s*-[efdrs]\s")


def is_code(f):
    """The code that could read a prose path: the tools and the tests."""
    return f.startswith(("tools/", "tests/")) and not f.endswith((".md", ".txt", ".json"))


MUST_FIND = ["docs/metrics.md", "CHANGELOG.md", "docs/GETTING-STARTED.md"]
RULED = {}  # {prose root: {regex of a line that names something else: why}}


def extra_t5(files, cls, say):
    code = [p for p in files if p.startswith(("src/", "tests/", "tools/", "docs/"))]
    say(len(code) >= 500 and all(cls.get(p) == "gauntlet" for p in code),
        "T5 every tracked path under src/, tests/, tools/ and docs/ is the linux gauntlet's (%d paths)" % len(code))


def extra_checks(say, plan, expect, blocks, wf):
    pr = dict(event="pull_request", action="synchronize")
    say(not [p for p, _ in PR_PATHS if "gauntlet-macos" in plan([p], **pr)["jobs"]], "T2 no pull-request path runs the macOS gauntlet")
    for leg in ("parity", "profile", "syscalls"):
        expect("T1 a dispatch with %s (a measurement)" % leg, plan(event="workflow_dispatch", flags=["--input", "measure=true"]), "measure", ["gauntlet"])
    expect("T1 a dispatch with no measurement leg", plan(event="workflow_dispatch", flags=["--input", "measure=false"]), "full", FULL_JOBS)
    expect("T1 measure means nothing to a pull request", plan(["src/main.lu"], flags=["--input", "measure=true"], **pr), "pr", ["gauntlet"])
    say("          IN_MEASURE: ${{ inputs.parity || inputs.profile || inputs.syscalls }}\n" in blocks["plan"],
        "T4 the plan reads the three measurement inputs")
    say(all(("        if: inputs.%s == true" % k) in wf or ("inputs.%s == true" % k) in wf for k in ("parity", "profile", "syscalls")),
        "T4 the linux job's own steps still choose the measurement over the gauntlet")
# T13: the macOS legs a trunk push may leave (name: runner label), as GitHub
# names them; T13_WHOLE, those that are whole jobs; T13_LINUX, other jobs a run has.
T13_REPO = "wolffe-lang/lobo"
T13_MAC = {"gauntlet-macos": "macos-latest"}
T13_WHOLE = ["gauntlet-macos"]
T13_LINUX = ["gauntlet"]


# --- end of this repository's ------------------------------------------------------
WORKFLOW = os.path.join(ROOT, ".github", "workflows", WORKFLOW_FILE)
NIGHTLY = NIGHTLY or ("full", FULL_JOBS)


def clean_env(**more):
    env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    env.update(more)
    return env


def plan(paths=None, **kw):
    args = [sys.executable, PLAN, "plan", "--json"]
    flags = kw.pop("flags", [])
    for k, v in kw.items():
        args += ["--" + k.replace("_", "-"), v]
    args += flags
    if paths is not None:
        args += ["--paths-from", "-"]
    r = subprocess.run(args, input="\n".join(paths or []) + "\n", capture_output=True, text=True, env=clean_env())
    if r.returncode != 0:
        return {"tier": "ERROR rc=%d %s" % (r.returncode, r.stderr.strip()[-200:]), "jobs": [], "matrix": {}}
    return json.loads(r.stdout)


wf = open(WORKFLOW, encoding="utf-8").read()
JOBS = re.findall(r"^  ([A-Za-z0-9_-]+):\s*$", wf[wf.index("\njobs:\n"):], re.M)
EVERY = [j for j in JOBS if j not in ("plan", "tier", "nightly-red")]


def expect(name, got, tier, jobs):
    why = []
    if got["tier"] != tier:
        why.append("tier %s, wanted %s" % (got["tier"], tier))
    if got["jobs"] != jobs:
        why.append("jobs %s, wanted %s" % (" ".join(got["jobs"]) or "none", " ".join(jobs) or "none"))
    hosts = ALL_HOSTS if tier in FULL_LEG_TIERS else PR_HOSTS
    if not got["tier"].startswith("ERROR") and got.get("matrix") != hosts:
        why.append("hosts %s, wanted %s" % (json.dumps(got.get("matrix")), json.dumps(hosts)))
    shown = "every job (%d), every host" % len(jobs) if tier == "full" else (" ".join(jobs) or "no job")
    shown += ", every host" if tier in FULL_LEG_TIERS and tier != "full" else ""
    say(not why, "%s: %s%s" % (name, tier, (" (" + "; ".join(why) + ")") if why else ", " + shown))


def in_order(jobs):
    return [j for j in EVERY if j in jobs]


# --- T1 the tiers by event ---------------------------------------------------
say(JOBS == WORKFLOW_JOBS, "T1 the workflow's jobs: %s" % " ".join(JOBS))
expect("T1 a push to trunk", plan(event="push"), "full", FULL_JOBS)
expect("T1 the nightly", plan(event="schedule"), NIGHTLY[0], NIGHTLY[1])
expect("T1 a dispatch, no tier", plan(event="workflow_dispatch"), "full", FULL_JOBS)
expect("T1 a dispatch, tier full", plan(event="workflow_dispatch", tier="full"), "full", FULL_JOBS)
say(plan(event="workflow_dispatch", tier="partial")["tier"].startswith("ERROR rc=2"), "T1 a dispatch's tier is full or pr, nothing else")
expect("T1 a pull request labelled full-matrix, prose only",
       plan([PROSE_PATHS[0]], event="pull_request", action="synchronize", labels="bug,full-matrix"), "full", FULL_JOBS)
expect("T1 the full-matrix label added",
       plan([PROSE_PATHS[0]], event="pull_request", action="labeled", label="full-matrix", labels="full-matrix"), "full", FULL_JOBS)
code, code_jobs = CODE_PATH
expect("T1 another label added", plan([code], event="pull_request", action="labeled", label="bug", labels="bug"), "noop", [])
expect("T1 another label added to a labelled pull request",
       plan([code], event="pull_request", action="labeled", label="bug", labels="bug,full-matrix"), "noop", [])
expect("T1 the tier input means nothing to a pull request",
       plan([code], event="pull_request", action="synchronize", tier="full"), "pr", in_order(code_jobs))

# --- T2 the pull-request tiers by path ------------------------------------------
pr = dict(event="pull_request", action="synchronize")
for p, jobs in PR_PATHS:
    expect("T2 %s" % p, plan([p], **pr), "pr", in_order(jobs))
for p in PROSE_PATHS:
    expect("T2 prose: %s" % p, plan([p], **pr), "noop", [])
expect("T2 prose alone, several", plan(PROSE_PATHS[:3], **pr), "noop", [])
expect("T2 prose beside code", plan([PROSE_PATHS[0], code, PROSE_PATHS[-1]], **pr), "pr", in_order(code_jobs))
for paths, jobs in PR_UNIONS:
    expect("T2 %s together" % " + ".join(paths), plan(paths, **pr), "pr", in_order(jobs))

# --- T3 full wins ---------------------------------------------------------------
expect("T3 a path no rule names", plan(["newplace/thing.rs"], **pr), "full", FULL_JOBS)
expect("T3 a new file at the root", plan(["build.rs"], **pr), "full", FULL_JOBS)
expect("T3 a markdown file at the root no rule names", plan(["NOTES.md"], **pr), "full", FULL_JOBS)
expect("T3 an unknown path beside prose", plan([PROSE_PATHS[0], "newplace/notes.md"], **pr), "full", FULL_JOBS)
expect("T3 an unknown path beside code", plan([code, "newplace/thing.rs"], **pr), "full", FULL_JOBS)
expect("T3 no changed paths to read", plan(**pr), "full", FULL_JOBS)
expect("T3 a change that names no path", plan([], **pr), "full", FULL_JOBS)
expect("T3 a merge that cannot be read (no repository there)",
       plan(repo=os.path.join(ROOT, "no", "such", "dir"), flags=["--merge"], **pr), "full", FULL_JOBS)
expect("T3 a dispatch, tier pr, an unknown path", plan(["newplace/thing.rs"], event="workflow_dispatch", tier="pr"), "full", FULL_JOBS)
expect("T3 a dispatch, tier pr, a branch that cannot be read",
       plan(repo=os.path.join(ROOT, "no", "such", "dir"), flags=["--merge"], event="workflow_dispatch", tier="pr"), "full", FULL_JOBS)
expect("T2 a dispatch, tier pr, code", plan([code], event="workflow_dispatch", tier="pr"), "pr", in_order(code_jobs))

# --- T6 the verdict -------------------------------------------------------------
def verdict(needs):
    r = subprocess.run([sys.executable, PLAN, "verdict"], capture_output=True, text=True, env=clean_env(NEEDS=json.dumps(needs)))
    return r.returncode, r.stdout + r.stderr


def run_of(tier, chosen, results=None, drop=(), hosts=None):
    outs = {"tier": tier, "jobs": json.dumps(chosen)}
    for k, v in (hosts if hosts is not None else (ALL_HOSTS if tier == "full" else PR_HOSTS)).items():
        outs[k] = json.dumps(v, separators=(",", ":"))
    for k in drop:  # GitHub leaves an empty output out of `needs`
        del outs[k]
    n = {"plan": {"result": "success", "outputs": outs}}
    for j in EVERY:
        n[j] = {"result": "success" if j in chosen else "skipped", "outputs": {}}
    n.update(results or {})
    return n


def vexpect(name, needs, want):
    rc, text = verdict(needs)
    say(rc == want, "T6 %s: exit %d%s" % (name, rc, "" if rc == want else " (wanted %d) %s" % (want, text.strip()[-300:])))


failed = {"result": "failure", "outputs": {}}
first, last = FULL_JOBS[0], FULL_JOBS[-1]
vexpect("a green full run", run_of("full", FULL_JOBS), 0)
vexpect("a green pr run", run_of("pr", in_order(code_jobs)), 0)
vexpect("a noop run", run_of("noop", []), 0)
vexpect("a noop run whose jobs output is absent", run_of("noop", [], drop=["jobs"]), 0)
vexpect("a chosen job failed", run_of("full", FULL_JOBS, {last: failed}), 1)
vexpect("a chosen job failed in a pr run", run_of("pr", in_order(code_jobs), {code_jobs[0]: failed}), 1)
vexpect("a chosen job was skipped", run_of("pr", in_order(code_jobs), {code_jobs[0]: {"result": "skipped", "outputs": {}}}), 1)
vexpect("a chosen job was cancelled", run_of("pr", in_order(code_jobs), {code_jobs[0]: {"result": "cancelled", "outputs": {}}}), 1)
vexpect("a job ran in a noop run", run_of("noop", [], {first: {"result": "success", "outputs": {}}}), 1)
vexpect("a full run whose jobs output is absent", run_of("full", FULL_JOBS, drop=["jobs"]), 1)
if len(FULL_JOBS) > 1:
    vexpect("a full run that chose less than every job", run_of("full", FULL_JOBS[:1]), 1)
    vexpect("a job ran unasked", run_of("pr", FULL_JOBS[:1], {FULL_JOBS[1]: {"result": "success", "outputs": {}}}), 1)
if ALL_HOSTS != PR_HOSTS:
    vexpect("a full run on the pull request's hosts", run_of("full", FULL_JOBS, hosts=PR_HOSTS), 1)
    vexpect("a pr run on every host", run_of("pr", in_order(code_jobs), hosts=ALL_HOSTS), 1)
    vexpect("a full run whose %s is absent" % sorted(ALL_HOSTS)[0], run_of("full", FULL_JOBS, drop=[sorted(ALL_HOSTS)[0]]), 1)
vexpect("a pr run that chose nothing", run_of("pr", []), 1)
vexpect("the plan failed", {"plan": {"result": "failure", "outputs": {}}, first: {"result": "skipped", "outputs": {}}}, 1)
vexpect("the plan named no tier", {"plan": {"result": "success", "outputs": {"jobs": "[]"}}, first: {"result": "skipped", "outputs": {}}}, 1)
vexpect("the plan named a tier that is none", run_of("fast", []), 1)
vexpect("the plan's jobs are no list", {"plan": {"result": "success", "outputs": {"tier": "pr", "jobs": first}}}, 1)
vexpect("a chosen job the tier job does not need", run_of("pr", [first, "lint"]), 1)

# --- T4 the wiring --------------------------------------------------------------
blocks = {}
for j in JOBS:
    m = re.search(r"^  %s:\s*\n(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)" % re.escape(j), wf, re.M | re.S)
    blocks[j] = m.group(1) if m else ""
say(JOBS[:1] == ["plan"] and JOBS[-2:] == ["tier", "nightly-red"], "T4 the plan is the first job, the tier the last but the nightly's issue")
for j in EVERY:
    b = blocks[j]
    nd = re.search(r"^    needs: (plan|\[plan(, [A-Za-z0-9_-]+)*\])$", b, re.M)
    ok = nd is not None
    ok = ok and ("    if: ${{ (github.event_name != 'pull_request' || contains(github.event.pull_request.labels.*.name, 'full-matrix') || contains(github.event.pull_request.labels.*.name, 'ci') || contains(github.event.pull_request.labels.*.name, 'release-matrix')) && (contains(fromJSON(needs.plan.outputs.jobs || '[]'), '%s')) }}\n" % j) in b
    say(ok, "T4 %s needs the plan and runs only when the plan names it" % j)
    out = "matrix_" + j.replace("-", "_")
    if out in ALL_HOSTS:
        say(("        include: ${{ fromJSON(needs.plan.outputs.%s || '[]') }}\n" % out) in b
            and "    runs-on: ${{ matrix.os }}\n" in b and not re.search(r"^        (os|include):\s*$|^        os: \[", b, re.M),
            "T4 %s takes its hosts from the plan" % j)
    else:
        say("matrix.os" not in b and re.search(r"^    runs-on: ubuntu-", b, re.M) is not None or j in OTHER_HOST_JOBS,
            "T4 %s has no matrix of hosts (%s)" % (j, (re.findall(r"^    runs-on: (.*)$", b, re.M) or ["?"])[0]))
reads = re.findall(r"needs\.plan\.outputs\.([a-z_]+)(\s*\|\|)?", wf)
say(len(reads) >= 3 and all(d for _, d in reads), "T4 every plan output is read with a default (%d reads: %s)" % (
    len(reads), " ".join(sorted(set(k for k, _ in reads)))))
say(all(("      %s: ${{ steps.plan.outputs.%s }}\n" % (k, k)) in blocks["plan"] for k in ["tier", "jobs"] + sorted(ALL_HOSTS)),
    "T4 the plan job declares tier, jobs and each matrix")
say('        run: python3 ci/tiers.py plan --merge --github-output "$GITHUB_OUTPUT"\n' in blocks["plan"]
    and "          fetch-depth: ${{ github.event_name == 'workflow_dispatch' && '0' || '2' }}\n" in blocks["plan"]
    and "HEAD_SHA: ${{ github.event.pull_request.head.sha }}" in blocks["plan"]
    and "IN_TIER: ${{ inputs.tier }}" in blocks["plan"],
    "T4 the plan reads the merge commit (depth 2) or a dispatch's branch (the history), and the tier input")
say("        run: python3 ci/tiers-test.py\n" in blocks["plan"]
    and blocks["plan"].index("ci/tiers-test.py") < blocks["plan"].index("ci/tiers.py plan"),
    "T4 the plan job runs this file before it plans")
t = blocks["tier"]
tn = re.findall(r"^      - ([A-Za-z0-9_-]+)\s*$", t, re.M)
say(sorted(tn) == sorted(["plan"] + EVERY), "T4 the tier job needs every job (%d of %d)" % (len(tn), len(EVERY) + 1))
ifs = re.findall(r"^    if: (.*)$", t, re.M)
say(ifs == ["${{ (github.event_name != 'pull_request' || contains(github.event.pull_request.labels.*.name, 'full-matrix') || contains(github.event.pull_request.labels.*.name, 'ci') || contains(github.event.pull_request.labels.*.name, 'release-matrix')) && (!cancelled()) }}"], "T4 the tier job runs on !cancelled(), never always() (%s)" % "; ".join(ifs))
say("    name: tier ${{ needs.plan.outputs.tier || 'unplanned' }}\n" in t, "T4 the tier job is named for the tier")
say("        run: python3 ci/tiers.py verdict\n" in t and "          NEEDS: ${{ toJSON(needs) }}\n" in t and "actions/checkout" in t,
    "T4 the tier job's check is ci/tiers.py verdict over toJSON(needs)")
n = blocks["nightly-red"]
say("    needs: tier\n" in n and "    if: ${{ failure() && github.event_name == 'schedule' }}\n" in n
    and "      issues: write\n" in n and "        run: ci/nightly-red.sh\n" in n and "WORKFLOW: ${{ github.workflow }}" in n,
    "T4 a red nightly, and only a red nightly, runs ci/nightly-red.sh with issues: write")
say("  cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n" in wf, "T4 cancel-in-progress for pull requests only")
group = re.search(r"^concurrency:\n  group: (.*)$", wf, re.M)
g = group.group(1).rstrip() if group else ""
say(g.endswith("|| format('ci-{0}-{1}', github.event_name, github.run_id) }}") and "github.ref" not in g.replace("github.head_ref", ""),
    "T4 a run that is no pull request's has a concurrency group of its own run id")
say("&& 'full' || 'pr'" in g and "format('noop-{0}', github.run_id)" in g,
    "T4 a pull request's full and pr runs are separate groups, and another label's noop cancels nothing")
say(re.search(r"^  push:\n    branches: \[%s\]\n" % re.escape(PUSH_BRANCHES), wf, re.M) is not None,
    "T4 a push runs on %s alone (a lane's push runs once, as its pull request)" % PUSH_BRANCHES)
say(re.search(r"^  schedule:\n(\s+#.*\n)*\s+- cron: ", wf, re.M) is not None, "T4 the nightly runs")
say("    types: [opened, synchronize, reopened, labeled]\n" in wf, "T4 adding a label starts a run")
say(re.search(r"^  workflow_dispatch:\n    inputs:\n(?:      [a-z_]+:\n(?:        .*\n)+)*      tier:\n", wf, re.M) is not None
    and "        options: [full, pr]\n" in wf, "T4 a dispatch takes the tier input, full or pr")
say(plan(event="push")["matrix"] == ALL_HOSTS, "T4 the full tier's hosts are the ones before tl28: %s" % json.dumps(BEFORE_HOSTS))
say(all(e in ALL_HOSTS.get(k, []) for k, v in BEFORE_HOSTS.items() for e in v) and
    all(len(ALL_HOSTS[k]) == len(v) for k, v in BEFORE_HOSTS.items()), "T4 no host left the full tier")

# --- T7 the change read from git ----------------------------------------------------
def g_(repo, *args):
    cmd = ["git", "-C", repo, "-c", "user.name=tiers-test", "-c", "user.email=tiers-test@invalid",
           "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false"] + list(args)
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def write(repo, rel, text):
    full = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(full) or full, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


MOVED = code + ".moved"


def merged(topic_paths):
    """A repository whose HEAD merges a topic branch (changing topic_paths)
    into a base that moved on meanwhile -> (repo, the topic's head)."""
    repo = tempfile.mkdtemp(prefix="tiers-test-")
    g_(repo, "init", "-q", "-b", "trunk")
    for rel in [code] + PROSE_PATHS[:2]:
        write(repo, rel, "one\n")
    g_(repo, "add", ".")
    g_(repo, "commit", "-q", "-m", "base")
    g_(repo, "checkout", "-q", "-b", "topic")
    for rel in topic_paths:
        write(repo, rel, "the topic\n")
    g_(repo, "add", ".")
    g_(repo, "commit", "-q", "-m", "topic")
    head = g_(repo, "rev-parse", "HEAD")
    g_(repo, "checkout", "-q", "trunk")
    write(repo, MOVED, "the base moved on\n")
    g_(repo, "add", ".")
    g_(repo, "commit", "-q", "-m", "trunk moves")
    g_(repo, "merge", "-q", "--no-ff", "-m", "merge", "topic")
    return repo, head


def dispatched(topic_paths):
    """A clone whose HEAD is a branch off trunk (changing topic_paths), its
    origin/trunk moved on meanwhile -> (the upstream, the clone)."""
    up = tempfile.mkdtemp(prefix="tiers-test-up-")
    g_(up, "init", "-q", "-b", "trunk")
    for rel in [code] + PROSE_PATHS[:1]:
        write(up, rel, "one\n")
    g_(up, "add", ".")
    g_(up, "commit", "-q", "-m", "base")
    clone = tempfile.mkdtemp(prefix="tiers-test-clone-")
    subprocess.run(["git", "clone", "-q", up, clone], check=True, capture_output=True)
    g_(clone, "checkout", "-q", "-b", "tl")
    for rel in topic_paths:
        write(clone, rel, "the branch\n")
    g_(clone, "add", ".")
    g_(clone, "commit", "-q", "-m", "branch")
    write(up, MOVED, "trunk moved on\n")
    g_(up, "add", ".")
    g_(up, "commit", "-q", "-m", "trunk moves")
    g_(clone, "fetch", "-q", "origin")
    return up, clone


made = []
try:
    repo, head = merged(PROSE_PATHS[:2])
    made.append(repo)
    expect("T7 a prose-only merge, the base moved on (its %s is not the pull request's)" % MOVED,
           plan(repo=repo, head_sha=head, flags=["--merge"], **pr), "noop", [])
    expect("T7 the same merge, the head not given", plan(repo=repo, flags=["--merge"], **pr), "noop", [])
    expect("T7 the merge's second parent is not the pull request's head",
           plan(repo=repo, head_sha="0" * 40, flags=["--merge"], **pr), "full", FULL_JOBS)
    g_(repo, "checkout", "-q", "topic")
    expect("T7 HEAD is the branch, not a merge commit", plan(repo=repo, head_sha=head, flags=["--merge"], **pr), "full", FULL_JOBS)
    repo, head = merged([PROSE_PATHS[0], code])
    made.append(repo)
    expect("T7 a merge that changes code and prose", plan(repo=repo, head_sha=head, flags=["--merge"], **pr), "pr", in_order(code_jobs))
    repo, head = merged([PROSE_PATHS[0], "somewhere/new.txt"])
    made.append(repo)
    expect("T7 a merge that adds a path no rule names", plan(repo=repo, head_sha=head, flags=["--merge"], **pr), "full", FULL_JOBS)
    dp = dict(event="workflow_dispatch", tier="pr", flags=["--merge"])
    up, clone = dispatched(PROSE_PATHS[:1])
    made += [up, clone]
    expect("T7 a dispatched prose-only branch, trunk moved on (its %s is not the branch's)" % MOVED,
           plan(repo=clone, **dp), "noop", [])
    up, clone = dispatched([code, PROSE_PATHS[0]])
    made += [up, clone]
    expect("T7 a dispatched branch that changes code", plan(repo=clone, **dp), "pr", in_order(code_jobs))
    up, clone = dispatched(["plant-unmapped.txt", code])
    made += [up, clone]
    expect("T7 a dispatched branch that adds a path no rule names (the plant)", plan(repo=clone, **dp), "full", FULL_JOBS)
    g_(clone, "checkout", "-q", "-B", "on-trunk", "origin/trunk")
    expect("T7 a dispatch at trunk itself, tier pr (no change to read)", plan(repo=clone, **dp), "full", FULL_JOBS)
    lone, _ = merged([code])
    made.append(lone)
    expect("T7 a dispatch with no origin/trunk to read", plan(repo=lone, **dp), "full", FULL_JOBS)
except (subprocess.CalledProcessError, OSError) as e:
    say(False, "T7 could not build its repositories: %s %s" % (e, getattr(e, "stderr", "")))
finally:
    for d in made:
        shutil.rmtree(d, ignore_errors=True)

# --- T8 the nightly's issue -------------------------------------------------------
FAKE_GH = r'''#!/usr/bin/env bash
printf '%s\n' "$*" >> "$FAKE_LOG"
case "$1 $2" in
  "label create") exit "${FAKE_LABEL_RC:-0}" ;;
  "issue list") printf '%s' "${FAKE_EXISTING:-}"; [ -n "${FAKE_EXISTING:-}" ] && echo; exit 0 ;;
esac
exit 0
'''


def nightly_red(existing="", label_rc=0):
    d = tempfile.mkdtemp(prefix="tiers-test-gh-")
    try:
        with open(os.path.join(d, "gh"), "w") as f:
            f.write(FAKE_GH)
        os.chmod(os.path.join(d, "gh"), 0o755)
        log = os.path.join(d, "log")
        env = dict(os.environ, PATH=d + os.pathsep + os.environ.get("PATH", ""), FAKE_LOG=log, FAKE_EXISTING=existing,
                   FAKE_LABEL_RC=str(label_rc), REPO="wolffe-lang/lobo", WORKFLOW=WORKFLOW_NAME,
                   RUN_URL="https://github.com/wolffe-lang/lobo/actions/runs/1")
        r = subprocess.run(["bash", RED], capture_output=True, text=True, env=env)
        calls = open(log).read().splitlines() if os.path.exists(log) else []
        return r.returncode, calls
    finally:
        shutil.rmtree(d, ignore_errors=True)


TITLE = "nightly red: %s on trunk" % WORKFLOW_NAME
rc, calls = nightly_red()
creates = [c for c in calls if c.startswith("issue create")]
say(rc == 0 and len(creates) == 1 and "--title %s" % TITLE in creates[0] and "--label nightly-red" in creates[0]
    and not [c for c in calls if c.startswith("issue comment")],
    "T8 no open issue: one is opened, labelled nightly-red, titled '%s'" % TITLE)
lists = [c for c in calls if c.startswith("issue list")]
say(len(lists) == 1 and "--state open" in lists[0] and "--label nightly-red" in lists[0] and TITLE in lists[0],
    "T8 the dedupe asks for an open nightly-red issue under the title")
rc, calls = nightly_red(existing="41")
say(rc == 0 and [c for c in calls if c.startswith("issue comment 41 ")] and not [c for c in calls if c.startswith("issue create")],
    "T8 an open issue: a comment on it, no new issue")
rc, calls = nightly_red(label_rc=1)
say(rc == 0 and [c for c in calls if c.startswith("issue create")], "T8 a label that already exists is no failure")
r = subprocess.run(["bash", RED], capture_output=True, text=True, env=clean_env(PATH=os.environ.get("PATH", "")))
say(r.returncode != 0, "T8 the script refuses to run without REPO, WORKFLOW and RUN_URL")
say(re.search(r"^name: %s$" % re.escape(WORKFLOW_NAME), wf, re.M) is not None, "T8 the workflow's name is %s, the title's" % WORKFLOW_NAME)

# --- T5 the tripwire: what the planner calls prose, nothing reads ---------------------
def tracked():
    try:
        return subprocess.run(["git", "-C", ROOT, "ls-files"], check=True, capture_output=True, text=True).stdout.split("\n")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


def classes(paths):
    out = {}
    for i in range(0, len(paths), 500):
        r = subprocess.run([sys.executable, PLAN, "classify"] + paths[i:i + 500], check=True, capture_output=True, text=True)
        out.update((line.split("\t")[0], line.split("\t")[1]) for line in r.stdout.splitlines())
    return out


def patterns(p):
    """How a line names p: a directory root (`notes/`) by `notes/` or a quoted
    "notes"; a file by its path, or its own name quoted (os.path.join)."""
    if p.endswith("/"):
        d = re.escape(p[:-1])
        return [re.compile(r"(?<![A-Za-z0-9_.-])%s/" % d), re.compile(r"[\"']%s[\"']" % d)]
    return [re.compile(r"(?<![A-Za-z0-9_./-])%s(?![A-Za-z0-9_])" % re.escape(p)),
            re.compile(r"[\"']%s[\"']" % re.escape(os.path.basename(p)))]


def readers(code_files, paths):
    """{path: ["file:line", ...]}: the lines of code_files that read a file
    (READS) and name the path (patterns). Comment lines are no reader, nor a
    line RULED says names something else (its regex, with its reason)."""
    pats = {p: patterns(p) for p in paths}
    hits = {p: [] for p in paths}
    for c in code_files:
        try:
            lines = open(os.path.join(ROOT, c), encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for n, line in enumerate(lines, 1):
            if line.lstrip().startswith(("#", "//")) or not READS.search(line):
                continue
            for p in paths:
                if any(x.search(line) for x in pats[p]) and not any(re.search(rx, line) for rx in RULED.get(p, {})):
                    hits[p].append("%s:%d" % (c, n))
    return hits


files = [f for f in tracked() if f]
if files:
    cls = classes(files)
    prose = sorted(p for p in files if cls.get(p) == "prose")
    unknown = sorted(p for p in files if cls.get(p) == "FULL")
    print("tiers-test: %d tracked paths are prose: %s" % (len(prose), " ".join(prose[:10]) + (" ..." if len(prose) > 10 else "")))
    code_files = [f for f in files if is_code(f)]
    seen = readers(code_files, MUST_FIND)
    say(all(seen[p] for p in MUST_FIND), "T5 the search fires: it finds what reads %s" % ", ".join(
        "%s (%s)" % (p, seen[p][0] if seen[p] else "NOTHING") for p in MUST_FIND))
    roots = sorted({p.split("/")[0] + ("/" if "/" in p else "") for p in prose})
    hit = {p: w for p, w in readers(code_files, roots).items() if w}
    say(not hit, "T5 no line of %d code file(s) that reads a file names a prose root (%s): %s" % (
        len(code_files), " ".join(roots), "; ".join("%s at %s" % (p, " ".join(w[:3])) for p, w in sorted(hit.items())) or "none"))
    extra_t5(files, cls, say)
    if unknown:
        print("tiers-test: WARN T5 %d tracked path(s) no rule names (a pull request touching one runs full): %s"
              % (len(unknown), " ".join(unknown[:20])))
    else:
        print("tiers-test: PASS T5 every one of %d tracked paths has a rule" % len(files))
else:
    say(False, "T5 not a git checkout: the tracked paths cannot be listed")

extra_checks(say, plan, expect, blocks, wf)

# T8, what the reporter writes is public: the issue's title and body, a comment,
# the label's description. The plain rule holds in every run: no lane, ruling,
# crawl or sprint word and no internal tag (two letters and two or three digits). A
# local record also passes PUBLIC_TEXT_REFUSE, a file of further words kept outside
# this repository; a word from that file is reported by its line number, never spelt.
PLAIN = re.compile(r"\b(?:lanes?|rulings?|crawls?|sprints?)\b|\b[a-z]{2}\d{2,3}[a-z]?\b", re.I)
LISTED = []
if os.environ.get("PUBLIC_TEXT_REFUSE"):
    with open(os.environ["PUBLIC_TEXT_REFUSE"], encoding="utf-8") as fh:
        LISTED = [(n, re.compile(r"(?<![A-Za-z0-9_-])%s(?![A-Za-z0-9_-])" % re.escape(w.strip()), re.I))
                  for n, w in enumerate(fh, 1) if w.strip() and not w.startswith("#")]


def _log_lines(x):
    return x.splitlines() if isinstance(x, str) else list(x)


written = "\n".join(c for e in ("", "41") for c in _log_lines(nightly_red(existing=e)[1]) if not c.startswith("issue list"))
said = sorted({m.group(0) for m in PLAIN.finditer(written)}) + ["listed word %d" % n for n, rx in LISTED if rx.search(written)]
say(bool(written) and not said, "T8 nothing the reporter writes in public carries an internal word (%s)%s" % (
    "the plain rule and %d listed words" % len(LISTED) if LISTED else "the plain rule", ": " + ", ".join(said) if said else ""))

# --- T13 a trunk push leaves the macOS legs already green at its commit -----------
# Merges are fast-forwards, so a trunk push runs the commit its pull request's run
# has just passed. On the runner's own push to trunk the plan asks the REST API for
# this workflow's runs at the commit and leaves a macOS leg or job only on positive
# evidence. These rows run the planner as the workflow does (EVENT, and the
# runner's GITHUB_EVENT_NAME, GITHUB_REF, GITHUB_SHA, GITHUB_REPOSITORY,
# GITHUB_API_URL; PLAN_TOKEN) over a scratch git repository (--repo), against a
# stand-in API on 127.0.0.1; then the verdict's rows and the wiring's.
import http.server
import math
import threading
import time
import urllib.parse

T13_TOKEN = "tiers-test-stand-in-token-5e8a"
T13_SCRUB = ENV_KEYS + ("PLAN_TOKEN", "PLAN_API_TIMEOUT", "GH_TOKEN", "GITHUB_TOKEN", "GITHUB_EVENT_NAME", "GITHUB_REF",
                        "GITHUB_SHA", "GITHUB_REPOSITORY", "GITHUB_API_URL", "GITHUB_SERVER_URL", "GITHUB_STEP_SUMMARY",
                        "GITHUB_OUTPUT")
T13_WF_PATH = ".github/workflows/" + WORKFLOW_FILE


class T13Server(http.server.ThreadingHTTPServer):
    # A client that timed out leaves a handler writing to a closed socket.
    daemon_threads = True

    def handle_error(self, request, client_address):
        pass


class T13API:
    """The REST API's two answers the plan reads: the runs of the workflow at a
    commit, and a run's jobs (paged). `fault` is (path prefix, kind)."""

    def __init__(self, runs=(), jobs=None, fault=None, page_cap=100, ignore_filter=False, totals=None):
        self.runs, self.jobs = list(runs), dict(jobs or {})
        self.fault, self.page_cap, self.ignore_filter = fault, page_cap, ignore_filter
        self.totals, self.requests, self.redirect_to = dict(totals or {}), [], None
        api = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                api.requests.append((self.path, self.headers.get("Authorization")))
                status, body, extra = api.answer(self.path)
                data = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                for k, v in extra.items():
                    self.send_header(k, v)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = T13Server(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        self.url = "http://127.0.0.1:%d" % self.server.server_address[1]

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def answer(self, path):
        u = urllib.parse.urlsplit(path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if self.fault and u.path.startswith(self.fault[0]):
            kind = self.fault[1]
            if kind in (500, 403, 404):
                return kind, {"message": "stand-in error %d" % kind}, {}
            if kind == "html":
                return 200, b"<html>not json</html>", {}
            if kind == "keys":
                return 200, {"message": "an answer without the expected keys"}, {}
            if kind == "slow":
                time.sleep(4)
            if kind == "redirect":
                return 302, {}, {"Location": self.redirect_to + path}
        if u.path == "/repos/%s/actions/workflows/%s/runs" % (T13_REPO, WORKFLOW_FILE):
            rs = [x for x in self.runs if self.ignore_filter or x["head_sha"] == q.get("head_sha")]
            return 200, {"total_count": len(rs), "workflow_runs": rs}, {}
        m = re.fullmatch(r"/repos/%s/actions/runs/(\d+)/jobs" % re.escape(T13_REPO), u.path)
        if m:
            rid = int(m.group(1))
            js = self.jobs.get(rid, [])
            per, page = min(int(q.get("per_page", 30)), self.page_cap), int(q.get("page", 1))
            return 200, {"total_count": self.totals.get(rid, len(js)), "jobs": js[(page - 1) * per:page * per]}, {}
        return 404, {"message": "Not Found"}, {}


def t11_repo():
    d = tempfile.mkdtemp(prefix="tiers-test-push-")
    g = ["git", "-C", d, "-c", "user.name=tiers-test", "-c", "user.email=tiers-test@invalid", "-c", "commit.gpgsign=false"]
    subprocess.run(["git", "-c", "init.defaultBranch=trunk", "init", "-q", d], check=True)
    with open(os.path.join(d, "f"), "w") as f:
        f.write("the pushed commit\n")
    subprocess.run(g + ["add", "f"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", "the pushed commit"], check=True)
    rev = lambda r: subprocess.run(["git", "-C", d, "rev-parse", r], capture_output=True, text=True, check=True).stdout.strip()
    return d, rev("HEAD"), rev("HEAD^{tree}")


T13_DIR, T13_SHA, T13_TREE = t11_repo()
T13_SEEN = []


def t11_plan(api, event="push", event_name="push", ref="refs/heads/trunk", sha=None, token=T13_TOKEN, timeout=None,
             summary=None):
    d = tempfile.mkdtemp(prefix="tiers-test-out-")
    out = os.path.join(d, "output")
    open(out, "w").close()
    env = {k: v for k, v in os.environ.items() if k not in T13_SCRUB}
    env.update(GITHUB_EVENT_NAME=event_name, GITHUB_REF=ref, GITHUB_SHA=sha or T13_SHA, GITHUB_REPOSITORY=T13_REPO,
               GITHUB_API_URL=api.url, GITHUB_SERVER_URL="https://github.com")
    if token:
        env["PLAN_TOKEN"] = token
    if timeout:
        env["PLAN_API_TIMEOUT"] = str(timeout)
    if summary:
        env["GITHUB_STEP_SUMMARY"] = summary
    r = subprocess.run([sys.executable, PLAN, "plan", "--event", event, "--repo", T13_DIR, "--github-output", out],
                       capture_output=True, text=True, env=env, timeout=120)
    text = open(out).read()
    shutil.rmtree(d, ignore_errors=True)
    T13_SEEN.append(r.stdout + r.stderr + text)
    if r.returncode != 0:
        return {"ERROR": r.returncode}, r.stderr
    o = dict(l.split("=", 1) for l in text.splitlines() if "=" in l)
    got = {"tier": o.get("tier"), "jobs": json.loads(o.get("jobs", "null")),
           "matrix": {k: json.loads(v) for k, v in o.items() if k.startswith("matrix_")}}
    got["covered"] = json.loads(o["macos_covered"]) if "macos_covered" in o else None
    return got, r.stderr


def t11_render(job, leg):
    return "%s (%s)" % (job, ", ".join(str(v).lower() if isinstance(v, bool) else str(v) for v in leg.values()))


def t11_less(p, names):
    """A plan less the macOS legs and jobs named."""
    q = {"tier": p["tier"], "jobs": [j for j in p["jobs"] if not (j in T13_WHOLE and j in names)]}
    q["matrix"] = {k: [l for l in v if t11_render(k[len("matrix_"):], l) not in names] for k, v in p["matrix"].items()}
    return q


def t11_wrun(rid, event="pull_request", conclusion="success", status="completed", sha=None, path=None):
    return {"id": rid, "event": event, "status": status, "conclusion": conclusion, "head_sha": sha or T13_SHA,
            "path": path or T13_WF_PATH, "run_attempt": 1}


def t11_job(name, conclusion="success", labels=None, steps=None):
    return {"name": name, "status": "completed", "conclusion": conclusion,
            "labels": labels if labels is not None else [T13_MAC.get(name, "ubuntu-24.04")], "steps": steps or []}


def t11_green(tree=None, step=True, drop=(), swap=None, extra=()):
    steps = [{"name": "Set up job", "conclusion": "success"}]
    if step:
        steps.append({"name": "the tree under test is %s" % (tree or T13_TREE), "conclusion": "success"})
    js = [t11_job("plan", steps=steps), t11_job("tier full")] + [t11_job(n) for n in T13_LINUX]
    js += [(swap or {}).get(n, t11_job(n)) for n in T13_MAC if n not in drop]
    return js + list(extra)


T13_PLANS = []
T13_LINE = re.compile(r"^tiers: (skip|keep) (.+?): (.*)$", re.M)


def t11_row(what, api, want_names, **kw):
    """`want_names`: the macOS names the plan should leave (the rest run)."""
    got, err = t11_plan(api, **kw)
    T13_PLANS.append(got)
    want = t11_less(T13_FULL, want_names)
    lines = T13_LINE.findall(err)
    skipped = {n: why for v, n, why in lines if v == "skip"}
    ok = ("ERROR" not in got and {k: got[k] for k in ("tier", "jobs", "matrix")} == want
          and sorted(got["covered"] or {}) == sorted(want_names) and sorted(n for _, n, _ in lines) == sorted(T13_MAC)
          and sorted(skipped) == sorted(want_names))
    say(ok, "T13 %s: leaves %s%s" % (what, sorted(want_names) or "no macOS leg",
                                      "" if ok else " (got %s; lines %s)" % (got, [(v, n) for v, n, _ in lines])))
    return got, err, skipped


T13_FULL, _ = t11_plan(T13API(), token=None)
say("ERROR" not in T13_FULL and T13_FULL["tier"] == "full" and T13_FULL["covered"] == {}
    and sorted(n for n in T13_MAC) == sorted(
        [t11_render(k[len("matrix_"):], l) for k, v in T13_FULL["matrix"].items() for l in v if l["os"].startswith("macos")]
        + [j for j in T13_FULL["jobs"] if j in T13_WHOLE]),
    "T13 a trunk push with no token plans the full tier, covers nothing, and its macOS legs are %s" % sorted(T13_MAC))

summary = os.path.join(tempfile.mkdtemp(prefix="tiers-test-sum-"), "summary.md")
api = T13API([t11_wrun(7001)], {7001: t11_green()})
got, err, skipped = t11_row("a green pull request run at the commit and tree", api, list(T13_MAC), summary=summary)
say(got.get("covered") and all((c["run"], c["event"], c["sha"], c["tree"], c["label"]) == (7001, "pull_request", T13_SHA, T13_TREE, T13_MAC[n])
                               for n, c in got["covered"].items())
    and all(("green in pull_request run 7001 at %s, tree %s" % (T13_SHA, T13_TREE)) in why for why in skipped.values()),
    "T13 each skip names the run it relied on (pull_request run 7001), the commit and the tree")
say(os.path.exists(summary) and open(summary).read().count("7001") >= len(T13_MAC), "T13 the step summary names the run for each skipped leg")
jq = [urllib.parse.parse_qs(urllib.parse.urlsplit(p).query) for p, _ in api.requests if "/jobs" in p]
say(jq and all(q.get("filter") == ["latest"] for q in jq), "T13 a run's jobs are read at its latest attempt (filter=latest)")
say(api.requests and all(a == "Bearer " + T13_TOKEN for _, a in api.requests), "T13 every request carries the workflow's token")
api.close()

api = T13API([t11_wrun(7002, event="workflow_dispatch")], {7002: t11_green()})
t11_row("a green dispatch run at the commit counts", api, list(T13_MAC))
api.close()
for ev in ("schedule", "push"):
    api = T13API([t11_wrun(7003, event=ev)], {7003: t11_green()})
    t11_row("a green %s run at the commit does not count" % ev, api, [])
    api.close()
api = T13API([t11_wrun(7004, conclusion="failure"), t11_wrun(7005, conclusion="cancelled"),
              t11_wrun(7006, status="in_progress", conclusion=None)], {i: t11_green() for i in (7004, 7005, 7006)})
t11_row("a failed, a cancelled and a running pull request run do not count", api, [])
api.close()
for what, jobs in (("a run that tested another tree", t11_green(tree="0" * 40)), ("a run whose plan names no tree", t11_green(step=False)),
                   ("a green run with no macOS job at all", t11_green(drop=list(T13_MAC)))):
    api = T13API([t11_wrun(7007)], {7007: jobs})
    t11_row(what + ": every macOS leg runs", api, [])
    api.close()
first = sorted(T13_MAC)[0]
rest = [n for n in T13_MAC if n != first]
for what, jobs in (("missing", t11_green(drop=[first])), ("cancelled", t11_green(swap={first: t11_job(first, conclusion="cancelled")})),
                   ("listed twice, once red", t11_green(extra=[t11_job(first, conclusion="failure")])),
                   ("run on Linux", t11_green(swap={first: t11_job(first, labels=["ubuntu-24.04"])}))):
    api = T13API([t11_wrun(7008)], {7008: jobs})
    t11_row("%s %s: it runs, the green ones do not" % (first, what), api, rest)
    api.close()
api = T13API([t11_wrun(7009), t11_wrun(7010, conclusion="failure")], {7009: t11_green(drop=[first]), 7010: t11_green()})
t11_row("two runs at the commit, the red one with every leg: only the green one counts", api, rest)
api.close()
if rest:
    api = T13API([t11_wrun(7011), t11_wrun(7012, event="workflow_dispatch")], {7011: t11_green(drop=[first]), 7012: t11_green(drop=rest)})
    t11_row("two green runs, each with some legs: each leg relies on a run that has it", api, list(T13_MAC))
    api.close()
api = T13API([t11_wrun(7013)], {7013: t11_green()}, page_cap=2)
t11_row("a jobs listing over several pages is read to its count", api, list(T13_MAC))
pages = math.ceil(len(t11_green()) / 2)
say(pages >= 2 and len([p for p, _ in api.requests if "/jobs" in p]) == pages, "T13 the planner read every page (%d)" % pages)
api.close()
api = T13API([t11_wrun(7014)], {7014: t11_green()}, totals={7014: 999})
t11_row("a jobs listing short of its total_count is no evidence", api, [])
api.close()
api = T13API([t11_wrun(7015, sha="1" * 40), t11_wrun(7016, path=".github/workflows/other.yml")], {7015: t11_green(), 7016: t11_green()},
             ignore_filter=True)
t11_row("runs of another commit or another workflow, listed anyway, do not count", api, [])
api.close()
for where, kind in (("/repos/%s/actions/workflows" % T13_REPO, 500), ("/repos/%s/actions/runs" % T13_REPO, 403),
                    ("/repos/%s/actions/workflows" % T13_REPO, "html"), ("/repos/%s/actions/runs" % T13_REPO, "keys"),
                    ("/repos/%s/actions/workflows" % T13_REPO, 404)):
    api = T13API([t11_wrun(7017)], {7017: t11_green()}, fault=(where, kind))
    t11_row("the lookup answered %s at %s: every macOS leg runs" % (kind, where.rsplit("/", 1)[-1]), api, [])
    api.close()
api = T13API([t11_wrun(7018)], {7018: t11_green()}, fault=("/repos/%s/actions/workflows" % T13_REPO, "slow"))
t0 = time.time()
t11_row("the lookup timed out: every macOS leg runs", api, [], timeout=1)
say(time.time() - t0 < 30, "T13 the timeout holds (%.1f s)" % (time.time() - t0))
api.close()
elsewhere = T13API([t11_wrun(7019)], {7019: t11_green()})
api = T13API([t11_wrun(7019)], {7019: t11_green()}, fault=("/repos/%s/actions/workflows" % T13_REPO, "redirect"))
api.redirect_to = elsewhere.url
t11_row("the API redirected: not followed, every macOS leg runs", api, [])
say(elsewhere.requests == [], "T13 a redirect takes the token nowhere (the other host saw %d requests)" % len(elsewhere.requests))
api.close()
elsewhere.close()
api = T13API([t11_wrun(7020)], {7020: t11_green()})
t11_row("no token: every macOS leg runs", api, [], token=None)
t11_row("the checkout is not the pushed commit: every macOS leg runs", api, [], sha="2" * 40)
say(api.requests == [], "T13 without a token, or off the pushed commit, nothing is asked")
api.close()
# A labelled pull request's run hands its plan EVENT=push: only the runner's own
# event and ref decide. Neither that run, another branch's push, the nightly nor a
# dispatch asks.
for what, kw in (("a labelled pull request's run (EVENT=push)", dict(event_name="pull_request")),
                 ("a push to another branch", dict(ref="refs/heads/a-lane")),
                 ("the nightly", dict(event="schedule", event_name="schedule")),
                 ("a dispatch", dict(event="workflow_dispatch", event_name="workflow_dispatch"))):
    api = T13API([t11_wrun(7021)], {7021: t11_green()})
    got, err = t11_plan(api, **kw)
    say(api.requests == [] and "ERROR" not in got and got["covered"] == {} and not T13_LINE.search(err),
        "T13 %s asks nothing and leaves nothing" % what)
    api.close()
say(all("ERROR" not in p for p in T13_PLANS), "T13 every trunk push plan exits 0")
say(T13_SEEN and not [s for s in T13_SEEN if T13_TOKEN in s], "T13 the token is never printed")
shutil.rmtree(T13_DIR, ignore_errors=True)

# The verdict: a full run less the covered legs, each covered leg named.
T13_COVER = {n: {"job": (n if n in T13_WHOLE else n.split(" (", 1)[0]), "label": T13_MAC[n], "run": 7001, "event": "pull_request",
                 "sha": "a" * 40, "tree": "b" * 40} for n in T13_MAC}
for n, c in T13_COVER.items():
    c["leg"] = None if n in T13_WHOLE else [l for l in T13_FULL["matrix"]["matrix_" + c["job"].replace("-", "_")]
                                            if t11_render(c["job"], l) == n][0]


def t11_needs(plan_, covered, ran=()):
    outs = {"tier": plan_["tier"], "jobs": json.dumps(plan_["jobs"]), "macos_covered": json.dumps(covered)}
    for k, v in plan_["matrix"].items():
        outs[k] = json.dumps(v, separators=(",", ":"))
    n = {"plan": {"result": "success", "outputs": outs}}
    for j in EVERY:
        n[j] = {"result": "success" if j in plan_["jobs"] or j in ran else "skipped", "outputs": {}}
    return n


left = t11_less(T13_FULL, list(T13_MAC))
rc, text = verdict(t11_needs(left, T13_COVER))
say(rc == 0 and all(("covered %s: green in pull_request run 7001 at %s, tree %s" % (n, "a" * 40, "b" * 40)) in text for n in T13_MAC),
    "T13 a full run less its covered macOS legs reads green and names each one's run%s" % ("" if rc == 0 else ": " + text.strip()[-300:]))
for what, needs in (
        ("the covered legs left without their cover", t11_needs(left, {})),
        ("a cover in a pr tier", t11_needs(dict(left, tier="pr"), T13_COVER)),
        ("a cover that names a push run", t11_needs(left, {n: dict(c, event="push") for n, c in T13_COVER.items()})),
        ("a cover with no run", t11_needs(left, {n: dict(c, run="x") for n, c in T13_COVER.items()})),
        ("a cover that is no object", dict(t11_needs(left, {}), plan={"result": "success", "outputs": dict(
            t11_needs(left, {})["plan"]["outputs"], macos_covered='["x"]')}))):
    rc, text = verdict(needs)
    say(rc == 1, "T13 the verdict says no to %s (exit %d)" % (what, rc))
linux = [(k, l) for k, v in T13_FULL["matrix"].items() for l in v if not l["os"].startswith("macos")]
if linux:
    k, l = linux[0]
    job = k[len("matrix_"):]
    name = t11_render(job, l)
    bad = dict(T13_COVER, **{name: {"job": job, "leg": l, "label": l["os"], "run": 7001, "event": "pull_request",
                                    "sha": "a" * 40, "tree": "b" * 40}})
    shorter = dict(left, matrix={kk: [x for x in vv if not (kk == k and x == l)] for kk, vv in left["matrix"].items()})
else:
    job = [j for j in left["jobs"] if j not in T13_WHOLE][0]
    bad = dict(T13_COVER, **{job: {"job": job, "leg": None, "label": "ubuntu-24.04", "run": 7001, "event": "pull_request",
                                   "sha": "a" * 40, "tree": "b" * 40}})
    shorter = dict(left, jobs=[j for j in left["jobs"] if j != job])
rc, _ = verdict(t11_needs(shorter, bad))
say(rc == 1, "T13 the verdict says no to a covered Linux leg or job (exit %d)" % rc)
rc, _ = verdict(t11_needs(T13_FULL, T13_COVER))
say(rc == 1, "T13 the verdict says no to a leg both covered and run (exit %d)" % rc)

# The wiring.
tb = dict(re.findall(r"^  ([A-Za-z0-9_-]+):\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)", wf.split("\njobs:\n", 1)[1], re.M | re.S))
pb = tb.get("plan", "")
say("      macos_covered: ${{ steps.plan.outputs.macos_covered }}\n" in pb, "T13 the plan job declares macos_covered")
TREE_NAME = "      - name: the tree under test is ${{ steps.tree.outputs.tree }}\n"
say("        id: tree\n" in pb and TREE_NAME in pb and pb.index("        id: tree\n") < pb.index(TREE_NAME) < pb.index("        id: plan\n")
    and "test \"$(git rev-parse 'HEAD^{tree}')\" = \"${{ steps.tree.outputs.tree }}\"" in pb,
    "T13 the plan job names the tree it tests in a step's name, checked, before the plan")
say(wf.count("PLAN_TOKEN") == 1 and re.search(r"^        id: plan\n        env:\n(          .*\n|          #.*\n)*          PLAN_TOKEN: \$\{\{ github\.token \}\}\n", pb, re.M) is not None,
    "T13 the plan's step, and no other, is given the workflow's token")
head = wf.split("\njobs:\n", 1)[0]
say(re.search(r"^permissions:\n(  [a-z-]+: read\n)*  actions: read\n", head, re.M) is not None
    and re.search(r"^permissions:\n(  [a-z-]+: read\n)*  contents: read\n", head, re.M) is not None
    and not re.search(r"^    permissions:", pb, re.M),
    "T13 the workflow reads its runs (actions: read beside contents: read), and the plan job asks for no permission of its own")
named = []
for n, label in T13_MAC.items():
    if n in T13_WHOLE:
        b = tb.get(n, "")
        named.append(("    runs-on: %s\n" % label) in b and not re.search(r"^    name: ", b, re.M))
    else:
        b = tb.get(n.split(" (", 1)[0], "")
        named.append("    runs-on: ${{ matrix.os }}\n" in b and not re.search(r"^    name: ", b, re.M))
say(named and all(named), "T13 the macOS jobs a trunk push looks for are named as this workflow names them: %s" % sorted(T13_MAC))

print("tiers-test: %s" % ("PASS" if fails == 0 else "FAIL (%d)" % fails))
sys.exit(1 if fails else 0)
