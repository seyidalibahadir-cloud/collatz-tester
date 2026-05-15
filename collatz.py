import json
import os
import sys
import time
from pathlib import Path

LIMIT = int(os.getenv("LIMIT", "100000"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "1000000"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "reports"))

# Global Cache: Daha önce hesaplanan sayılar için (hedefe_kalan_adim_sayisi, en_yuksek_deger) tutar.
# 1 sayısı 0 adımda kendisine ulaşır, gördüğü en yüksek değer 1'dir.
memo = {1: (0, 1)}

def collatz_next(n: int) -> int:
    return n // 2 if n % 2 == 0 else 3 * n + 1

def analyze_number(start: int, max_steps: int):
    n = start
    seen_in_path = {}
    path = []
    highest = n

    for step in range(max_steps):
        # Sayı daha önce çözülüp önbelleğe alındıysa, hesaplamayı kes ve sonucu birleştir.
        if n in memo:
            cached_steps, cached_highest = memo[n]
            total_steps = step + cached_steps
            overall_highest = max(highest, cached_highest)

            # Sadece başlangıç değerini önbelleğe eklemek performansı katlar.
            memo[start] = (total_steps, overall_highest)

            return {
                "status": "ok",
                "start": start,
                "steps": total_steps,
                "highest": overall_highest,
                "path_prefix": path[:25] if path else [start],
            }

        # Anomali/Döngü tespiti
        if n in seen_in_path:
            cycle_start_index = seen_in_path[n]
            cycle = path[cycle_start_index:]
            return {
                "status": "cycle",
                "start": start,
                "steps": step,
                "highest": highest,
                "cycle": cycle,
                "path_prefix": path[:25],
            }

        seen_in_path[n] = step
        path.append(n)
        
        n = collatz_next(n)
        if n > highest:
            highest = n

    # MAX_STEPS sınırına takılanlar
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

    print(f"Collatz taraması başlatılıyor. Limit: {LIMIT}, Max Adım: {MAX_STEPS}")

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

        if i % max(1, LIMIT // 10) == 0:
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

    lines = [
        "COLLATZ RAPORU",
        f"Limit: {LIMIT}",
        f"Maksimum adım sınırı: {MAX_STEPS}",
        f"Kontrol edilen sayı: {checked}",
        f"Süre: {round(elapsed, 3)} saniye",
        f"En uzun zincir: {max_steps_seen} (sayı: {max_steps_number})",
        f"En büyük ara değer: {max_value_seen} (sayı: {max_value_number})",
        f"Karşı örnek bulundu mu: {counterexample is not None}"
    ]

    if counterexample:
        lines.extend([
            "",
            "KARŞI ÖRNEK / ANOMALİ TESPİT EDİLDİ:",
            json.dumps(counterexample, indent=2, ensure_ascii=False)
        ])
        print("\n".join(lines))
        txt_path.write_text("\n".join(lines), encoding="utf-8")
        sys.exit(1)

    lines.extend([
        "",
        "Sonuç: Bu aralıkta 1'e ulaşmayan sayı bulunmadı."
    ])
    print("\n".join(lines))
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    sys.exit(0)

if __name__ == "__main__":
    main()
