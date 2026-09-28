#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import html
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

TERMINAL_STATES = {"SUCCEEDED", "FAILED", "BLOCKED"}
URL_RE = re.compile(r"https?://[^\s'\"<>]+")
PORT_RE = re.compile(r"(?<!\d)(?:localhost|127\.0\.0\.1|0\.0\.0\.0)?[: ](\d{2,5})(?!\d)")
IMPORT_RE = re.compile(r"\b(?:from|import|require\s*\(|from\s+['\"])([A-Za-z0-9_./@-]+)")
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_$.]*)\s*\(")


@dataclass
class TimelineTask:
    task_id: str
    dependencies: List[str]
    resource_path: str
    execution_command: str
    target_host: str
    target_ports: List[int]
    search_refs: List[str]
    max_memory_mb: int
    timeout_sec: int
    max_retries: int
    idempotency_mode: str
    foundry: str = ""
    sector: str = ""
    required_work: str = ""


@dataclass
class FileProfile:
    path: str
    exists: bool
    size_bytes: int
    lines_of_code: int
    sha256: str
    language: str
    cyclomatic_complexity: int
    imports: List[str]
    calls: List[str]
    urls: List[str]
    declared_ports: List[int]


@dataclass
class TimelineEvent:
    seq: int
    task_id: str
    event: str
    at_ns: int
    detail: Dict[str, object]


class DynamicTimelineKernel:
    """
    Spreadsheet -> deterministic graph compiler -> execution/readback ledger -> HTML projection.

    The timeline is not the scheduler. It derives graph, resource and relationship state,
    then executes only explicitly bound commands. A state is promoted only from direct evidence.
    """

    def __init__(self, config_path: Path, root: Path, ledger_path: Path):
        self.config_path = config_path
        self.root = root.resolve()
        self.ledger_path = ledger_path
        self.tasks: Dict[str, TimelineTask] = {}
        self.children: Dict[str, List[str]] = defaultdict(list)
        self.parents: Dict[str, List[str]] = defaultdict(list)
        self.state: Dict[str, str] = {}
        self.events: List[TimelineEvent] = []
        self.profiles: Dict[str, FileProfile] = {}
        self._load_config()
        self._compile_graph()

    def _load_config(self) -> None:
        with self.config_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            required = {
                "Task_ID", "Dependencies", "Resource_Path", "Execution_Command",
                "Target_Host", "Target_Ports", "Search_Refs", "Max_Memory_MB",
                "Timeout_Sec", "Max_Retries", "Idempotency_Mode"
            }
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"TIMELINE_SCHEMA_MISSING:{sorted(missing)}")

            for row in reader:
                task_id = (row["Task_ID"] or "").strip()
                if not task_id:
                    continue
                if task_id in self.tasks:
                    raise ValueError(f"DUPLICATE_TASK_ID:{task_id}")

                deps = self._split(row["Dependencies"])
                ports = [int(v) for v in self._split(row["Target_Ports"])]
                for p in ports:
                    if p < 1 or p > 65535:
                        raise ValueError(f"INVALID_PORT:{task_id}:{p}")

                task = TimelineTask(
                    task_id=task_id,
                    dependencies=deps,
                    resource_path=(row["Resource_Path"] or "").strip(),
                    execution_command=(row["Execution_Command"] or "").strip(),
                    target_host=(row["Target_Host"] or "").strip() or "127.0.0.1",
                    target_ports=ports,
                    search_refs=self._split(row["Search_Refs"]),
                    max_memory_mb=self._bounded_int(row["Max_Memory_MB"], 128, 16, 65536),
                    timeout_sec=self._bounded_int(row["Timeout_Sec"], 60, 1, 86400),
                    max_retries=self._bounded_int(row["Max_Retries"], 1, 1, 10),
                    idempotency_mode=(row["Idempotency_Mode"] or "IDEMPOTENT").strip().upper(),
                    foundry=(row.get("Foundry") or "").strip(),
                    sector=(row.get("Sector") or "").strip(),
                    required_work=(row.get("Required_Work") or "").strip(),
                )
                if task.idempotency_mode not in {"IDEMPOTENT", "NEVER"}:
                    raise ValueError(f"INVALID_IDEMPOTENCY_MODE:{task_id}:{task.idempotency_mode}")
                self.tasks[task_id] = task
                self.state[task_id] = "DECLARED"

    @staticmethod
    def _split(value: Optional[str]) -> List[str]:
        if not value:
            return []
        value = value.strip()
        if not value or value.upper() == "NONE":
            return []
        return [x.strip() for x in value.split(",") if x.strip()]

    @staticmethod
    def _bounded_int(value: Optional[str], default: int, low: int, high: int) -> int:
        try:
            n = int(float(value or default))
        except Exception:
            n = default
        return max(low, min(high, n))

    def _compile_graph(self) -> None:
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise ValueError(f"UNKNOWN_DEPENDENCY:{task.task_id}:{dep}")
                self.children[dep].append(task.task_id)
                self.parents[task.task_id].append(dep)

        scc = self._tarjan_scc()
        cycles = [component for component in scc if len(component) > 1]
        self_loops = [tid for tid in self.tasks if tid in self.children.get(tid, [])]
        if cycles or self_loops:
            raise ValueError(f"DEPENDENCY_CYCLE:{cycles}:{self_loops}")

    def _tarjan_scc(self) -> List[List[str]]:
        index = 0
        stack: List[str] = []
        on_stack: Set[str] = set()
        indices: Dict[str, int] = {}
        low: Dict[str, int] = {}
        result: List[List[str]] = []

        def strongconnect(v: str) -> None:
            nonlocal index
            indices[v] = index
            low[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in self.children.get(v, []):
                if w not in indices:
                    strongconnect(w)
                    low[v] = min(low[v], low[w])
                elif w in on_stack:
                    low[v] = min(low[v], indices[w])

            if low[v] == indices[v]:
                component: List[str] = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == v:
                        break
                result.append(component)

        for v in self.tasks:
            if v not in indices:
                strongconnect(v)
        return result

    def topological_order(self) -> List[str]:
        indegree = {tid: len(self.parents.get(tid, [])) for tid in self.tasks}
        queue = deque(sorted(tid for tid, degree in indegree.items() if degree == 0))
        out: List[str] = []
        while queue:
            u = queue.popleft()
            out.append(u)
            for v in sorted(self.children.get(u, [])):
                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)
        if len(out) != len(self.tasks):
            raise RuntimeError("TOPOLOGICAL_ORDER_INCOMPLETE")
        return out

    def profile_file(self, relative: str) -> FileProfile:
        if relative in self.profiles:
            return self.profiles[relative]

        candidate = (self.root / relative).resolve()
        if not str(candidate).startswith(str(self.root)):
            raise ValueError(f"RESOURCE_PATH_ESCAPE:{relative}")

        if not candidate.is_file():
            profile = FileProfile(relative, False, 0, 0, "", "unknown", 0, [], [], [], [])
            self.profiles[relative] = profile
            return profile

        data = candidate.read_bytes()
        text = data.decode("utf-8", errors="ignore")
        suffix = candidate.suffix.lower()
        language = {
            ".py": "python", ".ts": "typescript", ".tsx": "typescript",
            ".js": "javascript", ".jsx": "javascript", ".html": "html",
            ".json": "json", ".sql": "sql", ".sh": "shell"
        }.get(suffix, suffix.lstrip(".") or "unknown")

        complexity = 1
        imports: Set[str] = set()
        calls: Set[str] = set()

        if language == "python":
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match, ast.BoolOp, ast.comprehension)):
                        complexity += 1
                    if isinstance(node, ast.Import):
                        imports.update(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        imports.add(node.module or "")
                    elif isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            calls.add(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            calls.add(node.func.attr)
            except SyntaxError:
                complexity = -1
        else:
            complexity += len(re.findall(r"\b(if|for|while|catch|case|&&|\|\||\?)\b", text))
            imports.update(m.group(1) for m in IMPORT_RE.finditer(text))
            calls.update(m.group(1) for m in CALL_RE.finditer(text))

        urls = sorted(set(URL_RE.findall(text)))
        ports = sorted({int(p) for p in PORT_RE.findall(text) if 1 <= int(p) <= 65535})
        profile = FileProfile(
            path=relative,
            exists=True,
            size_bytes=len(data),
            lines_of_code=text.count("\n") + (1 if text else 0),
            sha256=hashlib.sha256(data).hexdigest(),
            language=language,
            cyclomatic_complexity=complexity,
            imports=sorted(x for x in imports if x),
            calls=sorted(calls)[:500],
            urls=urls,
            declared_ports=ports,
        )
        self.profiles[relative] = profile
        return profile

    def relation_map(self, task: TimelineTask, profile: FileProfile) -> Dict[str, object]:
        return {
            "dependencies": task.dependencies,
            "children": sorted(self.children.get(task.task_id, [])),
            "declared_target": {
                "host": task.target_host,
                "ports": task.target_ports,
                "search_refs": task.search_refs,
            },
            "observed_source": {
                "imports": profile.imports,
                "calls": profile.calls,
                "urls": profile.urls,
                "declared_ports": profile.declared_ports,
            },
        }

    def probe_ports(self, host: str, ports: List[int], timeout: float = 1.0) -> Dict[int, bool]:
        result: Dict[int, bool] = {}
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result[port] = sock.connect_ex((host, port)) == 0
        return result

    def derive_budget(self, task: TimelineTask, profile: FileProfile) -> Dict[str, object]:
        density = max(1, profile.lines_of_code) + max(1, profile.cyclomatic_complexity) * 8
        size_factor = max(1, profile.size_bytes // 4096)
        baseline_ms = min(task.timeout_sec * 1000, 250 + density * 2 + size_factor * 15)
        return {
            "logical_file_size_bytes": profile.size_bytes,
            "lines_of_code": profile.lines_of_code,
            "cyclomatic_complexity": profile.cyclomatic_complexity,
            "derived_baseline_ms": baseline_ms,
            "timeout_ms": task.timeout_sec * 1000,
            "max_memory_mb": task.max_memory_mb,
            "retry_budget": task.max_retries,
            "idempotency_mode": task.idempotency_mode,
        }

    def emit(self, task_id: str, event: str, **detail: object) -> None:
        self.events.append(TimelineEvent(len(self.events) + 1, task_id, event, time.time_ns(), detail))

    def execute(self) -> Dict[str, object]:
        for task_id in self.topological_order():
            task = self.tasks[task_id]
            profile = self.profile_file(task.resource_path)
            self.emit(task_id, "STATIC_ANALYSIS", profile=asdict(profile))
            self.emit(task_id, "RELATIONSHIP_MAP", relations=self.relation_map(task, profile))
            self.emit(task_id, "DYNAMIC_BUDGET", budget=self.derive_budget(task, profile))

            if not profile.exists:
                self.state[task_id] = "BLOCKED"
                self.emit(task_id, "BLOCKED", reason="RESOURCE_NOT_FOUND")
                continue

            if any(self.state.get(dep) != "SUCCEEDED" for dep in task.dependencies):
                self.state[task_id] = "BLOCKED"
                self.emit(task_id, "BLOCKED", reason="DEPENDENCY_NOT_SUCCEEDED")
                continue

            ports = self.probe_ports(task.target_host, task.target_ports)
            self.emit(task_id, "PORT_READBACK", host=task.target_host, ports=ports)
            if task.target_ports and not all(ports.values()):
                self.state[task_id] = "BLOCKED"
                self.emit(task_id, "BLOCKED", reason="REQUIRED_PORT_UNAVAILABLE")
                continue

            if not task.execution_command:
                self.state[task_id] = "IMPLEMENTED"
                self.emit(task_id, "IMPLEMENTED", reason="NO_EXECUTION_COMMAND_BOUND")
                continue

            argv = shlex.split(task.execution_command)
            idempotency_key = hashlib.sha256(
                json.dumps({"task": task_id, "argv": argv, "sha256": profile.sha256}, sort_keys=True).encode()
            ).hexdigest()
            attempts = 1 if task.idempotency_mode == "NEVER" else task.max_retries
            success = False

            for attempt in range(1, attempts + 1):
                started = time.monotonic_ns()
                self.state[task_id] = "EXECUTING"
                self.emit(task_id, "EXECUTION_STARTED", attempt=attempt, argv=argv, idempotency_key=idempotency_key)
                try:
                    cp = subprocess.run(
                        argv,
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        timeout=task.timeout_sec,
                        check=False,
                    )
                    elapsed_ms = (time.monotonic_ns() - started) / 1_000_000
                    evidence = {
                        "attempt": attempt,
                        "exit_code": cp.returncode,
                        "latency_ms": round(elapsed_ms, 3),
                        "stdout": cp.stdout[-20000:],
                        "stderr": cp.stderr[-20000:],
                        "idempotency_key": idempotency_key,
                    }
                    self.emit(task_id, "EXECUTION_RESULT", **evidence)
                    if cp.returncode == 0:
                        self.state[task_id] = "SUCCEEDED"
                        success = True
                        break
                except subprocess.TimeoutExpired as exc:
                    elapsed_ms = (time.monotonic_ns() - started) / 1_000_000
                    self.emit(task_id, "EXECUTION_TIMEOUT", attempt=attempt, latency_ms=round(elapsed_ms, 3), timeout_sec=task.timeout_sec)

                if attempt < attempts:
                    # Deterministic retry interval. Jitter belongs in a scheduler when collision
                    # avoidance is required; the compiler records the policy rather than injecting randomness.
                    delay_ms = min(5000, 250 * (2 ** (attempt - 1)))
                    self.emit(task_id, "RETRY_SCHEDULED", attempt=attempt + 1, delay_ms=delay_ms)
                    time.sleep(delay_ms / 1000)

            if not success:
                self.state[task_id] = "FAILED"
                self.emit(task_id, "FAILED", reason="EXECUTION_BUDGET_EXHAUSTED")

        report = self.report()
        self.ledger_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report

    def report(self) -> Dict[str, object]:
        return {
            "schema": "braink.dynamic-timeline.v1",
            "source_config": str(self.config_path),
            "root": str(self.root),
            "topological_order": self.topological_order(),
            "states": self.state,
            "profiles": {k: asdict(v) for k, v in self.profiles.items()},
            "events": [asdict(e) for e in self.events],
        }

    def write_html(self, output: Path) -> None:
        cards = []
        for tid in self.topological_order():
            task = self.tasks[tid]
            profile = self.profiles.get(task.resource_path) or self.profile_file(task.resource_path)
            state = self.state.get(tid, "DECLARED")
            relations = self.relation_map(task, profile)
            cards.append(f"""
<section class="task" data-state="{html.escape(state)}">
  <header><strong>{html.escape(tid)}</strong><span>{html.escape(state)}</span></header>
  <p>{html.escape(task.required_work or task.sector or task.resource_path)}</p>
  <dl>
    <dt>Resource</dt><dd>{html.escape(task.resource_path)}</dd>
    <dt>Logical size</dt><dd>{profile.size_bytes} bytes / {profile.lines_of_code} LOC / complexity {profile.cyclomatic_complexity}</dd>
    <dt>Dependencies</dt><dd>{html.escape(", ".join(task.dependencies) or "none")}</dd>
    <dt>Target</dt><dd>{html.escape(task.target_host)}:{html.escape(",".join(map(str, task.target_ports)) or "none")}</dd>
    <dt>Calls/imports</dt><dd>{html.escape(", ".join((profile.imports + profile.calls)[:25]) or "none observed")}</dd>
    <dt>Search refs</dt><dd>{html.escape(", ".join(task.search_refs) or "none")}</dd>
  </dl>
</section>""")

        payload = html.escape(json.dumps(self.report(), separators=(",", ":")))
        output.write_text(f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BrainK Dynamic Execution Timeline</title>
<style>
:root{{font-family:ui-sans-serif,system-ui;background:#0b0d10;color:#e8edf3}}
body{{margin:0}} header.top{{position:sticky;top:0;background:#11151bcc;padding:14px 20px;border-bottom:1px solid #27303b;backdrop-filter:blur(8px)}}
main{{max-width:1100px;margin:auto;padding:20px}} .grid{{display:grid;gap:12px}}
.task{{border:1px solid #27303b;border-radius:12px;padding:14px;background:#11151b}}
.task header{{display:flex;justify-content:space-between;gap:16px}} .task header span{{font:12px ui-monospace}}
dl{{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;font-size:13px}}dt{{color:#9aa8b8}}dd{{margin:0;overflow-wrap:anywhere}}
[data-state="SUCCEEDED"]{{border-color:#267a54}}[data-state="FAILED"],[data-state="BLOCKED"]{{border-color:#94464c}}[data-state="EXECUTING"]{{border-color:#9b7b2f}}
small{{color:#8795a5}}
</style>
<header class="top"><strong>BrainK Dynamic Execution Timeline</strong><br><small>Spreadsheet → static analysis → relations → constraints → execution/readback → evidence</small></header>
<main><div class="grid">{''.join(cards)}</div></main>
<script id="braink-timeline-state" type="application/json">{payload}</script>
</html>
""", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path, default=Path("dynamic_timeline_evidence.json"))
    parser.add_argument("--html", type=Path, default=Path("dynamic_timeline.html"))
    args = parser.parse_args()

    kernel = DynamicTimelineKernel(args.config, args.root, args.ledger)
    report = kernel.execute()
    kernel.write_html(args.html)
    print(json.dumps({
        "status": "PASS" if all(v in {"SUCCEEDED", "IMPLEMENTED"} for v in report["states"].values()) else "PARTIAL",
        "states": report["states"],
        "ledger": str(args.ledger),
        "html": str(args.html),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
