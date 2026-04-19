import os
import requests
import imagehash
from io import BytesIO
from PIL import Image

from config import IMAGE_BUCKET, PHASH_THRESHOLD
from lib.db import supabase


def ensure_bucket() -> None:
    """Create the storage bucket if it doesn't exist yet."""
    try:
        supabase.storage.create_bucket(IMAGE_BUCKET, {"public": True})
        print(f"  [Storage] Created bucket '{IMAGE_BUCKET}'")
    except Exception:
        pass  # already exists


def download_hash_store(asin: str, image_url: str, snapshot_date: str) -> tuple[str | None, str | None]:
    """
    Download ảnh từ Amazon, tính pHash, upload lên Supabase Storage.
    Returns: (phash_string, public_storage_url)
    """
    try:
        resp = requests.get(image_url, timeout=10)
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content)).convert("RGB")
        phash_val = str(imagehash.phash(img))

        buf = BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        path = f"{snapshot_date}/{asin}/main.jpg"
        supabase.storage.from_(IMAGE_BUCKET).upload(
            path,
            buf.read(),
            {"content-type": "image/jpeg", "upsert": "true"},
        )
        storage_url = supabase.storage.from_(IMAGE_BUCKET).get_public_url(path)
        return phash_val, storage_url

    except Exception as e:
        print(f"  [Image] Failed for {asin}: {e}")
        return None, None


def get_yesterday_hash(asin: str, yesterday: str) -> str | None:
    """Lấy pHash của ngày hôm qua từ DB để so sánh."""
    result = (
        supabase.table("daily_snapshots")
        .select("image_hash")
        .eq("asin", asin)
        .eq("snapshot_date", yesterday)
        .execute()
    )
    return result.data[0]["image_hash"] if result.data else None


def is_image_changed(current_hash: str, previous_hash: str | None) -> bool:
    if not previous_hash or not current_hash:
        return False
    distance = imagehash.hex_to_hash(current_hash) - imagehash.hex_to_hash(previous_hash)
    return distance > PHASH_THRESHOLD
