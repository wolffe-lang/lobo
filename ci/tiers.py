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
CLAUDE.md. Not prose, because the gauntlet reads it: docs/ (two pages are
generated and held to their tables, and the dist stages the rest),
CHANGELOG.md (the stamp and the release notes), README.md (the dist).
ci/tiers-test.py trips when a line of tools/ or tests/ that reads a file
starts naming a prose path.

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
    for name, legs in sorted(matrix_of(tier).items()):
        try:
            got = json.loads(out.get(name, "null"))
        except ValueError:
            got = out.get(name)
        if got != legs:
            print("tier: the plan's %s is %s; tier %s runs %s" % (name, json.dumps(got), tier, json.dumps(legs)))
            bad += 1
    print("tier %s: %d of %d job(s) chosen" % (tier, len(chosen), len(every)))
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
    r = plan(a)
    for line in r["log"]:
        print("tiers: " + line, file=sys.stderr)
    if a.json:
        print(json.dumps({"tier": r["tier"], "jobs": r["jobs"], "matrix": r["matrix"]}))
        return
    out = "tier=%s\njobs=%s\n" % (r["tier"], json.dumps(r["jobs"]))
    for name, legs in r["matrix"].items():
        out += "%s=%s\n" % (name, json.dumps(legs, separators=(",", ":")))
    sys.stdout.write(out)
    if a.github_output:
        with open(a.github_output, "a", encoding="utf-8") as f:
            f.write(out)


if __name__ == "__main__":
    main()
