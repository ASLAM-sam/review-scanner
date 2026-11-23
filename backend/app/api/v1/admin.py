"""
Restaurant Administration Endpoints
Protected routes: requires valid administrator Bearer token.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_admin, get_db
from app.models.user import AdminUserInDB
from app.schemas.common import APIResponse
from app.schemas.qr import QRDetailsResponse
from app.schemas.restaurant import RestaurantAdminResponse, RestaurantUpdateRequest
from app.schemas.subscription import (
    CreateOrderRequest,
    CreateOrderResponse,
    PaymentHistoryResponse,
    SubscriptionStatusResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse,
)
from app.services.qr_service import qr_service
from app.services.restaurant_service import restaurant_service
from app.services.subscription_service import subscription_service

router = APIRouter(prefix="/admin", tags=["Restaurant Administration"])


@router.get("/restaurant", response_model=APIResponse[RestaurantAdminResponse])
async def get_admin_restaurant_settings(
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """Retrieve complete restaurant installation settings for administrator."""
    settings_doc = await restaurant_service.get_settings(db)
    return APIResponse(
        success=True,
        message="Restaurant settings loaded",
        data=RestaurantAdminResponse(
            id=settings_doc.id,
            name=settings_doc.name,
            slug=settings_doc.slug,
            description=settings_doc.description,
            logo_url=settings_doc.logo_url,
            primary_color=settings_doc.primary_color,
            secondary_color=settings_doc.secondary_color,
            google_review_url=settings_doc.google_review_url,
            qr_destination_url=settings_doc.qr_destination_url,
            contact_phone=settings_doc.contact_phone,
            contact_email=settings_doc.contact_email,
            address=settings_doc.address,
            is_active=settings_doc.is_active,
            created_at=settings_doc.created_at,
            updated_at=settings_doc.updated_at,
        ),
    )


@router.put("/restaurant", response_model=APIResponse[RestaurantAdminResponse])
async def update_admin_restaurant_settings(
    payload: RestaurantUpdateRequest,
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """Update restaurant branding, Google review URL, and configuration."""
    updated = await restaurant_service.update_settings(db=db, update_data=payload)
    return APIResponse(
        success=True,
        message="Restaurant settings updated successfully",
        data=RestaurantAdminResponse(
            id=updated.id,
            name=updated.name,
            slug=updated.slug,
            description=updated.description,
            logo_url=updated.logo_url,
            primary_color=updated.primary_color,
            secondary_color=updated.secondary_color,
            google_review_url=updated.google_review_url,
            qr_destination_url=updated.qr_destination_url,
            contact_phone=updated.contact_phone,
            contact_email=updated.contact_email,
            address=updated.address,
            is_active=updated.is_active,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        ),
    )


@router.get("/qr", response_model=APIResponse[QRDetailsResponse])
async def get_admin_qr_details(
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Get dynamic QR code details for printing or digital presentation.
    Stable URL ensures the printed QR never needs to be reprinted.
    """
    settings_doc = await restaurant_service.get_settings(db)
    destination = settings_doc.qr_destination_url
    svg_str, data_url = qr_service.generate_qr_assets(destination)

    return APIResponse(
        success=True,
        message="Dynamic QR code assets generated",
        data=QRDetailsResponse(
            slug=settings_doc.slug,
            destination_url=destination,
            qr_svg=svg_str,
            qr_data_url=data_url,
        ),
    )


@router.get("/subscription", response_model=APIResponse[SubscriptionStatusResponse])
async def get_subscription_status(
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """Retrieve detailed subscription status, plan pricing, and period dates for this installation."""
    details = await subscription_service.get_subscription_details(db)
    return APIResponse(
        success=True,
        message="Subscription status retrieved",
        data=details,
    )


@router.post("/subscription/create-order", response_model=APIResponse[CreateOrderResponse])
async def create_renewal_order(
    payload: Optional[CreateOrderRequest] = None,
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Create a payment order with the gateway to renew subscription for 1 calendar month.
    Server strictly controls amount (₹249) and currency (INR).
    """
    idempotency_key = payload.idempotency_key if payload else None
    order_data = await subscription_service.create_renewal_order(
        db=db,
        admin_email=current_admin.email,
        idempotency_key=idempotency_key,
    )
    return APIResponse(
        success=True,
        message="Payment order created successfully",
        data=order_data,
    )


@router.post("/subscription/verify-payment", response_model=APIResponse[VerifyPaymentResponse])
async def verify_payment(
    payload: VerifyPaymentRequest,
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """
    Verify payment signature and activate subscription.
    Idempotent: Duplicate calls for the same order will not double-extend subscription.
    """
    result = await subscription_service.verify_and_activate(
        db=db,
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature,
    )
    return APIResponse(
        success=True,
        message=result.message,
        data=result,
    )


@router.get("/subscription/payments", response_model=APIResponse[PaymentHistoryResponse])
async def get_payment_history(
    limit: int = 50,
    current_admin: AdminUserInDB = Depends(get_current_admin),
    db: Optional[AsyncIOMotorDatabase] = Depends(get_db),
):
    """Retrieve audit history of renewal transactions and payment attempts."""
    history = await subscription_service.get_payment_history(db=db, limit=limit)
    return APIResponse(
        success=True,
        message="Payment history retrieved",
        data=history,
    )

