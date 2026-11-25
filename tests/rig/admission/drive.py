"""Loopback admission and connection-counter witnesses; standard library only."""
import argparse
import os
from pathlib import Path
import re
import resource
import select
import signal
import socket
import ssl
import subprocess
import threading
import time


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def until(predicate, description, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        value = predicate()
        if value:
            return value
        time.sleep(.01)
    raise AssertionError("deadline waiting for " + description)


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    else:
        process.wait()


class Server:
    def __init__(self, binary, directory, oracle=False, workers=1, reuseport=False,
                 connections=16, nofile=None, extra_plain=False, tls=False, control_unix=False):
        self.binary = str(Path(binary).resolve())
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.port = port()
        self.extra_port = port() if extra_plain else None
        self.tls_port = port() if tls else None
        self.master = workers > 1 or (not oracle and os.geteuid() == 0)
        self.oracle = oracle
        self.sockets = []
        self.log = self.directory / "server.log"
        self.config = self.directory / "server.conf"
        root = self.directory / "html"
        root.mkdir(exist_ok=True)
        (root / "index.html").write_text("ADMISSION\n")
        with (root / "big.bin").open("wb") as stream:
            stream.truncate(24 * 1024 * 1024)
        common = (f"worker_processes {workers};\npid {self.directory}/server.pid;\n"
                  f"events {{ worker_connections {connections}; }}\n")
        listen = f"127.0.0.1:{self.port}" + (" reuseport" if reuseport else "")
        if oracle:
            text = "daemon off;\nerror_log stderr notice;\n" + common
            http = "access_log off;"
            command = [self.binary, "-p", str(self.directory), "-c", str(self.config)]
        else:
            control_at = f"unix:{self.directory}/ctl.sock" if control_unix else "127.0.0.1:0"
            text = common + f"control {control_at};\n"
            if os.geteuid() == 0:
                text += "user root;\n"
            http = "metrics on;"
            command = [self.binary, "serve", "-p", str(self.directory), "-c", str(self.config)]
        listeners = f"listen {listen};"
        if extra_plain:
            listeners += f" listen 127.0.0.1:{self.extra_port};"
        if tls:
            fixture = Path(__file__).resolve().parents[3] / "tests/tls/fixtures"
            listeners += (f" listen 127.0.0.1:{self.tls_port} ssl;"
                          f" ssl_certificate {fixture}/fullchain.pem;"
                          f" ssl_certificate_key {fixture}/leaf.key; ssl_protocols TLSv1.3;")
        text += f"http {{ {http} server {{ {listeners} root {root}; }} }}\n"
        self.config.write_text(text)
        def limit():
            resource.setrlimit(resource.RLIMIT_NOFILE, (nofile, nofile))
        with self.log.open("wb") as output:
            self.process = subprocess.Popen(command, stdout=output, stderr=output,
                                            preexec_fn=limit if nofile is not None else None)
        try:
            if oracle:
                def worker_pids():
                    return [int(pid) for pid in re.findall(r"start worker process ([0-9]+)", self.log.read_text())]
                until(lambda: len(worker_pids()) == workers, "oracle workers")
                # A fork notice is not readiness. Direct a warm-up to every
                # worker, with only that worker running; all pids come from
                # this server's own log. No scheduling-time assertion.
                pids = worker_pids()
                for active in pids:
                    paused = [pid for pid in pids if pid != active]
                    try:
                        for pid in paused:
                            os.kill(pid, signal.SIGSTOP)
                        self.fetch("/index.html")
                    finally:
                        for pid in paused:
                            os.kill(pid, signal.SIGCONT)
            else:
                pattern = r"generation-activated gen=1 .*worker=[0-9]+" if self.master else r"generation-activated gen=1"
                until(lambda: len(re.findall(pattern, self.log.read_text())) >= workers,
                      "lobo workers")
                until(lambda: (f"worker {workers}: serving " in self.status()) if self.master
                      else ("generation 1: current live=0" in self.status()), "lobo control ready")
        except BaseException:
            self.close()
            raise

    def connect(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        self.sockets.append(sock)
        return sock

    def fetch(self, path):
        with socket.create_connection(("127.0.0.1", self.port), timeout=5) as sock:
            sock.sendall(f"GET {path} HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n".encode())
            data = b""
            while True:
                piece = sock.recv(65536)
                if not piece:
                    break
                data += piece
            assert data.startswith(b"HTTP/1.1 200"), data[:100]
            return data.split(b"\r\n\r\n", 1)[1].decode()

    def status(self):
        value = subprocess.run([self.binary, "status", "-p", str(self.directory),
                                "-c", str(self.config)], capture_output=True,
                               text=True, timeout=5)
        return value.stdout if value.returncode == 0 else ""

    def release(self):
        for sock in self.sockets:
            sock.close()
        self.sockets.clear()
        if not self.oracle:
            until(lambda: "live=0" in self.status() and "live=1" not in self.status(),
                  "connections released")

    def downloads(self, count):
        result = ""
        for _ in range(count):
            began = time.perf_counter()
            sock = self.connect()
            sock.sendall(b"GET /big.bin HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
            try:
                data = b""
                while b"\r\n\r\n" not in data:
                    piece = sock.recv(2048)
                    if not piece:
                        break
                    data += piece
                result += "2" if data.startswith(b"HTTP/1.1 200 ") else "1"
            except (ConnectionResetError, BrokenPipeError):
                result += "1"
            except TimeoutError as error:
                raise AssertionError(f"download {len(result) + 1} timed out; prefix={result}; log={self.log}") from error
            self.last_download_ms = (time.perf_counter() - began) * 1000
        return result

    def close(self):
        for sock in self.sockets:
            sock.close()
        self.sockets.clear()
        stop(self.process)


def sample(body, name):
    match = re.search(r"^" + re.escape(name) + r" ([0-9]+)$", body, re.M)
    assert match is not None, "missing series " + name
    return int(match[1])


def admission(binary, directory):
    # 28 is the same-host oracle's measured capacity, not a claim that
    # its own shared-listener scheduling is deterministic on every take.
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_before = usage.ru_utime + usage.ru_stime
    server = Server(binary, directory / "lobo", workers=2)
    try:
        mapping = server.downloads(29)
        print("admission map: lobo=" + mapping + " oracle-capacity=28", flush=True)
        # Observations only: no wall-time threshold decides the row.
        print(f"last-download-ms={server.last_download_ms:.3f} (observed, not gated)", flush=True)
        assert mapping == "2" * 28 + "1", "a full hand took a sibling's connection"
    finally:
        server.close()
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(f"child-cpu-ms={(usage.ru_utime + usage.ru_stime - cpu_before) * 1000:.3f}", flush=True)


def measure_oracle(binary, directory):
    server = Server(binary, directory / "oracle", oracle=True, workers=2)
    try:
        print("oracle measurement: map=" + server.downloads(29), flush=True)
    finally:
        server.close()


def refusal(binary, directory):
    server = Server(binary, directory)
    try:
        mapping = server.downloads(15)
        assert mapping == "2" * 14 + "1", "single-process admission changed: " + mapping
        server.release()
        body = server.fetch("/metrics")
        assert sample(body, "lobo_connections_refused_total") == 1
        assert sample(body, "lobo_connections_evicted_total") == 0
        for reason in ("emfile", "enfile", "other"):
            assert sample(body, f'lobo_accept_failures_total{{reason="{reason}"}}') == 0
        assert sample(body, "lobo_worker_id") == 0
    finally:
        server.close()


def eviction(binary, directory):
    server = Server(binary, directory)
    try:
        for _ in range(24):
            server.connect()
        until(lambda: len(select.select(server.sockets, [], [], 0)[0]) == 11,
              "eleven idle evictions after 24 accepts")
        # At 16 slots, the fourteenth idle accept and each following one
        # evicts one old idle connection: 24 - 13 = 11, the existing limit row.
        server.release()
        body = server.fetch("/metrics")
        assert sample(body, "lobo_connections_evicted_total") == 11
        assert sample(body, "lobo_connections_refused_total") == 0
    finally:
        server.close()


def accept_failure(binary, directory):
    server = Server(binary, directory, connections=1024, nofile=48)
    try:
        for _ in range(100):
            server.connect()
        until(lambda: re.search(r"accept(?:4)?\(\) failed \(24:", server.log.read_text()),
              "EMFILE accept failure")
        server.release()
        body = server.fetch("/metrics")
        assert sample(body, 'lobo_accept_failures_total{reason="emfile"}') >= 1
        assert sample(body, 'lobo_accept_failures_total{reason="enfile"}') == 0
        assert sample(body, 'lobo_accept_failures_total{reason="other"}') == 0
        assert sample(body, "lobo_connections_refused_total") == 0
        assert sample(body, "lobo_connections_evicted_total") == 0
    finally:
        server.close()


def worker_counters(binary, directory):
    server = Server(binary, directory, workers=2)
    rows = {}
    try:
        for line in server.status().splitlines():
            match = re.match(r"worker ([0-9]+): serving control=([^ ]+) .*pid=([0-9]+)", line)
            if match:
                assert int(match[3]) > 1, "owned worker pid is positive"
                rows[int(match[1])] = (match[2], int(match[3]))
        assert set(rows) == {1, 2}, "both workers' own control endpoints and pids"

        def live(ordinal):
            endpoint = rows[ordinal][0]
            with socket.create_connection(("127.0.0.1", int(endpoint.rsplit(":", 1)[1])), timeout=5) as sock:
                sock.sendall(b"status\n")
                text = b""
                while True:
                    piece = sock.recv(8192)
                    if not piece:
                        break
                    text += piece
                return text.decode()

        os.kill(rows[2][1], signal.SIGSTOP)
        assert server.downloads(15) == "2" * 14 + "1", "one awake worker's capacity"
        for sock in server.sockets:
            sock.close()
        server.sockets.clear()
        until(lambda: "generation 1: current live=0" in live(1), "first worker's releases")
        body = server.fetch("/metrics")
        assert sample(body, "lobo_worker_id") == 1
        assert sample(body, "lobo_connections_refused_total") == 1
        os.kill(rows[2][1], signal.SIGCONT)
        os.kill(rows[1][1], signal.SIGSTOP)
        body = server.fetch("/metrics")
        assert sample(body, "lobo_worker_id") == 2
        assert sample(body, "lobo_connections_refused_total") == 0
        assert sample(body, "lobo_connections_evicted_total") == 0
        for reason in ("emfile", "enfile", "other"):
            assert sample(body, f'lobo_accept_failures_total{{reason="{reason}"}}') == 0
    finally:
        for _, pid in rows.values():
            try:
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass
        server.close()


def worker_rows(server):
    rows = {}
    for line in server.status().splitlines():
        match = re.match(r"worker ([0-9]+): serving control=([^ ]+) .*pid=([0-9]+)", line)
        if match:
            assert int(match[3]) > 1, "owned worker pid is positive"
            rows[int(match[1])] = (match[2], int(match[3]))
    return rows


REPLACE_SECONDS = 8


def hand_replacement(binary, directory, hold):
    """A hand that dies is replaced within REPLACE_SECONDS of its death,
    also when another socket listens on its control endpoint (`hold`): a
    sibling given the same port, or any other listener. The master must
    learn of the death from the hand itself, not from a connect to the
    endpoint, which such a listener answers. The held endpoint accepts
    and closes, as any foreign listener would, so it never fills a
    backlog. The one process signalled is hand 2, once, by the pid the
    master's own status names, after its command line is read."""
    server = Server(binary, directory, workers=2)
    held = None
    done = threading.Event()
    drainer = None
    try:
        def both():
            rows = worker_rows(server)
            return rows if set(rows) == {1, 2} else None
        rows = until(both, "both hands serving")
        endpoint, pid = rows[2]
        proc = Path(f"/proc/{pid}/cmdline")
        if proc.exists():
            command = proc.read_bytes().replace(b"\0", b" ").decode().strip()
        else:
            command = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", "command="],
                                     capture_output=True, text=True, timeout=5).stdout.strip()
        assert f"-c {server.config} --worker 2 --worker-control" in command, \
            f"pid {pid} is not this run's hand 2: {command!r}"
        began = time.monotonic()
        os.kill(pid, signal.SIGKILL)
        if hold:
            port_number = int(endpoint.rsplit(":", 1)[1])

            def take():
                sock = socket.socket()
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind(("127.0.0.1", port_number))
                    sock.listen(64)
                    return sock
                except OSError:
                    sock.close()
                    return None
            held = until(take, f"this rig to listen on hand 2's endpoint {endpoint}", seconds=2)

            def drain():
                held.settimeout(.05)
                while not done.is_set():
                    try:
                        peer, _ = held.accept()
                        peer.close()
                    except socket.timeout:
                        pass
                    except OSError:
                        return
            drainer = threading.Thread(target=drain, daemon=True)
            drainer.start()

        def replaced():
            now = worker_rows(server)
            return now[2] if 2 in now and now[2][1] != pid else None
        left = REPLACE_SECONDS - (time.monotonic() - began)
        try:
            fresh = until(replaced, "a new hand 2", seconds=max(0.0, left))
        except AssertionError:
            rows_now = " | ".join(line for line in server.status().splitlines() if line.startswith("worker "))
            raise AssertionError(f"hand 2 (pid {pid}) not replaced within {REPLACE_SECONDS} s of its kill, "
                                 f"its endpoint {endpoint} {'held by this rig' if hold else 'left free'}; "
                                 f"status: {rows_now}") from None
        took = time.monotonic() - began
        print(f"lobo-admission: measured — hand 2 replaced {took:.2f} s after its kill: pid {pid} -> {fresh[1]}, "
              f"control {endpoint} -> {fresh[0]}", flush=True)
        if hold:
            log = server.log.read_text()
            assert "worker-exited worker=2 reason=signal code=-1" in log, \
                "the master logged hand 2's death as a kill: " + " | ".join(
                    line for line in log.splitlines() if "worker-exited" in line)
    finally:
        done.set()
        if drainer is not None:
            drainer.join(timeout=2)
        if held is not None:
            held.close()
        server.close()


def control(endpoint, command="ping"):
    with socket.create_connection(("127.0.0.1", int(endpoint.rsplit(":", 1)[1])), timeout=5) as sock:
        sock.sendall((command + "\n").encode())
        data = b""
        while True:
            piece = sock.recv(8192)
            if not piece:
                break
            data += piece
        return data.decode()


def closed(sock):
    try:
        return sock.recv(1, socket.MSG_PEEK) == b""
    except (ConnectionResetError, BrokenPipeError):
        return True
    except BlockingIOError:
        return False


def queued(server, port_number=None):
    sock = socket.create_connection(("127.0.0.1", port_number or server.port), timeout=5)
    server.sockets.append(sock)
    sock.setblocking(False)
    return sock


def full_workers(server, count=2):
    assert server.downloads(14 * count) == "2" * (14 * count), "full-worker premise: every download admitted"
    rows = worker_rows(server)
    assert set(rows) == set(range(1, count + 1)), "full-worker premise: every owned pid is readable"
    for endpoint, _ in rows.values():
        assert "generation 1: current live=14" in control(endpoint, "status"), "each worker holds fourteen"
    return rows


def pause(rows):
    for _, pid in rows.values():
        os.kill(pid, signal.SIGSTOP)
    def stopped(pid):
        status = Path(f"/proc/{pid}/status")
        if status.exists():
            return re.search(r"^State:\s+T", status.read_text(), re.M) is not None
        state = subprocess.run(["ps", "-o", "state=", "-p", str(pid)],
                               capture_output=True, text=True, timeout=5)
        return state.stdout.strip().startswith("T")
    until(lambda: all(stopped(pid) for _, pid in rows.values()), "owned workers stopped")


def resume(rows):
    for _, pid in rows.values():
        try:
            os.kill(pid, signal.SIGCONT)
        except ProcessLookupError:
            pass


# lobo#158: a hand that is stopped is left alone, and every dial the
# master makes to a hand is bounded. A stopped process's control queue is
# filled by connects that never send: each bounded to FILL_MS, until one
# does not complete in that time (TCP: the queue is full and the SYN is
# dropped), is refused (a full unix queue on macOS) or would block (a
# full unix queue on Linux). The host bounds every queue: a listen backlog
# is capped at net.core.somaxconn on Linux, and a queue holds at most one
# more than its backlog, so the fill stops by name after somaxconn + 2
# connects that all completed. Measured on a Linux host whose somaxconn is
# 4096: a hand's TCP control queue held 129 and its unix one 4097.
#
# A hand stopped by a signal is marked from the master's wait at once; a
# hand in a tracing stop only when a probe fails after its queue is full.
# The master probes a hand at most every 200 ms and bounds each dial by
# D = 250 ms, so the mark lands within 450 ms of the queue filling. The
# left-alone rows wait MARK_MS for it, twice that rounded up, before they
# read anything else (measured: 502 ms, polling every 100 ms, on the same
# Linux host).

FILL_MS = 200
REPLACED_MS = 2000
STATUS_MS = 3000
LEFT_ALONE_S = 5
PROBE_MS = 200
DIAL_MS = 250
MARK_MS = 1000
STOPPED_RESIDUE = {"status-master-not-accepting-unix"}


def queue_cap():
    """The most connects a fill makes: one past the largest queue the host
    allows (somaxconn + 1), and never fewer than 1024. Off Linux (no
    /proc/sys/net/core/somaxconn) 1024, which fills every queue measured
    there."""
    try:
        somaxconn = int(Path("/proc/sys/net/core/somaxconn").read_text().strip())
    except (OSError, ValueError):
        return 1024
    return max(1024, somaxconn + 2)


def fds_for(count):
    """Raise this process's soft descriptor limit to hold `count` sockets
    and some room, or say by name why it cannot."""
    want = count + 256
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft != resource.RLIM_INFINITY and soft < want:
        if hard != resource.RLIM_INFINITY and hard < want:
            raise AssertionError(f"a fill needs {want} descriptors and the hard limit is {hard}")
        resource.setrlimit(resource.RLIMIT_NOFILE, (want, hard))


def endpoint_connect(endpoint, timeout):
    if endpoint.startswith("unix:"):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect(endpoint[len("unix:"):])
        except BaseException:
            sock.close()
            raise
        return sock
    host, port_text = endpoint.rsplit(":", 1)
    return socket.create_connection((host, int(port_text)), timeout=timeout)


def fill(endpoint):
    cap = queue_cap()
    fds_for(cap)
    held = []
    while len(held) < cap:
        try:
            held.append(endpoint_connect(endpoint, FILL_MS / 1000))
        except OSError:
            return held
    for sock in held:
        sock.close()
    raise AssertionError(f"{cap} connects to {endpoint} completed: its queue never filled "
                         f"(the host allows at most {cap - 1})")


def proc_state(pid):
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            return stat.read_text().rsplit(") ", 1)[1].split()[0]
        except (OSError, IndexError):
            return "-"
    value = subprocess.run(["ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True, timeout=5)
    return value.stdout.strip()[:1] or "-"


def master_endpoint(server):
    lines = (server.directory / "server.pid").read_text().split()
    if len(lines) >= 2:
        return lines[1]
    return f"unix:{server.directory}/ctl.sock"


def own_hand(server, ordinal):
    """A hand's endpoint and pid from the master's own status, its command
    line read before anything signals it."""
    rows = until(lambda: (lambda r: r if set(r) == {1, 2} else None)(worker_rows(server)), "both hands serving")
    endpoint, pid = rows[ordinal]
    proc = Path(f"/proc/{pid}/cmdline")
    if proc.exists():
        command = proc.read_bytes().replace(b"\0", b" ").decode().strip()
    else:
        command = subprocess.run(["ps", "-ww", "-p", str(pid), "-o", "command="],
                                 capture_output=True, text=True, timeout=5).stdout.strip()
    assert f"-c {server.config} --worker {ordinal} --worker-control" in command, \
        f"pid {pid} is not this run's hand {ordinal}: {command!r}"
    return endpoint, pid


def timed_status(server, limit_ms=STATUS_MS):
    """`lobo status`, its exit, its output, and the milliseconds it took;
    a status that outlives `limit_ms` (plus two seconds' grace) is no
    answer."""
    began = time.monotonic()
    try:
        value = subprocess.run([server.binary, "status", "-p", str(server.directory), "-c", str(server.config)],
                               capture_output=True, text=True, timeout=limit_ms / 1000 + 2)
    except subprocess.TimeoutExpired:
        return None, "", int((time.monotonic() - began) * 1000)
    return value.returncode, value.stdout + value.stderr, int((time.monotonic() - began) * 1000)


def stop_hand(pid):
    os.kill(pid, signal.SIGSTOP)
    until(lambda: proc_state(pid) == "T", f"pid {pid} stopped")


def wake(pid):
    try:
        os.kill(pid, signal.SIGCONT)
    except ProcessLookupError:
        pass


def control_verb(server, verb):
    return subprocess.run([server.binary, "-s", verb, "-p", str(server.directory), "-c", str(server.config)],
                          capture_output=True, text=True, timeout=10)


def stopped_other_replaced(binary, directory, unix):
    """Hand 2 stopped, its queue full; hand 1 killed. Hand 1 is replaced
    within REPLACED_MS of its kill, and status answers within STATUS_MS
    meanwhile: the master is never held by a dial to the stopped hand."""
    server = Server(binary, directory, workers=2, control_unix=unix)
    held = []
    pid2 = None
    try:
        endpoint2, pid2 = own_hand(server, 2)
        _, pid1 = own_hand(server, 1)
        stop_hand(pid2)
        held = fill(endpoint2)
        began = time.monotonic()
        os.kill(pid1, signal.SIGKILL)
        try:
            until(lambda: "worker-started worker=1 restarts=1" in server.log.read_text(), "hand 1 replaced",
                  seconds=REPLACED_MS / 1000)
        except AssertionError:
            raise AssertionError(f"hand 1 not replaced within {REPLACED_MS} ms of its kill while hand 2 is stopped "
                                 f"with its queue full ({len(held)} connects held)") from None
        took = int((time.monotonic() - began) * 1000)
        code, text, ms = timed_status(server)
        assert code == 0 and ms <= STATUS_MS, f"status took {ms} ms (exit {code}) after hand 1's replacement"
        print(f"lobo-admission: measured — hand 1 replaced {took} ms after its kill; status in {ms} ms", flush=True)
    finally:
        for sock in held:
            sock.close()
        if pid2 is not None:
            wake(pid2)
        server.close()


def master_not_accepting(binary, directory, unix):
    """The master stopped, its queue full: `lobo status` says the master is
    not responding within STATUS_MS."""
    if unix and not Path("/proc").exists():
        return "a full unix queue is refused at once on this host, so the row cannot be red at trunk here"
    server = Server(binary, directory, workers=2, control_unix=unix)
    held = []
    master = server.process.pid
    try:
        own_hand(server, 2)
        endpoint = master_endpoint(server)
        stop_hand(master)
        held = fill(endpoint)
        code, text, ms = timed_status(server)
        assert code is not None, f"status gave no answer within {STATUS_MS} ms against a stopped master"
        # the client's two diagnostics: "not responding" for an endpoint
        # that refuses, "did not answer within" for one whose dial or reply
        # ran out its deadline, which is what a stopped master's is
        unanswered = "not responding" in text or "did not answer within" in text
        assert code != 0 and unanswered and ms <= STATUS_MS, \
            f"status against a stopped master: exit {code} after {ms} ms: {text.strip()[:200]!r}"
        print(f"lobo-admission: measured — status said the master did not answer, in {ms} ms", flush=True)
    finally:
        for sock in held:
            sock.close()
        wake(master)
        server.close()


def hand_left_alone(server, pid2, endpoint2, held):
    """Shared by the stopped and traced rows, from the moment hand 2 is
    stopped and its queue full: status shows it stopped within MARK_MS,
    then for LEFT_ALONE_S seconds it is alive, not exited, and status shows
    it stopped, each status within STATUS_MS."""
    filled = time.monotonic()
    rows = [""]

    def shown_stopped():
        code, text, ms = timed_status(server)
        rows[0] = " | ".join(l for l in text.splitlines() if l.startswith("worker ")) or f"exit {code} after {ms} ms"
        return re.search(r"^worker 2: stopped ", text, re.M) is not None

    while not shown_stopped():
        if time.monotonic() - filled >= MARK_MS / 1000:
            raise AssertionError(
                f"status did not show hand 2 stopped within {MARK_MS} ms of its queue filling (a probe every "
                f"{PROBE_MS} ms, each dial bounded by {DIAL_MS} ms: the mark is due within {PROBE_MS + DIAL_MS} ms, "
                f"and the row allows twice that, rounded up): {rows[0]}")
        time.sleep(0.1)
    print(f"lobo-admission: measured — hand 2 shown stopped {int((time.monotonic() - filled) * 1000)} ms "
          f"after its queue filled (bound {MARK_MS} ms)", flush=True)
    began = time.monotonic()
    while time.monotonic() - began < LEFT_ALONE_S:
        assert proc_state(pid2) not in ("-", "Z", ""), f"hand 2 (pid {pid2}) is gone"
        assert "worker-exited worker=2" not in server.log.read_text(), "the master ended the stopped hand 2"
        code, text, ms = timed_status(server)
        assert code == 0 and ms <= STATUS_MS, f"status took {ms} ms (exit {code}) while hand 2 is stopped"
        assert re.search(r"^worker 2: stopped ", text, re.M), \
            "status does not show hand 2 stopped: " + " | ".join(l for l in text.splitlines() if l.startswith("worker "))
        time.sleep(1)
    for sock in held:
        sock.close()
    held.clear()


def back_serving(server, endpoint2):
    until(lambda: re.search(r"^worker 2: serving ", server.status(), re.M), "hand 2 serving again",
          seconds=STATUS_MS / 1000)
    sock = endpoint_connect(endpoint2, 5)
    with sock:
        sock.sendall(b"status\n")
        data = b""
        while True:
            piece = sock.recv(8192)
            if not piece:
                break
            data += piece
    assert b"generation" in data, f"hand 2 did not answer status on its own endpoint: {data[:120]!r}"


def stopped_left_alone(binary, directory, unix):
    server = Server(binary, directory, workers=2, control_unix=unix)
    held = []
    pid2 = None
    try:
        endpoint2, pid2 = own_hand(server, 2)
        stop_hand(pid2)
        held = fill(endpoint2)
        hand_left_alone(server, pid2, endpoint2, held)
        wake(pid2)
        back_serving(server, endpoint2)
    finally:
        for sock in held:
            sock.close()
        if pid2 is not None:
            wake(pid2)
        server.close()


PTRACE_SEIZE = 0x4206
PTRACE_INTERRUPT = 0x4207
PTRACE_DETACH = 17


def traced_left_alone(binary, directory):
    """Hand 2 in a tracing stop, which the master's wait does not report:
    left alone as a stopped hand, found by its state."""
    if not Path("/proc").exists():
        return "no /proc: a tracing stop is a Linux row"
    import ctypes
    scope = Path("/proc/sys/kernel/yama/ptrace_scope")
    scope_text = scope.read_text().strip() if scope.exists() else "absent"
    libc = ctypes.CDLL(None, use_errno=True)
    libc.ptrace.argtypes = [ctypes.c_long, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
    libc.ptrace.restype = ctypes.c_long
    server = Server(binary, directory, workers=2)
    held = []
    pid2 = None
    seized = False
    try:
        endpoint2, pid2 = own_hand(server, 2)
        if libc.ptrace(PTRACE_SEIZE, pid2, None, None) != 0:
            return f"PTRACE_SEIZE refused: errno {ctypes.get_errno()} (ptrace_scope {scope_text})"
        seized = True
        if libc.ptrace(PTRACE_INTERRUPT, pid2, None, None) != 0:
            raise AssertionError(f"PTRACE_INTERRUPT failed: errno {ctypes.get_errno()}")
        until(lambda: proc_state(pid2) == "t", f"hand 2 (pid {pid2}) in a tracing stop")
        held = fill(endpoint2)
        hand_left_alone(server, pid2, endpoint2, held)
        if libc.ptrace(PTRACE_DETACH, pid2, None, None) != 0:
            raise AssertionError(f"PTRACE_DETACH failed: errno {ctypes.get_errno()}")
        seized = False
        back_serving(server, endpoint2)
    finally:
        for sock in held:
            sock.close()
        if seized:
            libc.ptrace(PTRACE_DETACH, pid2, None, None)
        server.close()


def stopped_missed_reload(binary, directory):
    """A guard: a reload while hand 2 is stopped reaches it once it
    continues."""
    server = Server(binary, directory, workers=2)
    pid2 = None
    try:
        _, pid2 = own_hand(server, 2)
        stop_hand(pid2)
        server.config.write_text(server.config.read_text().replace("worker_connections 16;", "worker_connections 17;"))
        control_verb(server, "reload")

        # read from the master's log, which every hand writes to: no dial,
        # so a status gather held by the stopped hand cannot decide it
        def activated(ordinal):
            return re.search(rf"generation-activated gen=2 seq=[0-9]+ worker={ordinal}\b", server.log.read_text())
        until(lambda: activated(1), "hand 1 at generation 2", seconds=STATUS_MS / 1000)
        assert not activated(2), "hand 2 reached generation 2 while it was stopped"
        wake(pid2)
        until(lambda: activated(2), "hand 2 at generation 2 after it continues", seconds=STATUS_MS / 1000)
    finally:
        if pid2 is not None:
            wake(pid2)
        server.close()


def stop_ends_stopped(binary, directory):
    """A guard: `stop` ends the master while hand 2 is stopped."""
    server = Server(binary, directory, workers=2)
    pid2 = None
    try:
        _, pid2 = own_hand(server, 2)
        stop_hand(pid2)
        control_verb(server, "stop")
        try:
            server.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise AssertionError("the master did not exit within 5000 ms of stop while hand 2 is stopped") from None
    finally:
        if pid2 is not None:
            wake(pid2)
        server.close()


def quit_waits_for_stopped(binary, directory):
    """A guard: `quit` waits for a stopped hand, and ends once it
    continues and drains."""
    server = Server(binary, directory, workers=2)
    pid2 = None
    try:
        _, pid2 = own_hand(server, 2)
        stop_hand(pid2)
        control_verb(server, "quit")
        time.sleep(LEFT_ALONE_S)
        assert server.process.poll() is None, "the master exited under quit while hand 2 was stopped"
        wake(pid2)
        try:
            server.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            raise AssertionError("the master did not exit within 5000 ms of hand 2 continuing under quit") from None
    finally:
        if pid2 is not None:
            wake(pid2)
        server.close()


def later_listener_progress(binary, directory):
    server = Server(binary, directory, workers=2, connections=18, extra_plain=True, tls=True)
    rows = {}
    try:
        rows = full_workers(server)
        pause(rows)
        primary = [queued(server) for _ in range(64)]
        later = {queued(server, server.extra_port): "extra-plaintext",
                 queued(server, server.tls_port): "tls"}
        resume(rows)
        refusals = 0
        finished = set()
        deadline = time.monotonic() + 15  # hang bound, not the progress assertion
        while refusals < 192 and len(finished) < 2 and time.monotonic() < deadline:
            ready = select.select(primary + [s for s in later if later[s] not in finished], [], [], 1)[0]
            for sock in ready:
                if not closed(sock):
                    continue
                if sock in later:
                    finished.add(later[sock])
                else:
                    primary.remove(sock)
                    sock.close()
                    refusals += 1
                    primary.append(queued(server))
        print(f"later listeners: primary-refusals={refusals} finished={sorted(finished)}", flush=True)
        assert finished == {"extra-plaintext", "tls"}, "later listeners starved while primary refusals progressed"
    finally:
        resume(rows)
        server.close()


def full_burst_progress(binary, directory):
    server = Server(binary, directory, workers=2)
    rows = {}
    try:
        rows = full_workers(server)
        pause(rows)
        pending = [queued(server) for _ in range(32)]
        resume(rows)
        until(lambda: any(closed(sock) for sock in pending), "first all-full refusal")
        # A second round trip per worker follows its preceding loop's
        # bounded burst. No wall-time threshold decides this row.
        for _ in range(2):
            for endpoint, _ in rows.values():
                assert control(endpoint) == "pong\n", "owned control barrier"
        refused = sum(closed(sock) for sock in pending)
        print(f"all-full burst: refused={refused}/32 after two control barriers per worker", flush=True)
        assert refused == 32, "queued refusals were serialized behind fresh pauses"
    finally:
        resume(rows)
        server.close()


def cpu_seconds(pid):
    tail = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    return (int(tail[11]) + int(tail[12])) / os.sysconf("SC_CLK_TCK")


def backoff_idle_cpu(binary, directory):
    if not Path("/proc/self/stat").exists() or not hasattr(resource, "prlimit"):
        return "Linux procfs and prlimit are needed for the owned-worker EMFILE/CPU witness"
    server = Server(binary, directory, workers=2, connections=18, extra_plain=True, tls=True)
    rows = {}
    limits = {}
    try:
        rows = full_workers(server)
        pause(rows)
        for _, pid in rows.values():
            limits[pid] = resource.prlimit(pid, resource.RLIMIT_NOFILE)
            fds = {int(p.name) for p in Path(f"/proc/{pid}/fd").iterdir()}
            first_hole = 0
            while first_hole in fds:
                first_hole += 1
            assert first_hole >= 3, "standard descriptors are open"
            # Only lower the soft limit on our own stopped worker. Every
            # fd below it is occupied; existing higher fds stay usable.
            resource.prlimit(pid, resource.RLIMIT_NOFILE, (first_hole, limits[pid][1]))
        queued(server)
        queued(server, server.tls_port)
        resume(rows)
        until(lambda: "accept() failed (24:" in server.log.read_text(), "multi-listener EMFILE")
        ratios = []
        for _ in range(3):
            before = sum(cpu_seconds(pid) for _, pid in rows.values())
            began = time.monotonic()
            time.sleep(1)
            elapsed = time.monotonic() - began
            used = sum(cpu_seconds(pid) for _, pid in rows.values()) - before
            ratios.append(used / (elapsed * len(rows)))
        print(f"EMFILE idle CPU fractions: {ratios}; minimum={min(ratios):.4f}; bound=0.10", flush=True)
        assert min(ratios) < .10, "admission timer spins inside accept-failure backoff"
    finally:
        for pid, limit in limits.items():
            try:
                resource.prlimit(pid, resource.RLIMIT_NOFILE, limit)
            except ProcessLookupError:
                pass
        resume(rows)
        server.close()


def one_hand_scope(binary, directory):
    if os.geteuid() != 0 or not Path("/proc/self/stat").exists():
        return "root Linux container needed to start a one-hand master"
    server = Server(binary, directory, workers=1)
    rows = {}
    try:
        rows = full_workers(server, count=1)
        pause(rows)
        pending = queued(server)
        resume(rows)
        for _ in range(2):
            assert control(rows[1][0]) == "pong\n", "one-hand control barrier"
        assert closed(pending), "one-hand master owed a pause despite having no sibling"
    finally:
        resume(rows)
        server.close()


# lobo#142: a TLS connection holds nothing. Each row puts one TLS
# connection in a hold on a single-process lobo (`worker_processes 1`, a
# plain and a TLS listener) and, while it holds, asks for a plaintext GET
# on another connection and a GET from a second TLS client. Both must be
# answered 200 within HOLD_MS, a bound fixed before any run. Every wait
# ends at HOLD_WAIT_MS, so a server that serves the held connection to
# completion costs a red row seconds, not its read timeout. The client is
# this python's ssl (TLS 1.3); the test CA is trusted only in the rows' own
# context. `tls-download-holds-none` is named residue (lobo#142's
# decision 2(b): a slow TLS download is still written on the loop until
# its follow-on): it runs and is reported, red as named, and not counted.
HOLD_MS = 1000
HOLD_WAIT_MS = 3000
TLS_FIXTURES = Path(__file__).resolve().parents[3] / "tests/tls/fixtures"
TLS_RESIDUE = {"tls-download-holds-none"}


def tls_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.load_verify_locations(TLS_FIXTURES / "ca.crt")
    return context


def tls_connect(server, seconds):
    raw = socket.create_connection(("127.0.0.1", server.tls_port), timeout=seconds)
    try:
        return tls_context().wrap_socket(raw, server_hostname="localhost")
    except BaseException:
        raw.close()
        raise


def client_hello():
    """The bytes of a real TLS 1.3 ClientHello from this python's ssl."""
    incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
    hello = tls_context().wrap_bio(incoming, outgoing, server_hostname="localhost")
    try:
        hello.do_handshake()
    except ssl.SSLWantReadError:
        pass
    return outgoing.read()


def read_answer(sock, deadline, whole=False):
    """The status line of an answer read before the monotonic `deadline`
    ('' if none came), and with `whole` its body read to Content-Length."""
    data = b""
    marker = b"\r\n\r\n" if whole else b"\r\n"
    while marker not in data:
        left = deadline - time.monotonic()
        if left <= 0:
            return ""
        sock.settimeout(left)
        try:
            piece = sock.recv(65536)
        except OSError:
            return ""
        if not piece:
            return ""
        data += piece
    status = data.split(b"\r\n", 1)[0].decode(errors="replace")
    if whole:
        head, body = data.split(b"\r\n\r\n", 1)
        match = re.search(rb"(?im)^content-length:\s*([0-9]+)", head)
        want = int(match[1]) if match else 0
        while len(body) < want:
            left = deadline - time.monotonic()
            if left <= 0:
                return ""
            sock.settimeout(left)
            try:
                piece = sock.recv(65536)
            except OSError:
                return ""
            if not piece:
                return ""
            body += piece
    return status


def answered_meanwhile(server, what):
    """While a hold is in place: a plaintext GET and a second TLS client's GET,
    each timed to its status line. Asserts both are 200 within HOLD_MS."""
    results = []
    for kind in ("plain", "tls"):
        began = time.monotonic()
        deadline = began + HOLD_WAIT_MS / 1000
        sock = None
        status = ""
        try:
            if kind == "plain":
                sock = socket.create_connection(("127.0.0.1", server.port), timeout=HOLD_WAIT_MS / 1000)
            else:
                sock = tls_connect(server, HOLD_WAIT_MS / 1000)
            sock.settimeout(max(0.01, deadline - time.monotonic()))
            sock.sendall(b"GET /index.html HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n")
            status = read_answer(sock, deadline)
        except OSError:
            status = ""
        finally:
            if sock is not None:
                sock.close()
        results.append((kind, status, (time.monotonic() - began) * 1000))
    line = "; ".join(f"{kind} {('answered ' + status) if status else 'no answer'} after {ms:.0f} ms"
                     for kind, status, ms in results)
    print(f"tls-hold: while {what}: {line}", flush=True)
    for kind, status, ms in results:
        assert status.startswith("HTTP/1.1 200") and ms <= HOLD_MS, \
            f"while {what}, the {kind} GET was not answered 200 within {HOLD_MS} ms ({line})"


def hold_handshake(server):
    hello = client_hello()
    sock = socket.create_connection(("127.0.0.1", server.tls_port), timeout=5)
    sock.sendall(hello[:len(hello) // 2])
    return sock, f"a client holds {len(hello) // 2} of a {len(hello)}-byte ClientHello", None


def hold_head(server):
    sock = tls_connect(server, 5)
    sock.sendall(b"GET /index.html HTTP/1.1\r\nHo")
    return sock, "a TLS client holds half a request head", None


def hold_idle(server):
    sock = tls_connect(server, 5)
    sock.sendall(b"GET /index.html HTTP/1.1\r\nHost: localhost\r\n\r\n")
    status = read_answer(sock, time.monotonic() + HOLD_WAIT_MS / 1000, whole=True)
    assert status.startswith("HTTP/1.1 200"), f"the idle row's first GET was not answered 200 ({status or 'no answer'})"
    return sock, "a TLS client served one GET stays connected and idle", None


def hold_upload(server):
    sock = tls_connect(server, 5)
    began = time.monotonic()
    sock.sendall(b"POST /index.html HTTP/1.1\r\nHost: localhost\r\nContent-Length: 6\r\n\r\na")
    status = read_answer(sock, began + HOLD_WAIT_MS / 1000)
    own = (status, (time.monotonic() - began) * 1000)
    return sock, "a TLS client holds a POST to a file route with 1 of its 6 body bytes", own


def hold_download(server):
    sock = tls_connect(server, 5)
    sock.sendall(b"GET /big.bin HTTP/1.1\r\nHost: localhost\r\n\r\n")
    time.sleep(0.5)
    return sock, "a TLS client asks for a 24 MiB file and reads none of it", None


def tls_hold(binary, directory, hold):
    if not ssl.HAS_TLSv1_3:
        return f"this python's ssl ({ssl.OPENSSL_VERSION}) has no TLS 1.3"
    server = Server(binary, directory, tls=True)
    sock = None
    try:
        sock, what, own = hold(server)
        answered_meanwhile(server, what)
        if own is not None:
            status, ms = own
            print(f"tls-hold: the holding client's own answer: {status or 'none'} after {ms:.0f} ms", flush=True)
            assert status.startswith("HTTP/1.1 405") and ms <= HOLD_MS, \
                f"the POST with a short body was not answered 405 after its head within {HOLD_MS} ms ({status or 'no answer'} after {ms:.0f} ms)"
    finally:
        if sock is not None:
            sock.close()
        server.close()


# the named residue rows of every mode: each runs and is reported, red as
# named and not counted; one that turns green fails until it is retired
RESIDUE = STOPPED_RESIDUE | TLS_RESIDUE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("admission", "counters", "oracle", "review", "tls-hold", "stopped"))
    parser.add_argument("binary")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--row", choices=("later-listener-progress", "all-full-burst-progress", "multi-listener-emfile-cpu", "one-hand-master-scope",
                                          "hand-replaced-endpoint-held", "hand-replaced-endpoint-free",
                                          "tls-handshake-holds-none", "tls-head-holds-none", "tls-idle-holds-none",
                                          "tls-upload-holds-none", "tls-download-holds-none",
                                          "hand-stopped-other-replaced", "hand-stopped-other-replaced-unix",
                                          "status-master-not-accepting", "status-master-not-accepting-unix",
                                          "hand-stopped-left-alone", "hand-stopped-left-alone-unix", "hand-traced-left-alone",
                                          "stopped-hand-gets-missed-reload", "stop-ends-stopped-hand",
                                          "quit-waits-for-stopped-hand"))
    args = parser.parse_args()
    if args.mode == "admission":
        rows = [("shared-listener-first28", lambda: admission(args.binary, args.directory))]
    elif args.mode == "oracle":
        rows = [("oracle-measurement", lambda: measure_oracle(args.binary, args.directory))]
    elif args.mode == "tls-hold":
        rows = [("tls-handshake-holds-none", lambda: tls_hold(args.binary, args.directory / "handshake", hold_handshake)),
                ("tls-head-holds-none", lambda: tls_hold(args.binary, args.directory / "head", hold_head)),
                ("tls-idle-holds-none", lambda: tls_hold(args.binary, args.directory / "idle", hold_idle)),
                ("tls-upload-holds-none", lambda: tls_hold(args.binary, args.directory / "upload", hold_upload)),
                ("tls-download-holds-none", lambda: tls_hold(args.binary, args.directory / "download", hold_download))]
    elif args.mode == "stopped":
        d = args.directory
        rows = [("hand-stopped-other-replaced", lambda: stopped_other_replaced(args.binary, d / "other", False)),
                ("hand-stopped-other-replaced-unix", lambda: stopped_other_replaced(args.binary, d / "other-unix", True)),
                ("status-master-not-accepting", lambda: master_not_accepting(args.binary, d / "master", False)),
                ("status-master-not-accepting-unix", lambda: master_not_accepting(args.binary, d / "master-unix", True)),
                ("hand-stopped-left-alone", lambda: stopped_left_alone(args.binary, d / "alone", False)),
                ("hand-stopped-left-alone-unix", lambda: stopped_left_alone(args.binary, d / "alone-unix", True)),
                ("hand-traced-left-alone", lambda: traced_left_alone(args.binary, d / "traced")),
                ("stopped-hand-gets-missed-reload", lambda: stopped_missed_reload(args.binary, d / "reload")),
                ("stop-ends-stopped-hand", lambda: stop_ends_stopped(args.binary, d / "stop")),
                ("quit-waits-for-stopped-hand", lambda: quit_waits_for_stopped(args.binary, d / "quit"))]
    elif args.mode == "review":
        rows = [("later-listener-progress", lambda: later_listener_progress(args.binary, args.directory / "later")),
                ("all-full-burst-progress", lambda: full_burst_progress(args.binary, args.directory / "burst")),
                ("multi-listener-emfile-cpu", lambda: backoff_idle_cpu(args.binary, args.directory / "backoff")),
                ("one-hand-master-scope", lambda: one_hand_scope(args.binary, args.directory / "one-hand"))]
    else:
        rows = [("connections-refused", lambda: refusal(args.binary, args.directory / "refused")),
                ("connections-evicted", lambda: eviction(args.binary, args.directory / "evicted")),
                ("accept-failures-emfile", lambda: accept_failure(args.binary, args.directory / "emfile")),
                ("connection-counters-per-worker", lambda: worker_counters(args.binary, args.directory / "workers")),
                ("hand-replaced-endpoint-held", lambda: hand_replacement(args.binary, args.directory / "held", hold=True)),
                ("hand-replaced-endpoint-free", lambda: hand_replacement(args.binary, args.directory / "free", hold=False))]
    if args.row:
        rows = [(name, run) for name, run in rows if name == args.row]
        if not rows:
            parser.error(f"--row {args.row} is not a row of the {args.mode} mode")
    red = 0
    for name, run in rows:
        try:
            outcome = run()
            if isinstance(outcome, str):
                print(f"lobo-admission: SKIPPED — {name}: {outcome}", flush=True)
            elif name in RESIDUE:
                # named residue: green here means it is fixed, and the row
                # must be retired from RESIDUE
                red += 1
                print(f"lobo-admission: FAILED — [{name}] the named residue row is green: retire it from RESIDUE", flush=True)
            else:
                print(f"lobo-admission: ok — [{name}]", flush=True)
        except (AssertionError, OSError, subprocess.SubprocessError) as error:
            if name in RESIDUE:
                print(f"lobo-admission: RESIDUE — [{name}] red, as named, not counted: {error}", flush=True)
                continue
            red += 1
            print(f"lobo-admission: FAILED — [{name}] {error}", flush=True)
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
