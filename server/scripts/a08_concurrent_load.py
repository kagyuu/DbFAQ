"""A08: 同時利用者 10 名の負荷(docs/P009-acceptance-direction/A08-concurrent-users.md)

10 人の仮想利用者が同時に、ER 図の取得 → テーブル詳細 → データタブの 1・2 ページ目を繰り返す。
すべての応答が 200 で、各操作が P001 §8.1 の目標内なら終了コード 0。

使い方: uv run python scripts/a08_concurrent_load.py [--base URL] [--users 10] [--rounds 10]
"""

import argparse
import asyncio
import random
import statistics
import sys
import time

import httpx

TABLES = ["COUNTRIES", "DEPARTMENTS", "EMPLOYEES", "JOBS", "JOB_HISTORY", "LOCATIONS", "REGIONS"]
LIMIT_SEC = 1.0  # P001 §8.1: ER 図 1 秒、データ 1 ページは Oracle の処理時間 + 1 秒


async def user(client: httpx.AsyncClient, uid: int, rounds: int, samples: dict, errors: list) -> None:
    rnd = random.Random(uid)

    async def get(kind: str, path: str) -> dict | None:
        t0 = time.perf_counter()
        try:
            r = await client.get(path)
        except httpx.HTTPError as e:
            errors.append(f"user{uid} {path}: {type(e).__name__} {e}")
            return None
        total = time.perf_counter() - t0
        if r.status_code != 200:
            errors.append(f"user{uid} {path}: HTTP {r.status_code} {r.text[:200]}")
            return None
        body = r.json()
        # rows は Oracle の処理時間(elapsed_ms)を除いたオーバーヘッドで判定する
        samples[kind].append(total - body["elapsed_ms"] / 1000 if kind == "rows" else total)
        return body

    for _ in range(rounds):
        table = rnd.choice(TABLES)
        await get("schema", "/api/schema")
        await get("detail", f"/api/schema/tables/HR/{table}")
        await get("rows", f"/api/schema/tables/HR/{table}/rows?offset=0&limit=50")
        await get("rows", f"/api/schema/tables/HR/{table}/rows?offset=50&limit=50")


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8088")
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--rounds", type=int, default=10)
    a = ap.parse_args()

    samples: dict[str, list[float]] = {"schema": [], "detail": [], "rows": []}
    errors: list[str] = []
    started = time.perf_counter()
    async with httpx.AsyncClient(base_url=a.base, timeout=60) as client:
        await asyncio.gather(*(user(client, i, a.rounds, samples, errors) for i in range(a.users)))
    print(f"users={a.users} rounds={a.rounds} elapsed={time.perf_counter() - started:.2f}s")

    ok = not errors
    for kind, xs in samples.items():
        if not xs:
            print(f"FAIL {kind}: 測定値なし")
            ok = False
            continue
        xs.sort()
        p95 = xs[max(0, int(len(xs) * 0.95) - 1)]
        verdict = "OK  " if xs[-1] < LIMIT_SEC else "FAIL"
        ok = ok and xs[-1] < LIMIT_SEC
        print(
            f"{verdict} {kind}: n={len(xs)} median={statistics.median(xs):.3f}s "
            f"p95={p95:.3f}s max={xs[-1]:.3f}s (< {LIMIT_SEC}s)"
        )
    print(f"{'OK  ' if not errors else 'FAIL'} errors={len(errors)}")
    for e in errors[:20]:
        print("  " + e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
