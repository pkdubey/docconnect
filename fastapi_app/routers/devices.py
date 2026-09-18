from typing import Optional

from asgiref.sync import sync_to_async
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from fastapi_app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])


class DeviceRegister(BaseModel):
    token: str
    platform: str = "FCM"  # FCM / APNS
    device_id: Optional[str] = None
    device_name: Optional[str] = None


class DeviceOut(BaseModel):
    id: str
    token: str
    platform: str
    created_at: str


@router.post("/", response_model=DeviceOut, status_code=201)
async def register_device(data: DeviceRegister, current_user=Depends(get_current_user)):
    def _register():
        devices = current_user.metadata.get('devices', [])
        # Avoid duplicate tokens
        for d in devices:
            if d['token'] == data.token:
                return d
        import uuid
        device = {
            "id": str(uuid.uuid4()),
            "token": data.token,
            "platform": data.platform,
            "device_id": data.device_id,
            "device_name": data.device_name,
            "created_at": __import__('datetime').datetime.now().isoformat(),
        }
        devices.append(device)
        current_user.metadata['devices'] = devices
        current_user.save(update_fields=['metadata'])
        return device

    device = await sync_to_async(_register, thread_sensitive=True)()
    return DeviceOut(id=device['id'], token=device['token'],
                     platform=device['platform'], created_at=device['created_at'])


@router.delete("/{device_id}/", status_code=204)
async def revoke_device(device_id: str, current_user=Depends(get_current_user)):
    def _revoke():
        devices = current_user.metadata.get('devices', [])
        new_devices = [d for d in devices if d['id'] != device_id]
        if len(new_devices) == len(devices):
            raise HTTPException(status_code=404, detail="Device not found")
        current_user.metadata['devices'] = new_devices
        current_user.save(update_fields=['metadata'])

    try:
        await sync_to_async(_revoke, thread_sensitive=True)()
    except HTTPException:
        raise
