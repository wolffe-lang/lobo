#!/usr/bin/env python3
"""Loopback-only completion behavior witnesses; never a performance record."""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Wire:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""
        sock.settimeout(5)

    def through(self, marker):
        while marker not in self.buf:
            piece = self.sock.recv(65536)
            if not piece:
                raise EOFError("connection ended before a complete message")
            self.buf += piece
        part, self.buf = self.buf.split(marker, 1)
        return part

    def take(self, length):
        while len(self.buf) < length:
            piece = self.sock.recv(65536)
            if not piece:
                raise EOFError("connection ended during a body")
            self.buf += piece
        part, self.buf = self.buf[:length], self.buf[length:]
        return part

    def message(self):
        head = self.through(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        headers = dict(line.lower().split(b":", 1) for line in lines[1:] if b":" in line)
        if b"chunked" in headers.get(b"transfer-encoding", b""):
            body = b""
            while True:
                size = int(self.through(b"\r\n").split(b";", 1)[0], 16)
                if size == 0:
                    while self.through(b"\r\n"):
                        pass
                    break
                body += self.take(size)
                require(self.take(2) == b"\r\n", "invalid fixture chunk framing")
        else:
            body = self.take(int(headers.get(b"content-length", b"0")))
        return lines[0], headers, body


def request(path, extra=b"", body=b""):
    return b"GET " + path.encode() + b" HTTP/1.1\r\nHost: t\r\n" + extra + b"\r\n" + body


class Backend:
    def __init__(self, delay=0):
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(128)
        self.listener.settimeout(.1)
        self.port = self.listener.getsockname()[1]
        self.stop = threading.Event()
        self.release = threading.Event()
        self.seen_gate = threading.Event()
        self.disconnected = threading.Event()
        self.delay = delay
        self.clients = []
        self.workers = []
        self.errors = []
        self.acceptor = threading.Thread(target=self.accept, daemon=True)
        self.acceptor.start()

    def accept(self):
        while not self.stop.is_set():
            try:
                sock, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.clients.append(sock)
            worker = threading.Thread(target=self.answer, args=(sock,), daemon=True)
            self.workers.append(worker)
            worker.start()

    def answer(self, sock):
        try:
            line, _, body = Wire(sock).message()
            path = line.split()[1]
            if b"gated" in path:
                self.seen_gate.set()
                sock.settimeout(.02)
                while not self.release.is_set() and not self.stop.is_set():
                    try:
                        if sock.recv(1, socket.MSG_PEEK) == b"":
                            self.disconnected.set()
                            return
                    except socket.timeout:
                        pass
            if self.delay:
                time.sleep(self.delay)  # Deliberately paced correctness traffic.
            response = path + b"=" + body
            sock.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(response)).encode()
                         + b"\r\nConnection: close\r\n\r\n" + response)
        except (OSError, EOFError) as error:
            if not self.stop.is_set():
                self.errors.append(str(error))
        finally:
            sock.close()

    def close(self):
        self.stop.set()
        self.release.set()
        self.listener.close()
        self.acceptor.join(2)
        for sock in self.clients:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
        for worker in self.workers:
            worker.join(2)
        require(not self.acceptor.is_alive() and not any(w.is_alive() for w in self.workers),
                "fixture backend did not stop")


class Fixture:
    def __init__(self, binary, mode, delay=0, shutdown="5s", out=None):
        self.binary = str(Path(binary).resolve())
        base = Path.cwd() / "target"
        base.mkdir(exist_ok=True)
        self.root = Path(out) if out else Path(tempfile.mkdtemp(prefix="completion_" + mode + "_", dir=base))
        if out:
            self.root.mkdir(exist_ok=False)
        for part in ("old", "new", "logs", "home"):
            (self.root / part).mkdir()
        (self.root / "old/tail").write_bytes(b"old-tail")
        (self.root / "new/tail").write_bytes(b"new-tail")
        (self.root / "old/old-only").write_bytes(b"old-only")
        (self.root / "new/old-only").write_bytes(b"new-only")
        self.backend = Backend(delay)
        self.shutdown = shutdown
        self.conf = self.root / "lobo.conf"
        self.write_conf("old")
        self.env = dict(os.environ, SHELL="/bin/sh", HOME=str(self.root / "home"))
        self.sockets = []
        self.success = False
        self.output = (self.root / "server.out").open("wb")
        argv = [self.binary, "serve", "-p", str(self.root), "-c", str(self.conf)]
        self.process = subprocess.Popen(argv, env=self.env, stdout=self.output, stderr=self.output)
        (self.root / "launcher.pid").write_text(str(self.process.pid) + "\n")
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError("server exited during startup: " + (self.root / "server.out").read_text())
            try:
                self.control("ping")
                break
            except (AssertionError, subprocess.TimeoutExpired):
                time.sleep(.02)
        else:
            raise AssertionError("server did not acknowledge startup ping")
        self.port = int((self.root / "port").read_text())

    def write_conf(self, generation):
        if not (self.root / "port").exists():
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", 0))
                (self.root / "port").write_text(str(probe.getsockname()[1]))
        port = (self.root / "port").read_text()
        self.conf.write_text(
            f"pid {self.root}/logs/lobo.pid;\ncontrol unix:{self.root}/logs/c.sock;\n"
            f"worker_shutdown_timeout {self.shutdown};\nevents {{ worker_connections 64; }}\n"
            "http {\nlog_format order '$request $status rt=$request_time';\n"
            f"access_log {self.root}/logs/access.log order;\nmetrics on;\n"
            f"server {{ listen 127.0.0.1:{port}; root {self.root}/{generation};\n"
            "keepalive_requests 10000;\n"
            f"location /up/ {{ proxy_pass http://127.0.0.1:{self.backend.port}; proxy_read_timeout 30s; }}\n"
            "}\n}\n")

    def control(self, verb):
        result = subprocess.run([self.binary, "control", verb, "-p", str(self.root), "-c", str(self.conf)],
                                env=self.env, capture_output=True, timeout=5)
        require(result.returncode == 0, "control " + verb + ": " + repr(result.stdout + result.stderr))
        return result.stdout

    def connect(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        self.sockets.append(sock)
        return sock

    def get(self, path):
        sock = self.connect()
        sock.sendall(request(path, b"Connection: close\r\n"))
        line, _, body = Wire(sock).message()
        require(b" 200 " in line, "unexpected static/control workload response: " + repr(line))
        sock.close()
        return body

    def access(self, count):
        deadline = time.monotonic() + 5
        path = self.root / "logs/access.log"
        while time.monotonic() < deadline:
            rows = path.read_text().splitlines() if path.exists() else []
            if len(rows) >= count:
                return rows
            time.sleep(.01)
        raise AssertionError("missing access records")

    def close(self):
        process = getattr(self, "process", None)
        try:
            if process is not None:
                if process.poll() is None:
                    try:
                        self.control("stop")
                    except (AssertionError, subprocess.TimeoutExpired):
                        pass
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    # Only the literal PID returned by this fixture's Popen.
                    process.kill()
                    process.wait(timeout=5)
        finally:
            for sock in getattr(self, "sockets", []):
                sock.close()
            if getattr(self, "backend", None) is not None:
                self.backend.close()
            if getattr(self, "output", None) is not None:
                self.output.close()
        root = getattr(self, "root", None)
        if getattr(self, "success", False) and root is not None:
            shutil.rmtree(root)
        elif root is not None:
            print("retained fixture:", root, flush=True)


def fixture(*args, **kwargs):
    instance = Fixture.__new__(Fixture)
    try:
        instance.__init__(*args, **kwargs)
    except BaseException:
        instance.close()
        raise
    return instance


def pipeline(binary):
    f = fixture(binary, "pipeline")
    try:
        sock = f.connect()
        wire = Wire(sock)
        second = b"POST /up/b HTTP/1.1\r\nHost: t\r\nContent-Length: 3\r\n\r\nb"
        sock.sendall(request("/up/gated-a") + second)
        require(f.backend.seen_gate.wait(5), "first exchange did not reach its upstream")
        sock.sendall(b"eePOST /up/c HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n"
                     b"2\r\nc1\r\n1\r\n!\r\n0\r\n\r\nGET /tail HTTP/1.1\r\nHost:")
        f.backend.release.set()
        expected = [b"/up/gated-a=", b"/up/b=bee", b"/up/c=c1!"]
        got = [wire.message()[2] for _ in expected]
        require(got == expected, "completion_pipeline_order: duplicate, lost or reordered response: " + repr(got))
        require(f.get("/tail") == b"old-tail", "partial head blocked an unrelated client")
        f.control("status")
        sock.sendall(b" t\r\n\r\n" + request("/up/d", b"Connection: close\r\n"))
        got = [wire.message()[2], wire.message()[2]]
        require(got == [b"old-tail", b"/up/d="], "completion_pipeline_order: split head or final body corrupted")
        rows = f.access(6)
        paths = [row.split()[1] for row in rows]
        require(paths.count("/up/gated-a") == paths.count("/up/b") == paths.count("/up/c") == paths.count("/up/d") == 1,
                "completion_pipeline_order: an exchange was logged more or less than once")
        require(paths.count("/tail") == 2 and len(rows) == 6, "completion_pipeline_order: static accounting was duplicated")
        scrape = f.get("/metrics")
        require(b'lobo_requests_total{class="2xx"} 6\n' in scrape,
                "completion_pipeline_order: request metric is not exactly six")
        f.success = True
    finally:
        f.close()


def ready(binary):
    f = fixture(binary, "ready")
    try:
        sock = f.connect()
        wire = Wire(sock)
        sock.sendall(request("/up/idle"))
        require(wire.message()[2] == b"/up/idle=", "initial idle exchange failed")
        f.control("ping")
        require(f.get("/tail") == b"old-tail", "an idle completed client blocked the loop")
        sock.sendall(b"GET /tail HTTP/1.1\r\nHost:")
        f.control("ping")
        require(f.get("/tail") == b"old-tail", "a partial next head blocked the loop")
        sock.sendall(b" t\r\n\r\n")
        require(wire.message()[2] == b"old-tail", "split next head was lost")
        sock.shutdown(socket.SHUT_WR)
        require(sock.recv(1) == b"", "EOF did not take the ordinary close path")
        partial = f.connect()
        partial_wire = Wire(partial)
        partial.sendall(request("/up/partial-close") + b"GET /tail HTTP/1.1\r\nHost:")
        require(partial_wire.message()[2] == b"/up/partial-close=", "exchange before partial close failed")
        partial.shutdown(socket.SHUT_WR)
        tail = partial.recv(4096)
        require(b"HTTP/1.1 200" not in tail, "a partial next request was answered as complete")
        while tail:
            tail = partial.recv(4096)
        f.success = True
    finally:
        f.close()


def mixed(binary, terminate=None):
    f = fixture(binary, "mixed_" + (terminate or "fairness"), delay=.005)
    counts = [0, 0]
    errors = []
    lock = threading.Lock()
    drivers = []
    total = 256
    try:
        quiet = [f.connect() for _ in range(54)]
        quiet[0].sendall(b"GET /tail HTTP/1.1\r\nHost:")
        def drive(index):
            try:
                sock = f.connect()
                wire = Wire(sock)
                for start in range(0, total, 8):
                    sock.sendall(b"".join(request(f"/up/hot{index}/{n}") for n in range(start, start + 8)))
                    for n in range(start, start + 8):
                        require(wire.message()[2] == f"/up/hot{index}/{n}=".encode(), "hot pipeline order changed")
                        with lock:
                            counts[index] += 1
                sock.close()
            except Exception as error:
                errors.append(str(error))
        for index in range(2):
            thread = threading.Thread(target=drive, args=(index,), daemon=True)
            drivers.append(thread)
            thread.start()
        deadline = time.monotonic() + 8
        while min(counts) < 4 and time.monotonic() < deadline and not errors:
            time.sleep(.005)
        require(min(counts) >= 4 and not errors, "both hot clients must begin progressing")
        before = list(counts)
        for verb in ("ping", "status", "reopen", "reload"):
            f.control(verb)
            require(max(counts) < total, "control witness ran only after hot traffic ended")
            require(f.get("/tail") == b"old-tail", "unrelated static request failed under hot/quiet mix")
            require(max(counts) < total, "static peer waited for the hot pipelines to finish")
        deadline = time.monotonic() + 5
        while min(counts[i] - before[i] for i in range(2)) < 1 and time.monotonic() < deadline and not errors:
            time.sleep(.005)
        require(all(counts[i] > before[i] for i in range(2)) and not errors, "both hot clients must progress across control")
        if terminate:
            require(max(counts) < total, "shutdown must be issued with traffic still active")
            f.control(terminate)
            require(max(counts) < total, "shutdown acknowledgement waited for hot traffic to finish")
        for sock in quiet:
            sock.close()
        for thread in drivers:
            thread.join(10)
        require(not any(t.is_alive() for t in drivers), "hot driver did not stop")
        if not terminate:
            require(counts == [total, total] and not errors, "hot pipelines lost work: " + repr((counts, errors)))
        else:
            f.process.wait(timeout=10)
        print("completion mix", terminate or "fairness", "counts", counts, flush=True)
        f.success = True
    finally:
        f.close()
        for thread in drivers:
            thread.join(2)


def drain(binary, forced=False):
    f = fixture(binary, "forced_drain" if forced else "drain", shutdown="100ms" if forced else "5s")
    try:
        sock = f.connect()
        wire = Wire(sock)
        sock.sendall(request("/up/gated-old") + request("/old-only"))
        require(f.backend.seen_gate.wait(5), "old-generation exchange did not begin")
        f.write_conf("new")
        f.control("reload")
        deadline = time.monotonic() + 5
        while f.get("/tail") != b"new-tail":
            require(time.monotonic() < deadline, "new generation did not become current")
            time.sleep(.01)
        if forced:
            require(sock.recv(1) == b"", "forced shutdown revived the old carried request")
            require(f.backend.disconnected.wait(5), "forced shutdown left the old upstream open")
            for _ in range(20):
                require(f.get("/tail") == b"new-tail", "old completion was applied to a reused connection")
            rows = f.access(21)
            require(not any("/old-only" in row or "/up/gated-old" in row for row in rows),
                    "a stopped exchange or its unserved carry was logged/counted as served")
        else:
            f.backend.release.set()
            require(wire.message()[2] == b"/up/gated-old=", "old exchange reply was lost")
            require(wire.message()[2] == b"old-only", "carried request borrowed the new generation")
        f.success = True
    finally:
        f.close()


def owed(binary, chunked=False):
    f = fixture(binary, "owed_chunked" if chunked else "owed_length")
    try:
        sock = f.connect()
        wire = Wire(sock)
        framing = b"Transfer-Encoding: chunked\r\n\r\n5\r\na" if chunked else b"Content-Length: 5\r\n\r\na"
        sock.sendall(request("/up/gated-first") + b"POST /up/owed HTTP/1.1\r\nHost: t\r\n" + framing)
        require(f.backend.seen_gate.wait(5), "first owed-body exchange did not begin")
        f.backend.release.set()
        require(wire.message()[2] == b"/up/gated-first=", "first reply was lost")
        f.control("ping")
        require(f.get("/tail") == b"old-tail", "resumed owed body blocked an unrelated client")
        rest = b"bcde\r\n0\r\n\r\n" if chunked else b"bcde"
        sock.sendall(rest + request("/tail", b"Connection: close\r\n"))
        require(wire.message()[2] == b"/up/owed=abcde", "resumed owed body was corrupted")
        require(wire.message()[2] == b"old-tail", "head following an owed body was lost")
        rows = f.access(4)
        require(len(rows) == 4 and sum("/up/owed" in row for row in rows) == 1,
                "resumed owed body was charged or logged more than once")
        f.success = True
    finally:
        f.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary")
    args = parser.parse_args()
    cases = [("completion_pipeline_order", lambda: pipeline(args.binary)),
             ("completion_ready_next", lambda: ready(args.binary)),
             ("completion_owed_length", lambda: owed(args.binary)),
             ("completion_owed_chunked", lambda: owed(args.binary, True)),
             ("completion_fairness", lambda: mixed(args.binary)),
             ("completion_control_stop", lambda: mixed(args.binary, "stop")),
             ("completion_control_quit", lambda: mixed(args.binary, "quit")),
             ("completion_drain", lambda: drain(args.binary)),
             ("completion_drain_forced", lambda: drain(args.binary, True))]
    failures = 0
    for name, action in cases:
        try:
            action()
            print("PASS", name, flush=True)
        except Exception as error:
            failures += 1
            print("FAIL", name, type(error).__name__, str(error), flush=True)
    return int(failures != 0)


if __name__ == "__main__":
    raise SystemExit(main())
