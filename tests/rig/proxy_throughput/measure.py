"""A loopback-only relative throughput witness; Python standard library only."""
import json
import math
from pathlib import Path
import re
import socket
import statistics
import subprocess
import sys
import time
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


def ratio(rows):
    ref = [r["rate"] for r in rows if r["name"] == "reference"]
    head = [r["rate"] for r in rows if r["name"] == "head"]
    if (len(rows) != 10 or len(ref) != 5 or len(head) != 5 or
            any(not math.isfinite(r["rate"]) or r["rate"] <= 0 for r in rows)):
        raise ValueError("five complete pairs are required")
    return statistics.median(head) / statistics.median(ref)


def passes(rows):
    return ratio(rows) >= .9


class RatchetTests(unittest.TestCase):
    def rows(self, head):
        return [dict(name=name, rate=speed) for _ in range(5)
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


def drive(port, count):
    result = subprocess.run(["ab", "-k", "-n", str(count), "-c", "32",
                             f"http://127.0.0.1:{port}/body"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, timeout=45)
    if result.returncode:
        raise RuntimeError(f"ApacheBench exited {result.returncode}: {result.stdout[-1000:]}")
    speed, got = rate(result.stdout)
    if got != count:
        raise ValueError(f"ApacheBench completed {got}, expected {count}")
    return speed, result.stdout

def measure(nginx, reference, head, scratch):
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "logs").mkdir(exist_ok=True)
    (scratch / "body").write_bytes(b"PROXIED-BODY-16\n")
    backend_port = free_port()
    conf = scratch / "backend.conf"
    conf.write_text(f"daemon off; master_process off; pid {scratch}/backend.pid; "
                    f"error_log {scratch}/backend.log; events {{worker_connections 2048;}} "
                    f"http {{access_log off; server {{listen 127.0.0.1:{backend_port}; root {scratch};}}}}")
    children = []
    rows = []
    files = []

    def launch(args, label):
        logfile = open(scratch / (label + ".stderr"), "w")
        files.append(logfile)
        process = subprocess.Popen(args, stdout=logfile, stderr=logfile)
        children.append(process)
        return process


    try:
        backend = launch([nginx, "-p", str(scratch), "-c", str(conf)], "backend")
        wait_up(backend_port, backend)
        for round_ in range(5):
            order = [("reference", reference), ("head", head)]
            if round_ % 2:
                order.reverse()
            for name, binary in order:
                port = free_port()
                conf = scratch / (name + ".conf")
                conf.write_text(f"pid {scratch}/{name}.pid; http {{access_log off; "
                                f"server {{listen 127.0.0.1:{port}; location / {{"
                                f"proxy_pass http://127.0.0.1:{backend_port};}}}}}}")
                process = launch([binary, "serve", "-p", str(scratch), "-c", str(conf)], name)
                wait_up(port, process)
                drive(port, 2000)
                speed, raw = drive(port, 20000)
                (scratch / f"{name}-{round_}.ab").write_text(raw)
                row = dict(round=round_, name=name, rate=speed)
                rows.append(row)
                print("lobo-proxy-throughput: " + json.dumps(row), flush=True)
                stop(process)
        (scratch / "measurements.json").write_text(json.dumps(rows, indent=2))
        print(subprocess.check_output(["uptime"], text=True).strip(), flush=True)
        for name in ["reference", "head"]:
            speeds = [r["rate"] for r in rows if r["name"] == name]
            print(f"lobo-proxy-throughput: {name}: median {statistics.median(speeds):.2f} "
                  f"req/s [{min(speeds):.2f}, {max(speeds):.2f}]", flush=True)
        value = ratio(rows)
        verdict = "ok" if passes(rows) else "FAILED"
        print(f"lobo-proxy-throughput: {verdict} — head/reference {value:.3f}x "
              "(bar 0.900x, this machine's own shape)", flush=True)
        return 0 if passes(rows) else 1
    finally:
        for process in reversed(children):
            stop(process)
        for file in files:
            file.close()


def main():
    if sys.argv[1:] == ["--self-test"]:
        unittest.main(argv=[sys.argv[0]])
    if len(sys.argv) != 5:
        raise ValueError("expected nginx, reference, head and scratch paths")
    return measure(*sys.argv[1:])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"lobo-proxy-throughput: FAILED — {error}", file=sys.stderr, flush=True)
        sys.exit(1)
