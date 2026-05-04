"""
Sentiment evaluation: compare RoBERTa against two lightweight baselines
(VADER and nlptown/bert-base-multilingual-uncased-sentiment) using star
ratings as a distant-supervision proxy.

Star -> label mapping (Pang & Lee 2008 convention):
    rating in {1, 2}    -> negative
    rating == 3         -> neutral
    rating in {4, 5}    -> positive

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


def _eval_metrics(pairs: list[tuple[str, str]]) -> dict:
    n = len(pairs)
    correct = sum(1 for gt, pred in pairs if gt == pred)
    accuracy = round(correct / n, 4)
    cm = _confusion(pairs)
    per_label = {lbl: _prf(cm, lbl) for lbl in ["negative", "neutral", "positive"]}
    macro_f1 = round(sum(p[2] for p in per_label.values()) / 3, 4)
    return {
        "n": n,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": {lbl: {"precision": p[0], "recall": p[1], "f1": p[2]}
                      for lbl, p in per_label.items()},
        "confusion": cm,
    }


def _vader_label(text: str) -> str:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    if not hasattr(_vader_label, "_analyzer"):
        _vader_label._analyzer = SentimentIntensityAnalyzer()
    compound = _vader_label._analyzer.polarity_scores(text)["compound"]
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def _nlptown_label(text: str, pipe) -> str:
    # nlptown returns "1 star" .. "5 stars"
    result = pipe(text[:512], truncation=True)[0]["label"]
    stars = int(result.split()[0])
    if stars <= 2:
        return "negative"
    if stars == 3:
        return "neutral"
    return "positive"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pull reviews with rating + roberta label + review_text
    rows: list[dict] = []
    page, size = 0, 1000
    while True:
        chunk = (supabase.table("reviews_raw")
                 .select("rating,sentiment_label,review_text")
                 .not_.is_("sentiment_label", "null")
                 .not_.is_("rating", "null")
                 .not_.is_("review_text", "null")
                 .range(page * size, (page + 1) * size - 1)
                 .execute()).data or []
        rows.extend(chunk)
        if len(chunk) < size:
            break
        page += 1

    # ── RoBERTa eval ──────────────────────────────────────────────
    roberta_pairs: list[tuple[str, str]] = []
    for r in rows:
        gt = _star_to_label(r.get("rating"))
        pred = r.get("sentiment_label")
        if gt and pred in {"positive", "neutral", "negative"}:
            roberta_pairs.append((gt, pred))

    n = len(roberta_pairs)
    if not n:
        print("[Eval] No (rating, sentiment_label) pairs found. Run analyze_sentiment.py first.")
        return

    roberta_result = _eval_metrics(roberta_pairs)
    label_dist_gt   = Counter(gt for gt, _ in roberta_pairs)
    label_dist_pred = Counter(pred for _, pred in roberta_pairs)

    # ── VADER baseline ────────────────────────────────────────────
    print(f"[Eval] Running VADER on {n} reviews ...")
    vader_pairs: list[tuple[str, str]] = []
    for r in rows:
        gt = _star_to_label(r.get("rating"))
        text = r.get("review_text") or ""
        if gt and text:
            vader_pairs.append((gt, _vader_label(text)))

    # ── nlptown baseline ──────────────────────────────────────────
    print(f"[Eval] Running nlptown on {n} reviews ...")
    try:
        from transformers import pipeline as hf_pipeline
        nlp_pipe = hf_pipeline(
            "text-classification",
            model="nlptown/bert-base-multilingual-uncased-sentiment",
            truncation=True,
        )
        nlptown_pairs: list[tuple[str, str]] = []
        for r in rows:
            gt = _star_to_label(r.get("rating"))
            text = r.get("review_text") or ""
            if gt and text:
                try:
                    nlptown_pairs.append((gt, _nlptown_label(text, nlp_pipe)))
                except Exception:
                    pass
        nlptown_result = _eval_metrics(nlptown_pairs) if nlptown_pairs else None
    except Exception as e:
        print(f"  [WARN] nlptown baseline skipped: {e}")
        nlptown_result = None

    vader_result = _eval_metrics(vader_pairs) if vader_pairs else None

    # ── Output ────────────────────────────────────────────────────
    result = {
        "as_of":   date.today().isoformat(),
        "roberta": {**roberta_result,
                    "label_dist_ground_truth": dict(label_dist_gt),
                    "label_dist_predicted":    dict(label_dist_pred)},
        "vader":   vader_result,
        "nlptown": nlptown_result,
        "notes":   "Ground truth = star rating mapping (noisy proxy). "
                   "VADER: rule-based lexicon. nlptown: fine-tuned BERT 1-5 stars.",
    }

    # Keep top-level keys for backward compatibility with thesis LaTeX
    result["n"]        = roberta_result["n"]
    result["accuracy"] = roberta_result["accuracy"]
    result["macro_f1"] = roberta_result["macro_f1"]
    result["per_class"] = roberta_result["per_class"]
    result["confusion"] = roberta_result["confusion"]
    result["label_dist_ground_truth"] = dict(label_dist_gt)
    result["label_dist_predicted"]    = dict(label_dist_pred)

    out_file = OUT_DIR / "sentiment_eval.json"
    out_file.write_text(json.dumps(result, indent=2))

    print(f"\n{'Model':<12} {'Acc':>6}  {'MacroF1':>8}  {'Neg F1':>8}  {'Neu F1':>8}  {'Pos F1':>8}")
    print("-" * 60)
    for name, res in [("RoBERTa", roberta_result), ("VADER", vader_result), ("nlptown", nlptown_result)]:
        if res is None:
            print(f"{name:<12}  skipped")
            continue
        pc = res["per_class"]
        print(f"{name:<12} {res['accuracy']:>6.3f}  {res['macro_f1']:>8.3f}  "
              f"{pc['negative']['f1']:>8.3f}  {pc['neutral']['f1']:>8.3f}  {pc['positive']['f1']:>8.3f}")

    print(f"\n[Eval] Written -> {out_file}")


if __name__ == "__main__":
    main()
