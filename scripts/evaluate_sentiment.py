"""
Sentiment evaluation: distant-supervision check of RoBERTa labels against
star ratings as a noisy ground-truth proxy.

Star -> label mapping (Pang & Lee 2008 convention):
    rating in {1, 2}    -> negative
    rating == 3         -> neutral
    rating in {4, 5}    -> positive

We report accuracy, macro-F1, and per-class precision/recall on the subset of
reviews that have BOTH a sentiment_label (RoBERTa output) and a rating.

Limitations (acknowledge in thesis):
- Stars are a *noisy* label. A 5-star review with mild text or a 4-star review
  with a critical tone will count against the model unfairly.
- Class balance is skewed positive on Amazon (most reviews are 4-5 stars), so
  macro-F1 matters more than raw accuracy.

Output: data/eval/sentiment_eval.json + console summary.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from collections import Counter
from datetime import date
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase


OUT_DIR = Path(__file__).parent.parent / "data" / "eval"


def _star_to_label(rating: int | None) -> str | None:
    if rating is None:
        return None
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    if rating >= 4:
        return "positive"
    return None


def _confusion(pairs: list[tuple[str, str]]) -> dict:
    labels = ["negative", "neutral", "positive"]
    cm = {gt: {pred: 0 for pred in labels} for gt in labels}
    for gt, pred in pairs:
        cm[gt][pred] += 1
    return cm


def _prf(cm: dict, label: str) -> tuple[float, float, float]:
    labels = ["negative", "neutral", "positive"]
    tp = cm[label][label]
    fp = sum(cm[gt][label] for gt in labels if gt != label)
    fn = sum(cm[label][pred] for pred in labels if pred != label)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(p, 4), round(r, 4), round(f1, 4)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pull every review that has both a star rating and a RoBERTa label.
    # Supabase-py returns 1000 rows by default; page until exhausted.
    rows: list[dict] = []
    page, size = 0, 1000
    while True:
        chunk = (supabase.table("reviews_raw")
                 .select("rating,sentiment_label")
                 .not_.is_("sentiment_label", "null")
                 .not_.is_("rating", "null")
                 .range(page * size, (page + 1) * size - 1)
                 .execute()).data or []
        rows.extend(chunk)
        if len(chunk) < size:
            break
        page += 1

    pairs: list[tuple[str, str]] = []
    for r in rows:
        gt = _star_to_label(r.get("rating"))
        pred = r.get("sentiment_label")
        if gt and pred in {"positive", "neutral", "negative"}:
            pairs.append((gt, pred))

    n = len(pairs)
    if not n:
        print("[Eval] No (rating, sentiment_label) pairs found. Run analyze_sentiment.py first.")
        return

    correct = sum(1 for gt, pred in pairs if gt == pred)
    accuracy = correct / n

    cm = _confusion(pairs)
    per_label = {lbl: _prf(cm, lbl) for lbl in ["negative", "neutral", "positive"]}
    macro_f1 = round(sum(p[2] for p in per_label.values()) / 3, 4)

    label_dist_gt = Counter(gt for gt, _ in pairs)
    label_dist_pred = Counter(pred for _, pred in pairs)

    result = {
        "as_of":         date.today().isoformat(),
        "n":             n,
        "accuracy":      round(accuracy, 4),
        "macro_f1":      macro_f1,
        "per_class":     {lbl: {"precision": p[0], "recall": p[1], "f1": p[2]}
                          for lbl, p in per_label.items()},
        "confusion":     cm,
        "label_dist_ground_truth": dict(label_dist_gt),
        "label_dist_predicted":    dict(label_dist_pred),
        "notes":         "Ground truth = star rating mapping. Noisy proxy; see eval script docstring.",
    }

    out_file = OUT_DIR / "sentiment_eval.json"
    out_file.write_text(json.dumps(result, indent=2))

    print(f"[Eval] n={n}  accuracy={accuracy:.3f}  macro-F1={macro_f1:.3f}")
    for lbl, (p, r, f1) in per_label.items():
        print(f"  {lbl:8s}  P={p:.3f}  R={r:.3f}  F1={f1:.3f}")
    print(f"[Eval] Written -> {out_file}")


if __name__ == "__main__":
    main()
