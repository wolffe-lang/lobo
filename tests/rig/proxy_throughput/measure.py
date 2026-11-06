"""A loopback-only relative throughput witness; Python standard library only."""
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import re
import socket
import statistics
import subprocess
import sys
import time
import tempfile
import unittest
from unittest import mock


def rate(output):
    failures = re.search(r"^Failed requests:\s+(\d+)", output, re.M)
    non2xx = re.search(r"^Non-2xx responses:\s+(\d+)", output, re.M)
    requests = re.search(r"^Complete requests:\s+(\d+)", output, re.M)
    speed = re.search(r"^Requests per second:\s+(\d+(?:\.\d+)?)\s", output, re.M)
    if (failures is None or int(failures[1]) != 0 or
            (non2xx is not None and int(non2xx[1]) != 0) or
            requests is None or speed is None or not math.isfinite(float(speed[1])) or
            float(speed[1]) <= 0):
        raise ValueError("ApacheBench did not report successful, complete responses")
    return float(speed[1]), int(requests[1])


def ratio(rows, pairs=5):
    ref = [r["rate"] for r in rows if r["name"] == "reference"]
    head = [r["rate"] for r in rows if r["name"] == "head"]
    if (len(rows) != 2 * pairs or len(ref) != pairs or len(head) != pairs or
            any(not math.isfinite(r["rate"]) or r["rate"] <= 0 for r in rows)):
        raise ValueError(f"{pairs} complete pairs are required")
    return statistics.median(head) / statistics.median(ref)


def passes(rows, pairs=5):
    return ratio(rows, pairs) >= .9


def control_passes(rows, pairs=5):
    # Identical bytes must satisfy the existing 0.900 budget with
    # either label assigned to them; a favorable bias is unsound too.
    value = ratio(rows, pairs)
    return value >= .9 and 1 / value >= .9


def settings(system, requests=None, warmup=None, pairs=None, report_only=False, ci=False):
    mac = system == "Darwin" and ci
    out = dict(requests=requests if requests is not None else (1000 if mac else 20000),
               warmup=warmup if warmup is not None else (100 if mac else 2000),
               pairs=pairs if pairs is not None else 5,
               report_only=report_only or ci)
    if not 32 <= out["requests"] <= 1000000 or not 32 <= out["warmup"] <= 100000:
        raise ValueError("request/warmup counts outside the bounded c=32 rig shape")
    if not 1 <= out["pairs"] <= 25:
        raise ValueError("pairs must be 1..25")
    return out


def keepalive(output):
    value = re.search(r"^Keep-Alive requests:\s+(\d+)", output, re.M)
    if value is None or int(value[1]) <= 0:
        raise ValueError("ApacheBench did not confirm HTTP keep-alive")
    return int(value[1])


def host_snapshot():
    out = dict(system=platform.system(),platform=platform.platform())
    if platform.system() == "Darwin":
        keys = ["net.inet.ip.portrange.first", "net.inet.ip.portrange.last",
                "net.inet.ip.portrange.hifirst", "net.inet.ip.portrange.hilast",
                "net.inet.tcp.msl", "kern.ipc.somaxconn"]
        for key in keys:
            value = subprocess.run(["sysctl", "-n", key], capture_output=True, text=True)
            out[key] = value.stdout.strip() if value.returncode == 0 else value.stderr.strip()
        net = subprocess.run(["netstat", "-an", "-p", "tcp"], capture_output=True, text=True)
        out["time_wait"] = sum("TIME_WAIT" in line for line in net.stdout.splitlines())
        out["established"] = sum("ESTABLISHED" in line for line in net.stdout.splitlines())
    return out


class SimulatedNamespace:
    """A namespace TIME_WAIT table on a fake clock, for the unit rows only.

    Entries live 60 seconds and none are kept past the capacity. A drive
    adds 0.6 entries per request (13,200 per warm-up and measured cycle,
    about what a hosted runner showed) at 6,000 requests per second.
    """

    def __init__(self, capacity, per_request=.6, rate=6000.0):
        self.capacity, self.per_request, self.rate = capacity, per_request, rate
        self.now, self.entries, self.events, self.live = 1000.0, [], [], set()
        self.saturated = False

    def count(self):
        self.entries = [(expiry, n) for expiry, n in self.entries if expiry > self.now]
        return sum(n for _, n in self.entries)

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.events.append(("sleep", frozenset(self.live)))
        self.now += seconds

    def popen(self, args, **kwargs):
        process = mock.Mock()
        process.args = args
        self.live.add(id(process))
        process.poll.side_effect = lambda: None if id(process) in self.live else 0
        self.events.append(("launch", args[0]))
        return process

    def stop(self, process):
        if id(process) in self.live:
            self.live.discard(id(process))
            self.events.append(("stop", process.args[0]))

    def drive(self, port, count, raw_path=None):
        self.events.append(("drive", count))
        added = round(count * self.per_request)
        room = self.capacity - self.count()
        if added >= room:
            self.saturated = True
        self.entries.append((self.now + 60, min(added, room)))
        self.now += count / self.rate
        return self.rate, f"Keep-Alive requests: {count}\n"


class RatchetTests(unittest.TestCase):
    def rows(self, head):
        return [dict(round=i, name=name, rate=speed) for i in range(5)
                for name, speed in [("reference", 100), ("head", head)]]

    def test_boundary(self):
        self.assertTrue(passes(self.rows(90)))
        self.assertFalse(passes(self.rows(89.999)))

    def test_one_outlier_cannot_rescue_a_regression(self):
        rows = self.rows(80)
        rows[-1]["rate"] = 10000
        self.assertFalse(passes(rows))

    def test_incomplete_pairs_refused(self):
        with self.assertRaises(ValueError):
            ratio(self.rows(100)[:-1])

    def test_failed_or_non_successful_responses_refused(self):
        good = "Complete requests: 20000\nFailed requests: 0\nRequests per second: 123.45\n"
        self.assertEqual(rate(good), (123.45, 20000))
        for bad in [good.replace("requests: 0", "requests: 1"),
                    good + "Non-2xx responses: 2\n", "", good.replace("123.45", "0")]:
            with self.assertRaises(ValueError):
                rate(bad)

    def test_nonpositive_and_nonfinite_samples_refused(self):
        for value in [0, -1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                ratio(self.rows(value))
        with self.assertRaises(ValueError):
            ratio(self.rows(100) + [dict(name="other", rate=100)])

    def test_drive_rejects_failure_and_short_count(self):
        good = "Complete requests: 20000\nFailed requests: 0\nRequests per second: 123.45\n"
        with mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 7, "bad")):
            with self.assertRaises(RuntimeError):
                drive(1234, 20000)
        with mock.patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, good)):
            self.assertEqual(drive(1234, 20000)[0], 123.45)
            with self.assertRaises(ValueError):
                drive(1234, 19999)

    def test_dead_and_unready_servers_refused(self):
        process = mock.Mock()
        process.poll.return_value = 1
        with self.assertRaises(RuntimeError):
            wait_up(1234, process)
        process.poll.return_value = None
        with mock.patch.object(socket, "create_connection", side_effect=OSError("not up")), mock.patch.object(time, "sleep"):
            with self.assertRaises(RuntimeError):
                wait_up(1234, process)

    def test_cleanup_uses_recorded_process_and_waits(self):
        process = mock.Mock()
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired("server", 5), 0]
        stop(process)
        process.terminate.assert_called_once_with()
        process.kill.assert_called_once_with()
        self.assertEqual(process.wait.call_count, 2)
        ended = mock.Mock()
        ended.poll.return_value = 0
        stop(ended)
        ended.terminate.assert_not_called()

    def test_platform_shapes_are_explicit(self):
        self.assertEqual(settings("Linux"), dict(requests=20000,warmup=2000,pairs=5,report_only=False))
        self.assertEqual(settings("Darwin",ci=True), dict(requests=1000,warmup=100,pairs=5,report_only=True))
        self.assertEqual(settings("Darwin"), settings("Linux"))
        self.assertEqual(settings("Linux",ci=True), dict(requests=20000,warmup=2000,pairs=5,report_only=True))
        self.assertEqual(settings("Linux",requests=100000,pairs=7)["pairs"],7)
        for kwargs in [dict(requests=0),dict(warmup=31),dict(pairs=0),dict(pairs=26)]:
            with self.assertRaises(ValueError): settings("Linux",**kwargs)

    def test_ci_reporting_does_not_accept_invalid_measurements(self):
        for system in ["Linux", "Darwin"]:
            self.assertTrue(settings(system,ci=True)["report_only"])
            with self.assertRaises(ValueError):
                ratio(self.rows(0))
            with self.assertRaises(ValueError):
                rate("Complete requests: 1000\nFailed requests: 1\nRequests per second: 1.0\n")
            with self.assertRaises(ValueError):
                keepalive("Keep-Alive requests: 0\n")

    def test_keepalive_confirmation_required(self):
        self.assertEqual(keepalive("Keep-Alive requests: 1000\n"),1000)
        for raw in ["", "Keep-Alive requests: 0\n"]:
            with self.assertRaises(ValueError): keepalive(raw)

    def test_same_binary_control_uses_the_bar_in_both_directions(self):
        self.assertTrue(control_passes(self.rows(100)))
        self.assertTrue(control_passes(self.rows(90)))
        self.assertTrue(control_passes(self.rows(110)))
        self.assertFalse(control_passes(self.rows(89.999)))
        self.assertFalse(control_passes(self.rows(112)))

    def test_unsound_reference_self_prevents_candidate_judgement(self):
        for advisory in (False, True):
            with mock.patch(__name__ + "._sample_pairing", return_value=self.rows(80)) as sample, \
                 mock.patch(__name__ + ".binary_digest", side_effect=lambda path: ("1" if str(path) == "ref" else "2") * 64), \
                 mock.patch("builtins.print"):
                self.assertEqual(measure("ng", "ref", "head", "unused", report_only=advisory), 1)
                self.assertEqual(sample.call_count, 1)
                self.assertEqual(sample.call_args.args[1:3], ("ref", "ref"))

    def test_control_collection_failure_is_named_and_stops_judgement(self):
        with mock.patch(__name__ + "._sample_pairing", side_effect=RuntimeError("transport failed")) as sample, \
             mock.patch(__name__ + ".binary_digest", side_effect=lambda path: ("1" if str(path) == "ref" else "2") * 64), \
             mock.patch("builtins.print") as output:
            self.assertEqual(measure("ng", "ref", "head", "unused"), 1)
            self.assertEqual(sample.call_count, 1)
            self.assertTrue(any("[reference-self]" in str(c.args[0]) for c in output.call_args_list))

    def test_control_precedes_unchanged_candidate_bar(self):
        for speed, expected in ((90, 0), (89.999, 1)):
            with mock.patch(__name__ + "._sample_pairing", side_effect=[self.rows(100), self.rows(speed)]) as sample, \
                 mock.patch(__name__ + ".binary_digest", side_effect=lambda path: ("1" if str(path) == "ref" else "2") * 64), \
                 mock.patch("builtins.print"):
                self.assertEqual(measure("ng", "ref", "head", "unused"), expected)
                self.assertEqual([c.args[1:3] for c in sample.call_args_list], [("ref", "ref"), ("ref", "head")])
        with mock.patch(__name__ + "._sample_pairing", return_value=self.rows(100)) as sample, \
             mock.patch(__name__ + ".binary_digest", side_effect=lambda path: ("1" if str(path) == "ref" else "2") * 64), \
             mock.patch("builtins.print"):
            self.assertEqual(measure("ng", "ref", "head", "unused", control_only=True), 0)
            self.assertEqual(sample.call_count, 1)

    def test_every_drive_has_a_distinct_backend_process_and_port(self):
        parent = Path(os.environ.get("TMPDIR", "target"))
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            with mock.patch(__name__ + ".free_port", side_effect=[31001, 31002, 31003, 31004]), \
                 mock.patch(__name__ + ".wait_up"), mock.patch(__name__ + ".stop") as stop_child, \
                 mock.patch(__name__ + ".host_snapshot", return_value={}), \
                 mock.patch(__name__ + ".tcp_snapshot", return_value={"available": True, "tw": 0}), \
                 mock.patch(__name__ + ".binary_digest", side_effect=lambda path: ("1" if str(path) == "ref" else "2") * 64), \
                 mock.patch(__name__ + ".wait_tcp_quiet") as quiet, \
                 mock.patch(__name__ + ".drive", return_value=(100, "Keep-Alive requests: 32\n")), \
                 mock.patch.object(subprocess, "check_output", return_value="up"), \
                 mock.patch.object(subprocess, "Popen") as launch, mock.patch("builtins.print"):
                rows = _sample_pairing("ng", "ref", "head", directory, requests=32, warmup=32, pairs=1)
                self.assertEqual([r["backend_port"] for r in rows], [31001, 31003])
                self.assertEqual(sum(c.args[0][0] == "ng" for c in launch.call_args_list), 2)
                self.assertEqual(sum(c.args[0][0] in ("ref", "head") for c in launch.call_args_list), 2)
                self.assertGreaterEqual(stop_child.call_count, 4)
                self.assertEqual(quiet.call_count, 2)

    def test_tcp_diagnostics_distinguish_backend_ports(self):
        data = ("sl local remote st\n"
                "0: 0100007F:7919 0100007F:8000 06 rest\n"
                "1: 0100007F:8001 0100007F:791B 01 rest\n"
                "2: 0100007F:8002 0100007F:8003 06 rest\n")
        with mock.patch.object(Path, "exists", return_value=True), \
             mock.patch.object(Path, "read_text", return_value=data):
            self.assertEqual(backend_tcp_states({31001, 31003}),
                             dict(available=True, states={"31001": {"06": 1}, "31003": {"01": 1}}))
        with mock.patch.object(Path, "exists", return_value=True), \
             mock.patch.object(Path, "read_text", return_value="TCP: inuse 4 orphan 0 tw 22000 alloc 8 mem 0\n"):
            self.assertEqual(tcp_snapshot()["tw"], 22000)
        with mock.patch.object(Path, "exists", return_value=False):
            self.assertEqual(tcp_snapshot(), {"available": False})
            self.assertEqual(backend_tcp_states({31001}), {"available": False})

    def test_settling_is_bounded_and_observes_namespace_counts(self):
        with mock.patch(__name__ + ".time_wait_count", side_effect=[2, 1, 0]), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=262144), \
             mock.patch.object(time, "sleep") as sleep, mock.patch("builtins.print"):
            result = wait_tcp_quiet("unit", timeout=120)
            self.assertEqual((result["before"], result["after"]), (2, 0))
            self.assertGreaterEqual(result["elapsed_seconds"], 0)
            self.assertEqual(sleep.call_count, 2)
        with mock.patch(__name__ + ".time_wait_count", return_value=1), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=262144), \
             mock.patch.object(time, "monotonic", side_effect=[0, 121]), \
             mock.patch("builtins.print"):
            with self.assertRaisesRegex(RuntimeError, "tcp-settle"):
                wait_tcp_quiet("unit", timeout=120)

    def test_tcp_saturation_is_refused(self):
        check_tcp_capacity(262143, 262144)
        with self.assertRaisesRegex(RuntimeError, "tcp-state"):
            check_tcp_capacity(262144, 262144)

    def test_drive_settle_threshold_is_three_quarters_of_capacity(self):
        self.assertEqual(DRIVE_SETTLE_FRACTION, .75)
        self.assertIsNone(drive_settle_target(36152, 13000, 65536))
        self.assertEqual(drive_settle_target(36153, 13000, 65536), 36152)
        self.assertIsNone(drive_settle_target(0, None, 65536))
        self.assertIsNone(drive_settle_target(65535, 13000, None))
        self.assertIsNone(drive_settle_target(150000, 15000, 262144))
        self.assertEqual(drive_settle_target(1, 49152, 65536), 0)
        with self.assertRaisesRegex(RuntimeError, r"^\[tcp-settle\] .*49153.*0\.75"):
            drive_settle_target(0, 49153, 65536)

    def test_per_drive_settle_reaches_its_target_or_refuses_by_name(self):
        with mock.patch(__name__ + ".time_wait_count", side_effect=[40000, 38000, 36000]), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=65536), \
             mock.patch.object(time, "sleep") as sleep, mock.patch("builtins.print"):
            result = wait_tcp_quiet("before drive unit", target=36152)
            self.assertEqual((result["before"], result["after"], result["target"], result["status"]),
                             (40000, 36000, 36152, "settled"))
            self.assertEqual(sleep.call_count, 2)
        with mock.patch(__name__ + ".time_wait_count", return_value=40000), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=65536), \
             mock.patch.object(time, "monotonic", side_effect=[0, 121]), \
             mock.patch("builtins.print"):
            with self.assertRaisesRegex(RuntimeError, r"^\[tcp-settle\] before drive unit"):
                wait_tcp_quiet("before drive unit", timeout=120, target=36152)
        with mock.patch(__name__ + ".time_wait_count", return_value=65536), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=65536), \
             mock.patch("builtins.print"):
            with self.assertRaisesRegex(RuntimeError, r"^\[tcp-state\]"):
                wait_tcp_quiet("before drive unit", target=36152)

    def simulate_pairing(self, capacity):
        fake = SimulatedNamespace(capacity)
        parent = Path(os.environ.get("TMPDIR", "target"))
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory, \
             mock.patch(__name__ + ".free_port", side_effect=itertools.count(31001)), \
             mock.patch(__name__ + ".wait_up"), mock.patch(__name__ + ".stop", fake.stop), \
             mock.patch(__name__ + ".host_snapshot", return_value={}), \
             mock.patch(__name__ + ".tcp_snapshot", lambda: dict(available=True, tw=fake.count())), \
             mock.patch(__name__ + ".time_wait_count", fake.count), \
             mock.patch(__name__ + ".tcp_capacity_limit", return_value=capacity), \
             mock.patch(__name__ + ".backend_tcp_states", return_value={"available": False}), \
             mock.patch(__name__ + ".binary_digest", return_value="1" * 64), \
             mock.patch(__name__ + ".drive", fake.drive), \
             mock.patch.object(subprocess, "check_output", return_value="up"), \
             mock.patch.object(subprocess, "Popen", fake.popen), \
             mock.patch.object(time, "sleep", fake.sleep), \
             mock.patch.object(time, "monotonic", fake.monotonic), \
             mock.patch("builtins.print"):
            rows = _sample_pairing("ng", "ref", "ref", directory)
        return fake, rows

    def test_a_whole_pairing_completes_in_a_65536_namespace(self):
        fake, rows = self.simulate_pairing(65536)
        self.assertEqual(len(rows), 10)
        self.assertFalse(fake.saturated)
        self.assertLessEqual(max(r["tcp_after"]["tw"] for r in rows), 49152)
        settled = [r["tcp_guard"] for r in rows if r["tcp_guard"]["status"] == "settled"]
        self.assertGreaterEqual(len(settled), 2)
        self.assertTrue(all(g["settle"]["after"] <= g["target"] < g["count"] for g in settled))

    def test_a_262144_namespace_never_settles_between_drives(self):
        fake, rows = self.simulate_pairing(262144)
        self.assertEqual(len(rows), 10)
        self.assertFalse(fake.saturated)
        self.assertEqual([r["tcp_guard"]["status"] for r in rows], ["room"] * 10)

    def test_no_settle_falls_inside_a_timed_drive(self):
        fake, rows = self.simulate_pairing(65536)
        sleeps = [i for i, event in enumerate(fake.events) if event[0] == "sleep"]
        drives = [i for i, event in enumerate(fake.events) if event[0] == "drive"]
        self.assertEqual(len(drives), 20)
        # Settles do happen between drive cycles, not only around the pairing.
        self.assertTrue([i for i in sleeps if drives[0] < i < drives[-1]])
        # A settle waits only while no owned child (backend or server) runs.
        self.assertEqual([fake.events[i][1] for i in sleeps], [frozenset()] * len(sleeps))
        # And never between a drive's warm-up and its measured requests.
        for warm, timed in zip(drives[::2], drives[1::2]):
            self.assertEqual((fake.events[warm][1], fake.events[timed][1]), (2000, 20000))
            self.assertEqual([i for i in sleeps if warm < i < timed], [])

    def test_digest_not_name_controls_symmetric_judgement(self):
        parent = Path(os.environ.get("TMPDIR", "target"))
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory)
            (root / "a").mkdir(); (root / "b").mkdir()
            left, right = root / "a/bin", root / "b/bin"
            left.write_bytes(b"same bytes"); right.write_bytes(b"same bytes")
            self.assertEqual(binary_digest(left), binary_digest(right))
            with mock.patch(__name__ + "._sample_pairing", side_effect=[self.rows(100), self.rows(160)]), mock.patch("builtins.print"):
                self.assertEqual(measure("ng", left, right, "unused"), 1)
            right.write_bytes(b"different bytes")
            self.assertNotEqual(binary_digest(left), binary_digest(right))
            for speed, expected in ((160, 0), (90, 0), (89.999, 1)):
                with mock.patch(__name__ + "._sample_pairing", side_effect=[self.rows(100), self.rows(speed)]), mock.patch("builtins.print"):
                    self.assertEqual(measure("ng", left, right, "unused"), expected)

    def test_pair_count_is_not_hardcoded(self):
        rows = [dict(name=name,rate=value) for _ in range(7)
                for name,value in [("reference",100),("head",90)]]
        self.assertTrue(passes(rows,7))
        with self.assertRaises(ValueError): ratio(rows,5)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_up(port, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("server exited before listening")
        try:
            with socket.create_connection(("127.0.0.1", port), .1):
                return
        except OSError:
            time.sleep(.05)
    raise RuntimeError("server did not listen within five seconds")


def stop(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def drive(port, count, raw_path=None):
    result = subprocess.run(["ab", "-k", "-n", str(count), "-c", "32",
                             f"http://127.0.0.1:{port}/body"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=45)
    if raw_path is not None:
        Path(raw_path).write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f"ApacheBench exited {result.returncode}: {result.stdout[-1000:]}")
    speed, got = rate(result.stdout)
    if got != count:
        raise ValueError(f"ApacheBench completed {got}, expected {count}")
    return speed, result.stdout

def binary_digest(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tcp_capacity_limit():
    path = Path("/proc/sys/net/ipv4/tcp_max_tw_buckets")
    return int(path.read_text().strip()) if path.exists() else None


def check_tcp_capacity(current, limit):
    if limit is None:
        return
    if current is None:
        raise RuntimeError("[tcp-state] namespace TIME_WAIT count unavailable")
    if current >= limit:
        raise RuntimeError(f"[tcp-state] namespace TIME_WAIT {current} reached capacity {limit}; pairing refused")


# A drive starts only with room for one more drive's TIME_WAIT entries
# under this fraction of the kernel-reported capacity. The other quarter
# is margin for a drive larger than the largest measured one: 16,384
# entries at a hosted runner's 65,536, more than a whole drive there.
DRIVE_SETTLE_FRACTION = .75


def drive_settle_target(current, increment, limit, fraction=DRIVE_SETTLE_FRACTION):
    """The count a drive must wait for, or None when it already has room.

    Room is the count plus one drive's measured increment at or under the
    fraction of capacity. With no reported capacity, or no drive measured
    yet (a pairing's first drive starts from its settled zero), there is
    nothing to predict. An increment no wait could make room for refuses.
    """
    if limit is None or increment is None:
        return None
    threshold = math.floor(fraction * limit)
    if current + increment <= threshold:
        return None
    if increment > threshold:
        raise RuntimeError(f"[tcp-settle] one drive adds {increment} TIME_WAIT entries, more than "
                           f"{fraction} of capacity {limit} ({threshold}); pairing refused")
    return threshold - increment


def time_wait_count():
    snapshot = tcp_snapshot()
    if snapshot.get("available") and "tw" in snapshot:
        return snapshot["tw"]
    if platform.system() == "Darwin":
        result = subprocess.run(["netstat", "-an", "-p", "tcp"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return sum("TIME_WAIT" in line.split() for line in result.stdout.splitlines())
    raise RuntimeError("[tcp-settle] namespace TIME_WAIT is not observable")


def wait_tcp_quiet(label, timeout=120, artifact=None, target=0, detail=None):
    """Observe actual namespace quietness, outside the timed AB drives.

    Around a pairing the target is zero. Before a drive it is the room
    one more drive needs (drive_settle_target), with the prediction's
    inputs in detail. The same bound, refusals and record apply to both.
    """
    began = time.monotonic()
    limit = tcp_capacity_limit()
    before = None
    goal = "" if target == 0 else f" to {target}"

    def finish(after, now, status):
        result = dict(label=label, before=before, after=after, target=target, elapsed_seconds=now - began,
                      ceiling_seconds=timeout, capacity_limit=limit, status=status, **(detail or {}))
        if artifact is not None:
            Path(artifact).write_text(json.dumps(result, indent=2))
        print("lobo-proxy-throughput: TCP SETTLE " + json.dumps(result), flush=True)
        return result

    try:
        current = before = time_wait_count()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        finish(None, time.monotonic(), "unavailable")
        raise
    noticed = began - 10
    while True:
        now = time.monotonic()
        try:
            check_tcp_capacity(current, limit)
        except RuntimeError:
            finish(current, now, "saturated")
            raise
        if current <= target:
            return finish(current, now, "settled")
        if now - began >= timeout:
            finish(current, now, "timeout")
            raise RuntimeError(f"[tcp-settle] {label} did not settle{goal} in {timeout} seconds; pairing refused and no further timed drive allowed")
        if now - noticed >= 10:
            print(f"lobo-proxy-throughput: settling {label}{goal}: namespace TIME_WAIT={current} elapsed={now - began:.1f}", flush=True)
            noticed = now
        time.sleep(1)
        try:
            current = time_wait_count()
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
            finish(None, time.monotonic(), "unavailable")
            raise


def settle_before_drive(label, limit, cycle_start, increment, artifact=None):
    """Make room for one drive before its backend starts.

    The caller runs this with every owned child stopped, so no settle can
    fall inside a warm-up or a timed window. The increment is the largest
    growth of any earlier drive cycle of the pairing (from one guard to
    the next); the first cycle grows from the pairing's settled zero, so
    its growth is exact. The returned record's start is the count the
    next cycle grows from.
    """
    if limit is None:
        return dict(status="no capacity reported")
    current = time_wait_count()
    if cycle_start is not None:
        grown = current - cycle_start
        increment = grown if increment is None else max(increment, grown)
    guard = dict(count=current, increment=increment, fraction=DRIVE_SETTLE_FRACTION,
                 threshold=math.floor(DRIVE_SETTLE_FRACTION * limit), capacity_limit=limit)
    target = drive_settle_target(current, increment, limit)
    if True:  # ws77 plant: the per-drive settle skipped
        guard.update(status="room", start=current)
        return guard
    settled = wait_tcp_quiet("before drive " + label, artifact=artifact, target=target,
                             detail=dict(increment=increment, fraction=DRIVE_SETTLE_FRACTION,
                                         threshold=guard["threshold"]))
    guard.update(status="settled", target=target, start=settled["after"], settle=settled)
    return guard


def verify_binary_digests(reference, head, expected):
    current = dict(reference=binary_digest(reference), head=binary_digest(head))
    if current != expected:
        raise RuntimeError("[binary-identity] binary bytes changed during the pairing; no ratio judged")


def tcp_snapshot():
    """Fast Linux socket counters; diagnostic data, never an acceptance gate."""
    path = Path("/proc/net/sockstat")
    if not path.exists():
        return {"available": False}
    for line in path.read_text().splitlines():
        if line.startswith("TCP:"):
            fields = line.split()[1:]
            return dict(available=True, **{fields[i]: int(fields[i + 1]) for i in range(0, len(fields), 2)})
    return {"available": False}


def backend_tcp_states(ports):
    """Count procfs TCP entries by the observed backend port after sampling.

    This potentially larger read is outside all timed drives. Local and
    remote matches are counted as entries, not claimed as distinct flows.
    """
    path = Path("/proc/net/tcp")
    if not path.exists():
        return {"available": False}
    ports = set(ports)
    counts = {str(port): {} for port in ports}
    for line in path.read_text().splitlines()[1:]:
        fields = line.split()
        local = int(fields[1].rsplit(":", 1)[1], 16)
        remote = int(fields[2].rsplit(":", 1)[1], 16)
        for port in {local, remote} & ports:
            state = fields[3]
            row = counts[str(port)]
            row[state] = row.get(state, 0) + 1
    return dict(available=True, states=counts)


def _sample_pairing(nginx, reference, head, scratch, requests=20000, warmup=2000, pairs=5,
                    backend_lifetime="fresh", report_only=False):
    # The gate isolates every drive with a fresh backend and destination
    # port. Other lifetimes are causal diagnostics, not CLI waiver switches.
    if backend_lifetime not in ("persistent", "restart-same-port", "fresh"):
        raise ValueError("unknown backend lifetime")
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "logs").mkdir(exist_ok=True)
    (scratch / "body").write_bytes(b"PROXIED-BODY-16\n")
    identities = dict(reference=binary_digest(reference), head=binary_digest(head))
    limit = tcp_capacity_limit()
    parameters = dict(requests=requests, warmup=warmup, pairs=pairs, backend_lifetime=backend_lifetime,
                      report_only=report_only, binary_sha256=identities, tcp_max_tw_buckets=limit,
                      settle_ceiling_seconds=120, drive_settle_fraction=DRIVE_SETTLE_FRACTION,
                      tcp_settle_scope="namespace before and after pairing, and before any drive whose "
                                       "measured increment would pass the fraction of capacity")
    print("lobo-proxy-throughput: binary SHA256 " + json.dumps(identities), flush=True)
    (scratch / "parameters.json").write_text(json.dumps(parameters, indent=2))
    (scratch / "host-before.json").write_text(json.dumps(host_snapshot(), indent=2))
    print("lobo-proxy-throughput: shape " + json.dumps(parameters), flush=True)
    children, rows, files = [], [], []
    used_ports = set()
    backend = None
    namespace_ready = False
    backend_port = None if backend_lifetime == "fresh" else free_port()
    cycle_start, increment = None, None

    def launch(args, label):
        logfile = open(scratch / (label + ".stderr"), "w")
        files.append(logfile)
        process = subprocess.Popen(args, stdout=logfile, stderr=logfile)
        children.append(process)
        return process

    try:
        if backend_lifetime == "fresh":
            wait_tcp_quiet("before " + str(scratch), artifact=scratch / "settle-before.json")
        namespace_ready = True
        for round_ in range(pairs):
            order = [("reference", reference), ("head", head)]
            if round_ % 2:
                order.reverse()
            for name, binary in order:
                label = f"{name}-{round_}"
                # Every owned child is stopped here, before this drive's
                # backend starts: outside the warm-up and the timed window.
                if backend_lifetime == "fresh":
                    guard = settle_before_drive(f"{label} of {scratch}", limit, cycle_start, increment,
                                                artifact=scratch / ("settle-" + label + ".json"))
                    cycle_start, increment = guard.get("start"), guard.get("increment")
                else:
                    guard = dict(status="no settle: diagnostic backend lifetime")
                if backend is None:
                    if backend_lifetime == "fresh":
                        for _ in range(100):
                            candidate = free_port()
                            if candidate not in used_ports:
                                backend_port = candidate
                                break
                        else:
                            raise RuntimeError("no distinct backend port available")
                    used_ports.add(backend_port)
                    conf = scratch / ("backend-" + label + ".conf")
                    conf.write_text(f"daemon off; master_process off; pid {scratch}/backend.pid; "
                                    f"error_log {scratch}/backend.log; events {{worker_connections 2048;}} "
                                    f"http {{access_log off; server {{listen 127.0.0.1:{backend_port}; root {scratch};}}}}")
                    backend = launch([nginx, "-p", str(scratch), "-c", str(conf)], "backend-" + label)
                    wait_up(backend_port, backend)
                before = tcp_snapshot()
                check_tcp_capacity(before.get("tw"), limit)
                port = free_port()
                conf = scratch / (label + ".conf")
                conf.write_text(f"pid {scratch}/{name}.pid; http {{access_log off; "
                                f"server {{listen 127.0.0.1:{port}; location / {{"
                                f"proxy_pass http://127.0.0.1:{backend_port};}}}}}}")
                process = launch([binary, "serve", "-p", str(scratch), "-c", str(conf)], label)
                wait_up(port, process)
                print(f"lobo-proxy-throughput: drive {name} round={round_} backend={backend_port} warmup={warmup} measured={requests}", flush=True)
                drive(port, warmup, scratch / (label + "-warmup.ab"))
                speed, raw = drive(port, requests, scratch / (label + ".ab"))
                row = dict(round=round_, name=name, rate=speed, keepalive_requests=keepalive(raw),
                           backend_port=backend_port, tcp_before=before, tcp_after=tcp_snapshot(),
                           tcp_guard=guard)
                rows.append(row)
                print("lobo-proxy-throughput: " + json.dumps(row), flush=True)
                check_tcp_capacity(row["tcp_after"].get("tw"), limit)
                stop(process)
                if backend_lifetime != "persistent":
                    stop(backend)
                    backend = None
        (scratch / "measurements.json").write_text(json.dumps(rows, indent=2))
        states = backend_tcp_states(used_ports)
        (scratch / "backend-tcp-states.json").write_text(json.dumps(states, indent=2))
        print("lobo-proxy-throughput: backend TCP entries " + json.dumps(states), flush=True)
        print(subprocess.check_output(["uptime"], text=True).strip(), flush=True)
        (scratch / "host-after.json").write_text(json.dumps(host_snapshot(), indent=2))
        return rows
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired):
        (scratch / "host-failure.json").write_text(json.dumps(host_snapshot(), indent=2))
        (scratch / "measurements-partial.json").write_text(json.dumps(rows, indent=2))
        raise
    finally:
        for process in reversed(children):
            stop(process)
        for file in files:
            file.close()
        if namespace_ready and backend_lifetime == "fresh":
            wait_tcp_quiet("after " + str(scratch), artifact=scratch / "settle-after.json")


def _report_pairing(rows, pairs, label, report_only=False, control=False):
    for name in ("reference", "head"):
        speeds = [r["rate"] for r in rows if r["name"] == name]
        print(f"lobo-proxy-throughput: {label} {name}: median {statistics.median(speeds):.2f} req/s [{min(speeds):.2f}, {max(speeds):.2f}]", flush=True)
    value = ratio(rows, pairs)
    good = control_passes(rows, pairs) if control else passes(rows, pairs)
    advisory = report_only and not control
    verdict = "REPORTED" if advisory else ("ok" if good else "FAILED")
    print(f"lobo-proxy-throughput: {verdict} — {label} head/reference {value:.3f}x (bar 0.900x{' both control directions' if control else ' advisory' if advisory else ''})", flush=True)
    paired = [next(r["rate"] for r in rows if r["round"] == i and r["name"] == "head") /
              next(r["rate"] for r in rows if r["round"] == i and r["name"] == "reference") for i in range(pairs)]
    print("lobo-proxy-throughput: paired ratios " + json.dumps(paired), flush=True)
    return 0 if advisory or good else 1


def measure(nginx, reference, head, scratch, requests=20000, warmup=2000, pairs=5,
            report_only=False, control_only=False):
    # Calibration is never advisory, including when CI only reports
    # the candidate ratio. Do not judge a candidate with an unsound rig.
    root = Path(scratch)
    identities = dict(reference=binary_digest(reference), head=binary_digest(head))
    print("lobo-proxy-throughput: requested binary SHA256 " + json.dumps(identities), flush=True)
    try:
        control_rows = _sample_pairing(nginx, reference, reference, root / "reference-self",
                                       requests, warmup, pairs)
        verify_binary_digests(reference, head, identities)
        calibrated = _report_pairing(control_rows, pairs, "[reference-self]", control=True) == 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"lobo-proxy-throughput: FAILED — [reference-self] collection failed: {error}; candidate not judged", flush=True)
        return 1
    if not calibrated:
        print("lobo-proxy-throughput: REFUSED — reference-self instrument check failed; candidate not judged", flush=True)
        return 1
    if control_only:
        return 0
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"lobo-proxy-throughput: CI MEASUREMENT — fresh backend/port per drive and bounded recorded TCP settling per pairing and before any drive that would pass {DRIVE_SETTLE_FRACTION} of capacity; SHA256 identity governs symmetric controls; reference-self calibration and saturation refusal are mandatory and fatal; only the candidate ratio remains advisory; transport, application, incomplete and non-keepalive failures remain fatal", flush=True)
    if platform.system() == "Darwin" and report_only:
        print("lobo-proxy-throughput: macOS CI uses its bounded short request window; calibration remains mandatory", flush=True)
    rows = _sample_pairing(nginx, reference, head, root / "comparison", requests, warmup, pairs,
                           report_only=report_only)
    verify_binary_digests(reference, head, identities)
    identical = identities["reference"] == identities["head"]
    return _report_pairing(rows, pairs, "[same-binary]" if identical else "comparison", report_only, control=identical)


def main():
    if sys.argv[1:] == ["--self-test"]:
        unittest.main(argv=[sys.argv[0]])
    parser=argparse.ArgumentParser()
    parser.add_argument("nginx"); parser.add_argument("reference"); parser.add_argument("head"); parser.add_argument("scratch")
    parser.add_argument("--requests",type=int); parser.add_argument("--warmup",type=int); parser.add_argument("--pairs",type=int)
    parser.add_argument("--report-only",action="store_true")
    parser.add_argument("--control-only",action="store_true")
    args=parser.parse_args()
    return measure(args.nginx,args.reference,args.head,args.scratch,control_only=args.control_only,
                   **settings(platform.system(),args.requests,args.warmup,args.pairs,args.report_only,ci=os.environ.get("GITHUB_ACTIONS")=="true"))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"lobo-proxy-throughput: FAILED — {error}", file=sys.stderr, flush=True)
        sys.exit(1)
