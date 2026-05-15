import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

LIMIT = int(os.getenv("LIMIT", "1000000"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "1000000"))
WORKERS = int(os.getenv("WORKERS", "4"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "reports"))

GLOBAL_MEMO = {1: 0}


def collatz_next(n: int) -> int:
    return n // 2 if n % 2 == 0 else 3 * n + 1


def analyze_number(start: int):
    n = start

    local_seen = set()
    highest = n
    steps = 0

    while n != 1 and steps < MAX_STEPS:

        if n in local_seen:
            return {
                "status": "cycle",
                "start": start,
                "steps": steps,
                "highest": highest,
            }

        local_seen.add(n)

        n = collatz_next(n)

        if n > highest:
            highest = n

        steps += 1

    if n != 1:
        return {
            "status": "timeout",
            "start": start,
            "steps": steps,
            "highest": highest,
        }

    return {
        "status": "ok",
        "start": start,
        "steps": steps,
        "highest": highest,
    }


def chunkify(limit, parts):
    size = math.ceil(limit / parts)

    chunks = []

    start = 1

    while start <= limit:
        end = min(start + size - 1, limit)
        chunks.append((start, end))
        start = end + 1

    return chunks


def process_chunk(chunk):
    start, end = chunk

    max_steps = -1
    max_steps_number = None

    max_value = -1
    max_value_number = None

    anomaly = None

    for i in range(start, end + 1):

        result = analyze_number(i)

        if result["steps"] > max_steps:
            max_steps = result["steps"]
            max_steps_number = i

        if result["highest"] > max_value:
            max_value = result["highest"]
            max_value_number = i

        if result["status"] != "ok":
            anomaly = result
            break

    return {
        "checked_from": start,
        "checked_to": end,
        "max_steps": max_steps,
        "max_steps_number": max_steps_number,
        "max_value": max_value,
        "max_value_number": max_value_number,
        "anomaly": anomaly,
    }


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    started = time.time()

    chunks = chunkify(LIMIT, WORKERS)

    print(f"Başlatıldı")
    print(f"Limit: {LIMIT}")
    print(f"Worker sayısı: {WORKERS}")

    results = []

    with ProcessPoolExecutor(max_workers=WORKERS) as executor:

        futures = [executor.submit(process_chunk, c) for c in chunks]

        for future in futures:
            result = future.result()

            print(
                f"Tamamlandı: "
                f"{result['checked_from']} - {result['checked_to']}"
            )

            results.append(result)

    elapsed = round(time.time() - started, 3)

    anomaly = None

    global_max_steps = -1
    global_max_steps_number = None

    global_max_value = -1
    global_max_value_number = None

    for r in results:

        if r["max_steps"] > global_max_steps:
            global_max_steps = r["max_steps"]
            global_max_steps_number = r["max_steps_number"]

        if r["max_value"] > global_max_value:
            global_max_value = r["max_value"]
            global_max_value_number = r["max_value_number"]

        if r["anomaly"]:
            anomaly = r["anomaly"]

    report = {
        "limit": LIMIT,
        "workers": WORKERS,
        "elapsed_seconds": elapsed,
        "max_steps": global_max_steps,
        "max_steps_number": global_max_steps_number,
        "max_value": global_max_value,
        "max_value_number": global_max_value_number,
        "anomaly_found": anomaly is not None,
        "anomaly": anomaly,
    }

    report_path = OUTPUT_DIR / "collatz_report.json"

    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n===== RAPOR =====")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if anomaly:
        print("\nANOMALİ BULUNDU")
        sys.exit(1)

    print("\nKarşı örnek bulunamadı.")
    sys.exit(0)


if __name__ == "__main__":
    main()
