"""Per-wake token ledger, so Perro can see what it spends.

The prompt tells Perro that wake-ups cost its owner money, but until now the
only record was the raw counts on each "sleep" log line. This keeps running
totals in home/spend.json (machine state, like dream.state — never in
home.json, which is the owner's config): today's wakes and tokens, plus
all-time totals, with the day rolling over at local midnight.

Tokens are the honest unit here: no prices are baked in, because pricing
moves and differs per backend. The model already knows wake-ups cost money;
this shows it how much of them it is using.
"""

import json
from datetime import datetime
from pathlib import Path

STATE_FILE = "spend.json"


def _today() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def _blank_day(day: str) -> dict:
    return {"day": day, "wakes": 0, "in": 0, "cached": 0, "out": 0}


def _load(home: Path) -> dict:
    path = home / STATE_FILE
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(state.get("today"), dict) and isinstance(state.get("total"), dict):
            return state
    except (OSError, ValueError):
        pass
    return {"today": _blank_day(_today()),
            "total": {"wakes": 0, "in": 0, "cached": 0, "out": 0}}


def record(home: Path, tokens_in: int, tokens_cached: int, tokens_out: int) -> None:
    """Add one finished wake-up's tokens to the ledger."""
    home = Path(home)
    home.mkdir(parents=True, exist_ok=True)
    state = _load(home)
    if state["today"].get("day") != _today():
        state["today"] = _blank_day(_today())
    for section in ("today", "total"):
        bucket = state[section]
        bucket["wakes"] += 1
        bucket["in"] += tokens_in
        bucket["cached"] += tokens_cached
        bucket["out"] += tokens_out
    (home / STATE_FILE).write_text(json.dumps(state), encoding="utf-8")


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def describe(home: Path) -> str:
    """One or two lines for the wake-up page."""
    state = _load(Path(home))
    t, total = state["today"], state["total"]
    line = (f"Today ({t['day']}): {t['wakes']} wake-up(s), {_fmt(t['in'])} tokens in "
            f"({_fmt(t['cached'])} cached), {_fmt(t['out'])} out.")
    if total["wakes"] > t["wakes"]:
        line += (f" All time: {total['wakes']} wake-ups, {_fmt(total['in'])} in "
                 f"({_fmt(total['cached'])} cached), {_fmt(total['out'])} out.")
    return line + " Wake-ups cost your owner money; don't wake often for nothing."
