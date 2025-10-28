import time
import psutil
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Set, Tuple, List, Optional


@dataclass
class NetSample:
    timestamp: float
    io_counters: Dict[str, psutil._common.snetio]  # interface -> snetio
    conns: Set[Tuple[str, int, str, int, str]]  # (laddr.ip, laddr.port, raddr.ip, raddr.port, status, pid)
    proc_map: Dict[int, str]  # pid -> name


def sample_network() -> NetSample:
    ts = time.time()
    io = psutil.net_io_counters(pernic=True)
    conns = set()
    proc_map = {}
    for c in psutil.net_connections(kind='inet'):
        laddr = c.laddr.ip if c.laddr else ""
        lport = c.laddr.port if c.laddr else 0
        raddr = c.raddr.ip if c.raddr else ""
        rport = c.raddr.port if c.raddr else 0
        status = c.status or ""
        pid = c.pid or 0
        proc_name = ""
        try:
            if pid:
                p = psutil.Process(pid)
                proc_name = p.name()
                proc_map[pid] = proc_name
        except Exception:
            proc_name = ""
        conns.add((laddr, lport, raddr, rport, status, pid))
    return NetSample(timestamp=ts, io_counters=io, conns=conns, proc_map=proc_map)


def diff_io(prev: Dict[str, psutil._common.snetio], cur: Dict[str, psutil._common.snetio], dt: float):
    res = {}
    for nic, curc in cur.items():
        prevc = prev.get(nic)
        if not prevc:
            continue
        sent = (curc.bytes_sent - prevc.bytes_sent) / dt
        recv = (curc.bytes_recv - prevc.bytes_recv) / dt
        res[nic] = (max(0, sent), max(0, recv))
    return res


class Sentinel:
    def __init__(self, config: dict):
        self.interval = float(config.get("general", {}).get("interval_seconds", 5))
        self.baseline_samples = int(config.get("general", {}).get("baseline_samples", 3))
        thr = config.get("thresholds", {})
        self.bytes_per_sec_threshold = int(thr.get("bytes_per_sec_threshold", 5_000_000))
        self.many_connections_threshold = int(thr.get("many_connections_threshold", 50))
        self.log_file = config.get("general", {}).get("log_file", "net_sentinel_events.jsonl")

        self.baseline_conns = set()
        self.last_sample: Optional[NetSample] = None
        self._startup_samples: List[NetSample] = []

        open(self.log_file, "a").close()

    def _log_event(self, ev: dict):
        ev["detected_at"] = time.time()
        with open(self.log_file, "a") as f:
            f.write(json.dumps(ev) + "\n")

    def _print_and_log(self, ev: dict):
        print(f"[ALERT] {ev.get('title')} - {ev.get('detail')}")
        self._log_event(ev)

    def build_baseline(self):
        print(f"[+] Building baseline using {self.baseline_samples} samples (interval {self.interval}s)...")
        for i in range(self.baseline_samples):
            s = sample_network()
            self._startup_samples.append(s)
            time.sleep(self.interval)
        base_conns = set()
        for s in self._startup_samples:
            for c in s.conns:
                base_conns.add(c)
        self.baseline_conns = base_conns
        self.last_sample = self._startup_samples[-1]
        print(f"[+] Baseline ready: {len(self.baseline_conns)} connections recorded.")

    def analyze(self, cur: NetSample):
        now = time.time()
        prev = self.last_sample
        if prev is None:
            self.last_sample = cur
            return

        dt = max(1.0, cur.timestamp - prev.timestamp)

        io_diff = diff_io(prev.io_counters, cur.io_counters, dt)
        for nic, (bps_sent, bps_recv) in io_diff.items():
            if bps_sent > self.bytes_per_sec_threshold or bps_recv > self.bytes_per_sec_threshold:
                ev = {
                    "title": "High throughput on interface",
                    "detail": f"{nic}: sent={int(bps_sent)} B/s recv={int(bps_recv)} B/s threshold={self.bytes_per_sec_threshold}",
                    "interface": nic,
                    "bytes_sent_per_sec": int(bps_sent),
                    "bytes_recv_per_sec": int(bps_recv),
                    "severity": "high"
                }
                self._print_and_log(ev)

        new_conns = []
        for c in cur.conns:
            raddr = c[2]
            if raddr:
                if c not in self.baseline_conns and c not in (prev.conns if prev else set()):
                    new_conns.append(c)
        if new_conns:
            for c in new_conns:
                laddr, lport, raddr, rport, status, pid = c
                proc = cur.proc_map.get(pid, "")
                ev = {
                    "title": "New outbound connection",
                    "detail": f"{proc or pid} -> {raddr}:{rport} ({status})",
                    "local": f"{laddr}:{lport}",
                    "remote": f"{raddr}:{rport}",
                    "pid": pid,
                    "process": proc,
                    "severity": "medium"
                }
                self._print_and_log(ev)

        pid_count: Dict[int, int] = {}
        for c in cur.conns:
            pid = c[5]
            if pid:
                pid_count[pid] = pid_count.get(pid, 0) + 1
        for pid, cnt in pid_count.items():
            if cnt >= self.many_connections_threshold:
                proc = cur.proc_map.get(pid, "")
                ev = {
                    "title": "Process with many connections",
                    "detail": f"pid={pid} name={proc} connections={cnt}",
                    "pid": pid,
                    "process": proc,
                    "conn_count": cnt,
                    "severity": "high"
                }
                self._print_and_log(ev)

        self.last_sample = cur

    def run_once(self):
        s = sample_network()
        self.analyze(s)

    def run_loop(self):
        try:
            while True:
                s = sample_network()
                self.analyze(s)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            print("\\n[+] net_sentinel exiting cleanly.")
