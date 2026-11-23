"""
Prompt Library Tests
Verifies at least 250 unique prompts, zero duplicate IDs, zero duplicate texts per language,
11 categories representation, positive/neutral/improvement coverage, session deduplication,
and multi-language support (English, Telugu, Hindi).
"""

import json
from pathlib import Path
import pytest
from app.services.prompt_service import prompt_service

CATEGORIES_EXPECTED = [
    "food_quality",
    "taste_freshness",
    "food_presentation",
    "service_staff",
    "speed_of_service",
    "restaurant_ambience",
    "cleanliness_hygiene",
    "family_dining",
    "value_for_money",
    "drinks_beverages",
    "overall_experience",
]


def test_prompt_file_integrity_and_minimum_count():
    json_path = Path("backend/app/data/feedback_prompts.json")
    assert json_path.exists(), "feedback_prompts.json must exist"

    with open(json_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    # 1. Minimum 250 unique prompts
    assert len(prompts) >= 250, f"Expected at least 250 prompts, found {len(prompts)}"

    # 2. Unique IDs
    ids = [p["id"] for p in prompts]
    assert len(ids) == len(set(ids)), "Duplicate prompt IDs detected!"

    # 3. Unique text per language
    texts_by_lang = {}
    for p in prompts:
        lang = p["language"]
        texts_by_lang.setdefault(lang, []).append(p["text"])

    for lang, texts in texts_by_lang.items():
        assert len(texts) == len(set(texts)), f"Duplicate prompt text detected in language '{lang}'"

    # English alone must exceed 250 prompts
    assert len(texts_by_lang["en"]) >= 250, f"Expected at least 250 English prompts, got {len(texts_by_lang['en'])}"


def test_all_categories_represented_with_all_sentiments():
    json_path = Path("backend/app/data/feedback_prompts.json")
    with open(json_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    cats_found = set(p["category"] for p in prompts)
    for expected_cat in CATEGORIES_EXPECTED:
        assert expected_cat in cats_found, f"Missing category: {expected_cat}"

    # Check sentiment distribution in English
    eng_prompts = [p for p in prompts if p["language"] == "en"]
    for expected_cat in CATEGORIES_EXPECTED:
        cat_items = [p for p in eng_prompts if p["category"] == expected_cat]
        sentiments = set(p["sentiment"] for p in cat_items)
        assert "positive" in sentiments, f"Missing positive prompt for category {expected_cat}"
        assert "neutral" in sentiments, f"Missing neutral prompt for category {expected_cat}"
        assert "improvement" in sentiments, f"Missing improvement prompt for category {expected_cat}"


def test_multilingual_coverage():
    json_path = Path("backend/app/data/feedback_prompts.json")
    with open(json_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    languages = set(p["language"] for p in prompts)
    assert "en" in languages
    assert "te" in languages
    assert "hi" in languages


@pytest.mark.asyncio
async def test_api_get_prompts_unfiltered(async_client):
    response = await async_client.get("/api/v1/public/prompts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 10
    # Every prompt must have required fields
    for p in data["data"]:
        assert "id" in p
        assert "category" in p
        assert "text" in p
        assert "sentiment" in p
        assert p["is_active"] is True


@pytest.mark.asyncio
async def test_api_get_prompts_category_filter(async_client):
    response = await async_client.get("/api/v1/public/prompts?category=service_staff&limit=8")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    for p in data["data"]:
        assert p["category"] == "service_staff"


@pytest.mark.asyncio
async def test_api_get_prompts_sentiment_filter(async_client):
    response = await async_client.get("/api/v1/public/prompts?sentiment=improvement&limit=6")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    for p in data["data"]:
        assert p["sentiment"] == "improvement"


@pytest.mark.asyncio
async def test_api_get_prompts_session_deduplication(async_client):
    # 1. Fetch first batch of 5
    res1 = await async_client.get("/api/v1/public/prompts?limit=5")
    batch1_ids = [p["id"] for p in res1.json()["data"]]

    # 2. Exclude first batch
    exclude_param = ",".join(batch1_ids)
    res2 = await async_client.get(f"/api/v1/public/prompts?limit=5&exclude_ids={exclude_param}")
    batch2_ids = [p["id"] for p in res2.json()["data"]]

    # Ensure no overlap between batches
    overlap = set(batch1_ids).intersection(set(batch2_ids))
    assert len(overlap) == 0, f"Found overlapping prompts: {overlap}"


@pytest.mark.asyncio
async def test_api_get_prompts_languages(async_client):
    for lang in ["en", "te", "hi"]:
        res = await async_client.get(f"/api/v1/public/prompts?language={lang}&limit=5")
        assert res.status_code == 200
        data = res.json()["data"]
        assert len(data) > 0
        for p in data:
            assert p["language"] == lang


@pytest.mark.asyncio
async def test_api_get_prompt_categories(async_client):
    response = await async_client.get("/api/v1/public/prompts/categories")
    assert response.status_code == 200
    cats = response.json()["data"]
    assert len(cats) == 11
    keys = [c["key"] for c in cats]
    for exp in CATEGORIES_EXPECTED:
        assert exp in keys


@pytest.mark.asyncio
async def test_api_get_prompt_stats(async_client):
    response = await async_client.get("/api/v1/public/prompts/stats")
    assert response.status_code == 200
    stats = response.json()["data"]
    assert stats["total_prompts"] >= 250
    assert stats["languages"]["en"] >= 250
    assert stats["languages"]["te"] > 0
    assert stats["languages"]["hi"] > 0


@pytest.mark.asyncio
async def test_submit_feedback_with_selected_prompts(async_client):
    payload = {
        "session_id": "session-with-prompts-test",
        "food_rating": 5,
        "service_rating": 5,
        "ambience_rating": 4,
        "overall_experience": "positive",
        "positive_tags": ["Flavorful"],
        "improvement_tags": [],
        "selected_prompts": [
            "The food quality was exceptional and cooked to perfection.",
            "Our server was knowledgeable and gave spot-on menu recommendations.",
        ],
        "customer_notes": "Great experience overall!",
    }
    response = await async_client.post("/api/v1/public/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

