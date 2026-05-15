import json
import os
import sys
import time
from pathlib import Path


LIMIT = int(os.getenv("LIMIT", "100000"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "1000000"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "reports"))


def collatz_next(n: int) -> int:
    return n // 2 if n % 2 == 0 else 3 * n + 1


def analyze_number(start: int, max_steps: int):
    n = start
    seen = {}
    path = [n]
    highest = n

    for step in range(max_steps):
        if n == 1:
            return {
                "status": "ok",
                "start": start,
                "steps": step,
                "highest": highest,
                "path_prefix": path[:25],
            }

        if n in seen:
            cycle_start_index = seen[n]
            cycle = path[cycle_start_index:]
            return {
                "status": "cycle",
                "start": start,
                "steps": step,
                "highest": highest,
                "cycle": cycle,
                "path_prefix": path[:25],
            }

        seen[n] = step
        n = collatz_next(n)
        path.append(n)
        if n > highest:
            highest = n

    return {
        "status": "timeout",
        "start": start,
        "steps": max_steps,
        "highest": highest,
        "path_prefix": path[:25],
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    started = time.time()

    max_steps_seen = -1
    max_steps_number = None
    max_value_seen = -1
    max_value_number = None

    counterexample = None
    checked = 0

    for i in range(1, LIMIT + 1):
        result = analyze_number(i, MAX_STEPS)
        checked += 1

        if result["steps"] > max_steps_seen:
            max_steps_seen = result["steps"]
            max_steps_number = i

        if result["highest"] > max_value_seen:
            max_value_seen = result["highest"]
            max_value_number = i

        if result["status"] != "ok":
            counterexample = result
            break

        if i % max(1, LIMIT // 20) == 0:
            print(f"İlerleme: {i}/{LIMIT}")

    elapsed = time.time() - started

    report = {
        "limit": LIMIT,
        "max_steps_cap": MAX_STEPS,
        "checked": checked,
        "elapsed_seconds": round(elapsed, 3),
        "max_steps_seen": max_steps_seen,
        "max_steps_number": max_steps_number,
        "max_value_seen": max_value_seen,
        "max_value_number": max_value_number,
        "counterexample_found": counterexample is not None,
        "counterexample": counterexample,
    }

    json_path = OUTPUT_DIR / "collatz_report.json"
    txt_path = OUTPUT_DIR / "collatz_report.txt"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("COLLATZ RAPORU")
    lines.append(f"Limit: {LIMIT}")
    lines.append(f"Maksimum adım sınırı: {MAX_STEPS}")
    lines.append(f"Kontrol edilen sayı: {checked}")
    lines.append(f"Süre: {round(elapsed, 3)} saniye")
    lines.append(f"En uzun zincir: {max_steps_seen} (sayı: {max_steps_number})")
    lines.append(f"En büyük ara değer: {max_value_seen} (sayı: {max_value_number})")
    lines.append(f"Karşı örnek bulundu mu: {counterexample is not None}")

    if counterexample:
        lines.append("")
        lines.append("KARŞI ÖRNEK / ANOMALİ:")
        lines.append(json.dumps(counterexample, indent=2, ensure_ascii=False))
        print("\n".join(lines))
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        sys.exit(1)

    lines.append("")
    lines.append("Sonuç: Bu aralıkta 1'e ulaşmayan sayı bulunmadı.")
    print("\n".join(lines))
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    sys.exit(0)


if __name__ == "__main__":
    main()
