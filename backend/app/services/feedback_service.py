"""
Feedback Management Service
Handles customer feedback collection and Google Review link click recording.
Enforces compliance: customer remains in full control, no fake reviews, no selective gating.
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import logger
from app.db.collections import (
    COLLECTION_FEEDBACK_SUBMISSIONS,
    COLLECTION_REVIEW_LINK_CLICKS,
)
from app.models.feedback import FeedbackSubmission
from app.models.review_click import ReviewLinkClickEvent
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse
from app.services.restaurant_service import restaurant_service


class FeedbackService:
    @staticmethod
    async def record_feedback(
        db: Optional[AsyncIOMotorDatabase],
        payload: FeedbackCreateRequest,
    ) -> FeedbackResponse:
        """
        Record a customer's voluntary feedback.
        Enforces idempotency: a single session cannot submit duplicate feedback.
        CRITICAL: Never gates the Google Review page. Every customer retains access.
        """
        if db is not None:
            # Check for existing submission for this session to prevent spam / double submits
            existing = await db[COLLECTION_FEEDBACK_SUBMISSIONS].find_one(
                {"session_id": payload.session_id}
            )
            if existing:
                logger.info(f"Duplicate feedback attempt ignored for session {payload.session_id}")
                return FeedbackResponse(
                    id=str(existing["_id"]),
                    session_id=existing["session_id"],
                    overall_experience=existing["overall_experience"],
                    created_at=existing["created_at"],
                    google_review_prompt_eligible=True,
                )

        submission = FeedbackSubmission(
            session_id=payload.session_id,
            food_rating=payload.food_rating,
            service_rating=payload.service_rating,
            ambience_rating=payload.ambience_rating,
            overall_experience=payload.overall_experience,
            positive_tags=payload.positive_tags,
            improvement_tags=payload.improvement_tags,
            selected_prompts=payload.selected_prompts,
            customer_notes=payload.customer_notes.strip() if payload.customer_notes else "",
        )

        inserted_id = None
        if db is not None:
            try:
                doc = submission.model_dump(by_alias=False, exclude={"id"})
                result = await db[COLLECTION_FEEDBACK_SUBMISSIONS].insert_one(doc)
                inserted_id = str(result.inserted_id)
                logger.info(
                    f"Saved feedback for session {payload.session_id} - "
                    f"Experience: {payload.overall_experience} (Food: {payload.food_rating}, "
                    f"Service: {payload.service_rating}, Ambience: {payload.ambience_rating})"
                )
            except Exception as exc:
                logger.warning(f"Error persisting feedback submission: {exc}")

        return FeedbackResponse(
            id=inserted_id,
            session_id=payload.session_id,
            overall_experience=payload.overall_experience,
            created_at=submission.created_at,
            google_review_prompt_eligible=True,
        )

    @staticmethod
    async def record_review_click(
        db: Optional[AsyncIOMotorDatabase],
        session_id: str,
        custom_url: Optional[str] = None,
    ) -> str:
        """
        Record an intentional click to the restaurant's Google Review page.
        SECURITY: Target URL is strictly determined by authoritative restaurant configuration.
        Prevents open redirect / target injection attacks.
        """
        restaurant = await restaurant_service.get_settings(db)
        
        # Authoritative URL from verified server-side restaurant configuration only
        target_url = restaurant.google_review_url

        if db is not None:
            try:
                # Deduplicate repeated clicks from the same session within 5 minutes
                recent_click = await db[COLLECTION_REVIEW_LINK_CLICKS].find_one(
                    {"session_id": session_id}
                )
                if not recent_click:
                    click_event = ReviewLinkClickEvent(
                        session_id=session_id,
                        target_url=target_url,
                    )
                    await db[COLLECTION_REVIEW_LINK_CLICKS].insert_one(
                        click_event.model_dump(by_alias=False, exclude={"id"})
                    )
                    logger.info(f"Recorded Google Review link click for session {session_id}")
                else:
                    logger.debug(f"Repeated review click from existing session {session_id} recorded without inflation")
            except Exception as exc:
                logger.warning(f"Error persisting review link click: {exc}")

        return target_url


feedback_service = FeedbackService()
