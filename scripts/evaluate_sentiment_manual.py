"""
Manual-labeled sentiment evaluation.

Reads data/eval/reviews_to_label.csv (after manual labeling) and computes:
  1. Star-rating proxy accuracy on manual labels  (PROXY NOISE measurement)
  2. RoBERTa accuracy on manual labels             (TRUE MODEL ACCURACY)
  3. RoBERTa accuracy on star-rating labels        (CURRENT EVALUATION)
  4. Confusion matrices for each comparison

The gap between (3) and (2) quantifies how much of RoBERTa's apparent error
is caused by proxy-label noise rather than true model error.

Output: data/eval/sentiment_manual_eval.json + console summary.
"""
from __future__ import annotations
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

IN_FILE  = Path(__file__).parent.parent / "data" / "eval" / "reviews_to_label.csv"
OUT_FILE = Path(__file__).parent.parent / "data" / "eval" / "sentiment_manual_eval.json"

LABELS = ("negative", "neutral", "positive")


def star_to_label(star: int) -> str:
    if star <= 2:
        return "negative"
    if star == 3:
        return "neutral"
    return "positive"


def normalize_label(s: str) -> str | None:
    s = (s or "").strip().lower()
    if s in LABELS:
        return s
    # tolerate common variants
    if s in ("pos", "+", "positive."):
        return "positive"
    if s in ("neg", "-", "negative."):
        return "negative"
    if s in ("neu", "neutral.", "0"):
        return "neutral"
    return None


def metrics(y_true: list[str], y_pred: list[str]) -> dict:
    n = len(y_true)
    correct = sum(1 for a, b in zip(y_true, y_pred) if a == b)
    accuracy = correct / n if n else 0.0

    # per-class P/R/F1
    per_class = {}
    macro_f1 = 0.0
    for cls in LABELS:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == cls and b == cls)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != cls and b == cls)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == cls and b != cls)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall    = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[cls] = {
            "precision": round(precision, 4),
            "recall":    round(recall, 4),
            "f1":        round(f1, 4),
            "support":   sum(1 for a in y_true if a == cls),
        }
        macro_f1 += f1
    macro_f1 /= len(LABELS)

    # confusion matrix
    matrix = {a: {b: 0 for b in LABELS} for a in LABELS}
    for a, b in zip(y_true, y_pred):
        if a in matrix and b in matrix[a]:
            matrix[a][b] += 1

    return {
        "n":              n,
        "accuracy":       round(accuracy, 4),
        "macro_f1":       round(macro_f1, 4),
        "per_class":      per_class,
        "confusion":      matrix,
    }


def main() -> None:
    if not IN_FILE.exists():
        print(f"[Manual-Eval] CSV not found: {IN_FILE}")
        print("[Manual-Eval] Run scripts/export_reviews_for_labeling.py first.")
        return

    rows: list[dict] = []
    with IN_FILE.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            manual = normalize_label(r.get("manual_label", ""))
            if manual is None:
                continue
            try:
                star = int(r.get("rating") or 0)
            except ValueError:
                continue
            roberta = normalize_label(r.get("roberta_label", ""))
            rows.append({
                "manual":  manual,
                "star":    star_to_label(star),
                "roberta": roberta,
            })

    if not rows:
        print("[Manual-Eval] No labeled rows found. Did you fill the 'manual_label' column?")
        return

    print(f"[Manual-Eval] Evaluating {len(rows)} labeled reviews.")

    # 1. Star vs Manual  (proxy noise)
    star_vs_manual = metrics([r["manual"] for r in rows], [r["star"] for r in rows])

    # 2. RoBERTa vs Manual  (true model accuracy)
    rb_rows = [r for r in rows if r["roberta"] is not None]
    roberta_vs_manual = metrics([r["manual"] for r in rb_rows], [r["roberta"] for r in rb_rows])

    # 3. RoBERTa vs Star  (current proxy evaluation, on the same sample)
    roberta_vs_star = metrics([r["star"] for r in rb_rows], [r["roberta"] for r in rb_rows])

    # Distribution sanity
    dist_manual  = dict(Counter(r["manual"]  for r in rows))
    dist_star    = dict(Counter(r["star"]    for r in rows))
    dist_roberta = dict(Counter(r["roberta"] for r in rb_rows if r["roberta"]))

    summary = {
        "as_of":               date.today().isoformat(),
        "n_total":             len(rows),
        "n_with_roberta":      len(rb_rows),
        "label_distribution": {
            "manual":  dist_manual,
            "star":    dist_star,
            "roberta": dist_roberta,
        },
        "proxy_noise":            star_vs_manual,
        "roberta_vs_manual":      roberta_vs_manual,
        "roberta_vs_star_proxy":  roberta_vs_star,
        "interpretation": {
            "proxy_noise_pct":      round((1 - star_vs_manual["accuracy"]) * 100, 2),
            "roberta_true_error_pct": round((1 - roberta_vs_manual["accuracy"]) * 100, 2),
            "roberta_proxy_error_pct": round((1 - roberta_vs_star["accuracy"]) * 100, 2),
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(summary, indent=2))

    print(f"\n[Manual-Eval] Star-rating accuracy on manual labels: {star_vs_manual['accuracy']:.3f}  "
          f"(proxy noise = {summary['interpretation']['proxy_noise_pct']}%)")
    print(f"[Manual-Eval] RoBERTa accuracy on manual labels:      {roberta_vs_manual['accuracy']:.3f}  "
          f"(true model error = {summary['interpretation']['roberta_true_error_pct']}%)")
    print(f"[Manual-Eval] RoBERTa accuracy on star proxy:         {roberta_vs_star['accuracy']:.3f}  "
          f"(apparent error = {summary['interpretation']['roberta_proxy_error_pct']}%)")
    print(f"[Manual-Eval] Written -> {OUT_FILE}")


if __name__ == "__main__":
    main()
