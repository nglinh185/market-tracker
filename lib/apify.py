import os
import requests
from apify_client import ApifyClient

_BASE = "https://api.apify.com/v2"


def _token() -> str:
    return os.environ["APIFY_TOKEN"]


def run_actor(actor_id: str, run_input: dict, timeout_min: int = 30) -> str:
    """Trigger actor, block until SUCCEEDED, return dataset_id."""
    client = ApifyClient(_token())
    print(f"  [Apify] Starting actor {actor_id} ...")

    run = client.actor(actor_id).call(
        run_input=run_input,
        timeout_secs=timeout_min * 60,
    )

    status     = run.get("status")
    dataset_id = run.get("defaultDatasetId")

    # item_count tu REST API chinh xac hon Python client
    item_count = _dataset_item_count(dataset_id)
    print(f"  [Apify] status={status} | items={item_count}")

    if status != "SUCCEEDED":
        raise RuntimeError(f"Actor run ended with status: {status}")
    if item_count == 0:
        raise ValueError("Actor returned 0 items — possible block or bad input")

    return dataset_id


def _dataset_item_count(dataset_id: str) -> int:
    resp = requests.get(
        f"{_BASE}/datasets/{dataset_id}",
        params={"token": _token()},
        timeout=10,
    )
    return resp.json().get("data", {}).get("itemCount", 0)


def fetch_dataset(dataset_id: str) -> list[dict]:
    """Paginated fetch via REST API (Python client có bug với một số actor output)."""
    items, offset, limit = [], 0, 1000

    while True:
        resp = requests.get(
            f"{_BASE}/datasets/{dataset_id}/items",
            params={"token": _token(), "offset": offset, "limit": limit},
            timeout=60,
        )
        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        offset += limit

    print(f"  [Apify] Fetched {len(items)} total items")
    return items
