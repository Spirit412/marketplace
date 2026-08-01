import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import (
    TokenPayload,
    get_token_payload,
)
from src.core.database import get_async_session
from src.dependencies import get_notification_service
from src.repositories.notification_repo import NotificationRepository
from src.schemes.request.notification import SendNotificationRequest
from src.schemes.response.notification import NotificationResponse
from src.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "/",
    summary="Get notifications",
)
async def get_notifications(
    token: Annotated[TokenPayload, Depends(get_token_payload)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    status: Annotated[str, Query(description="Filter: unread | all")] = "unread",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NotificationResponse]:
    """Get notifications for the authenticated user, filtered by status."""
    repo = NotificationRepository()
    user_id = uuid.UUID(token.user_id)

    if status == "unread":
        items = await repo.get_unread(session, user_id, limit=limit, offset=offset)
    else:
        items = await repo.get_history(session, user_id, limit=limit, offset=offset)

    return [
        NotificationResponse(
            uuid=item.id,
            event_type=item.event_type,
            channel=item.channel,
            notification_type=item.notification_type,
            subject=item.subject,
            body=item.body,
            status="unread" if item.status == "unread" else "read",
            created_at=item.created_at,
            read_at=item.read_at,
        )
        for item in items
    ]


@router.get(
    "/history",
    summary="Get notification history",
)
async def get_history(
    token: Annotated[TokenPayload, Depends(get_token_payload)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NotificationResponse]:
    """Get notification history for the authenticated user."""
    repo = NotificationRepository()
    user_id = uuid.UUID(token.user_id)
    items = await repo.get_history(session, user_id, limit=limit, offset=offset)

    return [
        NotificationResponse(
            uuid=item.id,
            event_type=item.event_type,
            channel=item.channel,
            notification_type=item.notification_type,
            subject=item.subject,
            body=item.body,
            status="unread" if item.status == "unread" else "read",
            created_at=item.created_at,
            read_at=item.read_at,
        )
        for item in items
    ]


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
    if request.user_uuids is None:
        raise HTTPException(
            status_code=400, detail="user_uuids is required for manual send"
        )

    results = await service.send_manual(
        session,
        user_uuids=request.user_uuids,
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
    "/{notification_uuid}/read",
    response_model=dict,
    summary="Mark notification as read",
)
async def mark_read(
    notification_uuid: uuid.UUID,
    _token: Annotated[TokenPayload, Depends(get_token_payload)],
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict[str, Any]:
    """Mark a specific notification as read."""
    repo = NotificationRepository()
    result = await repo.mark_read(session, notification_uuid)
    if result is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "ok", "uuid": str(result.id)}
