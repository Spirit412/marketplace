from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.dependencies import get_notification_service
from src.schemes.request.notification import SendNotificationRequest
from src.schemes.response.notification import NotificationResponse
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

NotificationIdPath = Annotated[
    UUID,
    Path(
        description="Notification id (UUID7).",
        examples=["019f0000-0000-7000-8000-000000000100"],
    ),
]


@router.get(
    "/",
    summary="Get notifications",
)
async def get_notifications(
    token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    status: Annotated[str, Query(description="Filter: unread | all")] = "unread",
    limit: Annotated[int, Query(ge=1, le=200, description="Max rows to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
) -> list[NotificationResponse]:
    """Get notifications for the authenticated user, filtered by status."""
    return await service.get_notifications(
        session,
        UUID(token.user_id),
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/history",
    summary="Get notification history",
)
async def get_history(
    token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    limit: Annotated[int, Query(ge=1, le=200, description="Max rows to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Rows to skip.")] = 0,
) -> list[NotificationResponse]:
    """Get notification history for the authenticated user."""
    return await service.get_history(
        session, UUID(token.user_id), limit=limit, offset=offset
    )


@router.post(
    "/",
    response_model=dict,
    summary="Send notification",
)
async def send_notification(
    request: SendNotificationRequest,
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """Send a notification to one or more users."""
    results = await service.send_manual(
        session,
        user_ids=request.user_ids,
        subject=request.subject,
        body=request.body,
        channel=request.channel.value,
        notification_type=request.notification_type.value,
    )
    return {
        "sent": len(results),
        "notification_ids": [str(notif.id) for notif in results],
    }


@router.post(
    "/{notification_id}/read",
    response_model=dict,
    summary="Mark notification as read",
)
async def mark_read(
    notification_id: NotificationIdPath,
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    service: Annotated[NotificationService, Depends(get_notification_service)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """Mark a specific notification as read."""
    result = await service.mark_read(session, notification_id)
    return {"status": "ok", "id": str(result.id)}
