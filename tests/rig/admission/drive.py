"""Loopback admission and connection-counter witnesses; standard library only."""
import argparse
import os
from pathlib import Path
import re
import resource
import select
import signal
import socket
import subprocess
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
                 connections=16, nofile=None):
        self.binary = str(Path(binary).resolve())
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.port = port()
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
            text = common + "control 127.0.0.1:0;\n"
            http = "metrics on;"
            command = [self.binary, "serve", "-p", str(self.directory), "-c", str(self.config)]
        text += f"http {{ {http} server {{ listen {listen}; root {root}; }} }}\n"
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
                pattern = r"generation-activated gen=1 .*worker=[0-9]+" if workers > 1 else r"generation-activated gen=1"
                until(lambda: len(re.findall(pattern, self.log.read_text())) >= workers,
                      "lobo workers")
                until(lambda: (f"worker {workers}: serving " in self.status()) if workers > 1
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
            sock = self.connect()
            sock.sendall(b"GET /big.bin HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
            try:
                data = sock.recv(2048)
                result += "2" if data.startswith(b"HTTP/1.1 200") else "1"
            except (ConnectionResetError, BrokenPipeError):
                result += "1"
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


def admission(binary, oracle, directory):
    results = {}
    for name, executable, is_oracle in [("oracle", oracle, True), ("lobo", binary, False)]:
        server = Server(executable, directory / name, oracle=is_oracle, workers=2)
        try:
            results[name] = server.downloads(29)
        finally:
            server.close()
    print("admission maps: oracle=" + results["oracle"] + " lobo=" + results["lobo"], flush=True)
    assert results["oracle"] == "2" * 28 + "1", "same-host oracle capacity changed"
    assert results["lobo"] == results["oracle"], "a full hand took a sibling's connection"


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("admission", "counters"))
    parser.add_argument("binary")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--oracle")
    args = parser.parse_args()
    if args.mode == "admission":
        rows = [("shared-listener-first28", lambda: admission(args.binary, args.oracle, args.directory))]
    else:
        rows = [("connections-refused", lambda: refusal(args.binary, args.directory / "refused")),
                ("connections-evicted", lambda: eviction(args.binary, args.directory / "evicted")),
                ("accept-failures-emfile", lambda: accept_failure(args.binary, args.directory / "emfile"))]
    red = 0
    for name, run in rows:
        try:
            run()
            print(f"lobo-admission: ok — [{name}]", flush=True)
        except (AssertionError, OSError, subprocess.SubprocessError) as error:
            red += 1
            print(f"lobo-admission: FAILED — [{name}] {error}", flush=True)
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
