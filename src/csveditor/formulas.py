from __future__ import annotations

import ast
import re
from dataclasses import dataclass

CELL_RE = re.compile(r"\b([A-Z]+)([1-9][0-9]*)\b")
RANGE_RE = re.compile(r"\b([A-Z]+[1-9][0-9]*):([A-Z]+[1-9][0-9]*)\b")


@dataclass
class EvalContext:
    get_raw: callable


def col_to_idx(col: str) -> int:
    idx = 0
    for ch in col:
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def cell_to_pos(cell: str) -> tuple[int, int]:
    m = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell)
    if not m:
        raise ValueError("bad cell")
    return int(m.group(2)) - 1, col_to_idx(m.group(1))


def _coerce_num(v: str) -> float:
    if v == "":
        return 0.0
    return float(v)


def eval_formula(raw: str, ctx: EvalContext, stack: set[str] | None = None) -> str:
    if not raw.startswith("="):
        return raw
    if stack is None:
        stack = set()
    expr = raw[1:].strip()

    def range_vals(a: str, b: str) -> list[str]:
        r1, c1 = cell_to_pos(a)
        r2, c2 = cell_to_pos(b)
        vals = []
        for r in range(min(r1, r2), max(r1, r2) + 1):
            for c in range(min(c1, c2), max(c1, c2) + 1):
                vals.append(resolve_cell(r, c))
        return vals

    def resolve_cell(r: int, c: int) -> str:
        key = f"{r},{c}"
        if key in stack:
            raise RuntimeError("#CYCLE!")
        stack.add(key)
        val = ctx.get_raw(r, c)
        if val.startswith("="):
            out = eval_formula(val, ctx, stack)
        else:
            out = val
        stack.remove(key)
        return out

    safe = expr
    range_tokens: dict[str, str] = {}
    for i, m in enumerate(RANGE_RE.finditer(expr)):
        token = m.group(0)
        key = f"__RANGE_{i}__"
        range_tokens[key] = f'RANGE("{m.group(1)}","{m.group(2)}")'
        safe = safe.replace(token, key)
    for m in CELL_RE.finditer(safe):
        token = m.group(0)
        safe = safe.replace(token, f'CELL("{token}")')
    for k, v in range_tokens.items():
        safe = safe.replace(k, v)
    safe = re.sub(r"(?<![<>])=(?!=)", "==", safe)
    safe = safe.replace("<>", "!=")

    env = {
        "SUM": lambda vals: sum(float(v) for v in vals if _is_num(v)),
        "AVERAGE": lambda vals: (sum(float(v) for v in vals if _is_num(v)) / max(1, sum(1 for v in vals if _is_num(v)))),
        "MIN": lambda vals: min(float(v) for v in vals if _is_num(v)),
        "MAX": lambda vals: max(float(v) for v in vals if _is_num(v)),
        "COUNT": lambda vals: sum(1 for v in vals if _is_num(v)),
        "CONCAT": lambda *vals: "".join(str(v) for v in vals),
        "LEFT": lambda text, n: str(text)[: int(float(n))],
        "RIGHT": lambda text, n: str(text)[-int(float(n)) :],
        "LEN": lambda text: len(str(text)),
        "ROUND": lambda n, d: round(float(n), int(float(d))),
        "IF": lambda cond, t, f: t if cond else f,
        "RANGE": range_vals,
        "CELL": lambda ref: _to_value(resolve_cell(*cell_to_pos(ref))),
    }

    try:
        node = ast.parse(safe, mode="eval")
        _ensure_safe(node)
        val = eval(compile(node, "<formula>", "eval"), {"__builtins__": {}}, env)
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        return str(val)
    except ZeroDivisionError:
        return "#DIV/0!"
    except RuntimeError as e:
        if str(e) == "#CYCLE!":
            return "#CYCLE!"
        return "#ERROR!"
    except Exception:
        return "#ERROR!"


def _is_num(v: str) -> bool:
    try:
        float(v)
        return True
    except Exception:
        return False


def _ensure_safe(node: ast.AST) -> None:
    allowed = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Gt,
        ast.GtE,
        ast.Lt,
        ast.LtE,
        ast.USub,
        ast.UAdd,
        ast.Tuple,
    )
    for n in ast.walk(node):
        if not isinstance(n, allowed):
            raise ValueError("unsafe")


def _to_value(v: str):
    try:
        return float(v)
    except Exception:
        return v
