"""
RoBERTa sentiment analysis tren reviews_raw.
Model: cardiffnlp/twitter-roberta-base-sentiment-latest
Chay sau ingest_reviews.py.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert


LABEL_MAP = {"positive": 1.0, "neutral": 0.0, "negative": -1.0}


def _load_model():
    from transformers import pipeline
    return pipeline(
        "sentiment-analysis",
        model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        truncation=True,
        max_length=512,
    )


def run_sentiment() -> None:
    rows = (
        supabase.table("reviews_raw")
        .select("id,asin,review_text,rating")
        .is_("sentiment_label", "null")
        .execute()
    ).data

    if not rows:
        print("[Sentiment] Khong co reviews chua phan tich.")
        return

    print(f"[Sentiment] Phan tich {len(rows)} reviews ...")
    model = _load_model()

    updates = []
    for r in rows:
        text = (r["review_text"] or "")[:512]
        try:
            result = model(text)[0]
            label = result["label"].lower()
            score = round(result["score"] * LABEL_MAP.get(label, 0), 4)
            updates.append({"id": r["id"], "sentiment_label": label, "sentiment_score": score})
        except Exception as e:
            print(f"  [WARN] review {r['id']}: {e}")

    for u in updates:
        supabase.table("reviews_raw").update({
            "sentiment_label": u["sentiment_label"],
            "sentiment_score": u["sentiment_score"],
        }).eq("id", u["id"]).execute()

    print(f"  Updated {len(updates)} reviews.")


def aggregate_to_daily() -> None:
    today = date.today().isoformat()
    # Note: dùng tất cả reviews (2018-2025) để train RoBERTa tốt hơn
    # BMS sẽ so sánh day-to-day sentiment change, không bị ảnh hưởng tuổi review
    rows = (
        supabase.table("reviews_raw")
        .select("asin,sentiment_label,sentiment_score")
        .not_.is_("sentiment_label", "null")
        .execute()
    ).data

    from collections import defaultdict
    by_asin: dict[str, list] = defaultdict(list)
    for r in rows:
        by_asin[r["asin"]].append(r)

    agg_rows = []
    for asin, reviews in by_asin.items():
        scores = [r["sentiment_score"] for r in reviews if r["sentiment_score"] is not None]
        labels = [r["sentiment_label"] for r in reviews if r["sentiment_label"]]
        if not labels:
            continue
        n = len(labels)
        agg_rows.append({
            "snapshot_date":       today,
            "asin":                asin,
            "review_count_new":    n,
            "avg_sentiment_score": round(sum(scores) / len(scores), 4) if scores else None,
            "positive_ratio":      round(labels.count("positive") / n, 4),
            "negative_ratio":      round(labels.count("negative") / n, 4),
        })

    n = upsert("review_sentiment_daily", agg_rows, "snapshot_date,asin")
    print(f"[Sentiment] Aggregated {n} ASINs -> review_sentiment_daily.")


def main() -> None:
    run_sentiment()
    aggregate_to_daily()


if __name__ == "__main__":
    main()
