"""
Device token registration for push notifications.

Supports:
  - FCM  (Android + Firebase Cloud Messaging)
  - APNS (iOS Apple Push Notification Service)

Tokens are stored in the DeviceToken DB model (notifications app).
Re-registering the same device_id updates the existing token.
"""
from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])


class DeviceRegister(BaseModel):
    token: str = Field(..., min_length=10)
    platform: str = Field("FCM", pattern=r'^(FCM|APNS)$')
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    bundle_id: Optional[str] = None  # iOS APNs bundle ID


class DeviceOut(BaseModel):
    id: str
    token: str
    platform: str
    device_name: Optional[str]
    bundle_id: Optional[str]
    created_at: str


@router.post("/", response_model=DeviceOut, status_code=201,
             summary="Register device for push notifications (FCM or APNS/iOS)")
async def register_device(data: DeviceRegister, current_user=Depends(get_current_user)):
    def _register():
        from apps.notifications.models import DeviceToken

        # Update-on-re-register: same device_id → update token
        if data.device_id:
            existing = DeviceToken.objects.filter(
                user=current_user, device_id=data.device_id
            ).first()
            if existing:
                existing.token = data.token
                existing.platform = data.platform
                if data.device_name:
                    existing.device_name = data.device_name
                if data.bundle_id is not None:
                    existing.bundle_id = data.bundle_id
                existing.is_active = True
                existing.save(update_fields=['token', 'platform', 'device_name', 'bundle_id', 'is_active', 'updated_at'])
                return existing

        # Upsert by token (same token re-registered by different user is reassigned)
        device, _ = DeviceToken.objects.update_or_create(
            token=data.token,
            defaults={
                'user': current_user,
                'platform': data.platform,
                'device_id': data.device_id,
                'device_name': data.device_name,
                'bundle_id': data.bundle_id,
                'is_active': True,
            },
        )
        return device

    device = await sync_to_async(_register, thread_sensitive=True)()
    return DeviceOut(
        id=str(device.id),
        token=device.token,
        platform=device.platform,
        device_name=device.device_name,
        bundle_id=device.bundle_id,
        created_at=device.created_at.isoformat(),
    )


@router.delete("/{device_id}/", status_code=204, summary="Revoke a device push token")
async def revoke_device(device_id: str, current_user=Depends(get_current_user)):
    def _revoke():
        from apps.notifications.models import DeviceToken
        updated = DeviceToken.objects.filter(id=device_id, user=current_user).update(is_active=False)
        if not updated:
            raise HTTPException(status_code=404, detail="Device not found")

    try:
        await sync_to_async(_revoke, thread_sensitive=True)()
    except HTTPException:
        raise


@router.get("/", summary="List registered devices for current user")
async def list_devices(current_user=Depends(get_current_user)):
    def _list():
        from apps.notifications.models import DeviceToken
        return list(DeviceToken.objects.filter(user=current_user, is_active=True).order_by('-created_at'))

    devices = await sync_to_async(_list, thread_sensitive=True)()
    return {
        "total": len(devices),
        "devices": [
            {
                "id": str(d.id),
                "platform": d.platform,
                "device_name": d.device_name,
                "device_id": d.device_id,
                "bundle_id": d.bundle_id,
                "created_at": d.created_at.isoformat(),
            }
            for d in devices
        ],
    }
