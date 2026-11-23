"""
Public Customer Endpoints
Accessible without authentication.
Isolated from administrative controls.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase
import segno
import io

from app.api.deps import get_db
from app.schemas.common import APIResponse
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse, ReviewClickRequest
from app.schemas.prompt import FeedbackPromptResponse, PromptCategoryInfo, PromptStatsResponse
from app.schemas.qr import QRScanRequest, QRScanResponse
from app.schemas.restaurant import RestaurantPublicResponse
from app.services.feedback_service import feedback_service
from app.services.prompt_service import prompt_service
from app.services.qr_service import qr_service
from app.services.restaurant_service import restaurant_service
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/public", tags=["Public Customer Interface"])


@router.get("/restaurant", response_model=APIResponse[RestaurantPublicResponse])
async def get_public_restaurant(
    slug: Optional[str] = None,
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """Fetch restaurant public branding and configuration."""
    settings_doc = await restaurant_service.get_settings(db)
    
    if slug and settings_doc.slug != slug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{slug}' was not found on this installation.",
        )

    if not settings_doc.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{settings_doc.name}' is currently inactive.",
        )

    sub_status = await subscription_service.get_current_status(db)

    return APIResponse(
        success=True,
        message="Restaurant information retrieved",
        data=RestaurantPublicResponse(
            name=settings_doc.name,
            slug=settings_doc.slug,
            description=settings_doc.description,
            logo_url=settings_doc.logo_url,
            primary_color=settings_doc.primary_color,
            secondary_color=settings_doc.secondary_color,
            google_review_url=settings_doc.google_review_url,
            contact_phone=settings_doc.contact_phone,
            contact_email=settings_doc.contact_email,
            address=settings_doc.address,
            is_active=settings_doc.is_active,
            subscription_status=sub_status,
        ),
    )


@router.post("/qr/scan", response_model=APIResponse[QRScanResponse])
async def handle_qr_scan(
    request: Request,
    payload: Optional[QRScanRequest] = None,
    user_agent: Optional[str] = Header(None),
    referer: Optional[str] = Header(None),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Log an anonymous QR scan event and return destination & subscription status.
    Customer session ID is issued or continued.
    """
    client_ip = request.client.host if request.client else None
    input_session_id = payload.session_id if payload else None
    input_referrer = (payload.referrer if payload and payload.referrer else referer)

    session_id, destination_url, sub_status = await qr_service.record_scan(
        db=db,
        client_ip=client_ip,
        user_agent=user_agent,
        referrer=input_referrer,
        session_id=input_session_id,
    )

    restaurant = await restaurant_service.get_settings(db)

    return APIResponse(
        success=True,
        message="QR scan processed successfully",
        data=QRScanResponse(
            session_id=session_id,
            destination_url=destination_url,
            subscription_status=sub_status,
            restaurant_name=restaurant.name,
            restaurant_slug=restaurant.slug,
        ),
    )


@router.post("/feedback", response_model=APIResponse[FeedbackResponse])
async def submit_feedback(
    payload: FeedbackCreateRequest,
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Submit customer feedback for food, service, ambience, and optional notes.
    CRITICAL: Customer retains free choice to visit Google Reviews; no gating or fabrication.
    Server-side expiry enforcement: Rejects submissions if restaurant subscription is expired.
    """
    is_sub_active = await subscription_service.is_active(db)
    if not is_sub_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUBSCRIPTION_EXPIRED: The feedback service for this restaurant is temporarily unavailable.",
        )

    result = await feedback_service.record_feedback(db=db, payload=payload)
    return APIResponse(
        success=True,
        message="Thank you for your feedback!",
        data=result,
    )


@router.post("/review-click", response_model=APIResponse[dict])
async def handle_review_click(
    payload: ReviewClickRequest,
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Record an intentional customer click towards the Google Review destination.
    Separate event from QR scan and feedback submission.
    SECURITY: The target URL is always determined by server-side restaurant configuration.
    Server-side expiry enforcement: Rejects review clicks if restaurant subscription is expired.
    """
    is_sub_active = await subscription_service.is_active(db)
    if not is_sub_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUBSCRIPTION_EXPIRED: The review redirection service for this restaurant is temporarily unavailable.",
        )

    target_url = await feedback_service.record_review_click(
        db=db,
        session_id=payload.session_id,
    )
    return APIResponse(
        success=True,
        message="Review link click recorded",
        data={"target_url": target_url},
    )


@router.get("/qr-image")
async def get_qr_image(
    format: str = "png",
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Directly stream the restaurant's dynamic QR code image (PNG or SVG).
    Stable URL for printing or digital display.
    """
    restaurant = await restaurant_service.get_settings(db)
    destination = restaurant.qr_destination_url

    qr = segno.make(destination, error="M")

    if format.lower() == "svg":
        buffer = io.BytesIO()
        qr.save(buffer, kind="svg", scale=8, dark="#111827", light="#ffffff")
        return Response(content=buffer.getvalue(), media_type="image/svg+xml")
    else:
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=8, dark="#111827", light="#ffffff")
        return Response(content=buffer.getvalue(), media_type="image/png")


# --- Smart Feedback Prompt Library Endpoints ---

@router.get("/prompts", response_model=APIResponse[List[FeedbackPromptResponse]])
async def get_prompts(
    category: Optional[str] = Query(None, description="Optional category filter (e.g. food_quality, service_staff)"),
    sentiment: Optional[str] = Query(None, description="Optional sentiment filter (positive, neutral, improvement)"),
    language: str = Query("en", description="Language code: en, te, hi"),
    limit: int = Query(12, ge=1, le=50, description="Max number of prompts to return"),
    exclude_ids: Optional[str] = Query(None, description="Comma-separated IDs already viewed in this session"),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Retrieve curated, non-repetitive feedback prompts from the 250+ library.
    Filters by category, sentiment, and language. Deduplicates within customer session.
    Server-side expiry enforcement: Blocks prompts when subscription is expired.
    """
    is_sub_active = await subscription_service.is_active(db)
    if not is_sub_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUBSCRIPTION_EXPIRED: Feedback prompts are unavailable while restaurant subscription is expired.",
        )

    excluded_list = [i.strip() for i in exclude_ids.split(",") if i.strip()] if exclude_ids else None
    results = prompt_service.get_prompts(
        category=category,
        sentiment=sentiment,
        language=language,
        limit=limit,
        exclude_ids=excluded_list,
        randomize=True,
    )
    return APIResponse(
        success=True,
        message=f"Retrieved {len(results)} feedback prompts",
        data=results,
    )


@router.get("/prompts/categories", response_model=APIResponse[List[PromptCategoryInfo]])
async def get_prompt_categories(
    language: str = Query("en", description="Language code: en, te, hi"),
):
    """Retrieve all available feedback prompt categories with item counts."""
    categories = prompt_service.get_categories(language=language)
    return APIResponse(
        success=True,
        message="Prompt categories retrieved",
        data=categories,
    )


@router.get("/prompts/stats", response_model=APIResponse[PromptStatsResponse])
async def get_prompt_stats():
    """Retrieve library telemetry: total count, language breakdown, and category distribution."""
    stats = prompt_service.get_stats()
    return APIResponse(
        success=True,
        message="Prompt library stats retrieved",
        data=stats,
    )

