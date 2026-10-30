#!/usr/bin/env python3
"""Hashlist guardrail checker (DEMO, fictional demo-ecu project).

Tests every change against the rules in guardrails/rules.md.
Python 3.10+ standard library only. No compiler needed: each rule parses C,
the DBC file, the measurements CSV or the golden answers with plain code.

Usage:
  python guardrails/checker.py                      check src/
  python guardrails/checker.py --path DIR           check one draft tree
  python guardrails/checker.py --json               machine readable, for agents
  python guardrails/checker.py --ci                 GitHub annotations + markdown summary
  python guardrails/checker.py --examples           prove every fail draft fails and every pass draft passes

Exit code 0 when everything passes, 1 on any failure.
https://hashlist.com
"""
from __future__ import annotations

import argparse
import ast
import bisect
import csv
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GUARD = REPO / "guardrails"
BOARD = REPO / "board" / "demo-ecu-rev-b"

RULES = {
    "R-001": ("Measured board data beats the datasheet for timing values", "GA-001", "HL-0001-pmic-settle-time"),
    "R-002": ("Scale factors come from the roller check, not the sheet", "GA-002", "HL-0002-wheel-speed-scaling"),
    "R-003": ("CAN signals use the byte order in the DBC", "GA-003", "HL-0003-can-byte-order"),
    "R-004": ("E2E protection uses CRC-8 J1850 and a counter that wraps at 14", "GA-004", "HL-0004-e2e-crc-counter"),
    "R-005": ("Variables shared with an ISR are volatile and read atomically", "GA-005", "HL-0005-isr-shared-variable"),
    "R-006": ("No blocking, printing or allocating calls in ISRs", "GA-006", "HL-0006-isr-blocking-calls"),
    "R-007": ("DMA buffers are cache line aligned and cache maintained", "GA-007", "HL-0007-dma-cache-coherency"),
    "R-008": ("The watchdog is refreshed only in Wdg_MainFunction", "GA-008", "HL-0008-watchdog-refresh"),
    "R-009": ("No dynamic memory outside src/startup", "GA-009", "HL-0009-no-dynamic-memory"),
    "R-010": ("SWCs talk to the bus only through Rte_ calls", "GA-010", "HL-0010-autosar-layer-boundary"),
}


# ----------------------------------------------------------------- data model

@dataclass
class Finding:
    rule: str
    file: str
    line: int
    message: str

    def as_dict(self, golden: dict) -> dict:
        title, ga, report = RULES[self.rule]
        g = golden.get(self.rule, {})
        return {
            "rule": self.rule,
            "title": title,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "golden_answer": {"id": ga, "answer": g.get("answer"), "source": g.get("source"), "not": g.get("not")},
            "failure_report": f"guardrails/failure-reports/{report}.md",
        }


@dataclass
class Fn:
    name: str
    params: str
    start: int  # index of "{"
    end: int    # index of matching "}"


def strip_comments(text: str) -> str:
    """Blank out comments and string contents, keep offsets and newlines."""
    out = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "//":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
        elif two == "/*":
            while i < n and text[i:i + 2] != "*/":
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            out.append("  ")
            i += 2
        elif c in "\"'":
            q = c
            out.append(q)
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    out.append(" ")
                    i += 1
                out.append(" " if text[i] != "\n" else "\n")
                i += 1
            out.append(q)
            i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)[:n]


def match_brace(text: str, i: int) -> int:
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return j
    return len(text) - 1


HEADER_RE = re.compile(
    r"(\w+)\s*\(([^;{}()]*(?:\([^()]*\)[^;{}()]*)*)\)\s*(?:__attribute__\s*\(\(.*?\)\)\s*)?$", re.S)


class Src:
    def __init__(self, rel: str, raw: str):
        self.rel = rel
        self.raw = raw
        self.text = strip_comments(raw)
        self._nl = [m.start() for m in re.finditer("\n", raw)]
        self.fns = self._functions()

    def line(self, pos: int) -> int:
        return bisect.bisect_left(self._nl, pos) + 1

    def _functions(self) -> list[Fn]:
        # blank preprocessor lines so "#define X (1u)" never looks like a header
        t = re.sub(r"^[ \t]*#(?:[^\n]*\\\n)*[^\n]*", lambda m: re.sub(r"[^\n]", " ", m.group(0)),
                   self.text, flags=re.M)
        fns, i, last = [], 0, 0
        while i < len(t):
            c = t[i]
            if c == ";":
                last = i + 1
            elif c == "{":
                j = match_brace(t, i)
                m = HEADER_RE.search(t[last:i])
                if m and m.group(1) not in ("if", "for", "while", "switch"):
                    fns.append(Fn(m.group(1), m.group(2), i, j))
                i = j
                last = j + 1
            i += 1
        return fns

    def body(self, fn: Fn) -> str:
        return self.text[fn.start:fn.end + 1]

    def file_scope(self) -> str:
        """Text with every function body blanked out (globals and macros remain)."""
        chars = list(self.text)
        for fn in self.fns:
            for k in range(fn.start, fn.end + 1):
                if chars[k] != "\n":
                    chars[k] = " "
        return "".join(chars)

    def fn_at(self, pos: int) -> Fn | None:
        for fn in self.fns:
            if fn.start <= pos <= fn.end:
                return fn
        return None

    def defines(self) -> dict[str, str]:
        d = {}
        for m in re.finditer(r"^[ \t]*#[ \t]*define[ \t]+(\w+)(?!\()[ \t]+(.*)$", self.text, re.M):
            d[m.group(1)] = m.group(2).strip()
        return d


class Tree:
    """A source tree to check. Paths are matched relative to its base."""

    def __init__(self, path: Path):
        path = Path(path).resolve()
        if (path / "src").is_dir() or (path / "test").is_dir():
            base = path
        elif path.name in ("src", "test"):
            base = path.parent
        else:
            base = path
        self.base = base
        self.files: list[Src] = []
        roots = [path] if path != base else [base / "src", base / "test"]
        for r in roots:
            if r.is_file():
                cands = [r]
            elif r.is_dir():
                cands = sorted(p for p in r.rglob("*") if p.suffix in (".c", ".h"))
            else:
                cands = []
            for p in cands:
                rel = p.relative_to(base).as_posix()
                self.files.append(Src(rel, p.read_text(encoding="utf-8", errors="replace")))

    def under(self, prefix: str) -> list[Src]:
        return [f for f in self.files if f.rel.startswith(prefix)]

    def src(self) -> list[Src]:
        return self.under("src/")


# --------------------------------------------------------- tiny C expression evaluator

class CEvalError(Exception):
    pass


def expand(expr: str, defs: dict[str, str], depth: int = 0) -> str:
    if depth > 6:
        return expr
    return re.sub(r"\b[A-Za-z_]\w*\b",
                  lambda m: "(" + expand(defs[m.group(0)], defs, depth + 1) + ")" if m.group(0) in defs else m.group(0),
                  expr)


def c_eval(expr: str, env: dict | None = None):
    env = env or {}
    e = re.sub(r"\(\s*(?:const\s+)?(?:u?int(?:8|16|32|64)_t|unsigned(?:\s+int|\s+char)?|float|double)\s*\)", "", expr)
    e = re.sub(r"\b(0[xX][0-9a-fA-F]+|\d+\.?\d*(?:[eE][-+]?\d+)?)[uUlLfF]*(?![\w.])", r"\1", e)
    try:
        tree = ast.parse(e.strip(), mode="eval")
    except SyntaxError as exc:
        raise CEvalError(f"cannot parse '{expr.strip()}'") from exc

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in env:
                return env[n.id]
            raise CEvalError(f"unknown name {n.id}")
        if isinstance(n, ast.UnaryOp):
            v = ev(n.operand)
            if isinstance(n.op, ast.USub):
                return -v
            if isinstance(n.op, ast.UAdd):
                return v
            if isinstance(n.op, ast.Invert):
                return ~int(v)
        if isinstance(n, ast.BinOp):
            a, b = ev(n.left), ev(n.right)
            op = type(n.op)
            if op is ast.Add:
                return a + b
            if op is ast.Sub:
                return a - b
            if op is ast.Mult:
                return a * b
            if op is ast.Div:
                return int(a / b) if isinstance(a, int) and isinstance(b, int) else a / b
            if op is ast.Mod:
                return a % b
            if op is ast.LShift:
                return int(a) << int(b)
            if op is ast.RShift:
                return int(a) >> int(b)
            if op is ast.BitAnd:
                return int(a) & int(b)
            if op is ast.BitOr:
                return int(a) | int(b)
            if op is ast.BitXor:
                return int(a) ^ int(b)
        raise CEvalError(f"unsupported syntax in '{expr.strip()}'")

    return ev(tree)


def c_int(s: str) -> int:
    return int(re.sub(r"[uUlL]+$", "", s.strip()), 0)


# ------------------------------------------------------------------ shared data

def load_golden() -> dict[str, dict]:
    out = {}
    p = GUARD / "golden-answers.jsonl"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                g = json.loads(line)
                out[g["rule"]] = g
    return out


def load_measurements() -> list[dict]:
    rows = []
    p = BOARD / "measurements.csv"
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append(r)
    return rows


def load_dbc_signal(name: str) -> dict:
    text = (BOARD / "demo.dbc").read_text(encoding="utf-8")
    m = re.search(rf"SG_\s+{name}\s*:\s*(\d+)\|(\d+)@([01])([+-])\s*\(([^,]+),([^)]+)\)", text)
    if not m:
        raise KeyError(name)
    return {"start": int(m.group(1)), "len": int(m.group(2)), "intel": m.group(3) == "1",
            "factor": float(m.group(5)), "offset": float(m.group(6))}


def dbc_pack(sig: dict, raw: int, nbytes: int = 8) -> tuple[list[int], list[int]]:
    """Return (bytes, mask) for one signal, following the DBC bit numbering rules."""
    data, mask = [0] * nbytes, [0] * nbytes
    pos = sig["start"]
    for k in range(sig["len"]):
        if sig["intel"]:
            bitpos, bit = sig["start"] + k, (raw >> k) & 1
        else:
            bitpos, bit = pos, (raw >> (sig["len"] - 1 - k)) & 1
            pos = pos + 15 if pos % 8 == 0 else pos - 1
        data[bitpos // 8] |= bit << (bitpos % 8)
        mask[bitpos // 8] |= 1 << (bitpos % 8)
    return data, mask


# ------------------------------------------------------------------------ rules

def r001(tree: Tree) -> list[Finding]:
    out = []
    meas = [m for m in load_measurements() if m.get("symbol")]
    for f in tree.src():
        defs = f.defines()
        for m in meas:
            sym = m["symbol"]
            if sym not in defs:
                continue
            try:
                val = c_eval(expand(defs[sym], defs))
            except CEvalError:
                continue
            need = float(m["value"])
            if val < need:
                pos = re.search(rf"#[ \t]*define[ \t]+{sym}\b", f.text).start()
                out.append(Finding("R-001", f.rel, f.line(pos),
                                   f"{sym} is {val:g} {m['unit']}, board measured {need:g} {m['unit']}"))
    for f in tree.under("test/"):
        for m in meas:
            sym = m["symbol"]
            board = re.search(rf"#[ \t]*define[ \t]+BOARD_{sym}[ \t]+(\S+)", f.text)
            if board and c_int(board.group(1)) != float(m["value"]):
                out.append(Finding("R-001", f.rel, f.line(board.start()),
                                   f"BOARD_{sym} is {board.group(1)}, measurements.csv says {m['value']}"))
            for am in re.finditer(r"\bTEST_ASSERT\w*\s*\(([^;]*);", f.text):
                args = am.group(1)
                if re.search(rf"\b{sym}\b", args) and re.search(r"(?<![\w.])\d+u?\b", args) and f"BOARD_{sym}" not in args:
                    out.append(Finding("R-001", f.rel, f.line(am.start()),
                                       f"test repeats the value of {sym} as a literal"))
    return out


def r002(tree: Tree, golden: dict) -> list[Finding]:
    out = []
    vectors = golden.get("R-002", {}).get("vectors", [])
    tol = golden.get("R-002", {}).get("tolerance_pct", 0.2)
    for f in tree.src():
        defs = f.defines()
        for name, val in defs.items():
            if not name.startswith("WSS_SCALE"):
                continue
            try:
                scale = c_eval(expand(val, defs))
            except CEvalError as exc:
                out.append(Finding("R-002", f.rel, 1, f"cannot evaluate {name}: {exc}"))
                continue
            worst = 0.0
            for v in vectors:
                kmh = v["counts"] * scale
                worst = max(worst, abs(kmh - v["true_kmh"]) / v["true_kmh"] * 100)
            if worst > tol:
                pos = re.search(rf"#[ \t]*define[ \t]+{name}\b", f.text).start()
                out.append(Finding("R-002", f.rel, f.line(pos),
                                   f"wheel speed error {worst:.2f}% against the roller check, limit {tol}%"))
    return out


def r003(tree: Tree) -> list[Finding]:
    out = []
    sig = load_dbc_signal("BrakePressure")
    for f in tree.src():
        for fn in f.fns:
            if fn.name != "BrkStatus_Encode":
                continue
            params = [p.strip() for p in fn.params.split(",")]
            names = [re.findall(r"(\w+)\s*(?:\[[^\]]*\])?\s*$", p)[0] for p in params if p]
            frame_n, raw_n = (names + ["frame", "raw"])[:2]
            stmts = re.findall(rf"\b{frame_n}\s*\[\s*(\d+)\s*\]\s*(\|=|=)\s*([^;]+);", f.body(fn))
            bad = None
            for phys in (100.0, 12.5, 0.1, 409.5):
                raw = round((phys - sig["offset"]) / sig["factor"])
                want, mask = dbc_pack(sig, raw)
                got = [0] * 8
                for idx, op, expr in stmts:
                    i = int(idx)
                    if not any(mask[i:i + 1]):
                        continue
                    try:
                        v = c_eval(expr, {raw_n: raw}) & 0xFF
                    except CEvalError:
                        continue
                    got[i] = v if op == "=" else got[i] | v
                if any((got[i] & mask[i]) != want[i] for i in range(8)):
                    bad = (phys, got, want, mask)
                    break
            if bad:
                phys, got, want, mask = bad
                end = "Intel" if not sig["intel"] else "Motorola"
                g = " ".join(f"{got[i]:02X}" for i in range(8) if mask[i])
                w = " ".join(f"{want[i]:02X}" for i in range(8) if mask[i])
                out.append(Finding("R-003", f.rel, f.line(fn.start),
                                   f"BrakePressure is {'Intel' if sig['intel'] else 'Motorola'} in demo.dbc, "
                                   f"{phys:g} bar encodes to {g}, expected {w} (looks like {end} order)"))
    return out


def crc8(data: bytes, poly: int, init: int, xorout: int) -> int:
    c = init
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c ^ xorout


def r004(tree: Tree) -> list[Finding]:
    out = []
    for f in tree.under("src/e2e/"):
        defs = f.defines()

        def get(suffix):
            for k, v in defs.items():
                if k.endswith(suffix):
                    return k, v
            return None, None

        names = [get(s) for s in ("CRC_POLY", "CRC_INIT", "CRC_XOROUT")]
        if all(n for n, _ in names):
            poly, init, xo = (c_int(v) for _, v in names)
            got = crc8(b"123456789", poly, init, xo)
            if got != 0x4B:
                pos = re.search(rf"#[ \t]*define[ \t]+{names[0][0]}\b", f.text).start()
                out.append(Finding("R-004", f.rel, f.line(pos),
                                   f"CRC-8 check value is 0x{got:02X}, expected 0x4B "
                                   f"(SAE J1850: poly 0x1D, init 0xFF, xorout 0xFF)"))
        elif "CRC" in f.text:
            out.append(Finding("R-004", f.rel, 1, "CRC parameters must be #defines ending in CRC_POLY, CRC_INIT, CRC_XOROUT"))
        k, v = get("COUNTER_MAX")
        if k is None:
            out.append(Finding("R-004", f.rel, 1, "no COUNTER_MAX define, the alive counter must wrap after 14"))
        else:
            used = re.findall(rf"\b{k}\b", f.text)
            pos = re.search(rf"#[ \t]*define[ \t]+{k}\b", f.text).start()
            if c_int(v) != 14:
                out.append(Finding("R-004", f.rel, f.line(pos), f"{k} is {c_int(v)}, the alive counter wraps after 14"))
            elif len(used) < 2:
                out.append(Finding("R-004", f.rel, f.line(pos), f"{k} is defined but never used to wrap the counter"))
    return out


ISR_RE = re.compile(r"_IRQHandler$")
WIDE_RE = re.compile(r"\b(?:u?int64_t|double|unsigned\s+long\s+long|long\s+long)\b")


def isrs(f: Src) -> list[Fn]:
    return [fn for fn in f.fns if ISR_RE.search(fn.name)]


def r005(tree: Tree) -> list[Finding]:
    out = []
    for f in tree.src():
        handlers = isrs(f)
        if not handlers:
            continue
        scope = f.file_scope()
        written = {}
        for h in handlers:
            body = f.body(h)
            for m in re.finditer(r"\b([A-Za-z_]\w*)(?:\s*\[[^\]]*\])?\s*(?:\+\+|--|[-+*/|&^]=|<<=|>>=|=(?!=))", body):
                written.setdefault(m.group(1), h)
            for m in re.finditer(r"(?:\+\+|--)\s*([A-Za-z_]\w*)", body):
                written.setdefault(m.group(1), h)
        for name, h in written.items():
            decl = re.search(rf"([^;{{}}]*?)\b{name}\b\s*(?:\[[^\]]*\])?\s*(?:=[^;]*)?;", scope)
            if not decl or not re.search(r"\b(?:u?int\d+_t|char|int|float|double|bool|_Bool)\b", decl.group(1)):
                continue
            dtext = decl.group(0)
            if "volatile" not in dtext:
                out.append(Finding("R-005", f.rel, f.line(decl.start() + len(decl.group(1))),
                                   f"{name} is written in {h.name} but not volatile"))
            if WIDE_RE.search(dtext):
                for fn in f.fns:
                    if fn in handlers:
                        continue
                    body = f.body(fn)
                    for m in re.finditer(rf"\b{name}\b", body):
                        before, after = body[:m.start()], body[m.end():]
                        guarded = (before.rfind("__disable_irq();") > before.rfind("__enable_irq();")
                                   and "__enable_irq();" in after)
                        if not guarded and "Irq_Snapshot" not in body:
                            out.append(Finding("R-005", f.rel, f.line(fn.start + m.start()),
                                               f"{fn.name} reads 64-bit {name} outside a critical section, "
                                               f"a 32-bit core can return a torn value"))
                            break
    return out


FORBIDDEN_IN_ISR = ["printf", "sprintf", "snprintf", "malloc", "calloc", "realloc", "free", "osDelay",
                    "HAL_Delay", "xQueueSend", "xQueueReceive", "xSemaphoreTake", "osMutexAcquire", "pvPortMalloc"]


def r006(tree: Tree) -> list[Finding]:
    out = []
    pat = re.compile(r"\b(" + "|".join(FORBIDDEN_IN_ISR) + r")\s*\(")
    for f in tree.src():
        for h in isrs(f):
            body = f.body(h)
            for m in pat.finditer(body):
                out.append(Finding("R-006", f.rel, f.line(h.start + m.start()),
                                   f"{m.group(1)}() called inside {h.name}"))
    return out


def r007(tree: Tree) -> list[Finding]:
    out = []
    tx = re.compile(r"\bHAL_(?:UART|SPI|USART)_Transmit(?:Receive)?_DMA\s*\(([^;]*)\)\s*;")
    rx = re.compile(r"\bHAL_(?:UART|SPI|USART)_(?:Receive|TransmitReceive)_DMA\s*\(([^;]*)\)\s*;")
    for f in tree.src():
        defs = f.defines()
        scope = f.file_scope()
        for kind, pat in (("TX", tx), ("RX", rx)):
            for m in pat.finditer(f.text):
                args = [a.strip() for a in m.group(1).split(",")]
                if len(args) < 2:
                    continue
                buf = re.sub(r"^\(.*?\)\s*|^&", "", args[1])
                if not re.fullmatch(r"\w+", buf):
                    continue
                d = re.search(rf"([^;{{}}]*?)\b{buf}\b\s*\[([^\]]*)\]([^;=]*)[;=]", scope)
                if not d:
                    continue
                decl = d.group(1) + d.group(3)
                line = f.line(m.start())
                nocache = '".dma_nocache"' in f.raw[d.start():d.end() + 1] or "dma_nocache" in decl
                if not re.search(r"aligned\s*\(\s*32\s*\)", decl):
                    out.append(Finding("R-007", f.rel, line, f"DMA buffer {buf} is not aligned(32)"))
                try:
                    size = c_eval(expand(d.group(2), defs))
                    if int(size) % 32:
                        out.append(Finding("R-007", f.rel, line,
                                           f"DMA buffer {buf} is {int(size)} bytes, not a multiple of the 32 byte cache line"))
                except CEvalError:
                    pass
                if nocache:
                    continue
                fn = f.fn_at(m.start())
                region = f.text[(fn.start if fn else 0):m.start()]
                if kind == "TX" and not re.search(rf"SCB_CleanDCache_by_Addr\s*\([^;]*\b{buf}\b", region):
                    out.append(Finding("R-007", f.rel, line,
                                       f"no SCB_CleanDCache_by_Addr({buf}) before the DMA transmit, "
                                       f"the D-cache can hold the data the DMA must read"))
                if kind == "RX" and not re.search(rf"SCB_InvalidateDCache_by_Addr\s*\([^;]*\b{buf}\b", f.text):
                    out.append(Finding("R-007", f.rel, line,
                                       f"no SCB_InvalidateDCache_by_Addr({buf}) after DMA receive completes"))
    return out


def r008(tree: Tree) -> list[Finding]:
    out = []
    pat = re.compile(r"\bHAL_IWDG_Refresh\s*\(|\bIWDG\d?\s*->\s*KR\s*=\s*0x?[Aa]{4}")
    for f in tree.src():
        for m in pat.finditer(f.text):
            fn = f.fn_at(m.start())
            if fn is None or fn.name != "Wdg_MainFunction":
                where = fn.name if fn else "file scope"
                out.append(Finding("R-008", f.rel, f.line(m.start()),
                                   f"watchdog refreshed in {where}, only Wdg_MainFunction may refresh it"))
            else:
                before = f.text[fn.start:m.start()]
                if "Wdg_AllAliveOk" not in before:
                    out.append(Finding("R-008", f.rel, f.line(m.start()),
                                       "Wdg_MainFunction refreshes without checking Wdg_AllAliveOk() first"))
    return out


def r009(tree: Tree) -> list[Finding]:
    out = []
    pat = re.compile(r"\b(malloc|calloc|realloc|free|pvPortMalloc|vPortFree)\s*\(")
    for f in tree.src():
        if f.rel.startswith("src/startup/"):
            continue
        for m in pat.finditer(f.text):
            out.append(Finding("R-009", f.rel, f.line(m.start()),
                               f"{m.group(1)}() outside src/startup (MISRA C:2012 Rule 21.3)"))
    return out


def r010(tree: Tree) -> list[Finding]:
    out = []
    pat = re.compile(r"\b((?:Com|CanIf|Can|CanTp|PduR)_\w+)\s*\(")
    inc = re.compile(r'#\s*include\s*[<"](Com|CanIf|Can|PduR)\.h[>"]')
    for f in tree.under("src/swc/"):
        for m in pat.finditer(f.text):
            out.append(Finding("R-010", f.rel, f.line(m.start()),
                               f"SWC calls {m.group(1)}() directly, use the Rte_ API"))
        for m in inc.finditer(f.raw):
            out.append(Finding("R-010", f.rel, f.raw[:m.start()].count("\n") + 1,
                               f"SWC includes {m.group(1)}.h, a layer below the RTE"))
    return out


def run_rules(tree: Tree) -> list[Finding]:
    golden = load_golden()
    found = (r001(tree) + r002(tree, golden) + r003(tree) + r004(tree) + r005(tree) + r006(tree)
             + r007(tree) + r008(tree) + r009(tree) + r010(tree))
    return sorted(found, key=lambda x: (x.rule, x.file, x.line))


# ----------------------------------------------------------------------- output

def rel_to_repo(p: Path) -> str:
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return str(p)


def print_text(findings: list[Finding], tree: Tree, golden: dict) -> None:
    shown = set()
    for f in findings:
        title, ga, report = RULES[f.rule]
        hl = report[:7]
        print(f"checker.py  {f.rule} fail \u00b7 {f.message} (see {hl})")
        print(f"            at {tree_label(tree)}{f.file}:{f.line}")
        if f.rule in shown:
            continue
        shown.add(f.rule)
        g = golden.get(f.rule)
        if g:
            print(f"            golden {ga}: {g['answer']}")
            if g.get("not"):
                print(f"            not: {g['not']}")
        print(f"            report guardrails/failure-reports/{report}.md")
    if findings:
        rules = sorted({f.rule for f in findings})
        print(f"checker.py  fail \u00b7 {len(findings)} finding(s) in {', '.join(rules)}")
    else:
        print("checker.py  pass \u00b7 all rules")


def tree_label(tree: Tree) -> str:
    try:
        r = tree.base.relative_to(REPO).as_posix()
        return "" if r == "." else r + "/"
    except ValueError:
        return ""


def print_ci(findings: list[Finding], tree: Tree, golden: dict) -> None:
    for f in findings:
        path = tree_label(tree) + f.file
        msg = f"{f.message} (see {RULES[f.rule][2]})".replace("\n", " ")
        print(f"::error file={path},line={f.line},title={f.rule} {RULES[f.rule][0]}::{msg}")
    md = ["## Hashlist guardrails (demo)", ""]
    if findings:
        md += ["Blocked. Fix these before merge:", "", "| Rule | Where | Problem | Failure report |", "|---|---|---|---|"]
        for f in findings:
            md.append(f"| {f.rule} | `{tree_label(tree)}{f.file}:{f.line}` | {f.message} | "
                      f"`guardrails/failure-reports/{RULES[f.rule][2]}.md` |")
    else:
        md.append("pass · all rules")
    text = "\n".join(md) + "\n"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)


def check_examples(as_json: bool) -> int:
    """Every examples/HL-N/fail must fail with exactly rule R-N, every pass tree must pass."""
    ex = REPO / "examples"
    results, bad = [], 0
    for d in sorted(ex.glob("HL-*")):
        n = int(d.name.split("-")[1])
        rule = f"R-{n:03d}"
        failed = sorted({f.rule for f in run_rules(Tree(d / "fail"))})
        passed = run_rules(Tree(d / "pass"))
        ok = failed == [rule] and not passed
        bad += 0 if ok else 1
        results.append({"example": d.name, "rule": rule, "fail_tree_rules": failed,
                        "pass_tree_findings": len(passed), "ok": ok})
    if as_json:
        print(json.dumps({"status": "pass" if not bad else "fail", "examples": results}, indent=2))
    else:
        for r in results:
            caught = ", ".join(r["fail_tree_rules"]) or "nothing"
            state = "pass" if r["pass_tree_findings"] == 0 else f"{r['pass_tree_findings']} finding(s)"
            mark = "ok  " if r["ok"] else "BAD "
            print(f"{mark}{r['example']}  fail draft caught by {caught} · fixed draft: {state}")
        print(f"checker.py  {'pass' if not bad else 'fail'} · {len(results) - bad} of {len(results)} scenarios behave as expected")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Hashlist guardrail checker (demo)")
    ap.add_argument("--path", default=str(REPO / "src"), help="tree to check (default: src/)")
    ap.add_argument("--json", action="store_true", help="machine readable output for agents")
    ap.add_argument("--ci", action="store_true", help="GitHub annotations and markdown summary")
    ap.add_argument("--examples", action="store_true", help="check that fail drafts fail and pass drafts pass")
    a = ap.parse_args(argv)
    if a.examples:
        return check_examples(a.json)
    tree = Tree(Path(a.path))
    golden = load_golden()
    findings = run_rules(tree)
    if a.json:
        print(json.dumps({"status": "fail" if findings else "pass", "checked_files": len(tree.files),
                          "findings": [f.as_dict(golden) for f in findings]}, indent=2))
    elif a.ci:
        print_ci(findings, tree, golden)
    else:
        print_text(findings, tree, golden)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
