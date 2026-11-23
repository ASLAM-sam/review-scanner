"""
Smart Feedback Prompt Service
Manages 250+ structured, multi-lingual feedback prompts.
Provides category filtering, sentiment filtering, session deduplication, and random sampling.
Works 100% locally with zero external API calls or AI costs.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import logger
from app.schemas.prompt import FeedbackPromptResponse, PromptCategoryInfo, PromptStatsResponse


class PromptService:
    def __init__(self):
        self._prompts: List[Dict] = []
        self._prompts_by_id: Dict[str, Dict] = {}
        self._loaded: bool = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        json_path = Path(__file__).resolve().parent.parent / "data" / "feedback_prompts.json"
        if not json_path.exists():
            logger.warning(f"Prompts file not found at {json_path}. Operating with empty library.")
            self._prompts = []
            self._prompts_by_id = {}
            self._loaded = True
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._prompts = [p for p in data if p.get("is_active", True)]
                self._prompts_by_id = {p["id"]: p for p in self._prompts}
                self._loaded = True
                logger.info(f"Loaded {len(self._prompts)} feedback prompts from {json_path.name}")
        except Exception as exc:
            logger.error(f"Failed to load prompts JSON from {json_path}: {exc}")
            self._prompts = []
            self._prompts_by_id = {}
            self._loaded = True

    def get_prompts(
        self,
        category: Optional[str] = None,
        sentiment: Optional[str] = None,
        language: str = "en",
        limit: int = 12,
        exclude_ids: Optional[List[str]] = None,
        randomize: bool = True,
    ) -> List[FeedbackPromptResponse]:
        """
        Query smart prompts matching category, sentiment, and language.
        Excludes previously viewed prompt IDs to prevent duplicates within a customer session.
        """
        self._ensure_loaded()

        excluded_set = set(exclude_ids or [])
        matched: List[Dict] = []

        for p in self._prompts:
            if p["id"] in excluded_set:
                continue
            if p.get("language", "en") != language:
                continue
            if category and p.get("category") != category:
                continue
            if sentiment and p.get("sentiment") != sentiment:
                continue
            matched.append(p)

        # If strict filtering returns fewer than requested, backfill from other sentiments or language default
        if len(matched) < limit and sentiment:
            for p in self._prompts:
                if p["id"] in excluded_set or p in matched:
                    continue
                if p.get("language", "en") != language:
                    continue
                if category and p.get("category") != category:
                    continue
                matched.append(p)
                if len(matched) >= limit * 2:
                    break

        # Randomize selection without duplicates if requested
        if randomize and matched:
            selected = random.sample(matched, min(len(matched), limit))
        else:
            selected = matched[:limit]

        return [FeedbackPromptResponse(**p) for p in selected]

    def get_categories(self, language: str = "en") -> List[PromptCategoryInfo]:
        """Return all distinct categories with counts for the specified language."""
        self._ensure_loaded()
        cat_counts: Dict[str, Dict] = {}

        for p in self._prompts:
            if p.get("language", "en") != language:
                continue
            cat_key = p["category"]
            cat_name = p.get("category_name", cat_key.replace("_", " ").title())
            if cat_key not in cat_counts:
                cat_counts[cat_key] = {"name": cat_name, "count": 0}
            cat_counts[cat_key]["count"] += 1

        return [
            PromptCategoryInfo(key=k, name=v["name"], count=v["count"])
            for k, v in sorted(cat_counts.items(), key=lambda x: x[1]["name"])
        ]

    def get_stats(self) -> PromptStatsResponse:
        """Return library metrics: total count, language breakdown, category distribution."""
        self._ensure_loaded()

        lang_counts: Dict[str, int] = {}
        sent_counts: Dict[str, int] = {}
        cat_counts: Dict[str, Dict] = {}

        for p in self._prompts:
            lang = p.get("language", "en")
            sent = p.get("sentiment", "positive")
            cat_key = p["category"]
            cat_name = p.get("category_name", cat_key)

            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            sent_counts[sent] = sent_counts.get(sent, 0) + 1

            if cat_key not in cat_counts:
                cat_counts[cat_key] = {"name": cat_name, "count": 0}
            cat_counts[cat_key]["count"] += 1

        category_list = [
            PromptCategoryInfo(key=k, name=v["name"], count=v["count"])
            for k, v in sorted(cat_counts.items(), key=lambda x: x[0])
        ]

        return PromptStatsResponse(
            total_prompts=len(self._prompts),
            languages=lang_counts,
            categories=category_list,
            sentiments=sent_counts,
        )


prompt_service = PromptService()

