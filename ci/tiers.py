#!/usr/bin/env python3
"""ci/tiers.py — which jobs a CI run runs, and whether it ran them (tl28,
ruling #92; wolf-lang's ci/tiers.py, tl21, cut to lobo).

    ci/tiers.py plan [--event E] [--action A] [--label L] [--labels L1,L2]
                     [--tier full|pr] [--input KEY=VALUE]...
                     [--merge [--head-sha SHA] | --paths-from FILE]
                     [--repo DIR] [--github-output FILE] [--json]
    ci/tiers.py verdict        (NEEDS: the `tier` job's `toJSON(needs)`)
    ci/tiers.py classify PATH...

`plan` options also read an environment variable of their name in capitals
(EVENT, ACTION, LABEL, LABELS, HEAD_SHA, IN_TIER; a dispatch's other inputs
as IN_<NAME>), which is how the workflow's `plan` job passes the event in.

THE TIERS. A job is a job of .github/workflows/ci.yml between `plan` and
`tier`.

  full     both gauntlets: `gauntlet` on linux x86-64 and `gauntlet-macos`
           (the long one: up to 26 minutes, a 90-minute ceiling). A push to
           trunk, the nightly `schedule`, a `workflow_dispatch` (its `tier`
           input full, the default), a pull request carrying the
           `full-matrix` label; and a pull request with a changed path no
           rule below names, or whose change cannot be read: what is not
           understood never shrinks a run.
  pr       any other pull-request run, and a dispatch with `tier` pr: the
           linux gauntlet. Every path of the server, its tests, its tools,
           its docs and CI names it (the gauntlet holds docs/ and the
           CHANGELOG to the code: tools/lobo-metricsdoc, lobo-logvars,
           lobo-stamp, lobo-dist); the macOS gauntlet waits for the full
           tier.
  noop     nothing but the plan and the verdict: a pull request whose
           changed paths are ALL prose, and a `labeled` event for a label
           other than `full-matrix`.
  measure  a dispatch with `parity`, `profile` or `syscalls` (ws22, ws25,
           ws27): the linux job alone, which runs the measurement INSTEAD
           of the gauntlet, as before. A number, never merge evidence.

A dispatch with `tier` pr reads the dispatched branch's change against
trunk (the merge base) exactly as a pull request's, so a plant can ask for
the pull-request tier without opening one; a path no rule names runs full.

PROSE IS NARROW (RULES, below): notes/ (the lanes' notes and evidence) and
the two guides, CONTRIBUTING.md and CLAUDE.md. Not prose, because the
gauntlet reads it: docs/ (two pages are generated and held to their tables,
and the dist stages the rest), CHANGELOG.md (the stamp and the release
notes), README.md (the dist). ci/tiers-test.py trips when a line of tools/
or tests/ that reads a file starts naming a prose path.

`verdict` checks a finished run: exit 0 when the plan succeeded, the jobs it
chose are the tier's, every chosen job succeeded and every other job was
skipped; 1 otherwise. GitHub leaves an EMPTY output out of `needs`, so each
is read with a default.

`plan` prints `tier=` and `jobs=` (a JSON list), to --github-output
(appended) and to standard output; with --json, one JSON object. The
reasons, one line per changed path, go to standard error, so a run's log
says why it has the jobs it has. Exit 0; 2 on a usage error.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = ".github/workflows/ci.yml"
FULL_LABEL = "full-matrix"
TRUNK = "trunk"
# Jobs that are no tier's choice: the plan, the verdict, and what runs after
# the verdict (the nightly's issue).
NOT_SELECTABLE = ("plan", "tier", "nightly-red")
TIERS = ("full", "pr", "noop")
# What a repository's config may add (the defaults: nothing):
#   ON_REQUEST   jobs that only a dispatch's own input runs, never full or pr;
#   EXTRA_TIERS  {tier: (the jobs it runs, of `every`; whether it runs every
#                leg; whether it runs ALL those jobs (True) or one or more of
#                them (False))}, for the verdict;
#   special(a, every, log) -> None, or (tier, the jobs it chose): a run the
#                event and the dispatch's own inputs (a.inputs) decide alone.
ON_REQUEST = ()
EXTRA_TIERS = {}


def special(a, every, log):
    return None

# --- this repository's ---------------------------------------------------------
# No job of lobo's has a matrix: the two gauntlets are two jobs, one host each.
MATRIX = {}


def pr_leg(job, leg):
    return True


LINUX = ("gauntlet",)
PROSE = ()
FULL = "FULL"
EXTRA_TIERS = {"measure": (lambda every: ["gauntlet"], False, True)}


def special(a, every, log):
    """A measurement dispatch (parity, profile or syscalls) is the linux job
    alone: its steps run the measurement instead of the gauntlet."""
    if a.event == "workflow_dispatch" and (a.inputs.get("measure") or "").lower() == "true":
        log.append("dispatch with a measurement leg (parity, profile or syscalls): measure")
        return "measure", ["gauntlet"]
    return None


# A changed path's targets: the first rule that matches decides. `*` stays
# inside one path segment; a trailing `/**` is everything below. A target is
# a tuple of jobs (PROSE: none) or FULL. No rule names `gauntlet-macos`: it
# is the full tier's.
RULES = [
    # Prose: no step reads it (ci/tiers-test.py T5).
    ("notes/**", PROSE),
    ("CONTRIBUTING.md", PROSE),
    ("CLAUDE.md", PROSE),
    # The server, its tests and tools, its docs and pages, its pins, CI.
    ("src/**", LINUX),
    ("tests/**", LINUX),
    ("tools/**", LINUX),
    ("docs/**", LINUX),
    ("conf/**", LINUX),
    ("html/**", LINUX),
    ("demo/**", LINUX),
    ("wolf-toolchain.toml", LINUX),
    ("CHANGELOG.md", LINUX),
    ("README.md", LINUX),
    ("ci/**", LINUX),
    (".github/**", LINUX),
    ("LICENSE", LINUX),
    ("LICENSE-TRAINING-DATA", LINUX),
    (".gitignore", LINUX),
    (".gitattributes", LINUX),
]
# --- end of this repository's -------------------------------------------------
# Below: the planner itself, the same in every repository tl28 tiered (wolf-std,
# pelt, wolf-book, lobo, boreutils, wolf-lsp). Only the docstring and the
# block above are this repository's.


def die(msg):
    print("tiers: " + msg, file=sys.stderr)
    sys.exit(2)


def matches(glob, path):
    if glob.endswith("/**"):
        return path.startswith(glob[:-2])
    rx = "".join("[^/]*" if c == "*" else re.escape(c) for c in glob)
    return re.fullmatch(rx, path) is not None


def classify(path):
    """-> (targets, the rule that decided): a tuple of jobs, or FULL."""
    for glob, targets in RULES:
        if matches(glob, path):
            return targets, glob
    return FULL, "no rule names it"


def workflow_jobs():
    """The workflow's jobs, in order: {id: [the ids it needs]}."""
    jobs, cur, inside = {}, None, False
    with open(os.path.join(ROOT, WORKFLOW), encoding="utf-8") as f:
        for line in f.read().splitlines():
            if re.match(r"^jobs:\s*$", line):
                inside = True
            elif inside and re.match(r"^\S", line):
                inside = False
            elif inside:
                m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
                if m:
                    cur = m.group(1)
                    jobs[cur] = []
                    continue
                m = re.match(r"^    needs:\s*(.*)$", line)
                if m and cur:
                    jobs[cur] = re.findall(r"[A-Za-z0-9_-]+", m.group(1))
    return jobs


def jobs_of(tier, every):
    """The jobs a tier runs, of `every` selectable job, in order. (The pr
    tier's are the paths' choice: every job is the most it may run.)"""
    if tier in ("full", "pr"):
        return [j for j in every if j not in ON_REQUEST]
    if tier in EXTRA_TIERS:
        return [j for j in every if j in EXTRA_TIERS[tier][0](every)]
    return []


def output_name(job):
    return "matrix_" + job.replace("-", "_")


def matrix_of(tier):
    """{output name: the legs a matrix job runs in this tier}. A job the tier
    does not choose still gets its pull-request legs, so no matrix is ever
    empty (the job is skipped by its `if:` either way)."""
    out = {}
    for job, legs in MATRIX.items():
        every_leg = tier == "full" or (tier in EXTRA_TIERS and EXTRA_TIERS[tier][1])
        out[output_name(job)] = list(legs) if every_leg else [l for l in legs if pr_leg(job, l)]
    return out


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), check=True,
                          capture_output=True, text=True).stdout


def merge_paths(repo, head_sha):
    """-> (the paths a pull request changes, how they were read): the
    checked-out merge commit against its first parent, the base it was
    merged into. (None, the reason) when that cannot be read."""
    try:
        parents = git(repo, "rev-list", "--parents", "-n", "1", "HEAD").split()
        if len(parents) != 3:
            return None, "HEAD has %d parent(s), not a pull request's merge commit" % (len(parents) - 1)
        if head_sha and parents[2] != head_sha:
            return None, "the merge's second parent %s is not the pull request's head %s" % (parents[2][:9], head_sha[:9])
        out = git(repo, "diff", "--name-only", "--no-renames", "-z", parents[1], parents[0])
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        return None, "git could not read the change (%s)" % e
    return [p for p in out.split("\0") if p], "%s..%s" % (parents[1][:9], parents[0][:9])


def branch_paths(repo):
    """-> (the paths a dispatched branch changes, how they were read): HEAD
    against its merge base with origin/trunk. (None, the reason) when that
    cannot be read."""
    try:
        base = git(repo, "merge-base", "origin/" + TRUNK, "HEAD").strip()
        out = git(repo, "diff", "--name-only", "--no-renames", "-z", base, "HEAD")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        return None, "git could not read the branch's change against origin/%s (%s)" % (TRUNK, e)
    return [p for p in out.split("\0") if p], "%s..HEAD" % base[:9]


def plan(a):
    needs = workflow_jobs()
    every = [j for j in needs if j not in NOT_SELECTABLE]
    for j in MATRIX:
        if j not in every:
            die("MATRIX names %s, which is no job of %s" % (j, WORKFLOW))
    for _, targets in RULES:
        if targets != FULL:
            for j in targets:
                if j not in every:
                    die("RULES name %s, which is no job of %s" % (j, WORKFLOW))
    log = []

    def result(tier, chosen=None):
        if chosen is None:
            chosen = jobs_of(tier, every)
        else:
            # A chosen job brings the jobs it needs (a job whose need is
            # skipped is skipped itself, and the verdict would say so).
            closed, todo = set(chosen), list(chosen)
            while todo:
                for n in needs.get(todo.pop(), []):
                    if n not in NOT_SELECTABLE and n not in closed:
                        log.append("%s needs %s: chosen too" % (" ".join(j for j in every if j in closed and n in needs.get(j, [])), n))
                        closed.add(n)
                        todo.append(n)
            chosen = [j for j in every if j in closed]
        return {"tier": tier, "jobs": chosen, "matrix": matrix_of(tier), "log": log}

    labels = [x for x in (a.labels or "").split(",") if x]
    ev = a.event or "workflow_dispatch"
    a.event = ev
    log.append("event=%s action=%s label=%s labels=%s tier=%s" % (
        ev, a.action or "-", a.label or "-", ",".join(labels) or "-", a.tier or "-"))

    if ev == "pull_request" and a.action == "labeled" and a.label != FULL_LABEL:
        log.append("a label other than %s was added: noop" % FULL_LABEL)
        return result("noop")
    sp = special(a, every, log)
    if sp is not None:
        return result(sp[0], sp[1])
    if ev == "workflow_dispatch":
        if (a.tier or "full") not in ("full", "pr"):
            die("--tier takes full or pr, not %r" % a.tier)
        if (a.tier or "full") == "full":
            log.append("dispatch, tier full: full")
            return result("full")
    elif ev != "pull_request":
        log.append("%s: full" % ev)
        return result("full")
    elif FULL_LABEL in labels:
        log.append("the %s label: full" % FULL_LABEL)
        return result("full")

    if a.paths_from:
        f = sys.stdin if a.paths_from == "-" else open(a.paths_from, encoding="utf-8")
        paths, how = [p.strip() for p in f.read().splitlines() if p.strip()], a.paths_from
    elif a.merge and ev == "pull_request":
        paths, how = merge_paths(a.repo or ROOT, a.head_sha)
    elif a.merge:
        paths, how = branch_paths(a.repo or ROOT)
    else:
        paths, how = None, "no --merge and no --paths-from"
    if paths is None:
        log.append("the changed paths cannot be read (%s): full" % how)
        return result("full")
    if not paths:
        log.append("the change names no path (%s), which no pull request's does: full" % how)
        return result("full")

    chosen, unknown = set(), 0
    for p in paths:
        targets, why = classify(p)
        if targets == FULL:
            unknown += 1
            log.append("%s -> FULL  [%s]" % (p, why))
            continue
        chosen |= set(targets)
        log.append("%s -> %s  [%s]" % (p, " ".join(j for j in every if j in targets) or "prose", why))
    if unknown:
        log.append("%d of %d path(s) no rule names: full" % (unknown, len(paths)))
        return result("full")
    if not chosen:
        log.append("%d path(s), every one prose: noop" % len(paths))
        return result("noop")
    log.append("%d path(s): pr, %s" % (len(paths), " ".join(j for j in every if j in chosen)))
    return result("pr", chosen)


def verdict(needs):
    """The `tier` job's check, from `toJSON(needs)`."""
    plan_job = needs.get("plan") or {}
    if plan_job.get("result") != "success":
        print("tier: the plan did not succeed (%s)" % plan_job.get("result"))
        return 1
    out = plan_job.get("outputs") or {}
    tier = out.get("tier", "")
    if tier not in TIERS and tier not in EXTRA_TIERS:
        print("tier: the plan named no tier (%r)" % tier)
        return 1
    try:
        chosen = json.loads(out.get("jobs", "[]"))
        assert isinstance(chosen, list)
    except (ValueError, AssertionError):
        print("tier: the plan's list of jobs cannot be read (%r)" % out.get("jobs"))
        return 1
    every = [j for j in needs if j != "plan"]
    bad = 0
    want_jobs = jobs_of(tier, every)
    try:
        covered = read_covered(out, tier, want_jobs)
    except ValueError as e:
        print("tier: %s" % e)
        return 1
    want_jobs = [j for j in want_jobs if j not in [c["job"] for c in covered.values() if c["leg"] is None]]
    some = tier == "pr" or (tier in EXTRA_TIERS and not EXTRA_TIERS[tier][2])
    if some:
        if not chosen or [j for j in chosen if j not in want_jobs]:
            print("tier: a %s run chose %s; it may choose one or more of %s" % (
                tier, " ".join(chosen) or "nothing", " ".join(want_jobs)))
            bad += 1
    elif tier in EXTRA_TIERS and not want_jobs:
        print("tier: tier %s names no job of this workflow" % tier)
        bad += 1
    elif sorted(chosen) != sorted(want_jobs):
        print("tier: the plan chose %s; tier %s is %s" % (
            " ".join(chosen) or "nothing", tier, " ".join(want_jobs) or "nothing"))
        bad += 1
    for name, legs in sorted(less_covered(matrix_of(tier), covered).items()):
        try:
            got = json.loads(out.get(name, "null"))
        except ValueError:
            got = out.get(name)
        if got != legs:
            print("tier: the plan's %s is %s; tier %s runs %s" % (name, json.dumps(got), tier, json.dumps(legs)))
            bad += 1
    print("tier %s: %d of %d job(s) chosen" % (tier, len(chosen), len(every)))
    for name, c in sorted(covered.items()):
        print("covered %s: green in %s run %d at %s, tree %s" % (name, c["event"], c["run"], c["sha"], c["tree"]))
    for job in every:
        want = "success" if job in chosen else "skipped"
        got = (needs[job] or {}).get("result")
        ok = got == want
        bad += not ok
        print("  %-18s %-9s %s" % (job, got, "ok" if ok else "WANTED " + want))
    missing = [j for j in chosen if j not in every]
    if missing:
        print("tier: chosen, but the tier job does not need it: %s" % " ".join(missing))
        bad += 1
    return 1 if bad else 0


# --- a trunk push leaves the macOS legs already green at its commit ---------------
# Merges are fast-forwards, so a push to trunk runs the commit its pull request's
# run has just passed. On the runner's own push to trunk (GITHUB_EVENT_NAME and
# GITHUB_REF: a labelled pull request's run hands the plan EVENT=push, so EVENT
# alone never decides) the plan asks the REST API, with the workflow's own
# read-only token (PLAN_TOKEN), for this workflow's runs at GITHUB_SHA. It leaves a
# macOS leg, or a whole macOS job, only when a completed, successful pull_request
# or workflow_dispatch run there tested the same tree (its `plan` job's step `the
# tree under test is <tree>`: a pull request's run tests its merge with the base,
# which is this tree only when the base is already in the commit) and has, at its
# latest attempt, that job once, green, on its macOS runner. Anything else runs
# it: no such run, a lookup that fails, times out, redirects or answers oddly, a
# jobs listing short of its count, no token, a checkout that is not the pushed
# commit. A matrix job keeps at least one leg, and a job another chosen job needs
# is never left. The plan writes `macos_covered=` (each leg or job it left, with
# the run, event, commit and tree it relied on) and logs one line a kind; the
# verdict accepts exactly those in place of a green job and names the run.
EVIDENCE_EVENTS = ("pull_request", "workflow_dispatch")
TREE_STEP = re.compile(r"^the tree under test is ([0-9a-f]{40}|[0-9a-f]{64})$")
HEX = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
MAX_RUNS, MAX_PAGES = 10, 5


def leg_name(job, leg):
    """The name GitHub gives a leg of a matrix job that has no `name:`."""
    return "%s (%s)" % (job, ", ".join(str(v).lower() if isinstance(v, bool) else str(v) for v in leg.values()))


def job_hosts():
    """{job: (its literal `name:` or None, its literal `runs-on:` or None)}."""
    out, cur, inside = {}, None, False
    with open(os.path.join(ROOT, WORKFLOW), encoding="utf-8") as f:
        for line in f.read().splitlines():
            if re.match(r"^jobs:\s*$", line):
                inside = True
            elif inside and re.match(r"^\S", line):
                inside = False
            elif inside:
                m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
                if m:
                    cur = m.group(1)
                    out[cur] = [None, None]
                    continue
                m = re.match(r"^    (name|runs-on):\s*(.*?)\s*$", line)
                if m and cur:
                    out[cur][0 if m.group(1) == "name" else 1] = m.group(2)
    return {j: tuple(v) for j, v in out.items()}


def macos_kinds(r):
    """{name: (job, leg or None, runner label)}: each macOS leg of a chosen matrix
    job with no `name:`, and each chosen job that runs on a literal macOS label."""
    hosts, kinds = job_hosts(), {}
    for job in r["jobs"]:
        name, runs_on = hosts.get(job, (None, None))
        if job in MATRIX:
            if name is None:
                for leg in r["matrix"].get(output_name(job), []):
                    if str(leg.get("os", "")).startswith("macos"):
                        kinds[leg_name(job, leg)] = (job, leg, leg["os"])
        elif runs_on and runs_on.startswith("macos") and "${{" not in (name or "") + runs_on:
            kinds[name or job] = (job, None, runs_on)
    return kinds


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """The plan follows no redirect: the token goes to the API alone."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "a redirect, not followed", headers, fp)


class Api:
    def __init__(self, base, repo, token, timeout):
        self.base, self.repo, self.token, self.timeout = base.rstrip("/"), repo, token, timeout
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, path, **query):
        url = "%s/repos/%s/%s?%s" % (self.base, self.repo, path, urllib.parse.urlencode(query))
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ci-tiers-plan",
        })
        with self.opener.open(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


def run_jobs(api, run_id):
    """A run's jobs at its latest attempt, every page; None when the listing
    falls short of its own count."""
    jobs = []
    for page in range(1, MAX_PAGES + 1):
        d = api.get("actions/runs/%d/jobs" % run_id, filter="latest", per_page=100, page=page)
        got, total = d["jobs"], int(d["total_count"])
        jobs += got
        if len(jobs) >= total:
            return jobs if len(jobs) == total else None
        if not got:
            return None
    return None


def tested_tree(jobs):
    """The tree a run's `plan` job named, or None."""
    plan_job = [j for j in jobs if j.get("name") == "plan"]
    if len(plan_job) != 1 or plan_job[0].get("conclusion") != "success":
        return None
    trees = [m.group(1) for s in (plan_job[0].get("steps") or []) if s.get("conclusion") == "success"
             for m in [TREE_STEP.match(s.get("name") or "")] if m]
    return trees[0] if len(trees) == 1 else None


def green_kind(jobs, names, label):
    """Whether every job named is in the run once, green, on its macOS runner."""
    found = [[j for j in jobs if j.get("name") == n] for n in names]
    return all(len(f) == 1 and f[0].get("conclusion") == "success" and label in (f[0].get("labels") or []) for f in found if f)


def macos_green(kinds, repo, log):
    """-> ({name: the run it is green in}, sha, tree); nothing on any doubt."""
    env = os.environ
    token = env.get("PLAN_TOKEN") or ""
    hide = lambda s: s.replace(token, "<token>") if token else s
    sha, slug = env.get("GITHUB_SHA") or "", env.get("GITHUB_REPOSITORY") or ""
    if not token:
        log.append("no token for the lookup: every macOS leg runs")
        return {}, sha, ""
    if not HEX.fullmatch(sha) or not slug:
        log.append("no pushed commit or repository named: every macOS leg runs")
        return {}, sha, ""
    try:
        head, tree = git(repo, "rev-parse", "HEAD").strip(), git(repo, "rev-parse", "HEAD^{tree}").strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        log.append("git could not name the checkout (%s): every macOS leg runs" % type(e).__name__)
        return {}, sha, ""
    if head != sha:
        log.append("the checkout %s is not the pushed commit %s: every macOS leg runs" % (head, sha))
        return {}, sha, ""
    log.append("the pushed commit %s, tree %s" % (sha, tree))
    try:
        api = Api(env.get("GITHUB_API_URL") or "https://api.github.com", slug, token,
                  float(env.get("PLAN_API_TIMEOUT") or 20))
        listing = api.get("actions/workflows/%s/runs" % os.path.basename(WORKFLOW), head_sha=sha, per_page=100)
        runs = [x for x in listing["workflow_runs"]
                if x.get("head_sha") == sha and x.get("path") == WORKFLOW and x.get("status") == "completed"
                and x.get("conclusion") == "success" and x.get("event") in EVIDENCE_EVENTS]
        runs.sort(key=lambda x: -int(x["id"]))
        found = {}
        for x in runs[:MAX_RUNS]:
            rid = int(x["id"])
            jobs = run_jobs(api, rid)
            if jobs is None:
                log.append("%s run %d: its jobs listing falls short of its count, not relied on" % (x["event"], rid))
                continue
            t = tested_tree(jobs)
            if t != tree:
                log.append("%s run %d tested tree %s, not %s: not relied on" % (x["event"], rid, t or "(not named)", tree))
                continue
            for name, (_, _, label) in kinds.items():
                if name not in found and green_kind(jobs, [name], label):
                    found[name] = x
        return found, sha, tree
    except Exception as e:  # any failure of the lookup runs every macOS leg
        log.append("the lookup failed (%s: %s): every macOS leg runs" % (type(e).__name__, hide(str(e))))
        return {}, sha, ""


def trunk_cover(r, a):
    """The plan less the macOS legs and jobs already green at this commit, on the
    runner's own push to trunk; the plan as it was otherwise."""
    r["macos_covered"] = {}
    env = os.environ
    if not (a.event == "push" and env.get("GITHUB_EVENT_NAME") == "push" and env.get("GITHUB_REF") == "refs/heads/" + TRUNK):
        return r
    if r["tier"] != "full":
        r["log"].append("tier %s: no macOS leg is left" % r["tier"])
        return r
    kinds = macos_kinds(r)
    found, sha, tree = macos_green(kinds, a.repo or ROOT, r["log"])
    needs = workflow_jobs()
    covered, why = {}, {}
    for name, (job, leg, label) in kinds.items():
        x = found.get(name)
        if x is None:
            why[name] = ("no completed, successful pull_request or workflow_dispatch run of %s at this commit "
                         "tested this tree with it green on %s" % (os.path.basename(WORKFLOW), label))
            continue
        if leg is not None:
            left = [l for l in r["matrix"][output_name(job)] if leg_name(job, l) not in found]
            if not left:
                why[name] = "green in %s run %d, but %s would be left no leg" % (x["event"], int(x["id"]), job)
                continue
        elif [j for j in r["jobs"] if j != job and job in needs.get(j, [])]:
            why[name] = "green in %s run %d, but a chosen job needs %s" % (x["event"], int(x["id"]), job)
            continue
        covered[name] = {"job": job, "leg": leg, "label": label, "run": int(x["id"]), "event": x["event"],
                         "sha": sha, "tree": tree}
    for name, c in covered.items():
        if c["leg"] is None:
            r["jobs"] = [j for j in r["jobs"] if j != c["job"]]
        else:
            out = output_name(c["job"])
            r["matrix"][out] = [l for l in r["matrix"][out] if l != c["leg"]]
    server, slug = env.get("GITHUB_SERVER_URL") or "https://github.com", env.get("GITHUB_REPOSITORY") or ""
    lines = []
    for name in kinds:
        c = covered.get(name)
        if c:
            lines.append("skip %s: green in %s run %d at %s, tree %s (%s/%s/actions/runs/%d)" % (
                name, c["event"], c["run"], c["sha"], c["tree"], server, slug, c["run"]))
        else:
            lines.append("keep %s: %s" % (name, why[name]))
    r["log"] += lines
    summary = env.get("GITHUB_STEP_SUMMARY")
    if summary and lines:
        try:
            with open(summary, "a", encoding="utf-8") as f:
                f.write("### The trunk push's macOS legs\n\n" + "".join("- %s\n" % l for l in lines) + "\n")
        except OSError as e:
            r["log"].append("the step summary could not be written (%s)" % e)
    r["macos_covered"] = covered
    return r


def read_covered(out, tier, want_jobs):
    """The plan's `macos_covered`, checked: only in tier full, only a macOS leg of
    the tier's matrix or a whole macOS job of the tier, each named as GitHub names
    it, with the run, event, commit and tree it relied on."""
    try:
        covered = json.loads(out.get("macos_covered") or "{}")
    except ValueError:
        raise ValueError("the plan's macos_covered cannot be read (%r)" % out.get("macos_covered"))
    if not isinstance(covered, dict):
        raise ValueError("the plan's macos_covered is no object (%r)" % out.get("macos_covered"))
    hosts, matrix = job_hosts(), matrix_of(tier)
    for name, c in covered.items():
        if tier != "full":
            raise ValueError("%s covered in tier %s: only the full tier leaves a macOS leg" % (name, tier))
        if not isinstance(c, dict) or not isinstance(c.get("run"), int) or c.get("event") not in EVIDENCE_EVENTS \
                or not all(HEX.fullmatch(str(c.get(k) or "")) for k in ("sha", "tree")):
            raise ValueError("%s covered with no run it relied on (%r)" % (name, c))
        job, leg = c.get("job"), c.get("leg")
        if job not in want_jobs:
            raise ValueError("%s covered, but %s is no job of tier %s" % (name, job, tier))
        if leg is not None:
            ok = (job in MATRIX and hosts.get(job, (None,))[0] is None and leg in matrix.get(output_name(job), [])
                  and str(leg.get("os", "")).startswith("macos") and leg_name(job, leg) == name)
        else:
            jname, runs_on = hosts.get(job, (None, None))
            ok = job not in MATRIX and bool(runs_on) and runs_on.startswith("macos") and (jname or job) == name
        if not ok:
            raise ValueError("%s covered, but it is no macOS leg or job of tier %s" % (name, tier))
    return covered


def less_covered(matrix, covered):
    """A tier's matrices less the legs the plan left as covered."""
    gone = [(c["job"], c["leg"]) for c in covered.values() if c.get("leg") is not None]
    return {name: [l for l in legs if not any(output_name(j) == name and l == leg for j, leg in gone)]
            for name, legs in matrix.items()}


def main():
    argv = sys.argv[1:]
    if argv == ["verdict"]:
        sys.exit(verdict(json.loads(os.environ["NEEDS"])))
    if argv[:1] == ["classify"]:
        for p in argv[1:]:
            targets, why = classify(p)
            print("%s\t%s\t%s" % (p, "FULL" if targets == FULL else (" ".join(targets) or "prose"), why))
        return
    if argv[:1] != ["plan"]:
        die("usage: ci/tiers.py plan [options] | verdict | classify PATH...")
    env = os.environ.get
    ap = argparse.ArgumentParser(prog="ci/tiers.py plan")
    ap.add_argument("--event", default=env("EVENT"))
    ap.add_argument("--action", default=env("ACTION"))
    ap.add_argument("--label", default=env("LABEL"))
    ap.add_argument("--labels", default=env("LABELS"))
    ap.add_argument("--head-sha", default=env("HEAD_SHA"))
    ap.add_argument("--tier", default=env("IN_TIER") or None)
    ap.add_argument("--input", action="append", default=[], metavar="KEY=VALUE",
                    help="a dispatch input; the environment's IN_<KEY> are read too")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--paths-from")
    ap.add_argument("--repo")
    ap.add_argument("--github-output")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    a.inputs = {k[3:].lower(): v for k, v in os.environ.items() if k.startswith("IN_") and k != "IN_TIER"}
    for kv in a.input:
        if "=" not in kv:
            die("--input takes KEY=VALUE, not %r" % kv)
        k, v = kv.split("=", 1)
        a.inputs[k] = v
    r = trunk_cover(plan(a), a)
    for line in r["log"]:
        print("tiers: " + line, file=sys.stderr)
    if a.json:
        print(json.dumps({"tier": r["tier"], "jobs": r["jobs"], "matrix": r["matrix"], "macos_covered": r["macos_covered"]}))
        return
    out = "tier=%s\njobs=%s\n" % (r["tier"], json.dumps(r["jobs"]))
    for name, legs in r["matrix"].items():
        out += "%s=%s\n" % (name, json.dumps(legs, separators=(",", ":")))
    out += "macos_covered=%s\n" % json.dumps(r["macos_covered"], separators=(",", ":"))
    sys.stdout.write(out)
    if a.github_output:
        with open(a.github_output, "a", encoding="utf-8") as f:
            f.write(out)


if __name__ == "__main__":
    main()
