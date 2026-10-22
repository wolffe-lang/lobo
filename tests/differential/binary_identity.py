#!/usr/bin/env python3
"""Linux black-box worker-image witness; never reads nginx's source.

Run inside a container, with taskset -c 0-3 and ulimit -c 0:
  python3 -I tests/differential/binary_identity.py --nginx tests/differential/bin/nginx
A copied pinned oracle suffices. --expect-reexec plants the opposite
expectation, which must fail: a fresh worker does not execute the new path.
"""
import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import tempfile
import time


def poll(fn, description, seconds=15):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        result = fn()
        if result:
            return result
        time.sleep(0.02)
    raise AssertionError(description)


def children(pid):
    return [int(p) for p in Path(f"/proc/{pid}/task/{pid}/children").read_text().split()]


def identity(path):
    st = Path(path).stat()
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns


def get(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1) as sock:
            sock.sendall(b"GET / HTTP/1.0\r\nHost: x\r\n\r\n")
            data = b""
            while True:
                piece = sock.recv(4096)
                if not piece:
                    return data
                data += piece
    except OSError:
        return b""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--nginx", type=Path, required=True)
    ap.add_argument("--expect-reexec", action="store_true")
    args = ap.parse_args()
    oracle = args.nginx.resolve()
    version = subprocess.run([str(oracle), "-v"], capture_output=True, check=True).stderr.decode().strip()
    assert version == "nginx version: nginx/1.30.4", version
    print(version, flush=True)
    # Inside the checkout: all processes and files belong to this witness.
    target = Path("target")
    target.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ws72-nginx-", dir=target) as scratch:
        d = Path(scratch).resolve()
        binary = d / "nginx"
        shutil.copy2(oracle, binary)
        (d / "html").mkdir()
        (d / "html/index.html").write_text("ws72-old-image\n")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        conf = d / "nginx.conf"
        user = "user root;" if os.geteuid() == 0 else ""
        conf.write_text(f"{user}\ndaemon off; master_process on; worker_processes 2;\n"
                        f"pid {d}/nginx.pid; error_log {d}/error.log notice;\n"
                        f"events {{ worker_connections 64; }}\nhttp {{ access_log off; "
                        f"server {{ listen 127.0.0.1:{port}; root {d}/html; }} }}\n")
        with (d / "stderr").open("wb") as log:
            master = subprocess.Popen([str(binary), "-p", str(d), "-c", str(conf)],
                                      stdout=log, stderr=log)
            try:
                old_workers = poll(lambda: children(master.pid) if len(children(master.pid)) == 2 else None,
                                   "two nginx workers")
                poll(lambda: b"ws72-old-image" in get(port), "initial nginx service")
                old_image = identity(f"/proc/{master.pid}/exe")
                replacement = d / "nginx.new"
                shutil.copy2(binary, replacement)
                with replacement.open("ab") as out:
                    out.write(b"x")
                replacement.replace(binary)
                new_image = identity(binary)
                assert old_image[:2] != new_image[:2] and old_image[2] + 1 == new_image[2]
                victim = old_workers[0]
                print(Path(f"/proc/{master.pid}/status").read_text().split("SigBlk:")[1].split("\n")[:1], flush=True)
                for pid in old_workers:
                    print(f"nginx worker {pid}: " + "; ".join(line for line in
                          Path(f"/proc/{pid}/status").read_text().splitlines()
                          if line.startswith(("SigBlk:", "SigIgn:"))), flush=True)
                os.kill(victim, signal.SIGTERM)
                workers = poll(lambda: current if len(current := children(master.pid)) == 2 and
                               victim not in current and set(current) != set(old_workers) else None,
                               "nginx replacement worker")
                fresh = next(pid for pid in workers if pid not in old_workers)
                replacement_image = identity(f"/proc/{fresh}/exe")
                print(f"startup={old_image} path-now={new_image} replacement={replacement_image}", flush=True)
                expected = new_image if args.expect_reexec else old_image
                assert replacement_image == expected, "nginx replacement image (opposite expectation is the plant)"
                assert all(identity(f"/proc/{pid}/exe") == old_image for pid in workers)
                assert b"ws72-old-image" in get(port), "nginx survivor/replacement still serves"
                print("GREEN nginx: two workers; replacement forks the old image, none execs the new path", flush=True)
                print("DELTA binary identity: nginx replaces from its old master image; lobo refuses a changed path", flush=True)
            finally:
                if master.poll() is None:
                    master.terminate()
                try:
                    master.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Only this witness's recorded child and its children.
                    for pid in children(master.pid):
                        os.kill(pid, signal.SIGKILL)
                    master.kill()
                    master.wait(timeout=5)


if __name__ == "__main__":
    main()
